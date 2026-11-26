#!/usr/bin/env python3
"""Checks that a project's declared requirements on a package admit a release version.

Usage: declared_range.py PYPROJECT DIST VERSION

uv ignores the version range of a requirement whose source is an editable path, so `uv lock` relocks past
a range that excludes the new version. This script reads every requirement on DIST in PYPROJECT
(`[project].dependencies`, `[project.optional-dependencies]`, `[dependency-groups]`) and checks each
against VERSION, a plain release number such as `6.0.0`.

Exit 0: every matching requirement admits VERSION, or none declares a range (prints nothing).
Exit 1: one stderr line per failing requirement, "<requirement> excludes <VERSION>" or
        "cannot check <requirement>: <reason>" (also when VERSION itself is not a plain release number).
Exit 2: wrong arguments, or PYPROJECT missing, unreadable or not valid TOML.
"""

import operator
import re
import sys
import tomllib

PLAIN_VERSION = re.compile(r"\d+(\.\d+)*")
REQUIREMENT = re.compile(
    r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(.*)", re.DOTALL
)
CLAUSE = re.compile(r"(>=|<=|==|!=|>|<)\s*([0-9]\S*)")
OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
}


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def to_tuple(version):
    return tuple(int(part) for part in version.split("."))


def compare(op, left, right):
    """Compares release tuples, padding the shorter one with zeros."""
    size = max(len(left), len(right))
    left += (0,) * (size - len(left))
    right += (0,) * (size - len(right))
    return OPERATORS[op](left, right)


def requirement_strings(data):
    """Yields every string requirement in the three dependency tables."""
    project = data.get("project", {})
    lists = [project.get("dependencies", [])]
    lists += project.get("optional-dependencies", {}).values()
    lists += data.get("dependency-groups", {}).values()
    for items in lists:
        yield from (item.strip() for item in items if isinstance(item, str))


def parse(requirement):
    """Returns (normalized name, specifier text) without extras and marker, or None if unparseable."""
    match = REQUIREMENT.fullmatch(requirement.split(";", 1)[0].strip())
    if not match:
        return None
    specifier = match.group(3).strip()
    if specifier.startswith("(") and specifier.endswith(")"):
        specifier = specifier[1:-1].strip()
    return normalize(match.group(1)), specifier


def judge(requirement, specifier, version):
    """Returns None when the specifier admits version, else the stderr line saying why not."""
    if not specifier or specifier.startswith("@"):
        return None
    target = to_tuple(version)
    for text in (part.strip() for part in specifier.split(",")):
        clause = CLAUSE.fullmatch(text)
        if not clause:
            op = re.match(r"[<>=!~]+", text)
            reason = f"unsupported operator {op.group(0)}" if op else "unparseable"
            return f"cannot check {requirement}: {reason}"
        op, number = clause.groups()
        if not PLAIN_VERSION.fullmatch(number):
            return f"cannot check {requirement}: unsupported version {number}"
        if not compare(op, target, to_tuple(number)):
            return f"{requirement} excludes {version}"
    return None


def problems(data, dist, version):
    """Yields one line per requirement on dist that excludes or cannot be checked against version."""
    for requirement in requirement_strings(data):
        parsed = parse(requirement)
        if parsed and parsed[0] == dist:
            line = judge(requirement, parsed[1], version)
            if line:
                yield line


def main(argv):
    if len(argv) != 4:
        print("usage: declared_range.py PYPROJECT DIST VERSION", file=sys.stderr)
        return 2
    path, dist, version = argv[1:]
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2
    if not PLAIN_VERSION.fullmatch(version):
        print(f"cannot check a pre-release version: {version}", file=sys.stderr)
        return 1
    found = list(problems(data, normalize(dist), version))
    for line in found:
        print(line, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
