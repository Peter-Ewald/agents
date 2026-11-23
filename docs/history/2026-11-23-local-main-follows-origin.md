---
date: 2026-11-23
title: Local main follows origin/main
outcome: completed
---

# Local `main` follows `origin/main`

Wave 05 in `agents`, branch `wave-05-local-main-follows-origin`. Serves the Next Up entry "Local `main`
follows `origin/main`" (step 1).

## Summary

| | |
|---|---|
| Goal | The main checkout of each active repo moves to `origin/main` after every landing, before every plan and at every session start, whenever that can be done by fast-forward alone. When it cannot, the agent is told why and the statusline shows how far `main` is behind |
| Kind | Implementation (harness). Reporting level: file and rule |
| Changes | **Scripts:** a new `sync_main.py` that fast-forwards the main checkout or says why not. **Hooks:** a new SessionStart hook that runs it for the active repos. **Statusline:** a new "main behind" part. **Wave skill:** Plan and Integrate call the script. **`CLAUDE.md`:** the steps for backlog curation through a pull request end with it. **Global settings:** registers the hook |
| Behaviour | (1) A clean main checkout that is behind fast-forwards to `origin/main`. (2) On another branch, with unpushed commits on `main`, or with an uncommitted file in the way, nothing changes and one line says why. (3) An unreachable or hanging remote gives a "fetch failed" line within the timeout, never a hang. (4) A context repo is only fetched. (5) A wave worktree is never touched. (6) At session start the agent learns which repos moved or were left behind; it hears nothing when all were up to date. (7) The statusline shows `main behind: agents 3` until `main` catches up |
| Decisions | See below |
| Risks and holds | No holds. Every session start waits for the active repos' fetches, which run in parallel and are capped at 8 s. Two sessions that start at once can collide on git's `index.lock`; the second reports it and changes nothing. This wave lands before the Pilot (Next Up step 2), which then runs on fresh checkouts |

### Decisions

| Decision | Chosen | Alternative |
|---|---|---|
| Language | `sync_main.py`, both a stdlib module and a command line, like `board.py`. The hook and the statusline import it, which makes the parallel fetches and the tests simple | `sync-main.sh` as the backlog entry says, with the hook and statusline shelling out to it |
| Where the list of active repos comes from | The "Active" row of the roles table in `instructions.md` (`<projects>/agents/instructions.md`), with `<projects>` set to `~/Projects` unless `CLAUDE_PROJECTS_DIR` overrides it. Promoting a repo there is enough to include it | A separate list in the script, which can drift from the table |
| Session start: wait or run in the background | Wait. The fetches run in parallel and each stops after 8 s, so the first file the session reads is already current | Run in the background: no delay, but a chat about the backlog could still read the old file |
| Context repos | Only fetched (`--fetch-only`), and only when a plan touches them. Session start and the statusline leave them out | Fast-forward a context repo too when it is on `main` |
| Hook events | `startup`, `resume`, `clear`; not `compact`, which does not start new work | All SessionStart events |

## Contracts

`.claude/scripts/sync_main.py`, stdlib only, run as is (it is covered by the existing allow rule
`Bash(~/Projects/agents/.claude/scripts/*)`):

- `sync_main_checkout(path: str, fetch_only: bool = False, timeout: float = 8.0) -> str`
  - Accepts any path in the repo, including a worktree, and resolves the main checkout through
    `git rev-parse --git-common-dir`, as `new-wave-worktree.sh` does.
  - Runs `git fetch origin` with `GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never` and the timeout.
  - Then, unless `fetch_only`, runs `git merge --ff-only origin/main` in the main checkout. That runs only
    when HEAD is `main` and `main` has no commits that `origin/main` lacks.
  - It never stashes, resets, rebases or switches branch, and it never raises.
  - It returns one line, `<repo>: <outcome>`, where `<repo>` is the basename of the main checkout. The
    outcome is one of:

    | Outcome | When |
    |---|---|
    | `up to date` | `main` already matches `origin/main` |
    | `fast-forwarded <N> commit(s) to <short sha>` | The fast-forward ran |
    | `fetched` | `fetch_only` was set |
    | `not synced, fetch failed (<reason>)` | The fetch failed or hit the timeout (`timed out after 8 s`) |
    | `not synced, checkout is on <branch>` | The fetch ran, but HEAD is not `main` |
    | `not synced, main has <N> commit(s) origin/main lacks` | `main` has unpushed commits |
    | `not synced, uncommitted changes in the way (<files>)` | Git refused because local changes would be overwritten |
    | `not synced, <first line of git's error>` | Any other refusal, such as `index.lock` |
    | `not a git repository` | The path is outside git |

- `commits_behind_origin(path: str) -> int | None`: `git rev-list --count main..origin/main`. It uses only
  local refs, never fetches, and returns `None` outside git or when either ref is missing.
- `active_repo_paths() -> list[str]`: paths under `<projects>` named in the Active row that exist and are
  git repositories.
- Command line: `sync_main.py [--fetch-only] PATH...`. It syncs every path in parallel, prints one line
  per path in argument order, and exits 0. It exits 2 only on a usage error.

`.claude/hooks/sync-main-at-start.py`, SessionStart:

- Runs `sync_main_checkout` for `active_repo_paths()` in parallel.
- It prints `additionalContext` that starts with `Main checkouts synced at session start:`, followed by
  every line that is not `up to date`.
- It is silent when every repo was up to date. On an internal error it prints to stderr and exits 0.

`statusline.py`: a fourth part after the inbox, `main behind: agents 3, Checkmate 1`. It covers the active
repos with a count above 0, read through `commits_behind_origin`. It is omitted when there are none, and
like the other parts it never breaks the statusline.

## Acceptance cases

All are checked by unit tests in `.claude/scripts/test_coordination.py`, using the existing `Env` git
fixture with a bare origin. A second clone pushes "a teammate's" commit.

| ID | Behaviour | Given | When | Then |
|---|---|---|---|---|
| AC1 | A clean checkout that is behind fast-forwards | The checkout is on `main`, 1 commit behind `origin/main` after the teammate's push | `sync_main.py <repo>` runs | HEAD equals `origin/main`; the output is `Repo_X: fast-forwarded 1 commit to <sha>`; exit 0 |
| AC2 | Up to date | `main` equals `origin/main` | sync runs | `Repo_X: up to date`; HEAD is unchanged |
| AC3 | Another branch is left alone | The checkout is on `wave-12-x` and the teammate has pushed | sync runs | The branch, HEAD and `main` are unchanged; `origin/main` is updated; the output is `not synced, checkout is on wave-12-x` |
| AC4 | Unpushed commits on `main` | `main` has 1 local commit, and `origin/main` has the teammate's commit | sync runs | `main` is unchanged; `not synced, main has 1 commit origin/main lacks` |
| AC5 | A dirty file in the way | `README.md` is modified locally, and the teammate's commit changes `README.md` | sync runs | HEAD is unchanged; the local `README.md` content is kept; `not synced, uncommitted changes in the way (README.md)` |
| AC6 | A dirty file not in the way | `notes.txt` is modified locally (tracked), and the teammate changes only `README.md` | sync runs | It fast-forwards; `notes.txt` keeps its local content |
| AC7 | An unreachable remote | `origin` points to a missing path | sync runs | `not synced, fetch failed (…)`; exit 0 |
| AC8 | A hanging remote is cut off | `origin` is an ssh URL, `GIT_SSH_COMMAND="sleep 30"` and timeout 1 s | `sync_main_checkout` runs | It returns within 5 s with `fetch failed (timed out after 1 s)` |
| AC9 | Fetch only | The checkout is on `main` and behind | `sync_main.py --fetch-only <repo>` runs | `origin/main` moves, `main` does not; the output is `Repo_X: fetched` |
| AC10 | A wave worktree is untouched | A worktree from `new-wave-worktree.sh` has an uncommitted edit | sync of the main checkout fast-forwards | The worktree's HEAD, branch and edit are unchanged |
| AC11 | Session start syncs the active repos and reports | `CLAUDE_PROJECTS_DIR=<tmp>`; `<tmp>/agents/instructions.md` has an Active row naming `Repo_X`; Repo_X is behind | The hook runs on `{"hook_event_name": "SessionStart"}` | Repo_X is fast-forwarded; `additionalContext` names `Repo_X: fast-forwarded 1 commit…` |
| AC12 | Session start is silent when everything is current | The same setup, but Repo_X is up to date | The hook runs | No output; exit 0 |
| AC13 | The statusline shows the lag | Repo_X's `main` is 2 behind the fetched `origin/main`, and no board entries | The statusline runs | It prints `main behind: Repo_X 2`; after a sync it prints nothing |

## Sub-tasks

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| T0 | Write the tests first, from AC1–AC13 | `.claude/scripts/test_coordination.py` | | The new tests fail because the script and hook are missing | `test-author` (medium) |
| S1 | The sync module and command line, to the contract | `.claude/scripts/sync_main.py` | T0 | AC1–AC10 pass | medium |
| S2 | The SessionStart hook and the statusline part | `.claude/hooks/sync-main-at-start.py`, `.claude/statusline.py` | S1 | AC11–AC13 pass; the existing statusline tests still pass | medium |
| S3 | Instructions: the wave skill's Plan step (sync each affected repo before reading it; `--fetch-only` for a context repo) and Integrate step 7 (sync the main checkout after the merge); the curation steps in `CLAUDE.md` "Shell commands and git" for a repo whose `main` needs a pull request: commit on a branch in the main checkout, complete the PR, switch back to `main`, delete the branch, run `sync_main.py` | `.claude/skills/wave/SKILL.md`, `CLAUDE.md` | | Read through | inline |
| S4 | Documentation upkeep | `docs/01-hooks.md` (hook row, statusline part, script paragraph), `README.md` (scripts list), `.claude/hooks/README.md` if it lists hooks, `backlog.md`, `docs/history/` | S1–S3 | `doc-conventions` check | inline |

## Board fields

- `integration=push` (from `.claude/rules/integration.md`)
- `mode=batch`
- No holds, exclusive resources or new dependencies.
- **Outside effect the plan names:** after the merge and the sync of `agents`, add the hook to the
  `SessionStart` array in `~/.claude/settings.json`. Use matcher `startup|resume|clear`, command
  `/Users/peter/Projects/agents/.claude/hooks/sync-main-at-start.py`, `timeout: 30`. The order matters:
  registering it before the merge would point every session start at a file the main checkout does not
  have yet.

## Verification

- `.claude/scripts/test_coordination.py`: all tests pass.
- Smoke test after the merge: `sync_main.py ~/Projects/agents ~/Projects/Semantic_Evaluation ~/Projects/Checkmate`
  prints one line per repo.
- `echo '{"hook_event_name":"SessionStart"}' | .claude/hooks/sync-main-at-start.py` exits 0.
- `echo '{}' | .claude/statusline.py` prints no error.

## Exit criteria

- AC1–AC13 pass and the existing tests still pass.
- The wave and `CLAUDE.md` texts name the script at all three points.
- The hook is registered.
- The backlog entry is removed and the pilot is step 1.
- The plan is archived.
