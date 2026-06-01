## 1. Critical: Vault Path Resolution

- [x] 1.1 In `scripts/scan-sessions.py`: change the default vault path constant from `~/claude-vault` to `~/Global Claude Vault`
- [x] 1.2 In `scripts/vault-context.py`: update `run_scan()` to pass `env={**os.environ, "CLAUDE_VAULT": str(vault)}` to the subprocess call
- [x] 1.3 In `scripts/vault-context.py`: add `sys.argv[1]` support — if `len(sys.argv) > 1`, use `sys.argv[1]` as the vault path override (fallback to env var / default)
- [x] 1.4 In `install.sh`: change hook command to include vault path as third argument: `[sys.executable, str(script_path), str(vault_path)]`
- [x] 1.5 In `install.ps1`: same as 1.4 for PowerShell hook format
- [x] 1.6 In `plugin.json` description field: replace `~/claude-vault/` with `~/Global Claude Vault`
- [x] 1.7 In `marketplace.json` description field: replace `~/claude-vault/` with `~/Global Claude Vault`

## 2. Critical: Python & Platform Compatibility

- [x] 2.1 Add `from __future__ import annotations` as first import in `scripts/vault-context.py`
- [x] 2.2 Add `from __future__ import annotations` as first import in `scripts/scan-sessions.py`
- [x] 2.3 Update README.md Requirements section: change "Python 3" to "Python 3.7+"
- [x] 2.4 In `plugin.json` hook: add `python3 ... || python ...` fallback for Windows; pass vault path as argv
- [x] 2.5 In plugin install flow: ensure `scan-sessions.py` is copied to `$VAULT/scripts/` alongside `vault-context.py`

## 3. Repo Hygiene & Version Alignment

- [x] 3.1 Run `git rm --cached .github/hooks/context-mode.json .serena/project.yml` to untrack personal machine files
- [x] 3.2 Verify both files remain in `.gitignore` (no re-addition)
- [x] 3.3 Deduplicate `.gitignore`: remove repeated patterns so each rule appears exactly once
- [x] 3.4 In `marketplace.json`: update `version` field from `0.1.0` to `1.0.0` (align with `plugin.json` and `__version__`)
- [x] 3.5 Bump all version strings `1.0.0` → `1.0.1`, tag `v1.0.1`, and push to GitHub `main` (bump patch for this bugfix set)

## 4. Data Quality Fixes

- [x] 4.1 In `scripts/vault-context.py` and/or `scripts/scan-sessions.py` slugify translation table: fix the `ü` entry — change target from `'ü'` to `'u'`; verify `ş→s`, `ğ→g`, `ı→i`, `ö→o`, `ç→c` are all correct
- [x] 4.2 In `scripts/vault-context.py`: standardize token count to `len(text) // 4`; add comment `# Token estimate: 1 token ≈ 4 chars`
- [x] 4.3 In `README.md` token savings section: update formula description to `characters ÷ 4` (was `bytes ÷ 5`); add a one-line note that numbers are estimates
- [x] 4.4 In `scripts/scan-sessions.py` snippet-writing code: add inline comment noting that the first-prompt snippet is written verbatim and is not secret-filtered
- [x] 4.5 In `README.md`: add a brief note in the pending.md / queue section that session snippets are plain text and not secret-filtered

## 5. Verification

- [x] 5.1 On a clean shell (no `CLAUDE_VAULT` exported): run `python3 scripts/scan-sessions.py` manually and confirm it writes to `~/Global Claude Vault/state/pending.md`
- [x] 5.2 Run `python3 scripts/vault-context.py` on Python 3.8 (or `python3 -c "import ast; ast.parse(open('scripts/vault-context.py').read())"`) — confirm no TypeError
- [x] 5.3 Confirm `slugify("Gümüş") == "gumus"`
- [x] 5.4 Run `git ls-files .github/hooks/context-mode.json .serena/project.yml` — confirm empty output
- [x] 5.5 Confirm all three version strings (`plugin.json`, `marketplace.json`, `__version__`) match

## 6. Follow-up review (2026-06-01) — completing the partial rename

A second pass (Opus 4.8 re-review) revealed the first round applied the fixes only to
the Python scripts, README.md, and JSON manifests — **the same bugs remained in command,
skill, template, and doc files**. These were completed:

- [x] 6.1 `~/claude-vault` → `~/Global Claude Vault` across the files the rename missed:
      `commands/ingest.md` (3×, incl. the critical `pending.md` read path), `commands/batch-ingest.md`,
      `skills/vault/SKILL.md` (10×), `templates/global-vault/CLAUDE.md`, `templates/project-vault/CLAUDE.md` (5×),
      `docs/CONCEPTS.md`, `docs/ATTRIBUTION.md`, `docs/EXAMPLES.md`
- [x] 6.2 Token methodology `÷ 5` → `÷ 4` where the first pass missed it:
      `commands/status.md` (2×), `docs/commands/vault-status.md`, `README.tr.md` (formula + rationale + example)
- [x] 6.3 `README.tr.md`: "Python 3" → "Python 3.7+" (parity with English README)
- [x] 6.4 `install.ps1`: add `doctor.md` to the copy list, the install summary, and the verify loop
      (Windows standalone install was silently missing `/vault:doctor`)
- [x] 6.5 `vault-context.py`: guard `bootstrap_vault()` on `CLAUDE.md` existence instead of the vault dir,
      so the plugin SessionStart hook pre-creating `<vault>/scripts/` no longer skips first-run bootstrap
- [x] 6.6 Final sweep: zero stray `claude-vault` paths, zero `÷ 5` methodology, both scripts parse, installer parity 3/3
