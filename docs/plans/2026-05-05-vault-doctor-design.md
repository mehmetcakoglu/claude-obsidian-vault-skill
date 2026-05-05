# vault:doctor — Design Document

**Date:** 2026-05-05  
**Status:** approved  

---

## Overview

`/vault:doctor` is a new slash command that scans both the global vault (`~/Global Claude Vault/`) and the project vault (`./docs/vault/`, if present in cwd) for structural, content, and link integrity issues. After reporting, it asks the user whether to fix all correctable issues automatically or review each one interactively.

---

## Flow

```
1. Scan both vaults → collect all issues
2. Print report to console
3. If no issues → "vault sağlıklı" message, stop
4. If issues exist → ask user:
     [A] Hepsini otomatik düzelt
     [B] Her birini tek tek gör
     [C] Sadece raporu kaydet, şimdilik geç
5a. [A] → apply all auto-fixable issues sequentially, log each action
5b. [B] → for each auto-fixable issue: explain + ask "düzelt / atla"
5c. [C] → skip fixes
6. Write report to syntheses/doctor-YYYY-MM-DD.md (in each affected vault)
7. Append to log.md
```

---

## Check Categories

### 1 — Structural (auto-fixable)

| Check | Auto-fix |
|-------|----------|
| Missing required folders: `syntheses/`, `decisions/`, `entities/`, `concepts/`, `bugs/`, `lessons/`, `sources/sessions/`, `state/`, `raw/` | Create folder |
| Missing required files: `index.md`, `log.md`, `vault-config.json` | Create stub file |
| Missing state files: `state/pending.md`, `state/ingested.txt` | Create empty file |

### 2 — Frontmatter (partially auto-fixable)

Applies to all `.md` files except `CLAUDE.md`, `index.md`, `log.md`.

| Check | Auto-fix |
|-------|----------|
| Missing required field: `title`, `tags`, `source`, `date`, `status` | Insert placeholder, mark with `# DOCTOR-PLACEHOLDER` comment |
| Invalid `status` value (not `draft \| active \| archived`) | Report only |

### 3 — Link Integrity (mixed)

| Check | Auto-fix |
|-------|----------|
| Entry in `index.md` points to non-existent file (dead link) | Remove entry from index.md |
| File exists but not listed in `index.md` | Add entry to index.md |
| Broken wikilink `[[...]]` — target file not found | Report only (intent unclear: renamed vs deleted) |
| Orphan page — not referenced from index.md or any other page | Report only |

### 4 — LINT (report only)

| Check | Note |
|-------|------|
| Stale page: `status: active` + `date` older than 90 days | Report with page list |
| Kaynaksız iddia: `source: manuel` but no `## Sources` section | Report with page list |
| One-way link: A→B exists, B→A missing | Report as suggestion |

---

## Console Output Format

```
vault:doctor — 2026-05-05
══════════════════════════════════════════
Global Vault  ~/Global Claude Vault/
──────────────────────────────────────────
  Yapı        ✓ Tüm klasörler mevcut
  Frontmatter ✗ 2 sayfada eksik alan
  Linkler     ✗ 3 kırık wikilink
              ✗ 2 index.md girişi kayıp dosyaya işaret ediyor
  LINT        ✗ 4 stale sayfa (>90 gün, status:active)
              ⚠ 1 kaynaksız iddia

Project Vault  ./docs/vault/
──────────────────────────────────────────
  ✓ Sorun bulunamadı

══════════════════════════════════════════
Toplam: 12 sorun (4 hata, 6 uyarı, 2 bilgi)

Düzeltilebilir: 7 sorun
  [A] Hepsini otomatik düzelt
  [B] Her birini tek tek gör
  [C] Sadece raporu kaydet, şimdilik geç
```

---

## Report File

Written to `syntheses/doctor-YYYY-MM-DD.md` in each vault that has issues, with YAML frontmatter:

```yaml
---
title: Vault Doctor Report — YYYY-MM-DD
tags: [vault, health, doctor]
source: "vault:doctor"
date: YYYY-MM-DD
status: draft
---
```

Content: full issue list grouped by category, with file paths, fix actions taken, and items requiring manual attention.

---

## log.md Entry

```
## [YYYY-MM-DD] vault:doctor | N hata, M uyarı, K bilgi — X otomatik düzeltildi
```

---

## Implementation Notes

- Use `ctx_batch_execute` for all file scanning (avoids context window overflow).
- Both vaults scanned in parallel where possible.
- Interactive mode ([B]): present issues in priority order — structural first, then frontmatter, then links, then LINT.
- Auto-fix mode ([A]): log each action clearly before applying. Never silently modify files.
- LINT-only issues (stale, one-way links, kaynaksız iddia) are always report-only — never auto-fixed.
- If project vault doesn't exist in cwd, skip project vault section silently (no error).

---

## Deliverables

1. `/Users/mehmetcakoglu/.claude/commands/vault/doctor.md` — slash command definition
2. Update `vault:help` command to include `vault:doctor` entry
