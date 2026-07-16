---
name: wave
argument-hint: [wave-name-or-number]
description: Runs a wave from backlog.md through its five phases end to end — plan, implement, documentation update, verification, commit proposal — per instructions.md's Implementation Waves section. Use when starting or continuing work on a specific pending wave, or when the user says things like "let's start wave 2" / "continue wave 3".
---

Drive the target wave (identified by `$ARGUMENTS`, or the next one in `backlog.md`'s Next Up tier if
unspecified) through all five phases from `instructions.md`'s Implementation Waves section. Run inline —
do not fork yourself for this; only the Documentation update phase below forks.

At every phase transition:
1. Update the `TodoWrite` list so exactly one of the five phases is `in_progress` and prior phases are
   `completed`.
2. Overwrite `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}` with one line: `<wave name> — <phase name>`.
   Use this exact path, not the scratchpad directory — the statusline script that reads it is a separate
   process that only knows the session ID (from its own stdin), not this session's scratchpad path, so the
   file has to live somewhere derivable from the session ID alone.

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
wave's tasks into concrete steps: exact files to touch, exact verification commands, exit criteria. Before
finalizing, invoke `design-conventions` via the Skill tool (per `CLAUDE.md`'s "Skill freshness" — don't
work from memory of an earlier read) and check the approach against it. Stay in this phase for as long as
discussion continues, revising the plan on feedback. Call `ExitPlanMode` only once ready.

If the discussion concludes without proceeding to Implement — the plan is dropped rather than approved —
archive it anyway, per `CLAUDE.md`'s "Plan history archiving", with outcome `dropped` and the reason given,
before ending the discussion. A dropped plan is exactly the kind of thing a future wave should be able to
find in `docs/history/`.

## 2. Implement

Normal coding against the approved plan. The lint hook (`lint-changed-lines.py`) and dependency hook
(`flag-new-dependency.py`) fire automatically on the relevant file edits — nothing extra to invoke here.

## 3. Documentation update

Spawn a forked agent (the `Agent` tool with `subagent_type: fork`) so it inherits full awareness of what
was just implemented. Its task prompt must explicitly tell it to:

- Apply the `doc-conventions` skill's rules (terminology, glossary placement, README structure,
  markdown/mermaid rendering).
- Follow the "Documentation update phase" checklist in `instructions.md` (README files, `docs/*.md`,
  `docs/glossary.md`, removing the completed wave's section from `backlog.md`, archiving the session plan
  to `docs/history/` per `CLAUDE.md`'s "Plan history archiving", `CHANGELOG.md` if a package was released).

Do this even if no `.md` file was touched during Implement — path-based skill triggering only fires on
markdown edits, and this phase needs the conventions regardless.

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
per Phase 3's own instructions) only after verification has actually passed.
