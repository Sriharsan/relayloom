#!/usr/bin/env sh
# Rehearsal demo check: synthetic records, deterministic outputs, no model calls.
cd "$(dirname "$0")/.." || exit 1
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python
exec "$PYTHON" scripts/check_demo.py "$@"
