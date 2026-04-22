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
- **Session scanner**: `scripts/scan-sessions.sh` scans
  `~/.claude/projects/*/*.jsonl` and writes a sorted pending-ingest queue.
- **`SessionStart` hook**: runs the scanner in the background on every new
  conversation, so the queue is always fresh without the user doing anything.
- **Hybrid scoping**: a **global vault** (`~/claude-vault/`) for
  cross-project knowledge alongside **per-project vaults** (`docs/vault/`) for
  project-specific knowledge.
- **Shared session registry**: `state/ingested.txt` is shared between the
  global vault and every project vault, so a session ingested into a project
  is never re-queued for the global vault (and vice versa).
- **Installer**: `install.sh` is idempotent, patches `settings.json` safely
  (deduplicates the hook by command string), and seeds both vaults.

## If you build on this

If you derive your own work from this project, please keep attribution to both:

1. Selma Kocabıyık's [knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline)
   (upstream — the pattern itself).
2. This repository — if you use the Claude Code-specific packaging, skill
   wrappers, or slash commands.

A one-line mention and a link back in your README is enough.
