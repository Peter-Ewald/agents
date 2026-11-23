# Glossary

Repository-wide terms for the `agents` harness. Package- or service-local terms would go in that
package's own `docs/glossary.md` instead — this repo has none of those, everything here is cross-repo by
design.

## Wave

One coherent slice of change that lands as a single completed objective, not a single commit. Every wave
runs in its own worktree through eight phases in order: Plan, Specify, Implement, Documentation upkeep,
Verification, Done check, Integrate, Report. See
[`../instructions.md`](../instructions.md#implementation-waves) for the full definition and
[`00-agents-overview.md`](00-agents-overview.md) for how the phases map onto this harness's mechanisms.

## Batch wave

The default kind of wave. It is planned with you in plan mode, filed on the coordination board as `ready`,
and then run in the background by a wave runner that the coordinator starts. It asks you nothing directly:
a stop condition ends it with a `blocked` report and one question.

## Interactive wave

A wave you ask to run in the planning session itself ("run wave 12 interactively"). It is filed on the
board as `running`, follows the same phases, done check and report as a batch wave, and asks you its
questions directly in that session.

## Sweep wave

A documentation sweep run as its own wave: a backlog entry whose plan names the scope and what to check.
The `doc-sweep` agent replaces the Specify and Implement phases and applies its fixes directly, because the
approved plan is the confirmation. No other wave runs a sweep.

## Acceptance case

One row of a wave's plan that says, in words and data you can check without reading code, what must be
true afterwards: the behaviour, a given situation, an action and the expected outcome, and how it is
checked (unit test, integration test or an eval item). A documentation or sweep wave has none.

## Tests-first commit

The first commit of a wave, made in the Specify phase: the tests that `test-author` wrote from the
acceptance cases, failing for the reason each case states, before any implementation exists. Its SHA is
recorded in the plan entry.

## Frozen test

A test or eval item written in the Specify phase that implementers may not change. An implementer who
believes one is wrong reports `blocked`. The done check lists any change to a frozen test with its reason.

## Tier

One of three implementer levels, `light` (Haiku), `medium` (Sonnet) and `strong` (Opus). A plan's sub-task
table names the tier per row; the cheapest tier that can do the sub-task well is chosen, and a failed
attempt is retried once, one tier up. See `wave/tiers.md`.

## Wave runner

The `wave-runner` subagent: the wave agent of one batch wave, running in the background from Specify to
Report. Briefed with a handover instead, it runs only the Integrate phase of a parked wave.

## Coordinator

The one long-lived session (`claude --name coordinator`, then `/coordinate`) that starts ready waves as
wave runners, at most four at once, relays their questions to you, wakes parked waves and keeps plan
statuses true. It never edits code or merges.

## Coordination board

The files under `~/.claude/coordination/`, one folder per repo, holding the rules between waves that must
outlast a session: plan entries, holds, requests, notices and locks. Read and written through `board.py`.
See [`05-parallel-waves.md`](05-parallel-waves.md).

## Inbox

A repo's open `request` and `notice` entries on the coordination board: work another repo asked for,
and steps a release asks of this repo. The agent whose session works on the repo raises them with you and
deletes each once it is a backlog entry, acted on or closed; the coordinator does not act on them.
`board.py inbox` lists them and the statusline counts them. Not a message queue: nothing is delivered
or acknowledged. See `instructions.md`'s "A repo's inbox".

## Plan entry

The board entry for one approved wave: its plan as approved, its mode (batch or interactive), status
(`ready`, `running`, `waiting`, `blocked`, `interrupted`), holds, exclusive resources and approved new
dependencies. Removed after the wave's merge.

## Hold

A "not before" rule between two waves on the board. A `start` hold keeps the waiting wave from starting
until the other wave's condition is true; a `merge` hold lets it run up to the done check but not integrate.

## Parked wave

A wave with status `waiting`: it finished its done check but an open `merge` hold keeps it from
integrating. Its branch is pushed (as a draft PR where PRs are used) and a handover is stored in its plan
entry; it costs nothing while parked.

## Handover

The section appended to a parked wave's plan entry (branch, worktree, PR, what integration still needs, the
report so far) that lets a fresh wave runner finish the Integrate phase without the parked wave's context.

## Integration lock

The board lock a wave holds from its rebase to its merge, so integration is serial per repo. While another
wave holds it, pushing `main` or completing a pull request is blocked.

## Dataset lock

The board lock a wave holds for one pull and push of a Langfuse dev dataset, so parallel waves push one
after the other. `push` itself keeps what others changed since the pull and refuses a real conflict.

## Done check

The table every wave passes before it integrates: each row (acceptance cases, frozen tests unchanged,
verification, eval results, documentation, backlog, history, changelog) needs its evidence. It replaces an
approval of the commit.

## Wave report

What a wave returns when it ends, and its PR description. Its head is for you: status, the question when
blocked, `For the user:` (what needs your attention, or "nothing") and a short outcome. Below a line
follows the evidence for the PR: acceptance cases, done check, deviations, follow-ups. The coordinator
relays only the head.

## Reporting level

How deep a message describes finished work: the units of what the work produced, one level above the
individual edits. Modules grouped by service or package for an implementation wave; document and section
for design work; file for a documentation sweep. Anything that needs your attention goes as deep as you
need to act on it. `instructions.md`'s "Talking to the User" holds the table.

## Backlog

The persistent, forward-looking `backlog.md` at a repo's root (formerly named `implementation_plan.md`).
Lists pending and in-progress waves only — a completed wave's section is removed entirely, not marked
done. Grouped into three tiers by descending certainty and immediacy — **Next Up** (ordered, landing soon),
**Planned** (committed, not yet sequenced), **Later Considerations** (ideas that may never be built) — so
an agent can surface just the tier a question's horizon implies instead of the whole file. See
[`../instructions.md`](../instructions.md#backlog-tiers).

## Plan history

The backward-looking counterpart to the backlog: `docs/history/` in a consuming repo, holding one file per
concluded plan (completed, dropped, or superseded) plus a cheap `index.md` of titles and outcomes. Checked
before planning new work, so an agent doesn't re-propose a direction already tried and dropped for a good
reason. Governed by a guardrail — **history informs, it never narrates** — that keeps the reasoning a
history entry surfaces out of code and docs as anything but a present-tense justification; no "first we
tried X, then Y" timelines leak into the docs themselves. See
[`../instructions.md`](../instructions.md#plan-history).

## Plan mode

A Claude Code permission mode that blocks `Edit`/`Write` calls at the harness level — not by convention,
by an actual permission boundary — until the user approves exiting it. Entered via `EnterPlanMode`, exited
via `ExitPlanMode`; exiting always surfaces an approval prompt, with "keep planning with feedback" as a
standing option alongside approving, so a concrete plan can be revised before anything is implemented,
once discussion has already converged in normal mode. General discussion, research, and backlog curation
happen in normal mode, not here — this harness enters plan mode specifically on an explicit signal to lock
in a concrete approach ("let's plan X" / "let's start wave N"), not on every discussion cue — see
[`00-agents-overview.md`](00-agents-overview.md).

## Skill

A markdown file (`SKILL.md`) that Claude Code loads either when its `description` matches the
conversation, or when a file matching its `paths` glob is read or edited, or by explicit `/name`
invocation. Skill content is not loaded by default — it only enters context when triggered — which is why
long procedural conventions (like [`doc-conventions`](02-skills-and-subagents.md)) belong in a skill rather
than always-on `CLAUDE.md` prose.

## Subagent

A separate Claude instance, defined by a markdown file under `.claude/agents/`, with its own system prompt
and (optionally) a restricted tool set. Invoked automatically when its `description` matches, or
explicitly. Starts with a fresh context unless it's a **fork** (below). See
[`02-skills-and-subagents.md`](02-skills-and-subagents.md) for the subagents this harness defines.

## Fork

A subagent that inherits the **full conversation transcript** of whatever spawned it, not just its
system prompt or model, so it already knows everything discussed so far. Cheaper than a fresh subagent for
tasks that need that context, since it reuses the parent's prompt cache. The `langfuse-upgrade` skill uses
one for its investigation. Wave work does not: implementers, `test-author` and `doc-sweep` start fresh
with a self-contained brief. Requires `CLAUDE_CODE_FORK_SUBAGENT=1`, set in `~/.claude/settings.json`'s
`env` block (see [`CLAUDE.md`](../CLAUDE.md)); without it, spawning a fork fails outright rather than
falling back gracefully.

## Skill freshness

The rule that a skill without a `paths:` trigger (anything matched by natural language or invoked
explicitly, rather than auto-loaded on a file pattern) must be invoked via the Skill tool at the moment
its content is actually needed, not recalled from a memory of having read it earlier in the conversation.
Skill content isn't reinjected across context compaction the way `instructions.md`/`CLAUDE.md` are — a
skill read once early in a long session can silently drift from what's actually specified. See
[`CLAUDE.md`](../CLAUDE.md)'s "Skill freshness" section.

## Hook

A script the harness runs automatically on a lifecycle event (see below), independent of whether the model
remembers to do something. Registered in `~/.claude/settings.json`, which is global — a hook registered
there applies to every repo, not just one. Contrast with a **step**: a hook always fires and cannot be
skipped by the model forgetting; a step is just an instruction inside a skill that the model carries out
itself, which means it depends on the model actually doing it. See
[`01-hooks.md`](01-hooks.md) for every hook this harness registers.

## Hook events used in this harness

- **`PreToolUse`** — fires before a tool call executes; can block it (exit code 2) with a message fed back
  to the model, or allow it through.
- **`PostToolUse`** — fires after a tool call executes; can report findings but the action has already
  happened, so it's for feedback (e.g. lint results), not prevention.
- **`SessionStart`** (matcher `compact`) / **`PreCompact`** — fire around a context compaction event.
- **`UserPromptSubmit`** / **`SubagentStart`** — fire at the start of a "round" (see below).

## Round

The span from one handoff to the next: a new user prompt, or a new subagent task, until that agent reports
back. The [web search cap](01-hooks.md#limit-web-searchpy) resets once per round, so a 10-search budget
applies per round, not per session.

## Skills and subagents of the wave loop

`wave`, `coordinate`, `implementer-contract`, the three implementer tiers, `test-author`, `wave-runner` and
`doc-sweep`, alongside `doc-conventions`, `design-conventions`, `ruff-cleanup` and `sdk-release`. See
[`02-skills-and-subagents.md`](02-skills-and-subagents.md) for what each one does.
