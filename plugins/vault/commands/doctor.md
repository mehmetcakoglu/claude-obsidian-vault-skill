description: Scan global and project vaults for structural, frontmatter, link, and lint issues. Report findings, then offer to fix all at once or interactively.
allowed-tools: Read(~/Global Claude Vault/**), Read($CLAUDE_VAULT/**), Read(./docs/vault/**), Bash(find * *), Bash(python3 * *), mcp__plugin_context-mode_context-mode__ctx_batch_execute, mcp__plugin_context-mode_context-mode__ctx_execute, Edit(~/Global Claude Vault/**), Edit($CLAUDE_VAULT/**), Edit(./docs/vault/**), Write(~/Global Claude Vault/**), Write($CLAUDE_VAULT/**), Write(./docs/vault/**)

# /vault:doctor

Scan both the global vault and the project vault (if present) for issues, report them, then offer repair options.

## Step 1 — Resolve vault paths

Resolve:
- `GLOBAL_VAULT = $CLAUDE_VAULT` if set, otherwise `~/Global Claude Vault`
- `PROJECT_VAULT = ./docs/vault` only if `./docs/vault/CLAUDE.md` exists, otherwise None

If `GLOBAL_VAULT` directory does not exist: print `❌ Global vault not found at <path>. Run install.sh first.` and stop.

## Step 2 — Scan each vault

For each vault (global first, then project if present), run four Python checks via `ctx_execute` (language: "python"). Substitute `<VAULT_PATH>` with the actual resolved path in each snippet before running.

### 2a — Structural check

```python
import os, json

REQUIRED_DIRS = [
    "syntheses", "decisions", "entities", "concepts",
    "bugs", "lessons", "sources/sessions", "state", "raw"
]
REQUIRED_FILES = ["index.md", "log.md", "vault-config.json", "CLAUDE.md"]
STATE_FILES = ["state/pending.md", "state/ingested.txt"]

issues = []
vault = "<VAULT_PATH>"

for d in REQUIRED_DIRS:
    if not os.path.isdir(os.path.join(vault, d)):
        issues.append({"type": "structural", "severity": "error",
                       "msg": f"Missing folder: {d}", "fix": "create_dir", "target": d})

for f in REQUIRED_FILES + STATE_FILES:
    if not os.path.isfile(os.path.join(vault, f)):
        issues.append({"type": "structural", "severity": "error",
                       "msg": f"Missing file: {f}", "fix": "create_file", "target": f})

print(json.dumps(issues))
```

### 2b — Frontmatter check

```python
import os, re, json

REQUIRED_FIELDS = ["title", "tags", "source", "date", "status"]
VALID_STATUSES = {"draft", "active", "archived"}
SKIP_FILES = {"CLAUDE.md", "index.md", "log.md"}

issues = []
vault = "<VAULT_PATH>"

for root, _, files in os.walk(vault):
    rel = os.path.relpath(root, vault)
    if any(rel.startswith(s) for s in ["state", "raw", "scripts", "archive", ".git"]):
        continue
    for fname in files:
        if not fname.endswith(".md") or fname in SKIP_FILES:
            continue
        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, vault)
        try:
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            issues.append({"type": "frontmatter", "severity": "warning",
                           "msg": f"Could not read: {rel_path}", "fix": None, "target": rel_path})
            continue
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
        status_match = re.search(r"^status:\s*(\S+)", fm_text, re.MULTILINE)
        if status_match and status_match.group(1) not in VALID_STATUSES:
            invalid_val = status_match.group(1)
            suggested = "archived" if invalid_val == "ingested" else None
            issues.append({"type": "frontmatter", "severity": "warning",
                           "msg": f"Invalid status '{invalid_val}': {rel_path}",
                           "fix": "fix_invalid_status" if suggested else None,
                           "suggested_value": suggested,
                           "target": rel_path})

print(json.dumps(issues))
```

### 2c — Link integrity check

```python
import os, re, json

issues = []
vault = "<VAULT_PATH>"

all_files = set()
for root, _, files in os.walk(vault):
    rel = os.path.relpath(root, vault)
    if any(rel.startswith(s) for s in ["state", "raw", "scripts", ".git"]):
        continue
    for fname in files:
        if fname.endswith(".md"):
            all_files.add(os.path.relpath(os.path.join(root, fname), vault))

index_path = os.path.join(vault, "index.md")
index_links = set()
if os.path.isfile(index_path):
    with open(index_path, encoding="utf-8") as fh:
        index_content = fh.read()
    index_links = set(re.findall(r"\[\[([^\]]+\.md)\]\]", index_content))

# Build basename → vault-relative path map (needed for normalization)
basename_to_path = {}
for f in all_files:
    basename_to_path[os.path.basename(f)] = f

# Normalize index_links: bare filenames → vault-relative paths
normalized_index_links = set()
for link in index_links:
    if "/" in link:
        normalized_index_links.add(link)
    else:
        resolved = basename_to_path.get(link)
        normalized_index_links.add(resolved if resolved else link)
index_links = normalized_index_links

for link in index_links:
    if link not in all_files:
        issues.append({"type": "link", "severity": "error",
                       "msg": f"index.md dead link: [[{link}]]",
                       "fix": "remove_index_entry", "target": link})

SKIP_BASES = {"CLAUDE.md", "index.md", "log.md"}
SKIP_PREFIXES = ("state/", "raw/", "scripts/")
for f in sorted(all_files):
    if os.path.basename(f) in SKIP_BASES:
        continue
    if any(f.startswith(p) for p in SKIP_PREFIXES):
        continue
    if f not in index_links:
        issues.append({"type": "link", "severity": "warning",
                       "msg": f"Not in index.md: {f}",
                       "fix": "add_index_entry", "target": f})

SKIP_WIKILINK_SCAN = {"CLAUDE.md"}  # template file, placeholder links are intentional
for f in all_files:
    if os.path.basename(f) in SKIP_WIKILINK_SCAN:
        continue
    full = os.path.join(vault, f)
    try:
        with open(full, encoding="utf-8") as fh:
            content = fh.read()
    except Exception:
        continue
    for link in re.findall(r"\[\[([^\]]+\.md)\]\]", content):
        if link not in all_files:
            in_report = f.startswith("syntheses/") or f.startswith("bugs/")
            issues.append({"type": "link", "severity": "error",
                           "msg": f"Broken wikilink [[{link}]] in {f}",
                           "fix": "fix_wikilink_in_report" if in_report else None,
                           "target": link, "source_file": f})

# Build referenced set — normalize bare filenames to vault-relative paths
referenced = set(index_links)
for f in all_files:
    full = os.path.join(vault, f)
    try:
        with open(full, encoding="utf-8") as fh:
            content = fh.read()
    except Exception:
        continue
    for link in re.findall(r"\[\[([^\]]+\.md)\]\]", content):
        if "/" in link:
            referenced.add(link)
        else:
            # bare filename — resolve to vault-relative path if possible
            resolved = basename_to_path.get(link)
            if resolved:
                referenced.add(resolved)
            else:
                referenced.add(link)

SKIP_ORPHAN = {"CLAUDE.md", "index.md", "log.md"}
SKIP_PREFIXES = ("state/", "raw/", "scripts/")
for f in all_files:
    if os.path.basename(f) in SKIP_ORPHAN:
        continue
    if any(f.startswith(p) for p in SKIP_PREFIXES):
        continue
    if f not in referenced:
        issues.append({"type": "link", "severity": "info",
                       "msg": f"Orphan page (not linked from anywhere): {f}",
                       "fix": None, "target": f})

print(json.dumps(issues))
```

### 2d — LINT check

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
        try:
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            continue
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            continue
        fm_text = fm_match.group(1)

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

        source_m = re.search(r"^source:\s*[\"']?manuel[\"']?", fm_text, re.MULTILINE)
        if source_m and "## Sources" not in content and "## Kaynaklar" not in content:
            issues.append({"type": "lint", "severity": "warning",
                           "msg": f"Source:manuel but no ## Sources section: {rel_path}",
                           "fix": "add_sources_section", "target": rel_path})

print(json.dumps(issues))
```

## Step 3 — Print report

Print all text in English. Use English for all output labels, section headers, fix messages, and user prompts. Only use another language if the user explicitly requests it.

After collecting all issues for both vaults, print the report:

```
vault:doctor — YYYY-MM-DD
══════════════════════════════════════════
Global Vault  ~/Global Claude Vault/
──────────────────────────────────────────
  Structure   ✓ All folders/files present
              ✗ Missing folder: bugs/
  Frontmatter ✓ All pages complete
              ✗ Missing field 'title': decisions/foo.md
  Links       ✗ 3 broken wikilinks (cannot auto-fix)
              ✗ 2 index.md dead links (fixable)
              ⚠ 5 pages missing from index.md (fixable)
              ℹ 1 orphan page
  LINT        ⚠ 4 stale pages (>90 days)
              ⚠ 1 unsourced claim

Project Vault  ./docs/vault/
──────────────────────────────────────────
  ✓ No issues found

══════════════════════════════════════════
Total: 17 issues  (N errors ✗ · M warnings ⚠ · K info ℹ)
Auto-fixable: X issues

Fix options:
  [A] Apply all auto-fixable issues automatically
  [B] Decide on each issue interactively
  [C] Save report only, skip fixes for now
```

If zero issues found across all vaults: print `✓ Vault healthy — no issues found.` and skip to Step 5.

Severity icons: `✗` error · `⚠` warning · `ℹ` info

## Step 4 — Handle user choice

Wait for the user to type A, B, or C (or [A], [B], [C]).

### [C] — Skip fixes

Go directly to Step 5.

### [A] — Auto-fix all

Apply all auto-fixable issues (those with a non-null `fix` field) in this order:
1. **create_dir**: Bash `mkdir -p <vault>/<target>` → print `✓ Directory created: <target>`
2. **create_file**: Use Write tool to create stub file → print `✓ File created: <target>`
   - `state/pending.md` stub content:
     ```
     # Pending Ingest Queue
     | # | Session ID | Project | Date | Size |
     |---|-----------|---------|------|------|
     ```
   - `state/ingested.txt`: empty file
   - `index.md` stub: `# Content Index\n\n_No entries yet._\n`
   - `log.md` stub: `# Vault Log\n`
   - `vault-config.json` stub: `{"auto_ingest": false, "auto_ingest_max_per_session": 5, "version": "0.0.0"}`
   - **Special case — `CLAUDE.md`**: Do **not** auto-create it. Instead, print `⚠ CLAUDE.md missing — must be created manually. Run /vault:init.` and skip this file.
3. **remove_index_entry**: Use Edit tool to remove the dead `[[target]]` line from index.md → print `✓ Removed from index.md: [[<target>]]`
4. **add_index_entry**: Append the missing page reference to the relevant section of index.md → print `✓ Added to index.md: <target>`
5. **add_frontmatter**: Open the file and prepend a complete frontmatter block at the top using the Edit tool:
   ```
   ---
   title: # DOCTOR-TODO
   tags: []
   source: "manuel"
   date: YYYY-MM-DD
   status: draft
   ---
   ```
   Print `✓ Frontmatter added: <target>`
6. **add_frontmatter_field**: Use Edit tool to insert the missing field with value `# DOCTOR-TODO` into the file's frontmatter block → print `✓ Field added: <field> → <target>`
7. **fix_invalid_status**: Use Edit tool to replace `status: <invalid_val>` with `status: <suggested_value>` in the frontmatter of `target`. The `suggested_value` is provided in the issue object → print `✓ Status fixed: <invalid_val> → <suggested_value>: <target>`
8. **fix_wikilink_in_report**: Use Edit tool to replace every `[[<target>]]` occurrence with plain `<target>` (no brackets) in `source_file`. Use `replace_all: true` → print `✓ Wikilink flattened in <source_file>: [[<target>]] → <target>`
9. **add_sources_section**: Use Edit tool to append `\n\n## Sources\n\n_(no source recorded)_` at the end of `target` → print `✓ Sources section added: <target>`

After all fixes: print `\nTotal X issues fixed.`

### [B] — Interactive

Supported fix types in interactive mode: `create_dir`, `create_file`, `remove_index_entry`, `add_index_entry`, `add_frontmatter`, `add_frontmatter_field`, `fix_invalid_status`, `fix_wikilink_in_report`, `add_sources_section`.

For each auto-fixable issue, one at a time:
1. Print: `[N/Total] <severity-icon> <msg>`
2. Print: `Fix: <brief description of what will be done>`
3. Ask: `Apply fix? (y/n)`
4. If `y`: apply fix, print `✓ Fixed`
5. If `n`: print `— Skipped`

After all issues: print summary `X fixed, Y skipped.`

After processing all auto-fixable issues, print a summary of non-fixable issues (broken wikilinks, orphans, stale pages, unsourced claims) that require manual attention, so the user has a complete picture.

## Step 5 — Write report

For each vault that had any issues, write `<vault>/syntheses/doctor-YYYY-MM-DD.md` using the Write tool:

```markdown
---
title: Vault Doctor Report — YYYY-MM-DD
tags: [vault, health, doctor]
source: "vault:doctor"
date: YYYY-MM-DD
status: draft
---

# Vault Doctor Report — YYYY-MM-DD

## Summary

- Total issues: N (X errors ✗, Y warnings ⚠, Z info ℹ)
- Auto-fixed: K issues
- Requires manual attention: M issues

## Structural Issues

<list each structural issue — status: fixed / skipped / report-only>

## Frontmatter Issues

<list>

## Link Integrity

<list — broken wikilinks and orphans: "Manual review required">

## LINT Warnings

<list — stale pages, unsourced claims>
```

Always run `mkdir -p <vault>/syntheses/` via Bash before writing the report file, regardless of whether structural fixes were applied.

## Step 6 — Update log.md

For each vault where any issues were found (regardless of whether fixes were applied), append to `log.md`:

```
## [YYYY-MM-DD] vault:doctor | N errors, M warnings, K info — X auto-fixed
```

## Error handling

- Read failure on any file during scan: add a warning issue `"Could not read: <path>"` and continue — never abort.
- `index.md` missing: skip link integrity check for that vault; structural check will already flag it.
- Project vault empty (no .md files): print `  Project vault is empty — no content yet.` for that vault section.
- If `ctx_execute` fails: note which check failed in the report, continue with remaining checks.