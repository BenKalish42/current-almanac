#!/usr/bin/env bash
# Deploy current-almanac to benkalish.com via PersonalWebsite repo.
# 1. Sync seed data, build app, copy to personal-website/static/Current/
# 2. Commit and push PersonalWebsite → Netlify deploys

set -e
ALMANAC="$(cd "$(dirname "$0")/.." && pwd)"
PERSONAL="$ALMANAC/../../PersonalWebsite/personal-website"
STATIC_CURRENT="$PERSONAL/static/Current"

cd "$ALMANAC"
echo "Deploy Current Almanac to benkalish.com"
echo "  Build from: $ALMANAC"
echo "  Deploy to:  $PERSONAL (PersonalWebsite)"
echo ""
read -r -p "Press Enter to deploy (or Ctrl+C to cancel)..."
echo ""

# 1. Sync AI-generated seed data into src for build
cp "$ALMANAC/data/output/seed_hexagrams.json" "$ALMANAC/src/data/seed_hexagrams.json"
echo "Synced seed_hexagrams.json"

# 2. Build (set VITE_API_URL in .env for production API; see docs/PRODUCTION_API.md)
if [ -z "${VITE_API_URL:-}" ] && [ -f "$ALMANAC/.env" ]; then
  . "$ALMANAC/.env" 2>/dev/null || true
fi
if [ -z "${VITE_API_URL:-}" ]; then
  echo "Note: VITE_API_URL not set. AI features will 404 on live site until backend is configured."
  echo "  See docs/PRODUCTION_API.md for setup."
fi
npm run build
echo "Build complete"

# 3. Copy dist to personal-website
mkdir -p "$STATIC_CURRENT"
rm -rf "$STATIC_CURRENT"/*
cp -r "$ALMANAC/dist"/* "$STATIC_CURRENT"
echo "Copied to $STATIC_CURRENT"

# 4. Commit and push PersonalWebsite
cd "$PERSONAL"
git add static/Current/
if git diff --staged --quiet; then
  echo "No changes in static/Current. Already up to date?"
  exit 0
fi
git status --short static/Current/
git commit -m "Deploy Current Almanac: seed hexagrams + app"
git push origin "$(git branch --show-current)"

echo ""
echo "Pushed. Netlify will deploy to benkalish.com shortly."
