---
description: Update the vault plugin to the latest version from GitHub
allowed-tools: Read($CLAUDE_VAULT/state/**), Read(~/Global Claude Vault/state/**), Bash(git -C * pull), Bash(bash */install.sh), Bash(python3 * --version)
---

# /vault:update

Pull the latest version from GitHub and re-run `install.sh`.

## Steps

1. **Detect install type** — check whether `$CLAUDE_PLUGIN_ROOT` is set:

   ### Plugin install (`$CLAUDE_PLUGIN_ROOT` is set)

   Claude Code's plugin system manages updates. Run:
   ```
   /plugin update vault@claude-obsidian-vault-skill
   ```
   Then restart your session. Stop here.

   ### Standalone install (`$CLAUDE_PLUGIN_ROOT` is not set)

   Continue with steps 2–5.

2. **Resolve the repo path** — read `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/state/plugin-source.txt`.
   - If the file doesn't exist or is empty → tell the user:
     "Source path not recorded. Navigate to the cloned repo and run `./install.sh` manually."
     Stop.

3. **Check for a newer version before pulling** — read `__version__` from
   `<repo>/plugins/vault/scripts/vault-context.py` (grep the `__version__ =` line).
   Also check `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/state/update-check.txt` for the
   last-known remote version. Show the user:
   ```
   Current version : v0.3.x
   Available       : v0.3.y  (or "already up to date")
   Repo            : <path>
   ```
   If already up to date, confirm and stop.

4. **Pull and install** — run via Bash:
   ```bash
   git -C "<repo_path>" pull --ff-only
   bash "<repo_path>/install.sh"
   ```
   Stream/show the install output.

5. **Confirm** — after a successful install, show:
   ```
   vault plugin updated to v0.3.y.
   Restart your Claude Code session for the new SessionStart hook to take effect.
   ```

## Error handling

- `git pull` fails (merge conflict, detached HEAD) → show the error and tell the user to resolve manually in the repo.
- `install.sh` fails → show the error; do not leave a partial install.
- Network unavailable → "Could not reach GitHub. Check your connection and try again."
