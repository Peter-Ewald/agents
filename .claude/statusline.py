#!/usr/bin/python3
"""Statusline script. Prints up to five parts, joined by "  |  ":

- the current wave and phase, if the `wave` skill has written one for this session;
- the blocked plans on the coordination board, in every session, so a wave waiting for the
  user's answer stays visible wherever the user is working: ``⚠ 2 blocked: Repo/wave-m6, …``;
- the open requests and notices (the inbox) per repo, in every session: ``inbox: agents 2, Checkmate 1``;
- the board entries that cannot be read, in every session, the first one named and the rest
  counted: ``⚠ board unreadable: agents/wave-m6, +2``. The other board parts skip such an entry;
- the active repos whose local `main` is behind `origin/main`, in every session: ``main behind: agents 3, Checkmate 1``.

Prints nothing when none applies.

The wave-phase file lives at /tmp/claude-wave-phase-<session_id> — a fixed path derived
only from the session ID, since this script and the `wave` skill run as separate
processes that don't share any other state. The board is read through `scripts/board.py`.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "scripts"))

SHOWN_BLOCKED = 2


def phase(event):
    session_id = event.get("session_id")
    if not session_id:
        return ""
    phase_file = Path(f"/tmp/claude-wave-phase-{session_id}")
    return phase_file.read_text().strip() if phase_file.exists() else ""


def blocked():
    try:
        import board

        names = [
            f"{entry.repo}/{entry.name}"
            for repo in board.all_repos()
            for entry in board.entries(repo)
            if entry.kind == "plan" and entry.get("status") == "blocked"
        ]
    except Exception:  # noqa: BLE001 — a broken entry must never break the statusline
        return ""
    if not names:
        return ""
    more = f", +{len(names) - SHOWN_BLOCKED}" if len(names) > SHOWN_BLOCKED else ""
    return f"⚠ {len(names)} blocked: {', '.join(names[:SHOWN_BLOCKED])}{more}"


def inbox():
    try:
        import board

        counts = [(repo, len(board.inbox_entries(repo))) for repo in board.all_repos()]
    except Exception:  # noqa: BLE001 — a broken entry must never break the statusline
        return ""
    counts = [(repo, n) for repo, n in counts if n]
    if not counts:
        return ""
    return "inbox: " + ", ".join(f"{repo} {n}" for repo, n in counts)


def unreadable():
    try:
        import board

        refs = [
            item.ref for repo in board.all_repos() for item in board.read_board(repo)[1]
        ]
    except Exception:  # noqa: BLE001 — a broken entry must never break the statusline
        return ""
    if not refs:
        return ""
    more = f", +{len(refs) - 1}" if len(refs) > 1 else ""
    return f"⚠ board unreadable: {refs[0]}{more}"


def main_behind():
    try:
        import sync_main

        counts = [
            (os.path.basename(path), sync_main.commits_behind_origin(path))
            for path in sync_main.active_repo_paths()
        ]
    except Exception:  # noqa: BLE001 — a broken repo must never break the statusline
        return ""
    counts = [(name, n) for name, n in counts if n]
    if not counts:
        return ""
    return "main behind: " + ", ".join(f"{name} {n}" for name, n in counts)


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}
    parts = [
        part
        for part in (phase(event), blocked(), inbox(), unreadable(), main_behind())
        if part
    ]
    if parts:
        print("  |  ".join(parts))


if __name__ == "__main__":
    main()
