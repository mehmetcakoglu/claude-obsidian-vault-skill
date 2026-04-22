#!/usr/bin/env bash
# Scans ~/.claude/projects/*/*.jsonl for new Claude Code sessions and writes
# a sorted pending queue to ${CLAUDE_VAULT:-$HOME/claude-vault}/state/pending.md.
#
# - Skips files modified in the last 10 minutes (likely live sessions)
# - Skips sessions whose ID is already in state/ingested.txt
# - Extracts first user prompt + first_ts + last_ts for each new session
# - Output is sorted by size descending (biggest first)
#
# Usage: scan-sessions.sh           # writes state/pending.md, prints count
#        scan-sessions.sh --quiet   # same but no stdout (for silent hooks)
#
# Env:   CLAUDE_VAULT               # override default vault location

set -euo pipefail

VAULT="${CLAUDE_VAULT:-$HOME/claude-vault}"
PROJECTS_DIR="$HOME/.claude/projects"
STATE_DIR="$VAULT/state"
INGESTED="$STATE_DIR/ingested.txt"
PENDING="$STATE_DIR/pending.md"
LIVE_THRESHOLD_SEC=600  # 10 minutes

QUIET=0
if [[ "${1:-}" == "--quiet" ]]; then QUIET=1; fi

mkdir -p "$STATE_DIR"
touch "$INGESTED"

if [[ ! -d "$PROJECTS_DIR" ]]; then
  [[ $QUIET -eq 0 ]] && echo "scan-sessions: no projects dir ($PROJECTS_DIR)"
  printf '# Pending sessions\n\n_No projects dir found._\n' > "$PENDING"
  exit 0
fi

NOW_EPOCH=$(date +%s)

# Python helper: reads JSONL, returns metadata as tab-separated line:
#   size<TAB>mtime<TAB>session_id<TAB>project<TAB>first_ts<TAB>last_ts<TAB>first_prompt
python3 - "$PROJECTS_DIR" "$INGESTED" "$NOW_EPOCH" "$LIVE_THRESHOLD_SEC" <<'PY' > "$STATE_DIR/.scan.tsv"
import json, os, sys, glob

projects_dir, ingested_path, now_s, live_s = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])

ingested = set()
if os.path.exists(ingested_path):
    with open(ingested_path) as f:
        for ln in f:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                ingested.add(ln.split()[0])

rows = []
for path in glob.glob(os.path.join(projects_dir, "*", "*.jsonl")):
    try:
        st = os.stat(path)
    except OSError:
        continue
    session_id = os.path.splitext(os.path.basename(path))[0]
    if session_id in ingested:
        continue
    if (now_s - int(st.st_mtime)) < live_s:
        continue  # live session, skip
    project = os.path.basename(os.path.dirname(path))
    first_prompt, first_ts, last_ts = "", "", ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                ts = obj.get("timestamp") or obj.get("createdAt") or ""
                if ts and not first_ts:
                    first_ts = ts
                if ts:
                    last_ts = ts
                if not first_prompt and obj.get("type") == "user":
                    msg = obj.get("message") or {}
                    content = msg.get("content")
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                        text = " ".join(parts)
                    else:
                        text = ""
                    text = text.strip()
                    if text and not text.startswith("<") and "tool_result" not in text[:40].lower():
                        first_prompt = text[:180].replace("\t", " ").replace("\n", " ")
    except OSError:
        continue
    rows.append((int(st.st_size), int(st.st_mtime), session_id, project, first_ts, last_ts, first_prompt))

rows.sort(key=lambda r: r[0], reverse=True)
for r in rows:
    print("\t".join(str(x) for x in r))
PY

COUNT=$(wc -l < "$STATE_DIR/.scan.tsv" | tr -d ' ')

{
  echo "# Pending sessions"
  echo
  echo "_Updated: $(date '+%Y-%m-%d %H:%M:%S')_"
  echo "_Scanned: ${PROJECTS_DIR}_"
  echo "_New sessions awaiting ingest: ${COUNT}_"
  echo
  if [[ "$COUNT" -eq 0 ]]; then
    echo "Queue is empty. No new sessions."
  else
    echo "| # | Size | Last msg | Session | Project | First prompt |"
    echo "|---|------|----------|---------|---------|--------------|"
    awk -F'\t' '{
      n++
      sz=$1; mt=$2; sid=$3; proj=$4; fts=$5; lts=$6; fp=$7
      if (sz > 1048576) szh=sprintf("%.1fM", sz/1048576)
      else if (sz > 1024) szh=sprintf("%.0fK", sz/1024)
      else szh=sz "B"
      lts_d = substr(lts,1,10)
      sid_s = substr(sid,1,8)
      gsub(/\|/, "\\|", fp)
      printf "| %d | %s | %s | `%s` | %s | %s |\n", n, szh, lts_d, sid_s, proj, fp
    }' "$STATE_DIR/.scan.tsv"
  fi
} > "$PENDING"

rm -f "$STATE_DIR/.scan.tsv"

if [[ $QUIET -eq 0 ]]; then
  if [[ "$COUNT" -gt 0 ]]; then
    echo "vault-scan: $COUNT pending session(s) — run /vault:ingest to process the next one."
  else
    echo "vault-scan: queue empty."
  fi
fi
