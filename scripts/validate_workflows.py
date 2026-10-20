#!/usr/bin/env python3
"""
scripts/validate_workflows.py
Validates n8n workflow JSON files according to security, structural, and license compliance rules.
Outputs results to validation_report.csv and returns structured report data.
"""

import os
import re
import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "sources"
WORKFLOWS_DIR = BASE_DIR / "workflows"
REPORT_CSV = BASE_DIR / "validation_report.csv"

# Regex patterns for detecting potential hardcoded secrets
SECRET_PATTERNS = [
    ("OpenAI API Key", re.compile(r"sk-[a-zA-Z0-9_\-]{20,}")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("Slack Token", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Generic Bearer Token", re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]{25,})", re.IGNORECASE)),
    ("Private Key Header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Patterns for dangerous execution or SSRF targets
DANGEROUS_CODE_PATTERNS = [
    re.compile(r"require\s*\(\s*['\"]child_process['\"]\s*\)"),
    re.compile(r"\b(exec|spawn|execSync|spawnSync)\s*\("),
    re.compile(r"import\s+subprocess"),
    re.compile(r"\bos\.(system|popen)\b"),
    re.compile(r"169\.254\.169\.254"), # AWS / Cloud metadata SSRF
]

def mask_secret(secret_str: str) -> str:
    """Masks secret so it is never exposed in logs or CSV reports."""
    if len(secret_str) <= 6:
        return "***"
    return secret_str[:3] + "*" * (len(secret_str) - 6) + secret_str[-3:]

def validate_workflow_data(data: dict, filepath: Path) -> dict:
    result = {
        "is_valid_json": True,
        "is_n8n_workflow": False,
        "title": "Untitled Workflow",
        "node_count": 0,
        "classification": "Invalid or unsupported",
        "risk_level": "LOW",
        "dangerous_execution": False,
        "dangerous_details": [],
        "external_http_count": 0,
        "external_destinations": [],
        "potential_secrets_count": 0,
        "potential_secrets": [],
        "community_nodes": [],
        "credentials_required": [],
        "issues": []
    }
    
    # Handle both top-level workflow and nested workflow export formats
    workflow_obj = data
    if "workflow" in data and isinstance(data["workflow"], dict) and "nodes" in data["workflow"]:
        workflow_obj = data["workflow"]
        
    if "name" in workflow_obj and isinstance(workflow_obj["name"], str):
        result["title"] = workflow_obj["name"]
    elif "name" in data and isinstance(data["name"], str):
        result["title"] = data["name"]
    else:
        result["title"] = filepath.stem.replace("-", " ").replace("_", " ").title()

    nodes = workflow_obj.get("nodes")
    if not isinstance(nodes, list):
        result["issues"].append("Missing or non-list 'nodes' field.")
        result["classification"] = "Invalid or unsupported"
        return result
        
    result["is_n8n_workflow"] = True
    result["node_count"] = len(nodes)
    
    if len(nodes) == 0:
        result["issues"].append("Workflow has 0 nodes.")
        result["classification"] = "Invalid or unsupported"
        return result

    node_names = set()
    raw_text = json.dumps(data)

    # 1. Scan for hardcoded secrets
    for secret_name, pattern in SECRET_PATTERNS:
        matches = pattern.findall(raw_text)
        for m in matches:
            val = m if isinstance(m, str) else m[0]
            # Ignore template placeholders like {{ $env.KEY }} or sk-your-key-here
            if any(placeholder in val.lower() for placeholder in ["your", "placeholder", "test", "dummy", "xxx", "{{"]):
                continue
            result["potential_secrets_count"] += 1
            result["potential_secrets"].append(f"{secret_name}: {mask_secret(val)}")

    # 2. Scan for dangerous execution patterns in code
    for pat in DANGEROUS_CODE_PATTERNS:
        if pat.search(raw_text):
            result["dangerous_execution"] = True
            result["dangerous_details"].append(f"Pattern matched: {pat.pattern}")

    # 3. Inspect individual nodes
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            result["issues"].append(f"Node #{idx} is not a valid dictionary.")
            continue
            
        n_name = node.get("name", f"Node_{idx}")
        n_type = node.get("type", "")
        
        if n_name in node_names:
            result["issues"].append(f"Duplicate node name: '{n_name}'")
        node_names.add(n_name)
        
        # Check node type
        if not n_type:
            result["issues"].append(f"Node '{n_name}' is missing 'type'.")
            
        # Dangerous node types
        if n_type == "n8n-nodes-base.executeCommand":
            result["dangerous_execution"] = True
            result["dangerous_details"].append(f"Execute Command Node detected ('{n_name}')")

        # Community node check
        if n_type and not (
            n_type.startswith("n8n-nodes-base.") 
            or n_type.startswith("@n8n/n8n-nodes-langchain.")
            or n_type.startswith("n8n-nodes-langchain.")
        ):
            if n_type not in result["community_nodes"]:
                result["community_nodes"].append(n_type)

        # Credentials check
        creds = node.get("credentials")
        if creds and isinstance(creds, dict):
            for c_type in creds.keys():
                if c_type not in result["credentials_required"]:
                    result["credentials_required"].append(c_type)

        # HTTP Request URL check
        if "httpRequest" in n_type.lower():
            params = node.get("parameters", {})
            url = params.get("url", "")
            if isinstance(url, str) and url.startswith("http"):
                result["external_http_count"] += 1
                if len(result["external_destinations"]) < 5:
                    result["external_destinations"].append(url)

    # 4. Check Connections
    connections = workflow_obj.get("connections", {})
    if isinstance(connections, dict):
        for source_node, conn_obj in connections.items():
            if source_node not in node_names:
                result["issues"].append(f"Connection source '{source_node}' does not exist in nodes list.")

    # Determine risk level and final classification
    if result["dangerous_execution"]:
        result["risk_level"] = "HIGH"
        result["classification"] = "Requires manual review"
    elif result["potential_secrets_count"] > 0:
        result["risk_level"] = "MEDIUM"
        result["classification"] = "Requires manual review"
    elif len(result["issues"]) > 0:
        result["risk_level"] = "LOW"
        result["classification"] = "Requires manual review"
    else:
        result["risk_level"] = "SAFE"
        result["classification"] = "Structurally plausible n8n workflow"

    return result

def validate_file(filepath: Path) -> dict:
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        data = json.loads(content)
        res = validate_workflow_data(data, filepath)
        res["filepath"] = str(filepath.resolve())
        return res
    except json.JSONDecodeError as e:
        return {
            "filepath": str(filepath.resolve()),
            "is_valid_json": False,
            "is_n8n_workflow": False,
            "title": filepath.stem,
            "node_count": 0,
            "classification": "Invalid or unsupported",
            "risk_level": "INVALID",
            "dangerous_execution": False,
            "dangerous_details": [],
            "external_http_count": 0,
            "external_destinations": [],
            "potential_secrets_count": 0,
            "potential_secrets": [],
            "community_nodes": [],
            "credentials_required": [],
            "issues": [f"JSON Parse Error: {str(e)}"]
        }
    except Exception as e:
        return {
            "filepath": str(filepath.resolve()),
            "is_valid_json": False,
            "is_n8n_workflow": False,
            "title": filepath.stem,
            "node_count": 0,
            "classification": "Invalid or unsupported",
            "risk_level": "ERROR",
            "dangerous_execution": False,
            "dangerous_details": [],
            "external_http_count": 0,
            "external_destinations": [],
            "potential_secrets_count": 0,
            "potential_secrets": [],
            "community_nodes": [],
            "credentials_required": [],
            "issues": [f"File read error: {str(e)}"]
        }

def run_validation_on_directory(target_dir: Path, output_csv: Path = REPORT_CSV):
    json_files = list(target_dir.rglob("*.json"))
    print(f"[*] Found {len(json_files)} JSON files in {target_dir}. Running validation checks...")
    
    reports = []
    for f in json_files:
        # Skip package.json or config files
        if f.name.lower() in ["package.json", "package-lock.json", "tsconfig.json", "branding.json", "categories.json"]:
            continue
        rep = validate_file(f)
        reports.append(rep)
        
    # Write CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "filepath", "title", "classification", "risk_level", "node_count",
            "issues_count", "dangerous_execution", "external_http_count",
            "potential_secrets_count", "community_nodes", "credentials_required", "issues"
        ])
        for r in reports:
            writer.writerow([
                r["filepath"],
                r["title"],
                r["classification"],
                r["risk_level"],
                r["node_count"],
                len(r["issues"]),
                r["dangerous_execution"],
                r["external_http_count"],
                r["potential_secrets_count"],
                ";".join(r["community_nodes"]),
                ";".join(r["credentials_required"]),
                " | ".join(r["issues"])
            ])
            
    print(f"[+] Validation report written to {output_csv}")
    
    # Summary
    class_counts = {}
    for r in reports:
        c = r["classification"]
        class_counts[c] = class_counts.get(c, 0) + 1
        
    print("\n[+] Validation Summary:")
    for k, v in class_counts.items():
        print(f"    - {k}: {v}")
        
    return reports

if __name__ == "__main__":
    scan_dir = WORKFLOWS_DIR if WORKFLOWS_DIR.exists() else SOURCES_DIR
    run_validation_on_directory(scan_dir)
