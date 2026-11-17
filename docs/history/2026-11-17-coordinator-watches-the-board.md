---
date: 2026-11-17
title: The coordinator watches the board and addresses waves by agent ID
outcome: completed
---

# Wave 03 (agents) — The coordinator watches the board and addresses waves by agent ID

## Summary

| | |
|---|---|
| **Goal** | A plan filed as `ready` gets started even while the coordinator sits idle. Waves run in the background and are addressed by the agent ID the Agent tool returns. Filing a plan from a planning session no longer gets blocked by auto mode's safety check, and the board script works under any `python3`. These are findings of the backlog's Next Up entry *Pilot: parallel waves on a real release*, which stays open. |
| **Kind** | Implementation (harness). Reported by script, skill and settings rule. |
| **Changes** | **Board script:** a new `board.py watch-for-work` command; `key=value` pairs accepted after options on Python 3.9 too. **`coordinate` skill:** a background-task check at setup; the board watch as a Monitor; waves started without `run_in_background`/`name` and addressed by the agent ID stored on the plan entry. **`wave` and `coordinate` skills:** run the board scripts as they are, never through `python3`. **Docs:** `docs/05-parallel-waves.md` and `docs/01-hooks.md`, the claims about how waves start, how they are addressed, and how the coordinator learns of board changes. **Your machine** (manual): VS Code restarted so the background-task variable is gone from its environment; an `autoMode.allow` entry; the two `python3 … board.py` rules removed. |
| **Behaviour** | `watch-for-work` prints one line when a batch plan becomes `ready` or `interrupted`, or when a hold is satisfied or removed, and stays silent otherwise. It also reports changes made while it was not running, and an unreadable entry. `board.py file … --repo R k=v` works under `/usr/bin/python3` (3.9). The coordinator refuses to start waves while background tasks are disabled, stores each wave's agent ID as `agent:` on its plan entry, and uses that ID to resume a wave and to tell after a restart whether its agent is gone. |
| **Decisions** | **D1** the coordinator watches the folder instead of the planner messaging it by name. **D2** it polls every 5 s using only the standard library. **D3** the watch reports only changes that can give the coordinator work. **D6** the agent ID is a free-text field; `board.py` doesn't know it. **D7** the Python 3.9 parsing bug is fixed here, because running the script as it is makes it hit. |
| **Risks and holds** | **Holds:** none, and no file overlap with Semantic_Evaluation wave 50, the only wave still running (wave 68 has merged and shipped as 4.6.0). **Monitor limit:** a Monitor runs at most 30 minutes, so the coordinator restarts it on each expiry notice: about 48 short turns a day. The watch keeps its own state, so nothing is lost between runs. **Manual step M0:** wait until wave 50 has returned before quitting VS Code, because quitting ends that wave. |

## Context

- **Waves aren't picked up while the coordinator is idle.** The `coordinate` skill says it reacts to
  board changes, but nothing delivers them:
  - `coordination-watch.py` (PostToolUse) runs only after the session's own tool calls.
  - It also exits at once outside a repo, and the coordinator runs in `~/Projects`.
  - An idle session wakes only on a message or a Monitor event.
- **Waves ran in the foreground.** `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` was set in `~/.zshrc`, so every
  `wave-runner` blocked the coordinator until it returned. The line is gone from `~/.zshrc`, but the
  running VS Code still carries the variable until it restarts.
  - `docs/05-parallel-waves.md` only checks `~/.claude/settings.json` for it.
  - The Agent tool has no `run_in_background` or `name` parameter. Background is the default.
  - Each call returns an agent ID, and the wave's report comes back as a message from that ID. Today
    the skill addresses waves by a `name` it cannot set.
- **The filing call was blocked.**
  - `python3 …/board.py` matched only the `Bash(python3 … board.py *)` rules. Auto mode switches those
    off, so its safety check reviewed the call and refused it.
  - Run as it is, `board.py` matches `Bash(~/Projects/agents/.claude/scripts/*)`, which auto mode keeps.
  - The shebang `#!/usr/bin/env python3` then picks whichever `python3` comes first on PATH: the
    activated virtual environment's 3.12 in VS Code, `/usr/bin/python3` (3.9) elsewhere.
- **Seven tests fail on `main` under 3.9, all for one reason.**
  - The tests are `test_inject`, both `test_inject_outside_repo_*`, `test_blocked_plans_listed_and_shown`,
    `test_set_preserves_body_and_order`, `test_merge_hold_blocks_main_push` and `test_watch`.
  - Each calls `board.py file/set` with `key=value` pairs after an option. Python 3.9's argparse rejects
    those pairs ("unrecognized arguments"); 3.12 accepts them, and there all 24 tests pass.
  - `test_watch` tests the `coordination-watch.py` hook and dates from wave 01. It is not a test written
    in advance for `watch-for-work`.
- **Out of scope:**
  - The working-directory hook fix: already done separately, in commit 9dd7a89.
  - `background: true` in `wave-runner.md`: background is already the default, and the setup check
    catches the variable coming back.

## Decisions

| # | Decision | Alternative |
|---|---|---|
| D1 | **The coordinator watches the board.** No change to the planner's routine; works whatever the session is called | The planner messages `Coordinator` after filing: depends on the session name and on every planner remembering |
| D2 | **Poll every 5 s with the standard library**, re-reading only entries whose file time changed | `fswatch`: a new dependency; macOS has no `inotify` |
| D3 | **Report only changes that can give the coordinator work** | Report every change: the coordinator wakes on its own `status=running` edits |
| D4 | The watch's state is `<board root>/.watch-for-work.json` and is kept between runs. On the first run there is no state, so it only records the board: the coordinator reads the whole board when it starts | State in `/tmp` per session: a restarted coordinator loses the changes made in between |
| D5 | You make the settings edits (M1). An agent editing its own permission settings is exactly what auto mode's check refuses | Keep the `python3` rules: they look like cover but don't work in auto mode |
| D6 | **`agent:` is a free-text field.** `board.py set … agent=<id>` already stores any key. No code reads it: the coordinator compares it with what `ListAgents` lists | Teach `board.py` the field (show it in `list`, check its format): code with no reader |
| D7 | **`board.py` parses with `parse_known_args`.** Leftover `key=value` tokens of `file`/`set` are added to the pairs; any other leftover token is still an argparse error | Pin the shebang to Homebrew's 3.12: breaks on any machine without that path, and the hooks import `board` under `/usr/bin/python3` anyway |

## Contracts

- **`board.py watch-for-work [--interval SECONDS] [--once]`**, in `board.py`, reusing `all_repos`,
  `entries`/`read_entry`, `format_line` and `_write_atomic`.
  - **State:** `{"<repo>/<name>": {"mtime_ns", "kind", "status"}}`.
  - **Output:** one flushed stdout line per event:
    - `work: plan <format_line>`: a new or status-changed `plan` with `mode: batch` and status `ready` or
      `interrupted`.
    - `work: hold <format_line>`: a hold whose status became `satisfied`.
    - `work: hold removed <repo>/<name>`: a hold that was not yet satisfied has disappeared.
    - `board: unreadable <repo>/<name>: <error>`: once per file time.
  - **Modes:** `--once` compares with the stored state, prints, saves and exits 0. Without it, the
    command loops every `--interval` seconds (default 5).
- **Argument parsing (D7):**
  - `main()` calls `parse_known_args`.
  - For `file` and `set`, every leftover token that contains `=` is appended to `args.pairs`.
  - Any other leftover token gives `parser.error("unrecognized arguments: …")`, as today.
- **`coordinate` skill, Setup**, in this order:
  1. Run `printenv CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`. If it prints `1` or `true`, stop. Tell the user
     that waves would run in the foreground and block the coordinator, that the variable must come out
     of their shell profile, and that VS Code must restart. Start no wave.
  2. Run `board.py list`.
  3. Start a Monitor on `~/Projects/agents/.claude/scripts/board.py watch-for-work` with
     `timeout_ms: 1800000` and the description "board: work for the coordinator". On an expiry notice,
     start it again.
- **`coordinate` skill, when an event arrives:**
  - On a `work:` line, re-read the board and apply *Starting waves* and *Waking parked waves*.
  - On a `board: unreadable` line, tell the user.
- **`coordinate` skill, starting waves:**
  - The Agent call is `subagent_type: "wave-runner"` with the same prompt as today, and no
    `run_in_background` or `name`.
  - Right after it, run `board.py set <repo>/<name> status=running agent=<returned agent ID>`.
  - *Waking parked waves* does the same. Its fresh agent's ID replaces the old one.
- **`coordinate` skill, addressing:**
  - *Questions to the user*, step 5: `SendMessage` to the entry's `agent` ID.
  - A report arrives as a message from an agent ID. The coordinator finds the wave's plan entry with
    `grep -l "agent: <id>" ~/.claude/coordination/*/*.md`.
  - *After a restart*: a `running` plan whose `agent` ID `ListAgents` does not list is gone. Set it to
    `interrupted` and start it again.
- **Run-as-is sentence**, where `wave/SKILL.md` (line 17) and `coordinate/SKILL.md` (line 9) define
  `board.py`: "Run the scripts as they are, never through `python3`. Only then does the allow rule for
  that folder cover them in auto mode."

## Acceptance cases

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | No state means baseline | a board with a ready batch plan, no state file | `watch-for-work --once` | prints nothing, exit 0, state written | unit |
| AC2 | New ready plan | baseline taken | a batch plan `status=ready` is filed; `--once` twice | first prints one `work: plan` line naming it, second nothing | unit |
| AC3 | Non-work changes are silent | as AC2, plan seen | `set status=running`; a notice filed; an interactive plan `status=ready` filed; `--once` | nothing | unit |
| AC4 | Interrupted plan | a batch plan `running`, seen | `set status=interrupted`; `--once` | one `work: plan` line | unit |
| AC5 | Hold satisfied | an open hold, seen | `satisfy`; `--once` | one `work: hold` line | unit |
| AC6 | Hold removed | an open hold, seen | `rm`; `--once` | one `work: hold removed` line | unit |
| AC7 | Unreadable entry, once | baseline taken | a `.md` without closing `---` appears; `--once` twice | first prints `board: unreadable` naming it, second nothing; exit 0 | unit |
| AC8 | Loop mode emits live | baseline taken | run with `--interval 0.2`, file a ready batch plan | the line appears within 2 s | unit |
| AC9 | Pairs after options on 3.9 | — | the whole suite under `/usr/bin/python3` (3.9) and under `python3.12`, with `board_cli` running `board.py` under that interpreter | 24 existing tests plus AC1–AC8 and AC10 pass under both | unit |
| AC10 | A stray token is still refused | — | `board.py file notice n --repo R stray` | exit 2, stderr names `stray`; nothing filed | unit |
| AC11 | Background check | the `coordinate` skill | read-through | Setup begins with the `printenv` check and stops with the stated message when it is set; no wave is started before it | read-through |
| AC12 | Waves addressed by ID | `coordinate` skill and `docs/05-parallel-waves.md` | read-through | no `run_in_background`, `name:` or `-integrate` naming is left; `agent=<id>` is stored on start and wake; `SendMessage`, report matching and the restart check use it; docs/05 says the same, and its constraint row names the shell environment, not only `settings.json` | read-through |

## Sub-tasks

| ID | Goal | Owned files | Depends on | Check | Runs as |
|---|---|---|---|---|---|
| T | Tests first for AC1–AC10. The suite runs `board.py` under `sys.executable`, so running the suite under 3.9 covers AC9 | `.claude/scripts/test_coordination.py` | — | new tests fail for the stated reason; under 3.12 the 24 existing tests pass, under 3.9 the 7 named ones fail | `test-author` |
| S1 | `watch-for-work` and the parsing fix | `.claude/scripts/board.py` | T | AC1–AC10 under both interpreters | medium |
| S2 | `coordinate` skill: Setup check, Monitor, agent IDs, run-as-is; `wave` skill: run-as-is | `.claude/skills/coordinate/SKILL.md`, `.claude/skills/wave/SKILL.md` | S1 | AC11, AC12 | inline |
| S3 | Docs: in `05-parallel-waves.md`, the "three hooks … without polling" paragraph, the coordinator list, `SendMessage` addressing and the constraints table. In `01-hooks.md`, `coordination-watch.py` covers only sessions inside a repo. Also any `board.py` command list in `02` or `.claude/hooks/README.md` | those files | S1 | AC12; no claim left that the coordinator learns of changes through the hook | inline |
| — | Plan archive `docs/history/2026-11-17-coordinator-watches-the-board.md` and its index line | `docs/history/` | all | — | inline |

## Board fields

- **Plan entry:** `agents/wave-03-coordinator-watches-board`, `mode: interactive`, `status: running`,
  `integration: push`. Filed with the script run as it is: a call that goes through without a prompt or
  a refusal confirms fix 1.
- **Holds, exclusive resources, new dependencies:** none.

## Verification

1. **The suite on both interpreters.** In the worktree, run
   `/usr/bin/python3 .claude/scripts/test_coordination.py` and
   `/opt/homebrew/bin/python3.12 .claude/scripts/test_coordination.py`. Both must pass in full.
2. **Live check in this session.**
   - Start a Monitor on `board.py watch-for-work --interval 1` with `CLAUDE_COORDINATION_DIR` set to a
     scratch board.
   - File a ready batch plan there and confirm the event arrives.
   - Stop the Monitor and remove the scratch board.

## Manual steps for you (I'll walk you through them after the wave)

- **M0. Background tasks back on.** The `~/.zshrc` line is already removed.
  - Once Semantic_Evaluation wave 50 (pods score only on their own judge models) has returned, quit and
    reopen VS Code.
  - In a new session, run `env | grep DISABLE_BACKGROUND`. It should print nothing.
- **M1. Edit `~/.claude/settings.json`.**
  - Delete `"Bash(python3 /Users/peter/Projects/agents/.claude/scripts/board.py *)"` and
    `"Bash(python3 ~/Projects/agents/.claude/scripts/board.py *)"`.
  - Add this inside `"autoMode"`, next to `"environment"`:

  ```json
  "allow": [
    "$defaults",
    "Running ~/Projects/agents/.claude/scripts/board.py, the user's coordination board command, to file, update, satisfy, lock, unlock or remove entries under ~/.claude/coordination/ is allowed. A plan entry filed with status ready or running records a plan the user approved in plan mode in that session, so filing it is not self-approval."
  ]
  ```

  - Then run `claude auto-mode config` and check that the entry is listed.
- **M2. Start the coordinator fresh** (`/coordinate` in a new session started after M0).
  - It runs the background check, reads the board and starts the watch.
- **M3. Optional live check.**
  - With the coordinator idle, I file a throwaway hold in `agents` and satisfy it.
  - The coordinator should wake, re-read the board and report nothing to start.
  - Then I remove the hold.
