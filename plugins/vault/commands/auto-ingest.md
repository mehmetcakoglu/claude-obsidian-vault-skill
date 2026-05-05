---
description: Enable, disable, or check the auto-ingest setting in vault-config.json
argument-hint: "[on | off | status]"
allowed-tools: Read($CLAUDE_VAULT/vault-config.json), Read(~/Global Claude Vault/vault-config.json), Edit($CLAUDE_VAULT/vault-config.json), Edit(~/Global Claude Vault/vault-config.json)
---

# /vault:auto-ingest

Toggle or inspect the `auto_ingest` flag in `vault-config.json`.

## Argument

- `on` — enable auto-ingest
- `off` — disable auto-ingest
- `on max N` — enable auto-ingest AND set `auto_ingest_max_per_session` to N (e.g. `/vault:auto-ingest on max 3`)
- `off max N` — disable auto-ingest AND set the max (useful to pre-configure before re-enabling)
- `max N` — update `auto_ingest_max_per_session` only, without changing the on/off state
- `status` or omitted — show current value without changing anything

## Steps

1. Resolve the config path:
   ```
   CONFIG=${CLAUDE_VAULT:-$HOME/Global Claude Vault}/vault-config.json
   ```

2. Read the file with the `Read` tool.

3. Parse arguments:
   - Extract the first token as the action: `on`, `off`, `max`, or `status`/omitted.
   - If `max N` appears anywhere in the argument string (e.g. `on max 3`, `max 5`), parse N as the new max value.
   - Validate: N must be a positive integer (1–50). If invalid → "Invalid max value 'X'. Must be a positive integer." Stop.

4. Act based on the parsed action:

   ### `on` (optionally with `max N`)
   - Set `auto_ingest` to `true` in the JSON.
   - If `max N` was provided, also set `auto_ingest_max_per_session` to N.
   - Write back with the `Edit` tool.
   - Confirm: "auto_ingest enabled. The next session will automatically process up to M sessions before responding."

   ### `off` (optionally with `max N`)
   - Set `auto_ingest` to `false` in the JSON.
   - If `max N` was provided, also set `auto_ingest_max_per_session` to N.
   - Write back with the `Edit` tool.
   - Confirm: "auto_ingest disabled. Ingest is now user-triggered (/vault:ingest or /vault:batch-ingest)."
   - If `max N` was also set: add "Max sessions per session set to N (will apply when auto_ingest is re-enabled)."

   ### `max N` (no on/off)
   - Update `auto_ingest_max_per_session` to N without changing the `auto_ingest` flag.
   - Write back with the `Edit` tool.
   - Confirm: "auto_ingest_max_per_session set to N. auto_ingest remains <on/off>."

   ### `status` or omitted
   - Read and display the relevant fields as a table:

   | Setting | Value |
   |---|---|
   | `auto_ingest` | true / false |
   | `auto_ingest_max_per_session` | N |

   - Add a one-line interpretation:
     - `true` → "Auto-ingest is ON — sessions are processed automatically at session start."
     - `false` → "Auto-ingest is OFF — use /vault:ingest or /vault:batch-ingest to process sessions manually."

5. **No restart needed.** The change takes effect on the next Claude Code session start (vault-context.py reads the config fresh each time).

## Error handling

- Config file not found → "vault-config.json not found at `$CONFIG`. Run `./install.sh` to seed it." Stop.
- Invalid action (not `on`, `off`, `max`, or `status`) → "Unknown argument '$1'. Usage: /vault:auto-ingest [on|off|status] [max N]". Stop.
- `max N` present but N is not a positive integer → "Invalid max value. Must be a positive integer (1–50)." Stop.
