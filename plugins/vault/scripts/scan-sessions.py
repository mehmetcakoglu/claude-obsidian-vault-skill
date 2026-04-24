#!/usr/bin/env python3
"""
scan-sessions.py — Cross-platform session scanner (macOS / Linux / Windows).

Scans ~/.claude/projects/*/*.jsonl for new Claude Code sessions and writes
a sorted pending queue to <vault>/state/pending.md.

Usage:
    python3 scan-sessions.py           # write pending.md, print count
    python3 scan-sessions.py --quiet   # silent (for hooks)

Env:
    CLAUDE_VAULT        override vault location (default: ~/claude-vault)
    CLAUDE_PLUGIN_ROOT  set by Claude Code plugin system; used for first-run
                        bootstrap when the vault skeleton does not yet exist
"""

import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

LIVE_THRESHOLD_SEC = 600  # skip files modified in last 10 min (live sessions)


# ── paths ─────────────────────────────────────────────────────────────────────

def get_vault() -> Path:
    return Path(os.environ.get("CLAUDE_VAULT", Path.home() / "claude-vault"))


def get_projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


# ── first-run bootstrap ───────────────────────────────────────────────────────

def maybe_bootstrap(vault: Path) -> None:
    """Seed vault from plugin templates on first run (plugin system only)."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        return
    if (vault / "CLAUDE.md").exists():
        return

    tpl = Path(plugin_root) / "templates" / "global-vault"
    if not tpl.is_dir():
        return

    for subdir in [
        "sources/sessions", "sources/prompts", "decisions", "concepts",
        "entities", "lessons", "syntheses", "archive", "raw", "scripts", "state",
    ]:
        (vault / subdir).mkdir(parents=True, exist_ok=True)

    for fname in ("CLAUDE.md", "index.md", "log.md", ".gitignore"):
        dst = vault / fname
        src = tpl / fname
        if not dst.exists() and src.exists():
            shutil.copy(src, dst)


# ── registry ──────────────────────────────────────────────────────────────────

def load_ingested(vault: Path) -> set:
    ingested_file = vault / "state" / "ingested.txt"
    if not ingested_file.exists():
        return set()
    ids: set[str] = set()
    for line in ingested_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.add(line.split()[0])
    return ids


# ── metadata extraction ───────────────────────────────────────────────────────

def extract_metadata(jsonl_path: Path) -> dict:
    """Read first/last timestamps + first user prompt from JSONL."""
    first_ts = last_ts = first_prompt = ""
    try:
        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                ts = obj.get("timestamp", "")
                if ts:
                    if not first_ts:
                        first_ts = ts[:10]
                    last_ts = ts[:10]
                msg = obj.get("message", {})
                if not first_prompt and isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    text = ""
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text += block.get("text", "")
                    text = re.sub(r"<[^>]+>", " ", text).strip()
                    text = re.sub(r"\s+", " ", text)
                    if len(text) > 20:
                        first_prompt = text[:120]
    except OSError:
        pass
    return {"first_ts": first_ts, "last_ts": last_ts, "first_prompt": first_prompt}


# ── size formatting ───────────────────────────────────────────────────────────

def fmt_size(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return f"{n}B"


# ── main ──────────────────────────────────────────────────────────────────────

def scan(quiet: bool = False) -> int:
    vault = get_vault()
    projects_dir = get_projects_dir()

    # First-run bootstrap (plugin system)
    maybe_bootstrap(vault)

    if not vault.exists():
        return 0

    state_dir = vault / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "ingested.txt").touch(exist_ok=True)

    if not projects_dir.exists():
        (state_dir / "pending.md").write_text(
            "# Pending sessions\n\n_No projects dir found._\n", encoding="utf-8"
        )
        return 0

    ingested = load_ingested(vault)
    now = time.time()
    sessions = []

    for jsonl in projects_dir.glob("*/*.jsonl"):
        try:
            mtime = jsonl.stat().st_mtime
            size  = jsonl.stat().st_size
        except OSError:
            continue
        if (now - mtime) < LIVE_THRESHOLD_SEC:
            continue
        session_id = jsonl.stem
        if session_id in ingested:
            continue
        meta = extract_metadata(jsonl)
        sessions.append({
            "session_id": session_id[:8],
            "project":    jsonl.parent.name,
            "size":       size,
            "last_ts":    meta["last_ts"],
            "first_prompt": meta["first_prompt"],
        })

    sessions.sort(key=lambda s: s["size"], reverse=True)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Pending sessions", "",
        f"_Updated: {now_str}_",
        f"_Scanned: {projects_dir}_",
        f"_New sessions awaiting ingest: {len(sessions)}_",
        "",
    ]
    if sessions:
        lines += [
            "| # | Size | Last msg | Session | Project | First prompt |",
            "|---|------|----------|---------|---------|--------------|",
        ]
        for i, s in enumerate(sessions, 1):
            preview = s["first_prompt"][:80].replace("|", "\\|")
            lines.append(
                f"| {i} | {fmt_size(s['size'])} | {s['last_ts']}"
                f" | `{s['session_id']}` | {s['project']} | {preview} |"
            )
    else:
        lines.append("Queue is empty. No new sessions.")

    (state_dir / "pending.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not quiet:
        if sessions:
            print(f"vault-scan: {len(sessions)} pending session(s)"
                  " — run /vault:ingest to process the next one.")
        else:
            print("vault-scan: queue empty.")

    return len(sessions)


if __name__ == "__main__":
    scan(quiet="--quiet" in sys.argv)
