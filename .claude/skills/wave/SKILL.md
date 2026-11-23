---
name: wave
argument-hint: [wave-name-or-number]
description: Runs a wave from backlog.md through its phases (plan, specify, implement, documentation upkeep, verification, done check, integrate, report) per instructions.md's Implementation Waves section, in its own worktree. Use when planning, starting or continuing a specific pending wave, or when the user says things like "let's plan wave 2", "start wave 3", "run wave 12 interactively" or "continue wave 3".
---

Drive the target wave (named by `$ARGUMENTS`, or the next one in `backlog.md`'s Next Up tier) through the
phases of `instructions.md`'s Implementation Waves section. Supporting files, read when the phase needs
them:

| File | Holds | Read in |
|---|---|---|
| [tiers.md](tiers.md) | The implementer tiers, mapping task types to tiers, the escalation rule | Plan, Implement |
| [board.md](board.md) | The coordination board: entry formats, holds, locks, parking and the handover | Plan, Integrate |
| [report.md](report.md) | The wave report | Report |

`board.py` below means `~/Projects/agents/.claude/scripts/board.py`, and `new-wave-worktree.sh` the script
next to it. Run both as they are, never through `python3` or `bash`: only then does the allow rule for
that folder cover them in auto mode.

At every phase transition, overwrite `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}` with one line:
`<wave name> — <phase name>`. Use this exact path, not the scratchpad directory: the statusline script
reads it from a separate process that knows only the session ID.

## Batch and interactive waves

| | Batch (default) | Interactive (only when the user says so, e.g. "run wave 12 interactively") |
|---|---|---|
| Plan | In the planning chat, with the user, in plan mode | The same |
| After approval | The plan is filed on the board as `ready`; the planning chat moves on. The coordinator starts a `wave-runner` for it | The plan is filed as `mode: interactive`, `status: running`; this session runs the wave |
| Questions | None reach the user directly: on a stop condition, set the plan entry to `blocked`, append the question to its body (see [board.md](board.md)) and return the report with it | Ask the user in this session |

Both follow the same phases, done check, board rules and report. Neither asks for an OK before commit,
push or PR: the done check replaces it.

## Who does what

The wave agent (Opus, high effort) owns judgment: the plan, the contracts between sub-tasks, reviewing each
result, verification, the done check, backlog and history edits, the commit messages and the integration.
Tests come from `test-author`; scoped execution goes to the implementer tiers in [tiers.md](tiers.md).
Each subagent is fresh and runs once: a correction or a retry is a new brief, never a resumed agent.

## 1. Plan

Once ready to lock in a concrete plan (backlog curation and design discussion having happened in normal
mode), call `EnterPlanMode`. Locate the wave in `backlog.md`'s Next Up tier; something named from Planned
or Later Considerations is promoted to Next Up first, rewritten to fit that tier's tone.

Name the repos the change needs, with their roles from `instructions.md`'s "Repositories and their
roles". The session starts in `~/Projects`, outside every repo, so nothing repo-specific is loaded yet.
For each affected repo read:

- its `CLAUDE.md` and untracked `.claude/rules/*.md` (conventions, test commands, `Integration: push`)
- its `backlog.md`: Next Up and the Planned entries the change touches
- its `docs/history/index.md`, opening only the detail files whose titles relate; cite them where they
  shaped the plan
- its inbox, `board.py inbox --repo <repo>`, raised with the user per `instructions.md`'s "A repo's
  inbox"; a notice the wave will act on is named in the plan

Work in two repos is one plan per repo, each filed in its own repo's board folder with its own
`integration`, linked by a `request` and a hold (see [board.md](board.md)). A plan that changes a
context repo carries the line `Role: contribution, agreed with <team>`.

Write the session plan (see `CLAUDE.md`'s "Session plan location"). Its title says in a few words what
the wave does ("Repeat the Copilot eval runs"); that title is how the wave is named in every message (see
`instructions.md`'s "Talking to the User"). The plan opens with a **summary** the user can approve from,
at the wave's reporting level, and puts the detail after it:

| Summary line | Holds |
|---|---|
| Goal | What is true afterwards that is not now, and which backlog entry it serves |
| Kind | Implementation, refactor, experiment, documentation or sweep; this sets the reporting level |
| Changes | The modules or documents affected, grouped by service, package or repo; no file list |
| Behaviour | The acceptance cases in one plain sentence each |
| Decisions | What the approval settles that the user might decide differently, each with the alternative |
| Risks and holds | What could make it fail or wait, and which other waves it touches |

Below the summary:

- **Goal, exit criteria, verification commands** (the repo's lint, format check, tests, smoke commands).
- **Acceptance cases**: for each behaviour the wave adds or changes, one row the user can check without
  reading code. Unit is the default; integration only where the behaviour lives in a seam between
  components; an eval item wherever it depends on a model (prompts, tools, routing, context).

  | ID | Behaviour | Given | When | Then | Checked by |
  |---|---|---|---|---|---|
  | AC1 | Batch upload rejects a duplicate id | a batch with two items sharing an id | it is uploaded | HTTP 422 naming the id; nothing stored | unit |
  | AC2 | Parental leave goes to the policy tool | a user asks how long parental leave is | the agent answers | it calls `search_policy` with topic parental leave | eval item, metric `tool_called` |

  A documentation or sweep wave has no cases; a refactor that keeps behaviour uses the existing suite; an
  experiment (`semeval-experiment`) measures rather than asserts. The plan says which applies and why.
- **Sub-task table**: ID, goal, owned files (no two concurrent sub-tasks share a file), depends on,
  acceptance check, and `Runs as`: `light`, `medium`, `strong` or `inline`, chosen per [tiers.md](tiers.md).
  Fix the contracts between sub-tasks (names, signatures, data shapes, where a responsibility lives) in the
  plan, so no sub-task makes a design decision. `inline` is for a couple of edits that would cost more to
  brief than to do.
- **Board fields**: holds on other waves (`start` or `merge`, see [board.md](board.md)), exclusive
  resources (for example service ports), new dependencies approved with the plan, and `integration`: `push`
  when the repo's `CLAUDE.md` or one of its `.claude/rules/*.md` carries an `Integration: push` line, `pr`
  otherwise.

Before finalizing, invoke `design-conventions` via the Skill tool and check the approach against it.
Discuss the plan with the user per `instructions.md`'s "Talking to the User": the summary and the open
decisions, not the sub-task table, unless asked. Revise on feedback; call `ExitPlanMode` once ready. On approval, file the plan entry and its holds on the
board per [board.md](board.md). A batch wave ends here for the planning chat; continue with the next
backlog entry, or suggest `/clear`.

A plan dropped instead of approved is archived anyway, per `CLAUDE.md`'s "Plan history archiving", with
outcome `dropped` and the reason.

## Worktree

Every wave runs in its own worktree on the branch `wave-<NN>-<slug>`:
`new-wave-worktree.sh <repo path> wave-<NN>-<slug>` creates it from the current `origin/main` (or resumes
an existing one, for an interrupted wave) and prints its path; `cd` there. It carries the main checkout's
untracked `.claude/rules/*.md` and the files `.worktreeinclude` lists. A session started outside the repo
reads the repo's `CLAUDE.md` and `.claude/rules/*.md` in the worktree before going on. Every sub-task works
in that worktree. Run the repo's environment setup there (`uv sync` for a uv project). Set the plan entry's status
to `running`.

## 2. Specify

Skip for a wave without acceptance cases. Otherwise brief `test-author` (add `model: "opus"` for
concurrency, auth, migrations or a published SDK API) with the acceptance cases, the worktree path, the
repo and wave key, and the owned test files. Then:

1. Check each test and eval item against its case: same situation, same expected outcome, failing for the
   stated reason. Send a mismatch back as a new brief.
2. Commit the tests as the wave's first commit, the **tests-first commit**:
   `git commit -m "Wave <NN>: tests first for <title>"`. Note its SHA in the plan entry (`board.py set
   ... tests_first=<sha>`). Eval items are not committed: `test-author` pushed them to the dev dataset,
   tagged `pending:<repo>/<wave key>`, without running them.
3. From now on these tests and items are **frozen**. An implementer who believes one is wrong reports
   `blocked`. You may correct one that misread a clear case and list the change in the report; a change to
   the case itself is a stop condition.

## 3. Implement

Work through the sub-task table in dependency order. For each tier row spawn `implementer-<tier>` with a
self-contained brief per the `implementer-contract` skill (goal, owned files, contract excerpt, frozen
tests, acceptance check, stop conditions); it has the repo's `CLAUDE.md` but none of this conversation. Do
`inline` rows yourself. Sub-tasks with disjoint owned files may run at the same time.

After each report, review with `git diff -- <owned files>` and check the reported checks actually ran. A
correction or a `blocked` report follows the escalation rule in [tiers.md](tiers.md); a correction that is
really a design change revises the plan row first. For an LLM agent, run the wave's own eval items once
the code is in place, three times each:
`eval-run --run-file <the project's regression run file> --items <ids> --repeats 3`. An item named by id
runs although it is still pending. The flags need `semantic-evaluation` 4.3.0 or later; a repo pinned
lower upgrades in a sub-task of its own plan (`semeval-upgrade`), and a plan without one stops the wave,
since the upgrade is a dependency it does not name.

Commit on the branch when Implement is done, so an interrupted wave resumes from its branch.

## 4. Documentation upkeep

Keep it to what this wave made wrong; a wave never runs a documentation sweep (see "Sweep waves"). Invoke
`doc-conventions` via the Skill tool first. README and docstring rewrites of touched code are sub-tasks
like any other. Yourself:

- Remove the wave's section from `backlog.md` and correct any other entry whose shape this wave changed.
- Fix the specific documentation claims this wave made false.
- Archive the session plan to `docs/history/` per `CLAUDE.md`'s "Plan history archiving".
- `CHANGELOG.md`, only in the wave that releases the package; others file a `notice`. The entry goes
  under `## [Unreleased]`, and no file names the new version yet (no pin, lock file, backlog or history
  line): the version is the next one after whatever is on `main` at Integrate, which no plan can know.

## 5. Verification

Run in the wave agent, not a subagent: it needs the Implement context to judge which failures are new. Run
the plan's verification commands (the test command comes from the repo's `CLAUDE.md`). For an LLM agent,
run the full regression per `semeval-maintain` step 5 with this wave's own items included:
`eval-run --run-file <the project's regression run file> --include-pending pending:<repo>/<wave key>`.
Other waves' pending items are left out by default. The selection stays on the command line, never in a
committed run file. Every new eval item must pass all three repeats from Implement. Name pre-existing failures explicitly.

## 6. Done check

The wave may integrate only when every row holds, each with its evidence:

| Check | Evidence |
|---|---|
| Every acceptance case passes | Each case with its test or item and the result |
| Frozen tests unchanged, or each change listed with its reason | `git diff <tests-first sha> HEAD -- <frozen files>` |
| Frozen eval items unchanged since the Specify push, or each change listed | The items' version stamps in the dev dataset |
| Verification passed | Each command with its result |
| For an LLM agent: new items 3 of 3, regression gate passed | Langfuse run names, result per metric |
| Documentation upkeep done | The files rewritten |
| `backlog.md` updated | Yes or not applicable |
| Plan archived in `docs/history/` with its index line | The file name |
| `CHANGELOG.md` entry under `## [Unreleased]`, if this wave releases a package | Yes or not applicable |

A failing check sends the wave back to Implement, under the escalation rule.

## 7. Integrate

Commit messages follow `instructions.md`'s "Commit messages", passed with `-m`, without a trailer.

1. **Park on an open merge hold.** If a hold with `blocks: merge` still names this wave, push the branch,
   open the PR as a draft (for `integration: pr`), write the handover and set status `waiting` per
   [board.md](board.md), and return the report with status `waiting`. Integration continues later from the
   handover, in a fresh agent.
2. **Take the lock:** `board.py lock <repo> --wave <wave key>`. If another wave holds it, wait and retry.
3. **Rebase** on the current `origin/main`. Conflicts in `backlog.md` (renumbering) and
   `docs/history/index.md` are mechanical; other conflicts follow both plans' intent, and one neither plan
   settles is a stop condition (release the lock first).
4. **Set the version**, if this wave releases a package: the next version after the newest on the rebased
   `main`, per SemVer. Write it into the `## [Unreleased]` heading (`## [x.y.z] - YYYY-MM-DD`), the
   package's project file, and every pin, lock file, backlog and history line that names the release. The
   lock makes this safe: no other wave of this repo can release in between.
5. **Re-verify** on the rebased branch: the verification commands; the regression run again only if
   `main` brought changes that can alter the agent's behaviour.
6. **Land it**, never with a merge commit you created:
   - `integration: pr`: push the branch (`--force-with-lease` after the rebase), create or publish the PR
     with the report as its description, wait for required checks, and complete it with rebase and
     fast-forward, using the completion command the repo's instructions name. On Azure Repos
     `az repos pr update` cannot choose a strategy, so the PR completes through `az rest` (PATCH on
     `.../repositories/<repo>/pullrequests/<id>`, `completionOptions.mergeStrategy: "rebase"`); on
     GitHub it is
     `gh pr merge --rebase`. If the repository refuses that strategy, complete it with the one it allows
     and say so in the report.
   - `integration: push`: `git push origin HEAD:main`; if `main` moved, rebase again rather than merge.
7. **After the merge:** remove the wave's `pending:` tags from its eval items (dataset lock, pull, edit,
   push, unlock); satisfy the holds that wait on this wave; release the lock; remove the worktree and
   delete the branch locally and on origin; delete the plan entry and the notices the plan names as
   handled (`board.py rm`). A server-side rebase gives the commits new ids, so `git branch -d` may
   refuse: confirm the change is on `origin/main`, then use `git branch -D`.

## 8. Report

Return the report in [report.md](report.md) and put the whole of it into the PR description. An
interactive wave shows only its head in chat (status, question, `For the user:`, outcome, PR link) and
then suggests `/clear`.

## Stop conditions

Stop with `blocked` and one stated question when two parts of the plan contradict each other or a case
cannot be tested as written; a frozen test looks wrong in a way the case does not settle; a dependency the
plan does not name is needed; the change needs work in another repo (also file a `request` there); a check
still fails after the escalation one tier up; a rebase conflict neither plan settles; or an action with
outside effects the plan does not name (a release, deleting data, a shared setting). Never lower a
threshold, skip hooks (`--no-verify`), force-push `main`, or touch another wave's worktree.

## Sweep waves

A documentation sweep is its own wave: a backlog entry whose plan names the scope (a path or the whole
repo) and what to check. The `doc-sweep` agent replaces Specify and Implement (add `model: "opus"` for a
whole repo or a restructuring); it applies its fixes directly, since the approved plan is the
confirmation, and lists them in its report. Worktree, done check (without the test rows), integration,
board and report are the same. The planning agent proposes a sweep wave when a sequence of waves in one
area ends, or when the backlog names one.
