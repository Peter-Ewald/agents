#!/bin/bash
# Relocks every project that installs sdk/<package> editable, after its version was bumped.
# Assumes it's run from the Semantic Evaluation repo root (where sdk/<package>/ lives).
# Prints the relocked uv.lock paths (relative to the repo root) on stdout, one per line;
# progress and uv output go to stderr.
set -euo pipefail

PACKAGE="${1:?usage: relock-editable.sh <package>}"
PYPROJECT="sdk/$PACKAGE/pyproject.toml"
DIST="${PACKAGE//_/-}"

if [ ! -f "$PYPROJECT" ]; then
  echo "No such file: $PYPROJECT (run from the Semantic Evaluation repo root)" >&2
  exit 1
fi

VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' "$PYPROJECT" | head -n 1)"
if [ -z "$VERSION" ]; then
  echo "No version = \"...\" line in $PYPROJECT" >&2
  exit 1
fi

# Reads the lock's [[package]] entry for $DIST. Usage: lock_info <lock> <mode>
#   editable: prints "yes" when the entry has an editable source, nothing otherwise
#   version:  prints the version the entry records
lock_info() {
  python3 - "$1" "$2" "$DIST" <<'PY'
import sys, tomllib

path, mode, dist = sys.argv[1:4]
with open(path, "rb") as f:
    data = tomllib.load(f)
for pkg in data.get("package", []):
    if pkg.get("name") != dist:
        continue
    if mode == "editable":
        if "editable" in pkg.get("source", {}):
            print("yes")
            break
    else:
        print(pkg.get("version", ""))
        break
PY
}

git ls-files | while IFS= read -r lock; do
  case "$lock" in
    uv.lock | */uv.lock) ;;
    *) continue ;;
  esac
  if [ "$(lock_info "$lock" editable)" != "yes" ]; then
    continue
  fi
  dir="$(dirname "$lock")"
  echo "Relocking $dir for $DIST $VERSION" >&2
  if ! uv --directory "$dir" lock >&2; then
    echo "relock failed in $dir (uv lock exited non-zero)" >&2
    exit 1
  fi
  recorded="$(lock_info "$lock" version)"
  if [ "$recorded" != "$VERSION" ]; then
    echo "relock failed in $dir: $lock records $DIST ${recorded:-<none>}, expected $VERSION" >&2
    exit 1
  fi
  echo "$lock"
done
