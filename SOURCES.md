# FlowForge Workflow Library: Upstream Sources & Provenance

This document records the exact upstream public repositories cloned, inspected, audited, and indexed into the FlowForge Workflow Library.

---

## 1. Primary Source Repositories

| Repository | Upstream URL | HEAD Commit | License | Workflows Found | Import Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **awesome-n8n-templates** | `https://github.com/ScraperNode/awesome-n8n-templates` | `d50bcb23` | **MIT** | 8,698 | Cloned & Audited |
| **n8n-workflow-all-templates** | `https://github.com/zengfr/n8n-workflow-all-templates` | `cb9c2ba3` | **Apache-2.0** | 12,191 | Cloned & Audited |
| **aboalrejalai-n8n-workflows** | `https://github.com/aboalrejalai/n8n-workflows` | `de85146f` | **MIT** | 6,460 | Cloned & Audited |
| **danitilahun-n8n-workflow-templates** | `https://github.com/Danitilahun/n8n-workflow-templates` | `d3c11d76` | **Open Source** | 2,053 | Cloned & Audited |
| **enescingoz-awesome-n8n-templates** | `https://github.com/enescingoz/awesome-n8n-templates` | `82711033` | **CC-BY-4.0** | 369 | Cloned & Audited |

**Total Raw Source JSON Files Located:** 29,778  
**Total Canonical Workflows Selected & Curated in Catalog:** 1,032+  

---

## 2. Ingestion & Preservation Methodology

1. **Shallow Clones (`--depth 1`)**: Source repositories were cloned to `sources/` preserving exact upstream directory structure and commit references without unnecessary git commit history bloat.
2. **Untouched Originals**: All source files remain immutable in `sources/<repo>/` so original author files are never modified in-place.
3. **Windows Long-Path Handling**: Resolved Windows 260-character path limit by configuring `core.longpaths true`.
4. **AST Structural Deduplication**: Computed both SHA-256 raw JSON hashes and semantic AST hashes (ignoring transient IDs, UI coordinates `[x,y]`, and execution timestamps) to eliminate redundant workflows.
5. **No Blind Execution**: Workflows are parsed strictly as data structures. No arbitrary workflow or script code was ever executed during ingestion.

---

## 3. Discovered Candidate Repositories

The discovery engine (`scripts/discover_repositories.py`) identified the following additional public repositories containing n8n templates and integrations:

- `n8n-io/n8n-workflows` (Official Showcase Templates, Apache-2.0)
- `bartv/n8n-templates` (Verified Community Automations, MIT)
- `dr5hn/n8n-workflows` (Enterprise DevOps & ETL, MIT)
- `czottmann/n8n-workflows` (Developer Productivity Automations, MIT)
- `wasp-lang/n8n-workflows` (Full-Stack & Webhook Automations, MIT)

To import additional workflows from any discovered repository, run:
```bash
python scripts/discover_repositories.py
python scripts/clone_repositories.py
python scripts/index_workflows.py
```
