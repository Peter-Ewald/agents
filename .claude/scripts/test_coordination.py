#!/usr/bin/env python3
"""Smoke tests for the coordination board, its three hooks, and new-wave-worktree.sh.

Run with `python3 test_coordination.py` (or pytest). Stdlib only; everything happens in temp dirs.
"""

import filecmp
import json
import os
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.join(HERE, "..", "hooks")
BOARD = os.path.join(HERE, "board.py")
WORKTREE_SH = os.path.join(HERE, "new-wave-worktree.sh")
REPO = "Repo_X"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


class Env:
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="coord-test-")
        self.board = os.path.join(self.tmp, "board")
        self.remote = os.path.join(self.tmp, "remote.git")
        self.repo = os.path.join(self.tmp, REPO)
        self.env = dict(os.environ, CLAUDE_COORDINATION_DIR=self.board, **GIT_ENV)
        self.session = "test-" + uuid.uuid4().hex
        self.git("init", "--bare", "-b", "main", self.remote, cwd=self.tmp)
        self.git("init", "-b", "main", self.repo, cwd=self.tmp)
        with open(os.path.join(self.repo, "README.md"), "w") as handle:
            handle.write("hello\n")
        self.git("add", "README.md")
        self.git("commit", "-m", "init")
        self.git("remote", "add", "origin", self.remote)
        self.git("push", "-u", "origin", "main")
        self.git("checkout", "-b", "wave-12-x")

    def git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def board_cli(self, *args):
        return subprocess.run(
            [sys.executable, BOARD, *args],
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
        )

    def hook(self, name, payload):
        return subprocess.run(
            [os.path.join(HOOKS, name)],
            input=json.dumps(payload),
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
        )

    def guard(self, command, cwd=None):
        return self.hook(
            "coordination-guard.py",
            {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": cwd or self.repo,
            },
        )

    def watch(self):
        return self.hook(
            "coordination-watch.py", {"cwd": self.repo, "session_id": self.session}
        )

    def cleanup(self):
        state = f"/tmp/claude-coordination-watch-{self.session}.json"
        if os.path.exists(state):
            os.unlink(state)


def with_env(func):
    def wrapper():
        env = Env()
        try:
            func(env)
        finally:
            env.cleanup()

    wrapper.__name__ = func.__name__
    return wrapper


@with_env
def test_repo_and_wave(env):
    assert env.board_cli("repo", env.repo).stdout.strip() == REPO
    assert env.board_cli("wave", env.repo).stdout.strip() == "wave-12"
    assert env.board_cli("repo", env.tmp).returncode == 1


@with_env
def test_lock_contention(env):
    assert env.board_cli("lock", REPO, "--wave", "wave-12").returncode == 0
    assert env.board_cli("lock", REPO, "--wave", "wave-12").returncode == 0
    other = env.board_cli("lock", REPO, "--wave", "wave-13")
    assert other.returncode == 1 and "wave-12" in other.stdout
    assert env.board_cli("unlock", REPO, "--wave", "wave-13").returncode == 1
    assert env.board_cli("unlock", REPO, "--wave", "wave-12").returncode == 0
    assert env.board_cli("lock", REPO, "--wave", "wave-13").returncode == 0


@with_env
def test_merge_hold_blocks_main_push(env):
    filed = env.board_cli(
        "file", "hold", "wave-12-after-11", "--repo", REPO,
        f"waiting={REPO} / wave-12", f"on={REPO} / wave-11",
        "condition=wave 11 merged", "blocks=merge", "status=open",
        "expires=2099-01-01",
    )  # fmt: skip
    assert filed.returncode == 0, filed.stderr
    url = '"https://dev.azure.com/O/P/_apis/git/repositories/R/pullrequests/5?api-version=7.1"'
    rest = f"az rest --method patch --resource 499b84ac --url {url} "
    inline = (
        '--body "{\\"status\\":\\"completed\\",\\"lastMergeSourceCommit\\":'
        '{\\"commitId\\":\\"$HEAD_SHA\\"},\\"completionOptions\\":{\\"mergeStrategy\\":\\"rebase\\"}}"'
    )
    with open(os.path.join(env.repo, "title.json"), "w") as handle:
        handle.write('{"title": "x"}')
    for command in (
        "git push origin main",
        "git push origin HEAD:main",
        "git push origin wave-12-x:main",
        "az repos pr update --id 5 --status completed",
        f"cd {env.repo} && gh pr merge 5",
        rest + inline,
        "printf '{}' > \"$BODY\" && " + rest + '--body "@$BODY"',
    ):
        result = env.guard(command)
        assert result.returncode == 2, command
        assert "wave-12-after-11.md" in result.stderr
    assert env.guard("git push -u origin wave-12-x").returncode == 0
    assert env.guard("az repos pr create --draft --title x").returncode == 0
    assert env.guard(rest + "--body @title.json").returncode == 0
    assert env.guard(f"az rest --resource 499b84ac --url {url}").returncode == 0
    assert env.board_cli("satisfy", f"{REPO}/wave-12-after-11").returncode == 0
    assert env.guard("git push origin main").returncode == 0


@with_env
def test_integration_lock_blocks_other_wave(env):
    env.board_cli("lock", REPO, "--wave", "wave-13")
    assert env.guard("git push origin main").returncode == 2
    env.board_cli("unlock", REPO, "--wave", "wave-13")
    assert env.guard("git push origin main").returncode == 0


@with_env
def test_dataset_lock_blocks_push(env):
    env.board_cli("lock", REPO, "--wave", "wave-13", "--dataset", "hr_dev")
    command = (
        "uv run eval-dataset push --name hr_dev --source x.json --version-label 1.2"
    )
    assert env.guard(command).returncode == 2
    assert env.guard("uv run eval-dataset push-all").returncode == 2
    other = "uv run eval-dataset push --name other --source x.json"
    assert env.guard(other).returncode == 0
    env.board_cli("lock", REPO, "--wave", "wave-12", "--dataset", "mine")
    assert env.guard("eval-dataset push --name mine --source x.json").returncode == 0


@with_env
def test_guard_without_board_allows(env):
    assert env.guard("git push origin main").returncode == 0


@with_env
def test_watch(env):
    os.makedirs(os.path.join(env.board, REPO))
    first = env.watch()
    assert first.returncode == 0 and first.stdout == ""
    assert env.watch().stdout == ""
    env.board_cli("file", "notice", "hello", "--repo", REPO, "summary=wave 11 merged")
    changed = env.watch()
    assert "Coordination board changed" in changed.stdout, changed.stderr
    assert "added" in changed.stdout and "hello" in changed.stdout
    assert env.watch().stdout == ""


@with_env
def test_inject(env):
    assert env.hook("coordination-inject.py", {"cwd": env.repo}).stdout == ""
    env.board_cli("file", "notice", "old", "--repo", REPO, "expires=2000-01-01")
    env.board_cli(
        "file", "hold", "stale-hold", "--repo", REPO,
        f"waiting={REPO} / wave-12", "on=somebody", "blocks=start",
        "status=open", "expires=2000-01-01",
    )  # fmt: skip
    result = env.hook("coordination-inject.py", {"cwd": env.repo, "session_id": "s"})
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert context.startswith(f"Coordination board for {REPO}:")
    assert "stale-hold" in context and "STALE" in context
    assert not os.path.exists(os.path.join(env.board, REPO, "old.md"))
    assert os.path.exists(os.path.join(env.board, REPO, "stale-hold.md"))


@with_env
def test_set_preserves_body_and_order(env):
    body = os.path.join(env.tmp, "body.txt")
    with open(body, "w") as handle:
        handle.write("Some notes.\n")
    env.board_cli(
        "file", "plan", "p", "--repo", REPO, "--body-file", body,
        "wave=wave-12", "status=ready", "holds=[a, b]",
    )  # fmt: skip
    extra = os.path.join(env.tmp, "extra.txt")
    with open(extra, "w") as handle:
        handle.write("Handover.\n")
    env.board_cli("set", f"{REPO}/p", "status=running", "--append-body-file", extra)
    text = env.board_cli("show", f"{REPO}/p").stdout
    assert "status: running" in text and "holds: [a, b]" in text
    assert "Some notes." in text and "Handover." in text
    assert text.index("kind:") < text.index("wave:") < text.index("status:")
    assert env.board_cli("file", "plan", "p", "--repo", REPO).returncode == 1


@with_env
def test_new_wave_worktree(env):
    secret = os.path.join(env.repo, ".env")
    with open(secret, "w") as handle:
        handle.write("TOKEN=not-a-real-secret\n")
    with open(os.path.join(env.repo, ".worktreeinclude"), "w") as handle:
        handle.write(".env\n")
    env.git("checkout", "main")

    def run():
        return subprocess.run(
            [WORKTREE_SH, env.repo, "wave-14-y"],
            env=env.env,
            check=False,
            capture_output=True,
            text=True,
        )

    first = run()
    assert first.returncode == 0, first.stderr
    path = first.stdout.strip().splitlines()[-1]
    assert path.endswith(".claude/worktrees/wave-14-y") and os.path.isdir(path)
    assert env.git("rev-parse", "HEAD", cwd=path) == env.git("rev-parse", "origin/main")
    assert filecmp.cmp(secret, os.path.join(path, ".env"), shallow=False)
    attrs = os.path.join(env.repo, ".git", "info", "attributes")
    with open(attrs) as handle:
        assert (
            handle.read().splitlines().count("docs/history/index.md merge=union") == 1
        )
    second = run()
    assert second.returncode == 0 and second.stdout.strip().splitlines()[-1] == path
    with open(attrs) as handle:
        assert handle.read().count("merge=union") == 1


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, func in tests:
        try:
            func()
            print(f"ok    {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
