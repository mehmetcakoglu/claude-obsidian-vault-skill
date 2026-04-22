---
title: {{PROJECT_NAME}} vault ingest log
date: {{CURRENT_DATE}}
status: active
---

# {{PROJECT_NAME}} Vault — Ingest Log

Append one entry per ingest or lint, newest at the bottom.

Template:

```
## YYYY-MM-DD — ingest #N — <slug>
- **Source**: <path> (<size>)
- **Topics**: comma-separated tags
- **Pages created**:
  - [[sources/sessions/...]]
  - [[decisions/...]]
  - [[bugs/...]]
- **Skipped/excluded**: what was filtered out and why (secrets, noise, NDA…)
- **Commit**: `<hash>`
```
