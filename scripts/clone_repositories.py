#!/usr/bin/env python3
"""
scripts/clone_repositories.py
Clones target n8n workflow source repositories into sources/ using shallow clones.
Records provenance: remote URL, HEAD commit hash, clone date, license files found.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "sources"
SOURCES_MANIFEST_FILE = SOURCES_DIR / "sources_manifest.json"

DEFAULT_REPOSITORIES = [
    {
        "id": "scrapernode-awesome-n8n",
        "name": "awesome-n8n-templates",
        "url": "https://github.com/ScraperNode/awesome-n8n-templates",
        "primary_author": "ScraperNode",
        "description": "Curated collection of production-ready n8n templates and workflows."
    },
    {
        "id": "zengfr-all-templates",
        "name": "n8n-workflow-all-templates",
        "url": "https://github.com/zengfr/n8n-workflow-all-templates",
        "primary_author": "zengfr",
        "description": "Massive aggregation of public community workflows and node examples."
    },
    {
        "id": "aboalrejalai-workflows",
        "name": "aboalrejalai-n8n-workflows",
        "url": "https://github.com/aboalrejalai/n8n-workflows",
        "primary_author": "aboalrejalai",
        "description": "AI-focused and marketing automation n8n workflows."
    },
    {
        "id": "danitilahun-templates",
        "name": "danitilahun-n8n-workflow-templates",
        "url": "https://github.com/Danitilahun/n8n-workflow-templates",
        "primary_author": "Danitilahun",
        "description": "Enterprise and integration automation templates for n8n."
    },
    {
        "id": "enescingoz-awesome-n8n",
        "name": "enescingoz-awesome-n8n-templates",
        "url": "https://github.com/enescingoz/awesome-n8n-templates",
        "primary_author": "Enes Cingöz",
        "description": "Hand-picked advanced workflows, AI automations, and scraper pipelines."
    }
]

LICENSE_NAMES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md", "LICENSE-MIT", "LICENSE-APACHE"]

def run_git(args, cwd=None):
    try:
        res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def detect_repo_license(repo_path: Path):
    found = []
    for item in repo_path.iterdir():
        if item.is_file() and item.name.upper() in [x.upper() for x in LICENSE_NAMES]:
            found.append(item.name)
    if not found:
        # Check README for license mentions
        readme_candidates = list(repo_path.glob("README*"))
        if readme_candidates:
            readme_text = readme_candidates[0].read_text(encoding="utf-8", errors="ignore")
            if "MIT License" in readme_text or "License: MIT" in readme_text:
                return "MIT (declared in README)", []
            elif "Apache License" in readme_text:
                return "Apache-2.0 (declared in README)", []
            elif "GPL" in readme_text:
                return "GPL (declared in README)", []
        return "Unknown / Not specified", []
    
    # Read first license file content
    lic_file = repo_path / found[0]
    content = lic_file.read_text(encoding="utf-8", errors="ignore")
    lic_type = "Custom / Unspecified"
    if "MIT License" in content or "Permission is hereby granted, free of charge" in content:
        lic_type = "MIT"
    elif "Apache License" in content and "Version 2.0" in content:
        lic_type = "Apache-2.0"
    elif "General Public License" in content:
        lic_type = "GPL"
    elif "BSD" in content:
        lic_type = "BSD"
    elif "Creative Commons" in content or "CC0" in content:
        lic_type = "CC / Public Domain"
    return lic_type, found

def clone_or_update_repo(repo_info: dict) -> dict:
    repo_name = repo_info["name"]
    target_dir = SOURCES_DIR / repo_name
    url = repo_info["url"]
    
    status = "cloned"
    err_msg = None
    commit_hash = "unknown"
    clone_time = datetime.utcnow().isoformat() + "Z"
    
    print(f"[*] Processing repository: {repo_info['id']} ({url})...")
    
    if target_dir.exists() and (target_dir / ".git").exists():
        print(f"    Target directory exists. Pulling latest commit...")
        git_pull = run_git(["pull", "--ff-only"], cwd=str(target_dir))
        commit_hash = run_git(["rev-parse", "HEAD"], cwd=str(target_dir)) or "unknown"
        status = "already_exists_updated"
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target_dir)],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            print(f"    [!] Failed to clone {url}: {res.stderr.strip()}")
            status = "failed"
            err_msg = res.stderr.strip()
        else:
            commit_hash = run_git(["rev-parse", "HEAD"], cwd=str(target_dir)) or "unknown"
            status = "cloned_shallow"
            print(f"    [+] Successfully cloned ({commit_hash[:8]})")
    
    license_type, license_files = ("Unknown", [])
    if target_dir.exists():
        license_type, license_files = detect_repo_license(target_dir)

    record = {
        "id": repo_info["id"],
        "name": repo_name,
        "url": url,
        "primary_author": repo_info["primary_author"],
        "description": repo_info["description"],
        "status": status,
        "commit_hash": commit_hash,
        "import_timestamp": clone_time,
        "local_path": str(target_dir.relative_to(BASE_DIR)),
        "license_type": license_type,
        "license_files": license_files,
        "error": err_msg
    }
    return record

def main():
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    
    for repo_info in DEFAULT_REPOSITORIES:
        record = clone_or_update_repo(repo_info)
        results.append(record)
        
    SOURCES_MANIFEST_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[+] Successfully saved source manifest to {SOURCES_MANIFEST_FILE}")
    
    success_count = sum(1 for r in results if r["status"] in ["cloned_shallow", "already_exists_updated"])
    print(f"[+] Repositories processed: {len(results)} | Successful: {success_count} | Failed: {len(results) - success_count}")

if __name__ == "__main__":
    main()
