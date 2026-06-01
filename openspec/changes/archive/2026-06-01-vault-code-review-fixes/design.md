## Context

The plugin has two Python entry points: `vault-context.py` (runs as a SessionStart hook) and `scan-sessions.py` (subprocess called by `vault-context.py` to populate the pending queue). A rename from `~/claude-vault` to `~/Global Claude Vault` was applied to most of the codebase but was missed in `scan-sessions.py`. Additionally, the `run_scan()` call in `vault-context.py` spawns a subprocess without forwarding the `CLAUDE_VAULT` env var, so even if the user exports it, the subprocess won't see it unless explicitly passed. The combined effect is a silently broken scan pipeline on all default installs.

A second independent bug: `install.sh` embeds the custom vault path only as a fallback string for locating the script file — it never exports it or passes it to the running Python process, so `vault-context.py` ignores custom paths entirely.

Beyond correctness bugs, there are repo hygiene issues (tracked files with personal absolute paths), a version drift between `plugin.json`/`__version__` (1.0.0) and `marketplace.json` (0.1.0), Python version compat issues (`Path | None` syntax requires 3.10+ without `__future__`), and minor data quality bugs in slugify and token counting.

## Goals / Non-Goals

**Goals:**
- Make the scan→pending pipeline work on all default installs
- Make `CLAUDE_VAULT=/path ./install.sh` actually route through to runtime
- Achieve Python 3.7+ compatibility via `__future__` annotations
- Make plugin install (Option A) work on Windows and fully copy required scripts
- Fix slugify Turkish character mapping
- Standardize token savings methodology with documented assumptions
- Remove personal machine paths from git tracking
- Align all version strings to 1.0.0

**Non-Goals:**
- Refactoring the overall vault architecture
- Adding new vault features
- Changing the ingest pipeline
- Altering the CLAUDE.md injection format

## Decisions

### D1: Pass vault path as `sys.argv[1]` to `vault-context.py`

**Decision**: The hook command becomes `[sys.executable, str(script_path), str(vault_path)]`; `vault-context.py` reads `sys.argv[1]` if present and uses it as the vault override.

**Rationale**: This is the most explicit and robust approach — no reliance on env var inheritance, no need for shell-level exports, works on Windows and macOS. The alternative (writing a permanent `export CLAUDE_VAULT=...` to `~/.zshrc`/`~/.bashrc`) is fragile across shells and would surprise users.

**Alternative considered**: Inject `CLAUDE_VAULT` into the hook's environment block — rejected because `~/.claude/settings.json` hook format doesn't have a native env section, and shell-level exports don't propagate to subprocess spawned by the Claude Code daemon.

### D2: Pass `CLAUDE_VAULT` explicitly in `run_scan()` subprocess call

**Decision**: Change `subprocess.run([sys.executable, scan_script])` to `subprocess.run([sys.executable, scan_script], env={**os.environ, "CLAUDE_VAULT": str(vault)})`.

**Rationale**: Even with D1, `os.environ` inside `vault-context.py` may not have `CLAUDE_VAULT` set if the user didn't export it. Explicit forwarding is defense-in-depth and costs nothing. The alternative (reading `sys.argv` in `scan-sessions.py` too) would work but adds coupling; env var forwarding keeps `scan-sessions.py` independently runnable.

### D3: Fix `scan-sessions.py` default path independently of D2

**Decision**: Change the default in `scan-sessions.py` from `~/claude-vault` to `~/Global Claude Vault`.

**Rationale**: Without this, manual `python3 scan-sessions.py` invocations (without CLAUDE_VAULT set) still write to the wrong directory. D2 alone would fix the hook path but leave the standalone invocation broken.

### D4: `from __future__ import annotations` over requiring Python 3.10+

**Decision**: Add `from __future__ import annotations` to the top of both Python files.

**Rationale**: This backports PEP 604 `X | Y` union syntax to Python 3.7+ at zero cost. Requiring 3.10+ via README would exclude Ubuntu 20.04 system Python (3.8) and older macOS Homebrew setups. The `__future__` import is a one-liner that solves it universally.

### D5: Standardize token counting to `bytes / 4` (character-approximate)

**Decision**: Use `len(text) / 4` (characters, which approximates tokens) consistently everywhere — token log, README savings calculation, and status display.

**Rationale**: The current state uses `chars / 4` in the log but `bytes / 5` in the README. `bytes / 5` is a common heuristic for English-heavy tokenization but is less accurate for Turkish/multilingual content (which this plugin explicitly handles). `chars / 4` is more universally applicable. Both are estimates — what matters is consistency and documentation. All occurrences will be updated and a `# Token estimate: 1 token ≈ 4 chars` comment added where the constant appears.

### D6: Windows Python detection in plugin install (Option A)

**Decision**: Change the hardcoded `python3` in the hook command to a detection snippet that tries `python3`, then `python`, then `py`.

**Rationale**: On Windows, `python3` is almost never in PATH. The standalone installer already handles this — parity is required for the plugin path to honestly claim "Full support" on Windows.

## Risks / Trade-offs

- **D1 changes hook format** → Any user who manually configured the hook (not via install.sh) will have the old format without `sys.argv[1]`. Mitigation: `vault-context.py` must treat `sys.argv[1]` as optional (fall back to default path if absent), so old hook configs continue to work.
- **D5 changes reported token numbers** → Historical token-log entries used `chars / 4`; changing the README formula to match is cosmetic alignment, not a data migration. Mitigation: add a one-line note in README that numbers are estimates.
- **git rm --cached** for context-mode.json and serena files → Future installs won't include these files, but existing clones already have them. No functional impact; pure repo cleanliness.

## Migration Plan

1. Apply all code changes (scripts, install scripts, plugin.json, marketplace.json, README)
2. `git rm --cached .github/hooks/context-mode.json .serena/project.yml`
3. Commit everything in a single PR
4. Create GitHub tag/release `v1.0.1` after merge (bumping patch version for bugfixes)
5. No vault data migration needed — all changes are in the plugin code, not stored vault data

## Open Questions

- Should `marketplace.json` version be bumped to `1.0.1` (the post-fix release) rather than aligned to `1.0.0`? Recommend yes if a GitHub release is created alongside this fix.
