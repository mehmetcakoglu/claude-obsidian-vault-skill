---
title: Global vault ingest log
date: 2026-04-23
status: active
---

# Global Vault — Ingest Log

Append one entry per ingest or lint, newest at the bottom.

Template:

```
## YYYY-MM-DD — ingest #N — <slug>
- **Source**: <path> (<size>)
- **Topics**: comma-separated tags
- **Pages created**:
  - [[sources/sessions/...]]
  - [[decisions/...]]
- **Skipped/excluded**: what was filtered out and why (secrets, noise, NDA…)
- **Commit**: `<hash>`
```
