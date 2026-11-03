#!/usr/bin/env bash
# Merge the newest upstream *release tag* into a sync branch cut from $BASE_BRANCH.
#
# Tracks releases rather than upstream's main so half-finished upstream work never reaches HA.
# Outputs (to $GITHUB_OUTPUT, or stdout when run by hand):
#   upstream_tag   newest tag on upstream
#   changed        true when that tag is not yet in $BASE_BRANCH
#   conflict       true when the merge did not apply cleanly (nothing is left behind)
#   conflict_files files with conflicts
#   branch         the sync branch holding the clean merge
set -euo pipefail

UPSTREAM_URL="${UPSTREAM_URL:-https://github.com/kramttocs/ha-blueiris.git}"
BASE_BRANCH="${BASE_BRANCH:-main}"
# Files this fork deliberately does not carry. If upstream edits one, the merge reports a
# modify/delete conflict, which is resolved here by keeping it deleted.
LOCAL_REMOVALS=(.github/workflows/validate.yaml)
out() {
  if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "$1=$2" >> "$GITHUB_OUTPUT"; else echo "$1=$2"; fi
}

if git remote get-url upstream >/dev/null 2>&1; then
  git remote set-url upstream "$UPSTREAM_URL"
else
  git remote add upstream "$UPSTREAM_URL"
fi
# Upstream tags go into their own namespace so they cannot collide with this fork's release tags.
git fetch --quiet --no-tags upstream "+refs/tags/*:refs/upstream-tags/*"

latest=$(git for-each-ref --format='%(refname:strip=2)' refs/upstream-tags | sort -V | tail -1)
if [ -z "$latest" ]; then
  echo "No tags found on $UPSTREAM_URL" >&2
  exit 1
fi
out upstream_tag "$latest"

if git merge-base --is-ancestor "refs/upstream-tags/$latest" "$BASE_BRANCH"; then
  echo "$BASE_BRANCH already contains upstream $latest"
  out changed false
  exit 0
fi

branch="sync/$latest"
git checkout -q -B "$branch" "$BASE_BRANCH"
merged=false
if git merge --no-edit -m "Merge upstream release $latest" "refs/upstream-tags/$latest"; then
  merged=true
else
  for f in "${LOCAL_REMOVALS[@]}"; do
    if git ls-files -u -- "$f" | grep -q .; then git rm -q -- "$f"; fi
  done
  if [ -z "$(git diff --name-only --diff-filter=U)" ] && git commit --no-edit -q; then merged=true; fi
fi
if [ "$merged" = true ]; then
  out changed true
  out conflict false
  out branch "$branch"
else
  files=$(git diff --name-only --diff-filter=U | tr '\n' ' ')
  git merge --abort
  git checkout -q "$BASE_BRANCH"
  git branch -q -D "$branch"
  echo "Merge of upstream $latest conflicts in: $files" >&2
  out changed true
  out conflict true
  out conflict_files "$files"
fi
