---
description: Show vault health — path, version, queue size, auto_ingest state, last ingest
allowed-tools: Read($CLAUDE_VAULT/**), Read(~/Global Claude Vault/**), Bash(python3 * --version), Bash(grep * *)
---

# /vault:status

Show a comprehensive health snapshot of the vault system in a single glance.

## Steps

1. **Resolve vault path**: `VAULT=${CLAUDE_VAULT:-$HOME/Global Claude Vault}`

2. **Existence check**: If `$VAULT` does not exist, print:
   > ❌ Vault not found at `<path>`. Run `./install.sh` to set up.
   Stop.

3. **Collect facts** (read all in one pass):
   - **Installed version**: grep `__version__` from `$VAULT/scripts/vault-context.py`
   - **auto_ingest + auto_ingest_max_per_session**: read `$VAULT/vault-config.json`
   - **Queue size**: count data rows in `$VAULT/state/pending.md` (lines matching `^| [0-9]`)
   - **Total ingested**: count lines in `$VAULT/state/ingested.txt` (non-empty, non-comment)
   - **Last ingest**: last non-empty line in `$VAULT/state/ingested.txt` that contains a session slug
   - **Last token injection**: last line of `$VAULT/state/token-log.txt`
   - **Update-check date**: content of `$VAULT/state/update-check.txt`
   - **Project vault**: check if `./docs/vault/CLAUDE.md` exists in cwd → "yes (docs/vault/)" or "no"

4. **Print status table**:

```
vault status
────────────────────────────────────────────────────────
  Vault path     : ~/Global Claude Vault
  Plugin version : v0.3.4
  Python         : python3 3.x.x

  Queue (pending): N sessions
  Total ingested : N sessions
  Last ingest    : 2026-04-26 — <slug>

  auto_ingest    : off  (max 5 per session)
  Last injection : 2026-05-05 09:47  (~1200 tokens, project: foo)
  Update check   : 2026-05-05 (up to date)

  Project vault  : yes (docs/vault/)   ← or "no (run /vault:init to create one)"
────────────────────────────────────────────────────────
```

5. **Action hints** (append only when relevant):
   - Queue > 0 and auto_ingest is off → "Run `/vault:ingest` or `/vault:batch-ingest` to process pending sessions."
   - Queue > 7 → "Large queue — consider `/vault:batch-ingest 5` in multiple runs."
   - Project vault absent → "No project vault. Run `/vault:init` to create one for this project."
   - Plugin version differs from update-check remote → show the update notice.

## Error handling

- `vault-config.json` not found → show "config: missing (defaults assumed)".
- `state/pending.md` not found → show "queue: unknown (run /vault:scan)".
- `state/token-log.txt` not found → show "last injection: never".
- `scripts/vault-context.py` not found → show "version: unknown".
- Any individual read failure → show "?" for that field and continue.
