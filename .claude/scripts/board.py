#!/usr/bin/env python3
"""Coordination board helper: a folder of small markdown files that parallel Claude Code
sessions (one per wave branch / git worktree) use to coordinate.

Layout: ``<root>/<repo>/<name>.md``. The root is ``~/.claude/coordination/`` unless the
``CLAUDE_COORDINATION_DIR`` environment variable overrides it. The repo folder is named after
the directory that contains the git common dir, so every worktree of a repo shares one folder.

Each entry has a front matter block (``key: value`` lines between two ``---`` lines) and an
optional markdown body. Values are scalar strings or flow lists ``[a, b]``.

Stdlib only; usable as a CLI (``board.py --help``) and as a module by the coordination hooks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time

KINDS = ("plan", "hold", "request", "notice", "lock")
INBOX_KINDS = ("request", "notice")
LOCK_MAX_AGE = dt.timedelta(hours=2)


class BoardError(Exception):
    """A user-facing failure; the CLI prints it to stderr and exits 1."""


# --------------------------------------------------------------------------- paths


def board_root() -> str:
    override = os.environ.get("CLAUDE_COORDINATION_DIR")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(os.path.expanduser("~"), ".claude", "coordination")


def _git(path: str, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", path, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def repo_name(path: str | None = None) -> str | None:
    """Board folder name for the repo containing PATH, or None outside git."""
    path = os.path.abspath(path or os.getcwd())
    common = _git(path, "rev-parse", "--git-common-dir")
    if not common:
        return None
    common = os.path.abspath(os.path.join(path, common))
    return os.path.basename(os.path.dirname(common))


def wave_key_from_branch(branch: str | None) -> str:
    match = re.match(r"^wave-([^-\s]+)(?:-|$)", branch or "")
    return "wave-" + match.group(1) if match else ""


def wave_key(path: str | None = None) -> str:
    """Wave key of the branch checked out at PATH ('' if it is not a wave branch)."""
    path = os.path.abspath(path or os.getcwd())
    return wave_key_from_branch(_git(path, "branch", "--show-current"))


def parse_wave_ref(value: str) -> tuple[str, str]:
    """'<repo> / wave-12-slug' -> ('<repo>', 'wave-12'); whitespace-insensitive."""
    repo, _, wave = value.partition("/")
    if not wave:
        repo, wave = "", repo
    match = re.match(r"wave-([^-\s]+)", wave.strip())
    return repo.strip(), ("wave-" + match.group(1) if match else wave.strip())


def wave_matches(value: str, repo: str, key: str) -> bool:
    if not key:
        return False
    ref_repo, ref_key = parse_wave_ref(value)
    return ref_repo == repo and ref_key == key


# --------------------------------------------------------------------------- entries


class Entry:
    def __init__(self, repo: str, name: str, path: str, fields: dict, body: str):
        self.repo = repo
        self.name = name
        self.path = path
        self.fields = fields
        self.body = body

    @property
    def kind(self) -> str:
        return str(self.fields.get("kind", ""))

    def get(self, key: str, default: str = "") -> str:
        value = self.fields.get(key, default)
        return ", ".join(value) if isinstance(value, list) else str(value)


def _parse_value(raw: str):
    raw = re.sub(r"\s+#.*$", "", raw.strip()).strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [item.strip() for item in inner.split(",") if item.strip()]
    return raw


def _format_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


def parse_text(text: str) -> tuple[dict, str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    fields: dict = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n" + "\n".join(lines[i + 1 :])
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = _parse_value(value)
    raise BoardError("front matter has no closing '---'")


def render(fields: dict, body: str) -> str:
    head = "".join(f"{k}: {_format_value(v)}\n" for k, v in fields.items())
    return "---\n" + head + "---" + (body if body else "\n")


def _write_atomic(path: str, text: str) -> None:
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def repo_dir(repo: str) -> str:
    return os.path.join(board_root(), repo)


def read_entry(repo: str, name: str) -> Entry:
    path = os.path.join(repo_dir(repo), name + ".md")
    try:
        with open(path) as handle:
            text = handle.read()
    except FileNotFoundError:
        raise BoardError(f"no such entry: {repo}/{name}") from None
    fields, body = parse_text(text)
    return Entry(repo, name, path, fields, body)


def entries(repo: str) -> list[Entry]:
    folder = repo_dir(repo)
    if not os.path.isdir(folder):
        return []
    found = []
    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".md") and not filename.startswith("."):
            found.append(read_entry(repo, filename[:-3]))
    return found


def inbox_entries(repo: str) -> list[Entry]:
    return [e for e in entries(repo) if e.kind in INBOX_KINDS]


def all_repos() -> list[str]:
    root = board_root()
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


def _today(now: dt.datetime | None) -> dt.date:
    return (now or dt.datetime.now()).date()


def _parse_dt(value: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def is_stale(entry: Entry, now: dt.datetime | None = None) -> bool:
    now = now or dt.datetime.now()
    if entry.kind == "lock":
        created = _parse_dt(entry.get("created"))
        return created is not None and now - created > LOCK_MAX_AGE
    if entry.kind in ("hold", "plan", "request", "notice"):
        expires = entry.get("expires")
        try:
            return bool(expires) and dt.date.fromisoformat(expires) < _today(now)
        except ValueError:
            return False
    return False


def _lock_filename(dataset: str | None) -> str:
    return f"lock-dataset-{dataset}" if dataset else "lock"


def lock_holder(repo: str, dataset: str | None = None) -> Entry | None:
    try:
        return read_entry(repo, _lock_filename(dataset))
    except BoardError:
        return None


def dataset_locks(repo: str) -> list[Entry]:
    return [e for e in entries(repo) if e.name.startswith("lock-dataset-")]


def open_merge_holds_for(repo: str, key: str) -> list[Entry]:
    return [
        e
        for e in entries(repo)
        if e.kind == "hold"
        and e.get("status", "open") == "open"
        and e.get("blocks") == "merge"
        and wave_matches(e.get("waiting"), repo, key)
    ]


def summary(entry: Entry) -> str:
    kind = entry.kind
    if kind == "hold":
        return (
            f"{entry.get('waiting')} waits on {entry.get('on')}: "
            f"{entry.get('condition')} [blocks {entry.get('blocks')}]"
        )
    if kind == "plan":
        title = f'"{entry.get("title")}" ' if entry.get("title") else ""
        return f"{title}{entry.get('wave')} {entry.get('mode')} integration={entry.get('integration')}"
    if kind == "lock":
        return f"held by {entry.get('wave')} since {entry.get('created')}"
    first = next((ln.strip() for ln in entry.body.splitlines() if ln.strip()), "")
    fallback = entry.get("summary") or first
    if kind == "request":
        need = entry.get("need")
        if not need:
            return fallback
        sender = entry.get("from")
        return f"from {sender}: {need}" if sender else need
    if kind == "notice":
        return entry.get("text") or fallback
    return fallback


def format_line(entry: Entry, now: dt.datetime | None = None) -> str:
    stale = "  STALE" if is_stale(entry, now) else ""
    return (
        f"{entry.repo}/{entry.name}  kind={entry.kind}  "
        f"status={entry.get('status', '-')}  {summary(entry)}{stale}"
    )


def age_text(entry: Entry) -> str:
    created = _parse_dt(entry.get("created"))
    if created is None:
        return "unknown age"
    minutes = int((dt.datetime.now() - created).total_seconds() // 60)
    return f"{minutes} min ago"


# --------------------------------------------------------------------------- CLI


def _split_ref(ref: str) -> tuple[str, str]:
    repo, sep, name = ref.partition("/")
    if not sep or not repo or not name:
        raise BoardError(f"expected REPO/NAME, got {ref!r}")
    return repo, name


def _parse_pairs(pairs: list[str]) -> dict:
    fields = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise BoardError(f"expected key=value, got {pair!r}")
        fields[key.strip()] = _parse_value(value)
    return fields


def _read_file(path: str) -> str:
    with open(path) as handle:
        return handle.read()


def _qualify_wave(wave: str, repo: str) -> str:
    ref_repo, key = parse_wave_ref(wave)
    return f"{ref_repo or repo} / {key}"


def cmd_repo(args) -> int:
    name = repo_name(args.path)
    if name is None:
        print("not inside a git repository", file=sys.stderr)
        return 1
    print(name)
    return 0


def cmd_wave(args) -> int:
    print(wave_key(args.path))
    return 0


def cmd_list(args) -> int:
    for repo in [args.repo] if args.repo else all_repos():
        for entry in entries(repo):
            if args.kind and entry.kind != args.kind:
                continue
            if args.status and entry.get("status") != args.status:
                continue
            print(format_line(entry))
    return 0


def cmd_file(args) -> int:
    if args.kind not in KINDS:
        raise BoardError(f"unknown kind {args.kind!r}; one of {', '.join(KINDS)}")
    if "/" in args.name:
        raise BoardError("NAME must not contain '/'")
    path = os.path.join(repo_dir(args.repo), args.name + ".md")
    if os.path.exists(path):
        raise BoardError(f"{args.repo}/{args.name} already exists")
    fields = {"kind": args.kind}
    fields.update(_parse_pairs(args.pairs))
    fields.setdefault("created", dt.date.today().isoformat())
    body = "\n" + _read_file(args.body_file) if args.body_file else "\n"
    _write_atomic(path, render(fields, body))
    print(f"filed {args.repo}/{args.name}")
    return 0


def cmd_set(args) -> int:
    repo, name = _split_ref(args.ref)
    entry = read_entry(repo, name)
    entry.fields.update(_parse_pairs(args.pairs))
    body = entry.body
    if args.append_body_file:
        body = body.rstrip("\n") + "\n\n" + _read_file(args.append_body_file)
        if not body.endswith("\n"):
            body += "\n"
    _write_atomic(entry.path, render(entry.fields, body))
    return 0


def cmd_show(args) -> int:
    repo, name = _split_ref(args.ref)
    with open(read_entry(repo, name).path) as handle:
        sys.stdout.write(handle.read())
    return 0


def cmd_rm(args) -> int:
    repo, name = _split_ref(args.ref)
    os.unlink(read_entry(repo, name).path)
    return 0


def cmd_satisfy(args) -> int:
    repo, name = _split_ref(args.ref)
    entry = read_entry(repo, name)
    if entry.kind != "hold":
        raise BoardError(f"{args.ref} is a {entry.kind}, not a hold")
    entry.fields["status"] = "satisfied"
    _write_atomic(entry.path, render(entry.fields, entry.body))
    return 0


def cmd_lock(args) -> int:
    wave = _qualify_wave(args.wave, args.repo)
    holder = lock_holder(args.repo, args.dataset)
    if holder is not None:
        if parse_wave_ref(holder.get("wave")) == parse_wave_ref(wave):
            return 0
        print(f"held by {holder.get('wave')} ({age_text(holder)})", file=sys.stderr)
        print(f"held by {holder.get('wave')} ({age_text(holder)})")
        return 1
    fields = {"kind": "lock", "wave": wave}
    if args.dataset:
        fields["dataset"] = args.dataset
    fields["created"] = dt.datetime.now().isoformat(timespec="seconds")
    target = os.path.join(repo_dir(args.repo), _lock_filename(args.dataset) + ".md")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(render(fields, "\n"))
        try:
            os.link(tmp, target)  # atomic, fails if the lock already exists
        except FileExistsError:
            holder = lock_holder(args.repo, args.dataset)
            who = holder.get("wave") if holder else "another wave"
            print(f"held by {who}", file=sys.stderr)
            print(f"held by {who}")
            return 1
    finally:
        os.unlink(tmp)
    return 0


def cmd_unlock(args) -> int:
    wave = _qualify_wave(args.wave, args.repo)
    holder = lock_holder(args.repo, args.dataset)
    if holder is None:
        return 0
    if parse_wave_ref(holder.get("wave")) != parse_wave_ref(wave):
        print(f"lock is held by {holder.get('wave')}, not {wave}", file=sys.stderr)
        return 1
    os.unlink(holder.path)
    return 0


WATCH_STATE = ".watch-for-work.json"


def _watch_scan(state: dict | None) -> tuple[dict, list[str]]:
    """Scan the board against ``state``; return the new state and the event lines."""
    first = state is None
    state = state or {}
    new: dict = {}
    events: list[str] = []
    for repo in all_repos():
        folder = repo_dir(repo)
        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".md") or filename.startswith("."):
                continue
            name = filename[:-3]
            key = f"{repo}/{name}"
            try:
                mtime_ns = os.stat(os.path.join(folder, filename)).st_mtime_ns
            except OSError:
                continue
            old = state.get(key)
            if old is not None and old.get("mtime_ns") == mtime_ns:
                new[key] = old
                continue
            try:
                entry = read_entry(repo, name)
            except (BoardError, UnicodeDecodeError) as exc:
                new[key] = {"mtime_ns": mtime_ns, "kind": "", "status": ""}
                events.append(f"board: unreadable {key}: {exc}")
                continue
            kind = entry.fields.get("kind", "")
            status = entry.fields.get("status", "")
            new[key] = {"mtime_ns": mtime_ns, "kind": kind, "status": status}
            old_status = old.get("status") if old else None
            if (
                kind == "plan"
                and entry.fields.get("mode") == "batch"
                and status in ("ready", "interrupted")
                and old_status != status
            ):
                events.append(f"work: plan {format_line(entry)}")
            elif kind == "hold" and status == "satisfied" and old_status != status:
                events.append(f"work: hold {format_line(entry)}")
    for key, old in state.items():
        if (
            key not in new
            and old.get("kind") == "hold"
            and old.get("status") != "satisfied"
        ):
            events.append(f"work: hold removed {key}")
    return new, ([] if first else events)


def cmd_watch_for_work(args) -> int:
    path = os.path.join(board_root(), WATCH_STATE)
    try:
        with open(path) as handle:
            state = json.load(handle)
    except FileNotFoundError:
        state = None
    except (OSError, ValueError) as exc:
        # Changes since the last scan are unknown: make the reader re-read the whole board.
        print(f"work: watch state reset, re-read the board ({path}: {exc})", flush=True)
        state = None
    try:
        while True:
            state, events = _watch_scan(state)
            for line in events:
                print(line, flush=True)
            _write_atomic(path, json.dumps(state))
            if args.once:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0


def cmd_inbox(args) -> int:
    for repo in [args.repo] if args.repo else all_repos():
        for entry in inbox_entries(repo):
            print(format_line(entry))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("repo", help="board folder name for a path")
    p.add_argument("path", nargs="?")
    p.set_defaults(func=cmd_repo)

    p = sub.add_parser("wave", help="wave key of the current branch")
    p.add_argument("path", nargs="?")
    p.set_defaults(func=cmd_wave)

    p = sub.add_parser("list", help="one line per entry")
    p.add_argument("--repo")
    p.add_argument("--kind")
    p.add_argument("--status")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("inbox", help="requests and notices: the repos' inbox")
    p.add_argument("--repo")
    p.set_defaults(func=cmd_inbox)

    p = sub.add_parser("file", help="create an entry")
    p.add_argument("kind")
    p.add_argument("name")
    p.add_argument("--repo", required=True)
    p.add_argument("--body-file")
    p.add_argument("pairs", nargs="*", metavar="key=value")
    p.set_defaults(func=cmd_file)

    p = sub.add_parser("set", help="update fields of an entry")
    p.add_argument("ref", metavar="REPO/NAME")
    p.add_argument("--append-body-file")
    p.add_argument("pairs", nargs="*", metavar="key=value")
    p.set_defaults(func=cmd_set)

    for name, func in (("show", cmd_show), ("rm", cmd_rm), ("satisfy", cmd_satisfy)):
        p = sub.add_parser(name)
        p.add_argument("ref", metavar="REPO/NAME")
        p.set_defaults(func=func)

    for name, func in (("lock", cmd_lock), ("unlock", cmd_unlock)):
        p = sub.add_parser(name)
        p.add_argument("repo")
        p.add_argument("--wave", required=True)
        p.add_argument("--dataset")
        p.set_defaults(func=func)

    p = sub.add_parser(
        "watch-for-work",
        help="print board changes that can give the coordinator work (new ready batch plans, "
        "satisfied or removed holds)",
    )
    p.add_argument("--interval", type=float, default=5.0, help="seconds between scans")
    p.add_argument("--once", action="store_true", help="scan once and exit")
    p.set_defaults(func=cmd_watch_for_work)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, rest = parser.parse_known_args(argv)
    # Python 3.9 argparse leaves key=value tokens after an option unparsed.
    if args.command in ("file", "set"):
        args.pairs.extend(token for token in rest if "=" in token)
        rest = [token for token in rest if "=" not in token]
    if rest:
        parser.error(f"unrecognized arguments: {' '.join(rest)}")
    if args.command in ("file", "set"):
        stray = [pair for pair in args.pairs if "=" not in pair]
        if stray:
            parser.error(f"unrecognized arguments: {' '.join(stray)}")
    try:
        return args.func(args)
    except (BoardError, OSError) as exc:
        print(f"board.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
