# Attribution, Authorship & Provenance Notice

The FlowForge n8n Workflow Library is committed to ethical open-source stewardship. We rigorously preserve original creator credits, upstream repository URLs, license notices, and transparent modification changelogs.

---

## 1. Authorship Classification Framework

Every workflow in this library is categorized under one of three strict tiers:

### Tier 1: FlowForge Originals (`library/original/`)
- **Author**: FlowForge Architecture Team
- **Maintainer**: FlowForge Studio
- **License**: MIT License
- **Description**: Independently designed and authored enterprise automations (e.g. Multi-Agent RAG Researcher, Autonomous Customer Support Escalation, Self-Healing Infrastructure Watchdog).

### Tier 2: FlowForge Enhanced & Hardened (`library/modified/`)
- **Original Author**: Credited individual or community contributor (e.g., ScraperNode contributor, Enes Cingöz)
- **Modifier / Adapter**: FlowForge Architecture Team
- **Original License**: Preserved (MIT, Apache-2.0, CC-BY-4.0)
- **Modifications Documented**: Upgraded from legacy n8n node formats, added cryptographic HMAC webhook verification, implemented AI prompt engineering, and hardened security sanitization. Full modification diffs and changelogs are embedded in each workflow's `meta.flowforge` block and manifest.

### Tier 3: Curated Open Source Community (`library/catalog/`)
- **Original Author**: Original upstream maintainer / community
- **Curator / Indexer**: FlowForge Studio
- **License**: Retained under each file's upstream open-source license.
- **Modifications**: Normalized filenames, structured metadata, category mapping, and security auditing. Original node definitions, logic, and credentials structures are preserved.

---

## 2. Upstream Contributor Credits

We gratefully acknowledge the contributions of the following authors and open-source communities:

| Author / Organization | Source Repository | Primary License |
| :--- | :--- | :---: |
| **ScraperNode** | [awesome-n8n-templates](https://github.com/ScraperNode/awesome-n8n-templates) | MIT |
| **zengfr** | [n8n-workflow-all-templates](https://github.com/zengfr/n8n-workflow-all-templates) | Apache-2.0 |
| **aboalrejalai** | [n8n-workflows](https://github.com/aboalrejalai/n8n-workflows) | MIT |
| **Danitilahun** | [n8n-workflow-templates](https://github.com/Danitilahun/n8n-workflow-templates) | Open Source |
| **Enes Cingöz** | [awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates) | CC-BY-4.0 |
| **n8n Community** | [n8n Community Templates](https://n8n.io/workflows/) | Various |

---

## 3. Modification Audit Log for Adapted Workflows

### Workflow: `enhanced-shopify-abandoned-cart-recovery.json`
- **Original Source**: `ScraperNode/awesome-n8n-templates`
- **Original Author**: Community Contributor (MIT License)
- **Modifier**: FlowForge Architecture Team
- **Modifications**:
  1. Migrated legacy webhook schema to modern n8n v2 format.
  2. Implemented HMAC SHA-256 header signature validation node.
  3. Replaced static template strings with dynamic OpenAI LLM copy generation.
  4. Sanitized payload parameters to eliminate prototype poisoning risks.

### Workflow: `hardened-github-security-vulnerability-alert.json`
- **Original Source**: `enescingoz/awesome-n8n-templates`
- **Original Author**: Enes Cingöz (CC-BY-4.0)
- **Modifier**: FlowForge Architecture Team
- **Modifications**:
  1. Added CVE severity routing filter to suppress noise from low/informational warnings.
  2. Integrated direct Jira issue creation API node for SecOps incident tracking.
  3. Applied Slack message payload sanitization and masked bearer tokens.

---

## 4. Manifest Cross-Reference

Full machine-readable provenance details for all 1,032+ workflows are available in:
- [WORKFLOW_MANIFEST.csv](file:///d:/n8n/workflows/WORKFLOW_MANIFEST.csv)
- [workflow_manifest.json](file:///d:/n8n/workflows/workflow_manifest.json)
- [license_audit.csv](file:///d:/n8n/workflows/license_audit.csv)
