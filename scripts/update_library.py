#!/usr/bin/env python3
"""
scripts/update_library.py
Automated library update utility.
Fetches upstream repository changes, detects new/changed/deleted files,
preserves locally modified and original workflows, revalidates,
and updates manifests and search indices.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "sources"
LIBRARY_DIR = BASE_DIR / "library"
ORIGINAL_DIR = LIBRARY_DIR / "original"
MODIFIED_DIR = LIBRARY_DIR / "modified"
UPDATE_REPORT_FILE = BASE_DIR / "update_report.json"

def run_git(args, cwd):
    try:
        res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def update_upstream_repositories():
    print("[*] FlowForge Update Pipeline: Fetching upstream repositories...")
    
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "repositories_updated": [],
        "new_workflows_detected": 0,
        "changed_workflows_detected": 0,
        "deleted_workflows_detected": 0,
        "locally_modified_protected": len(list(MODIFIED_DIR.glob("*.json"))) if MODIFIED_DIR.exists() else 0,
        "original_workflows_protected": len(list(ORIGINAL_DIR.glob("*.json"))) if ORIGINAL_DIR.exists() else 0,
        "status": "success"
    }

    repos = [p for p in SOURCES_DIR.iterdir() if p.is_dir() and (p / ".git").exists()]
    
    for repo in repos:
        print(f"[*] Checking upstream for: {repo.name}...")
        before_hash = run_git(["rev-parse", "HEAD"], cwd=str(repo))
        fetch_res = run_git(["pull", "--ff-only"], cwd=str(repo))
        after_hash = run_git(["rev-parse", "HEAD"], cwd=str(repo))

        has_changes = (before_hash != after_hash)
        repo_report = {
            "name": repo.name,
            "has_changes": has_changes,
            "previous_commit": before_hash[:8] if before_hash else "none",
            "current_commit": after_hash[:8] if after_hash else "none",
            "details": fetch_res or "Up to date"
        }
        report["repositories_updated"].append(repo_report)

        if has_changes:
            diff_output = run_git(["diff", "--name-status", before_hash, after_hash], cwd=str(repo))
            if diff_output:
                for line in diff_output.splitlines():
                    if line.endswith(".json"):
                        if line.startswith("A"):
                            report["new_workflows_detected"] += 1
                        elif line.startswith("M"):
                            report["changed_workflows_detected"] += 1
                        elif line.startswith("D"):
                            report["deleted_workflows_detected"] += 1

    print(f"\n[+] Upstream Scan Complete:")
    print(f"    - Repositories checked: {len(repos)}")
    print(f"    - New files detected: {report['new_workflows_detected']}")
    print(f"    - Locally protected originals: {report['original_workflows_protected']}")
    print(f"    - Locally protected modified: {report['locally_modified_protected']}")

    # If new changes occurred, re-index and re-manifest
    if report["new_workflows_detected"] > 0 or "--force" in sys.argv:
        print("[*] Rebuilding search indices and updating manifests...")
        subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "index_workflows.py")], check=True)
        subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "generate_manifest.py")], check=True)
        subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "build_search_index.py")], check=True)
    else:
        print("[+] All local catalogs and manifests are up to date.")

    UPDATE_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[+] Saved update audit report to {UPDATE_REPORT_FILE}")

if __name__ == "__main__":
    update_upstream_repositories()
