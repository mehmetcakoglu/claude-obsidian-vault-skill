---
description: Scan ~/.claude/projects for new Claude Code sessions and update the vault's pending-ingest queue
allowed-tools: Bash($CLAUDE_VAULT/scripts/scan-sessions.sh), Bash(~/Global Claude Vault/scripts/scan-sessions.sh), Bash($CLAUDE_VAULT/scripts/scan-sessions.py), Bash(~/Global Claude Vault/scripts/scan-sessions.py), Read($CLAUDE_VAULT/state/**), Read(~/Global Claude Vault/state/**)
---

# /vault:scan

Refresh the pending-ingest queue and display a formatted summary of what's waiting.

## Steps

1. Execute `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/scripts/scan-sessions.py --quiet` (falls back to `.sh` if `.py` not present). This regenerates `state/pending.md`.

2. Read `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/state/pending.md`.

3. **If the queue is empty**: print
   > Queue is empty — nothing to ingest.
   Stop.

4. **If the queue is non-empty**: print a formatted summary:

   ```
   Pending ingest queue — N session(s)
   ──────────────────────────────────────────────────────────────────────
   #   Size      Date        Project            Session ID (prefix)
   ──────────────────────────────────────────────────────────────────────
   1   4.2 MB    2026-05-04  my-project         a1b2c3d4…
   2   1.1 MB    2026-05-03  other-project      e5f6a7b8…
   3    800 KB   2026-05-01  my-project         c9d0e1f2…
   ──────────────────────────────────────────────────────────────────────
   Total: N sessions  |  Largest: X.X MB  |  Oldest: YYYY-MM-DD
   ```

   Extract columns from `pending.md`: rank, size, date, project name, session ID prefix (first 8 chars).

5. **Action hints** (always shown when queue is non-empty):
   - N = 1 → "Run `/vault:ingest` to process it."
   - 2 ≤ N ≤ 5 → "Run `/vault:batch-ingest` to process all N sessions (default limit: 5)."
   - N > 5 → "Run `/vault:batch-ingest 5` (then repeat) or `/vault:auto-ingest on` to drain automatically."
   - N > 7 → also add: "Large queue — splitting into multiple runs keeps context pressure low."
   - Any session → "Run `/vault:skip <session-id-prefix>` to permanently skip a session."

Do **not** start processing sessions. This command is scan-only.
