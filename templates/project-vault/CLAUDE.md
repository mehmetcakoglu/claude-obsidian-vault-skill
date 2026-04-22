# {{PROJECT_NAME}} Vault — Constitution

This file is the **schema** for the project's vault. Claude Code agents read it
before every ingest, query, or lint operation.

> Tagline: {{TAGLINE}}
> Primary stack: {{STACK}}
> Generated on: {{CURRENT_DATE}}

## 1. Scope

This vault holds **project-specific** knowledge:

- Domain rules, business logic, and vocabulary unique to {{PROJECT_NAME}}
- Architectural decisions affecting this repository
- Entities (models, services, modules) as they evolve
- Bugs and their fixes (with commit hashes and regression tests)
- Concepts that only make sense in the {{PROJECT_NAME}} context

Domain terms you'll encounter: {{DOMAIN_TERMS}}
External integrations: {{INTEGRATIONS}}

## 2. Out of scope

- **Cross-project knowledge** (Claude Code patterns, general git/CI workflow,
  tool tutorials) → write into the global vault at
  `${CLAUDE_VAULT:-$HOME/claude-vault}` instead.
- **NDA / confidential material** that cannot be shared with collaborators.
- **Ephemeral conversation state** — use TodoWrite / plan mode / memory.
- **Runtime preferences** (e.g. "always use Sonnet 4.6") — those belong in
  `~/.claude/CLAUDE.md` or the repo's root `CLAUDE.md`, not in this vault.

## 3. Directory layout

```
{{PROJECT_SLUG}}/docs/vault/
├── CLAUDE.md          # this file (schema)
├── index.md           # hand-maintained search surface
├── log.md             # chronological ingest log
├── sources/
│   ├── sessions/      # session summaries (YYYY-MM-DD-<slug>.md)
│   └── prompts/       # reusable prompt templates
├── decisions/         # architectural decisions (YYYY-MM-DD-<slug>.md)
├── bugs/              # symptom → root cause → fix (<slug>.md)
├── entities/          # models, services, modules (<slug>.md)
├── concepts/          # domain concepts (<slug>.md)
├── syntheses/         # filed-back query answers
├── archive/           # superseded pages (never delete — move here)
└── raw/               # immutable source material (gitignored for large files)
```

Shared state with the global vault lives at
`${CLAUDE_VAULT:-$HOME/claude-vault}/state/ingested.txt`.

## 4. Page format

```yaml
---
title: Descriptive page title
tags: [tag1, tag2]
source: "sources/sessions/YYYY-MM-DD-<slug>.md"   # required
date: YYYY-MM-DD
status: draft | active | archived
related_code: "path/to/file:line_range"           # recommended
severity: low | medium | high | critical          # bugs only
session_size: "30M, 3451 messages"                # sources/sessions/ only
---
```

Body: markdown. Every non-trivial claim cites a source — either
`[[sources/...]]` or an external URL. Close with `## Sources` and `## Related`.

## 5. Sections by page type

- **sources/sessions/** — Purpose · What happened · Files touched · Decisions · Bugs/fixes · Open questions
- **decisions/** — Context · Decision · Alternatives · Rationale · Affected code · Consequences
- **bugs/** — Symptoms · Reproduction · Root cause · Fix (commit hash) · Regression test · Prevention
- **entities/** — Definition · Responsibility · Related files · Relationships · Key decisions
- **concepts/** — Definition · Rule/formula · Examples · Related entities · Rationale

## 6. File naming

- Kebab-case, ASCII only. Transliterate non-ASCII characters as needed
  (`ı→i`, `ş→s`, `ğ→g`, `ü→u`, `ö→o`, `ç→c`, etc.).
- Date-prefixed for chronological categories: `YYYY-MM-DD-<slug>.md`.
- Stable slug-only names for entities/concepts/bugs: `<slug>.md`.

## 7. Cross-linking

- Use `[[relative/path/page.md]]` for Obsidian-compatible links.
- Every page should have at least one inbound link from `index.md` or another
  page — orphan pages are flagged during lint.
- When A → B, consider whether B should also link back to A.

## 8. Hard rules (inviolable)

1. **`raw/` is immutable.**
2. **No sourceless claims.** `source` frontmatter field + `## Sources` body section.
3. **No deletions.** Move outdated pages to `archive/`.
4. **Contradictions stay visible.** Use `## CONFLICT`; keep `## RESOLVED (YYYY-MM-DD)`.
5. **`index.md` updated on every ingest/lint.**
6. **Security.** Never write secrets — use `stored in env` or `redacted`, log the exclusion.
7. **Commit prefix**: `docs(vault):`.
8. **Atomicity.** One decision = one page; one bug = one page.
9. **Cross-vault purity.** Project-specific stuff stays here; cross-project goes to the global vault — link across instead of duplicating.
10. **Vault language.** Pick one and stay consistent; technical terms may stay English.

## 9. Workflows

### INGEST (source → pages)

1. Read `${CLAUDE_VAULT:-$HOME/claude-vault}/state/pending.md` (or take a session ID argument).
2. Parse the source via `ctx_execute` / `ctx_execute_file`. Never `Read` multi-megabyte transcripts.
3. Show a 5–7 bullet summary; wait for approval.
4. Write pages following §3–§5.
5. Update `index.md`; append to `log.md`.
6. Append the session ID to `${CLAUDE_VAULT:-$HOME/claude-vault}/state/ingested.txt`.
7. Re-run `${CLAUDE_VAULT:-$HOME/claude-vault}/scripts/scan-sessions.sh --quiet`.
8. Commit with a `docs(vault):` message.

### QUERY (question → answer)

1. Read `index.md` (this vault first, then the global vault if needed).
2. Follow links to source/entity/decision/concept/bug pages.
3. Answer with citations.
4. If the synthesis is novel → `syntheses/YYYY-MM-DD-<slug>.md` + `log.md` entry.

### LINT (health check)

Check: orphan pages, stale claims (60+ days `active` contradicting newer sources),
missing concepts (3+ references, no page), one-way links, dead `related_code`
paths, duplicate entities. Produce `syntheses/lint-YYYY-MM-DD.md`.

## 10. Project-specific conventions

<!-- Fill in after `/vault:init` has run; customize to the codebase. -->
<!-- Examples you might add:                                         -->
<!-- - Code references use `app/module.py:42-58` notation.           -->
<!-- - API endpoints documented in `entities/` with request/response -->
<!--   examples.                                                     -->
<!-- - Database migration decisions always link to the migration     -->
<!--   file in `related_code`.                                       -->

## 11. Routing cheat sheet

| Content | Target |
|---|---|
| {{PROJECT_NAME}} domain rule or business logic | **This vault** |
| {{PROJECT_NAME}} architectural decision | **This vault** |
| Bug found in this repo | **This vault** (`bugs/`) |
| Cross-project Claude Code pattern | **Global vault** |
| General git / CI / testing workflow | **Global vault** |
| NDA / confidential content | **Neither vault** |

## 12. Credits

The LLM-Wiki pattern used here was introduced by
[Selma Kocabıyık](https://github.com/selmakcby) in the
[knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline) repository.
The Claude Code packaging (auto-scan, slash commands, hybrid scoping) lives in
[claude-obsidian-vault-skill](https://github.com/mehmetcakoglu/claude-obsidian-vault-skill),
MIT licensed.
