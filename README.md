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
| `scan-sessions.sh` | Scans `~/.claude/projects/*/*.jsonl` and writes a sorted queue |
| Global vault skeleton | Lives at `~/claude-vault/` (configurable via `$CLAUDE_VAULT`) |
| `SessionStart` hook | Runs the scan in the background on every new conversation |

## Install

```bash
git clone https://github.com/mehmetcakoglu/claude-obsidian-vault-skill.git
cd claude-obsidian-vault-skill
./install.sh
```

The installer is idempotent — rerun it any time to update the skill/commands.
It:
- Copies the skill to `~/.claude/skills/vault/`
- Copies the slash commands to `~/.claude/commands/vault/`
- Seeds `~/claude-vault/` with a CLAUDE.md, index.md, log.md, .gitignore, and
  the scan script (won't overwrite existing files)
- Patches `~/.claude/settings.json` to register the SessionStart hook (safe:
  deduplicates by command string)
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
                            │ scan-sessions.sh (SessionStart hook)
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

**Scan is automatic. Ingest is user-triggered.** This is deliberate:

- Scanning is cheap and non-destructive — let it run on every session start.
- Ingest writes files, decides routing, and filters secrets. That deserves
  human review: a 5–7 bullet summary with an approval gate every time.

This keeps token use bounded and prevents misclassification or accidental
secret leakage into a vault.

## Compatibility

- **Claude Code** (CLI, VS Code extension, Cursor, Antigravity) — full support
- **Claude.ai web chat / Claude Work** — **not supported**: no local filesystem
  access. The vault is an on-disk artifact.

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
