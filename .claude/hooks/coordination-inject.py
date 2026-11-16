#!/usr/bin/python3
"""SessionStart hook — injects the repo's open coordination board entries into the session.

Silent when the cwd is not in git or the repo has no board folder / no entries. Deletes expired
notices first; expired holds and old locks are shown as STALE, never deleted. See
`.claude/scripts/board.py` for the board layout.
"""

import json
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
import board

MAX_CHARS = 10_000


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    cwd = event.get("cwd") or os.getcwd()
    repo = board.repo_name(cwd)
    if repo is None or not os.path.isdir(board.repo_dir(repo)):
        sys.exit(0)

    board.delete_expired_notices(repo)
    open_entries = [
        e
        for e in board.entries(repo)
        if not (e.kind == "hold" and e.get("status") == "satisfied")
    ]
    if not open_entries:
        sys.exit(0)

    text = f"Coordination board for {repo}:\n" + "\n".join(
        board.format_line(e) for e in open_entries
    )
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n... (truncated; run board.py list for the rest)"
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": text,
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"coordination-inject: {exc}", file=sys.stderr)
        sys.exit(0)
