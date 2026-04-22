#!/usr/bin/env bash
# claude-obsidian-vault-skill installer
#
# Idempotent. Installs the vault skill, slash commands, scan script, and a
# global-vault skeleton. Patches Claude Code's settings.json to register a
# SessionStart hook that keeps the pending-ingest queue fresh.
#
# Usage:
#   ./install.sh                 # install into defaults (~/.claude, ~/claude-vault)
#   CLAUDE_VAULT=/path ./install.sh     # custom vault location
#
# Rerun-safe: existing files are left in place; the settings.json hook is
# deduplicated by command string.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
VAULT_HOME="${CLAUDE_VAULT:-$HOME/claude-vault}"

SKILL_SRC="$REPO_ROOT/skill"
CMD_SRC="$REPO_ROOT/commands"
SCRIPT_SRC="$REPO_ROOT/scripts"
TPL_GLOBAL="$REPO_ROOT/templates/global-vault"

SKILL_DST="$CLAUDE_HOME/skills/vault"
CMD_DST="$CLAUDE_HOME/commands/vault"
SETTINGS="$CLAUDE_HOME/settings.json"

say() { printf '[vault-install] %s\n' "$*"; }
warn() { printf '[vault-install] WARN: %s\n' "$*" >&2; }

# ---- 1. sanity ----
command -v python3 >/dev/null 2>&1 || { warn "python3 is required"; exit 1; }

say "Claude home: $CLAUDE_HOME"
say "Vault home : $VAULT_HOME"

mkdir -p "$CLAUDE_HOME/skills" "$CLAUDE_HOME/commands"

# ---- 2. install skill ----
mkdir -p "$SKILL_DST"
cp -f "$SKILL_SRC/SKILL.md" "$SKILL_DST/SKILL.md"
say "Installed skill: $SKILL_DST/SKILL.md"

# ---- 3. install slash commands ----
mkdir -p "$CMD_DST"
for f in init.md scan.md ingest.md; do
  cp -f "$CMD_SRC/$f" "$CMD_DST/$f"
done
say "Installed slash commands: /vault:init /vault:scan /vault:ingest"

# ---- 4. install global vault skeleton (do not overwrite if already present) ----
mkdir -p "$VAULT_HOME"/{sources/sessions,sources/prompts,decisions,concepts,entities,lessons,syntheses,archive,raw,scripts,state}

for f in CLAUDE.md index.md log.md .gitignore; do
  if [[ ! -e "$VAULT_HOME/$f" ]]; then
    cp "$TPL_GLOBAL/$f" "$VAULT_HOME/$f"
    say "Seeded $VAULT_HOME/$f"
  else
    say "Kept existing $VAULT_HOME/$f"
  fi
done

cp -f "$SCRIPT_SRC/scan-sessions.sh" "$VAULT_HOME/scripts/scan-sessions.sh"
chmod +x "$VAULT_HOME/scripts/scan-sessions.sh"
say "Installed scan script: $VAULT_HOME/scripts/scan-sessions.sh"

touch "$VAULT_HOME/state/ingested.txt"

# ---- 5. git init the vault if it isn't already a repo ----
if [[ ! -d "$VAULT_HOME/.git" ]]; then
  ( cd "$VAULT_HOME" && git init -q && git add . && git commit -qm "chore(vault): initial skeleton from claude-obsidian-vault-skill" ) || warn "git init skipped"
  say "Initialized git repo at $VAULT_HOME"
fi

# ---- 6. patch settings.json (SessionStart hook) ----
HOOK_CMD="$VAULT_HOME/scripts/scan-sessions.sh --quiet"

python3 - "$SETTINGS" "$HOOK_CMD" "$VAULT_HOME" <<'PY'
import json, os, re, sys
from pathlib import Path

settings_path, hook_cmd, vault_home = sys.argv[1], sys.argv[2], sys.argv[3]
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

# Normalize paths for dedupe: expand $HOME, $CLAUDE_VAULT, ~, resolve to real path.
def _norm(cmd: str) -> str:
    if not cmd:
        return ""
    s = cmd
    s = s.replace("$CLAUDE_VAULT", vault_home)
    s = s.replace("${CLAUDE_VAULT}", vault_home)
    s = s.replace("$HOME", os.environ.get("HOME", ""))
    s = s.replace("${HOME}", os.environ.get("HOME", ""))
    s = os.path.expanduser(s)
    return re.sub(r"\s+", " ", s).strip()

target = _norm(hook_cmd)

def _cmds(entry):
    return [_norm(h.get("command", "")) for h in entry.get("hooks", []) if isinstance(h, dict)]

already = any(target in _cmds(e) for e in session_hooks if isinstance(e, dict))

if already:
    print("[vault-install] SessionStart hook already present — no change")
    sys.exit(0)

session_hooks.append({
    "matcher": "startup",
    "hooks": [{
        "type": "command",
        "command": hook_cmd,
        "run_in_background": True,
        "timeout": 20
    }]
})

p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2) + "\n")
print(f"[vault-install] Patched {p} with SessionStart hook")
PY

say "Done. Start a new Claude Code session and the pending queue will auto-scan."
say "Next: cd into a project and run /vault:init to set up its project vault."
