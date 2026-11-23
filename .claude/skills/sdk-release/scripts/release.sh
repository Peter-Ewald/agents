#!/bin/bash
# Releases sdk/<package> at <version>: bump version, relock every project that installs the
# package editable, build, publish, stage the result.
# Assumes it's run from the Semantic Evaluation repo root (where sdk/<package>/ lives)
# and that sdk/<package>/CHANGELOG.md already has a `## [<version>]` entry — the caller
# (sdk-release SKILL.md) checks that before invoking this script.
set -euo pipefail

PACKAGE="${1:?usage: release.sh <package> <version>}"
VERSION="${2:?usage: release.sh <package> <version>}"
PKG_DIR="sdk/$PACKAGE"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$PKG_DIR" ]; then
  echo "No such package directory: $PKG_DIR (run from the Semantic Evaluation repo root)" >&2
  exit 1
fi

if ! grep -q "^## \[$VERSION\]" "$PKG_DIR/CHANGELOG.md"; then
  echo "$PKG_DIR/CHANGELOG.md has no entry for $VERSION yet — add it before releasing." >&2
  exit 1
fi

sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" "$PKG_DIR/pyproject.toml"

# Before publishing, so a project that cannot take the new version stops the release.
LOCKS="$("$SCRIPT_DIR/relock-editable.sh" "$PACKAGE")"

rm -rf "$PKG_DIR/dist"
(
  cd "$PKG_DIR"
  uv sync
  uv build
  # hatch_build.py stages the docs into the wheel; refuse to publish one without them.
  uv run pytest -q -m slow tests/test_packaged_docs.py
  uv publish --index ramtech-pypi "dist/${PACKAGE}-${VERSION}"*
)

STAGED="$PKG_DIR/pyproject.toml
$PKG_DIR/CHANGELOG.md
$PKG_DIR/uv.lock"
if [ -n "$LOCKS" ]; then
  STAGED="$STAGED
$LOCKS"
fi
STAGED="$(printf '%s\n' "$STAGED" | sort -u)"
printf '%s\n' "$STAGED" | while IFS= read -r path; do
  git add "$path"
done
echo "Staged for $PACKAGE $VERSION — commit when ready:"
printf '  %s\n' $STAGED
