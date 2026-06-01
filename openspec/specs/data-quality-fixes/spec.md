# data-quality-fixes Specification

## Purpose
TBD - created by archiving change vault-code-review-fixes. Update Purpose after archive.
## Requirements
### Requirement: slugify correctly maps Turkish characters to ASCII equivalents
The `slugify` function's character translation table SHALL map every non-ASCII Turkish character to its ASCII equivalent (not to itself or another non-ASCII character).

#### Scenario: ü maps to u
- **WHEN** `slugify("Gümüş")` is called
- **THEN** the result is `"gumus"` (not `"gms"`)

#### Scenario: All Turkish vowels/consonants map correctly
- **WHEN** `slugify` is called with any string containing `ş`, `ğ`, `ı`, `ü`, `ö`, `ç` (upper or lower)
- **THEN** each maps to its ASCII equivalent: `s`, `g`, `i`, `u`, `o`, `c`

### Requirement: Token savings methodology is consistent and documented
Token estimation SHALL use a single formula (`len(text) / 4`, character-based) everywhere it appears in code, logs, README, and the status display. The assumption SHALL be documented with an inline comment.

#### Scenario: Token log uses chars/4
- **WHEN** vault-context.py writes a token log entry
- **THEN** the token count is computed as `len(injected_text) // 4`

#### Scenario: README savings calculation uses the same formula
- **WHEN** the README describes token savings methodology
- **THEN** it states `characters ÷ 4` as the estimate basis (not `bytes ÷ 5`)

#### Scenario: Code comment documents assumption
- **WHEN** the token constant appears in source code
- **THEN** a comment `# Token estimate: 1 token ≈ 4 chars` appears on the same or adjacent line

### Requirement: pending.md privacy caveat is documented in code
The code that writes first-prompt snippets to `pending.md` SHALL include an inline comment noting that snippet content is not secret-filtered and that `pending.md` is not gitignored.

#### Scenario: Privacy comment present in source
- **WHEN** the snippet-writing code in `scan-sessions.py` is read
- **THEN** a comment notes that the snippet is written verbatim without secret filtering

#### Scenario: README privacy note present
- **WHEN** the README describes the `pending.md` queue
- **THEN** it mentions that session snippets are plain text and not secret-filtered

