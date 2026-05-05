---
description: Process all pending Claude Code sessions in sequence, up to a configurable maximum per run
argument-hint: "[optional: max N — default 5]"
allowed-tools: Read($CLAUDE_VAULT/**), Read(~/Global Claude Vault/**), Read(~/.claude/projects/**), Read(*/docs/vault/**), Write($CLAUDE_VAULT/**), Write(~/Global Claude Vault/**), Write(*/docs/vault/**), Edit($CLAUDE_VAULT/**), Edit(~/Global Claude Vault/**), Edit(*/docs/vault/**), Bash(python3 *), Bash(git -C * add *), Bash(git -C * commit *)
---

# /vault:batch-ingest

Process multiple pending sessions from the ingest queue in a single command, calling the `/vault:ingest` workflow repeatedly until the queue is empty or the per-run limit is reached.

## Argument

- `$1` — optional maximum number of sessions to process in this run.
  - If omitted, read `auto_ingest_max_per_session` from `${CLAUDE_VAULT:-$HOME/claude-vault}/vault-config.json`. If the key is absent, default to **5**.
  - Pass `all` to process every pending session regardless of count (use with caution on large queues — context pressure).

## Pre-flight

1. Read `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/state/pending.md`.
   - If empty → say "Queue is empty. Nothing to ingest." and stop.
2. Count the pending rows (`N_pending`).
3. Resolve the limit:
   - `$1` is a number → `limit = min($1, N_pending)`
   - `$1` is `all` → `limit = N_pending`
   - `$1` omitted → read `vault-config.json`; fallback to 5
4. **Confirmation gate for `all` or `limit > 7`**:
   - If `$1` is `all` OR `limit > 7`, print a summary and ask for confirmation **before processing anything**:
     > "About to process **N sessions** in one run. This will consume significant context window.
     > Sessions: [list the first 5 slugs from pending.md, then '… and N more' if >5]
     > Proceed? (yes / no — or reply with a lower number to process fewer)"
   - If the user replies with a number, treat it as the new limit.
   - If the user replies `no` or `n`, stop without processing anything.
   - If the user replies `yes` or `y`, continue.
   - For `limit ≤ 7` and no `all` flag, skip the confirmation prompt and proceed directly.
5. Warn if `limit > 5`:
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
