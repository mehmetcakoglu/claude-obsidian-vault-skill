# vault-path-resolution Specification

## Purpose
TBD - created by archiving change vault-code-review-fixes. Update Purpose after archive.
## Requirements
### Requirement: scan-sessions.py defaults to ~/Global Claude Vault
`scan-sessions.py` SHALL use `~/Global Claude Vault` as its default vault path when `CLAUDE_VAULT` is not set in the environment.

#### Scenario: Default path used when CLAUDE_VAULT unset
- **WHEN** `scan-sessions.py` is invoked without `CLAUDE_VAULT` in the environment
- **THEN** it scans `~/Global Claude Vault` for new sessions and writes to `~/Global Claude Vault/state/pending.md`

#### Scenario: CLAUDE_VAULT override still respected
- **WHEN** `scan-sessions.py` is invoked with `CLAUDE_VAULT=/custom/path` in the environment
- **THEN** it uses `/custom/path` as the vault root

### Requirement: run_scan passes CLAUDE_VAULT to subprocess
`vault-context.py`'s `run_scan()` function SHALL pass `CLAUDE_VAULT` explicitly in the subprocess environment.

#### Scenario: CLAUDE_VAULT forwarded even when not in parent env
- **WHEN** `vault-context.py` calls `run_scan()` and `CLAUDE_VAULT` is not in the shell environment
- **THEN** the subprocess receives `CLAUDE_VAULT` set to the resolved vault path
- **THEN** `scan-sessions.py` writes to the correct vault

### Requirement: Custom vault path passed as argv to vault-context.py
`install.sh` and `install.ps1` SHALL embed the vault path as `sys.argv[1]` in the hook command, and `vault-context.py` SHALL accept it as a runtime override.

#### Scenario: Custom path install routes correctly at runtime
- **WHEN** user runs `CLAUDE_VAULT=/my/vault ./install.sh`
- **THEN** the generated hook command is `[python, vault-context.py, /my/vault]`
- **THEN** `vault-context.py` uses `/my/vault` as its vault root

#### Scenario: Legacy hooks without argv still work
- **WHEN** `vault-context.py` is invoked without `sys.argv[1]`
- **THEN** it falls back to `~/Global Claude Vault` or `CLAUDE_VAULT` env var

### Requirement: Description text references correct default path
`plugin.json` and `marketplace.json` description fields SHALL reference `~/Global Claude Vault` (not `~/claude-vault`).

#### Scenario: Marketplace description shows correct path
- **WHEN** a user views the plugin in the Claude Code marketplace
- **THEN** the description text mentions `~/Global Claude Vault`

