#!/usr/bin/python3
"""SessionStart hook — injects open coordination board entries into the session.

Inside a repo it injects that repo's board. Outside a repo (for example a window opened on a
folder of repos) it injects every repo's board, one block per repo that has open entries. Silent
when nothing is open. Deletes expired notices first; expired holds and old locks are shown as
STALE, never deleted. See `.claude/scripts/board.py` for the board layout.
"""

import json
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
import board

MAX_CHARS = 10_000


def board_block(repo):
    """Delete the repo's expired notices and return its open-entries block, or None if none."""
    board.delete_expired_notices(repo)
    open_entries = [
        e
        for e in board.entries(repo)
        if not (e.kind == "hold" and e.get("status") == "satisfied")
    ]
    if not open_entries:
        return None
    return f"Coordination board for {repo}:\n" + "\n".join(
        board.format_line(e) for e in open_entries
    )


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    cwd = event.get("cwd") or os.getcwd()
    repo = board.repo_name(cwd)
    if repo is None:
        blocks = [board_block(name) for name in board.all_repos()]
    elif os.path.isdir(board.repo_dir(repo)):
        blocks = [board_block(repo)]
    else:
        blocks = []
    blocks = [block for block in blocks if block is not None]
    if not blocks:
        sys.exit(0)

    text = "\n\n".join(blocks)
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
