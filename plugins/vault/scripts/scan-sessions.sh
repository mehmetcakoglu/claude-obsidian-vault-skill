#!/usr/bin/env bash
# scan-sessions.sh — Unix wrapper; logic lives in scan-sessions.py (cross-platform)
exec python3 "$(dirname "$0")/scan-sessions.py" "$@"
