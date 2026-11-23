#!/usr/bin/python3
"""Fast-forward a repo's main checkout to ``origin/main``, or say in one line why not.

Every wave runs in its own git worktree, so the main checkout of a repo is rarely touched and
falls behind ``origin/main``. ``sync_main_checkout`` brings it forward without ever disturbing
work: it never stashes, resets, rebases or switches branch, only fast-forwards ``main`` when
that is safe. Any path in the repo works, including a linked worktree: the main checkout is the
parent of the git common dir.

Each result is one line, ``<repo>: <outcome>``, where ``<repo>`` is the main checkout's folder
name. ``commits_behind_origin`` reads local refs only, for the statusline. ``active_repo_paths``
lists the Active repositories from the role table in ``instructions.md``.

Stdlib only; usable as a CLI (``sync_main.py --help``) and as a module by the session hooks.
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
from concurrent.futures import ThreadPoolExecutor

NOT_A_REPO = "not a git repository"


# --------------------------------------------------------------------------- git


class _GitResult:
    def __init__(self, code: int, out: str, err: str, timed_out: bool = False):
        self.code = code
        self.out = out.strip()
        self.err = err.strip()
        self.timed_out = timed_out


def _git(cwd: str, *args: str, timeout: float | None = None, no_prompt: bool = False):
    env = dict(os.environ)
    if no_prompt:
        env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    proc = subprocess.Popen(
        ["git", *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # git's ssh child keeps the pipes open after git dies, so kill the whole group.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()
        out, err = proc.communicate()
        return _GitResult(-1, out or "", err or "", timed_out=True)
    return _GitResult(proc.returncode, out, err)


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "unknown error"


def _plural(count: int) -> str:
    return f"{count} commit" if count == 1 else f"{count} commits"


def _main_checkout(path: str) -> str | None:
    if not os.path.isdir(path):
        return None
    result = _git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if result.code != 0 or not result.out:
        return None
    return os.path.dirname(result.out.rstrip("/"))


def _count(main: str, rev_range: str) -> int | None:
    result = _git(main, "rev-list", "--count", rev_range)
    if result.code != 0:
        return None
    try:
        return int(result.out)
    except ValueError:
        return None


# --------------------------------------------------------------------------- sync


def sync_main_checkout(
    path: str, fetch_only: bool = False, timeout: float = 8.0
) -> str:
    """Fetch origin and fast-forward the main checkout of the repo containing ``path``."""
    name = os.path.basename(os.path.abspath(path).rstrip("/")) or path
    try:
        main = _main_checkout(path)
        if main is None:
            return f"{name}: {NOT_A_REPO}"
        name = os.path.basename(main)
        return f"{name}: {_sync(main, fetch_only, timeout)}"
    except Exception as exc:  # noqa: BLE001 - last resort, a sync never breaks the caller
        return f"{name}: not synced, {_first_line(str(exc))}"


def _sync(main: str, fetch_only: bool, timeout: float) -> str:
    fetch = _git(main, "fetch", "origin", timeout=timeout, no_prompt=True)
    if fetch.timed_out:
        return f"not synced, fetch failed (timed out after {timeout:g} s)"
    if fetch.code != 0:
        return f"not synced, fetch failed ({_first_line(fetch.err)})"
    if fetch_only:
        return "fetched"

    head = _git(main, "symbolic-ref", "--short", "-q", "HEAD")
    branch = head.out if head.code == 0 and head.out else "detached HEAD"
    if branch != "main":
        return f"not synced, checkout is on {branch}"

    ahead = _count(main, "origin/main..main")
    behind = _count(main, "main..origin/main")
    if ahead is None or behind is None:
        return "not synced, origin/main not found"
    if ahead > 0:
        return f"not synced, main has {_plural(ahead)} origin/main lacks"
    if behind == 0:
        return "up to date"

    merge = _git(main, "merge", "--ff-only", "origin/main")
    if merge.code != 0:
        message = merge.err or merge.out
        if "would be overwritten" in message:
            files = re.findall(r"^\t(.+)$", message, flags=re.MULTILINE)
            if files:
                return (
                    f"not synced, uncommitted changes in the way ({', '.join(files)})"
                )
        return f"not synced, {_first_line(message)}"
    short = _git(main, "rev-parse", "--short", "HEAD").out
    return f"fast-forwarded {_plural(behind)} to {short}"


def commits_behind_origin(path: str) -> int | None:
    """Commits on ``origin/main`` that ``main`` lacks, from local refs only (no fetch)."""
    try:
        main = _main_checkout(path)
        if main is None:
            return None
        return _count(main, "main..origin/main")
    except Exception:  # noqa: BLE001 - never raises
        return None


# --------------------------------------------------------------------------- repos


def active_repo_paths() -> list[str]:
    """Paths of the Active repositories named in ``<projects>/agents/instructions.md``."""
    try:
        projects = os.environ.get("CLAUDE_PROJECTS_DIR") or os.path.expanduser(
            "~/Projects"
        )
        with open(
            os.path.join(projects, "agents", "instructions.md"), encoding="utf-8"
        ) as fh:
            lines = fh.read().splitlines()
        for line in lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if (
                line.lstrip().startswith("|")
                and len(cells) >= 2
                and cells[0] == "Active"
            ):
                names = re.findall(r"`([^`]+)`", cells[1])
                paths = [os.path.join(projects, name) for name in names]
                return [p for p in paths if os.path.exists(os.path.join(p, ".git"))]
    except Exception:  # noqa: BLE001 - never raises
        return []
    return []


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fast-forward each repo's main checkout to origin/main, one line per path."
    )
    parser.add_argument(
        "--fetch-only", action="store_true", help="fetch, never move main"
    )
    parser.add_argument(
        "paths", metavar="PATH", nargs="+", help="any path inside a repo"
    )
    args = parser.parse_args(argv)
    with ThreadPoolExecutor(max_workers=len(args.paths)) as pool:
        lines = list(
            pool.map(lambda p: sync_main_checkout(p, args.fetch_only), args.paths)
        )
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
