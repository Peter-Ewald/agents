#!/usr/bin/python3
"""PreToolUse hook (matcher: Bash) — blocks `git commit` if a staged pyproject.toml
version bump doesn't have a matching staged CHANGELOG.md update in the same package
directory. Changelog-before-commit ordering, per instructions.md's release conventions.
"""
import json
import os
import re
import subprocess
import sys


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("tool_name") != "Bash":
        sys.exit(0)

    command = event.get("tool_input", {}).get("command", "")
    if not re.search(r"(^|[;&|]\s*)git\s+commit\b", command):
        sys.exit(0)

    cwd = event.get("cwd", ".")
    try:
        staged = subprocess.run(
            ["git", "-C", cwd, "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=10,
        ).stdout.splitlines()
    except Exception:
        sys.exit(0)  # fail open — can't determine staged files

    staged_set = set(staged)
    problems = []
    for f in staged:
        if not f.endswith("pyproject.toml"):
            continue
        try:
            diff = subprocess.run(
                ["git", "-C", cwd, "diff", "--cached", "-U0", "--", f],
                capture_output=True, text=True, timeout=10,
            ).stdout
        except Exception:
            continue
        if re.search(r"^\+\s*version\s*=", diff, re.MULTILINE):
            changelog = os.path.join(os.path.dirname(f), "CHANGELOG.md")
            if changelog not in staged_set:
                problems.append((f, changelog))

    if problems:
        lines = ["Version bump staged without a matching CHANGELOG.md update:"]
        for f, changelog in problems:
            lines.append(f"  {f} bumped, but {changelog} is not staged")
        lines.append("Update the changelog first, then stage it alongside the version bump.")
        print("\n".join(lines), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
