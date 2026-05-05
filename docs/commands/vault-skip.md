# /vault:skip

> Mark a pending session as skipped so it no longer appears in the ingest queue.

---

## Usage

```
/vault:skip <session-id>
```

| Argument | Description |
|---|---|
| `session-id` | Required. First 8+ characters of the session ID to skip. Must match a row in `state/pending.md`. |

---

## What it does

1. Reads `state/pending.md` and finds the row whose session ID starts with the given prefix.
2. If not found → prints "Session `<id>` not found in queue." and stops.
3. Appends the full session ID to `state/ingested.txt` with a `# skipped` comment:
   ```
   a1b2c3d4-...  # skipped
   ```
4. Re-runs `scan-sessions.py --quiet` to refresh `pending.md` (the skipped session disappears).
5. Prints confirmation:
   ```
   ✓ Skipped: a1b2c3d4 (2026-04-24, Personal-Finance-Tracker, 143 KB)
   Queue: 2 sessions remaining.
   ```

---

## Why skip a session?

- **Trivial sessions**: immediately exited without meaningful work
- **Sensitive sessions**: contained credentials or private data you don't want archived
- **Duplicate sessions**: same topic already ingested from another session
- **Test sessions**: quick experiments not worth long-term storage

Skipped sessions are recorded in `state/ingested.txt` (preventing re-appearance) but no vault page is written.

---

## Irreversibility

Skipping cannot be undone via a command. To re-queue a skipped session:

1. Open `state/ingested.txt`
2. Remove the line for that session ID
3. Run `/vault:scan` to re-discover it

---

## Files read

- `$VAULT/state/pending.md`

## Files written

- `$VAULT/state/ingested.txt` (session ID appended with `# skipped`)
- `$VAULT/state/pending.md` (refreshed)

---

## Related

- [vault-scan.md](vault-scan.md) — view the queue
- [vault-ingest.md](vault-ingest.md) — archive instead of skipping
- [Index](../index.md)
