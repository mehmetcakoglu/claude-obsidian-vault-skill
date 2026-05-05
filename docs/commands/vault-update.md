# /vault:update

> Pull the latest version from GitHub and reinstall the vault plugin.

---

## Usage

```
/vault:update
```

No arguments.

---

## What it does

### Step 1 — Detect install type

Checks whether `$CLAUDE_PLUGIN_ROOT` is set (plugin install) or not (standalone install).

**Plugin install** (`$CLAUDE_PLUGIN_ROOT` is set):
```
Claude Code's plugin system manages updates. Run:
  /plugin update vault@claude-obsidian-vault-skill
Then restart your session.
```
Stops here.

**Standalone install** (most users): continues with steps 2–5.

### Step 2 — Resolve repo path

Reads `$VAULT/state/plugin-source.txt` to find the cloned repository path.

If the file is missing:
```
Source path not recorded. Navigate to the cloned repo and run ./install.sh manually.
```

### Step 3 — Version check

Reads `__version__` from `<repo>/plugins/vault/scripts/vault-context.py` (installed version) and `state/update-check.txt` (cached remote version).

```
Current version : v1.0.0
Available       : v1.0.1
Repo            : ~/Development/Repos/claude-obsidian-vault-skill
```

If already up to date → confirms and stops.

### Step 4 — Pull and install

```bash
git -C "<repo_path>" pull --ff-only
bash "<repo_path>/install.sh"
```

The install script:
- Copies new slash commands to `~/.claude/commands/vault/`
- Copies new scripts to `$VAULT/scripts/`
- Updates the skill file in `~/.claude/skills/vault/`
- Preserves all vault data (no overwriting of existing vault pages)

### Step 5 — Confirm

```
✓ vault plugin updated: v1.0.0 → v1.0.1
Restart your Claude Code session for the new SessionStart hook to take effect.
```

---

## Update detection

`vault-context.py` checks GitHub once per day at SessionStart by fetching `plugin.json` from the repository. The result is cached in `state/update-check.txt` as `YYYY-MM-DD REMOTE_VERSION`.

When a newer version is available, the following notice is injected into every session context until the update is applied:

```
⚠️  vault update available: v1.0.0 → v1.0.1. Run /vault:update to upgrade.
```

---

## Manual update (fallback)

If `/vault:update` can't find the repo:

```bash
cd ~/Development/Repos/claude-obsidian-vault-skill  # or wherever you cloned it
git pull
./install.sh
```

---

## What install.sh does

| Step | Action |
|---|---|
| 1 | Detect Python (python3 or python) |
| 2 | Copy skill SKILL.md → `~/.claude/skills/vault/` |
| 3 | Copy slash commands → `~/.claude/commands/vault/` (doctor, status, ingest, batch-ingest, scan, init, skip, auto-ingest, update, help) |
| 4 | Copy scripts → `$VAULT/scripts/` (vault-context.py, scan-sessions.py + platform wrappers) |
| 5 | Bootstrap global vault skeleton (skips existing files) |
| 6 | Patch `~/.claude/settings.json` — register synchronous SessionStart hook |
| 7 | Verify all components installed correctly |

---

## Files read

- `$VAULT/state/plugin-source.txt`
- `$VAULT/state/update-check.txt`
- `<repo>/plugins/vault/scripts/vault-context.py` (for current local version)

## Files written

- `~/.claude/skills/vault/SKILL.md`
- `~/.claude/commands/vault/*.md`
- `$VAULT/scripts/vault-context.py`
- `$VAULT/scripts/scan-sessions.py`
- `~/.claude/settings.json` (SessionStart hook, if not already present)

---

## Related

- [vault-status.md](vault-status.md) — shows current version and update notice
- [Index](../index.md)
