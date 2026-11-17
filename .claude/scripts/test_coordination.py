#!/usr/bin/env python3
"""Smoke tests for the coordination board, its three hooks, new-wave-worktree.sh, and the other hooks
that parse a Bash command (require-changelog-before-commit.py, keep-working-directory.py).

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


@with_env
def test_blocked_plans_listed_and_shown(env):
    for name, status in (("p1", "blocked"), ("p2", "running"), ("p3", "blocked")):
        env.board_cli("file", "plan", name, "--repo", REPO, f"status={status}")
    env.board_cli("file", "hold", "h1", "--repo", REPO, "status=blocked")
    listed = env.board_cli("list", "--kind", "plan", "--status", "blocked").stdout
    assert [line.split()[0] for line in listed.splitlines()] == [
        f"{REPO}/p1",
        f"{REPO}/p3",
    ]

    def statusline(payload):
        return subprocess.run(
            [os.path.join(HERE, "..", "statusline.py")],
            input=json.dumps(payload),
            env=env.env,
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()

    assert statusline({}) == f"⚠ 2 blocked: {REPO}/p1, {REPO}/p3"
    phase_file = f"/tmp/claude-wave-phase-{env.session}"
    with open(phase_file, "w") as handle:
        handle.write("wave-12 — Implement\n")
    try:
        shown = statusline({"session_id": env.session})
    finally:
        os.unlink(phase_file)
    assert shown == f"wave-12 — Implement  |  ⚠ 2 blocked: {REPO}/p1, {REPO}/p3"
    env.board_cli("set", f"{REPO}/p1", "status=running")
    env.board_cli("set", f"{REPO}/p3", "status=running")
    assert statusline({}) == ""


OTHER_REPO = "Repo_Y"


@with_env
def test_inject_outside_repo_shows_all_boards(env):
    """AC1: outside a repo the hook shows every repo's board and clears expired notices."""
    for repo in (REPO, OTHER_REPO):
        env.board_cli("file", "plan", f"open-{repo}", "--repo", repo, "status=ready")
        env.board_cli(
            "file", "notice", f"old-{repo}", "--repo", repo, "expires=2000-01-01"
        )
    result = env.hook("coordination-inject.py", {"cwd": env.tmp, "session_id": "s"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), "no block is printed outside a repo"
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    for repo in (REPO, OTHER_REPO):
        assert context.count(f"Coordination board for {repo}:") == 1, context
        assert f"open-{repo}" in context, context
        assert not os.path.exists(os.path.join(env.board, repo, f"old-{repo}.md")), (
            f"expired notice of {repo} not deleted"
        )


@with_env
def test_inject_outside_repo_silent_when_nothing_open(env):
    """AC2: outside a repo with no open entries anywhere the hook prints nothing."""
    empty = env.hook("coordination-inject.py", {"cwd": env.tmp, "session_id": "s"})
    assert empty.returncode == 0 and empty.stdout == "", empty.stdout
    for repo in (REPO, OTHER_REPO):
        env.board_cli(
            "file", "notice", f"old-{repo}", "--repo", repo, "expires=2000-01-01"
        )
    expired = env.hook("coordination-inject.py", {"cwd": env.tmp, "session_id": "s"})
    assert expired.returncode == 0 and expired.stdout == "", expired.stdout
    # Precondition that makes the silence meaningful: an open entry outside a repo is shown.
    env.board_cli("file", "plan", "open", "--repo", REPO, "status=ready")
    shown = env.hook("coordination-inject.py", {"cwd": env.tmp, "session_id": "s"})
    assert "open" in shown.stdout, "no block is printed outside a repo"


def _stage_version_bump(env, changelog):
    with open(os.path.join(env.repo, "pyproject.toml"), "w") as handle:
        handle.write('[project]\nname = "x"\nversion = "1.0.0"\n')
    env.git("add", "pyproject.toml")
    if changelog:
        with open(os.path.join(env.repo, "CHANGELOG.md"), "w") as handle:
            handle.write("## [1.0.0]\n")
        env.git("add", "CHANGELOG.md")


def _changelog_hook(env, command):
    return env.hook(
        "require-changelog-before-commit.py",
        {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": env.tmp},
    )


@with_env
def test_changelog_hook_checks_repo_after_cd(env):
    """AC4: a commit after cd into a repo is checked in that repo, not the start folder."""
    _stage_version_bump(env, changelog=False)
    result = _changelog_hook(env, f"cd {env.repo} && git commit -m x")
    assert result.returncode == 2, (
        f"exit {result.returncode}: the hook checks the start folder, not {env.repo}"
    )
    assert "pyproject.toml" in result.stderr, result.stderr


@with_env
def test_changelog_hook_checks_repo_of_git_dash_c(env):
    """AC5: a commit with git -C is checked in the named repo."""
    _stage_version_bump(env, changelog=False)
    result = _changelog_hook(env, f"git -C {env.repo} commit -m x")
    assert result.returncode == 2, (
        f"exit {result.returncode}: the hook checks the start folder, not {env.repo}"
    )


@with_env
def test_changelog_hook_passes_complete_release_after_cd(env):
    """AC6: a version bump with its CHANGELOG.md staged passes after cd."""
    command = f"cd {env.repo} && git commit -m x"
    # Precondition: the hook does look into the repo, so the pass below is due to the changelog.
    _stage_version_bump(env, changelog=False)
    blocked = _changelog_hook(env, command)
    assert blocked.returncode == 2, (
        f"exit {blocked.returncode}: the hook checks the start folder, not {env.repo}"
    )
    _stage_version_bump(env, changelog=True)
    result = _changelog_hook(env, command)
    assert result.returncode == 0, result.stderr


@with_env
def test_new_wave_worktree_copies_personal_rules(env):
    """AC8: a new worktree gets the main checkout's untracked .claude/rules files."""
    rules = os.path.join(env.repo, ".claude", "rules")
    os.makedirs(rules)
    rule = os.path.join(rules, "integration.md")
    with open(rule, "w") as handle:
        handle.write("Integration: push\n")
    env.git("checkout", "main")
    assert not os.path.exists(os.path.join(env.repo, ".worktreeinclude"))

    def run():
        return subprocess.run(
            [WORKTREE_SH, env.repo, "wave-99-x"],
            env=env.env,
            check=False,
            capture_output=True,
            text=True,
        )

    first = run()
    assert first.returncode == 0, first.stderr
    path = first.stdout.strip().splitlines()[-1]
    copied = os.path.join(path, ".claude", "rules", "integration.md")
    assert os.path.isfile(copied), "the worktree has no .claude/rules/integration.md"
    assert filecmp.cmp(rule, copied, shallow=False)
    second = run()
    assert second.returncode == 0, second.stderr
    assert filecmp.cmp(rule, copied, shallow=False)


PROJECT = "/projects"


def _keep_dir(command, cwd=PROJECT, agent_id=None):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
    if agent_id:
        payload["agent_id"] = agent_id
    return subprocess.run(
        [os.path.join(HOOKS, "keep-working-directory.py")],
        input=json.dumps(payload),
        env=dict(os.environ, CLAUDE_PROJECT_DIR=PROJECT),
        check=False,
        capture_output=True,
        text=True,
    )


def test_keep_dir_blocks_cd_into_repo():
    """A top-level cd into a repo would carry over in the main session: blocked."""
    result = _keep_dir(f"cd {PROJECT}/RepoA && git status -sb")
    assert result.returncode == 2, result.stderr
    assert f"{PROJECT}/RepoA" in result.stderr and "git -C" in result.stderr, (
        result.stderr
    )


def test_keep_dir_blocks_relative_cd_and_unresolvable_targets():
    for command in (
        "cd RepoA",
        "ls; cd RepoA/docs",
        'cd "$WT" && ls',
        "cd -",
        "popd",
        "if true; then cd RepoA; fi",
        "echo hi\ncd RepoA",
    ):
        result = _keep_dir(command)
        assert result.returncode == 2, f"{command!r} allowed"


def test_keep_dir_allows_commands_that_leave_the_directory():
    for command in (
        f"git -C {PROJECT}/RepoA status -sb",
        f"(cd {PROJECT}/RepoA && uv run pytest -q)",
        f"x=$(cd {PROJECT}/RepoA && pwd); echo $x",
        f"cd {PROJECT}/RepoA && ls; cd {PROJECT}",
        'echo "cd RepoA; rm" && grep -n cd file.txt',
        "uv --directory RepoA run pytest -q",
    ):
        result = _keep_dir(command)
        assert result.returncode == 0, f"{command!r} blocked: {result.stderr}"


def test_keep_dir_reads_quotes_nested_in_command_substitution():
    """Quotes inside `$( … )` inside double quotes don't make the command unreadable."""
    nested = 'echo "n=$(grep -o \'"entrypoint":"[^"]*"\' f | tr \'\\n\' \' \')"'
    allowed = _keep_dir(f"( cd {PROJECT}/RepoA && for f in $(ls); do {nested}; done )")
    assert allowed.returncode == 0, allowed.stderr
    blocked = _keep_dir(f"{nested}; cd RepoA")
    assert blocked.returncode == 2 and f"{PROJECT}/RepoA" in blocked.stderr, (
        blocked.stderr
    )


def test_keep_dir_allows_wave_worktree_root_only():
    worktree = f"{PROJECT}/RepoA/.claude/worktrees/wave-12-x"
    assert _keep_dir(f"cd {worktree}").returncode == 0
    assert _keep_dir(f"cd {worktree}/legal_poc && uv run pytest -q").returncode == 2


def test_keep_dir_allows_return_to_project_dir():
    assert _keep_dir(f"cd {PROJECT}", cwd=f"{PROJECT}/RepoA").returncode == 0
    assert _keep_dir("cd ..", cwd=f"{PROJECT}/RepoA").returncode == 0


def test_keep_dir_ignores_subagents():
    assert _keep_dir(f"cd {PROJECT}/RepoA", agent_id="abc123").returncode == 0


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
