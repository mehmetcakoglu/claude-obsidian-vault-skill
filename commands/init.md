---
description: Bootstrap a project vault — docs/vault/ skeleton + customized CLAUDE.md tailored to the current project
argument-hint: "[optional: project root path, defaults to cwd]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /vault:init

Bootstrap `docs/vault/` in a project: create the directory skeleton, write a customized `CLAUDE.md`, seed `index.md` + `log.md`, set up `.gitignore`, and offer to commit.

## Argument

- `$1` — optional project root path. If omitted, use `pwd` as the project root.

## 1. Discovery (automatic)

1. Determine the project root:
   - If `$1` is provided, use it.
   - Otherwise, use the current working directory.
   - Target skeleton will be created at `${PROJECT_ROOT}/docs/vault/`.
2. Pre-flight checks:
   - If `${PROJECT_ROOT}/docs/vault/CLAUDE.md` already exists → stop and tell the user the vault is already initialized. Do not overwrite.
   - If `${PROJECT_ROOT}/.git` does not exist → warn but proceed (skip the commit step later).
3. Collect auto-detected defaults (for questionnaire suggestions) by reading in parallel:
   - **Project name**: `basename "$PROJECT_ROOT"`
   - **Git remote**: `git -C "$PROJECT_ROOT" remote get-url origin` (if present, confirm project name)
   - **Stack hints** (from presence of files):
     - `pyproject.toml` / `requirements.txt` / `manage.py` → Python / Django
     - `package.json` → Node.js; inspect dependencies: `vue` → Vue, `react` → React, `next` → Next.js, `svelte` → SvelteKit
     - `go.mod` → Go
     - `Cargo.toml` → Rust
     - `Gemfile` → Ruby / Rails
     - `docker-compose.yml` / `Dockerfile` → containerized
     - `vercel.json` / `netlify.toml` / `fly.toml` → hosting platform
   - **Root `CLAUDE.md`**: read the first 80 lines if present (hints for project context)
   - **Monorepo apps**: list `apps/` or `packages/` subdirectories if present

## 2. Questionnaire

Use `AskUserQuestion` if available (one call, multiple questions). Otherwise ask all five questions in a single numbered message and wait for the reply.

1. **Official project name?** (default: detected basename)
2. **What does the project do in one sentence?** (tagline — e.g. "SaaS invoicing for Turkish SMEs")
3. **Primary tech stack?** (default: detected hints; let the user correct)
4. **Project-specific domain terms?** (comma-separated — e.g. "invoice, installment, receivable". Can be empty.)
5. **Integrated tools / infrastructure?** (comma-separated — e.g. "Vercel, Supabase, OpenSpec, Docker". Can be empty.)

Show the user a summary of their answers and ask for confirmation (`y/n`). Do not write any files until they confirm.

## 3. Create skeleton

Single bash command:

```bash
mkdir -p "$PROJECT_ROOT"/docs/vault/{archive,bugs,concepts,decisions,entities,syntheses}
mkdir -p "$PROJECT_ROOT"/docs/vault/raw/{sessions,docs}
mkdir -p "$PROJECT_ROOT"/docs/vault/sources/sessions
```

## 4. Write files

Substitute placeholders using the answers:

- `{{PROJECT_NAME}}` — answer #1
- `{{PROJECT_SLUG}}` — answer #1 converted to kebab-case ASCII (transliterate non-ASCII: `ı→i`, `ş→s`, `ğ→g`, `ü→u`, `ö→o`, `ç→c`, etc.)
- `{{TAGLINE}}` — answer #2
- `{{STACK}}` — answer #3
- `{{DOMAIN_TERMS}}` — answer #4 (use `—` if empty)
- `{{INTEGRATIONS}}` — answer #5 (use `—` if empty)
- `{{CURRENT_DATE}}` — `date +%Y-%m-%d`
- `{{CLAUDE_PROJECTS_DIRNAME}}` — `$PROJECT_ROOT` with `/` replaced by `-` (including leading slash → leading `-`). This matches the directory name under `~/.claude/projects/`.

### 4.1 `docs/vault/.gitignore` — verbatim

```
# Raw Claude Code JSONL sessions are not committed
raw/sessions/*.jsonl
raw/sessions/*.symlink

# Large binaries
raw/**/*.pdf
raw/**/*.zip
raw/**/*.tar*
raw/**/*.mp4

# OS
.DS_Store

# Obsidian workspace (personal)
.obsidian/workspace*
.obsidian/graph.json
```

### 4.2 `docs/vault/CLAUDE.md`

~~~markdown
# {{PROJECT_SLUG}}-vault — Project Vault Schema

> **Project-specific** knowledge archive. {{TAGLINE}}
>
> Cross-project knowledge (Claude Code patterns, generic workflow) lives in the global vault at `~/claude-vault/`.
>
> This file is the vault's constitution. Every ingest/query/lint reads it first.

---

## 1. Purpose

Persistent knowledge archive for **{{PROJECT_NAME}}**:

- Project-specific architectural decisions and their rationale
- Domain business rules and terminology
- Bug reports with root cause and permanent fix
- Feature development history (what, why, when)
- Deployment and integration decisions
- Data model / API evolution history

### Scope

- Stack: {{STACK}}
- Integrations: {{INTEGRATIONS}}
- Domain terms: {{DOMAIN_TERMS}}

### Out of scope (belongs elsewhere)

- Generic Claude Code patterns → `~/claude-vault/`
- Cross-project workflow preferences → `~/claude-vault/`
- Other projects → their own vaults
- Runtime instructions → project-root `CLAUDE.md` (separate file, not this one)

---

## 2. Language

Pick a single primary language for this vault and stay consistent. Technical terms may remain English in non-English vaults. File names are always kebab-case ASCII (transliterate non-ASCII characters).

---

## 3. Directory layout

| Directory | Content |
|---|---|
| `raw/sessions/` | Claude Code JSONL transcripts (symlinks, gitignored) |
| `raw/docs/` | Reference documents (PRDs, PDFs, spec samples) |
| `sources/sessions/` | One summary page per JSONL transcript |
| `entities/` | Project entities: models, components, services, pages, endpoints |
| `concepts/` | Domain concepts and patterns |
| `decisions/` | Architectural decisions (ADR-like, atomic) |
| `bugs/` | Bug reports: root cause, fix, regression note |
| `syntheses/` | Feature overviews, period summaries, comparisons |
| `archive/` | Outdated pages (never deleted) |

---

## 4. Naming convention

- `kebab-case.md`, ASCII only
- **Sources**: `sources/sessions/YYYY-MM-DD-<short-slug>.md`
- **Decisions**: `decisions/YYYY-MM-DD-<slug>.md`
- **Bugs**: `bugs/<slug>.md` (date in frontmatter)
- **Entities**: `entities/<category>/<name>.md` or `entities/<name>.md` (categories: `models/`, `components/`, `services/`)
- **Concepts**: `concepts/<topic>.md`

---

## 5. Page format

```markdown
---
title: Page title
tags: [tag1, tag2]
source: "sources/sessions/YYYY-MM-DD-<slug>.md"
date: YYYY-MM-DD
status: draft | active | archived
related_code: "path/to/file.py:line_range"  # optional
session_size: "Nm, X messages"              # only for sources/sessions/
---

# Page title

Body. Every claim cites a source.

## Sources
- [[sources/sessions/...]]

## Related
- [[entities/...]]
- [[concepts/...]]
```

### Sections by page type

- **sources/sessions/** — Purpose · What happened · Files touched · Decisions · Bugs/fixes · Open questions
- **decisions/** — Context · Decision · Alternatives · Rationale · Affected code · Consequences
- **bugs/** — Symptoms · Reproduction · Root cause · Fix (commit hash) · Regression test · Prevention
- **entities/** — Definition · Responsibility · Related files · Relationships · Key decisions
- **concepts/** — Definition · Rule/formula · Examples · Related entities · Rationale

### Conflicts

Use a `## CONFLICT` section with source references. When resolved, do not delete it — add a `## RESOLVED (YYYY-MM-DD)` note beneath.

---

## 6. INGEST workflow

When a new JSONL lands in `raw/sessions/` (via symlink or copy) or the user triggers `/vault:ingest`:

1. **Parse**: Split the JSONL into manageable chunks. For each chunk extract:
   - Main topic (feature / bug / refactor / research)
   - Files and directories touched
   - Decisions made (confirmed by the user?)
   - Bug / fix pairs
   - New domain concepts introduced
2. **Summarize**: Show a 5–7 bullet summary to the user, wait for approval.
3. **Write**:
   - `sources/sessions/YYYY-MM-DD-<slug>.md` — session summary
   - New or changed entities → `entities/...`
   - Each architectural decision → `decisions/YYYY-MM-DD-<slug>.md`
   - Each bug → `bugs/<slug>.md` (root cause + fix commit hash)
   - New concepts → `concepts/<slug>.md`
   - Update `index.md` and `log.md`
4. **Push-to-global rule**: If a finding is NOT project-specific → reference it in the global vault at `~/claude-vault/` instead of duplicating it here.

### Global vs project split

| Example | Destination |
|---|---|
| Project-specific domain term (from {{DOMAIN_TERMS}}) | Project (this vault) |
| Cross-project pattern (Claude Code hook, git workflow) | Global |
| Code specific to `{{STACK}}` | Project |
| Generic framework knowledge | Global |

---

## 7. QUERY workflow

When the user asks a question:

1. Read this project vault's `index.md` first, then the linked pages.
2. If insufficient, fall back to the global vault (`~/claude-vault/`).
3. Read referenced code files if needed.
4. Synthesize the answer with a citation for every claim.
5. If the synthesis is novel, file it back as `syntheses/YYYY-MM-DD-<slug>.md` and log it.

---

## 8. LINT workflow

Weekly or on demand:

- Orphan pages
- Stale claims (60+ days `active` contradicting newer sources)
- Missing concepts (referenced in 3+ pages, no page of their own)
- One-way links
- **Code drift**: `related_code` paths that no longer exist or whose line ranges shifted
- Duplicate entities
- Areas flagged for additional research

Report: `syntheses/lint-YYYY-MM-DD.md`

---

## 9. Hard rules

1. `raw/` is never modified. JSONLs are gitignored — symlinks preferred.
2. No sourceless claims. Every page has a `source` frontmatter and a `## Sources` section.
3. No deletions — move to `archive/`.
4. Contradictions are visible, never hidden.
5. `index.md` is updated on every ingest/lint.
6. **No project-external knowledge here** — link to the global vault instead.
7. Code references are version-pinned (commit hash or migration number).
8. **Commit policy**: vault commits use the `docs(vault):` prefix.

---

## 10. Global vault relationship

- **This vault → global**: when a finding is not project-specific, link to the global vault.
- **Global → this vault**: when a global page touches on this project, link here.
- **No duplication**: each piece of knowledge lives in exactly one vault.

---

## 11. Integrations

### Claude Code ingest
- Raw source: `~/.claude/projects/{{CLAUDE_PROJECTS_DIRNAME}}/`
- Auto-scan: `~/claude-vault/scripts/scan-sessions.sh` (SessionStart hook)
- Manual triggers: `/vault:scan`, `/vault:ingest`
- Session ID registry: `~/claude-vault/state/ingested.txt`

### Git
- Vault commits use the `docs(vault):` prefix.
- JSONLs are gitignored.
- Branch strategy: same as the parent project.

### Project integrations: {{INTEGRATIONS}}

---

## 12. Schema evolution

Any change to this file triggers a `## [YYYY-MM-DD] schema | <description>` entry in `log.md`. Breaking changes (directory reorganization, frontmatter field renames) migrate affected pages in the same commit.
~~~

### 4.3 `docs/vault/index.md`

```markdown
# {{PROJECT_SLUG}}-vault — Content Index

> Catalog of every page in the vault. Updated after every ingest.

**Last updated:** {{CURRENT_DATE}} (init)

---

## Syntheses (syntheses/)

_No syntheses yet._

---

## Decisions (decisions/)

_No decisions yet._

---

## Entities (entities/)

_No entities yet._

---

## Concepts (concepts/)

_No concepts yet._

---

## Bugs (bugs/)

_No bugs yet._

---

## Sources (sources/)

### Claude Code sessions (sources/sessions/)

_No sessions ingested yet._
```

### 4.4 `docs/vault/log.md`

```markdown
# Event Log (log.md)

> Append-only, timestamped log. Every ingest, filed-back query, and lint pass is recorded here.
>
> **Format:** `## [YYYY-MM-DD] <type> | <slug>`
>
> **Types:** `ingest`, `query`, `lint`, `schema` (for schema changes).

---

## [{{CURRENT_DATE}}] schema | vault-init

- Vault skeleton created: `docs/vault/`
- `CLAUDE.md` customized for this project
- Stack: {{STACK}}
- Domain terms: {{DOMAIN_TERMS}}
- Integrations: {{INTEGRATIONS}}
- Hybrid with global vault: `~/claude-vault/`
- First ingest pending (`/vault:scan` + `/vault:ingest` to trigger)
```

## 5. Commit offer

1. Ask the user: "Commit the new vault now? (`docs(vault): bootstrap project vault`) [y/n]"
2. If `y`:
   ```bash
   cd "$PROJECT_ROOT" && git add docs/vault/ && git commit -m "docs(vault): bootstrap project vault

   - docs/vault/ skeleton (sources, entities, decisions, concepts, bugs, syntheses, archive, raw)
   - CLAUDE.md tailored to {{PROJECT_NAME}}
   - Integrated with global ~/claude-vault/ via scan-sessions.sh + /vault:scan|ingest"
   ```
3. If `n`: show `git status` so the user can stage manually.

## 6. Closing report

Show the user:
- ✅ Directories created (9 folders)
- ✅ Files written (CLAUDE.md, index.md, log.md, .gitignore)
- ℹ️ Next steps:
  1. Continue working in the project with Claude Code.
  2. New sessions land in the scan queue automatically (global SessionStart hook).
  3. When ready, run `/vault:ingest` to process the first session into this vault.
  4. Edit `CLAUDE.md` later as the domain evolves — remember to add a `schema` entry to `log.md`.

## Error handling

- `docs/vault/CLAUDE.md` exists → "Vault is already initialized. Edit `docs/vault/CLAUDE.md` manually, or remove that directory and rerun." Stop.
- `$PROJECT_ROOT` is not a git repo → warn and proceed (skip commit step).
- User answers `n` to the confirmation → exit without writing anything.
- `AskUserQuestion` tool unavailable → ask via plain numbered message and wait.
