#!/usr/bin/python3
"""PreToolUse hook (matcher: Bash) — blocks `git commit` if a staged pyproject.toml
version bump doesn't have a matching staged CHANGELOG.md update in the same package
directory. Changelog-before-commit ordering, per instructions.md's release conventions.

The check runs in the repo each `git commit` targets: the session's start folder, or the
directory a `cd <repo> &&` or `git -C <repo>` in the command points to. A failure to
determine the staged files is printed to stderr and never blocks the commit.
"""

import json
import os
import re
import subprocess
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
from shell_command import git_target, segments_with_directory


def git_output(directory, *args):
    """Stdout of `git -C directory args`; raises RuntimeError if git fails."""
    result = subprocess.run(
        ["git", "-C", directory, *args],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        stderr_lines = result.stderr.strip().splitlines()
        reason = stderr_lines[0] if stderr_lines else f"git exited {result.returncode}"
        raise RuntimeError(f"{directory}: {reason}")
    return result.stdout


def commit_directories(command, start_directory):
    """Distinct directories in which the command runs `git commit`, in order."""
    directories = []
    for tokens, segment_dir in segments_with_directory(command, start_directory):
        target = git_target(tokens, segment_dir) if tokens else None
        if target is None:
            continue
        directory, args = target
        if args and args[0] == "commit" and directory not in directories:
            directories.append(directory)
    return directories


def unmatched_version_bumps(directory):
    """(pyproject, changelog) pairs where a staged version bump lacks a staged changelog."""
    staged = git_output(directory, "diff", "--cached", "--name-only").splitlines()
    staged_set = set(staged)
    problems = []
    for f in staged:
        if not f.endswith("pyproject.toml"):
            continue
        diff = git_output(directory, "diff", "--cached", "-U0", "--", f)
        if re.search(r"^\+\s*version\s*=", diff, re.MULTILINE):
            changelog = os.path.join(os.path.dirname(f), "CHANGELOG.md")
            if changelog not in staged_set:
                problems.append((f, changelog))
    return problems


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None
    if event.get("tool_name") != "Bash":
        return None

    command = (event.get("tool_input") or {}).get("command", "")
    start_directory = event.get("cwd") or os.getcwd()

    lines = []
    for directory in commit_directories(command, start_directory):
        try:
            problems = unmatched_version_bumps(directory)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f"require-changelog-before-commit: {exc}", file=sys.stderr)
            continue
        for f, changelog in problems:
            lines.append(
                f"  {f} bumped, but {changelog} is not staged (repo: {directory})"
            )

    if not lines:
        return None
    return "\n".join(
        [
            "Version bump staged without a matching CHANGELOG.md update:",
            *lines,
            "Update the changelog first, then stage it alongside the version bump.",
        ]
    )


if __name__ == "__main__":
    try:
        message = main()
    except Exception as exc:  # noqa: BLE001
        print(f"require-changelog-before-commit: {exc}", file=sys.stderr)
        sys.exit(0)
    if message:
        print(message, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
