#!/usr/bin/env bash
# Deploy current-almanac to benkalish.com via Netlify.
# Netlify deploys automatically on git push to origin.
# Run from project root, or after the AI synthesizer completes.

set -e
cd "$(dirname "$0")/.."

echo "Deploy to benkalish.com (Netlify)"
echo "  Repo: $(git remote get-url origin 2>/dev/null || echo 'no remote')"
echo "  This will: git add, commit, push → triggers Netlify deploy"
echo ""
read -r -p "Press Enter to deploy (or Ctrl+C to cancel)..."
echo ""

# Stage changes (seed data, scripts, src, etc.)
git add data/output/seed_hexagrams.json 2>/dev/null || true
git add -A

if git diff --staged --quiet; then
  echo "Nothing to commit. Working tree clean."
  exit 0
fi

git status --short
git commit -m "Deploy: seed hexagrams + app updates"
git push origin "$(git branch --show-current)"

echo ""
echo "Pushed. Netlify will deploy to benkalish.com shortly."
