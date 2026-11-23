#!/usr/bin/python3
"""SessionStart hook — injects open coordination board entries into the session.

Inside a repo it injects that repo's board. Outside a repo (for example a window opened on a
folder of repos) it injects every repo's board, one block per repo that has open entries. Silent
when nothing is open. Nothing is deleted: expired notices, expired holds and old locks are
shown as STALE. When a shown entry is a request or notice, a final line points to the repo's
inbox rule in instructions.md. See `.claude/scripts/board.py` for the board layout.
"""

import json
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
import board

MAX_CHARS = 10_000
INBOX_POINTER = (
    "Requests and notices are the repo's inbox: raise them per "
    "instructions.md § \"A repo's inbox\" once the session's work concerns that repo."
)


def open_entries(repo):
    return [
        e
        for e in board.entries(repo)
        if not (e.kind == "hold" and e.get("status") == "satisfied")
    ]


def board_block(repo, shown):
    """Return the repo's open-entries block, or None if none."""
    if not shown:
        return None
    return f"Coordination board for {repo}:\n" + "\n".join(
        board.format_line(e) for e in shown
    )


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    cwd = event.get("cwd") or os.getcwd()
    repo = board.repo_name(cwd)
    if repo is None:
        repos = board.all_repos()
    elif os.path.isdir(board.repo_dir(repo)):
        repos = [repo]
    else:
        repos = []
    shown = {name: open_entries(name) for name in repos}
    blocks = [board_block(name, shown[name]) for name in repos]
    blocks = [block for block in blocks if block is not None]
    if not blocks:
        sys.exit(0)
    has_inbox = any(
        e.kind in board.INBOX_KINDS for entries in shown.values() for e in entries
    )

    text = "\n\n".join(blocks)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n... (truncated; run board.py list for the rest)"
    if has_inbox:
        text += "\n\n" + INBOX_POINTER
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
