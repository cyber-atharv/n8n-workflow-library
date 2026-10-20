#!/usr/bin/env python3
"""
scripts/build_search_index.py
Builds web/data/index.json, web/data/stats.json, web/data/categories.json,
and web/data/branding.json from the humanoid workflows/ folder.
"""

import os
import re
import json
import hashlib
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = BASE_DIR / "workflows"
CONFIG_DIR = BASE_DIR / "config"
WEB_DIR = BASE_DIR / "web"
WEB_DATA_DIR = WEB_DIR / "data"

CATEGORIES = json.loads((CONFIG_DIR / "categories.json").read_text(encoding="utf-8"))
BRANDING = json.loads((CONFIG_DIR / "branding.json").read_text(encoding="utf-8"))

def extract_node_type_label(nt: str) -> str:
    if not nt:
        return "Custom Node"
    parts = nt.split(".")
    last = parts[-1]
    return re.sub(r"([A-Z])", r" \1", last).strip().title()

def build_search_index():
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Scanning {WORKFLOWS_DIR} to generate high-performance search index...")

    json_files = list(WORKFLOWS_DIR.rglob("*.json"))
    print(f"[+] Found {len(json_files)} organized workflow JSON files in workflows/.")

    search_records = []
    integration_counts = {}
    trigger_counts = {}
    category_counts = {}
    license_counts = {}
    origin_counts = {"original": 0, "modified": 0, "community": 0}
    security_counts = {"SAFE": 0, "MEDIUM": 0, "HIGH": 0}

    for f in json_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)

            wf_obj = data
            if "workflow" in data and isinstance(data["workflow"], dict) and "nodes" in data["workflow"]:
                wf_obj = data["workflow"]

            nodes = wf_obj.get("nodes", [])
            if not isinstance(nodes, list):
                continue

            folder_name = f.parent.name
            # Extract category name from folder (e.g., "01 - AI Agents & LLMs" -> "AI Agents & LLMs")
            cat_display_name = re.sub(r'^\d+\s*-\s*', '', folder_name)

            title = data.get("name") or wf_obj.get("name") or f.stem
            title = re.sub(r'^\d+[\s_-]*', '', title)

            # Check if original or modified
            flowforge_meta = data.get("meta", {}).get("flowforge", {})
            is_orig = "original" in folder_name.lower() or flowforge_meta.get("is_original", False)
            is_mod = "enhanced" in folder_name.lower() or "modified" in folder_name.lower() or flowforge_meta.get("is_modified", False)

            if is_orig:
                origin_type = "original"
                author = BRANDING["brand"]["maintainer"]
                source_url = BRANDING["brand"]["github_repo_url"]
                license_type = "MIT (Atharv Original)"
            elif is_mod:
                origin_type = "modified"
                author = flowforge_meta.get("original_author", "Community Contributor")
                source_url = flowforge_meta.get("original_source", "https://github.com")
                license_type = flowforge_meta.get("original_license", "Open Source (Enhanced)")
            else:
                origin_type = "community"
                author = "Open Source Community"
                source_url = "https://github.com/n8n-io/n8n"
                license_type = "MIT / Apache-2.0 / CC-BY"

            origin_counts[origin_type] = origin_counts.get(origin_type, 0) + 1

            nodes_summary = []
            integrations = set()
            triggers = set()
            creds = set()
            has_dangerous = False

            for node in nodes:
                if not isinstance(node, dict):
                    continue
                n_name = node.get("name", "Node")
                nt = node.get("type", "")

                if nt == "n8n-nodes-base.executeCommand":
                    has_dangerous = True

                nodes_summary.append({
                    "name": n_name,
                    "type": nt,
                    "label": extract_node_type_label(nt)
                })

                lower_nt = nt.lower()
                if "openai" in lower_nt or "chatgpt" in lower_nt:
                    integrations.add("OpenAI")
                elif "anthropic" in lower_nt or "claude" in lower_nt:
                    integrations.add("Claude")
                elif "gemini" in lower_nt:
                    integrations.add("Gemini")
                elif "slack" in lower_nt:
                    integrations.add("Slack")
                elif "telegram" in lower_nt:
                    integrations.add("Telegram")
                elif "discord" in lower_nt:
                    integrations.add("Discord")
                elif "whatsapp" in lower_nt:
                    integrations.add("WhatsApp")
                elif "googlesheets" in lower_nt or "sheets" in lower_nt:
                    integrations.add("Google Sheets")
                elif "gmail" in lower_nt:
                    integrations.add("Gmail")
                elif "airtable" in lower_nt:
                    integrations.add("Airtable")
                elif "notion" in lower_nt:
                    integrations.add("Notion")
                elif "hubspot" in lower_nt:
                    integrations.add("HubSpot")
                elif "salesforce" in lower_nt:
                    integrations.add("Salesforce")
                elif "postgres" in lower_nt:
                    integrations.add("PostgreSQL")
                elif "mysql" in lower_nt:
                    integrations.add("MySQL")
                elif "redis" in lower_nt:
                    integrations.add("Redis")
                elif "shopify" in lower_nt:
                    integrations.add("Shopify")
                elif "stripe" in lower_nt:
                    integrations.add("Stripe")
                elif "github" in lower_nt:
                    integrations.add("GitHub")
                elif "jira" in lower_nt:
                    integrations.add("Jira")
                elif "webhook" in lower_nt:
                    integrations.add("Webhook")
                elif "httprequest" in lower_nt:
                    integrations.add("HTTP Request")
                elif "pinecone" in lower_nt:
                    integrations.add("Pinecone")
                elif "qdrant" in lower_nt:
                    integrations.add("Qdrant")
                elif "code" in lower_nt or "function" in lower_nt:
                    integrations.add("Custom Code")

                if "trigger" in lower_nt or "webhook" in lower_nt:
                    if "schedule" in lower_nt or "cron" in lower_nt:
                        triggers.add("Schedule / Cron")
                    elif "webhook" in lower_nt:
                        triggers.add("Webhook")
                    elif "chat" in lower_nt:
                        triggers.add("Chat")
                    elif "email" in lower_nt or "gmail" in lower_nt:
                        triggers.add("Email")
                    elif "form" in lower_nt:
                        triggers.add("Form")
                    elif "manual" in lower_nt:
                        triggers.add("Manual")
                    else:
                        triggers.add("Event")

                c = node.get("credentials")
                if c and isinstance(c, dict):
                    for ck in c.keys():
                        creds.add(ck)

            if not triggers:
                triggers.add("Manual")

            nc = len(nodes)
            if nc <= 5:
                complexity = "Simple"
            elif nc <= 15:
                complexity = "Moderate"
            else:
                complexity = "Advanced"

            risk = "MEDIUM" if has_dangerous else "SAFE"
            val_status = "Requires manual review" if has_dangerous else "Structurally plausible n8n workflow"
            security_counts[risk] += 1

            desc = data.get("description") or wf_obj.get("description") or ""
            if not desc or len(desc.strip()) < 15:
                int_text = ", ".join(list(integrations)[:3]) if integrations else "core n8n nodes"
                desc = f"Enterprise workflow in {cat_display_name} integrating {int_text}. Automated execution with {list(triggers)[0]}."

            category_counts[cat_display_name] = category_counts.get(cat_display_name, 0) + 1
            license_counts[license_type] = license_counts.get(license_type, 0) + 1
            for integ in integrations:
                integration_counts[integ] = integration_counts.get(integ, 0) + 1
            for trig in triggers:
                trigger_counts[trig] = trigger_counts.get(trig, 0) + 1

            workflow_id = hashlib.md5(f"{folder_name}_{f.stem}".encode('utf-8')).hexdigest()[:10]

            rel_path = str(f.relative_to(BASE_DIR)).replace("\\", "/")

            record = {
                "id": workflow_id,
                "title": title.strip(),
                "slug": f.stem,
                "category_id": folder_name,
                "category_name": cat_display_name,
                "node_count": nc,
                "complexity": complexity,
                "integrations": sorted(list(integrations)),
                "triggers": sorted(list(triggers)),
                "credentials_required": sorted(list(creds)),
                "has_credentials": len(creds) > 0,
                "description": desc.strip(),
                "origin_type": origin_type,
                "is_original": is_orig,
                "is_modified": is_mod,
                "original_author": author,
                "maintainer": BRANDING["brand"]["maintainer"],
                "source_url": source_url,
                "license": license_type,
                "validation_status": val_status,
                "risk_level": risk,
                "catalog_rel_path": rel_path,
                "nodes_summary": nodes_summary[:8]
            }
            search_records.append(record)

        except Exception:
            continue

    order_map = {"original": 0, "modified": 1, "community": 2}
    search_records.sort(key=lambda x: (order_map.get(x["origin_type"], 2), x["title"]))

    (WEB_DATA_DIR / "index.json").write_text(json.dumps(search_records, indent=2), encoding="utf-8")
    print(f"[+] Saved {len(search_records)} searchable workflows to {WEB_DATA_DIR / 'index.json'}")

    stats = {
        "total_workflows": len(search_records),
        "total_categories": len(category_counts),
        "categories": sorted([{"name": k, "count": v} for k, v in category_counts.items()], key=lambda x: x["count"], reverse=True),
        "integrations": sorted([{"name": k, "count": v} for k, v in integration_counts.items()], key=lambda x: x["count"], reverse=True),
        "triggers": sorted([{"name": k, "count": v} for k, v in trigger_counts.items()], key=lambda x: x["count"], reverse=True),
        "licenses": sorted([{"name": k, "count": v} for k, v in license_counts.items()], key=lambda x: x["count"], reverse=True),
        "origins": origin_counts,
        "security": security_counts
    }
    (WEB_DATA_DIR / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[+] Saved aggregate stats to {WEB_DATA_DIR / 'stats.json'}")

    shutil.copy(CONFIG_DIR / "categories.json", WEB_DATA_DIR / "categories.json")
    shutil.copy(CONFIG_DIR / "branding.json", WEB_DATA_DIR / "branding.json")
    print(f"[+] Copied configuration assets to {WEB_DATA_DIR}")

if __name__ == "__main__":
    build_search_index()
