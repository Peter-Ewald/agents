# Glossary

Repository-wide terms for the `agents` harness. Package- or service-local terms would go in that
package's own `docs/glossary.md` instead — this repo has none of those, everything here is cross-repo by
design.

## Wave

One coherent slice of change that lands as a single completed objective, not a single commit. Every wave
runs through five phases in order: Plan, Implement, Documentation update, Verification, Commit message
proposal. See [`../instructions.md`](../instructions.md#implementation-waves) for the full definition and
[`00-agents-overview.md`](00-agents-overview.md) for how the phases map onto this harness's mechanisms.

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
standing option alongside approving, so a plan can be discussed and revised indefinitely before anything
is implemented. This harness enters/exits it automatically on natural-language cues ("let's plan X" /
"let's implement X") rather than requiring a manual UI toggle — see
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
[`02-skills-and-subagents.md`](02-skills-and-subagents.md) for the two subagents this harness defines.

## Fork

A subagent that inherits the **full conversation transcript** of whatever spawned it — not just its
system prompt or model — so it already knows everything discussed or implemented so far. Cheaper than a
fresh subagent for tasks that need that context, since it reuses the parent's prompt cache. Used for the
end-of-wave documentation update (needs to know what was just built), not for the ad hoc `doc-sweep`
(deliberately wants a fresh, no-context read of the repo instead).

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

## Doc-conventions / doc-sweep / ruff-cleanup / design-conventions / sdk-release

Five of the skill/subagent pieces this harness currently ships (alongside `wave`). See
[`02-skills-and-subagents.md`](02-skills-and-subagents.md) for what each one does.
