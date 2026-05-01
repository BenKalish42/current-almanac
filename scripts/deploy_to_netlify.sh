#!/usr/bin/env bash
#
# One-shot deploy of current-almanac/dist to Netlify.
#
# Usage:
#   NETLIFY_AUTH_TOKEN=<your_token> NETLIFY_SITE_ID=<site_id> ./scripts/deploy_to_netlify.sh
#
# Or, for first-time setup against a new site:
#   NETLIFY_AUTH_TOKEN=<token> ./scripts/deploy_to_netlify.sh --new
#
# Get a personal access token: https://app.netlify.com/user/applications
# Get the site id: Netlify dashboard → Site → Settings → General → Site information.
#
# This script exists because Netlify is hooked to BenKalish42/PersonalWebsite,
# not to current-almanac directly. The recommended long-term path is the
# `.github/workflows/deploy-to-benkalish.yml` GitHub Action — but this is the
# fallback when you want to push a build straight from your dev machine without
# going through that repo at all.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${NETLIFY_AUTH_TOKEN:-}" ]]; then
  echo "ERROR: NETLIFY_AUTH_TOKEN is not set."
  echo "  Get one: https://app.netlify.com/user/applications"
  exit 1
fi

# --- 1. Build (unless --no-build was passed) ---
if [[ "${1:-}" != "--no-build" ]]; then
  echo "→ Building production bundle…"
  if [[ -f data/output/seed_hexagrams.json ]]; then
    cp data/output/seed_hexagrams.json src/data/seed_hexagrams.json
  fi
  npm run build
fi

# --- 2. Deploy ---
NETLIFY_FLAGS=("--dir=dist" "--prod" "--message=current-almanac@$(git rev-parse --short HEAD)")

if [[ "${1:-}" == "--new" ]]; then
  echo "→ Creating a fresh Netlify site and deploying…"
  npx -y netlify@26 deploy "${NETLIFY_FLAGS[@]}"
else
  if [[ -z "${NETLIFY_SITE_ID:-}" ]]; then
    echo "ERROR: NETLIFY_SITE_ID is not set, and --new wasn't passed."
    echo "  Either set NETLIFY_SITE_ID, or rerun with --new to create a new site."
    exit 1
  fi
  echo "→ Deploying to existing Netlify site $NETLIFY_SITE_ID…"
  npx -y netlify@26 deploy --site="$NETLIFY_SITE_ID" "${NETLIFY_FLAGS[@]}"
fi

echo "✓ Deploy complete."
