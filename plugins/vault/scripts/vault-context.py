#!/usr/bin/env python3
"""
vault-context.py — Cross-platform vault context injector (macOS / Linux / Windows).

Called synchronously by the Claude Code SessionStart hook.
stdout is captured and injected as a <system-reminder> into the session context.

What it does:
  1. Runs scan-sessions.py to refresh pending.md
  2. Auto-creates a project entity if none exists for the current project
  3. Outputs: index.md + project entity + recent project sessions + pending count
  4. Appends an explicit instruction for Claude to read relevant vault pages
  5. Logs injected token estimate to {vault}/state/token-log.txt
  6. If vault-config.json has auto_ingest=true, instructs Claude to process the
     pending queue automatically before responding to the first user message

Usage (in ~/.claude/settings.json):
    macOS / Linux:
        python3 -c "import pathlib,subprocess,sys,os; p=pathlib.Path(os.environ.get('CLAUDE_VAULT', str(pathlib.Path.home()/'Global Claude Vault')))/'scripts'/'vault-context.py'; subprocess.run([sys.executable,str(p)]) if p.exists() else None"
    Windows (replace python3 with python if needed):
        python -c "import pathlib,subprocess,sys,os; p=pathlib.Path(os.environ.get('CLAUDE_VAULT', str(pathlib.Path.home()/'Global Claude Vault')))/'scripts'/'vault-context.py'; subprocess.run([sys.executable,str(p)]) if p.exists() else None"

Environment variables:
    CLAUDE_VAULT        Override global vault directory (default: ~/Global Claude Vault)
    CLAUDE_PROJECT_DIR  Override project directory (default: cwd)
"""

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

__version__ = "0.3.4"
_UPDATE_URL = (
    "https://raw.githubusercontent.com/mehmetcakoglu/"
    "claude-obsidian-vault-skill/main/plugins/vault/.claude-plugin/plugin.json"
)

# Maximum characters to inject per index.md to avoid bloating context window.
_MAX_INDEX_CHARS = 6000
# Maximum characters for a single entity file injection.
_MAX_ENTITY_CHARS = 3000


# ── helpers ───────────────────────────────────────────────────────────────────

def get_vault() -> Path:
    return Path(os.environ.get("CLAUDE_VAULT", Path.home() / "Global Claude Vault"))


def get_project_dir() -> Path:
    raw = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return Path(raw) if raw else Path.cwd()


def vault_display_path(vault: Path) -> str:
    """Return ~/... form when vault is inside home dir, else absolute."""
    try:
        return "~/" + vault.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(vault)


def slugify(name: str) -> str:
    s = name.lower()
    s = s.replace(" ", "-").replace("_", "-")
    s = s.translate(str.maketrans("ışğüöçİŞĞÜÖÇ", "isgüocISGUOC"))
    return re.sub(r"[^a-z0-9-]", "", s)


def detect_lang(project_dir: Path) -> str:
    checks = [
        ("manage.py",        "Django/Python"),
        ("pyproject.toml",   "Python"),
        ("requirements.txt", "Python"),
        ("go.mod",           "Go"),
        ("Cargo.toml",       "Rust"),
        ("pom.xml",          "Java/Maven"),
        ("package.json",     "Node.js/JavaScript"),
    ]
    for marker, lang in checks:
        if (project_dir / marker).exists():
            return lang
    return "unknown"


def frontmatter_field(path: Path, field: str) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[:20]:
            if line.startswith(f"{field}:"):
                return line.split(":", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def truncate(text: str, max_chars: int, label: str = "") -> str:
    """Truncate text with a clear marker so Claude knows content was cut."""
    if len(text) <= max_chars:
        return text
    suffix = f"\n\n… _(içerik kesildi — {label} {len(text)} karakter, limit {max_chars})_"
    return text[:max_chars] + suffix


# ── project vault detection ───────────────────────────────────────────────────

def get_project_vault(project_dir: Path) -> Path | None:
    """Return docs/vault/ if it has a CLAUDE.md (project vault present)."""
    candidate = project_dir / "docs" / "vault"
    if (candidate / "CLAUDE.md").exists():
        return candidate
    return None


# ── scan ──────────────────────────────────────────────────────────────────────

def run_scan(vault: Path) -> None:
    scanner = vault / "scripts" / "scan-sessions.py"
    if scanner.exists():
        import subprocess
        subprocess.run(
            [sys.executable, str(scanner), "--quiet"],
            capture_output=True,
        )


# ── entity auto-create ────────────────────────────────────────────────────────

def ensure_entity(vault: Path, project_dir: Path) -> Path | None:
    home = Path.home()
    if project_dir == home or str(project_dir) in ("/", str(home)):
        return None
    # Skip global auto-entity if a project vault exists — it manages its own entities
    if get_project_vault(project_dir):
        return None

    slug         = slugify(project_dir.name)
    entity_file  = vault / "entities" / f"{slug}.md"

    if entity_file.exists():
        return entity_file

    lang  = detect_lang(project_dir)
    today = date.today().isoformat()

    entity_file.parent.mkdir(parents=True, exist_ok=True)
    entity_file.write_text(
        f"---\ntitle: {project_dir.name}\n"
        f"tags: [project, entity, auto-generated]\n"
        f'source: "auto-generated"\ndate: {today}\nstatus: active\n---\n\n'
        f"# {project_dir.name}\n\n"
        f"**Proje dizini:** `{project_dir}`  \n"
        f"**Dil/Framework:** {lang}  \n"
        f"**Oluşturuldu:** {today} (vault-context.py)\n\n"
        f"## Açıklama\n\n_Otomatik oluşturuldu. Bilgi biriktikçe güncellenecek._\n\n"
        f"## Kararlar\n\n_Henüz kayıt yok._\n\n"
        f"## Dersler\n\n_Henüz kayıt yok._\n\n"
        f"## Related\n\n- [[sources/sessions/]]\n",
        encoding="utf-8",
    )

    # Insert into index.md under ### Projeler
    index = vault / "index.md"
    if index.exists():
        text  = index.read_text(encoding="utf-8")
        entry = (f"- [[entities/{slug}.md]] — "
                 f"{project_dir.name} ({lang}, auto-entity {today})\n")
        if slug not in text:
            text = re.sub(r"(### Projeler\n)", r"\1" + entry, text, count=1)
            index.write_text(text, encoding="utf-8")

    return entity_file


# ── recent sessions ───────────────────────────────────────────────────────────

def recent_sessions(vault: Path, project_name: str, slug: str, limit: int = 3) -> list[dict]:
    sessions_dir = vault / "sources" / "sessions"
    if not sessions_dir.exists():
        return []
    results: list[dict] = []
    for md in sorted(sessions_dir.glob("*.md"), reverse=True):
        try:
            content = md.read_text(encoding="utf-8")
        except OSError:
            continue
        if project_name.lower() in content.lower() or slug in content.lower():
            results.append({
                "date":  frontmatter_field(md, "date"),
                "title": frontmatter_field(md, "title") or md.stem,
                "rel":   md.relative_to(vault).as_posix(),
            })
            if len(results) >= limit:
                break
    return results


def recent_project_vault_sessions(project_vault: Path, limit: int = 3) -> list[dict]:
    """Return the most recent sessions from the project vault."""
    sessions_dir = project_vault / "sources" / "sessions"
    if not sessions_dir.exists():
        return []
    results: list[dict] = []
    for md in sorted(sessions_dir.glob("*.md"), reverse=True):
        try:
            title = frontmatter_field(md, "title") or md.stem
            dt    = frontmatter_field(md, "date")
        except OSError:
            continue
        results.append({"date": dt, "title": title, "path": str(md)})
        if len(results) >= limit:
            break
    return results


# ── config ────────────────────────────────────────────────────────────────────

def read_config(vault: Path) -> dict:
    cfg_file = vault / "vault-config.json"
    if not cfg_file.exists():
        return {}
    try:
        return json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── update check ─────────────────────────────────────────────────────────────

def check_for_update(vault: Path) -> str | None:
    """Fetch latest version from GitHub once per day. Returns a notice or None."""
    stamp = vault / "state" / "update-check.txt"
    today = date.today().isoformat()
    try:
        if stamp.exists() and stamp.read_text(encoding="utf-8").strip() == today:
            return None
    except OSError:
        pass

    try:
        import urllib.request
        with urllib.request.urlopen(_UPDATE_URL, timeout=2) as resp:
            remote = json.loads(resp.read().decode()).get("version", "")
        stamp.write_text(today, encoding="utf-8")
    except Exception:
        return None

    if remote and remote != __version__:
        return (
            f"⚠️  vault plugin update available: v{__version__} → v{remote}. "
            f"Run `./install.sh` from the repo (or `git pull && ./install.sh`) to update."
        )
    return None


# ── pending count ─────────────────────────────────────────────────────────────

def pending_count(vault: Path) -> int:
    pf = vault / "state" / "pending.md"
    if not pf.exists():
        return 0
    return sum(1 for line in pf.read_text(encoding="utf-8").splitlines()
               if re.match(r"^\| [0-9]", line))


# ── token logging ─────────────────────────────────────────────────────────────

def log_token_usage(vault: Path, char_count: int) -> None:
    """
    Append a one-line entry to {vault}/state/token-log.txt.
    Estimate: 1 token ≈ 4 characters (conservative for mixed TR/EN text).
    """
    token_estimate = char_count // 4
    log_file = vault / "state" / "token-log.txt"
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        project = os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd().name))
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"{timestamp}\t{char_count:>7} chars\t~{token_estimate:>5} tokens"
                f"\t{Path(project).name}\n"
            )
    except OSError:
        pass  # Never crash on logging failure


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    vault = get_vault()
    if not vault.exists():
        return

    project_dir   = get_project_dir()
    slug          = slugify(project_dir.name)
    project_vault = get_project_vault(project_dir)
    vault_disp    = vault_display_path(vault)

    run_scan(vault)
    entity_file = ensure_entity(vault, project_dir)

    cfg              = read_config(vault)
    auto_ingest      = bool(cfg.get("auto_ingest", False))
    auto_ingest_max  = int(cfg.get("auto_ingest_max_per_session", 5))

    out: list[str] = ["<vault-context>", ""]

    # ── Project vault (docs/<vault-name>/) — injected first when present ─────
    if project_vault:
        pv_index = project_vault / "index.md"
        if pv_index.exists():
            pv_index_text = truncate(
                pv_index.read_text(encoding="utf-8").rstrip(),
                _MAX_INDEX_CHARS,
                label="proje vault index",
            )
            out += [
                f"## Proje Vault İçerik Haritası ({project_dir.name})",
                "",
                pv_index_text,
                "",
            ]
        pv_sessions = recent_project_vault_sessions(project_vault)
        if pv_sessions:
            out += [f"## {project_dir.name} — Son Proje Sessionları", ""]
            for s in pv_sessions:
                out.append(f"- {s['date']}: {s['title']}  →  `{s['path']}`")
            out.append("")

    # ── Global vault ─────────────────────────────────────────────────────────
    index = vault / "index.md"
    if index.exists():
        global_index_text = truncate(
            index.read_text(encoding="utf-8").rstrip(),
            _MAX_INDEX_CHARS,
            label="global vault index",
        )
        out += ["## Global Vault İçerik Haritası", "", global_index_text, ""]

    # Project entity (global vault, only when no project vault)
    if entity_file and entity_file.exists():
        entity_text = truncate(
            entity_file.read_text(encoding="utf-8").rstrip(),
            _MAX_ENTITY_CHARS,
            label="entity",
        )
        out += [f"## Aktif Proje: {project_dir.name}", "", entity_text, ""]

    # Recent sessions in global vault (only when no project vault)
    if not project_vault:
        sessions = recent_sessions(vault, project_dir.name, slug)
        if sessions:
            out += ["## Bu Projeye Ait Son Sessionlar", ""]
            for s in sessions:
                out.append(f"- {s['date']}: {s['title']}  →  [[{s['rel']}]]")
            out.append("")

    # Pending ingest
    n = pending_count(vault)
    if n > 0:
        if auto_ingest:
            out += [
                "## Bekleyen Ingest — ⚡ OTOMATİK MOD",
                "",
                f"**auto_ingest=true**: {n} session ingest kuyruğunda.",
                f"Kullanıcının ilk mesajına geçmeden önce `/vault:ingest` komutunu en fazla "
                f"{auto_ingest_max} kez çalıştır (her seferinde 1 session işlenir).",
                "Kuyruk boşaldığında veya limite ulaşıldığında normal konuşmaya geç.",
                "",
            ]
        else:
            out += [
                "## Bekleyen Ingest",
                "",
                f"{n} session ingest bekliyor → `/vault:ingest` ile işleyebilirsin.",
                "",
            ]

    # Update check (once per day, silent on network failure)
    update_notice = check_for_update(vault)
    if update_notice:
        out += [update_notice, ""]

    # Instruction
    if project_vault:
        pv_disp = vault_display_path(project_vault)
        out += [
            "---",
            "**VAULT KULLANIM TALİMATI:** Kodlama görevine başlamadan önce:",
            f"1. Proje vault'undan (`{pv_disp}`) ilgili `decisions/` ve `bugs/` sayfalarını `Read` ile yükle.",
            f"2. Global vault'tan (`{vault_disp}/`) ilgili `decisions/` ve `lessons/` sayfalarını yükle.",
            "Geçmiş kararlar ve dersler yeniden keşfedilmesi gereken bilgiler değildir.",
            "",
            "</vault-context>",
        ]
    else:
        out += [
            "---",
            "**VAULT KULLANIM TALİMATI:** Kodlama görevine başlamadan önce yukarıdaki",
            f"haritadan (`{vault_disp}/`) ilgili `decisions/` ve `lessons/` sayfalarını `Read` ile yükle.",
            "Geçmiş kararlar ve dersler yeniden keşfedilmesi gereken bilgiler değildir.",
            "",
            "</vault-context>",
        ]

    output_text = "\n".join(out)
    print(output_text)
    log_token_usage(vault, len(output_text))


if __name__ == "__main__":
    main()
