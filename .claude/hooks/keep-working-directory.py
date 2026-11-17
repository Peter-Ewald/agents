#!/usr/bin/python3
"""PreToolUse hook (matcher: Bash): keeps the main session's working directory where it is.

In the main session, a `cd` at the top level of a Bash command carries over to every later command.
Path-scoped skills and rules are matched against that directory: `doc-conventions`
(`paths: ["**/*.md"]`) stops loading for markdown files outside it. So a session started in
`~/Projects` that drifted into one repo silently loses it for every other repo.

Blocks (exit 2) a command whose top-level `cd` or `pushd` would leave the session anywhere other than
- the directory it is in now,
- the session's project directory (`CLAUDE_PROJECT_DIR`, where the session started), or
- the root of a worktree `<repo>/.claude/worktrees/<name>`, where a wave works,
and a top-level `popd`, `cd -` or `cd $VAR`, whose target cannot be checked.

Always allows a `cd` inside `( … )` or `$( … )`, a command without a directory change, and every
command of a subagent (the event carries `agent_id`; a subagent's `cd` does not carry over).
Internal errors are printed to stderr and never block.
"""

import json
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
from shell_command import persistent_directory


def _same(a, b):
    return bool(a and b) and os.path.realpath(a) == os.path.realpath(b)


def _is_worktree_root(path):
    parent = os.path.dirname(os.path.normpath(path))
    return os.path.basename(parent) == "worktrees" and (
        os.path.basename(os.path.dirname(parent)) == ".claude"
    )


def blocked_reason(event):
    """The block message for this PreToolUse event, or None to allow it."""
    if event.get("tool_name") != "Bash" or event.get("agent_id"):
        return None
    command = (event.get("tool_input") or {}).get("command", "")
    if not any(word in command for word in ("cd", "pushd", "popd")):
        return None
    cwd = event.get("cwd") or os.getcwd()
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    final = persistent_directory(command, cwd)
    if final is not None and (
        _same(final, cwd) or _same(final, project) or _is_worktree_root(final)
    ):
        return None
    where = (
        f"to {final}"
        if final is not None
        else "to a directory this hook cannot work out"
    )
    home = project or cwd
    return (
        f"Blocked: this command's top-level `cd` would move the session's working directory {where}, "
        "and in the main session that carries over to every later command. Path-scoped skills "
        "and rules (doc-conventions) are matched against the working directory, so files "
        "outside it would stop loading them.\n"
        "Run the command without moving the session: `git -C <dir> …`, absolute paths, a tool's "
        "own option such as `uv --directory <dir> run …`, or a subshell `( cd <dir> && … )`.\n"
        f"A plain `cd` with a literal path is allowed back to {home} and into the root of a wave "
        "worktree (`<repo>/.claude/worktrees/<branch>`)."
    )


def main():
    try:
        reason = blocked_reason(json.load(sys.stdin))
    except Exception as exc:  # noqa: BLE001 - a hook error must never block the command
        print(f"keep-working-directory: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0
    if reason is None:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
