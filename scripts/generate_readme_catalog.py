#!/usr/bin/env python3
"""
scripts/generate_readme_catalog.py
Generates WORKFLOWS.md containing complete clickable catalog of all 1,044+ workflows,
and creates the README.md browsable showcase directory.
"""

import os
import re
import json
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = BASE_DIR / "workflows"
INDEX_JSON = BASE_DIR / "web" / "data" / "index.json"
WORKFLOWS_MD = BASE_DIR / "WORKFLOWS.md"
README_MD = BASE_DIR / "README.md"

def encode_path(p: str) -> str:
    # URL encode path segments for markdown links
    parts = p.replace("\\", "/").split("/")
    return "/".join(urllib.parse.quote(part) for part in parts)

def build_catalogs():
    if not INDEX_JSON.exists():
        print(f"[-] {INDEX_JSON} missing.")
        return

    items = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    print(f"[*] Loaded {len(items)} workflows from index. Building catalog documentation...")

    # Group workflows by category folder
    grouped = {}
    for item in items:
        cat_folder = item.get("category_id") or "Other"
        grouped.setdefault(cat_folder, []).append(item)

    # Sort categories alphabetically / numbered
    sorted_cats = sorted(grouped.keys())

    # 1. Build WORKFLOWS.md (Complete 1,044+ clickable directory)
    lines_full = []
    lines_full.append("# 📚 Complete Directory of n8n Workflows (1,044+ Index)")
    lines_full.append("")
    lines_full.append("Click on any workflow title below to directly open and inspect its raw JSON definition.")
    lines_full.append("To import any workflow into n8n: open the JSON file, copy the contents, and press **Ctrl+V** on your n8n canvas.")
    lines_full.append("")
    lines_full.append("## Quick Category Index")
    lines_full.append("")

    for cat in sorted_cats:
        count = len(grouped[cat])
        anchor = cat.lower().replace(" ", "-").replace("&", "").replace(",", "").replace("(", "").replace(")", "").replace("--", "-")
        lines_full.append(f"- [{cat}](#{anchor}) ({count} workflows)")

    lines_full.append("")
    lines_full.append("---")
    lines_full.append("")

    for cat in sorted_cats:
        wfs = grouped[cat]
        cat_clean = re.sub(r'^\d+\s*-\s*', '', cat)
        folder_link = encode_path(f"workflows/{cat}")
        
        lines_full.append(f"## {cat}")
        lines_full.append(f"📂 **Folder:** [`workflows/{cat}/`]({folder_link}) | **Total Workflows:** {len(wfs)}")
        lines_full.append("")
        lines_full.append("| Workflow Name | Nodes | Trigger | Key Integrations | Direct Link |")
        lines_full.append("| :--- | :---: | :--- | :--- | :---: |")

        for wf in wfs:
            rel_path = wf.get("catalog_rel_path", "")
            enc_link = encode_path(rel_path)
            title = wf.get("title", "Workflow").replace("|", "-")
            nodes = wf.get("node_count", 0)
            trigs = ", ".join(wf.get("triggers", [])[:1]) or "Manual"
            integs = ", ".join(wf.get("integrations", [])[:3]) or "Core"
            lines_full.append(f"| [{title}]({enc_link}) | {nodes} | {trigs} | {integs} | [View JSON]({enc_link}) |")

        lines_full.append("")
        lines_full.append("---")
        lines_full.append("")

    WORKFLOWS_MD.write_text("\n".join(lines_full), encoding="utf-8")
    print(f"[+] Successfully generated complete clickable index: {WORKFLOWS_MD}")

    # 2. Build README.md with Featured Showcase & Direct Hyperlinks
    readme_content = f"""# ⚡ Atharv Automation Studio | Enterprise n8n Workflow Library

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Workflows](https://img.shields.io/badge/Workflows-1%2C044%2B%20Curated-coral)](workflows/)
[![Catalog Index](https://img.shields.io/badge/Full%20Catalog-WORKFLOWS.md-purple)](WORKFLOWS.md)
[![Maintainer](https://img.shields.io/badge/Maintainer-cyber--atharv-black)](https://github.com/cyber-atharv)

A production-ready collection of **1,044+ verified n8n workflows** organized into **30 clean humanoid categories**. Every single workflow can be clicked, analyzed, and imported onto your canvas with one click.

👉 **[Browse the Full 1,044+ Clickable Workflow Directory (WORKFLOWS.md)](WORKFLOWS.md)**

---

## ⚡ How to Import Any Workflow into n8n

1. **Click on any workflow link below** to view its JSON file.
2. **Copy the JSON**: Click the "Copy raw file" button on GitHub (or select all and copy).
3. **Paste onto Canvas**: Open any n8n canvas (Cloud or Self-Hosted) and press **`Ctrl+V`** (or **`Cmd+V`**).
4. All nodes, parameters, and connection wires will appear instantly!

---

## 🌟 Flagship Originals & Hardened Architectures

Handcrafted and security-hardened enterprise workflows built from scratch:

| Workflow Architecture | Category | Nodes | Description | Direct Link |
| :--- | :--- | :---: | :--- | :---: |
| **[Multi-Agent RAG Research & Knowledge Synthesis](<workflows/00 - Atharv Flagship Originals/Atharv Flagship - Multi-Agent RAG Research & Knowledge Synthesis.json>)** | AI & Research | 6 | Autonomous signal collector, GPT-4o reasoning agent, Qdrant vector search & Slack digest. | [View JSON](<workflows/00 - Atharv Flagship Originals/Atharv Flagship - Multi-Agent RAG Research & Knowledge Synthesis.json>) |
| **[Autonomous Lead Enrichment & HubSpot Sync](<workflows/00 - Atharv Flagship Originals/Atharv Flagship - Autonomous Lead Enrichment & HubSpot Sync.json>)** | Lead Gen & CRM | 5 | Inbound lead webhook, Hunter domain intelligence, AI ICP fit scoring & HubSpot CRM upsert. | [View JSON](<workflows/00 - Atharv Flagship Originals/Atharv Flagship - Autonomous Lead Enrichment & HubSpot Sync.json>) |
| **[Self-Healing DevOps Infrastructure Watchdog](<workflows/00 - Atharv Flagship Originals/Atharv Flagship - Self-Healing DevOps Infrastructure Watchdog.json>)** | DevOps & Sentry | 5 | Polling sentry, endpoint health evaluation, automated Kubernetes pod restart webhook & Discord alert. | [View JSON](<workflows/00 - Atharv Flagship Originals/Atharv Flagship - Self-Healing DevOps Infrastructure Watchdog.json>) |
| **[Shopify Abandoned Cart Recovery Engine](<workflows/00 - Atharv Enhanced & Hardened/Atharv Enhanced - Shopify Abandoned Cart Recovery Engine.json>)** | E-Commerce | 4 | Hardened with cryptographic HMAC SHA-256 header verification, OpenAI personalized recovery copy. | [View JSON](<workflows/00 - Atharv Enhanced & Hardened/Atharv Enhanced - Shopify Abandoned Cart Recovery Engine.json>) |
| **[Hardened GitHub Security Alert & Jira Escalation](<workflows/00 - Atharv Enhanced & Hardened/Atharv Enhanced - Hardened GitHub Security Alert & Jira Escalation.json>)** | Security & DevOps | 4 | Automated Dependabot CVE triage, severity routing filter, Jira bug ticket creation & SecOps alert. | [View JSON](<workflows/00 - Atharv Enhanced & Hardened/Atharv Enhanced - Hardened GitHub Security Alert & Jira Escalation.json>) |

---

## 🗂️ Browse Workflows by Category

Click on any workflow name below to jump directly to its file:

"""

    # Add Category Sections to README
    for cat in sorted_cats:
        if "00 -" in cat:
            continue # already featured in top table
        wfs = grouped[cat]
        cat_clean = re.sub(r'^\d+\s*-\s*', '', cat)
        folder_link = encode_path(f"workflows/{cat}")

        readme_content += f"### [{cat}]({folder_link}) ({len(wfs)} workflows)\n\n"
        readme_content += "| Featured Workflow | Nodes | Trigger | Integrations | Link |\n"
        readme_content += "| :--- | :---: | :--- | :--- | :---: |\n"

        # Show up to 4 featured workflows with links
        for wf in wfs[:4]:
            rel_path = wf.get("catalog_rel_path", "")
            enc_link = encode_path(rel_path)
            title = wf.get("title", "Workflow").replace("|", "-")
            nodes = wf.get("node_count", 0)
            trigs = ", ".join(wf.get("triggers", [])[:1]) or "Manual"
            integs = ", ".join(wf.get("integrations", [])[:3]) or "Core"
            readme_content += f"| [{title}]({enc_link}) | {nodes} | {trigs} | {integs} | [View JSON]({enc_link}) |\n"

        readme_content += f"\n👉 *[View all {len(wfs)} workflows in {cat_clean} →]({folder_link})*\n\n"

    readme_content += """---

## 🖥️ Interactive Web UI & Flow Visualizer

This repository includes a standalone local web application with an interactive SVG node flow visualizer:

```bash
# Start local server (Python 3.10+)
python scripts/serve.py 8080
```
Open **`http://localhost:8080/web/`** in your browser.

- Instant search across all 1,044+ workflows
- Interactive flowchart graph with zoom, pan, and node inspection
- 1-click copy button for instant canvas pasting
- Filter by integrations, triggers, complexity, and credentials

---

## 🛡️ License

Created, designed, and curated by [Atharv Hogade](https://github.com/cyber-atharv).  
Licensed under the [MIT License](LICENSE).
"""

    README_MD.write_text(readme_content, encoding="utf-8")
    print(f"[+] Successfully generated README.md with direct clickable links: {README_MD}")

if __name__ == "__main__":
    build_catalogs()
