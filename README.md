# Claude Obsidian Vault Skill

**English** | [Türkçe](README.tr.md)

> Give Claude Code a persistent memory. Every session is archived into a searchable markdown wiki — so past decisions, bugs, and patterns are always in context, never re-explained.

---

## Why bother?

Without a vault, every Claude Code session starts from zero. You re-explain the same architectural decisions, Claude rediscovers bugs you already fixed, and patterns from three months ago are as invisible as if they never happened.

With a vault:

- **Past decisions are in context before your first message** — Claude reads them automatically at session start
- **Bugs stay fixed** — root causes and fixes are recorded and surfaced
- **Knowledge compounds** — every session makes the next one better

---

## Install

Pick one method. Both install the same skill, commands, and hook.

### Option A — Claude Code plugin (recommended)

Type these two commands inside Claude Code:

```
/plugin marketplace add mehmetcakoglu/claude-obsidian-vault-skill
/plugin install vault@claude-obsidian-vault-skill
```

Then **restart your Claude Code session**.

### Option B — Standalone (macOS / Linux)

```bash
git clone https://github.com/mehmetcakoglu/claude-obsidian-vault-skill.git
cd claude-obsidian-vault-skill
./install.sh
```

### Option C — Standalone (Windows PowerShell)

```powershell
git clone https://github.com/mehmetcakoglu/claude-obsidian-vault-skill.git
cd claude-obsidian-vault-skill
.\install.ps1
```

> **Requires Python 3** in PATH on all platforms.

**Custom vault location** — set `CLAUDE_VAULT` before installing:

```bash
CLAUDE_VAULT=/my/path ./install.sh          # macOS / Linux
$env:CLAUDE_VAULT = "D:\my-vault"; .\install.ps1  # Windows
```

After a standalone install, **restart your Claude Code session** for the `SessionStart` hook to activate.

---

## First-time setup (5 minutes)

**1. Verify the install**

In a new Claude Code session, run:
```
/vault:status
```
You should see your vault path, plugin version, and config — all green. If anything is wrong, it tells you what to fix.

**2. Bootstrap a project vault** _(optional but recommended)_

Navigate to a project and run:
```
/vault:init
```
Claude asks 5 quick questions (project name, stack, domain terms) and creates `docs/vault/` with a customized knowledge schema. Do this once per project.

**3. Archive your first session**

```
/vault:scan          # see what's waiting in the queue
/vault:ingest        # archive the top session
```

That's it. From here, the `SessionStart` hook scans automatically every time Claude Code starts. Just run `/vault:ingest` when you're ready to archive.

---

## Commands

| Command | What it does |
|---|---|
| `/vault:help` | Quick-reference card for all commands |
| `/vault:status` | Health check — vault path, version, queue size, config |
| `/vault:init` | Bootstrap `docs/vault/` for the current project |
| `/vault:scan` | Refresh + display the pending-ingest queue |
| `/vault:ingest [id]` | Archive the next (or a specific) pending session |
| `/vault:batch-ingest [N\|all]` | Archive up to N sessions in one run (default 5) |
| `/vault:skip <id>` | Permanently remove a session from the queue |
| `/vault:auto-ingest [on\|off\|status]` | Toggle automatic archiving at session start |
| `/vault:auto-ingest [on\|off] [max N]` | Also set the per-session maximum |
| `/vault:update` | Pull latest version from GitHub and reinstall |

---

## Everyday use

### Archiving sessions

Sessions appear in the queue ~10 minutes after they end. Process them whenever it suits you:

```
/vault:scan              # check the queue
/vault:ingest            # archive one session (biggest first)
/vault:batch-ingest 3    # archive up to 3 at once
/vault:skip a1b2c3d4     # skip a session you don't want archived
```

Each ingested session is routed automatically:
- If the project has `docs/vault/CLAUDE.md` → **project vault**
- Otherwise → **global vault** at `~/Global Claude Vault/`

### Asking questions

Just ask naturally. The `vault` skill activates on phrases like:
- _"what did we decide about X?"_
- _"have we seen this bug before?"_
- _"why did we choose Y?"_

Claude reads the right `index.md`, follows the links, and cites its sources.

### Vault hygiene

```
check the vault
```

Claude scans for orphan pages, stale claims, dead code references, and duplicate entities, then writes a report to `syntheses/lint-YYYY-MM-DD.md`.

---

## Configuration

Settings live in `~/Global Claude Vault/vault-config.json`. The easiest way to change them is via slash commands:

```
/vault:auto-ingest status       # check current state
/vault:auto-ingest on           # enable automatic archiving
/vault:auto-ingest on max 3     # enable, process at most 3 sessions per start
/vault:auto-ingest off          # disable (manual mode, the default)
```

**When to enable auto-ingest:** you trust Claude's judgment on what to archive and want zero maintenance.

**When to leave it off (default):** you want to review each session before it's written, or archiving would interrupt your flow.

---

## How it works

```
~/.claude/projects/*/*.jsonl        (Claude Code session transcripts)
          │
          │  vault-context.py runs at every session start (synchronous)
          │    ├─ scans the pending queue
          │    ├─ auto-creates a project entity if none exists
          │    └─ injects vault index + recent sessions → Claude context
          ▼
   ~/Global Claude Vault/state/pending.md
          │
          │  /vault:ingest (user-triggered, or automatic with auto_ingest=true)
          ▼
    ┌─────┴──────────────────────────────────┐
    │                                        │
    ▼                                        ▼
Global vault                         Project vault
~/Global Claude Vault/               <repo>/docs/vault/
 · cross-project decisions            · domain-specific rules
 · Claude Code patterns               · architectural decisions
 · lessons learned                    · bug/fix history
                                      · entities & concepts
    │                                        │
    └──────────── shared ingested.txt ───────┘
           (a session is never archived twice)
```

The scan and context injection happen automatically. Ingesting (writing pages) is user-triggered by default, because it filters secrets, decides routing, and writes permanent files — that deserves a human in the loop.

---

## Token savings

`/vault:status` shows how many tokens the vault has saved. Here's how that number is calculated — and why it's meaningful.

### How Claude Code sessions actually work

Every time you send a message, Claude Code sends the **entire conversation history up to that point** to the API. A session with 10 prompts sends context cumulatively:

```
Turn 1:   30K tokens sent
Turn 2:   60K tokens sent   ← full history resent
Turn 3:   90K tokens sent
...
Turn 10: 300K tokens sent
─────────────────────────
Total:   ~1.65M tokens sent to the API during the session
```

The session JSONL file on disk stores each message **once** — so a 3 MB file represents ~600K tokens of unique content, not the 1.65M actually sent.

### What "savings" means here

The vault doesn't reduce tokens spent *during* a session. What it eliminates is the **cold-start cost** at the beginning of every *future* session — the tokens that would otherwise be spent re-reading files and re-explaining past decisions.

```
Without vault — future session:
  Read key files to reconstruct context  ~50–600K tokens
  User re-explains past decisions        ~300 tokens
  Claude re-discovers known patterns     (and sometimes gets them wrong)

With vault — future session:
  Inject pre-digested summary            ~800–2,000 tokens
```

### How savings are measured

The JSONL file size is the ground truth for "how much information was in this session." To understand that session's content in a future conversation without a vault, you'd need to read some or all of that transcript. The vault condenses it to a small summary injected at session start.

```
savings per session ≈ (JSONL bytes ÷ 5) − injection tokens
```

_1 token ≈ 5 bytes for JSON transcript data (JSON structure overhead is higher than plain text)._

A 3 MB session contains ~600K tokens of information. The vault injects ~1,200 tokens of its essence. The compression ratio is typically **200–500×**.

---

## Compatibility

| Platform | Status |
|---|---|
| macOS | Full support |
| Linux | Full support |
| Windows (Git Bash / WSL) | Full support via `install.sh` |
| Windows (PowerShell) | Full support via `install.ps1` |
| Claude.ai web / Claude Work | Not supported (no local filesystem) |

---

## Credits

Built on the **LLM-Wiki pattern** (`RAW → WIKI ← SCHEMA`) by
[Selma Kocabıyık](https://github.com/selmakcby) —
[knowledge-pipeline](https://github.com/selmakcby/knowledge-pipeline).

Claude Code packaging (slash commands, auto-scan, hybrid scoping, session registry) by
[Mehmet Çakoğlu](https://github.com/mehmetcakoglu).

See [`docs/ATTRIBUTION.md`](docs/ATTRIBUTION.md) for the full attribution.

---

MIT License — see [`LICENSE`](LICENSE).
