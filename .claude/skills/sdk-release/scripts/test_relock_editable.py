#!/usr/bin/env python3
"""Tests for relock-editable.sh: after an SDK version bump, every git-tracked uv.lock that installs the
SDK editable is relocked to the new version, and no other lock is touched.

Run with `python3 test_relock_editable.py` (or pytest). Stdlib only; each fixture is a temp git repo with
path dependencies only, and every uv call runs with UV_OFFLINE=1, so no network is needed.
"""

import json
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


def toml_list(items):
    # A JSON string is a valid TOML basic string, quotes and backslashes escaped.
    return "[" + ", ".join(json.dumps(item) for item in items) + "]"


def sdk_package(repo, package, version, extras=()):
    # No [build-system]: the metadata is static, so locking an editable path dependency on it needs no
    # build backend and works offline. Each extra maps to no dependencies.
    text = (
        f'[project]\nname = "{package.replace("_", "-")}"\nversion = "{version}"\n'
        'requires-python = ">=3.8"\ndependencies = []\n'
    )
    if extras:
        text += "\n[project.optional-dependencies]\n" + "".join(
            f"{extra} = []\n" for extra in extras
        )
    write(os.path.join(repo, "sdk", package, "pyproject.toml"), text)


def consumer(
    repo,
    name,
    requirements=(),
    sources=(),
    *,
    optional=None,
    groups=None,
    editable=True,
):
    """Writes and locks <repo>/<name>. `optional` and `groups` map an extra or dependency-group name
    to its requirement list; `editable=False` makes every path source non-editable."""
    text = (
        f'[project]\nname = "{name.replace("_", "-")}"\nversion = "0.1.0"\n'
        f'requires-python = ">=3.8"\ndependencies = {toml_list(requirements)}\n'
    )
    if optional:
        text += "\n[project.optional-dependencies]\n" + "".join(
            f"{extra} = {toml_list(reqs)}\n" for extra, reqs in optional.items()
        )
    if groups:
        text += "\n[dependency-groups]\n" + "".join(
            f"{group} = {toml_list(reqs)}\n" for group, reqs in groups.items()
        )
    if sources:
        flag = "true" if editable else "false"
        text += "\n[tool.uv.sources]\n" + "".join(
            f'{package.replace("_", "-")} = {{ path = "../sdk/{package}", editable = {flag} }}\n'
            for package in sources
        )
    write(os.path.join(repo, name, "pyproject.toml"), text)
    check(["uv", "--directory", os.path.join(repo, name), "lock"], repo)


def has_editable_entry(lock_path, dist):
    with open(lock_path, "rb") as handle:
        lock = tomllib.load(handle)
    return any(
        package["name"] == dist and "editable" in package.get("source", {})
        for package in lock.get("package", [])
    )


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


# Declared-range check: before any `uv lock`, every editable consumer's declared requirements on the
# package must admit the new version, because uv ignores a range on an editable path source.


class RangeRun:
    """One repo with sdk/pkg_a 1.0.0 and the given consumers (name -> consumer() keyword arguments),
    committed, then pkg_a bumped to `new` and `relock-editable.sh pkg_a` run once."""

    def __init__(self, prefix, consumers, new="1.1.0", extras=()):
        self.repo = init_repo(f"relock-range-{prefix}-")
        sdk_package(self.repo, "pkg_a", "1.0.0", extras=extras)
        for name, kwargs in consumers.items():
            consumer(self.repo, name, **kwargs)
            assert locked_version(self.lock(name), "pkg-a") == "1.0.0", name
        commit_all(self.repo)
        self.before = {name: read_bytes(self.lock(name)) for name in consumers}
        bump(self.repo, "pkg_a", "1.0.0", new)
        self.result = run(["bash", SCRIPT, "pkg_a"], self.repo)

    def lock(self, name):
        return os.path.join(self.repo, name, "uv.lock")

    def report(self):
        return (
            f"exit {self.result.returncode}\nstdout:\n{self.result.stdout}\n"
            f"stderr:\n{self.result.stderr}"
        )

    def assert_succeeded(self):
        assert self.result.returncode == 0, self.report()

    def assert_stopped_naming(self, *dirs):
        assert self.result.returncode != 0, self.report()
        for name in dirs:
            assert f"range check failed in {name}:" in self.result.stderr, self.report()


def editable(*requirements, **kwargs):
    """consumer() arguments for a project requiring `requirements`, with pkg_a as a path source."""
    return dict(requirements=list(requirements), sources=["pkg_a"], **kwargs)


OK = editable("pkg-a>=1.0.0,<2")


# Range AC1
def test_range_admitting_new_version_relocks():
    fixture = RangeRun("ok", {"ok": OK})
    fixture.assert_succeeded()
    assert locked_version(fixture.lock("ok"), "pkg-a") == "1.1.0"


# Range AC2
def test_range_excluding_new_version_stops_before_any_relock():
    fixture = RangeRun("pinned", {"ok": OK, "pinned": editable("pkg-a>=1.0.0,<1.1")})
    fixture.assert_stopped_naming("pinned")
    assert "<1.1" in fixture.result.stderr, fixture.report()
    assert "1.1.0" in fixture.result.stderr, fixture.report()
    assert fixture.result.stdout == "", fixture.report()
    for name in ("ok", "pinned"):
        assert read_bytes(fixture.lock(name)) == fixture.before[name], name


# Range AC3
def test_range_check_reports_every_excluding_project():
    fixture = RangeRun(
        "two",
        {
            "pinned": editable("pkg-a>=1.0.0,<1.1"),
            "pinned2": editable("pkg-a<1.1"),
        },
    )
    fixture.assert_stopped_naming("pinned", "pinned2")


# Range AC4
def test_range_bare_requirement_relocks():
    fixture = RangeRun("bare", {"bare": editable("pkg-a")})
    fixture.assert_succeeded()
    assert locked_version(fixture.lock("bare"), "pkg-a") == "1.1.0"


# Range AC5
def test_range_check_normalizes_name_and_drops_extras_and_markers():
    fixture = RangeRun(
        "extras",
        {"x": editable('PKG_A[extra]>=1,<1.1 ; python_version >= "3.8"')},
        extras=("extra",),
    )
    fixture.assert_stopped_naming("x")


# Range AC6
def test_range_not_equal_new_version_stops():
    fixture = RangeRun("ne", {"ne": editable("pkg-a!=1.1.0")})
    fixture.assert_stopped_naming("ne")


# Range AC6
def test_range_exact_pin_to_old_version_stops():
    fixture = RangeRun("eq", {"eq": editable("pkg-a==1.0.0")})
    fixture.assert_stopped_naming("eq")


# Range AC7
def test_range_unsupported_operator_stops_as_uncheckable():
    fixture = RangeRun("tilde", {"tilde": editable("pkg-a~=1.0")})
    fixture.assert_stopped_naming("tilde")
    assert "cannot check" in fixture.result.stderr, fixture.report()


# Range AC8
def test_range_in_dependency_group_is_checked():
    fixture = RangeRun("grp", {"grp": editable("pkg-a", groups={"dev": ["pkg-a<1.1"]})})
    fixture.assert_stopped_naming("grp")


# Range AC9
def test_range_check_refuses_pre_release_version():
    fixture = RangeRun("rc", {"ok": OK}, new="1.1.0rc1")
    assert fixture.result.returncode != 0, fixture.report()
    assert "cannot check a pre-release version" in fixture.result.stderr, (
        fixture.report()
    )


# Range AC10
def test_range_of_non_editable_consumer_is_not_checked():
    fixture = RangeRun(
        "remote",
        {"remote": editable("pkg-a<1.1", editable=False)},
    )
    assert not has_editable_entry(fixture.lock("remote"), "pkg-a")
    fixture.assert_succeeded()
    assert read_bytes(fixture.lock("remote")) == fixture.before["remote"]


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
