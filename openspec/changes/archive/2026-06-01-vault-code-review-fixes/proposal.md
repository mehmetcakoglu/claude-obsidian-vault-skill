## Why

A code review by Claude Opus 4.8 surfaced two critical bugs that break the plugin's core automation (the scan→pending pipeline is silently broken in default installs), plus a cluster of medium and minor issues that hurt cross-platform reliability and repo credibility. Fixing these before any further promotion is a prerequisite.

## What Changes

- **CRITICAL**: Fix vault path mismatch — `scan-sessions.py` defaults to `~/claude-vault` instead of `~/Global Claude Vault`; align it and pass `CLAUDE_VAULT` env var explicitly in `run_scan()`
- **CRITICAL**: Fix custom vault path support — `CLAUDE_VAULT=/path ./install.sh` silently ignores the custom path at runtime; pass vault path as `sys.argv[1]` to `vault-context.py`
- Fix `plugin.json` and `marketplace.json` descriptions still referencing `~/claude-vault/`
- Remove personally-identifiable machine paths from tracked files (`.github/hooks/context-mode.json`, `.serena/project.yml`) with `git rm --cached`
- Deduplicate `.gitignore` entries
- Align version: `marketplace.json` shows `0.1.0`, code and `plugin.json` show `1.0.0` — sync to `1.0.0`
- Add `from __future__ import annotations` to both `.py` files for Python 3.7+ compatibility (currently breaks on Python 3.8/3.9 with `TypeError` at import)
- Fix plugin install (Option A): detect `python`/`python3`/`py` on Windows; copy `scan-sessions.py` to vault on plugin install so `run_scan()` can find it
- Fix `slugify` bug: `'ü'` maps to `'ü'` (no-op) instead of `'u'` — `"Gümüş"` → `"gms"` today
- Standardize token savings methodology: choose one formula (chars/4 or bytes/5) and document assumptions in code and README
- Add inline comment to `pending.md` write path noting that first-prompt snippets are not secret-filtered

## Capabilities

### New Capabilities
- `vault-path-resolution`: Consistent, override-able vault path resolution shared between `vault-context.py` and `scan-sessions.py`, with explicit argv support for custom installs
- `python-platform-compat`: Python 3.7+ compatibility via `__future__` annotations; Windows-safe Python executable detection in plugin hooks; `scan-sessions.py` copied to vault on plugin install
- `data-quality-fixes`: Correct `slugify` Turkish character map; standardized and documented token-savings methodology; documented pending.md privacy caveat

### Modified Capabilities

<!-- No existing specs to delta against -->

## Impact

- `scripts/vault-context.py`: argv vault path override, `run_scan()` env passthrough, token methodology, `__future__` import
- `scripts/scan-sessions.py`: default vault path fix, `__future__` import
- `install.sh` / `install.ps1`: pass vault path as script argument; copy `scan-sessions.py` to vault; detect Python executable on Windows
- `plugin.json`, `marketplace.json`: description text, version alignment
- `.gitignore`: deduplication
- `.github/hooks/context-mode.json`, `.serena/project.yml`: untracked via `git rm --cached`
- `README.md`: Python version requirement, token methodology note
