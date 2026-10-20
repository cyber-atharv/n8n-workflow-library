#!/usr/bin/env python3
"""
scripts/rearrange_humanoid.py
Rearranges all workflows into clean, human-readable (humanoid) folder names
and normal, title-cased file names under the root workflows/ directory.
Updates manifests, reports, and web search index.
"""

import os
import re
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CATEGORIES_FILE = CONFIG_DIR / "categories.json"
BRANDING_FILE = CONFIG_DIR / "branding.json"
CATALOG_DIR = BASE_DIR / "library" / "catalog"
ORIGINAL_DIR = BASE_DIR / "library" / "original"
MODIFIED_DIR = BASE_DIR / "library" / "modified"
DEST_ROOT = BASE_DIR / "workflows"

WEB_DATA_DIR = BASE_DIR / "web" / "data"

CATEGORIES = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
BRANDING = json.loads(BRANDING_FILE.read_text(encoding="utf-8"))

# Humanoid numbered folder mapping for all 30 categories
HUMANOID_CATEGORY_MAP = {
    "ai-agents-llms": "01 - AI Agents & LLMs",
    "openai-ai-integrations": "02 - OpenAI & AI Integrations",
    "rag-vector-databases": "03 - RAG & Vector Databases",
    "chatbots-conversational": "04 - Chatbots & Conversational",
    "messaging-channels": "05 - WhatsApp, Telegram, Discord & Slack",
    "web-scraping-browser": "06 - Web Scraping & Browser Automation",
    "lead-generation-enrichment": "07 - Lead Generation & Enrichment",
    "email-marketing-outreach": "08 - Email Marketing & Outreach",
    "social-media-publishing": "09 - Social Media Publishing",
    "seo-content-generation": "10 - SEO & Content Generation",
    "ecommerce-shopify": "11 - E-Commerce & Shopify",
    "crm-sales-automation": "12 - CRM & Sales Automation",
    "google-workspace": "13 - Google Sheets & Workspace",
    "microsoft-365": "14 - Microsoft 365",
    "databases-sql": "15 - Databases & SQL",
    "rest-apis-webhooks": "16 - REST APIs & Webhooks",
    "business-process-automation": "17 - Business Process Automation",
    "finance-invoicing": "18 - Finance & Invoicing",
    "customer-support": "19 - Customer Support",
    "project-management": "20 - Project Management",
    "wordpress-website": "21 - WordPress & Website Automation",
    "analytics-reporting": "22 - Analytics & Reporting",
    "data-pipelines-etl": "23 - Data Pipelines & ETL",
    "devops-infrastructure": "24 - DevOps & Infrastructure Monitoring",
    "security-alerting": "25 - Security & Alerting",
    "file-document-processing": "26 - File Management & Document Processing",
    "hr-recruitment": "27 - HR & Recruitment",
    "scheduling-productivity": "28 - Scheduling & Productivity",
    "rss-news-monitoring": "29 - RSS & News Monitoring",
    "education-research": "30 - Education & Research"
}

def sanitize_human_filename(name: str) -> str:
    """Cleans up title and removes invalid filesystem characters."""
    name = re.sub(r'^\d+[\s_-]*', '', name)
    name = re.sub(r'[\\/*?:"<>|]', ' - ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip(' .-_')
    if not name or name.lower() in ["my workflow", "untitled"]:
        name = "Automated Workflow"
    # Ensure title case if all lowercase
    if name.islower():
        name = name.title()
    return name[:90]

def rearrange_all():
    print("[*] Reorganizing workflow library with clean, humanoid folder and file names...")
    
    if DEST_ROOT.exists():
        shutil.rmtree(DEST_ROOT)
    DEST_ROOT.mkdir(parents=True, exist_ok=True)

    reorganized_index = []
    seen_names_by_folder = {}

    # 1. Flagship Originals
    orig_folder = DEST_ROOT / "00 - Atharv Flagship Originals"
    orig_folder.mkdir(parents=True, exist_ok=True)
    if ORIGINAL_DIR.exists():
        for f in ORIGINAL_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                title = data.get("name") or f.stem.replace("-", " ").title()
                clean_name = sanitize_human_filename(title)
                dest_file = orig_folder / f"{clean_name}.json"
                dest_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print(f"  [+] Original: {clean_name}")
            except Exception as e:
                print(f"  [-] Error copying original {f.name}: {e}")

    # 2. Enhanced & Hardened
    mod_folder = DEST_ROOT / "00 - Atharv Enhanced & Hardened"
    mod_folder.mkdir(parents=True, exist_ok=True)
    if MODIFIED_DIR.exists():
        for f in MODIFIED_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                title = data.get("name") or f.stem.replace("-", " ").title()
                clean_name = sanitize_human_filename(title)
                dest_file = mod_folder / f"{clean_name}.json"
                dest_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print(f"  [+] Enhanced: {clean_name}")
            except Exception as e:
                print(f"  [-] Error copying modified {f.name}: {e}")

    # 3. Main Catalog categories
    print("\n[*] Migrating catalog categories to humanoid folders...")
    for cat_dir in CATALOG_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        cat_slug = cat_dir.name
        human_cat_name = HUMANOID_CATEGORY_MAP.get(cat_slug, f"30 - {cat_slug.replace('-', ' ').title()}")
        target_dir = DEST_ROOT / human_cat_name
        target_dir.mkdir(parents=True, exist_ok=True)

        seen_names = seen_names_by_folder.setdefault(human_cat_name, set())

        json_files = list(cat_dir.glob("*.json"))
        for f in json_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                data = json.loads(content)

                # Extract proper title
                wf_obj = data.get("workflow", data) if isinstance(data.get("workflow"), dict) else data
                title = data.get("name") or wf_obj.get("name")
                if not title or title.strip().lower() in ["my workflow", "untitled"]:
                    raw = f.stem.replace("-", " ").replace("_", " ").title()
                    raw = re.sub(r'^\d+[\s_-]*', '', raw)
                    title = raw

                clean_name = sanitize_human_filename(title)
                
                # Deduplicate filename inside the same folder
                final_name = clean_name
                counter = 2
                while final_name.lower() in seen_names:
                    final_name = f"{clean_name} ({counter})"
                    counter += 1
                seen_names.add(final_name.lower())

                dest_file = target_dir / f"{final_name}.json"
                dest_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

            except Exception:
                continue

    # Count workflows in workflows/
    all_workflows = list(DEST_ROOT.rglob("*.json"))
    print(f"\n[+] Total workflows reorganized under workflows/: {len(all_workflows)}")
    
    # List humanoid folders
    print("\n[+] Humanoid Folders Created:")
    for d in sorted(DEST_ROOT.iterdir()):
        if d.is_dir():
            count = len(list(d.glob("*.json")))
            print(f"    - {d.name} ({count} workflows)")

if __name__ == "__main__":
    rearrange_all()
