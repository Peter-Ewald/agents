# Hooks

All hook scripts live in [`../.claude/hooks/`](../.claude/hooks/README.md) and are registered globally in
`~/.claude/settings.json`, which is why they need no per-repo distribution step — see
[`03-cross-repo-distribution.md`](03-cross-repo-distribution.md) for why that's different from skills and
subagents. Every script is a standalone Python 3 file with a `/usr/bin/python3` shebang (the system
interpreter, hardcoded rather than relying on `env`/`PATH`, since a hook can fire with whatever cwd or venv
happens to be active in the calling session) and can be tested directly by piping synthetic JSON to it on
stdin — the examples below do exactly that.

## `reinject-instructions.py`

**Events:** `PreCompact`, `SessionStart` (matcher: `compact`), and `PostToolUse` (matcher: `Edit|Write`,
filtered internally to `CLAUDE.md`/`instructions.md` only).

Concatenates `~/Projects/agents/CLAUDE.md` and `instructions.md` and returns them as
`hookSpecificOutput.additionalContext` (or `systemMessage` for `PreCompact`, which doesn't support
`hookSpecificOutput`), re-injecting the full instructions in two situations: around a compaction event
(the original reason this hook exists — it's undocumented whether Claude Code's own automatic
post-compaction re-injection of a project's root `CLAUDE.md` re-resolves an `@instructions.md` import or
just replays the literal line, so this hook makes that question irrelevant either way), and right after
`CLAUDE.md` or `instructions.md` is edited directly. The second case exists because these two files are
"always loaded" via the `@import` chain but never automatically re-read mid-session after a direct edit —
unlike a skill (fixed by "Skill freshness": invoke fresh via the Skill tool), there's no equivalent
re-invoke mechanism for the core convention files themselves. The `PostToolUse` branch checks
`event.tool_input.file_path` against both files' resolved absolute paths and silently no-ops for every
other file, in any repo.

```sh
echo '{"hook_event_name": "SessionStart"}' | ../.claude/hooks/reinject-instructions.py

# PostToolUse on the watched files — emits additionalContext
echo '{"hook_event_name": "PostToolUse", "tool_name": "Edit", "tool_input": {"file_path": "/Users/peter/Projects/agents/instructions.md"}}' \
  | ../.claude/hooks/reinject-instructions.py

# PostToolUse on anything else — silent no-op
echo '{"hook_event_name": "PostToolUse", "tool_name": "Edit", "tool_input": {"file_path": "/tmp/unrelated.py"}}' \
  | ../.claude/hooks/reinject-instructions.py; echo "exit: $?"
```

## `lint-changed-lines.py`

**Event:** `PostToolUse` (matcher: `Edit|Write`).

Runs `uvx ruff check` on a just-edited `.py` file and blocks (exit 2) only if a violation falls on a line
the edit actually touched — determined from `git diff -U0` against the file's last commit, or "every line"
if the file is untracked. Pre-existing violations elsewhere in the file are reported via
`additionalContext` but never block, since blocking on debt the edit didn't introduce would be disruptive
across repos with varying lint history. Uses `uvx ruff` rather than a bare `ruff` on `PATH` so it works
whether or not the target repo declares ruff as a dependency. Fails open (never blocks) if git or `uvx`
aren't available.

```sh
echo '{"tool_name": "Edit", "tool_input": {"file_path": "/path/to/file.py"}, "cwd": "/path/to/repo"}' \
  | ../.claude/hooks/lint-changed-lines.py; echo "exit: $?"
```

## `ruff-autofix.py`

**Event:** `PostToolUse` (matcher: `Edit|Write`).

Runs `uvx ruff check --fix` (safe fixes only — never `--unsafe-fixes`) then `uvx ruff format` on a
just-edited `.py` file, whole-file. Fix runs before format, not after: removing an unused import can
leave blank lines behind that only `ruff format` cleans up, so formatting first would leave that
cleanup stranded until the next edit (confirmed non-idempotent within one invocation during testing).
Whole-file rather than changed-lines-scoped because ruff has no partial-file/line-range autofix mode —
and safe fixes are safe precisely because they can't change program behavior, so whole-file scope costs
only extra diff noise, not correctness risk. Reports via `additionalContext` how many lines `ruff
format` touched and how many issues `--fix` resolved, so the agent (and eventually the human reviewer)
knows extra changes landed beyond the intended edit; stays silent if nothing changed. Never blocks
(always exits 0) — blocking stays `lint-changed-lines.py`'s job. Fails open if `uvx`/ruff are
unavailable.

Registered ahead of `lint-changed-lines.py` in `~/.claude/settings.json`'s `PostToolUse` → `Edit|Write`
array so its fixes land first — array order for hooks sharing a matcher is genuinely undocumented, but
`lint-changed-lines.py` re-derives everything fresh from disk on every run with no cached state, so run
order only affects how much friction an edit hits before landing a clean file, never whether a block
verdict was ever actually wrong.

```sh
echo '{"tool_name": "Edit", "tool_input": {"file_path": "/path/to/file.py"}}' \
  | ../.claude/hooks/ruff-autofix.py; echo "exit: $?"
```

## `limit-web-search.py`

**Events:** `UserPromptSubmit` and `SubagentStart` (mode `reset`); `PreToolUse`, matcher `WebSearch`
(mode `check`).

Caps `WebSearch` calls at 10 per **round** (see [glossary](glossary.md#round)) for both the main agent and
subagents. `reset` zeroes a per-session-per-agent counter file at the start of a round; `check` increments
it and hard-blocks (exit 2) the 11th call, asking the agent to report back rather than keep searching —
this was written after an unbounded web-search loop burned a large amount of budget in one sitting.
Deliberately scoped to `WebSearch` only, not `WebFetch`.

```sh
echo '{"session_id": "s1", "agent_id": "main"}' | ../.claude/hooks/limit-web-search.py reset
echo '{"session_id": "s1", "agent_id": "main", "tool_name": "WebSearch"}' \
  | ../.claude/hooks/limit-web-search.py check; echo "exit: $?"
```

## `flag-new-dependency.py`

**Event:** `PreToolUse` (matcher: `Edit|Write`).

Blocks (exit 2) an edit to `pyproject.toml`, `package.json`, or `requirements*.txt` if it introduces a
dependency name that wasn't there before — a version-only change to an existing dependency does not block.
Heuristic rather than a full parser: regex-based for `pyproject.toml`'s `[project] dependencies = [...]`
shape and for `requirements*.txt`; real JSON parsing for `package.json`. A missed edge case just means the
addition goes unflagged, same as before this hook existed — it isn't the only safety net.

## `require-changelog-before-commit.py`

**Event:** `PreToolUse` (matcher: `Bash`).

Blocks (exit 2) a `git commit` if a staged `pyproject.toml` shows a version bump but the matching
`CHANGELOG.md` in the same package directory isn't also staged. Enforces changelog-before-release ordering
mechanically instead of relying on remembering to write the changelog first.

The check runs in the repo each `git commit` in the command targets: the directory after a
`cd <repo> &&`, or the one given by `git -C <repo>`, and the session's start folder otherwise. This
matters in a session started in `~/Projects`, which is not a repo. A failure to read the staged files
prints one line to stderr and never blocks the commit. The command parsing
(`segments_with_directory`, `git_target`) lives in
[`../.claude/scripts/shell_command.py`](../.claude/scripts/shell_command.py), which
`coordination-guard.py` and `keep-working-directory.py` share.

## `keep-working-directory.py`

**Event:** `PreToolUse` (matcher: `Bash`).

In the main session a `cd` at the top level of a Bash command carries over to every later command, and
path-scoped skills are matched against that working directory: `doc-conventions` (`paths: ["**/*.md"]`)
stops loading for markdown outside it. A session started in `~/Projects` that drifted into one repo
silently loses it for every other repo, without any error to notice.

The hook blocks (exit 2) a command whose top-level `cd` or `pushd` would leave the session anywhere other
than where it is now, the session's start folder (`CLAUDE_PROJECT_DIR`) or the root of a worktree
`<repo>/.claude/worktrees/<name>`, where the `wave` skill moves on purpose. It also blocks a top-level
`popd`, `cd -` or `cd $VAR`, whose target it cannot check. The block message names the alternatives:
`git -C`, absolute paths, a tool's own directory option, or a subshell `( cd <dir> && … )`. A `cd` inside
`( … )` or `$( … )` and every subagent command (the event carries `agent_id`; a subagent's `cd` does not
carry over) always pass. The parsing (`persistent_directory`) lives in `shell_command.py`; it respects
quoting but not heredoc bodies, so a heredoc line starting with `cd` can block wrongly. An internal error
prints one line to stderr and never blocks.

```sh
echo '{"tool_name": "Bash", "tool_input": {"command": "cd ~/Projects/agents && git status"}, "cwd": "'$HOME'/Projects"}' \
  | CLAUDE_PROJECT_DIR=$HOME/Projects ../.claude/hooks/keep-working-directory.py; echo "exit: $?"
```

## `validate_excalidraw_bindings.py`

**Event:** `PostToolUse` (matcher: `Edit|Write`).

Blocks (exit 2) a Write/Edit to any `.excalidraw` file, in any repo, if its native bindings are broken: an
arrow's `startBinding`/`endBinding` missing or not reciprocated by the target element's `boundElements`, a
bound text's `containerId` not reciprocated, or a `groupIds` entry used by only one element. No-ops on
anything that isn't an `Edit`/`Write` to a `.excalidraw` file. Registered globally rather than per-repo
because the check is entirely generic — no dependency on any repo's brand or theme conventions. The
authoritative copy (with its own test suite) lives in the "Agent Toolkit for Presentations and Visuals"
repo's `.claude/hooks/validate_excalidraw_bindings.py`, alongside the `diagram-excalidraw` skill it backs
up; this copy is kept in sync with that one by hand.

```sh
echo '{"tool_name": "Write", "tool_input": {"file_path": "/path/to/diagram.excalidraw"}}' \
  | ../.claude/hooks/validate_excalidraw_bindings.py; echo "exit: $?"
```

## `sync-main-at-start.py`

**Event:** `SessionStart` (matcher: `startup|resume|clear`; not `compact`, which starts no new work).

Waves land from their own worktrees, so a repo's main checkout (the folder `~/Projects/<repo>` itself)
does not move when `origin/main` does, and a session that reads `backlog.md` there would read an old
copy. This hook brings the main checkout of every active repo (the "Active" row of the roles table in
`instructions.md`) forward to `origin/main` before the session reads anything. It fetches all of them in
parallel and waits for the fetches, each capped at 8 s. It reports what moved or stayed behind as
context for the agent, one line per repo under `Main checkouts synced at session start:`, and is silent
when every repo was already up to date. Context repos are left out.

The work is done by [`../.claude/scripts/sync_main.py`](../.claude/scripts/sync_main.py), a stdlib
module and command line (`sync_main.py [--fetch-only] PATH...`) that the `wave` skill also runs before
a plan and after a merge. For each path it resolves the repo's main checkout (a worktree path works
too), runs `git fetch origin`, and runs `git merge --ff-only origin/main` only when the checkout is on
`main` and `main` has no commits `origin/main` lacks. It never stashes, resets, rebases or switches
branch, and it never touches a wave's worktree. Each path gives one line, `<repo>: <outcome>`: `up to
date`, `fast-forwarded 2 commits to <sha>`, `fetched` (with `--fetch-only`), or `not synced, <reason>`,
for example `checkout is on wave-12-x`, `main has 1 commit origin/main lacks`, `uncommitted changes in
the way (README.md)` or `fetch failed (timed out after 8 s)`. Its exit code is 0 whatever the outcome.

```sh
~/Projects/agents/.claude/scripts/sync_main.py ~/Projects/agents ~/Projects/Checkmate
echo '{"hook_event_name": "SessionStart"}' | CLAUDE_PROJECTS_DIR=/tmp/none ../.claude/hooks/sync-main-at-start.py
```

`CLAUDE_PROJECTS_DIR` overrides `~/Projects`, the folder that holds the repos and `agents/instructions.md`.

## Coordination board hooks

Parallel waves (one session or subagent per branch `wave-<NN>-<slug>`, each in its own git worktree)
coordinate through the **board**: a folder of small markdown files at `~/.claude/coordination/<repo>/`
(override with `CLAUDE_COORDINATION_DIR`). `<repo>` is the name of the directory holding the git common
dir, so every worktree of a repo shares one folder. An entry is front matter (`kind`, `created`,
`expires`, ...) plus an optional body; kinds are `plan`, `hold`, `request`, `notice`, `lock`.
[`../.claude/scripts/board.py`](../.claude/scripts/board.py) is the stdlib helper (CLI and module) that
reads and writes entries (`board.py --help`); the hooks import it. All three hooks stay silent when the
repo has no board folder.

| Hook | Event | What it does |
|---|---|---|
| `coordination-inject.py` | `SessionStart` | Injects the open entries, one line each, with a request's sender and need and a notice's text; expired entries and locks older than 2 hours are marked `STALE`, never deleted. Inside a repo it injects that repo's board. Outside a repo (a session started in `~/Projects`) it injects every repo's board as one `Coordination board for <repo>:` block per repo with open entries. When a shown entry is a request or notice, a last line points to `instructions.md`'s "A repo's inbox". Silent when nothing is open |
| `coordination-watch.py` | `PostToolUse` | Stats the board folder (state in `/tmp/claude-coordination-watch-<session_id>.json`) and reports added, changed or removed entries; silent on the first call and when nothing changed. Covers only a session inside a repo, and only after that session's own tool calls; the coordinator, which runs outside every repo and idles between events, uses `board.py watch-for-work` instead (see [05-parallel-waves.md](05-parallel-waves.md)) |
| `coordination-guard.py` | `PreToolUse` (matcher `Bash`) | Blocks (exit 2) integrating to main (`git push` to main, `az repos pr update --status completed`, an `az rest` PATCH on `.../pullrequests/<id>` whose body completes the PR or cannot be read yet, `gh pr merge`) while an open `blocks: merge` hold names this wave as waiting or `lock.md` is held by another wave, and blocks `eval-dataset push` / `push-all` while the matching `lock-dataset-<D>.md` is held by another wave |

`guard` fails open: an internal error is printed to stderr and the command proceeds. It parses the command with
[`../.claude/scripts/shell_command.py`](../.claude/scripts/shell_command.py), the module the changelog hook shares.

[`../.claude/scripts/new-wave-worktree.sh`](../.claude/scripts/new-wave-worktree.sh) `REPO_PATH BRANCH`
creates (or resumes) the worktree `<main checkout>/.claude/worktrees/<BRANCH>` from `origin/main`, copies
the untracked files listed in the main checkout's `.worktreeinclude` (such as `.env`) and the main
checkout's untracked `.claude/rules/*.md` (a personal `integration.md`, whether or not listed), and ensures
`docs/history/index.md merge=union` is in the repo's `info/attributes`. It prints the worktree path as its
last line. `python3 .claude/scripts/test_coordination.py` smoke-tests the board, the three hooks and the
script in temp dirs, along with `require-changelog-before-commit.py`, `keep-working-directory.py`,
`sync_main.py`, `sync-main-at-start.py` and the statusline.

```sh
echo '{"tool_name": "Bash", "tool_input": {"command": "git push origin main"}, "cwd": "/path/to/repo"}' \
  | ../.claude/hooks/coordination-guard.py; echo "exit: $?"
```

## `statusline.py` (not a lifecycle hook, but lives alongside these)

[`../.claude/statusline.py`](../.claude/statusline.py), registered under `statusLine` rather than `hooks`
in `~/.claude/settings.json`. It prints up to four parts, joined by `  |  `:

| Part | Source | Shown |
|---|---|---|
| Wave and phase, `wave-12 — Implement` | `/tmp/claude-wave-phase-<session_id>`, written by the `wave` skill (see [`02-skills-and-subagents.md`](02-skills-and-subagents.md)) | In the session that runs the wave |
| Blocked plans, `⚠ 2 blocked: Checkmate/wave-m6, Repo/wave-12` | Plan entries with `status: blocked` on the coordination board, read through `board.py` | In every session, so a question waiting for you is visible wherever you work |
| Inbox, `inbox: Checkmate 3, Project-Green-HR-MVP 6` | Open `request` and `notice` entries per repo, read through `board.inbox_entries()`; repos with none are left out | In every session, so requests and notices are raised rather than forgotten (see `instructions.md`'s "A repo's inbox") |
| Main behind, `main behind: agents 3, Checkmate 1` | Per active repo, the commits on `origin/main` that the main checkout's `main` lacks, read through `sync_main.commits_behind_origin()` from local refs (no fetch); repos at 0 are left out | In every session, so a checkout that could not be fast-forwarded stays visible until it catches up |

It prints nothing when none applies. Same JSON-on-stdin shape as a hook, which is why it's documented
here, but it isn't triggered by a lifecycle event — Claude Code polls it for display.

```sh
echo '{"session_id": "s1"}' | ../.claude/statusline.py   # no wave, no blocked plan, empty inbox, no lag: prints nothing
```

## Testing a hook change

Every script reads one JSON object from stdin and either exits 0 (optionally printing a
`hookSpecificOutput` JSON object to stdout) or exits 2 with a plain-text message on stderr that Claude
sees as the block reason. That contract makes each hook fully testable standalone, without a real Claude
Code session or a live compaction/tool-use event — pipe in the JSON shape the real event would send (shown
above for each hook) and check the exit code and output match what you expect.
