#!/usr/bin/python3
"""PostToolUse hook — tells the session when the repo's coordination board changed.

Runs after every tool call, so the no-change path only stats the board folder's files. State
(cwd -> repo mapping and the last seen name -> mtime snapshot) lives in
/tmp/claude-coordination-watch-<session_id>.json. The first call of a session only records the
snapshot; the SessionStart inject hook already covered the start.
"""

import json
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
import board


def snapshot(folder):
    snap = {}
    try:
        with os.scandir(folder) as it:
            for item in it:
                if item.name.endswith(".md") and not item.name.startswith("."):
                    snap[item.name[:-3]] = item.stat().st_mtime_ns
    except FileNotFoundError:
        pass
    return snap


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    cwd = event.get("cwd") or os.getcwd()
    session = str(event.get("session_id") or "unknown")
    state_path = f"/tmp/claude-coordination-watch-{session}.json"
    try:
        with open(state_path) as handle:
            state = json.load(handle)
    except (OSError, ValueError):
        state = {}

    repos = state.setdefault("repos", {})
    if cwd not in repos:
        repos[cwd] = board.repo_name(cwd) or ""
    repo = repos[cwd]
    if not repo:
        sys.exit(0)

    snaps = state.setdefault("snapshots", {})
    current = snapshot(board.repo_dir(repo))
    previous = snaps.get(repo)
    if previous == current:
        sys.exit(0)
    snaps[repo] = current
    with open(state_path, "w") as handle:
        json.dump(state, handle)
    if previous is None:
        sys.exit(0)

    parts = []
    for name in sorted(current):
        if name not in previous or previous[name] != current[name]:
            verb = "added" if name not in previous else "changed"
            try:
                line = board.format_line(board.read_entry(repo, name))
            except board.BoardError:
                line = f"{repo}/{name}"
            parts.append(f"{verb}: {line}")
    for name in sorted(set(previous) - set(current)):
        parts.append(f"removed: {repo}/{name}")
    if not parts:
        sys.exit(0)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": f"Coordination board changed ({repo}):\n"
                    + "\n".join(parts),
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
        print(f"coordination-watch: {exc}", file=sys.stderr)
        sys.exit(0)
