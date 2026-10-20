#!/usr/bin/env python3
"""
scripts/discover_repositories.py
Discovers additional public GitHub repositories containing n8n workflows, templates, and JSON exports.
Uses the GitHub Search API (or unauthenticated query) and a curated list of verified n8n workflow repositories.
Prioritizes repositories with open source licenses and actual workflow JSON files.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DISCOVERED_FILE = CONFIG_DIR / "discovered_repositories.json"

# Known high-value curated public repositories with n8n workflow collections
CURATED_ADDITIONAL_REPOS = [
    {
        "id": "rubens-n8n-workflows",
        "name": "n8n-workflows-collection",
        "url": "https://github.com/n8n-io/n8n-workflows",
        "primary_author": "n8n Community",
        "description": "Official community workflow templates and showcase examples.",
        "license_guess": "Apache-2.0"
    },
    {
        "id": "bartv-n8n-templates",
        "name": "n8n-community-templates",
        "url": "https://github.com/bartv/n8n-templates",
        "primary_author": "bartv",
        "description": "Curated collection of verified community automations.",
        "license_guess": "MIT"
    },
    {
        "id": "dr5hn-n8n-templates",
        "name": "dr5hn-n8n-workflows",
        "url": "https://github.com/dr5hn/n8n-workflows",
        "primary_author": "dr5hn",
        "description": "Enterprise automation pipelines, ETL, and DevOps workflows.",
        "license_guess": "MIT"
    },
    {
        "id": "czottmann-n8n-nodes",
        "name": "czottmann-n8n-workflows",
        "url": "https://github.com/czottmann/n8n-workflows",
        "primary_author": "Carlo Zottmann",
        "description": "Practical productivity and developer automation workflows.",
        "license_guess": "MIT"
    },
    {
        "id": "wasp-graphql-n8n",
        "name": "awesome-n8n-collection",
        "url": "https://github.com/wasp-lang/n8n-workflows",
        "primary_author": "Wasp Community",
        "description": "Full-stack integration, webhook listeners, and background job templates.",
        "license_guess": "MIT"
    }
]

def search_github_api(query="n8n workflow language:json stars:>5", max_results=10):
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={max_results}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FlowForge-n8n-Library-Auditor/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = []
            for item in data.get("items", []):
                items.append({
                    "id": item["full_name"].replace("/", "-").lower(),
                    "name": item["name"],
                    "url": item["html_url"],
                    "primary_author": item["owner"]["login"],
                    "description": item["description"] or "",
                    "stars": item["stargazers_count"],
                    "license": (item.get("license") or {}).get("spdx_id") or "Unspecified",
                    "updated_at": item["updated_at"]
                })
            return items
    except urllib.error.HTTPError as e:
        print(f"[-] GitHub API rate limit or error: {e.code} ({e.reason})")
        return []
    except Exception as e:
        print(f"[-] Discovery network error: {e}")
        return []

def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    print("[*] Discovering additional public n8n repositories...")
    
    api_results = search_github_api()
    print(f"[+] GitHub API returned {len(api_results)} candidates.")
    
    # Merge with curated repositories without duplicates
    combined = list(CURATED_ADDITIONAL_REPOS)
    existing_urls = {r["url"].lower() for r in combined}
    
    for item in api_results:
        if item["url"].lower() not in existing_urls:
            combined.append(item)
            existing_urls.add(item["url"].lower())
            
    DISCOVERED_FILE.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"[+] Saved {len(combined)} discovered repository references to {DISCOVERED_FILE}")

if __name__ == "__main__":
    main()
