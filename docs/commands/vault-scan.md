# /vault:scan

> Scan `~/.claude/projects/` for new Claude Code sessions and refresh the pending-ingest queue.

---

## Usage

```
/vault:scan
```

No arguments.

---

## What it does

1. Runs `scan-sessions.py` (the same script that runs automatically at SessionStart).
2. Compares all `.jsonl` files in `~/.claude/projects/` against `state/ingested.txt`.
3. Writes new, not-yet-ingested sessions to `state/pending.md` (sorted by file size, largest first).
4. Displays the current queue contents.

### Output example

```
vault:scan — 2026-05-05

Scanned: ~/.claude/projects/  (23 projects, 148 sessions)
Already ingested: 52
Skipped: 4

Pending queue (3 sessions):
────────────────────────────────────────────────────────
 #  Session ID      Project                      Date        Size
 1  5e2a1f3b…      claude-obsidian-vault-skill  2026-05-05  4.2 MB
 2  8c3d9e7a…      Personal-Finance-Tracker     2026-05-04  1.1 MB
 3  2b4f6a1c…      claude-obsidian-vault-skill  2026-05-03  0.8 MB
────────────────────────────────────────────────────────
Run /vault:ingest to process the next session.
```

---

## When to run manually

The scan runs automatically at every SessionStart via the `vault-context.py` hook. Run `/vault:scan` manually when:

- You want to see the current queue without starting a new session
- You suspect the queue is stale (e.g. after force-quitting Claude Code)
- After `/vault:skip` to verify the session was removed

---

## Session discovery logic

`scan-sessions.py` does the following:

1. Lists all `.jsonl` files under `~/.claude/projects/`
2. Reads `state/ingested.txt` to build the set of already-processed IDs
3. Filters out any ID in `state/ingested.txt` (includes both ingested and skipped sessions, since `/vault:skip` also writes to `ingested.txt`)
4. Sorts remaining sessions by file size (descending) — largest sessions have more content worth archiving
5. Writes `state/pending.md` with a numbered Markdown table

---

## Files read

- `~/.claude/projects/**/*.jsonl`
- `$VAULT/state/ingested.txt`

## Files written

- `$VAULT/state/pending.md` (overwritten)

---

## Related

- [vault-ingest.md](vault-ingest.md) — process the queue
- [vault-skip.md](vault-skip.md) — remove a session from the queue
- [Index](../index.md)
