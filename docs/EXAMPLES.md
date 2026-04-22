# Examples

End-to-end walkthroughs of the three main operations: `INGEST`, `QUERY`,
`LINT`. Commands shown are what you type to Claude Code — the LLM drives the
rest.

---

## Example 1 — Bootstrapping a new project

You've cloned `billing-service`, started a Claude Code session, and want a
project vault.

```
cd billing-service/
/vault:init
```

What happens:

1. The command inspects the current directory — `pyproject.toml` found →
   stack = Python.
2. Claude asks you 3–5 clarifying questions:
   - What does this project do? _("Customer billing + invoicing, Django +
     Stripe")_
   - What's the tagline you'd use in a README?
   - Key domain terms? _("subscription, invoice, proration, dunning")_
   - Any external integrations? _("Stripe, SendGrid, Postgres")_
   - Primary vault language? _("English")_
3. Claude writes:
   - `docs/vault/CLAUDE.md` — filled from the template with your answers
   - `docs/vault/index.md`, `log.md`, `.gitignore`
   - `docs/vault/{sources,decisions,concepts,entities,bugs,syntheses,archive,raw}/`
4. Claude offers to commit. You accept.
5. From now on, `/vault:ingest` routes sessions that happen inside
   `billing-service/` to this project vault.

---

## Example 2 — Ingesting yesterday's session

Yesterday's conversation made two architectural decisions and fixed a nasty
bug. You ended the session; today you run:

```
/vault:scan       # (optional — SessionStart hook did it already)
/vault:ingest
```

The flow:

1. Claude reads `~/claude-vault/state/pending.md`, picks the biggest
   unprocessed session.
2. It maps the session's project folder to your local repository. The repo
   has `docs/vault/CLAUDE.md` → **project vault**.
3. It parses the JSONL via `ctx_execute` (keeps the transcript out of the
   LLM context) and sends you a 6-bullet summary:
   - User asked to refactor `InvoiceService` to split out proration logic
   - Decision: keep proration as a pure function in `billing/proration.py`
   - Decision: cache rates in Redis with a 30s TTL
   - Bug: `Invoice.total` was recomputed 3× per request — fixed in commit
     `a1b2c3d`
   - Files touched: `billing/{proration,invoice}.py`, tests, Redis config
   - Open question: should the cache be per-tenant or global?
4. You say "yes, proceed".
5. Claude writes:
   - `sources/sessions/2026-04-22-invoice-refactor.md`
   - `decisions/2026-04-22-proration-as-pure-function.md`
   - `decisions/2026-04-22-redis-rate-cache-30s-ttl.md`
   - `bugs/invoice-total-recomputed-thrice.md`
6. Claude updates `docs/vault/index.md`, appends to `log.md`, appends the
   session ID to `~/claude-vault/state/ingested.txt`, re-runs the scan,
   commits with `docs(vault): ingest #N — invoice-refactor`.

Now tomorrow when someone asks _"why is proration a standalone module?"_,
Claude finds `decisions/2026-04-22-proration-as-pure-function.md` and
answers with citation.

---

## Example 3 — Querying the vault

A week later, you start a new session and type:

> "Have we seen a bug where `Invoice.total` gets recomputed multiple times?"

No slash command needed. The vault skill activates on the phrase "have we
seen a bug":

1. Claude reads `docs/vault/index.md`, scans the Bugs section.
2. Finds `bugs/invoice-total-recomputed-thrice.md` — opens it.
3. Responds with the answer: "Yes, fixed 2026-04-22. Root cause was that
   `total` was calling `proration.compute()` from three different places in
   the same request; the fix cached the result on the Invoice instance.
   Commit: `a1b2c3d`."

If this combined multiple pages in a novel way, Claude would also file the
answer back as `syntheses/2026-04-29-invoice-recompute-analysis.md`.

---

## Example 4 — Vault hygiene (lint)

Every month or so you ask:

> "Lint the vault — anything stale, orphaned, or inconsistent?"

Claude:

1. Walks all pages under `docs/vault/**/*.md`.
2. Builds a link graph. Finds:
   - **2 orphans**: `concepts/dunning-calendar.md`,
     `entities/stripe-webhook-router.md` — referenced nowhere.
   - **1 stale claim**: `decisions/2026-02-10-use-postgres-for-events.md`
     says "we use Postgres for the event log" but
     `sources/sessions/2026-04-18-kafka-migration.md` supersedes it.
   - **1 missing concept**: "prorate" appears in 5 pages but has no
     `concepts/prorate.md`.
3. Writes `syntheses/lint-2026-05-01.md` with the report and concrete
   proposals (link the orphans from `index.md`, mark the Postgres decision
   `status: archived`, create a prorate concept page).
4. Logs it in `log.md`.
5. Waits for you to approve the fixes one-by-one.

---

## Example 5 — Cross-project learning

You hit a bug in `billing-service` that matches a pattern you saw a month ago
in `chat-backend`. The fix was the same. Where does the lesson live?

- Bug itself → `billing-service/docs/vault/bugs/<slug>.md` (project-specific)
- Underlying **pattern** (e.g. "async cache invalidation fires before the new
  value lands") → `~/claude-vault/lessons/<slug>.md` (global)

The project bug page links to the global lesson:

```yaml
# billing-service/docs/vault/bugs/stripe-webhook-replay.md
related: "[[~/claude-vault/lessons/async-cache-invalidation-race.md]]"
```

Next time you encounter the same pattern in a third project, Claude finds the
global lesson first and shortens the debugging loop.
