#!/usr/bin/python3
"""PostToolUse hook (matcher: Edit|Write) — lints a just-edited Python file with ruff and
blocks only if a violation falls on a line the edit actually touched. Pre-existing
violations elsewhere in the file are reported but never block, since blocking on debt the
edit didn't introduce would be disruptive across repos with varying lint history.

Fails open (never blocks) if git or ruff aren't available, or anything else goes wrong —
this hook should never be the reason an unrelated repo/workflow breaks.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def changed_line_ranges(file_path: str, cwd: str):
    """Returns a set of changed 1-indexed line numbers, or None if undeterminable
    (caller should then skip blocking entirely rather than guess)."""
    try:
        status = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain", "--", file_path],
            capture_output=True, text=True, timeout=10,
        )
        if status.returncode != 0:
            return None
        if status.stdout.strip().startswith("??"):
            # Untracked file: every line is "changed" (no baseline to compare against).
            with open(file_path) as f:
                return set(range(1, sum(1 for _ in f) + 1))

        diff = subprocess.run(
            ["git", "-C", cwd, "diff", "-U0", "--", file_path],
            capture_output=True, text=True, timeout=10,
        )
        if diff.returncode != 0:
            return None
        lines = set()
        for line in diff.stdout.splitlines():
            m = HUNK_RE.match(line)
            if not m:
                continue
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count == 0:
                # Pure deletion at this hunk — nothing added/changed on the new-file side.
                continue
            lines.update(range(start, start + count))
        return lines
    except Exception:
        return None


UVX = str(Path.home() / ".local/bin/uvx")


def ruff_violations(file_path: str):
    try:
        result = subprocess.run(
            [UVX, "ruff", "check", "--output-format=json", file_path],
            capture_output=True, text=True, timeout=30,
        )
        if not result.stdout.strip():
            return []
        return json.loads(result.stdout)
    except Exception:
        return None


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("tool_name") not in ("Edit", "Write"):
        sys.exit(0)

    file_path = event.get("tool_input", {}).get("file_path", "")
    if not file_path.endswith(".py"):
        sys.exit(0)

    cwd = event.get("cwd", str(Path(file_path).parent))

    changed = changed_line_ranges(file_path, cwd)
    violations = ruff_violations(file_path)
    if violations is None:
        sys.exit(0)  # ruff unavailable or errored — fail open

    if changed is None:
        # No git baseline available — report only, never block.
        if violations:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"ruff found {len(violations)} pre-existing issue(s) in {file_path} "
                        "(no git baseline available to check which lines this edit touched)."
                    ),
                }
            }))
        sys.exit(0)

    blocking = [v for v in violations if v.get("location", {}).get("row") in changed]
    if blocking:
        lines = ", ".join(str(v["location"]["row"]) for v in blocking)
        codes = ", ".join(sorted({v.get("code", "?") for v in blocking}))
        print(
            f"ruff found {len(blocking)} violation(s) on lines this edit touched "
            f"(lines {lines}; codes: {codes}) in {file_path}. Fix these before continuing.",
            file=sys.stderr,
        )
        sys.exit(2)

    if violations:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"ruff found {len(violations)} pre-existing issue(s) elsewhere in "
                    f"{file_path}, none on lines this edit touched — not blocking."
                ),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
