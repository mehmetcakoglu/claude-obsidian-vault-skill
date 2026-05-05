# /vault:doctor

> Scan both the global and project vaults for structural, frontmatter, link, and lint issues — then offer to fix them automatically or interactively.

---

## Usage

```
/vault:doctor
```

No arguments.

---

## What it does

Runs four checks against each vault (global first, project vault if present), collects all issues, prints a report, and asks the user how to proceed.

### Step 1 — Resolve vault paths

| Variable | Value |
|---|---|
| `GLOBAL_VAULT` | `$CLAUDE_VAULT` if set, otherwise `~/Global Claude Vault` |
| `PROJECT_VAULT` | `./docs/vault` if `./docs/vault/CLAUDE.md` exists, otherwise skipped |

### Step 2 — Four checks (Python via ctx_execute)

#### 2a — Structural check

Verifies required directories and files exist.

**Required directories:** `syntheses`, `decisions`, `entities`, `concepts`, `bugs`, `lessons`, `sources/sessions`, `state`, `raw`

**Required files:** `index.md`, `log.md`, `vault-config.json`, `CLAUDE.md`, `state/pending.md`, `state/ingested.txt`

#### 2b — Frontmatter check

Walks all `.md` files (excluding `CLAUDE.md`, `index.md`, `log.md`, and `state/`, `raw/`, `scripts/`, `archive/` directories).

Checks each file for:
- Presence of a `---` frontmatter block
- Required fields: `title`, `tags`, `source`, `date`, `status`
- Valid `status` value: `draft`, `active`, or `archived`
- Special: `status: ingested` → auto-fixable to `archived`

#### 2c — Link integrity check

- Reads `index.md` and extracts all `[[...]]` wikilinks
- Normalizes bare filenames to vault-relative paths
- Flags dead links in `index.md` (fixable)
- Flags pages not listed in `index.md` (fixable)
- Scans all pages for broken `[[wikilinks]]` — auto-fixable in `syntheses/` and `bugs/`
- Flags orphan pages (not linked from anywhere) as info
- **Skips `CLAUDE.md`** for wikilink content scanning (template placeholders are intentional)

#### 2d — LINT check

- **Stale pages**: `status: active` + date > 90 days ago
- **Missing Sources section**: `source: manuel` in frontmatter but no `## Sources` section in body (fixable)
- **Missing ingest sizes**: sessions in `state/ingested.txt` not covered by `state/ingest-sizes.txt` — causes `vault:status` to show "no data yet" (fixable)

### Step 3 — Report

Prints a formatted report grouped by vault and check category. Example:

```
vault:doctor — 2026-05-05
══════════════════════════════════════════════════════════════
Global Vault  ~/Global Claude Vault/
──────────────────────────────────────────────────────────────
  Structure   ✓ All folders/files present
  Frontmatter ⚠ Invalid status 'ingested': sources/sessions/foo.md  [fixable]
  Links       ⚠ syntheses/doctor-2026-05-05.md not in index.md      [fixable]
  LINT        ⚠ ingest-sizes.txt missing 3/52 session sizes          [fixable]

Total: 3 issues  (0 errors ✗ · 3 warnings ⚠)
Auto-fixable: 3

Fix options:
  [A] Apply all auto-fixable issues automatically
  [B] Decide on each issue interactively
  [C] Save report only, skip fixes for now
```

### Step 4 — Fix modes

**[A] Auto-fix:** applies all fixable issues in order (see fix types below).

**[B] Interactive:** presents each fixable issue one at a time and asks `Apply fix? (y/n)`.

**[C] Skip:** writes the report only.

### Step 5 — Write report

Writes `<vault>/syntheses/doctor-YYYY-MM-DD.md` for each vault that had issues.

### Step 6 — Update log.md

Appends `## [YYYY-MM-DD] vault:doctor | N errors, M warnings — X auto-fixed` to each affected vault's `log.md`.

---

## Fix types

| Fix type | Trigger | Action |
|---|---|---|
| `create_dir` | Missing required directory | `mkdir -p <vault>/<dir>` |
| `create_file` | Missing required file | Write stub content |
| `remove_index_entry` | Dead `[[link]]` in `index.md` | Edit tool removes the line |
| `add_index_entry` | Page missing from `index.md` | Append entry to relevant section |
| `add_frontmatter` | No frontmatter block | Prepend complete stub frontmatter |
| `add_frontmatter_field` | Missing field in frontmatter | Insert field with `# DOCTOR-TODO` value |
| `fix_invalid_status` | `status: ingested` | Replace with `status: archived` |
| `fix_wikilink_in_report` | `[[broken.md]]` in `syntheses/` or `bugs/` | Remove `[[` and `]]`, keep plain path |
| `add_sources_section` | `source: manuel` without `## Sources` | Append `## Sources\n\n_(no source recorded)_` |
| `populate_ingest_sizes` | Sessions missing from `ingest-sizes.txt` | Scan `~/.claude/projects/*/SESSION_ID.jsonl`, write sizes |

**Not auto-fixable:** broken wikilinks in source files, orphan pages, stale pages, unsourced claims in non-`manuel` files, `CLAUDE.md` placeholder links.

---

## Files read

| File | Why |
|---|---|
| `<vault>/index.md` | Link integrity check |
| `<vault>/**/*.md` | Frontmatter, link, lint checks |
| `<vault>/state/ingested.txt` | LINT: ingest-sizes coverage |
| `<vault>/state/ingest-sizes.txt` | LINT: ingest-sizes coverage |
| `~/.claude/projects/*/SESSION_ID.jsonl` | `populate_ingest_sizes` fix |

## Files written

| File | When |
|---|---|
| `<vault>/syntheses/doctor-YYYY-MM-DD.md` | Always (report) |
| `<vault>/log.md` | Always (log entry) |
| `<vault>/index.md` | When `add_index_entry` or `remove_index_entry` fixes applied |
| Various vault pages | When frontmatter or wikilink fixes applied |
| `<vault>/state/ingest-sizes.txt` | When `populate_ingest_sizes` fix applied |

---

## Allowed tools

```
Read(~/Global Claude Vault/**)
Read($CLAUDE_VAULT/**)
Read(./docs/vault/**)
Bash(find * *)
Bash(python3 * *)
mcp__plugin_context-mode_context-mode__ctx_batch_execute
mcp__plugin_context-mode_context-mode__ctx_execute
Edit(~/Global Claude Vault/**)
Edit(./docs/vault/**)
Write(~/Global Claude Vault/**)
Write(./docs/vault/**)
```

---

## Related

- [vault-status.md](vault-status.md) — health snapshot
- [vault-ingest.md](vault-ingest.md) — populates `ingest-sizes.txt` during normal use
- [Index](../index.md)
