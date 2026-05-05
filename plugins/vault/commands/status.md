---
description: Show vault health — path, version, queue size, auto_ingest state, last ingest, token savings
allowed-tools: Read($CLAUDE_VAULT/**), Read(~/Global Claude Vault/**), Read(~/.claude/projects/**), Bash(python3 --version), Bash(python3 -c *), Bash(grep * $CLAUDE_VAULT/**), Bash(grep * ~/Global\ Claude\ Vault/**)
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
   - **Update-check**: parse `$VAULT/state/update-check.txt` — format is `YYYY-MM-DD REMOTE_VERSION` (e.g. `2026-05-05 1.0.0`). Extract the date and remote version. Compare remote version to installed version: if remote > installed, show update notice; otherwise show "up to date".
   - **Project vault**: check if `./docs/vault/CLAUDE.md` exists in cwd → "yes (docs/vault/)" or "no"
   - **Token log**: read ALL lines of `$VAULT/state/token-log.txt` for the savings calculation below

4. **Token savings calculation** — run as a Python snippet via `ctx_execute` or inline math:

   **Step A — Injection cost** (actual): parse every non-empty line of `token-log.txt`:
   ```
   2026-04-26 21:00   5430 chars   ~1357 tokens   Personal-Finance-Tracker
   ```
   Extract the integer after `~` and before ` tokens`.
   ```
   sessions_tracked = number of valid lines
   total_injected   = sum of all token values
   avg_injection    = total_injected / sessions_tracked  (0 if no sessions)
   ```

   **Step B — Raw session cost** (optional, best-effort):
   Try to find JSONL file sizes to compute actual savings. This block is always attempted but degrades gracefully.

   1. Try `$VAULT/state/ingest-sizes.txt` — each line: `SESSION_ID\tSIZE_BYTES\tDATE\tPROJECT`
   2. For any session ID in `ingested.txt` NOT covered by `ingest-sizes.txt`, try:
      - `~/.claude/projects/*/SESSION_ID.jsonl` — if found, add its byte size
   3. Sum → `total_raw_bytes`, count → `sessions_with_size`
   4. `total_raw_tokens = total_raw_bytes / 5`

   **Step C — Compute savings** (only if `sessions_with_size > 0`):
   ```
   estimated_savings = total_raw_tokens - total_injected
   ```

5. **Print status table** — the "Token savings" section is **always printed**, even when raw size data is unavailable:

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
  Update check   : 2026-05-05 (v1.0.0, up to date)
                   OR: 2026-05-05 (v1.0.1 available — run /vault:update)

  Project vault  : yes (docs/vault/)

────────────────────────────────────────────────────────
  Token savings
────────────────────────────────────────────────────────
  Injection cost (actual)
    Sessions tracked : 42
    Total injected   : ~48,300 tokens
    Avg per session  : ~1,150 tokens
    Last injection   : 2026-05-05 09:47  (~1,200 tokens, project: my-project)

  Raw session cost (38/42 sessions with size data)
    Total raw JSONL  : ~248 MB  →  ~49,600,000 tokens

  Savings
    Estimated saved  : ~49,551,700 tokens
    ROI              : vault injected 0.1% of what sessions contained  (~1,026×)
────────────────────────────────────────────────────────
  ℹ  JSONL bytes ÷ 5 = token estimate. Sessions missing: 4/42 (JSONL not on disk).
```

   **Degraded output** (when raw size data is unavailable — e.g. no ingest yet):

```
────────────────────────────────────────────────────────
  Token savings
────────────────────────────────────────────────────────
  Injection cost (actual)
    Sessions tracked : 5
    Total injected   : ~6,200 tokens
    Avg per session  : ~1,240 tokens
    Last injection   : 2026-05-05 10:17  (~1,703 tokens, project: my-project)

  Raw session cost   : no data yet
    ℹ  Run /vault:ingest to start tracking raw session sizes.
       Savings will appear here after the first ingest.
────────────────────────────────────────────────────────
```

   Formatting rules:
   - **Always print the Token savings section** — never skip it entirely.
   - Always show the "Injection cost" sub-block from `token-log.txt` (if log is missing, show "No injection data yet").
   - Show "Raw session cost" sub-block only if `sessions_with_size > 0`; otherwise show the degraded note.
   - Format large numbers with thousands separators.
   - Raw JSONL size in MB (`total_raw_bytes / 1_048_576`).

6. **Action hints** (append only when relevant):
   - Queue > 0 and auto_ingest is off → "Run `/vault:ingest` or `/vault:batch-ingest` to process pending sessions."
   - Queue > 7 → "Large queue — consider `/vault:batch-ingest 5` in multiple runs."
   - Project vault absent → "No project vault. Run `/vault:init` to create one for this project."
   - Plugin version differs from update-check remote → show the update notice.

## Error handling

- `vault-config.json` not found → show "config: missing (defaults assumed)".
- `state/pending.md` not found → show "queue: unknown (run /vault:scan)".
- `state/token-log.txt` not found or empty → show "No injection data yet" inside the Token savings section (never skip the section header).
- `state/ingest-sizes.txt` not found AND no JSONL files found → show "Raw session cost: no data yet" with the ingest hint. Never skip the whole Token savings block.
- `scripts/vault-context.py` not found → show "version: unknown".
- Any individual read failure → show "?" for that field and continue.
