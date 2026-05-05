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
- `status` or omitted — show current value without changing anything

## Steps

1. Resolve the config path:
   ```
   CONFIG=${CLAUDE_VAULT:-$HOME/Global Claude Vault}/vault-config.json
   ```

2. Read the file with the `Read` tool.

3. Act based on `$1`:

   ### `on`
   - Set `auto_ingest` to `true` in the JSON.
   - Write back with the `Edit` tool (change only the `auto_ingest` line).
   - Confirm: "auto_ingest enabled. The next session will automatically process up to `auto_ingest_max_per_session` (currently N) sessions before responding."

   ### `off`
   - Set `auto_ingest` to `false` in the JSON.
   - Write back with the `Edit` tool.
   - Confirm: "auto_ingest disabled. Ingest is now user-triggered (/vault:ingest or /vault:batch-ingest)."

   ### `status` or omitted
   - Read and display the relevant fields as a table:

   | Setting | Value |
   |---|---|
   | `auto_ingest` | true / false |
   | `auto_ingest_max_per_session` | N |

   - Add a one-line interpretation:
     - `true` → "Auto-ingest is ON — sessions are processed automatically at session start."
     - `false` → "Auto-ingest is OFF — use /vault:ingest or /vault:batch-ingest to process sessions manually."

4. **No restart needed.** The change takes effect on the next Claude Code session start (vault-context.py reads the config fresh each time).

## Error handling

- Config file not found → "vault-config.json not found at `$CONFIG`. Run `./install.sh` to seed it." Stop.
- Invalid `$1` (not `on`, `off`, or `status`) → "Unknown argument '$1'. Usage: /vault:auto-ingest [on | off | status]". Stop.
