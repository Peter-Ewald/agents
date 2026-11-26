#!/usr/bin/python3
"""PreToolUse hook (matcher: Bash) — blocks integrating to main or pushing a dataset while the
coordination board says another wave must go first.

Blocks (exit 2) when
- the command integrates to main (`git push` targeting main, `az repos pr update --status
  completed`, an `az rest` PATCH that completes a pull request, `gh pr merge`) and an open
  `blocks: merge` hold names this repo+wave as waiting, or the repo integration lock `lock.md` is
  held by a different wave;
- the command pushes a dataset (`eval-dataset push --name D` / `push-all`) and the matching
  `lock-dataset-<D>.md` is held by a different wave;
- either kind of command runs while an entry in the repo's own board folder cannot be read (the
  message names it and says to repair or remove it), since holds and locks may hide in it.
No board folder: allow silently. Internal errors are printed to stderr and never block.
"""

import json
import os
import re
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
import board
from shell_command import git_target, segments_with_directory

MAIN_BRANCHES = ("main", "master")


def push_targets_main(args, directory):
    """args: tokens after `push`. True if the push lands on main."""
    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]
    if not refspecs:
        branch = board._git(directory, "branch", "--show-current")
        return branch in MAIN_BRANCHES
    for spec in refspecs:
        dst = spec.lstrip("+").split(":")[-1]
        dst = dst.removeprefix("refs/heads/")
        if dst in MAIN_BRANCHES:
            return True
    return False


def option(args, *names):
    """Value of the first of `names` given as `name value` or `name=value`, else None."""
    for i, arg in enumerate(args):
        for name in names:
            if arg == name and i + 1 < len(args):
                return args[i + 1]
            if arg.startswith(name + "="):
                return arg.split("=", 1)[1]
    return None


def rest_completes_pr(args, directory):
    """args: tokens after `az rest`. True if the call can complete a pull request.

    Azure Repos completes with rebase and fast-forward only through the REST API, as a PATCH on
    `.../pullrequests/<id>` whose body sets status completed or turns on auto-complete. A body given
    as `@file` that cannot be read yet (written earlier in the same command, or named by a shell
    variable) counts as completing.
    """
    if (option(args, "--method", "-m") or "").lower() != "patch":
        return False
    if "/pullrequests/" not in (option(args, "--url", "--uri", "-u") or "").lower():
        return False
    body = option(args, "--body", "-b")
    if not body:
        return False
    if body.startswith("@"):
        try:
            path = os.path.join(directory, os.path.expanduser(body[1:]))
            with open(path) as handle:
                body = handle.read()
        except OSError:
            return True
    return bool(re.search(r'"status"\s*:\s*"completed"|"autoCompleteSetBy"', body))


def classify(tokens, directory):
    """Return (directory, kind, dataset) with kind in merge|dataset|None."""
    if not tokens:
        return directory, None, None
    target = git_target(tokens, directory)
    if target is not None:
        target_dir, args = target
        if args and args[0] == "push" and push_targets_main(args[1:], target_dir):
            return target_dir, "merge", None
        return target_dir, None, None
    if tokens[:3] == ["gh", "pr", "merge"]:
        return directory, "merge", None
    if tokens[:3] == ["az", "repos", "pr"] and "update" in tokens[3:4]:
        joined = " ".join(tokens)
        if re.search(
            r"--status[ =]completed\b|--auto-complete[ =](true|yes|on)\b", joined
        ):
            return directory, "merge", None
        return directory, None, None
    if tokens[:2] == ["az", "rest"]:
        if rest_completes_pr(tokens[2:], directory):
            return directory, "merge", None
        return directory, None, None
    for idx, tok in enumerate(tokens[:8]):
        if os.path.basename(tok) == "eval-dataset" and idx + 1 < len(tokens):
            sub = tokens[idx + 1]
            if sub == "push-all":
                return directory, "dataset", ""
            if sub == "push":
                dataset = ""
                for j, a in enumerate(tokens[idx + 2 :], start=idx + 2):
                    if a == "--name" and j + 1 < len(tokens):
                        dataset = tokens[j + 1]
                    elif a.startswith("--name="):
                        dataset = a.split("=", 1)[1]
                return directory, "dataset", dataset
    return directory, None, None


def other_holder(entry, repo, key):
    """True when the lock entry is held by a wave other than (repo, key)."""
    return board.parse_wave_ref(entry.get("wave")) != (repo, key) or not key


def check(kind, dataset, directory):
    repo = board.repo_name(directory)
    if repo is None or not os.path.isdir(board.repo_dir(repo)):
        return None
    key = board.wave_key(directory)
    folder = f"{board.repo_dir(repo)}/"
    broken = board.read_board(repo)[1]
    if broken:
        name = broken[0].ref.split("/", 1)[-1]
        return (
            f"coordination: unreadable board entry {folder}{name}.md "
            f"({broken[0].reason}); repair or remove it (board.py rm {repo}/{name}) "
            "before integrating."
        )
    if kind == "merge":
        holds = board.open_merge_holds_for(repo, key)
        if holds:
            return (
                f"coordination: open merge hold {folder}{holds[0].name}.md names "
                f"{repo} / {key} as waiting; park this wave until the hold is satisfied "
                f"(board.py satisfy {repo}/{holds[0].name})."
            )
        lock = board.lock_holder(repo)
        if lock is not None and other_holder(lock, repo, key):
            return (
                f"coordination: integration lock {folder}lock.md is held by "
                f"{lock.get('wave')}; wait for it to release, or park this wave."
            )
    elif kind == "dataset":
        locks = (
            [board.lock_holder(repo, dataset)] if dataset else board.dataset_locks(repo)
        )
        for lock in locks:
            if lock is not None and other_holder(lock, repo, key):
                return (
                    f"coordination: dataset lock {folder}{lock.name}.md is held by "
                    f"{lock.get('wave')}; wait for it to release, or park this wave."
                )
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None
    command = (event.get("tool_input") or {}).get("command", "")
    directory = event.get("cwd") or os.getcwd()
    for tokens, segment_dir in segments_with_directory(command, directory):
        seg_dir, kind, dataset = classify(tokens, segment_dir)
        if kind:
            reason = check(kind, dataset, seg_dir)
            if reason:
                return reason
    return None


if __name__ == "__main__":
    try:
        reason = main()
    except Exception as exc:  # noqa: BLE001
        print(f"coordination-guard: {exc}", file=sys.stderr)
        sys.exit(0)
    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
