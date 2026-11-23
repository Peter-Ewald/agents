#!/usr/bin/env python3
"""Tests for relock-editable.sh: after an SDK version bump, every git-tracked uv.lock that installs the
SDK editable is relocked to the new version, and no other lock is touched.

Run with `python3 test_relock_editable.py` (or pytest). Stdlib only; each fixture is a temp git repo with
path dependencies only, and every uv call runs with UV_OFFLINE=1, so no network is needed.
"""

import os
import subprocess
import sys
import tempfile
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "relock-editable.sh")
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
ENV = dict(os.environ, UV_OFFLINE="1", **GIT_ENV)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write(text)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def run(args, cwd):
    return subprocess.run(
        args, check=False, cwd=cwd, env=ENV, capture_output=True, text=True
    )


def check(args, cwd):
    result = run(args, cwd)
    assert result.returncode == 0, f"{args} failed:\n{result.stdout}\n{result.stderr}"
    return result


def sdk_package(repo, package, version):
    # No [build-system]: the metadata is static, so locking an editable path dependency on it needs no
    # build backend and works offline.
    write(
        os.path.join(repo, "sdk", package, "pyproject.toml"),
        f'[project]\nname = "{package.replace("_", "-")}"\nversion = "{version}"\n'
        'requires-python = ">=3.8"\ndependencies = []\n',
    )


def consumer(repo, name, requirements=(), sources=()):
    deps = ", ".join(f'"{req}"' for req in requirements)
    text = (
        f'[project]\nname = "{name.replace("_", "-")}"\nversion = "0.1.0"\n'
        f'requires-python = ">=3.8"\ndependencies = [{deps}]\n'
    )
    if sources:
        text += "\n[tool.uv.sources]\n" + "".join(
            f'{package.replace("_", "-")} = {{ path = "../sdk/{package}", editable = true }}\n'
            for package in sources
        )
    write(os.path.join(repo, name, "pyproject.toml"), text)
    check(["uv", "--directory", os.path.join(repo, name), "lock"], repo)


def locked_version(lock_path, dist):
    with open(lock_path, "rb") as handle:
        lock = tomllib.load(handle)
    for package in lock.get("package", []):
        if package["name"] == dist:
            return package["version"]
    return None


def bump(repo, package, old, new):
    path = os.path.join(repo, "sdk", package, "pyproject.toml")
    with open(path) as handle:
        text = handle.read()
    assert f'version = "{old}"' in text
    write(path, text.replace(f'version = "{old}"', f'version = "{new}"'))


def init_repo(prefix):
    repo = tempfile.mkdtemp(prefix=prefix)
    check(["git", "init", "-q", "-b", "main", repo], repo)
    return repo


def commit_all(repo):
    check(["git", "add", "-A"], repo)
    check(["git", "commit", "-q", "-m", "fixture"], repo)


class Release:
    """The shared fixture of AC1, AC2, AC3 and AC5: one repo, one run of `relock-editable.sh pkg_a`."""

    def __init__(self):
        self.repo = init_repo("relock-test-")
        sdk_package(self.repo, "pkg_a", "1.0.0")
        sdk_package(self.repo, "pkg_b", "1.0.0")
        consumer(self.repo, "app", ["pkg-a"], ["pkg_a"])
        consumer(self.repo, "other")
        consumer(self.repo, "b_only", ["pkg-b"], ["pkg_b"])
        commit_all(self.repo)
        # Locked after the commit and never added: scratch/uv.lock stays untracked.
        consumer(self.repo, "scratch", ["pkg-a"], ["pkg_a"])
        assert locked_version(self.lock("app"), "pkg-a") == "1.0.0"
        assert locked_version(self.lock("scratch"), "pkg-a") == "1.0.0"
        self.before = {
            name: read_bytes(self.lock(name)) for name in ("other", "b_only", "scratch")
        }
        bump(self.repo, "pkg_a", "1.0.0", "1.1.0")
        self.result = run(["bash", SCRIPT, "pkg_a"], self.repo)
        self.stdout_lines = self.result.stdout.splitlines()

    def lock(self, name):
        return os.path.join(self.repo, name, "uv.lock")

    def assert_succeeded(self):
        assert self.result.returncode == 0, (
            f"exit {self.result.returncode}\nstdout:\n{self.result.stdout}\n"
            f"stderr:\n{self.result.stderr}"
        )


_RELEASE = None


def release():
    global _RELEASE
    if _RELEASE is None:
        _RELEASE = Release()
    return _RELEASE


# AC1
def test_relocks_editable_installer_to_new_version():
    fixture = release()
    fixture.assert_succeeded()
    assert locked_version(fixture.lock("app"), "pkg-a") == "1.1.0"
    assert "app/uv.lock" in fixture.stdout_lines, fixture.result.stdout


# AC2
def test_leaves_lock_without_sdk_dependency_untouched():
    fixture = release()
    fixture.assert_succeeded()
    assert read_bytes(fixture.lock("other")) == fixture.before["other"]
    assert "other/uv.lock" not in fixture.stdout_lines, fixture.result.stdout


# AC3
def test_leaves_lock_of_other_sdk_package_untouched():
    fixture = release()
    fixture.assert_succeeded()
    assert read_bytes(fixture.lock("b_only")) == fixture.before["b_only"]
    assert "b_only/uv.lock" not in fixture.stdout_lines, fixture.result.stdout


# AC4
def test_failed_relock_stops_run_naming_project():
    repo = init_repo("relock-test-broken-")
    sdk_package(repo, "pkg_a", "1.0.0")
    consumer(repo, "broken_consumer", ["pkg-a"], ["pkg_a"])
    commit_all(repo)
    assert (
        locked_version(os.path.join(repo, "broken_consumer", "uv.lock"), "pkg-a")
        == "1.0.0"
    )
    bump(repo, "pkg_a", "1.0.0", "1.1.0")
    # The new version adds a dependency that cannot be resolved offline, so `uv lock` fails.
    path = os.path.join(repo, "sdk", "pkg_a", "pyproject.toml")
    with open(path) as handle:
        text = handle.read()
    assert "dependencies = []" in text
    write(
        path, text.replace("dependencies = []", 'dependencies = ["no-such-dist-xyz"]')
    )
    result = run(["bash", SCRIPT, "pkg_a"], repo)
    assert result.returncode != 0, (
        f"exit 0\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "broken_consumer" in result.stderr, result.stderr


# AC5
def test_leaves_untracked_lock_untouched():
    fixture = release()
    fixture.assert_succeeded()
    assert read_bytes(fixture.lock("scratch")) == fixture.before["scratch"]
    assert "scratch/uv.lock" not in fixture.stdout_lines, fixture.result.stdout


def main():
    tests = [
        value for name, value in sorted(globals().items()) if name.startswith("test_")
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
        else:
            print(f"ok   {test.__name__}")
    print(f"{len(tests) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
