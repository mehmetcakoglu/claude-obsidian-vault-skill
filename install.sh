#!/usr/bin/env bash
# claude-obsidian-vault-skill installer
#
# Idempotent. Installs the vault skill, slash commands, scripts, and a
# global-vault skeleton. Patches Claude Code's settings.json to register a
# synchronous SessionStart hook that injects vault context at session start.
#
# Requirements: Python 3 (python3 or python in PATH)
#
# Usage:
#   ./install.sh                          # install into defaults
#   CLAUDE_VAULT=/path ./install.sh       # custom vault location
#
# Windows: run from Git Bash or WSL. Pure PowerShell users → see README.md.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
VAULT_HOME="${CLAUDE_VAULT:-$HOME/claude-vault}"

PLUGIN_SRC="$REPO_ROOT/plugins/vault"
SKILL_SRC="$PLUGIN_SRC/skills/vault"
CMD_SRC="$PLUGIN_SRC/commands"
SCRIPT_SRC="$PLUGIN_SRC/scripts"
TPL_GLOBAL="$PLUGIN_SRC/templates/global-vault"

SKILL_DST="$CLAUDE_HOME/skills/vault"
CMD_DST="$CLAUDE_HOME/commands/vault"
SETTINGS="$CLAUDE_HOME/settings.json"

say()  { printf '[vault-install] %s\n' "$*"; }
warn() { printf '[vault-install] WARN: %s\n' "$*" >&2; }

# ---- detect Python ----
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  warn "Python 3 not found. Install Python 3 and re-run."
  exit 1
fi
say "Python: $($PYTHON --version 2>&1)"
say "Claude home: $CLAUDE_HOME"
say "Vault home : $VAULT_HOME"

mkdir -p "$CLAUDE_HOME/skills" "$CLAUDE_HOME/commands"

# ---- 1. install skill ----
mkdir -p "$SKILL_DST"
cp -f "$SKILL_SRC/SKILL.md" "$SKILL_DST/SKILL.md"
say "Installed skill → $SKILL_DST/SKILL.md"

# ---- 2. install slash commands ----
mkdir -p "$CMD_DST"
for f in init.md scan.md ingest.md; do
  cp -f "$CMD_SRC/$f" "$CMD_DST/$f"
done
say "Installed slash commands: /vault:init /vault:scan /vault:ingest"

# ---- 3. install global vault skeleton (do not overwrite existing files) ----
mkdir -p "$VAULT_HOME"/{sources/sessions,sources/prompts,decisions,concepts,entities,lessons,syntheses,archive,raw,scripts,state}

for f in CLAUDE.md index.md log.md .gitignore; do
  if [[ ! -e "$VAULT_HOME/$f" ]]; then
    cp "$TPL_GLOBAL/$f" "$VAULT_HOME/$f"
    say "Seeded $VAULT_HOME/$f"
  else
    say "Kept existing $VAULT_HOME/$f"
  fi
done

# ---- 4. install scripts (Python main + platform wrappers) ----
for f in scan-sessions.py vault-context.py scan-sessions.sh vault-context.sh scan-sessions.ps1 vault-context.ps1; do
  [[ -f "$SCRIPT_SRC/$f" ]] && cp -f "$SCRIPT_SRC/$f" "$VAULT_HOME/scripts/$f"
done
chmod +x "$VAULT_HOME/scripts/"*.sh "$VAULT_HOME/scripts/"*.py 2>/dev/null || true
say "Installed scripts: Python (.py) + Unix (.sh) + Windows (.ps1)"

touch "$VAULT_HOME/state/ingested.txt"

# ---- 5. git init vault if needed ----
if [[ ! -d "$VAULT_HOME/.git" ]]; then
  ( cd "$VAULT_HOME" && git init -q && git add . \
    && git commit -qm "chore(vault): initial skeleton from claude-obsidian-vault-skill" ) \
    || warn "git init skipped"
  say "Initialized git repo at $VAULT_HOME"
fi

# ---- 6. patch settings.json (synchronous vault-context SessionStart hook) ----
# vault-context.py scans the queue AND injects index + project entity + recent
# sessions into the session context as a system-reminder. Runs synchronously so
# Claude sees it before the first user message.
$PYTHON - "$SETTINGS" "$VAULT_HOME" "$PYTHON" <<'PY'
import json, sys
from pathlib import Path

settings_path, vault_home, python_exe = sys.argv[1], sys.argv[2], sys.argv[3]
p = Path(settings_path)
data = {}
if p.exists() and p.stat().st_size > 0:
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        print(f"[vault-install] WARN: could not parse {p}: {e}", file=sys.stderr)
        sys.exit(0)

hooks = data.setdefault("hooks", {})
session_hooks = hooks.setdefault("SessionStart", [])

# Already patched?
already = any(
    "vault-context.py" in str(h.get("command", ""))
    for entry in session_hooks if isinstance(entry, dict)
    for h in entry.get("hooks", []) if isinstance(h, dict)
)
if already:
    print("[vault-install] vault-context hook already present — no change")
    sys.exit(0)

# Remove legacy scan-sessions.sh hook (replaced by vault-context.py)
updated = []
for entry in session_hooks:
    if not isinstance(entry, dict):
        updated.append(entry)
        continue
    filtered = [h for h in entry.get("hooks", [])
                if "scan-sessions.sh" not in str(h.get("command", ""))]
    if filtered:
        updated.append({**entry, "hooks": filtered})
session_hooks[:] = updated

# Build cross-platform hook command using pathlib (no shell expansion needed)
hook_cmd = (
    f'{python_exe} -c "import pathlib,subprocess,sys; '
    f"p=pathlib.Path('{vault_home}')/'scripts'/'vault-context.py'; "
    f'subprocess.run([sys.executable,str(p)]) if p.exists() else None"'
)

session_hooks.append({
    "matcher": "",
    "hooks": [{"type": "command", "command": hook_cmd, "timeout": 30}]
})

p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2) + "\n")
print(f"[vault-install] Patched {p} with synchronous vault-context hook")
PY

say ""
say "Installation complete."
say "  1. Start a new Claude Code session — vault context is auto-injected."
say "  2. Run /vault:init inside a project to set up a project vault."
say "  3. Run /vault:ingest to process pending sessions."
say ""
say "Windows (no Git Bash): see README.md for manual settings.json setup."
