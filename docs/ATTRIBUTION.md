# Attribution

## Upstream work — LLM-Wiki pattern

This project is a derivative of the **LLM-Wiki pattern** (also called
"RAW → WIKI ← SCHEMA") introduced by **[Selma Kocabıyık](https://github.com/selmakcby)**
in the open-source project
[knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline).

Selma's project defines the core ideas that this repository builds on:

- **RAW / WIKI / SCHEMA separation** — immutable source material, a
  hand-maintained wiki, and a rulebook (CLAUDE.md) that governs both.
- **INGEST / QUERY / LINT operations** — the three canonical verbs for
  maintaining the wiki over time.
- **Atomic pages** — one decision, one bug, one concept per file.
- **Obsidian-compatible markdown** — YAML frontmatter + `[[wiki-link]]`
  cross-references as the knowledge substrate.
- **Sourceless-claim prohibition** — every claim points to a source.
- **`archive/` instead of delete** — outdated pages move, never disappear.

Selma's `knowledge-pipeline` is distributed under the MIT license. This
project retains that license (see [`../LICENSE`](../LICENSE)) and adopts the
same terms.

## Downstream additions — Claude Code packaging

This repository ([claude-obsidian-vault-skill](https://github.com/mehmetcakoglu/claude-obsidian-vault-skill))
adds Claude Code-specific packaging on top of the LLM-Wiki pattern. Nothing
below changes the core pattern — they are operational conveniences:

- **Slash commands**: `/vault:init`, `/vault:scan`, `/vault:ingest` — wired
  to Claude Code's slash-command system under `~/.claude/commands/vault/`.
- **Auto-registered skill**: `~/.claude/skills/vault/SKILL.md` with a
  frontmatter description that activates the skill whenever the user mentions
  archiving, past decisions, bugs, or prior sessions.
- **Cross-platform scripts** (pure Python 3, stdlib only):
  - `scan-sessions.py` — scans `~/.claude/projects/*/*.jsonl` and writes a
    sorted pending-ingest queue; replaces the original `scan-sessions.sh`.
  - `vault-context.py` — synchronous `SessionStart` hook: scans the queue,
    auto-creates a project entity if absent, and injects vault context (index,
    project entity, recent sessions, pending count) into Claude's session as a
    `system-reminder`. Claude has past decisions and lessons loaded before the
    first user message.
  - Unix `.sh` and Windows `.ps1` wrappers are one-liners that delegate to the
    Python scripts.
- **`SessionStart` hook**: runs `vault-context.py` **synchronously** on every
  new conversation — context injection + scan in a single pass, zero manual
  steps for the user.
- **Auto project entity**: on first visit to a project, `vault-context.py`
  detects the stack and creates `entities/<slug>.md` automatically.
- **Hybrid scoping**: a **global vault** (`~/claude-vault/`) for
  cross-project knowledge alongside **per-project vaults** (`docs/vault/`) for
  project-specific knowledge.
- **Shared session registry**: `state/ingested.txt` is shared between the
  global vault and every project vault, so a session ingested into a project
  is never re-queued for the global vault (and vice versa).
- **Installer**: `install.sh` detects `python3`/`python`, copies all scripts
  (`.py` + `.sh` + `.ps1`), is idempotent, patches `settings.json` safely
  (deduplicates the hook, removes the old async scan hook), and seeds both
  vaults. Windows users without Git Bash can follow the manual steps in
  `README.md`.

## If you build on this

If you derive your own work from this project, please keep attribution to both:

1. Selma Kocabıyık's [knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline)
   (upstream — the pattern itself).
2. This repository — if you use the Claude Code-specific packaging, skill
   wrappers, or slash commands.

A one-line mention and a link back in your README is enough.
