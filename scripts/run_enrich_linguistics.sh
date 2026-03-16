#!/bin/bash
# Run linguistic enrichment with a Python that has SSL (avoids pyenv TLS issues).
# Usage: ./scripts/run_enrich_linguistics.sh

set -e
cd "$(dirname "$0")/.."

if command -v python3.12 &>/dev/null; then
  exec python3.12 scripts/09_enrich_linguistics.py
elif command -v python3 &>/dev/null && python3 -c "import ssl" 2>/dev/null; then
  exec python3 scripts/09_enrich_linguistics.py
else
  echo "Error: Need Python with SSL. Try: python3.12 scripts/09_enrich_linguistics.py"
  exit 1
fi
