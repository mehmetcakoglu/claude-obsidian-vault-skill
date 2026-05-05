---
description: Bootstrap a project vault — docs/vault/ skeleton + customized CLAUDE.md tailored to the current project
argument-hint: "[--interactive | project root path]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# /vault:init

Bootstrap `docs/vault/` for the current project. By default runs **fully automatic** — no questions asked. Pass `--interactive` to answer questions and customize before writing.

## Argument

- _(none)_ — auto-detect everything and create the vault immediately
- `--interactive` — ask the 5 customization questions before writing (old behaviour)
- `<path>` — use a specific project root instead of cwd (can be combined with `--interactive`)

---

## Mode A — Automatic (default)

### 0. Global vault pre-flight

Check `${CLAUDE_VAULT:-$HOME/Global Claude Vault}` exists. If not:
> "Global vault not found. Start a new Claude Code session first — it will be created automatically."
Stop.

### 1. Auto-detect

Determine project root (`$1` if provided, else `pwd`) and collect facts silently:

| Field | How detected |
|---|---|
| `PROJECT_NAME` | `basename "$PROJECT_ROOT"` |
| `PROJECT_SLUG` | kebab-case ASCII of `PROJECT_NAME` (transliterate `ışğüöçİŞĞÜÖÇ`) |
| `STACK` | First matching marker in project root: `manage.py`→Django/Python · `pyproject.toml`/`requirements.txt`→Python · `package.json`→Node.js (+ peek at deps: react→React, next→Next.js, vue→Vue, svelte→SvelteKit) · `go.mod`→Go · `Cargo.toml`→Rust · `Gemfile`→Ruby/Rails · else "unknown" |
| `INTEGRATIONS` | Files present: `docker-compose.yml`/`Dockerfile`→Docker · `vercel.json`→Vercel · `netlify.toml`→Netlify · `fly.toml`→Fly.io · `supabase/`→Supabase · `k8s/`/`kubernetes/`→Kubernetes · join found ones with ", " · `—` if none |
| `TAGLINE` | `"{{PROJECT_NAME}} — {{STACK}} project"` (generic placeholder; edit CLAUDE.md later) |
| `DOMAIN_TERMS` | `—` (add after the first few ingest sessions) |
| `CURRENT_DATE` | today's date `YYYY-MM-DD` |
| `CLAUDE_PROJECTS_DIRNAME` | `$PROJECT_ROOT` with `/` replaced by `-` |

Pre-flight: if `docs/vault/CLAUDE.md` already exists → print "Vault already initialized." and stop.

### 2. Create skeleton & write files

Run immediately — no confirmation prompt:

```bash
mkdir -p "$PROJECT_ROOT"/docs/vault/{archive,bugs,concepts,decisions,entities,syntheses,sources/sessions,raw/sessions,raw/docs}
```

Write the four files using the auto-detected values (see templates in **Appendix** below).

### 3. Commit

If `.git` exists in `$PROJECT_ROOT`, auto-commit without asking:

```bash
cd "$PROJECT_ROOT"
git add docs/vault/
git commit -m "docs(vault): bootstrap project vault

- docs/vault/ skeleton for {{PROJECT_NAME}}
- Stack: {{STACK}} | Integrations: {{INTEGRATIONS}}
- Edit docs/vault/CLAUDE.md to add domain terms and tagline"
```

If not a git repo, skip silently.

### 4. Closing report

```
✅ docs/vault/ created for {{PROJECT_NAME}}
   Stack detected : {{STACK}}
   Integrations   : {{INTEGRATIONS}}

   Next steps:
   1. Edit docs/vault/CLAUDE.md — add your domain terms and a one-line tagline.
   2. Run /vault:ingest when you're ready to archive your first session.

   Tip: run /vault:status to confirm everything is wired up.
```

---

## Mode B — Interactive (`--interactive`)

Same as Mode A, but **after auto-detection** and **before writing any files**, ask the 5 questions with the detected values as defaults:

1. **Project name?** (default: `{{PROJECT_NAME}}`)
2. **One-line tagline?** (default: `{{PROJECT_NAME}} — {{STACK}} project`)
3. **Tech stack?** (default: `{{STACK}}`)
4. **Domain terms?** (comma-separated, default: empty)
5. **Integrations?** (comma-separated, default: `{{INTEGRATIONS}}`)

Show a confirmation summary, then proceed to steps 2–4 of Mode A.

---

## Appendix — File templates

### `docs/vault/.gitignore`

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

### `docs/vault/CLAUDE.md`

~~~markdown
# {{PROJECT_SLUG}}-vault — Project Vault Schema

> **Project-specific** knowledge archive. {{TAGLINE}}
>
> Cross-project knowledge (Claude Code patterns, generic workflow) lives in the global vault.
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

- Generic Claude Code patterns → global vault
- Cross-project workflow preferences → global vault
- Other projects → their own vaults
- Runtime instructions → project-root `CLAUDE.md` (not this file)

---

## 2. Directory layout

| Directory | Content |
|---|---|
| `raw/sessions/` | Claude Code JSONL transcripts (symlinks, gitignored) |
| `raw/docs/` | Reference documents (PRDs, PDFs) |
| `sources/sessions/` | One summary page per JSONL transcript |
| `entities/` | Project entities: models, components, services, endpoints |
| `concepts/` | Domain concepts and patterns |
| `decisions/` | Architectural decisions (ADR-like, atomic) |
| `bugs/` | Bug reports: root cause, fix, regression note |
| `syntheses/` | Feature overviews, period summaries, comparisons |
| `archive/` | Outdated pages (never deleted) |

---

## 3. Naming convention

- `kebab-case.md`, ASCII only
- **Sources**: `sources/sessions/YYYY-MM-DD-<short-slug>.md`
- **Decisions**: `decisions/YYYY-MM-DD-<slug>.md`
- **Bugs**: `bugs/<slug>.md` (date in frontmatter)
- **Entities**: `entities/<name>.md`
- **Concepts**: `concepts/<topic>.md`

---

## 4. Page format

```markdown
---
title: Page title
tags: [tag1, tag2]
source: "sources/sessions/YYYY-MM-DD-<slug>.md"
date: YYYY-MM-DD
status: draft | active | archived
related_code: "path/to/file.py:line_range"  # optional
---

# Page title

Body. Every claim cites a source.

## Sources
- [[sources/sessions/YYYY-MM-DD-slug.md]]

## Related
- [[entities/...]]
```

---

## 5. INGEST workflow

1. Parse with sandbox tool (never Read multi-MB JSONLs directly)
2. Write `sources/sessions/YYYY-MM-DD-<slug>.md`
3. Add decisions/, bugs/, entities/, concepts/ pages where warranted
4. Update `index.md` and `log.md`
5. Append session ID to global `state/ingested.txt`
6. Commit with `docs(vault):` prefix

---

## 6. Hard rules

1. No sourceless claims — every page has `source` frontmatter
2. No deletions — move to `archive/`
3. No secrets (API keys, passwords, IPs) — use placeholders
4. `index.md` updated on every ingest/lint
5. File names: kebab-case ASCII only
6. Commit prefix: `docs(vault):`

---

## 7. Claude Code integration

- Raw source: `~/.claude/projects/{{CLAUDE_PROJECTS_DIRNAME}}/`
- Session ID registry: `${CLAUDE_VAULT:-~/Global Claude Vault}/state/ingested.txt`
~~~

### `docs/vault/index.md`

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

### `docs/vault/log.md`

```markdown
# Event Log (log.md)

> Append-only, timestamped log.
>
> **Format:** `## [YYYY-MM-DD] <type> | <slug>`
> **Types:** `ingest`, `query`, `lint`, `schema`

---

## [{{CURRENT_DATE}}] schema | vault-init

- Vault skeleton created: `docs/vault/`
- Stack: {{STACK}}
- Integrations: {{INTEGRATIONS}}
- Domain terms: {{DOMAIN_TERMS}} _(edit CLAUDE.md to add project-specific terms)_
```

---

## Error handling

- `docs/vault/CLAUDE.md` already exists → "Vault already initialized." Stop.
- Global vault missing → tell user to start a new session first. Stop.
- `$PROJECT_ROOT` is not a git repo → skip commit step, note in closing report.
