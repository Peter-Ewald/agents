---
date: 2026-11-17
title: One window over all repos
outcome: completed
---

# One window over all repos

`agents` wave 02, branch `wave-02-one-window`, mode `interactive`, integration `push`.
Serves the backlog entry "One window over all repos" (Next Up, step 1).

## Summary

| | |
|---|---|
| Goal | Every chat (planning and coordinator) starts in `~/Projects`, opened as one VS Code window. The harness knows each repo's role (a default that one plan can override), plans across repos, applies personal repo rules inside worktrees, and its hooks work when the start folder is not a repo. |
| Kind | Harness and instruction changes. Reported per file and rule. |
| Changes | **agents**: `instructions.md` (new section on repos and their roles), `wave` skill (Plan phase across repos), `wave-runner` (reads repo rules), two hooks (`coordination-inject`, `require-changelog-before-commit`), the shell-command parsing they share with `coordination-guard`, `new-wave-worktree.sh`, docs 01/03/04/05, hooks README. **Checkmate**: a validation-commands section in `CLAUDE.md`. **Local, not committed**: workspace file, Semantic_Evaluation settings fix, auto-memory move. |
| Behaviour | Outside a repo, the session-start hook shows every repo's open board entries. A commit with `cd <repo> &&` or `git -C <repo>` is checked for a missing changelog in that repo, not in the start folder. A new worktree gets the main checkout's untracked `.claude/rules/*.md`. |
| Decisions | See "Decisions" below. |
| Risks and holds | No holds. The new instructions only reach other sessions after merge. The pilot of the window (after merge) may show that Claude Code loads `Project-Green-HR-MVP`'s skills or agents from a subfolder; the fallback is in "Pilot". |

## Attention: Semantic_Evaluation team settings were overwritten

The two `WebFetch` rules went into `Semantic_Evaluation/.claude/settings.json`, the tracked team file,
replacing its `Bash(pip show *)` and `Bash(ruff check *)`. Meanwhile `.claude/settings.local.json` still
has all the old entries. The fix (sub-task L2) restores the tracked file from git and writes the
two-rule content into `settings.local.json`.

## Decisions

| Decision | Chosen | Alternative |
|---|---|---|
| Where repo roles live | New section "Repositories and their roles" in `instructions.md`, loaded by every session and assistant | A separate `repos.md` imported by `CLAUDE.md`, or `CLAUDE.md` only (Claude Code only) |
| How a role is overridden | **One piece of work:** the plan's `Role:` line ("contribution, agreed with <team>"), or your statement in chat for small work outside a wave. **Permanently:** edit the table | A per-repo untracked `.claude/rules/role.md` (one more file per repo to keep true) |
| Personal repo rules in worktrees | `new-wave-worktree.sh` copies untracked `.claude/rules/*.md` itself, so no repo has to list them in `.worktreeinclude` | Keep relying on each repo's `.worktreeinclude` (Checkmate lists `integration.md` today; a new repo silently gets `pr`) |
| Workspace file | Rewrite `~/Projects/projects.code-workspace` in place: one folder `.`, not versioned | Version it in `agents` (one more copy to keep in step with the local folders) |
| Shared shell parsing | New `.claude/scripts/shell_command.py` with the segment and directory parsing now inside `coordination-guard.py`; both hooks use it | Copy the parsing into the changelog hook (two copies drift) |
| `project_green/frontdoor_probe` | Left out of Checkmate's gate: no project file | Give it a `pyproject.toml` (Checkmate work, its own change) |

Plan history: the autonomous parallel waves plan (2026-11-16) set up the board, worktrees and
`.worktreeinclude`. This wave builds on it and changes none of its decisions.

## Repo roles (content for `instructions.md`)

| Role | Repos | Day to day | Override for one piece of work |
|---|---|---|---|
| Active | `Semantic_Evaluation`, `Checkmate`, `agents` | Waves, backlog, board | — |
| Context | `ramgpt-next`, `Project-Green-HR-MVP`, `Chapter_Repos/Litellm-Model integration layer`, `Chapter_Repos/LLM Evaluation Architecture` | Read, `git fetch`, read other branches (`git show`/`git diff origin/<branch>`; switch the checkout only when asked). Their `CLAUDE.md` describes the repo; its workflow and commands don't apply. No commit, no push | A plan with `Role: contribution, agreed with <team>`: integration `pr`, the team's branch, PR and repo conventions for what lands, and none of this harness's personal files committed |
| Later | `Training`, `Website`, `Drainage 2.0` (runs on a Windows VM) | Not used until promoted in this table | — |
| Ignored | `Archive`, `MLDEC-CC-harness` | Never read (denied in the global settings) | — |

## Acceptance cases

The hook and script changes have cases. The instruction and doc changes have none (documentation work):
they are checked in review and in the pilot.

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | Session start outside a repo shows all boards | a start folder that is not a repo; boards for two repos, each with one open entry and one expired notice | `coordination-inject.py` runs | the context has one block per repo, headed `Coordination board for <repo>:`, both entries listed; both expired notices deleted | unit |
| AC2 | Outside a repo with nothing open, it stays silent | a start folder that is not a repo; no open entries anywhere | it runs | no output, exit 0 | unit |
| AC3 | Inside a repo, behaviour unchanged | the existing `test_inject` | it runs | passes unchanged | unit (existing) |
| AC4 | A commit after `cd` is checked in that repo | start folder not a repo; repo R with a staged `pyproject.toml` version bump and no staged `CHANGELOG.md` | `cd R && git commit -m x` | blocked (exit 2), naming the `pyproject.toml` | unit |
| AC5 | A commit with `git -C` is checked in that repo | as AC4 | `git -C R commit -m x` | blocked (exit 2) | unit |
| AC6 | A complete release commit passes | as AC4, with `CHANGELOG.md` staged | `cd R && git commit -m x` | exit 0 | unit |
| AC7 | The guard is unchanged after the parsing moves | the existing guard tests | they run | pass unchanged | unit (existing) |
| AC8 | A worktree gets the personal rules | a main checkout with an untracked `.claude/rules/integration.md` and no `.worktreeinclude` | `new-wave-worktree.sh` creates a worktree | the worktree has the same file; running it again for the same branch changes nothing | unit |

## Sub-tasks

All in the worktree of `agents`, except L1–L3 (local files) and C1 (Checkmate).

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| T1 | Tests for AC1, AC2, AC4–AC6, AC8 that fail now | `.claude/scripts/test_coordination.py` | — | new tests fail for the stated reason, existing pass | `test-author` |
| S1 | Shared parsing: `shell_command.py` with `segments_with_directory(command, cwd)` (applies `cd`) and `git_target(tokens, directory)` (applies `-C`, returns the directory and the git subcommand args); `coordination-guard.py` uses it | `.claude/scripts/shell_command.py`, `.claude/hooks/coordination-guard.py` | T1 | AC7 | medium |
| S2 | Changelog hook checks the repo of each `git commit` segment through `shell_command` | `.claude/hooks/require-changelog-before-commit.py` | S1 | AC4–AC6 | medium |
| S3 | Inject hook: outside a repo, one block per repo in `board.all_repos()` with open entries | `.claude/hooks/coordination-inject.py` | T1 | AC1–AC3 | light |
| S4 | Worktree script copies untracked `.claude/rules/*.md` (`git ls-files -o -- .claude/rules`) | `.claude/scripts/new-wave-worktree.sh` | T1 | AC8 | light |
| S5 | Repo roles section | `instructions.md` | — | review | inline |
| S6 | Plan phase across repos: name the affected repos; for each read `CLAUDE.md`, `.claude/rules/*.md`, its backlog's Next Up and related Planned entries, `docs/history/index.md` (detail files only when their titles relate); one plan per repo on its own board folder with its own `integration`, linked by request and hold; a context repo needs the `Role:` line. `integration` comes from the target repo's `CLAUDE.md` or `.claude/rules/*.md`. Runner: read both in the worktree | `.claude/skills/wave/SKILL.md`, `.claude/agents/wave-runner.md` | S4 | review | inline |
| S7 | Docs upkeep: 01 (the two hooks), 03 (Gotcha 4 rewritten for one window on `~/Projects`, `.worktreeinclude` no longer needed for rules, integration section), 04 and 05 (both chats start in `~/Projects`), hooks README | `docs/01-hooks.md`, `docs/03-…`, `docs/04-…`, `docs/05-…`, `.claude/hooks/README.md` | S1–S6 | `doc-conventions` | medium |
| L1 | Workspace file: folder `.`; `files.exclude` for `Archive`, `MLDEC-CC-harness`, `Drainage 2.0`, `Training`, `Website`, `.boost`, `.ruff_cache`, `**/.claude/worktrees`; `files.watcherExclude` for `**/.claude/worktrees/**`, `**/.venv/**`; `git.repositoryScanMaxDepth: 2`; no Copilot settings | `~/Projects/projects.code-workspace` | — | valid JSON | inline |
| L2 | Semantic_Evaluation settings: `git checkout -- .claude/settings.json`; `settings.local.json` holds only the two `WebFetch` rules | those two files | — | `git status` no longer lists `settings.json` | inline |
| L3 | Move the three Semantic_Evaluation auto-memories to `~/.claude/projects/-Users-peter-Projects/memory/` with their index lines | both memory folders | — | files and index present there | inline |
| C1 | Checkmate `CLAUDE.md`: "Validation commands" table (`legal_poc`: `uv run ruff check .`, `uv run pytest -q`; `project_green/release_service`: `uv run pytest -q`, each run from its folder) | `Checkmate/CLAUDE.md` | — | commands run as written | inline; committed and pushed after your OK (outside a wave) |

## Board fields

- `integration=push` (`agents/.claude/rules/integration.md`), `mode=interactive`, `status=running`
- No holds, no exclusive resources, no new dependencies.

## Verification

- `python3 .claude/scripts/test_coordination.py` in the worktree: all pass, including AC1–AC8.
- `uv run --with ruff ruff check .claude/hooks .claude/scripts` (or the hooks' ruff if a repo env exists).
- Hook smoke from a non-repo folder, with JSON on stdin as in `docs/01-hooks.md`.
- `python3 -m json.tool ~/Projects/projects.code-workspace`.
- Checkmate: run the three commands from C1 once and report the results.

## Pilot (after merge, by you)

1. Open `~/Projects/projects.code-workspace`; start a chat there.
2. Check: the start shows all boards; no repo's `CLAUDE.md` loads at start; reading a Checkmate file
   loads `Checkmate/CLAUDE.md`; `/agents` lists this harness's `doc-sweep`, not Project-Green-HR-MVP's.
3. If Project-Green-HR-MVP's agents or skills appear: hide its `.claude` with
   `git sparse-checkout set --no-cone '/*' '!/.claude/'` in that clone. Git then treats `.claude` as not
   checked out rather than deleted, so nothing can reach a commit.
4. Afterwards: delete `Checkmate/Checkmate.code-workspace` (a Checkmate commit) and
   `Semantic_Evaluation/semantic-evaluation.code-workspace` (a Semantic_Evaluation pull request). Both are
   outside this wave.

## Exit criteria

AC1–AC8 pass; docs and hooks README describe the window on `~/Projects`; the backlog entry is removed; the
plan is archived in `docs/history/`; pushed to `main` of `agents`; L1–L3 done; C1 committed after OK.
