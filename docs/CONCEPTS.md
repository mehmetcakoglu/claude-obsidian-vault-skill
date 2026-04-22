# Concepts

A quick tour of the ideas this skill implements. For the original formulation
see [Selma Kocabıyık's knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline).

## RAW → WIKI ← SCHEMA

Three layers, each with one job:

```
       RAW                     WIKI                    SCHEMA
   source material     →  hand-maintained wiki  ←  rulebook (CLAUDE.md)
   (sessions, PDFs,        (markdown pages,          (how to ingest,
   PR descriptions,         YAML frontmatter,         what sections,
   transcripts)             [[wiki-links]])           naming rules)
```

- **RAW is immutable.** You never edit a transcript. If it's wrong, you write
  a correction page that cites the transcript.
- **WIKI is atomic and append-mostly.** One decision per file. Old pages move
  to `archive/`, they don't get deleted.
- **SCHEMA is the constitution.** Every LLM agent reads `CLAUDE.md` before
  touching the vault; the rules stay consistent across weeks, LLMs, and
  humans.

## INGEST / QUERY / LINT

The three verbs that keep the wiki alive.

### INGEST (source → pages)

Pull a new source into the wiki.

1. Parse in a sandbox (avoid flooding the LLM's context with raw transcripts).
2. Summarize for the user. Get approval.
3. Write atomic pages: `sources/sessions/…`, plus whichever `decisions/`,
   `bugs/`, `concepts/`, `entities/` pages are justified.
4. Update `index.md`. Append to `log.md`. Commit with `docs(vault):`.

### QUERY (question → answer)

Answer a question using the wiki.

1. Read `index.md` first — it's the hand-maintained search surface.
2. Follow `[[wiki-links]]` to the actually relevant pages.
3. Synthesize an answer with citations.
4. If the synthesis is novel (combines multiple sources in a new way), file it
   back as `syntheses/YYYY-MM-DD-<slug>.md` so the wiki gets smarter over time.

### LINT (health check)

Periodically audit the vault for:

- **Orphans** — pages nothing else links to
- **Stale claims** — `status: active` pages older than 60 days that contradict
  newer sources
- **Missing concepts** — terms referenced in ≥3 pages but with no page of their
  own
- **One-way links** — A links to B, but B doesn't link back
- **Dead `related_code`** — file paths that no longer exist
- **Duplicate entities** — two pages describing the same thing

The output is itself a wiki page: `syntheses/lint-YYYY-MM-DD.md`.

## Hybrid vaults (Claude Code addition)

| Vault | Location | Content |
|---|---|---|
| Global | `~/claude-vault/` | Cross-project: Claude Code patterns, general tooling, personal preferences |
| Project | `<repo>/docs/vault/` | Project-specific: domain rules, architecture, bugs, entities |

**Rule of thumb:** if the knowledge is useful in a project you don't have yet,
it's global. If it only makes sense inside the current codebase, it's project.

**Why split?** A project vault gets cloned with the repo — the domain history
travels with the code. The global vault sticks with you across projects and
captures lessons about Claude Code itself, your tooling habits, recurring
debugging patterns.

**Shared registry.** Both vaults share
`~/claude-vault/state/ingested.txt`, so a session that was ingested into a
project vault is never re-queued for the global vault.

## Semi-automatic ingest (Claude Code addition)

**Scan is automatic; ingest is user-triggered.**

A `SessionStart` hook runs `scan-sessions.sh --quiet` on every new
conversation. It walks `~/.claude/projects/*/*.jsonl`, skips live sessions
(mtime < 10 min), skips already-ingested IDs, and writes a sorted queue at
`~/claude-vault/state/pending.md`.

The user triggers `/vault:ingest` when they want to process the next session.
The LLM parses it in a sandbox, summarizes, waits for approval, writes pages,
commits. One session per invocation — reviewable, bounded token cost.

## Atomicity

One idea per page. One decision, one bug, one concept. If a single session
touches three decisions and two bugs, you write five pages plus the session
summary. This discipline makes the wiki navigable — every link points to a
focused page, not a grab-bag.

## Sourcelessness is a bug

Every page has:

- a `source:` field in frontmatter
- a `## Sources` section at the bottom

If you can't cite it, you can't claim it. That's the single most important
rule — it keeps the wiki honest across time.
