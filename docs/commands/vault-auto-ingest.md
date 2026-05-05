# /vault:auto-ingest

> Enable, disable, or check the auto-ingest setting. When enabled, Claude automatically processes pending sessions at the start of each session.

---

## Usage

```
/vault:auto-ingest status               # show current state
/vault:auto-ingest on                   # enable (default max: 5)
/vault:auto-ingest on max N             # enable, set per-session maximum to N
/vault:auto-ingest off                  # disable (manual mode)
```

---

## What it does

Reads or modifies `vault-config.json` in the global vault:

```json
{
  "auto_ingest": true,
  "auto_ingest_max_per_session": 3
}
```

### status

Prints current configuration:

```
auto_ingest    : on
max per session: 3

When enabled, Claude will automatically process up to 3 pending sessions
at the start of each Claude Code session.
```

### on / off

Updates `vault-config.json` and confirms:

```
✓ auto_ingest set to: on (max 3 per session)
Takes effect at the next session start.
```

---

## How auto-ingest works at SessionStart

When `auto_ingest=true`, `vault-context.py` includes the following instruction in the injected `<system-reminder>`:

```
AUTO-INGEST: N sessions pending. Process them now using /vault:ingest
before responding to the first user message.
```

Claude then calls `/vault:ingest` up to `auto_ingest_max_per_session` times before the user's first message is answered.

### Trade-offs

| | `auto_ingest: off` (default) | `auto_ingest: on` |
|---|---|---|
| Control | Full — you decide what to archive | Automatic — Claude decides |
| Secret filtering | Manual review opportunity | Claude applies security filter |
| Latency | None at session start | ~30–90s per session if queue is non-empty |
| Queue buildup | Possible (manual clearing needed) | Unlikely (processes queue continuously) |

**Recommendation:** leave off until you trust the security filter and don't need to review each session before archiving.

---

## Files read

- `$VAULT/vault-config.json`

## Files written

- `$VAULT/vault-config.json` (when toggling)

---

## Related

- [vault-batch-ingest.md](vault-batch-ingest.md) — manual bulk processing
- [vault-status.md](vault-status.md) — shows current auto_ingest state
- [Index](../index.md)
