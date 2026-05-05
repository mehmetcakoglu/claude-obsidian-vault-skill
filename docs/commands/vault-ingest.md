# /vault:ingest

> Archive one pending Claude Code session into the appropriate vault, following the target vault's CLAUDE.md rules.

---

## Usage

```
/vault:ingest [session-id]
```

| Argument | Description |
|---|---|
| `session-id` | Optional. First 8+ characters of a session ID to force-ingest. If omitted, takes the **first row** in `state/pending.md` (sorted by size, largest first). |

---

## What it does

### Pre-flight

1. Reads `state/pending.md`. If empty → prints "Queue is empty." and stops.
2. Selects target session (by argument or first row).
3. Resolves the JSONL path: `~/.claude/projects/<project>/<session-id>.jsonl`
4. Determines target vault:
   - If the project folder maps to a local repo with `docs/vault/CLAUDE.md` → **project vault**
   - Otherwise → **global vault**

### Ingest

1. **Parses** the JSONL via `ctx_execute` or `ctx_execute_file` (never `Read` — multi-MB files overflow context). Extracts:
   - User prompts and their topics
   - Major decisions made
   - Files touched
   - Errors encountered and fixes applied
   - Duration and compaction events

2. **Decides** which pages to write:
   - `sources/sessions/YYYY-MM-DD-<slug>.md` — always
   - `decisions/`, `concepts/`, `entities/`, `bugs/`, `lessons/` — only when content justifies a standalone atomic page
   - Prefers linking to existing pages over duplicating

3. **Writes** pages with full YAML frontmatter (`title`, `tags`, `source`, `date`, `status`). Cross-links pages with `[[path/to/page.md]]`.

4. **Security filter:** never writes secrets (API keys, tokens, passwords, production IPs, DB credentials). Uses placeholders (`stored in env`, `redacted`) and notes exclusions in `log.md`.

### Post-ingest bookkeeping

1. Updates `index.md`: adds new pages under correct section headings, bumps "Last updated".
2. Appends to `log.md`: date, slug, source path, size, topics, pages created, exclusions.
3. **Appends session ID to `state/ingested.txt`** with a `# ingest #N — <slug>` comment.
4. **Appends size entry to `state/ingest-sizes.txt`**: `SESSION_ID\tBYTES\tDATE\tPROJECT`.
5. Re-runs `scan-sessions.py --quiet` to refresh `pending.md`.
6. Commits the change with `docs(vault): ingest #N — <slug>`.

---

## Output example

```
Ingesting: 2026-04-23-pft-receivable-ledger-reorg
Source: ~/.claude/projects/-Users-me-Personal-Finance-Tracker/c72d256b.jsonl  (8.7 MB)
Target: project vault (docs/vault/)

Summary:
  - Moved receivable categories to Income section in UI
  - Fixed net_remaining formula (was double-counting)
  - Files touched: ledger.vue, AccountPlan.vue, api/receivables.py

Pages to write:
  ✓ sources/sessions/2026-04-23-pft-receivable-ledger-reorg-and-net-fix.md
  ✓ bugs/net-remaining-double-count.md
  ✓ decisions/2026-04-23-receivable-under-income.md

Approve? (y/n)
```

---

## Session routing logic

```
project folder name
        │
        ▼
map to local filesystem path
        │
        ├─ path/docs/vault/CLAUDE.md exists?
        │           YES → project vault at path/docs/vault/
        │           NO  → global vault
        ▼
write pages to target vault
```

The mapping from `~/.claude/projects/<folder>` to a filesystem path is done by reversing the folder name encoding (e.g. `-Users-me-MyProject` → `/Users/me/MyProject`).

---

## Files read

- `$VAULT/state/pending.md` (queue)
- `~/.claude/projects/<project>/<session>.jsonl` (source transcript)
- `<target-vault>/CLAUDE.md` (ingest rules)
- `<target-vault>/index.md` (for update)

## Files written

| File | Content |
|---|---|
| `<vault>/sources/sessions/YYYY-MM-DD-<slug>.md` | Session summary |
| `<vault>/decisions/YYYY-MM-DD-<slug>.md` | Architectural decisions (if any) |
| `<vault>/bugs/<slug>.md` | Bug reports with root cause and fix (if any) |
| `<vault>/concepts/<slug>.md` | New domain concepts (if any) |
| `<vault>/entities/<name>.md` | New or updated entities (if any) |
| `<vault>/lessons/<slug>.md` | Failure stories (if any) |
| `<vault>/index.md` | Updated with new page links |
| `<vault>/log.md` | Ingest log entry |
| `$GLOBAL_VAULT/state/ingested.txt` | Session ID appended |
| `$GLOBAL_VAULT/state/ingest-sizes.txt` | Size entry appended |

---

## Stop criteria

Processes **one** session per invocation. Use `/vault:batch-ingest` to process multiple.

---

## Related

- [vault-batch-ingest.md](vault-batch-ingest.md) — process multiple sessions
- [vault-scan.md](vault-scan.md) — refresh the queue
- [vault-skip.md](vault-skip.md) — skip a session
- [Index](../index.md)
