---
description: Ingest the next pending Claude Code session into the appropriate vault (global or project)
argument-hint: "[optional: session-id prefix, defaults to top of queue]"
---

# /vault:ingest

Process one pending Claude Code session from `${CLAUDE_VAULT:-$HOME/claude-vault}/state/pending.md` into the appropriate vault, following the LLM-Wiki INGEST rules defined in each vault's `CLAUDE.md`.

## Argument

- `$1` — optional session ID (first 8+ characters) to force-ingest. If omitted, take the first row in `state/pending.md` (biggest by size).

## Pre-flight

1. Read `${CLAUDE_VAULT:-$HOME/claude-vault}/state/pending.md`. If empty → say "Queue is empty." and stop.
2. Pick the target session:
   - If `$1` is provided: match the row whose session ID starts with `$1`. Error if not found.
   - Otherwise: take the first row.
3. Identify:
   - **Source path**: `~/.claude/projects/<project>/<session-id>.jsonl`
   - **Target vault**:
     - If the project folder name maps to a local repository that has `docs/vault/CLAUDE.md`, use that **project vault**.
     - Otherwise, use the **global vault** at `${CLAUDE_VAULT:-$HOME/claude-vault}`.

## Ingest (follow the target vault's CLAUDE.md)

1. Parse the JSONL via a sandbox execution tool (`ctx_execute`, `ctx_execute_file`, or an equivalent local python helper). Never `Read` multi-megabyte transcripts — they overflow the context window. Build a summary covering: user prompts, major decisions, files touched, errors and fixes, duration, compaction events.
2. Decide which pages are warranted:
   - 1 × source file in `sources/sessions/YYYY-MM-DD-<slug>.md` (always)
   - Additional `decisions/`, `concepts/`, `entities/`, `bugs/`, `lessons/`, or `syntheses/` pages **only** when content justifies a standalone atomic page. Prefer linking to existing pages over duplicating.
3. Use YAML frontmatter on every page: `title`, `tags`, `source`, `date`, `status` (and `severity` for bugs).
4. Cross-link pages using `[[path/to/page.md]]`.
5. **Security filter**: never write secrets (API keys, tokens, passwords, production IPs, DB credentials) into any vault page. Use placeholders like `stored in env` or `redacted` and note the exclusion in `log.md`.

## Post-ingest bookkeeping

1. Update the target vault's `index.md`: add new pages under their section headings, bump the "Last updated" line, increment the ingest counter if present.
2. Append an entry to the target vault's `log.md`:
   - Date + ingest type + slug
   - Source path and size
   - Topics covered
   - List of pages created
   - Any skipped / excluded content and why
3. **Append the processed session ID to `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/state/ingested.txt`** with a `# ingest #N — <slug>` comment, even when the session was ingested into a project vault. `ingested.txt` is the shared registry across all vaults.

4. **Record the session's raw file size** in `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/state/ingest-sizes.txt` — one tab-separated line:
   ```
   <session-id>\t<size-in-bytes>\t<YYYY-MM-DD>\t<project-name>
   ```
   Get the byte size from the JSONL source path (`stat` or `os.path.getsize`). This data is used by `/vault:status` to compute accurate token savings (raw JSONL bytes → tokens saved vs. vault injection cost). If the file size cannot be determined, skip this step silently.

5. Re-run `${CLAUDE_VAULT:-$HOME/Global Claude Vault}/scripts/scan-sessions.py --quiet` to refresh `pending.md`.
5. Commit the change in the target repository (global vault repo for global ingests, project repo for project ingests) with a `docs(vault): ingest #N — <slug>` message.

## Stop criteria

Process **one** session per invocation. If the user wants more, they can run `/vault:ingest` again. This keeps each ingest reviewable and keeps token usage bounded.
