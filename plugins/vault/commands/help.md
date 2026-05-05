---
description: List all vault slash commands with one-line descriptions and usage hints
---

# /vault:help

Print a quick-reference card for every `/vault:*` command. No tools needed — respond immediately from this file.

## Output

Print the following verbatim (substitute the current version from `__version__` in `scripts/vault-context.py` if easily available, otherwise use "vault plugin"):

```
vault plugin — slash command reference
════════════════════════════════════════════════════════════

  /vault:help                  This help card
  /vault:status                Health check — path, queue, version, config
  /vault:doctor                Scan vaults for issues and offer to fix them

  /vault:init                  Bootstrap docs/vault/ for the current project
  /vault:scan                  Refresh the pending-ingest queue (shows queue contents)
  /vault:ingest [session-id]   Process the next (or a specific) pending session
  /vault:batch-ingest [N|all]  Process up to N sessions in one run (default 5)
  /vault:skip <session-id>     Mark a session as skipped (won't appear in queue again)

  /vault:auto-ingest [on|off|status]         Toggle or inspect auto_ingest
  /vault:auto-ingest [on|off] [max N]        Also set auto_ingest_max_per_session
  /vault:update                              Pull latest version from GitHub + reinstall

════════════════════════════════════════════════════════════
Typical first-session workflow:
  1. /vault:init          → bootstrap a project vault (first time only)
  2. /vault:scan          → see what's in the queue
  3. /vault:ingest        → archive the next session
  4. /vault:status        → confirm everything looks good
  5. /vault:doctor        → check vault health periodically
════════════════════════════════════════════════════════════
Docs & source: https://github.com/mehmetcakoglu/claude-obsidian-vault-skill
```

Do not invoke any tools. Print this text and stop.
