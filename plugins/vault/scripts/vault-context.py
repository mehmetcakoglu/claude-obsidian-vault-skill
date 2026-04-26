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
  5. If vault-config.json has auto_ingest=true, instructs Claude to process the
     pending queue automatically before responding to the first user message

Usage (in ~/.claude/settings.json):
    macOS / Linux:
        python3 -c "import pathlib,subprocess,sys; p=pathlib.Path.home()/'claude-vault'/'scripts'/'vault-context.py'; subprocess.run([sys.executable,str(p)]) if p.exists() else None"
    Windows (replace python3 with python if needed):
        python -c "import pathlib,subprocess,sys; p=pathlib.Path.home()/'claude-vault'/'scripts'/'vault-context.py'; subprocess.run([sys.executable,str(p)]) if p.exists() else None"
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path


# ── helpers ───────────────────────────────────────────────────────────────────

def get_vault() -> Path:
    return Path(os.environ.get("CLAUDE_VAULT", Path.home() / "claude-vault"))


def get_project_dir() -> Path:
    raw = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return Path(raw) if raw else Path.cwd()


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


# ── config ────────────────────────────────────────────────────────────────────

def read_config(vault: Path) -> dict:
    cfg_file = vault / "vault-config.json"
    if not cfg_file.exists():
        return {}
    try:
        return json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── pending count ─────────────────────────────────────────────────────────────

def pending_count(vault: Path) -> int:
    pf = vault / "state" / "pending.md"
    if not pf.exists():
        return 0
    return sum(1 for line in pf.read_text(encoding="utf-8").splitlines()
               if re.match(r"^\| [0-9]", line))


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    vault = get_vault()
    if not vault.exists():
        return

    project_dir  = get_project_dir()
    slug         = slugify(project_dir.name)

    run_scan(vault)
    entity_file = ensure_entity(vault, project_dir)

    cfg              = read_config(vault)
    auto_ingest      = bool(cfg.get("auto_ingest", False))
    auto_ingest_max  = int(cfg.get("auto_ingest_max_per_session", 5))

    out: list[str] = ["<vault-context>", ""]

    # Index
    index = vault / "index.md"
    if index.exists():
        out += ["## Vault İçerik Haritası", "", index.read_text(encoding="utf-8").rstrip(), ""]

    # Project entity
    if entity_file and entity_file.exists():
        out += [f"## Aktif Proje: {project_dir.name}", "",
                entity_file.read_text(encoding="utf-8").rstrip(), ""]

    # Recent sessions
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

    # Instruction
    out += [
        "---",
        "**VAULT KULLANIM TALİMATI:** Kodlama görevine başlamadan önce yukarıdaki",
        "haritadan ilgili `decisions/` ve `lessons/` sayfalarını `Read` ile yükle.",
        "Geçmiş kararlar ve dersler yeniden keşfedilmesi gereken bilgiler değildir.",
        "",
        "</vault-context>",
    ]

    print("\n".join(out))


if __name__ == "__main__":
    main()
