#!/bin/bash
# Releases sdk/<package> at <version>: bump version, build, publish, stage the result.
# Assumes it's run from the Task Force Evaluation repo root (where sdk/<package>/ lives)
# and that sdk/<package>/CHANGELOG.md already has a `## [<version>]` entry — the caller
# (sdk-release SKILL.md) checks that before invoking this script.
set -euo pipefail

PACKAGE="${1:?usage: release.sh <package> <version>}"
VERSION="${2:?usage: release.sh <package> <version>}"
PKG_DIR="sdk/$PACKAGE"

if [ ! -d "$PKG_DIR" ]; then
  echo "No such package directory: $PKG_DIR (run from the Task Force Evaluation repo root)" >&2
  exit 1
fi

if ! grep -q "^## \[$VERSION\]" "$PKG_DIR/CHANGELOG.md"; then
  echo "$PKG_DIR/CHANGELOG.md has no entry for $VERSION yet — add it before releasing." >&2
  exit 1
fi

sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" "$PKG_DIR/pyproject.toml"

rm -rf "$PKG_DIR/dist"
(
  cd "$PKG_DIR"
  uv sync
  uv build
  uv publish --index ramtech-pypi "dist/${PACKAGE}-${VERSION}"*
)

git add "$PKG_DIR/pyproject.toml" "$PKG_DIR/CHANGELOG.md" "$PKG_DIR/uv.lock"
echo "Staged pyproject.toml, CHANGELOG.md, and uv.lock for $PACKAGE $VERSION — commit when ready."
