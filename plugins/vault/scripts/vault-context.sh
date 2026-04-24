#!/usr/bin/env bash
# vault-context.sh — Unix wrapper; logic lives in vault-context.py (cross-platform)
exec python3 "$(dirname "$0")/vault-context.py" "$@"
