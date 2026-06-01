# claude-obsidian-vault-skill installer — Windows PowerShell
#
# Idempotent. Installs the vault skill, slash commands, scripts, and a
# global-vault skeleton. Patches Claude Code's settings.json to register a
# synchronous SessionStart hook that injects vault context at session start.
#
# Requirements: Python 3 (python3 or python in PATH)
#
# Usage:
#   .\install.ps1                                    # install into defaults
#   $env:CLAUDE_VAULT = "D:\my-vault" ; .\install.ps1  # custom vault location
#
# Tested on Windows 10/11 with PowerShell 5.1 and 7+.

$ErrorActionPreference = "Stop"

$RepoRoot    = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeHome  = if ($env:CLAUDE_HOME)  { $env:CLAUDE_HOME  } else { Join-Path $env:USERPROFILE ".claude" }
$VaultHome   = if ($env:CLAUDE_VAULT) { $env:CLAUDE_VAULT } else { Join-Path $env:USERPROFILE "Global Claude Vault" }

$PluginSrc  = Join-Path $RepoRoot  "plugins\vault"
$SkillSrc   = Join-Path $PluginSrc "skills\vault"
$CmdSrc     = Join-Path $PluginSrc "commands"
$ScriptSrc  = Join-Path $PluginSrc "scripts"
$TplGlobal  = Join-Path $PluginSrc "templates\global-vault"

$SkillDst   = Join-Path $ClaudeHome "skills\vault"
$CmdDst     = Join-Path $ClaudeHome "commands\vault"
$Settings   = Join-Path $ClaudeHome "settings.json"

function Say  { param($msg) Write-Host "[vault-install] $msg" }
function Warn { param($msg) Write-Warning "[vault-install] WARN: $msg" }

# ---- detect Python ----
$Python = $null
foreach ($candidate in @("python3", "python")) {
    try {
        $ver = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0) { $Python = $candidate; break }
    } catch { }
}
if (-not $Python) {
    Warn "Python 3 not found. Install Python 3 and re-run."
    exit 1
}
$pyVer = & $Python --version 2>&1
Say "Python: $pyVer"
Say "Claude home: $ClaudeHome"
Say "Vault home : $VaultHome"

New-Item -ItemType Directory -Force -Path (Join-Path $ClaudeHome "skills")   | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ClaudeHome "commands") | Out-Null

# ---- 1. install skill ----
New-Item -ItemType Directory -Force -Path $SkillDst | Out-Null
Copy-Item -Force (Join-Path $SkillSrc "SKILL.md") (Join-Path $SkillDst "SKILL.md")
Say "Installed skill → $SkillDst\SKILL.md"

# ---- 2. install slash commands ----
New-Item -ItemType Directory -Force -Path $CmdDst | Out-Null
$commands = @("init.md","scan.md","ingest.md","batch-ingest.md","auto-ingest.md","update.md","status.md","help.md","skip.md","doctor.md")
foreach ($f in $commands) {
    $src = Join-Path $CmdSrc $f
    if (Test-Path $src) { Copy-Item -Force $src (Join-Path $CmdDst $f) }
}
Say "Installed slash commands: /vault:init /vault:scan /vault:ingest /vault:batch-ingest /vault:auto-ingest /vault:update /vault:status /vault:help /vault:skip /vault:doctor"

# ---- 3. install global vault skeleton (do not overwrite existing files) ----
$vaultDirs = @(
    "sources\sessions","sources\prompts","decisions","concepts",
    "entities","lessons","syntheses","archive","raw","scripts","state"
)
foreach ($d in $vaultDirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $VaultHome $d) | Out-Null
}

foreach ($f in @("CLAUDE.md","index.md","log.md",".gitignore","vault-config.json")) {
    $dst = Join-Path $VaultHome $f
    if (-not (Test-Path $dst)) {
        Copy-Item (Join-Path $TplGlobal $f) $dst
        Say "Seeded $dst"
    } else {
        Say "Kept existing $dst"
    }
}

# ---- 4. install scripts ----
$scripts = @("scan-sessions.py","vault-context.py","scan-sessions.ps1","vault-context.ps1","scan-sessions.sh","vault-context.sh")
foreach ($f in $scripts) {
    $src = Join-Path $ScriptSrc $f
    if (Test-Path $src) {
        Copy-Item -Force $src (Join-Path $VaultHome "scripts\$f")
    }
}
Say "Installed scripts: Python (.py) + Unix (.sh) + Windows (.ps1)"

$ingestedTxt = Join-Path $VaultHome "state\ingested.txt"
if (-not (Test-Path $ingestedTxt)) { New-Item -ItemType File -Path $ingestedTxt | Out-Null }

# ---- record source repo path ----
$RepoRoot | Set-Content -Path (Join-Path $VaultHome "state\plugin-source.txt") -Encoding UTF8
Say "Recorded source path → $VaultHome\state\plugin-source.txt"

# ---- 5. git init vault if needed ----
$gitDir = Join-Path $VaultHome ".git"
if (-not (Test-Path $gitDir)) {
    try {
        Push-Location $VaultHome
        git init -q
        git add .
        git commit -qm "chore(vault): initial skeleton from claude-obsidian-vault-skill"
        Pop-Location
        Say "Initialized git repo at $VaultHome"
    } catch {
        Warn "git init skipped: $_"
        if ((Get-Location).Path -ne $RepoRoot) { Pop-Location }
    }
}

# ---- 6. patch settings.json (synchronous vault-context SessionStart hook) ----
$patchScript = @"
import json, sys
from pathlib import Path

settings_path, vault_home, python_exe = sys.argv[1], sys.argv[2], sys.argv[3]
p = Path(settings_path)
data = {}
if p.exists() and p.stat().st_size > 0:
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        print(f'[vault-install] WARN: could not parse {p}: {e}', file=sys.stderr)
        sys.exit(0)

hooks = data.setdefault('hooks', {})
session_hooks = hooks.setdefault('SessionStart', [])

already = any(
    'vault-context.py' in str(h.get('command', ''))
    for entry in session_hooks if isinstance(entry, dict)
    for h in entry.get('hooks', []) if isinstance(h, dict)
)
if already:
    print('[vault-install] vault-context hook already present - no change')
    sys.exit(0)

# Remove legacy scan-sessions.sh hook
updated = []
for entry in session_hooks:
    if not isinstance(entry, dict):
        updated.append(entry)
        continue
    filtered = [h for h in entry.get('hooks', [])
                if 'scan-sessions.sh' not in str(h.get('command', ''))]
    if filtered:
        updated.append({**entry, 'hooks': filtered})
session_hooks[:] = updated

vault_fwd = vault_home.replace('\\\\', '/')
# Pass vault path as argv[1] so vault-context.py uses the correct path without relying on env var.
hook_cmd = (
    f'{python_exe} -c "import pathlib,subprocess,sys,os; '
    f"vault=pathlib.Path(os.environ.get('CLAUDE_VAULT','{vault_fwd}')); "
    f"p=vault/'scripts'/'vault-context.py'; "
    f'subprocess.run([sys.executable,str(p),str(vault)]) if p.exists() else None"'
)

session_hooks.append({
    'matcher': '',
    'hooks': [{'type': 'command', 'command': hook_cmd, 'timeout': 30}]
})

p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2) + '\n')
print(f'[vault-install] Patched {p} with synchronous vault-context hook')
"@

$tmpScript = Join-Path $env:TEMP "vault_patch_$([System.Guid]::NewGuid().ToString('N')).py"
$patchScript | Set-Content -Path $tmpScript -Encoding UTF8
try {
    & $Python $tmpScript $Settings $VaultHome $Python
} finally {
    Remove-Item -Force $tmpScript -ErrorAction SilentlyContinue
}

Say ""
Say "Installation complete."
Say "  1. Start a new Claude Code session - vault context is auto-injected."
Say "  2. Run /vault:init inside a project to set up a project vault."
Say "  3. Run /vault:ingest to process the next pending session."
Say "     Run /vault:batch-ingest [N] to process up to N sessions at once (default 5)."
Say "  4. Run /vault:auto-ingest on|off to toggle automatic session processing."
Say ""

# ---- 7. post-install verification ----
Say ""
Say "Verifying installation..."
$VerifyOK = $true

foreach ($script in @("scan-sessions.py","vault-context.py")) {
    $path = Join-Path $VaultHome "scripts\$script"
    if (Test-Path $path) { Say "  OK $script" }
    else { Warn "  FAIL $script not found at $path"; $VerifyOK = $false }
}

$skillFile = Join-Path $SkillDst "SKILL.md"
if (Test-Path $skillFile) { Say "  OK skill (SKILL.md)" }
else { Warn "  FAIL skill not found at $skillFile"; $VerifyOK = $false }

foreach ($cmd in @("init","scan","ingest","batch-ingest","auto-ingest","update","status","help","skip","doctor")) {
    $path = Join-Path $CmdDst "$cmd.md"
    if (Test-Path $path) { Say "  OK /vault:$cmd" }
    else { Warn "  FAIL /vault:$cmd not found"; $VerifyOK = $false }
}

if (Test-Path $Settings) {
    $settingsContent = Get-Content $Settings -Raw
    if ($settingsContent -match "vault-context\.py") {
        Say "  OK SessionStart hook registered in $Settings"
    } else {
        Warn "  FAIL SessionStart hook not found in $Settings"
        $VerifyOK = $false
    }
} else {
    Warn "  FAIL settings.json not found at $Settings"
    $VerifyOK = $false
}

$pyCheck = & $Python -c "import json, pathlib, subprocess, re, datetime" 2>&1
if ($LASTEXITCODE -eq 0) { Say "  OK Python dependencies OK" }
else { Warn "  FAIL Python dependency check failed: $pyCheck"; $VerifyOK = $false }

Say ""
if ($VerifyOK) {
    Say "All checks passed. Start a new Claude Code session to activate vault context."
} else {
    Warn "Some checks failed - review warnings above and re-run install.ps1 if needed."
}
