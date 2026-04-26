---
description: Process all pending Claude Code sessions in sequence, up to a configurable maximum per run
argument-hint: "[optional: max N — default 5]"
---

# /vault:batch-ingest

Process multiple pending sessions from the ingest queue in a single command, calling the `/vault:ingest` workflow repeatedly until the queue is empty or the per-run limit is reached.

## Argument

- `$1` — optional maximum number of sessions to process in this run.
  - If omitted, read `auto_ingest_max_per_session` from `${CLAUDE_VAULT:-$HOME/claude-vault}/vault-config.json`. If the key is absent, default to **5**.
  - Pass `all` to process every pending session regardless of count (use with caution on large queues — context pressure).

## Pre-flight

1. Read `${CLAUDE_VAULT:-$HOME/claude-vault}/state/pending.md`.
   - If empty → say "Queue is empty. Nothing to ingest." and stop.
2. Count the pending rows (`N_pending`).
3. Resolve the limit:
   - `$1` is a number → `limit = min($1, N_pending)`
   - `$1` is `all` → `limit = N_pending`
   - `$1` omitted → read `vault-config.json`; fallback to 5
4. Warn if `limit > 5`:
   > "Processing X sessions in one run. Context window pressure increases with each session — quality may degrade toward the end. Consider splitting into two runs if X > 7."

## Processing loop

Repeat up to `limit` times:

1. Check `pending.md` — if empty, break early.
2. Invoke the full `/vault:ingest` workflow for the top session (no `$1` argument — always take the queue head).
3. After each completed ingest, print a one-line progress indicator:
   > `[batch-ingest] ✓ N/limit — <slug> (N_remaining remaining in queue)`
4. If context window is approaching capacity (last ~20%), stop early and report:
   > "Stopped at N/limit — context window is getting full. Run /vault:batch-ingest again to continue."

## Post-batch summary

After the loop ends, print a compact summary:

```
Batch ingest complete.
  Processed : N sessions
  Remaining : M sessions in queue
  Run /vault:batch-ingest again to continue, or /vault:ingest for single-session review.
```

## Stop criteria

- Queue is empty
- `limit` sessions processed
- Context window approaching capacity (stops early with a message)

One invocation = at most `limit` sessions. Run again to continue if sessions remain.
