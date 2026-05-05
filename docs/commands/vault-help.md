# /vault:help

> Print a quick-reference card for every `/vault:*` command.

---

## Usage

```
/vault:help
```

No arguments. Responds immediately from the skill file — no tools invoked.

---

## Output

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
```

---

## Implementation note

`/vault:help` reads from the skill file and prints verbatim — no file system access required. This makes it the fastest vault command and safe to run offline.

---

## Related

- [Index](../index.md) — full technical documentation
- [vault-status.md](vault-status.md)
