#!/usr/bin/env python3
"""
scripts/check_licenses.py
Audits open-source licenses, copyright notices, and compliance obligations
across all cloned source repositories and individual workflows.
Outputs results to license_audit.csv.
"""

import os
import re
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "sources"
AUDIT_CSV = BASE_DIR / "license_audit.csv"

LICENSE_PATTERNS = [
    ("MIT", "MIT", re.compile(r"MIT\s+License|Permission\s+is\s+hereby\s+granted,\s+free\s+of\s+charge", re.IGNORECASE)),
    ("Apache-2.0", "Apache-2.0", re.compile(r"Apache\s+License.*Version\s+2\.0", re.IGNORECASE | re.DOTALL)),
    ("GPL-3.0", "GPL-3.0", re.compile(r"GNU\s+General\s+Public\s+License.*version\s+3", re.IGNORECASE | re.DOTALL)),
    ("AGPL-3.0", "AGPL-3.0", re.compile(r"GNU\s+Affero\s+General\s+Public\s+License", re.IGNORECASE)),
    ("BSD-3-Clause", "BSD-3-Clause", re.compile(r"Redistribution\s+and\s+use\s+in\s+source\s+and\s+binary\s+forms.*Neither\s+the\s+name", re.IGNORECASE | re.DOTALL)),
    ("BSD-2-Clause", "BSD-2-Clause", re.compile(r"Redistribution\s+and\s+use\s+in\s+source\s+and\s+binary\s+forms", re.IGNORECASE)),
    ("CC0-1.0", "CC0-1.0", re.compile(r"Creative\s+Commons\s+Zero|CC0\s+1\.0", re.IGNORECASE)),
    ("CC-BY-4.0", "CC-BY-4.0", re.compile(r"Creative\s+Commons\s+Attribution\s+4\.0|CC\s+BY\s+4\.0", re.IGNORECASE)),
    ("Unlicense", "Unlicense", re.compile(r"This\s+is\s+free\s+and\s+unencumbered\s+software\s+released\s+into\s+the\s+public\s+domain", re.IGNORECASE))
]

COPYRIGHT_REGEX = re.compile(r"Copyright\s+(?:\(c\)\s*)?(?:[0-9]{4}(?:\s*-\s*[0-9]{4})?\s+)?([^\r\n]+)", re.IGNORECASE)

LICENSE_RULES = {
    "MIT": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "Permissive. Keep original copyright notice and MIT permission notice intact."
    },
    "Apache-2.0": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "Permissive. Retain copyright, notice files, and clearly document any modifications."
    },
    "BSD-3-Clause": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "Permissive. Retain BSD copyright notice, conditions, and disclaimer."
    },
    "BSD-2-Clause": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "Permissive. Retain BSD 2-clause conditions and disclaimer."
    },
    "GPL-3.0": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": True,
        "compliance_notes": "Copyleft. Any derived works or modifications must be licensed under GPL-3.0."
    },
    "AGPL-3.0": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": True,
        "compliance_notes": "Network copyleft. Service execution triggers source code disclosure obligations."
    },
    "CC0-1.0": {
        "allows_commercial": True,
        "requires_attribution": False,
        "requires_sharealike": False,
        "compliance_notes": "Public domain dedication. Free for all commercial and private use."
    },
    "CC-BY-4.0": {
        "allows_commercial": True,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "Attribution required. Provide appropriate credit and link to the license."
    },
    "Unlicense": {
        "allows_commercial": True,
        "requires_attribution": False,
        "requires_sharealike": False,
        "compliance_notes": "Public domain dedication. No conditions."
    },
    "Custom / Review Required": {
        "allows_commercial": False,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "License text does not match standard open-source templates; manual legal review required."
    },
    "Unspecified / Missing": {
        "allows_commercial": False,
        "requires_attribution": True,
        "requires_sharealike": False,
        "compliance_notes": "No license file found in repository root. Assume all rights reserved under default copyright until clarified."
    }
}

def analyze_repo_license(repo_path: Path) -> dict:
    license_files = []
    for item in repo_path.iterdir():
        if item.is_file() and any(k in item.name.upper() for k in ["LICENSE", "COPYING", "NOTICE"]):
            license_files.append(item)

    detected_spdx = "Unspecified / Missing"
    detected_name = "Unspecified / Missing"
    copyright_holder = "Unknown"
    license_file_path = "None"

    if license_files:
        lic_file = license_files[0]
        license_file_path = str(lic_file.relative_to(BASE_DIR))
        text = lic_file.read_text(encoding="utf-8", errors="ignore")

        # Detect copyright holder
        cr_match = COPYRIGHT_REGEX.search(text)
        if cr_match:
            copyright_holder = cr_match.group(1).strip()

        # Match against patterns
        matched = False
        for name, spdx, pattern in LICENSE_PATTERNS:
            if pattern.search(text):
                detected_name = name
                detected_spdx = spdx
                matched = True
                break
        if not matched:
            detected_name = "Custom / Review Required"
            detected_spdx = "CUSTOM"
    else:
        # Check README.md
        readmes = list(repo_path.glob("README*"))
        if readmes:
            r_text = readmes[0].read_text(encoding="utf-8", errors="ignore")
            for name, spdx, pattern in LICENSE_PATTERNS:
                if pattern.search(r_text):
                    detected_name = f"{name} (in README)"
                    detected_spdx = spdx
                    license_file_path = str(readmes[0].relative_to(BASE_DIR))
                    break

    rules = LICENSE_RULES.get(detected_name, LICENSE_RULES.get(detected_spdx, LICENSE_RULES["Unspecified / Missing"]))

    # Count workflows in repo
    wf_count = len([f for f in repo_path.rglob("*.json") if f.name.lower() not in ["package.json", "tsconfig.json"]])

    return {
        "repo_name": repo_path.name,
        "license_name": detected_name,
        "spdx_id": detected_spdx,
        "license_file_path": license_file_path,
        "copyright_holder": copyright_holder,
        "allows_commercial": rules["allows_commercial"],
        "requires_attribution": rules["requires_attribution"],
        "requires_sharealike": rules["requires_sharealike"],
        "compliance_notes": rules["compliance_notes"],
        "workflows_count": wf_count
    }

def run_license_audit(output_csv: Path = AUDIT_CSV):
    if not SOURCES_DIR.exists():
        print("[-] Sources directory does not exist yet.")
        return []

    repos = [p for p in SOURCES_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]
    print(f"[*] Auditing licenses for {len(repos)} source repositories...")

    records = []
    for repo in repos:
        rec = analyze_repo_license(repo)
        records.append(rec)

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "repo_name", "license_name", "spdx_id", "license_file_path",
            "copyright_holder", "allows_commercial", "requires_attribution",
            "requires_sharealike", "compliance_notes", "workflows_count"
        ])
        for r in records:
            writer.writerow([
                r["repo_name"], r["license_name"], r["spdx_id"], r["license_file_path"],
                r["copyright_holder"], r["allows_commercial"], r["requires_attribution"],
                r["requires_sharealike"], r["compliance_notes"], r["workflows_count"]
            ])

    print(f"[+] License audit report written to {output_csv}")
    for r in records:
        print(f"    - {r['repo_name']}: {r['license_name']} ({r['workflows_count']} workflows) | Attribution required: {r['requires_attribution']}")

    return records

if __name__ == "__main__":
    run_license_audit()
