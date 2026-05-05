# vault plugin — Technical Documentation

> v1.0.0 · [GitHub](https://github.com/mehmetcakoglu/claude-obsidian-vault-skill) · [README](../README.md)

---

## Overview

The vault plugin is a knowledge persistence layer for Claude Code. It archives Claude Code sessions into Obsidian-compatible Markdown wikis and injects relevant context at the start of every session so Claude can reference past decisions, bugs, and lessons without re-discovering them.

---

## Architecture

### Dual-vault model

```
~/.claude/projects/<project>/          ← raw JSONL transcripts (Claude Code)
         │
         ▼
~/Global Claude Vault/                 ← global vault (cross-project knowledge)
   sources/sessions/                   ← one page per session
   decisions/                          ← cross-project architectural decisions
   entities/                           ← tools, services, frameworks
   concepts/                           ← patterns, idioms, mental models
   lessons/                            ← failure stories: symptom → root cause → fix
   syntheses/                          ← lint/doctor reports, filed-back answers
   archive/                            ← superseded pages (never deleted)
   state/                              ← pending.md, ingested.txt, ingest-sizes.txt …
   scripts/                            ← vault-context.py, scan-sessions.py
         │
         ▼ (if project has docs/vault/CLAUDE.md)
<project>/docs/vault/                  ← project vault (project-specific knowledge)
   sources/sessions/
   decisions/
   entities/
   concepts/
   bugs/
   lessons/
   syntheses/
```

Every ingested session is routed automatically:
- Project has `docs/vault/CLAUDE.md` → **project vault**
- Otherwise → **global vault**

### Session lifecycle

```
Claude Code session ends
        │
        ▼ (~10 min later, JSONL flushed to disk)
scan-sessions.py runs at next SessionStart
        │
        ▼
state/pending.md updated (new sessions listed)
        │
        ▼
/vault:ingest (or auto_ingest=true)
        │
        ├─ parses JSONL via ctx_execute
        ├─ writes sources/sessions/YYYY-MM-DD-<slug>.md
        ├─ writes decisions/, entities/, concepts/, bugs/, lessons/ as needed
        ├─ updates index.md + log.md
        └─ appends to state/ingested.txt + state/ingest-sizes.txt
```

### SessionStart hook

At every session start, `vault-context.py` runs synchronously and injects a `<system-reminder>` block containing:

1. Global vault `index.md` (up to 6,000 chars)
2. Project entity page (if exists, up to 3,000 chars)
3. Last 3 project sessions (summaries)
4. Pending queue count
5. Update notice (if newer version available on GitHub)
6. Auto-ingest instruction (if `auto_ingest=true`)

This costs ~1,000–2,000 tokens per session but eliminates re-discovery across sessions.

---

## File layout reference

### Global vault state files

| File | Purpose |
|---|---|
| `state/pending.md` | Queue of sessions awaiting ingest (updated by scan-sessions.py) |
| `state/ingested.txt` | Registry of all ingested session IDs (shared across both vaults) |
| `state/ingest-sizes.txt` | JSONL byte sizes per session (`SESSION_ID\tBYTES\tDATE\tPROJECT`) |
| `state/token-log.txt` | Injection cost log (`DATE TIME\tCHARS\t~TOKENS\tPROJECT`) |
| `state/update-check.txt` | Last GitHub version check (`YYYY-MM-DD REMOTE_VERSION`) |
| `state/plugin-source.txt` | Path to the cloned repo (used by `/vault:update`) |

### Vault page frontmatter

Every page (except `index.md`, `log.md`, `CLAUDE.md`) must have:

```yaml
---
title: Page title
tags: [tag1, tag2]
source: "sources/sessions/YYYY-MM-DD-<slug>.md"   # or "vault:doctor", "manual"
date: YYYY-MM-DD
status: draft | active | archived
---
```

Optional fields: `related_code`, `session_size`, `severity` (bugs only).

---

## Update system

Version is tracked in two places:
- `plugins/vault/scripts/vault-context.py` → `__version__` (installed copy)
- `plugins/vault/.claude-plugin/plugin.json` → `"version"` (what GitHub serves for update checks)

At each SessionStart, `vault-context.py` fetches `plugin.json` from GitHub (once per day, cached in `state/update-check.txt` as `YYYY-MM-DD REMOTE_VERSION`). If the remote version is newer, a notice is injected into the session context: `⚠️ vault update available: vX.Y.Z → vA.B.C. Run /vault:update to upgrade.`

---

## Command reference

| Command | Summary | Doc |
|---|---|---|
| `/vault:help` | Print command quick-reference card | [vault-help.md](commands/vault-help.md) |
| `/vault:status` | Vault health snapshot — version, queue, token savings | [vault-status.md](commands/vault-status.md) |
| `/vault:doctor` | Scan both vaults for issues and offer to fix them | [vault-doctor.md](commands/vault-doctor.md) |
| `/vault:init` | Bootstrap `docs/vault/` for the current project | [vault-init.md](commands/vault-init.md) |
| `/vault:scan` | Refresh the pending-ingest queue | [vault-scan.md](commands/vault-scan.md) |
| `/vault:ingest [id]` | Archive the next (or a specific) pending session | [vault-ingest.md](commands/vault-ingest.md) |
| `/vault:batch-ingest [N\|all]` | Archive up to N sessions in one run | [vault-batch-ingest.md](commands/vault-batch-ingest.md) |
| `/vault:skip <id>` | Permanently remove a session from the queue | [vault-skip.md](commands/vault-skip.md) |
| `/vault:auto-ingest [on\|off\|status]` | Toggle automatic archiving at session start | [vault-auto-ingest.md](commands/vault-auto-ingest.md) |
| `/vault:update` | Pull latest version from GitHub and reinstall | [vault-update.md](commands/vault-update.md) |

---

## Further reading

- [CONCEPTS.md](CONCEPTS.md) — LLM-Wiki pattern, hybrid vault design, session routing
- [EXAMPLES.md](EXAMPLES.md) — Worked examples: ingest, query, doctor, cross-project learning
- [ATTRIBUTION.md](ATTRIBUTION.md) — Credits and prior art
