---
name: wave
argument-hint: [wave-name-or-number]
description: Runs a wave from backlog.md through its five phases end to end — plan, implement, documentation upkeep, verification, commit proposal — per instructions.md's Implementation Waves section. Use when starting or continuing work on a specific pending wave, or when the user says things like "let's start wave 2" / "continue wave 3".
---

Drive the target wave (identified by `$ARGUMENTS`, or the next one in `backlog.md`'s Next Up tier if
unspecified) through all five phases from `instructions.md`'s Implementation Waves section. The phases
themselves run in this conversation; only the scoped sub-tasks inside Implement and Documentation upkeep
go to the `implementer` (see "Who does what"). Do not fork yourself unless Phase 3 below establishes that
this particular wave owns a full documentation sweep.

At every phase transition, overwrite `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}` with one line:
`<wave name> — <phase name>`. Use this exact path, not the scratchpad directory — the statusline script
that reads it is a separate process that only knows the session ID (from its own stdin), not this
session's scratchpad path, so the file has to live somewhere derivable from the session ID alone.

## Who does what

The main agent (Opus, high effort) owns judgment: the plan, the contracts between sub-tasks, reviewing
each result, verification, backlog and history edits, and the commit message. Scoped execution goes to
the `implementer` subagent (Sonnet, medium effort), which starts from a small fresh context instead of
this conversation's — that, more than the cheaper model, is where the saving comes from. The same split
can be overridden per sub-task in the plan, or per session with `/model` and `/effort`.

## 1. Plan

Once ready to lock in a concrete plan for this wave — backlog curation and any design discussion having
already happened in normal mode — call `EnterPlanMode`. Read `backlog.md` and locate the target wave in
its Next Up tier. If `$ARGUMENTS`
(or the discussion) instead names something sitting in Planned or Later Considerations, treat that as a
promotion: move it into Next Up as part of this phase — rewritten to fit that tier's tone, per
`instructions.md`'s "Backlog tiers" — before planning it like any other wave.

Before writing the session plan, read
`docs/history/index.md` if it exists — for any entry whose title looks related to this wave's topic, open
that specific detail file. Use it to avoid re-proposing a direction already tried and dropped, and cite it
in the session plan when relevant ("considered in `docs/history/2026-05-02-...md` — rejected because X").
Write (or refine) the session plan — see `CLAUDE.md`'s "Session plan location" for where — expanding the
wave's tasks into concrete steps: exact files to touch, exact verification commands, exit criteria.

Split the implementation and its documentation into a **sub-task table** in the plan:

| Column | Holds |
|---|---|
| ID | `S1`, `S2`, … |
| Goal | What the sub-task delivers, in one line |
| Owned files | The only files it may change; no two sub-tasks that run at the same time share a file |
| Depends on | Sub-task IDs that must be reviewed first |
| Acceptance check | The exact commands that prove it done |
| Runs as | `implementer` (default), `implementer, opus` for a sub-task that needs judgment, or `inline` |

Fix the contracts between sub-tasks — names, signatures, data shapes, where a responsibility lives — in
the plan itself, so no sub-task has to make a design decision. Mark a sub-task `inline` when it is a
couple of edits: briefing and reviewing it would cost more than doing it. Before
finalizing, invoke `design-conventions` via the Skill tool (per `CLAUDE.md`'s "Skill freshness" — don't
work from memory of an earlier read) and check the approach against it. Stay in this phase for as long as
discussion continues, revising the plan on feedback. Call `ExitPlanMode` only once ready.

If the discussion concludes without proceeding to Implement — the plan is dropped rather than approved —
archive it anyway, per `CLAUDE.md`'s "Plan history archiving", with outcome `dropped` and the reason given,
before ending the discussion. A dropped plan is exactly the kind of thing a future wave should be able to
find in `docs/history/`.

## 2. Implement

Work through the sub-task table in dependency order. For each `implementer` row, spawn the `implementer`
agent (add `model: "opus"` for an `implementer, opus` row) with a self-contained brief: it has the repo's
`CLAUDE.md` but none of this conversation. The brief carries the goal, owned files, the contract excerpt
from the plan, the acceptance check, and the stop conditions — whatever would otherwise force it to
guess. Do `inline` rows yourself.

After each report:

- Review the result with `git diff -- <owned files>`, not by re-reading the files whole. Check the
  report's checks actually ran and passed.
- A small correction goes back to the same implementer via `SendMessage`, so it keeps its context. A
  `blocked` report, or a correction that is really a design change, comes back to you: revise the plan
  row, then re-brief or do it inline.
- Start a dependent sub-task only after its dependencies are reviewed. Sub-tasks with disjoint owned
  files may run at the same time; never two that share a file.

The lint hook (`lint-changed-lines.py`) and dependency hook (`flag-new-dependency.py`) fire on the
implementer's edits the same as on yours.

## 3. Documentation upkeep

**Default: keep it to what this wave actually made wrong.** Invoke `doc-conventions` via the Skill tool
first — path-based triggering only fires on markdown edits, so a wave that touched no `.md` file still
needs the rules loaded. The README and docstring rewrites are sub-tasks like any other: the plan's table
names them, the `implementer` does them, and you review the diff. `backlog.md`, the `docs/history/`
archive, and `CHANGELOG.md` stay with you — they depend on this conversation. Then:

- Remove the completed wave's section from `backlog.md`, and correct any later wave whose shape this one
  changed.
- Rewrite the comments, docstrings and READMEs of the code this wave touched.
- Fix any documentation statement this wave has just made factually wrong — the specific claims, not the
  documents around them.
- Archive the session plan to `docs/history/` per `CLAUDE.md`'s "Plan history archiving".
- `CHANGELOG.md`, if the wave ships a released package.

**A full sweep of `docs/` is not part of a wave by default.** Re-reading and re-deriving every document is
expensive, and for a repo mid-way through a planned sequence it also produces churn: a document describing
a transition gets rewritten into successively less wrong states rather than once, correctly, at the end.

`backlog.md` is where a repo declares how it wants this handled, and it is authoritative over this default.
Read it, and follow what it says:

- **A backlog that sequences documentation as its own wave** — do the inline upkeep above and nothing more;
  the sweep is that wave's job when it comes up.
- **A backlog whose wave definition names a documentation sweep as part of that wave's own scope** — that
  wave, and only that wave, runs the sweep. Spawn a forked agent for it (the `Agent` tool with
  `subagent_type: fork`, so it inherits full awareness of what was just implemented), and have its prompt
  name the specific sections to rewrite or delete, the `doc-conventions` rules to apply, and the
  "Documentation update phase" checklist in `instructions.md`.
- **A backlog that says nothing either way** — do the inline upkeep, and say in chat that no sweep was run
  and what a sweep would still owe, so the user can ask for one.

## 4. Verification

Run as a step in the main agent, not a subagent — it needs the Implement phase's context to judge which
failures are new. Detect the repo's own test command (don't hardcode one; it varies per repo — look for
`pytest`, `npm test`, a `Makefile` target, etc.) and run it. Separate pre-existing failures from ones this
wave introduced, and name the pre-existing ones explicitly when reporting rather than folding them into a
generic "some tests failed."

## 5. Commit proposal

Draft the commit message per the template in `instructions.md`'s "Commit messages" section. Present it in
chat and wait for explicit confirmation before running the real `git commit` — see `CLAUDE.md`'s "Shell
commands and git" for the exact mechanism.

Mark the wave done (remove its section from `backlog.md` and archive the session plan to `docs/history/`,
per Phase 3's own instructions) only after verification has actually passed. Where verification depends on
hardware or an environment this session cannot reach, say so plainly rather than treating the wave as
finished, and name the steps still outstanding.

Once the commit lands, end the turn by suggesting `/clear` before the next piece of work. Everything the
next wave needs is already in `backlog.md`, `docs/history/`, and the code; carrying this conversation
forward only makes every later call re-read it.
