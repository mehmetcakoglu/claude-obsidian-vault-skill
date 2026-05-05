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

4. **Token savings calculation** — run this as a Python snippet using `ctx_execute` or inline math:

   Parse every non-empty line of `token-log.txt`. Each line has the format:
   ```
   2026-04-26 21:00   5430 chars   ~1357 tokens   Personal-Finance-Tracker
   ```
   Extract the integer after `~` and before ` tokens`.

   Compute:
   ```
   sessions_tracked   = number of valid lines
   total_injected     = sum of all token values
   avg_injection      = total_injected / sessions_tracked   (or 0 if no sessions)

   # Conservative baseline: without vault, Claude would spend ~2,500 tokens per session
   # re-reading 3–4 context files (~600 tokens each) + user re-explaining decisions (~300 tokens).
   BASELINE_PER_SESSION = 2500

   total_baseline     = BASELINE_PER_SESSION * sessions_tracked
   estimated_savings  = total_baseline - total_injected   (can be negative early on)
   roi_pct            = (estimated_savings / total_injected * 100) if total_injected > 0 else 0
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
  Token savings (estimated)
────────────────────────────────────────────────────────
  Sessions tracked   : 42
  Total injected     : ~48,300 tokens
  Avg per session    : ~1,150 tokens

  Baseline (no vault): ~105,000 tokens  (2,500 × 42 sessions)
  Estimated saved    : ~56,700 tokens
  ROI                : ~117%  (saved 2.2× what was injected)

  Last injection     : 2026-05-05 09:47  (~1,200 tokens, project: my-project)
────────────────────────────────────────────────────────
  ℹ  Savings estimate assumes ~2,500 tokens of context-discovery cost per
     session without the vault (3–4 file reads + user re-explanation).
     Actual savings vary by project complexity and session length.
```

   - If `sessions_tracked` is 0 → show "No injection data yet. Start a new session to begin tracking."
   - If `estimated_savings` < 0 → show "Not yet at breakeven — vault needs ~N more sessions." (N = ceil(total_injected / (BASELINE - avg_injection)))
   - Format large numbers with thousands separators (48,300 not 48300).
   - ROI label: < 0% → "not yet at breakeven", 0–50% → "approaching breakeven", > 50% → show the multiplier (e.g. "saved 2.2× what was injected").

6. **Action hints** (append only when relevant):
   - Queue > 0 and auto_ingest is off → "Run `/vault:ingest` or `/vault:batch-ingest` to process pending sessions."
   - Queue > 7 → "Large queue — consider `/vault:batch-ingest 5` in multiple runs."
   - Project vault absent → "No project vault. Run `/vault:init` to create one for this project."
   - Plugin version differs from update-check remote → show the update notice.

## Error handling

- `vault-config.json` not found → show "config: missing (defaults assumed)".
- `state/pending.md` not found → show "queue: unknown (run /vault:scan)".
- `state/token-log.txt` not found or empty → show savings section as "No injection data yet."
- `scripts/vault-context.py` not found → show "version: unknown".
- Any individual read failure → show "?" for that field and continue.
