# /vault:status

> Show a comprehensive health snapshot of the vault system in a single glance.

---

## Usage

```
/vault:status
```

No arguments.

---

## Output

```
vault status
────────────────────────────────────────────────────────
  Vault path     : ~/Global Claude Vault
  Plugin version : v1.0.0
  Python         : 3.x.x

  Queue (pending): 0 sessions
  Total ingested : 52 sessions
  Last ingest    : ingest #28 — serena-activate-vault-status (2026-04-28)

  auto_ingest    : off  (max 5/session)
  Update check   : 2026-05-05 (v1.0.0, up to date)

  Project vault  : yes (docs/vault/)

────────────────────────────────────────────────────────
  Token savings
────────────────────────────────────────────────────────
  Injection cost (actual)
    Sessions tracked : 42
    Total injected   : ~48,300 tokens
    Avg per session  : ~1,150 tokens
    Last injection   : 2026-05-05 09:47  (~1,200 tokens, project: my-project)

  Raw session cost (43/52 sessions with size data)
    Total raw JSONL  : ~357 MB  →  ~75,000,000 tokens

  Savings
    Estimated saved  : ~74,951,700 tokens
    ROI              : vault injected 0.1% of what sessions contained  (~1,026×)
────────────────────────────────────────────────────────
```

---

## Data sources

| Field | Source |
|---|---|
| Plugin version | `__version__` in `$VAULT/scripts/vault-context.py` |
| Python version | `python3 --version` |
| Queue size | Lines matching `^| [0-9]` in `state/pending.md` |
| Total ingested | Non-empty, non-comment lines in `state/ingested.txt` |
| Last ingest | Last matching line in `state/ingested.txt` |
| auto_ingest | `vault-config.json` → `auto_ingest`, `auto_ingest_max_per_session` |
| Update check | `state/update-check.txt` format: `YYYY-MM-DD REMOTE_VERSION` |
| Project vault | `./docs/vault/CLAUDE.md` exists in cwd |
| Injection cost | `state/token-log.txt` — each line: `DATE TIME\tCHARS\t~TOKENS\tPROJECT` |
| Raw session sizes | `state/ingest-sizes.txt` (primary) then JSONL scan fallback |

### Update check format

`state/update-check.txt` is written as `YYYY-MM-DD REMOTE_VERSION` (e.g. `2026-05-05 1.0.0`). If the remote version is higher than the installed version, the field shows:

```
Update check   : 2026-05-05 (v1.0.1 available — run /vault:update)
```

### Token savings calculation

**Step A — Injection cost (actual):** parse `token-log.txt`, extract the integer after `~` and before ` tokens`. Sum all values.

**Step B — Raw session cost (best-effort):**
1. Check `state/ingest-sizes.txt` (populated by `/vault:ingest` and `/vault:doctor`)
2. For sessions not in that file, scan `~/.claude/projects/*/SESSION_ID.jsonl` for byte sizes
3. `raw_tokens ≈ total_bytes / 5`

**Step C — Savings:** `estimated_saved = raw_tokens - total_injected`

If no size data is available at all, the savings block shows a degraded message: `Raw session cost: no data yet — run /vault:doctor to populate.`

---

## Action hints

Shown only when relevant:

| Condition | Hint |
|---|---|
| Queue > 0 and `auto_ingest=off` | Run `/vault:ingest` or `/vault:batch-ingest` |
| Queue > 7 | Consider `/vault:batch-ingest 5` in multiple runs |
| No project vault | Run `/vault:init` to create one |
| Remote version > installed | Run `/vault:update` |

---

## Files read

- `$VAULT/scripts/vault-context.py`
- `$VAULT/vault-config.json`
- `$VAULT/state/pending.md`
- `$VAULT/state/ingested.txt`
- `$VAULT/state/ingest-sizes.txt`
- `$VAULT/state/token-log.txt`
- `$VAULT/state/update-check.txt`
- `~/.claude/projects/*/SESSION_ID.jsonl` (fallback only)

## Files written

None — read-only command.

---

## Related

- [vault-doctor.md](vault-doctor.md) — fixes issues surfaced by status
- [vault-update.md](vault-update.md) — handles update notices
- [Index](../index.md)
