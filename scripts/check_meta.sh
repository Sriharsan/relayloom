#!/usr/bin/env sh
# Live Meta acceptance check. Refuses unless --i-have-credit is passed.
# Sends ONE billable request when allowed. Never prints the API key.
cd "$(dirname "$0")/.." || exit 1
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python
exec "$PYTHON" scripts/check_meta.py "$@"
