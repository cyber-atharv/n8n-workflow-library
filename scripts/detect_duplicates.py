#!/usr/bin/env python3
"""
scripts/detect_duplicates.py
Identifies exact and semantic/structural duplicate n8n workflows across all cloned repositories.
Outputs results to duplicate_report.csv.
"""

import os
import json
import hashlib
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "sources"
WORKFLOWS_DIR = BASE_DIR / "workflows"
REPORT_CSV = BASE_DIR / "duplicate_report.csv"

def compute_exact_hash(data: dict) -> str:
    """Computes SHA-256 of normalized minified JSON."""
    canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

def compute_structural_hash(data: dict) -> str:
    """
    Computes structural hash by stripping non-functional metadata
    such as canvas coordinates [x,y], random IDs, and execution counters.
    """
    workflow_obj = data
    if "workflow" in data and isinstance(data["workflow"], dict) and "nodes" in data["workflow"]:
        workflow_obj = data["workflow"]

    nodes = workflow_obj.get("nodes", [])
    if not isinstance(nodes, list):
        return ""

    normalized_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        cleaned = {
            "name": node.get("name"),
            "type": node.get("type"),
            "typeVersion": node.get("typeVersion"),
            "parameters": node.get("parameters", {})
        }
        normalized_nodes.append(cleaned)

    # Sort nodes by name for order-independent hashing
    normalized_nodes.sort(key=lambda x: str(x.get("name", "")))

    normalized_connections = workflow_obj.get("connections", {})

    structural_obj = {
        "nodes": normalized_nodes,
        "connections": normalized_connections
    }
    dumped = json.dumps(structural_obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(dumped.encode('utf-8')).hexdigest()

def scan_and_detect_duplicates(target_dirs=None, output_csv=REPORT_CSV):
    if target_dirs is None:
        target_dirs = [WORKFLOWS_DIR] if WORKFLOWS_DIR.exists() else [SOURCES_DIR]

    json_files = []
    for d in target_dirs:
        for f in d.rglob("*.json"):
            if f.name.lower() in ["package.json", "package-lock.json", "tsconfig.json", "branding.json", "categories.json", "sources_manifest.json"]:
                continue
            json_files.append(f)

    print(f"[*] Analyzing {len(json_files)} workflow files for exact and structural duplicates...")

    exact_map = {}       # exact_hash -> list of files
    structural_map = {}  # struct_hash -> list of files
    file_records = []

    for f in json_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)
            
            # Skip non-n8n json
            nodes = data.get("nodes")
            if not nodes and "workflow" in data and isinstance(data["workflow"], dict):
                nodes = data["workflow"].get("nodes")
            if not isinstance(nodes, list) or len(nodes) == 0:
                continue

            title = data.get("name") or f.stem
            exact_h = compute_exact_hash(data)
            struct_h = compute_structural_hash(data)

            record = {
                "filepath": str(f.resolve()),
                "filename": f.name,
                "title": title,
                "exact_hash": exact_h,
                "structural_hash": struct_h,
                "status": "Unique",
                "canonical_filepath": "",
                "similarity_reason": "None"
            }
            file_records.append(record)

            exact_map.setdefault(exact_h, []).append(record)
            structural_map.setdefault(struct_h, []).append(record)

        except Exception:
            continue

    # Mark duplicates
    exact_dup_count = 0
    struct_dup_count = 0

    for exact_h, records in exact_map.items():
        if len(records) > 1:
            canonical = records[0]
            canonical["status"] = "Canonical"
            canonical["canonical_filepath"] = canonical["filepath"]
            for dup in records[1:]:
                dup["status"] = "Exact Duplicate"
                dup["canonical_filepath"] = canonical["filepath"]
                dup["similarity_reason"] = "Identical raw JSON SHA-256"
                exact_dup_count += 1

    for struct_h, records in structural_map.items():
        if len(records) > 1:
            # Check records that were not already marked as exact duplicates
            unmarked = [r for r in records if r["status"] == "Unique"]
            if len(unmarked) > 1:
                canonical = unmarked[0]
                canonical["status"] = "Canonical"
                canonical["canonical_filepath"] = canonical["filepath"]
                for dup in unmarked[1:]:
                    dup["status"] = "Structural Clone"
                    dup["canonical_filepath"] = canonical["filepath"]
                    dup["similarity_reason"] = "Identical nodes, logic, and topology (different coordinates or IDs)"
                    struct_dup_count += 1

    # Write CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "filepath", "filename", "title", "status",
            "similarity_reason", "canonical_filepath", "exact_hash", "structural_hash"
        ])
        for r in file_records:
            writer.writerow([
                r["filepath"], r["filename"], r["title"], r["status"],
                r["similarity_reason"], r["canonical_filepath"],
                r["exact_hash"], r["structural_hash"]
            ])

    print(f"[+] Total files analyzed: {len(file_records)}")
    print(f"[+] Exact duplicates: {exact_dup_count}")
    print(f"[+] Structural duplicates: {struct_dup_count}")
    print(f"[+] Unique canonical workflows: {len(file_records) - exact_dup_count - struct_dup_count}")
    print(f"[+] Duplicate report saved to {output_csv}")

    return file_records

if __name__ == "__main__":
    scan_and_detect_duplicates()
