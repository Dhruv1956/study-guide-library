#!/usr/bin/env bash
# One-command sync: pulls the latest content from each guide's source file,
# re-applies the Library back-link / safe-area snippet, commits, and pushes.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

python3 scripts/sync_guides.py

if git diff --quiet && git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

changed_files=$(git status --porcelain | awk '{print $2}' | grep '^guides/' | xargs -n1 basename | sed 's/\.html$//' | paste -sd, -)

git add -A
git commit -q -m "Sync guides: ${changed_files:-content update}

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
git push

echo "Synced and pushed."
