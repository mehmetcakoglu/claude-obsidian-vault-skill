# /vault:init

> Bootstrap a project vault — create `docs/vault/` with a full directory skeleton and a customized `CLAUDE.md` tailored to this project.

---

## Usage

```
/vault:init
```

No arguments. Runs in the current working directory.

---

## What it does

1. **Detects project context**: reads the current directory's git remote, language stack (package.json, pyproject.toml, go.mod, etc.), and existing source structure.

2. **Creates directory skeleton:**
   ```
   docs/vault/
   ├── CLAUDE.md              ← customized constitution
   ├── index.md               ← empty content index
   ├── log.md                 ← empty event log
   ├── vault-config.json      ← default config
   ├── sources/
   │   └── sessions/
   ├── decisions/
   ├── entities/
   ├── concepts/
   ├── bugs/
   ├── lessons/
   ├── syntheses/
   ├── archive/
   ├── raw/
   │   ├── sessions/          ← symlinks to JSONL (gitignored)
   │   └── docs/
   └── state/
       ├── pending.md
       └── ingested.txt
   ```

3. **Generates `CLAUDE.md`** — a customized vault constitution that includes:
   - Project name, stack, and integrations (detected automatically)
   - Domain vocabulary (extracted from directory/file names)
   - Directory layout table
   - Naming conventions
   - Page format templates
   - Ingest, query, and lint workflows
   - Hard rules (no sourceless claims, no deletions, etc.)

4. **Creates `vault-config.json`** with safe defaults:
   ```json
   {
     "auto_ingest": false,
     "auto_ingest_max_per_session": 5,
     "version": "0.0.0"
   }
   ```

5. **Adds `.gitignore`** entries for `raw/sessions/` (JSONL symlinks) and any other ignored patterns.

6. **Prints confirmation** and suggests the next step:
   ```
   ✓ Project vault initialized at docs/vault/
   ✓ CLAUDE.md generated for: my-project (Django + Vue)

   Next: run /vault:scan to see what's in the queue, then /vault:ingest to archive sessions.
   ```

---

## Idempotency

Safe to re-run. Existing files are **never overwritten** — only missing files and directories are created. Use this to repair a partially-initialized vault.

---

## CLAUDE.md generation

The generated `CLAUDE.md` adapts to the project:

| Detected signal | CLAUDE.md adaptation |
|---|---|
| `package.json` | Stack includes Node.js/TypeScript |
| `pyproject.toml` / `requirements.txt` | Stack includes Python |
| `go.mod` | Stack includes Go |
| `pom.xml` / `build.gradle` | Stack includes Java/Spring |
| Git remote URL | Homepage and repository fields |
| Directory names | Domain vocabulary suggestions |
| Existing `docs/` | Links to existing documentation |

---

## Files created

| File | Content |
|---|---|
| `docs/vault/CLAUDE.md` | Customized vault constitution |
| `docs/vault/index.md` | Empty content index |
| `docs/vault/log.md` | Empty event log |
| `docs/vault/vault-config.json` | Default config |
| `docs/vault/state/pending.md` | Empty queue |
| `docs/vault/state/ingested.txt` | Empty registry |
| `docs/vault/.gitignore` | Ignores raw/sessions/ |
| All required directories | — |

---

## Related

- [vault-scan.md](vault-scan.md) — next step after init
- [vault-doctor.md](vault-doctor.md) — verifies vault structure
- [Index](../index.md)
