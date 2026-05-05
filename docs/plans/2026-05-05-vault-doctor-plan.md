# vault:doctor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/vault:doctor` slash command that scans both global and project vaults for issues, reports them, then asks user to fix all at once, interactively one-by-one, or skip.

**Architecture:** A single markdown command file (`~/.claude/commands/vault/doctor.md`) following the same pattern as existing vault commands. Claude executes all scanning via `ctx_batch_execute` Python snippets, collects a structured issue list, prints the report, then drives repair through user-chosen mode. A second file (`help.md`) is updated to include the new command.

**Tech Stack:** Markdown command file + Python (via ctx_execute) for file scanning + YAML frontmatter parsing + wikilink regex + Claude native Edit/Write tools for fixes.

---

## Task 1: Write `doctor.md` — Phase 1 (scan + report)

**Files:**
- Create: `~/.claude/commands/vault/doctor.md`

**Step 1: Create the file with frontmatter and scan phase**

Write `~/.claude/commands/vault/doctor.md` with the following content:

```markdown
description: Scan global and project vaults for structural, frontmatter, link, and lint issues. Report findings, then offer to fix all at once or interactively.
allowed-tools: Read(~/Global Claude Vault/**), Read($CLAUDE_VAULT/**), Read(./docs/vault/**), Bash(find * *), Bash(python3 * *), mcp__plugin_context-mode_context-mode__ctx_batch_execute, mcp__plugin_context-mode_context-mode__ctx_execute, Edit(~/Global Claude Vault/**), Edit($CLAUDE_VAULT/**), Edit(./docs/vault/**), Write(~/Global Claude Vault/**), Write($CLAUDE_VAULT/**), Write(./docs/vault/**)

# /vault:doctor

Scan both the global vault and the project vault (if present) for issues, report them, then offer repair options.

## Step 1 — Resolve vault paths

```python
GLOBAL_VAULT = os.environ.get("CLAUDE_VAULT", os.path.expanduser("~/Global Claude Vault"))
PROJECT_VAULT = "./docs/vault" if os.path.isfile("./docs/vault/CLAUDE.md") else None
```

If `GLOBAL_VAULT` directory does not exist: print `❌ Global vault not found at <path>. Run install.sh first.` and stop.

## Step 2 — Scan each vault

For each vault (global, then project if present), run a `ctx_batch_execute` call with these commands:

### 2a — Structural check (Python)

```python
import os, json

REQUIRED_DIRS = [
    "syntheses", "decisions", "entities", "concepts",
    "bugs", "lessons", "sources/sessions", "state", "raw"
]
REQUIRED_FILES = ["index.md", "log.md", "vault-config.json", "CLAUDE.md"]
STATE_FILES = ["state/pending.md", "state/ingested.txt"]

issues = []
vault = "<VAULT_PATH>"  # substitute actual path

for d in REQUIRED_DIRS:
    if not os.path.isdir(os.path.join(vault, d)):
        issues.append({"type": "structural", "severity": "error",
                       "msg": f"Missing folder: {d}", "fix": "create_dir", "target": d})

for f in REQUIRED_FILES + STATE_FILES:
    if not os.path.isfile(os.path.join(vault, f)):
        issues.append({"type": "structural", "severity": "error",
                       "msg": f"Missing file: {f}", "fix": "create_file", "target": f})

import json; print(json.dumps(issues))
```

### 2b — Frontmatter check (Python)

```python
import os, re, json

REQUIRED_FIELDS = ["title", "tags", "source", "date", "status"]
VALID_STATUSES = {"draft", "active", "archived"}
SKIP_FILES = {"CLAUDE.md", "index.md", "log.md"}

issues = []
vault = "<VAULT_PATH>"

for root, _, files in os.walk(vault):
    # skip state/, raw/, scripts/, archive/
    rel = os.path.relpath(root, vault)
    if any(rel.startswith(s) for s in ["state", "raw", "scripts", "archive", ".git"]):
        continue
    for fname in files:
        if not fname.endswith(".md") or fname in SKIP_FILES:
            continue
        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, vault)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        # parse frontmatter
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            issues.append({"type": "frontmatter", "severity": "error",
                           "msg": f"No frontmatter block: {rel_path}",
                           "fix": "add_frontmatter", "target": rel_path})
            continue
        fm_text = fm_match.group(1)
        for field in REQUIRED_FIELDS:
            if not re.search(rf"^{field}:", fm_text, re.MULTILINE):
                issues.append({"type": "frontmatter", "severity": "error",
                               "msg": f"Missing field '{field}': {rel_path}",
                               "fix": "add_frontmatter_field",
                               "target": rel_path, "field": field})
        # check status value
        status_match = re.search(r"^status:\s*(\S+)", fm_text, re.MULTILINE)
        if status_match and status_match.group(1) not in VALID_STATUSES:
            issues.append({"type": "frontmatter", "severity": "warning",
                           "msg": f"Invalid status '{status_match.group(1)}': {rel_path}",
                           "fix": None, "target": rel_path})

print(json.dumps(issues))
```

### 2c — Link integrity check (Python)

```python
import os, re, json

issues = []
vault = "<VAULT_PATH>"

# 1. Collect all md files (relative paths)
all_files = set()
for root, _, files in os.walk(vault):
    rel = os.path.relpath(root, vault)
    if any(rel.startswith(s) for s in ["state", "raw", "scripts", ".git"]):
        continue
    for fname in files:
        if fname.endswith(".md"):
            all_files.add(os.path.relpath(os.path.join(root, fname), vault))

# 2. Parse index.md entries [[...]]
index_path = os.path.join(vault, "index.md")
index_links = set()
if os.path.isfile(index_path):
    with open(index_path, encoding="utf-8") as fh:
        index_content = fh.read()
    index_links = set(re.findall(r"\[\[([^\]]+\.md)\]\]", index_content))

# Dead links in index.md
for link in index_links:
    if link not in all_files:
        issues.append({"type": "link", "severity": "error",
                       "msg": f"index.md dead link: [[{link}]]",
                       "fix": "remove_index_entry", "target": link})

# Pages not in index.md (skip CLAUDE.md, log.md, index.md itself, state/)
for f in sorted(all_files):
    skip = {"CLAUDE.md", "index.md", "log.md"}
    if os.path.basename(f) in skip:
        continue
    if f.startswith("state/") or f.startswith("raw/") or f.startswith("scripts/"):
        continue
    if f not in index_links:
        issues.append({"type": "link", "severity": "warning",
                       "msg": f"Not in index.md: {f}",
                       "fix": "add_index_entry", "target": f})

# 3. Broken wikilinks across all files
for f in all_files:
    full = os.path.join(vault, f)
    with open(full, encoding="utf-8") as fh:
        content = fh.read()
    for link in re.findall(r"\[\[([^\]]+\.md)\]\]", content):
        if link not in all_files:
            issues.append({"type": "link", "severity": "error",
                           "msg": f"Broken wikilink [[{link}]] in {f}",
                           "fix": None, "target": link, "source_file": f})

# 4. Orphan pages (not referenced from index.md or any other file)
referenced = set(index_links)
for f in all_files:
    full = os.path.join(vault, f)
    with open(full, encoding="utf-8") as fh:
        content = fh.read()
    for link in re.findall(r"\[\[([^\]]+\.md)\]\]", content):
        referenced.add(link)

skip_orphan = {"CLAUDE.md", "index.md", "log.md"}
for f in all_files:
    if os.path.basename(f) in skip_orphan:
        continue
    if f.startswith("state/") or f.startswith("raw/") or f.startswith("scripts/"):
        continue
    if f not in referenced:
        issues.append({"type": "link", "severity": "info",
                       "msg": f"Orphan page (not linked from anywhere): {f}",
                       "fix": None, "target": f})

print(json.dumps(issues))
```

### 2d — LINT check (Python)

```python
import os, re, json
from datetime import date, datetime

issues = []
vault = "<VAULT_PATH>"
today = date.today()

for root, _, files in os.walk(vault):
    rel = os.path.relpath(root, vault)
    if any(rel.startswith(s) for s in ["state", "raw", "scripts", "archive", ".git"]):
        continue
    for fname in files:
        if not fname.endswith(".md") or fname in {"CLAUDE.md", "index.md", "log.md"}:
            continue
        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, vault)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            continue
        fm_text = fm_match.group(1)

        # Stale: status:active + date > 90 days
        status_m = re.search(r"^status:\s*(\S+)", fm_text, re.MULTILINE)
        date_m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", fm_text, re.MULTILINE)
        if status_m and status_m.group(1) == "active" and date_m:
            try:
                page_date = datetime.strptime(date_m.group(1), "%Y-%m-%d").date()
                age = (today - page_date).days
                if age > 90:
                    issues.append({"type": "lint", "severity": "warning",
                                   "msg": f"Stale page ({age}d, status:active): {rel_path}",
                                   "fix": None, "target": rel_path})
            except ValueError:
                pass

        # Kaynaksız iddia: source:manuel but no ## Sources section
        source_m = re.search(r"^source:\s*[\"']?manuel[\"']?", fm_text, re.MULTILINE)
        if source_m and "## Sources" not in content and "## Kaynaklar" not in content:
            issues.append({"type": "lint", "severity": "warning",
                           "msg": f"Source:manuel but no ## Sources section: {rel_path}",
                           "fix": None, "target": rel_path})

print(json.dumps(issues))
```

## Step 3 — Print report

After collecting issues from all four checks for each vault, print the report:

```
vault:doctor — YYYY-MM-DD
══════════════════════════════════════════
Global Vault  ~/Global Claude Vault/
──────────────────────────────────────────
  Yapı        ✓ Tüm klasörler/dosyalar mevcut
              ✗ Missing folder: bugs/
  Frontmatter ✓ Tüm sayfalar tam
              ✗ Missing field 'title': decisions/foo.md
  Linkler     ✗ 3 kırık wikilink (otomatik düzeltilemez)
              ✗ 2 index.md dead link (düzeltilebilir)
              ⚠ 5 sayfa index.md'de yok (düzeltilebilir)
              ℹ 1 orphan sayfa
  LINT        ✗ 4 stale sayfa (>90 gün)
              ⚠ 1 kaynaksız iddia

Project Vault  ./docs/vault/
──────────────────────────────────────────
  ✓ Sorun bulunamadı

══════════════════════════════════════════
Toplam: 17 sorun  (N hata ✗ · M uyarı ⚠ · K bilgi ℹ)
Otomatik düzeltilebilir: X sorun

Düzeltme seçeneği:
  [A] Tüm düzeltilebilir sorunları otomatik uygula
  [B] Her sorun için ayrı ayrı karar ver
  [C] Sadece raporu kaydet, şimdilik geç
```

Severity legend:
- `✗` error — yapısal sorun veya kırık link
- `⚠` warning — lint uyarısı, eksik öneri
- `ℹ` info — orphan, bilgilendirme

## Step 4 — Handle user choice

### If user picks [C] or no fixable issues

Skip to Step 5 (write report).

### If user picks [A] — Auto-fix all

Iterate through all auto-fixable issues in this order:

1. **create_dir**: `mkdir -p <vault>/<target>` — print `✓ Klasör oluşturuldu: <target>`
2. **create_file**: Create stub file — print `✓ Dosya oluşturuldu: <target>`
   - `state/pending.md` stub:
     ```markdown
     # Pending Ingest Queue
     | # | Session ID | Project | Date | Size |
     |---|-----------|---------|------|------|
     ```
   - `state/ingested.txt` stub: empty file
   - `index.md` stub: minimal CONTENT_INDEX header matching the vault's language
   - `log.md` stub: `# Vault Log\n`
3. **remove_index_entry**: Remove the dead `[[link]]` line from `index.md` — print `✓ index.md'den kaldırıldı: [[<target>]]`
4. **add_index_entry**: Append missing page to the appropriate section in `index.md` — print `✓ index.md'e eklendi: <target>`
5. **add_frontmatter_field**: Open the file, insert the missing field after `---` with value `# DOCTOR-TODO` — print `✓ Alan eklendi: <field> → <target>`

After all fixes: print `\nToplam X sorun düzeltildi.`

### If user picks [B] — Interactive

For each auto-fixable issue, one at a time:
1. Print the issue clearly: `[N/Total] <severity> <msg>`
2. Describe what the fix will do: `Düzeltme: <action description>`
3. Ask: `Düzelteyim mi? (e/h/atla)`
4. If `e` (evet): apply fix, print `✓ Düzeltildi`
5. If `h` (hayır) or `atla`: print `— Atlandı`
6. Move to next issue

After loop: print summary of fixed vs skipped.

## Step 5 — Write report to syntheses/

For each vault that had issues, write `<vault>/syntheses/doctor-YYYY-MM-DD.md`:

```markdown
---
title: Vault Doctor Report — YYYY-MM-DD
tags: [vault, health, doctor]
source: "vault:doctor"
date: YYYY-MM-DD
status: draft
---

# Vault Doctor Report — YYYY-MM-DD

## Özet

- Toplam sorun: N (X hata, Y uyarı, Z bilgi)
- Otomatik düzeltilen: K sorun
- Manuel ilgi gerektiren: M sorun

## Yapısal Sorunlar

<list each issue with status: düzeltildi / atlandı / rapor-only>

## Frontmatter Sorunları

<list>

## Link Bütünlüğü

<list — broken wikilinks and orphans marked as "Manuel inceleme gerekli">

## LINT Uyarıları

<list — stale pages, kaynaksız iddias>
```

## Step 6 — Update log.md

Append to `<vault>/log.md`:

```
## [YYYY-MM-DD] vault:doctor | N hata, M uyarı, K bilgi — X otomatik düzeltildi
```

## Error handling

- If a vault file cannot be read during scanning: log `? (okuma hatası)` for that file and continue — never abort the whole scan.
- If index.md is missing: skip link integrity check for that vault, report it as a structural error.
- If project vault `./docs/vault/` has no `.md` files yet: print `  Project vault boş — henüz içerik yok.`
- If `ctx_execute` fails for a Python snippet: catch error, note which check failed, continue with remaining checks.
```

**Step 2: Verify file was created correctly**

Check that the file exists and has proper frontmatter:
```bash
head -5 ~/.claude/commands/vault/doctor.md
```
Expected: first line is `description: Scan global and project vaults...`

**Step 3: Commit**

```bash
git add ~/.claude/commands/vault/doctor.md
git commit -m "feat: add vault:doctor slash command"
```

---

## Task 2: Update `help.md` to include `vault:doctor`

**Files:**
- Modify: `~/.claude/commands/vault/help.md`

**Step 1: Read current help.md**

Read `~/.claude/commands/vault/help.md` to find the exact line to insert after.

**Step 2: Add vault:doctor entry**

In the command table, after the `/vault:status` line, insert:

```
  /vault:doctor                Scan vault health and optionally fix issues
```

And update the "Typical first-session workflow" section to add:

```
  /vault:doctor       → periodic health check + repair
```

**Step 3: Verify**

Read the updated file to confirm the entry appears correctly.

**Step 4: Commit**

```bash
git add ~/.claude/commands/vault/help.md
git commit -m "docs: add vault:doctor to help command"
```

---

## Task 3: Smoke test

**Step 1: Run `/vault:doctor` in a fresh session**

Open a new Claude Code session and run `/vault:doctor`. Verify:
- Both vaults are scanned
- Report is printed with correct format
- Repair prompt appears (or "vault sağlıklı" if no issues)
- Choosing [A], [B], [C] each behaves correctly
- Report file is written to `syntheses/doctor-YYYY-MM-DD.md`
- `log.md` is updated

**Step 2: Confirm no regressions**

Run `/vault:status` and `/vault:help` — verify they still work correctly and that `/vault:help` now shows `vault:doctor`.

---

## Deliverables Checklist

- [ ] `~/.claude/commands/vault/doctor.md` created
- [ ] `~/.claude/commands/vault/help.md` updated
- [ ] `syntheses/doctor-YYYY-MM-DD.md` produced on first run
- [ ] `log.md` updated on first run
