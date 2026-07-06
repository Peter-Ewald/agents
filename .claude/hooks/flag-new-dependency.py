#!/usr/bin/python3
"""PreToolUse hook (matcher: Edit|Write) — blocks adding a new third-party dependency to
pyproject.toml / package.json / requirements*.txt without it being flagged in chat first,
per instructions.md's "No new dependencies without flagging" rule. A version-only change
to an existing dependency does not block.

Heuristic, not a full parser: regex-based for pyproject.toml (covers the common
[project] dependencies = [...] shape) and requirements*.txt; real JSON parsing for
package.json. Good enough to catch the common case; a missed edge case just means the
addition goes unflagged, same as before this hook existed.
"""
import json
import re
import sys
from pathlib import Path


def extract_name(spec: str) -> str:
    spec = spec.strip()
    m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", spec)
    return (m.group(0) if m else spec).lower()


def pyproject_deps(content: str) -> set:
    names = set()
    m = re.search(r"(?ms)^dependencies\s*=\s*\[(.*?)\]", content)
    if m:
        for dq, sq in re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1)):
            names.add(extract_name(dq or sq))
    return names


def package_json_deps(content: str) -> set:
    names = set()
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return names
    for key in ("dependencies", "devDependencies"):
        names.update((data.get(key) or {}).keys())
    return {n.lower() for n in names}


def requirements_deps(content: str) -> set:
    names = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        names.add(extract_name(line))
    return names


def deps_for(file_path: str, content: str) -> set:
    name = Path(file_path).name
    if name == "pyproject.toml":
        return pyproject_deps(content)
    if name == "package.json":
        return package_json_deps(content)
    if name.startswith("requirements") and name.endswith(".txt"):
        return requirements_deps(content)
    return set()


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("tool_name") not in ("Edit", "Write"):
        sys.exit(0)

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    name = Path(file_path).name
    if not (
        name == "pyproject.toml"
        or name == "package.json"
        or (name.startswith("requirements") and name.endswith(".txt"))
    ):
        sys.exit(0)

    try:
        old_content = Path(file_path).read_text()
    except (FileNotFoundError, OSError):
        old_content = ""

    if event["tool_name"] == "Write":
        new_content = tool_input.get("content", "")
    else:
        new_content = old_content.replace(
            tool_input.get("old_string", ""), tool_input.get("new_string", ""), 1
        )

    added = deps_for(file_path, new_content) - deps_for(file_path, old_content)
    if added:
        names = ", ".join(sorted(added))
        print(
            f"New dependency detected in {file_path}: {names}. Flag this addition in "
            "chat with the reason and an alternatives note before proceeding, per "
            "instructions.md's \"No new dependencies without flagging\" rule.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
