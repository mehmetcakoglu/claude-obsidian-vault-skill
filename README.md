# Claude Obsidian Vault Skill

> A hybrid, Obsidian-compatible knowledge vault for [Claude Code](https://docs.claude.com/en/docs/claude-code).
> Archives sessions, decisions, bugs, concepts, and entities into a persistent
> markdown wiki — split between a **global** vault (cross-project knowledge) and
> **per-project** vaults (project-specific knowledge).

Built on the **LLM-Wiki pattern** (`RAW → WIKI ← SCHEMA`) introduced by
[Selma Kocabıyık](https://github.com/selmakcby) in her
[knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline) repo.
This project adds Claude Code-specific packaging: slash commands,
auto-scanning of session transcripts, hybrid global/project scoping, and a
shared session-ID registry. See [`docs/ATTRIBUTION.md`](docs/ATTRIBUTION.md).

## What you get

| Piece | What it does |
|---|---|
| `/vault:init` slash command | Bootstraps `docs/vault/` for the current project, asks a few questions, fills in a CLAUDE.md template |
| `/vault:scan` slash command | Refreshes the pending-ingest queue (also runs automatically at session start) |
| `/vault:ingest` slash command | Processes the next pending Claude Code session into the appropriate vault |
| `vault` skill | Auto-activates whenever you mention archiving, prior decisions, bugs, or past sessions |
| `scan-sessions.py` | Scans `~/.claude/projects/*/*.jsonl` and writes a sorted queue (cross-platform Python) |
| `vault-context.py` | Injects vault context (index + project entity + recent sessions) into Claude at session start |
| `*.sh` / `*.ps1` | Thin wrappers that call the Python scripts (Unix / Windows) |
| Global vault skeleton | Lives at `~/claude-vault/` (configurable via `$CLAUDE_VAULT`) |
| `SessionStart` hook | Injects vault context synchronously on every new conversation |

## Install

### Option A — Claude Code plugin (recommended)

Inside Claude Code:

```
/plugin marketplace add mehmetcakoglu/claude-obsidian-vault-skill
/plugin install vault@claude-obsidian-vault-skill
```

That's it. The plugin brings the skill, the three slash commands
(`/vault:init`, `/vault:scan`, `/vault:ingest`), and the `SessionStart` hook
with it. On first launch the hook seeds `~/claude-vault/` from the plugin's
bundled templates if it doesn't exist yet.

Custom vault location:

```
# in your shell profile (before starting Claude Code)
export CLAUDE_VAULT=/some/other/path
```

### Option B — Standalone install (no plugin system)

Use this if you want a git-managed copy on disk instead of going through the
plugin system:

```bash
git clone https://github.com/mehmetcakoglu/claude-obsidian-vault-skill.git
cd claude-obsidian-vault-skill
./install.sh
```

The installer is idempotent — rerun it any time to update the skill/commands.
It:
- Copies the skill to `~/.claude/skills/vault/`
- Copies the slash commands to `~/.claude/commands/vault/`
- Seeds `~/claude-vault/` with CLAUDE.md, index.md, log.md, .gitignore, and
  the scan script (won't overwrite existing files)
- Patches `~/.claude/settings.json` to register the SessionStart hook (safe:
  normalizes paths and deduplicates)
- `git init`s the global vault if it isn't a repo yet

Custom vault location:

```bash
CLAUDE_VAULT=/some/other/path ./install.sh
```

## Usage

### In a new project

```
cd my-project/
# inside Claude Code:
/vault:init
```

The command auto-detects your stack (Python/Node/Go/Rust/Ruby/Docker…) and asks
a few clarifying questions. It then writes `docs/vault/` with a filled-in
CLAUDE.md, index.md, log.md, and .gitignore.

### Archiving a past session

After any conversation ends (>10 min since last message), it shows up in the
queue. To process it:

```
/vault:scan      # optional — hook runs this automatically anyway
/vault:ingest    # processes the next (biggest) session, asks for approval, writes pages, commits
```

If the session belonged to a project that has `docs/vault/CLAUDE.md`, the pages
go into the project vault. Otherwise they go to the global vault. The session
ID lands in the shared `state/ingested.txt` registry either way.

### Asking questions (QUERY)

Just ask. The skill activates on phrases like _"what did we decide about X"_,
_"have we seen this bug before"_, _"why did we choose Y"_. It reads the right
`index.md`, follows the links, and cites sources in its answer.

### Vault hygiene (LINT)

```
# inside Claude Code:
check the vault
```

or `/vault:lint` if you've added that command. Orphan pages, stale claims,
dead `related_code` paths, duplicate entities → a report at
`syntheses/lint-YYYY-MM-DD.md`.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                   ~/.claude/projects/*/*.jsonl                       │
│             (raw Claude Code session transcripts)                    │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ vault-context.py (SessionStart hook, sync)
                            │   ├─ scans pending queue
                            │   ├─ auto-creates project entity
                            │   └─ injects context → Claude system-reminder
                            ▼
               ~/claude-vault/state/pending.md   (queue)
                            │
                            │ /vault:ingest (user-triggered)
                            ▼
        ┌─────────────────────┴──────────────────────┐
        │                                             │
        ▼                                             ▼
  Global vault                              Project vault
  ~/claude-vault/                           <repo>/docs/vault/
  • cross-project decisions                 • domain rules
  • Claude Code patterns                    • architectural decisions
  • tool lessons                            • bug/fix history
  • personal preferences                    • entities
        │                                             │
        └──────────────► shared ingested.txt ◄────────┘
             (a session is never ingested twice)
```

## Philosophy: semi-automatic

**Scan + context injection are automatic. Ingest is user-triggered.**

At every session start, `vault-context.py` runs synchronously and:
1. Refreshes the pending queue (cheap scan, non-destructive)
2. Auto-creates a project entity if none exists
3. Injects vault context into Claude as a `system-reminder` — past decisions
   and lessons are available **before the first message**, no manual query

Ingest is the only step that stays user-triggered: it writes files, decides
routing, and filters secrets. That deserves human review every time — a 5–7
bullet summary with an approval gate keeps token cost bounded and prevents
misclassification or accidental secret leakage.

## Compatibility

| Platform | Support |
|---|---|
| macOS | ✅ Full support |
| Linux | ✅ Full support |
| Windows (Git Bash / WSL) | ✅ Full support via `install.sh` |
| Windows (PowerShell / cmd) | ✅ Use `.ps1` wrappers; add hook manually (see below) |
| Claude.ai web / Claude Work | ❌ No local filesystem access |

### Windows manual setup (PowerShell)

1. Copy `plugins/vault/scripts/` to `%USERPROFILE%\claude-vault\scripts\`
2. Copy `plugins/vault/commands/` to `%USERPROFILE%\.claude\commands\vault\`
3. Copy `plugins/vault/skills/vault/SKILL.md` to `%USERPROFILE%\.claude\skills\vault\SKILL.md`
4. Add to `%USERPROFILE%\.claude\settings.json` → `hooks.SessionStart`:

```json
{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "python -c \"import pathlib,subprocess,sys; p=pathlib.Path.home()/'claude-vault'/'scripts'/'vault-context.py'; subprocess.run([sys.executable,str(p)]) if p.exists() else None\"",
    "timeout": 30
  }]
}
```

> Replace `python` with `python3` if that's what's in your PATH.

**Requires Python 3** in PATH on all platforms.

## License

MIT. See [`LICENSE`](LICENSE).

## Credits

- LLM-Wiki pattern (RAW → WIKI ← SCHEMA) and the INGEST/QUERY/LINT vocabulary:
  **[Selma Kocabıyık](https://github.com/selmakcby)** — see
  [knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline).
- Claude Code packaging (auto-scan, slash commands, hybrid scoping, session
  registry): **[Mehmet Çakoğlu](https://github.com/mehmetcakoglu)** — this
  repository.

See [`docs/ATTRIBUTION.md`](docs/ATTRIBUTION.md) for the full attribution.
