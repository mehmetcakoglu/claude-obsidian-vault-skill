---
description: Scan ~/.claude/projects for new Claude Code sessions and update the vault's pending-ingest queue
allowed-tools: Bash($CLAUDE_VAULT/scripts/scan-sessions.sh), Bash(~/claude-vault/scripts/scan-sessions.sh), Read($CLAUDE_VAULT/state/**), Read(~/claude-vault/state/**)
---

# /vault:scan

Run the scan script and display the resulting queue to the user.

## Steps

1. Execute `${CLAUDE_VAULT:-$HOME/claude-vault}/scripts/scan-sessions.sh`. This regenerates `state/pending.md` with any newly discovered sessions.
2. Read `${CLAUDE_VAULT:-$HOME/claude-vault}/state/pending.md` and show it to the user.
3. If the queue is non-empty, remind the user they can run `/vault:ingest` to process the next session (biggest-first by default).
4. If the queue is empty, confirm there is nothing to do and stop.

Do **not** start processing sessions. This command is scan-only — ingest is a separate command.
