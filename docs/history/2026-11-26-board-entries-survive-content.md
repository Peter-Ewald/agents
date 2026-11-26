---
date: 2026-11-26
title: Board entries survive their content
outcome: completed
---

# Wave 07 (agents): Board entries survive their content

## Summary

| | |
|---|---|
| **Goal** | Whatever an agent files on the board comes back the same, and one broken entry file never hides the rest of the board. Serves the backlog entry *Board entries survive their content* (moved to Next Up for this wave). |
| **Kind** | Implementation (harness: `board.py` and the coordination hooks). |
| **Changes** | `board.py`: field values are stored and read exactly as written, and the board is read entry by entry, so a broken entry is skipped and named. Callers: the statusline, the inject hook and the guard hook. Docs: the board and hooks pages. |
| **Behaviour** | A `need=` or `text=` that contains ` #` or looks like `[a, b]` comes back unchanged. A value with a line break is refused when it is filed. A broken entry (no closing `---`, or not UTF-8) is named by `list`, `inbox`, the statusline and the inject hook, and everything else is still shown. The guard blocks integration in a repo whose board has a broken entry. |
| **Decisions** | D1 values are plain text, D2 refuse line breaks, D3 the guard blocks on a broken entry, D4 `list`/`inbox` exit 1 when they skipped an entry (see below). |
| **Risks and holds** | No holds. Touches only `agents`. A running wave's agent uses the board while this lands; the changes are compatible with every entry already on disk. |

## Context

`board.py` parses every front matter value through `_parse_value`, which treats ` #…` as a comment
and a value in `[…]` as a list. The same function runs when an entry is **filed** (`_parse_pairs`),
so `need=fix #42 soon` is stored as `need: fix`, with no warning. Only `holds`, `exclusive` and
`new_dependencies` are ever written as `[…]`, and no code reads them as a list: `Entry.get` joins them
back into a string. Nothing on the board relies on inline comments either: entries are written only by
`board.py` (`render`).

`entries(repo)` raises on the first unreadable file. `BoardError` covers a missing closing `---`; a
non-UTF-8 file raises `UnicodeDecodeError`, which only `_watch_scan` catches. Effects today:

| Reader | What happens on one broken entry |
|---|---|
| statusline (`blocked()`, `inbox()`) | `except Exception: return ""`: the blocked and inbox parts disappear for every repo, silently |
| `coordination-inject.py` outside a repo | Hook crashes: no board block at all |
| `board.py list` / `inbox` | Stops at the broken repo; a non-UTF-8 file gives a traceback (`main()` catches only `BoardError`, `OSError`) |
| `coordination-guard.py` | `main` raises, the hook fails open: the push goes through even past an open merge hold |
| `coordination-watch.py` | Catches `BoardError` only; a non-UTF-8 file crashes the hook |
| `watch-for-work` (`_watch_scan`) | Already reports `board: unreadable <ref>: <error>` once and goes on |

History: the *coordinator watches the board* plan (2026-11-17) introduced the `board: unreadable` line
for `watch-for-work`; this wave gives the other readers the same behaviour.

## Decisions

| # | Decision | Alternative | Why this one |
|---|---|---|---|
| D1 | Every field value is plain text, stored and read verbatim (stripped of surrounding spaces). No inline comments, no list parsing; `holds=[a, b]` is stored as the text `[a, b]`, as today on disk | Quote values on filing and unquote on reading | Nothing reads lists or comments, so removing both parsing rules is simpler than an escaping scheme, and every entry on disk reads the same as before |
| D2 | `file` and `set` refuse a value that contains a line break: exit 1, `board.py: value of <key> contains a line break; put longer text in the body (--body-file)`, nothing written | Fold line breaks into spaces | A front matter value is one line; refusing is loud and the agent retries. Folding would change the text silently |
| D3 | The guard blocks integrating to `main` and `eval-dataset push` (exit 2) while the repo's own board folder has an unreadable entry, naming it and how to fix it (`board.py show`/`rm`, or repair the file). A broken entry in another repo's folder does not block | Skip it like the other readers (the guard stays fail-open, as now) | An unreadable file may be a merge hold or a lock; skipping it would let a wave land past it. A broken entry is rare and the message says how to clear it |
| D4 | `board.py list` and `inbox` print every readable entry on stdout, one `board.py: unreadable <repo>/<name>: <reason>` line per broken entry on stderr, and exit 1 | Exit 0 with the warning | The output is complete either way; exit 1 makes a script or agent that checks the status notice the broken file |

## Contracts

`board.py` (module API; the hooks and statusline import it):

- `_parse_value(raw) -> str`: `raw.strip()`. Used for reading and filing. `_format_value` and the list
  branch in `Entry.get` go.
- `_parse_pairs` raises `BoardError(f"value of {key} contains a line break; put longer text in the body (--body-file)")`
  for a value containing `\n` or `\r`.
- `read_entry(repo, name)` raises `BoardError` for every unreadable entry, its message naming the entry:
  `<repo>/<name>: front matter has no closing '---'`, `<repo>/<name>: not UTF-8 (<detail>)`; missing
  stays `no such entry: <repo>/<name>`.
- New `class Unreadable(NamedTuple): ref: str; reason: str` (`ref` is `<repo>/<name>`, `reason` the
  error text without the ref).
- New `read_board(repo) -> tuple[list[Entry], list[Unreadable]]`: reads every entry of the repo's folder,
  never raises for one entry.
- `entries(repo)` returns `read_board(repo)[0]` (skips unreadable entries). `inbox_entries`,
  `dataset_locks`, `open_merge_holds_for` keep their signatures.
- `cmd_list`, `cmd_inbox`: D4. `_watch_scan` catches `BoardError` only (the decode error is now one).

Callers:

- `statusline.py`: a new part after the inbox part, `⚠ board unreadable: <ref>[, +N]` (first ref shown,
  the rest counted); the blocked and inbox parts use `entries` and keep working.
- `coordination-inject.py`: per repo, after its entry lines, one line `unreadable: <ref>: <reason>` per
  broken entry; a repo with only broken entries still gets its block.
- `coordination-guard.py` `check()`: for `merge` and `dataset`, if `read_board(repo)` names any
  unreadable entry, return `coordination: unreadable board entry <folder><name>.md (<reason>); repair or remove it (board.py rm <repo>/<name>) before integrating.`
- `coordination-watch.py`: unchanged code; it now gets `BoardError` for both kinds of broken file.

## Acceptance cases

All unit tests in `.claude/scripts/test_coordination.py`, run against a temp board (`CLAUDE_COORDINATION_DIR`).

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | `#` survives filing | empty board | `file request r --repo A "need=fix #42 soon"` | `show A/r` has `need: fix #42 soon`; `inbox --repo A` line ends `fix #42 soon` | unit |
| AC2 | Brackets stay text | empty board | `file notice n --repo A "text=[a, b]"`; `file plan p ... "holds=[a, b]"` | inbox line shows `[a, b]`; `show A/p` has `holds: [a, b]` | unit |
| AC3 | Line break refused | empty board, then a filed notice | `file` with a value containing `\n`; `set` with one | exit 1, stderr names the key and `--body-file`; no new file, existing file unchanged | unit |
| AC4 | No closing `---` named, rest shown | repo A: a good notice and `broken.md` without closing `---`; repo B: a good notice | `inbox` (all repos) and `list` | both good notices on stdout; stderr `board.py: unreadable A/broken: …closing '---'`; exit 1 | unit |
| AC5 | Non-UTF-8 named, no traceback | as AC4, `broken.md` holds bytes `\xff\xfe` | `inbox` and `list` | as AC4, reason says not UTF-8; no `Traceback` on stderr | unit |
| AC6 | Statusline keeps its parts | as AC4 plus a blocked plan in B | statusline runs | inbox part counts A 1 and B 1, blocked part names the plan, a part `⚠ board unreadable: A/broken` | unit |
| AC7 | Inject hook names it | as AC4, session cwd outside every repo | `coordination-inject.py` | blocks for A and B with their good lines; A's block has `unreadable: A/broken: …` | unit |
| AC8 | Guard blocks in its own repo only | wave worktree of repo A; A's folder has `broken.md` | `git push origin HEAD:main` through the guard | exit 2, message names `broken.md` and `board.py rm A/broken`; with the broken file in B's folder instead, exit 0 | unit |
| AC9 | `watch-for-work` on a non-UTF-8 entry | baseline taken | a non-UTF-8 `.md` appears; `--once` twice | first prints `board: unreadable` naming it, second nothing; exit 0 | unit |
| AC10 | Watch hook survives non-UTF-8 | session inside repo A, snapshot taken | a non-UTF-8 entry appears; hook runs | reports `added: A/broken`, exit 0 | unit |

The existing suite (including `test_set_preserves_body_and_order` with `holds: [a, b]` and
`test_watch_for_work_reports_unreadable_entry_once`) keeps passing unchanged.

## Sub-tasks

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| S0 | Tests first: AC1–AC10 | `.claude/scripts/test_coordination.py` | — | every new test fails for the reason its case states; existing tests pass | `test-author` (medium) |
| S1 | `board.py` per the contract | `.claude/scripts/board.py` | S0 | AC1–AC5, AC9 pass; full suite passes | medium |
| S2 | Callers per the contract | `.claude/statusline.py`, `.claude/hooks/coordination-inject.py`, `.claude/hooks/coordination-guard.py` | S0 (contract fixed, runs alongside S1) | AC6–AC8, AC10 pass once S1 is in; full suite passes | medium |
| S3 | Documentation upkeep | `docs/01-hooks.md` (inject row: unreadable line; guard: blocks on an unreadable entry in its repo, otherwise fails open; statusline section), `.claude/skills/wave/board.md` (a value is one line of text, taken verbatim; longer text goes in the body), `.claude/hooks/README.md` if it states either, `backlog.md` (remove the entry), `docs/history/` | S1, S2 | `doc-conventions` loaded; claims match the code | inline |

## Verification

- `python3 .claude/scripts/test_coordination.py` (the repo's suite; also run under `/usr/bin/python3`, 3.9, since the hooks run there).
- `ruff check .claude` and `ruff format --check .claude`.
- Smoke on a temp board: file a request with `need=fix #42 soon`, add a non-UTF-8 entry, run `board.py inbox`, the statusline and the inject hook by hand.

## Exit criteria

AC1–AC10 pass, the suite passes under both Pythons, lint clean, docs and backlog updated, plan archived.

## Board fields

`repo=agents wave=wave-07-board-entries-survive-content "title=Board entries survive their content" mode=batch status=ready integration=push approved=2026-11-26 expires=2026-12-10`. No holds, no exclusive resources, no new dependencies.
