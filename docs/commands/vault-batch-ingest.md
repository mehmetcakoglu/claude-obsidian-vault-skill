# /vault:batch-ingest

> Process multiple pending sessions in sequence, up to a configurable maximum.

---

## Usage

```
/vault:batch-ingest [N|all]
```

| Argument | Description |
|---|---|
| `N` | Process at most N sessions. Defaults to `auto_ingest_max_per_session` from `vault-config.json` (default: 5). |
| `all` | Process every session in the queue. Use with care on large queues. |

---

## What it does

1. Reads `state/pending.md` to determine queue size.
2. If queue is empty → prints "Queue is empty." and stops.
3. Processes sessions one by one, invoking the same logic as `/vault:ingest` for each.
4. After each session: prints a progress line and checks whether to continue.
5. Stops when the limit is reached or the queue is exhausted.
6. Prints a summary: N ingested, M skipped/failed.

### Progress output

```
vault:batch-ingest — queue: 7 sessions, limit: 5
────────────────────────────────────────────────
[1/5] Ingesting 2026-04-26-vault-plugin-batch-ingest-and-auto-update … ✓
[2/5] Ingesting 2026-04-25-context-mode-mcp-install … ✓
[3/5] Ingesting 2026-04-24-serena-slash-command … ✓
[4/5] Ingesting 2026-04-23-pft-receivable-ledger-reorg … ✓
[5/5] Ingesting 2026-03-31-filarch-ai-hasura-mcp-sprint … ✓
────────────────────────────────────────────────
Done. 5 ingested, 2 remaining in queue.
Run /vault:batch-ingest again to process more.
```

---

## Large queue strategy

When the queue has more sessions than the limit allows in one run:

```
/vault:batch-ingest 5   # process 5 today
/vault:batch-ingest 5   # process 5 more next session
```

The queue is persistent — sessions stay until ingested or skipped.

---

## Difference from /vault:ingest

| | `/vault:ingest` | `/vault:batch-ingest` |
|---|---|---|
| Sessions per run | 1 | N (configurable) |
| Requires approval | Yes (per session summary) | Configurable — auto-approves each |
| Best for | Reviewing individual sessions | Clearing backlog |

---

## Files read/written

Same as `/vault:ingest` for each processed session, plus `state/pending.md` (refreshed after each).

---

## Related

- [vault-ingest.md](vault-ingest.md) — single-session ingest
- [vault-skip.md](vault-skip.md) — skip unwanted sessions before batch
- [vault-auto-ingest.md](vault-auto-ingest.md) — automatic background ingesting
- [Index](../index.md)
