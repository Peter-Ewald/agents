# Hooks

All hook scripts live in [`../.claude/hooks/`](../.claude/hooks/README.md) and are registered globally in
`~/.claude/settings.json`, which is why they need no per-repo distribution step — see
[`03-cross-repo-distribution.md`](03-cross-repo-distribution.md) for why that's different from skills and
subagents. Every script is a standalone Python 3 file with a `/usr/bin/python3` shebang (the system
interpreter, hardcoded rather than relying on `env`/`PATH`, since a hook can fire with whatever cwd or venv
happens to be active in the calling session) and can be tested directly by piping synthetic JSON to it on
stdin — the examples below do exactly that.

## `reinject-instructions.py`

**Event:** `PreCompact`, and `SessionStart` (matcher: `compact`).

Concatenates `~/Projects/agents/CLAUDE.md` and `instructions.md` and returns them as
`hookSpecificOutput.additionalContext`, re-injecting the full instructions after a compaction event. This
exists because it's undocumented whether Claude Code's own automatic post-compaction re-injection of a
project's root `CLAUDE.md` re-resolves an `@instructions.md` import or just replays the literal line —
this hook makes that question irrelevant by re-injecting the resolved content explicitly either way.

```sh
echo '{"hook_event_name": "SessionStart"}' | ../.claude/hooks/reinject-instructions.py
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

## `statusline.py` (not a lifecycle hook, but lives alongside these)

[`../.claude/statusline.py`](../.claude/statusline.py), registered under `statusLine` rather than `hooks`
in `~/.claude/settings.json`. Reads `/tmp/claude-wave-phase-<session_id>` (written by the `wave` skill —
see [`02-skills-and-subagents.md`](02-skills-and-subagents.md)) and prints it, or prints nothing if no wave
is in progress. Same JSON-on-stdin shape as a hook, which is why it's documented here, but it isn't
triggered by a lifecycle event — Claude Code polls it for display.

```sh
echo '{"session_id": "s1"}' | ../.claude/statusline.py   # prints nothing, no wave in progress
```

## Testing a hook change

Every script reads one JSON object from stdin and either exits 0 (optionally printing a
`hookSpecificOutput` JSON object to stdout) or exits 2 with a plain-text message on stderr that Claude
sees as the block reason. That contract makes each hook fully testable standalone, without a real Claude
Code session or a live compaction/tool-use event — pipe in the JSON shape the real event would send (shown
above for each hook) and check the exit code and output match what you expect.
