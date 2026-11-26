#!/bin/bash
# Relocks every project that installs sdk/<package> editable, after its version was bumped.
# First checks that each such project's declared requirements on the package admit the new version
# (uv ignores a range on an editable path source); if any excludes it, stops before any relock.
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

HERE="$(cd "$(dirname "$0")" && pwd)"

# Directories of the git-tracked uv.lock files that record $DIST with an editable source.
editable_dirs=()
while IFS= read -r lock; do
  case "$lock" in
    uv.lock | */uv.lock) ;;
    *) continue ;;
  esac
  if [ "$(lock_info "$lock" editable)" = "yes" ]; then
    editable_dirs+=("$(dirname "$lock")")
  fi
done < <(git ls-files)

failures=()
for dir in ${editable_dirs[@]+"${editable_dirs[@]}"}; do
  if ! messages="$(python3 "$HERE/declared_range.py" "$dir/pyproject.toml" "$DIST" "$VERSION" 2>&1)"; then
    while IFS= read -r line; do
      failures+=("range check failed in $dir: $line")
    done <<<"$messages"
  fi
done
if [ "${#failures[@]}" -gt 0 ]; then
  printf '%s\n' "${failures[@]}" >&2
  exit 1
fi

for dir in ${editable_dirs[@]+"${editable_dirs[@]}"}; do
  lock="$dir/uv.lock"
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
