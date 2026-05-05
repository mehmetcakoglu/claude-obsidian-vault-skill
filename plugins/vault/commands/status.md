---
description: Show vault health — path, version, queue size, auto_ingest state, last ingest, token savings
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
   - **Update-check date**: content of `$VAULT/state/update-check.txt`
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

   **Step B — Raw session cost** (actual, not estimated): this is what vault replaced.
   Without a vault, the user would need to read raw session transcripts or re-explain context.
   The JSONL file size is the ground truth for how much information was in each session.

   1. Read `$VAULT/state/ingest-sizes.txt` — each line: `SESSION_ID\tSIZE_BYTES\tDATE\tPROJECT`
   2. For any ingested session NOT in `ingest-sizes.txt`, try to locate its JSONL:
      - Search `~/.claude/projects/*/SESSION_ID.jsonl` (use the session IDs from `ingested.txt`)
      - If found, record its byte size
   3. Sum all found byte sizes → `total_raw_bytes`
   4. Convert: `total_raw_tokens = total_raw_bytes / 5`
      _(JSONL is JSON-heavy; 1 token ≈ 5 bytes is a reasonable estimate for structured JSON transcript data)_
   5. Track how many ingested sessions had size data: `sessions_with_size`

   **Step C — Compute**:
   ```
   estimated_savings = total_raw_tokens - total_injected
   roi_pct           = (estimated_savings / total_injected * 100) if total_injected > 0 else 0
   coverage_pct      = sessions_with_size / total_ingested * 100  (how much data we have)
   ```

5. **Print status table**:

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
  Update check   : 2026-05-05 (up to date)

  Project vault  : yes (docs/vault/)

────────────────────────────────────────────────────────
  Token savings
────────────────────────────────────────────────────────
  Injection cost (actual)
    Sessions tracked : 42
    Total injected   : ~48,300 tokens
    Avg per session  : ~1,150 tokens
    Last injection   : 2026-05-05 09:47  (~1,200 tokens, project: my-project)

  Raw session cost (actual, 38/42 sessions with size data)
    Total raw JSONL  : ~248 MB  →  ~49,600,000 tokens
    Avg per session  : ~1,181,000 tokens

  Savings
    Estimated saved  : ~49,551,700 tokens
    ROI              : ~1,026×  (vault injected 0.1% of what sessions contained)
────────────────────────────────────────────────────────
  ℹ  Raw token estimate: JSONL bytes ÷ 5  (JSON transcript overhead).
     Sessions missing size data (4/42): JSONL files not found on disk.
```

   Formatting rules:
   - Format large numbers with thousands separators.
   - Raw JSONL size in MB for readability (`total_raw_bytes / 1_048_576`).
   - If `sessions_tracked` is 0 → show "No injection data yet. Start a new session to begin tracking."
   - If `sessions_with_size` is 0 → skip the "Raw session cost" block and show:
     "No session size data yet. Run `/vault:ingest` — sizes are recorded from the first ingest onward."
   - If `sessions_with_size < total_ingested` → note "X/N sessions with size data" so the user knows partial coverage.
   - If `estimated_savings` < 0 → impossible given JSONL sizes vs injection, but if it happens show "Unusual — injection cost exceeds raw session size."
   - ROI as a multiplier ("vault injected X% of what sessions contained") is more intuitive than a percentage when ROI >> 100%.

6. **Action hints** (append only when relevant):
   - Queue > 0 and auto_ingest is off → "Run `/vault:ingest` or `/vault:batch-ingest` to process pending sessions."
   - Queue > 7 → "Large queue — consider `/vault:batch-ingest 5` in multiple runs."
   - Project vault absent → "No project vault. Run `/vault:init` to create one for this project."
   - Plugin version differs from update-check remote → show the update notice.

## Error handling

- `vault-config.json` not found → show "config: missing (defaults assumed)".
- `state/pending.md` not found → show "queue: unknown (run /vault:scan)".
- `state/token-log.txt` not found or empty → show "No injection data yet. Start a new session to begin tracking."
- `state/ingest-sizes.txt` not found → skip raw cost block, show note about future tracking.
- `scripts/vault-context.py` not found → show "version: unknown".
- Any individual read failure → show "?" for that field and continue.
