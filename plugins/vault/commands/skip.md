---
description: Mark a pending session as skipped so it no longer appears in the ingest queue
argument-hint: "<session-id prefix — first 8+ characters>"
allowed-tools: Read($CLAUDE_VAULT/state/**), Read(~/Global Claude Vault/state/**), Edit($CLAUDE_VAULT/state/ingested.txt), Edit(~/Global Claude Vault/state/ingested.txt), Bash($CLAUDE_VAULT/scripts/scan-sessions.py), Bash(~/Global Claude Vault/scripts/scan-sessions.py)
---

# /vault:skip

Permanently skip a pending session — it will never appear in the ingest queue again.
The session JSONL is left untouched on disk; only its ID is added to the `ingested.txt` registry.

## Argument

- `$1` — required. Session ID prefix (first 8+ characters). Use `/vault:scan` to find IDs.
  - Example: `/vault:skip a1b2c3d4`

## Steps

1. **Validate argument**: If `$1` is empty → print:
   > "Usage: /vault:skip <session-id-prefix>
   > Run /vault:scan to see pending session IDs."
   Stop.

2. **Resolve paths**:
   ```
   VAULT=${CLAUDE_VAULT:-$HOME/Global Claude Vault}
   PENDING=$VAULT/state/pending.md
   INGESTED=$VAULT/state/ingested.txt
   ```

3. **Find the session in pending.md**: Search for a row whose session ID starts with `$1`.
   - If not found → print: "Session ID prefix '$1' not found in the pending queue. It may already be ingested or skipped. Run /vault:scan to refresh." Stop.
   - If found → extract the full session ID and the project name.

4. **Confirm** before writing:
   > "Skip session `<full-session-id>` (project: `<project-name>`)? It will never be ingested. [yes / no]"
   - If no → stop without writing anything.

5. **Register as skipped**: Append to `ingested.txt`:
   ```
   <full-session-id>  # skipped — /vault:skip <YYYY-MM-DD>
   ```

6. **Refresh queue**: Re-run `$VAULT/scripts/scan-sessions.py --quiet` to regenerate `pending.md`.

7. **Confirm**: Print:
   > "Skipped. Session `<slug>` removed from queue. N sessions remaining."

## Notes

- Skip is permanent within the current `ingested.txt`. To un-skip, remove the line from `ingested.txt` manually.
- Only sessions in the **pending** queue can be skipped. Already-ingested sessions are already absent from the queue.
- This command does not delete any JSONL files from `~/.claude/projects/`.

## Error handling

- `pending.md` not found → "Queue file not found. Run /vault:scan first." Stop.
- `ingested.txt` not writable → show the OS error and stop.
- Ambiguous prefix (matches >1 session) → list all matches and ask the user to provide more characters. Stop.
