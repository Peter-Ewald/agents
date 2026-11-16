#!/usr/bin/env bash
# Create (or resume) the git worktree for a wave branch.
#
# Usage: new-wave-worktree.sh REPO_PATH BRANCH
#
# The worktree lives at <main checkout>/.claude/worktrees/<BRANCH>. A new branch starts from
# origin/main (origin/master as fallback; local main when there is no origin). Files matched by
# the main checkout's .worktreeinclude (untracked, e.g. .env) are copied into the worktree.
# It also ensures, once per clone, the merge=union line for docs/history/index.md in
# info/attributes and .claude/worktrees/ in info/exclude. Prints the worktree path last.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 REPO_PATH BRANCH" >&2
  exit 1
fi
repo_path=$1
branch=$2

common=$(git -C "$repo_path" rev-parse --path-format=absolute --git-common-dir)
main=$(dirname "$common")
path="$main/.claude/worktrees/$branch"

if [ -e "$path/.git" ]; then
  echo "$path"
  exit 0
fi

if git -C "$main" remote get-url origin >/dev/null 2>&1; then
  git -C "$main" fetch origin >&2
  if git -C "$main" rev-parse --verify -q origin/main >/dev/null; then
    base=origin/main
  else
    base=origin/master
  fi
else
  base=main
fi

mkdir -p "$(dirname "$path")"
if git -C "$main" show-ref --verify --quiet "refs/heads/$branch"; then
  git -C "$main" worktree add "$path" "$branch" >&2
else
  git -C "$main" worktree add -b "$branch" "$path" "$base" >&2
fi

if [ -f "$main/.worktreeinclude" ]; then
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mkdir -p "$path/$(dirname "$rel")"
    cp -p "$main/$rel" "$path/$rel"
  done < <(git -C "$main" ls-files -o -i --exclude-from="$main/.worktreeinclude")
fi

mkdir -p "$common/info"
ensure_line() {
  if ! grep -qxF "$1" "$2" 2>/dev/null; then
    echo "$1" >> "$2"
  fi
}
# Both files are per clone and shared by all its worktrees, so a team repo gets no commit.
ensure_line 'docs/history/index.md merge=union' "$common/info/attributes"
ensure_line '.claude/worktrees/' "$common/info/exclude"

echo "$path"
