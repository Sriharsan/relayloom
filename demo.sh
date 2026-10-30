#!/usr/bin/env sh
# Start the Relayloom rehearsal workroom on loopback and open it in a browser.
# Rehearsal mode: invented records, deterministic outputs, no model calls.
# Usage: ./demo.sh [port]   Stop with Ctrl+C.
cd "$(dirname "$0")" || exit 1
PORT="${1:-8800}"
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python
"$PYTHON" -m relayloom --port "$PORT" &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null' INT TERM EXIT
URL="http://127.0.0.1:$PORT"
i=0
until "$PYTHON" -c "import urllib.request,sys; urllib.request.urlopen(sys.argv[1], timeout=1)" "$URL" 2>/dev/null; do
  i=$((i + 1)); [ "$i" -gt 50 ] && { echo "The workroom did not start on $URL"; exit 1; }
  sleep 0.2
done
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
elif command -v open >/dev/null 2>&1; then open "$URL"
else echo "Open $URL in your browser."; fi
wait "$SERVER"
