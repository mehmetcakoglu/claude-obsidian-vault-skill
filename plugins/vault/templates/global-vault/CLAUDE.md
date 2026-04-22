# Global Claude Vault — Constitution

This file is the **schema** for the global vault. It governs how Claude Code agents
ingest, query, and maintain pages across every project on this machine.

## 1. Scope

The global vault holds **cross-project, domain-agnostic** knowledge:

- Claude Code patterns (hooks, skills, slash commands, MCP servers)
- General development workflows (git, CI, testing, packaging)
- Tooling lessons (editor, shell, container, cloud)
- Personal style and collaboration preferences
- Reusable concepts that apply to more than one project

## 2. Out of scope

Do **not** write into the global vault:

- Project-specific architecture, domain rules, entities, bugs — those belong in
  the project's own `docs/vault/` (create one with `/vault:init`).
- NDA or confidential material — does not belong in any shared vault.
- Ephemeral conversation state — use TodoWrite / plan mode / memory files.
- Runtime instructions (e.g. "always use Sonnet 4.6") — those belong in
  `~/.claude/CLAUDE.md`, not in the vault.

## 3. Directory layout

```
~/claude-vault/
├── CLAUDE.md          # this file (schema)
├── index.md           # hand-maintained search surface
├── log.md             # chronological ingest log
├── sources/
│   ├── sessions/      # Claude Code session summaries (YYYY-MM-DD-<slug>.md)
│   └── prompts/       # reusable prompt templates
├── decisions/         # cross-project architectural decisions
├── concepts/          # reusable domain-agnostic concepts
├── entities/          # tools, frameworks, services I use across projects
├── lessons/           # failure stories: symptom → root cause → fix → prevention
├── syntheses/         # filed-back answers and lint reports
├── archive/           # outdated pages (never delete — move here)
├── raw/               # immutable source material (gitignored for large files)
└── state/             # scan/ingest state — not hand-edited
    ├── pending.md     # auto-generated queue (gitignored)
    └── ingested.txt   # shared session ID registry
```

## 4. Page format

Every page starts with YAML frontmatter:

```yaml
---
title: Descriptive page title
tags: [tag1, tag2]
source: "sources/sessions/YYYY-MM-DD-<slug>.md"  # required
date: YYYY-MM-DD
status: draft | active | archived
related_code: "path/to/file.py:line_range"       # optional
session_size: "30M, 3451 messages"               # only for sources/sessions/
---
```

Body: markdown. Every non-trivial claim points to a source — either
`[[sources/...]]` or an external URL. Close the page with a `## Sources`
section and a `## Related` section.

## 5. Sections by page type

- **sources/sessions/** — Purpose · What happened · Files touched · Decisions · Bugs/fixes · Open questions
- **decisions/** — Context · Decision · Alternatives · Rationale · Affected code · Consequences
- **entities/** — Definition · Responsibility · Related files · Relationships · Key decisions
- **concepts/** — Definition · Rule/formula · Examples · Related entities · Rationale
- **lessons/** — Symptoms · Reproduction · Root cause · Fix · Regression test · Prevention

## 6. File naming

- Kebab-case, ASCII only. Transliterate non-ASCII (`ı→i`, `ş→s`, `ğ→g`, `ü→u`, `ö→o`, `ç→c`, etc.).
- Date-prefixed where it helps chronological sort: `YYYY-MM-DD-<slug>.md`.
- No spaces, no special characters other than `-`.

## 7. Cross-linking

- Use `[[relative/path/page.md]]` for Obsidian-compatible links.
- Every page should have at least one inbound link from `index.md` or another page.
- When you link A → B, consider whether B should also link back to A.

## 8. Hard rules (inviolable)

1. **`raw/` is immutable.** Source material never changes. JSONL transcripts are
   gitignored; link with symlinks or paths.
2. **No sourceless claims.** Every page has a `source` frontmatter field and a
   `## Sources` section in the body.
3. **No deletions.** Outdated pages move to `archive/` — git history preserves
   the rest.
4. **Contradictions are visible.** If two sources disagree, mark a `## CONFLICT`
   section. When resolved, rename it `## RESOLVED (YYYY-MM-DD)` — do not delete
   the context.
5. **`index.md` is updated on every ingest/lint.** It is the primary search
   surface at small-to-medium scale.
6. **Security.** API keys, tokens, passwords, production IPs, database
   credentials are **never** written into any vault page. Use placeholders like
   `stored in env` or `redacted`, and note the exclusion in `log.md`.
7. **Commit prefix.** All vault commits use the `docs(vault):` prefix so they
   can be filtered in PR review.
8. **Atomicity.** One decision = one page. One bug = one page. Do not merge.
9. **Vault language.** Pick a single primary language for this vault and stay
   consistent across pages; technical terms may remain in English regardless.

## 9. Workflows

### INGEST (source → pages)

1. Read `pending.md` or accept an explicit session-ID argument.
2. Parse the source via a sandbox execution tool (`ctx_execute`,
   `ctx_execute_file`, or a local python helper). Never `Read` multi-megabyte
   transcripts — they overflow the context window.
3. Present a 5–7 bullet summary to the user; wait for approval.
4. After approval, write pages in the appropriate directories (see §3).
5. Update `index.md` and append a log entry.
6. Append the session ID to `state/ingested.txt`.
7. Re-run `scan-sessions.sh --quiet` to refresh `pending.md`.
8. Commit with a `docs(vault):` prefix.

### QUERY (question → answer)

1. Open `index.md`.
2. Follow links to the relevant source/entity/decision/concept pages.
3. Synthesize the answer with source citations.
4. If the synthesis is novel, file it back as
   `syntheses/YYYY-MM-DD-<slug>.md` and log it.

### LINT (health check)

Check for: orphan pages, stale `active` pages older than 60 days contradicting
newer sources, missing concepts (referenced 3+ times without their own page),
one-way links (A→B without B→A), dead `related_code` paths, duplicate entities.
Produce `syntheses/lint-YYYY-MM-DD.md` and log it.

## 10. Semi-automatic ingest flow

- A `SessionStart` hook runs `scan-sessions.sh --quiet` on every new
  conversation, keeping `state/pending.md` fresh.
- The user triggers `/vault:ingest` when they want to process the next
  session — one at a time, reviewable, token-bounded.
- The session registry (`state/ingested.txt`) is shared between the global
  vault and every project vault, so a session ingested into a project is not
  re-proposed for the global vault.

## 11. Credits

The LLM-Wiki pattern this vault implements was introduced by
[Selma Kocabıyık](https://github.com/selmakcby) in the
[knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline) repository.
This Claude Code packaging (auto-scan, slash commands, hybrid scoping) is a
derivative, distributed under MIT in
[claude-obsidian-vault-skill](https://github.com/mehmetcakoglu/claude-obsidian-vault-skill).
