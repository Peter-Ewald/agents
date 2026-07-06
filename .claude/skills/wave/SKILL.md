---
name: wave
argument-hint: [wave-name-or-number]
description: Runs a wave from implementation_plan.md through its five phases end to end — plan, implement, documentation update, verification, commit proposal — per instructions.md's Implementation Waves section. Use when starting or continuing work on a specific pending wave, or when the user says things like "let's start wave 2" / "continue wave 3".
---

Drive the target wave (identified by `$ARGUMENTS`, or the next one in `implementation_plan.md`'s
processing-order table if unspecified) through all five phases from `instructions.md`'s Implementation
Waves section. Run inline — do not fork yourself for this; only the Documentation update phase below
forks.

At every phase transition:
1. Update the `TodoWrite` list so exactly one of the five phases is `in_progress` and prior phases are
   `completed`.
2. Overwrite `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}` with one line: `<wave name> — <phase name>`.
   Use this exact path, not the scratchpad directory — the statusline script that reads it is a separate
   process that only knows the session ID (from its own stdin), not this session's scratchpad path, so the
   file has to live somewhere derivable from the session ID alone.

## 1. Plan

Call `EnterPlanMode`. Read `implementation_plan.md` and locate the target wave. Write (or refine) the
session plan — see `CLAUDE.md`'s "Session plan location" for where — expanding the wave's tasks into
concrete steps: exact files to touch, exact verification commands, exit criteria. Stay in this phase for
as long as discussion continues, revising the plan on feedback. Call `ExitPlanMode` only once ready.

## 2. Implement

Normal coding against the approved plan. The lint hook (`lint-changed-lines.py`) and dependency hook
(`flag-new-dependency.py`) fire automatically on the relevant file edits — nothing extra to invoke here.

## 3. Documentation update

Spawn a forked agent (the `Agent` tool with `subagent_type: fork`) so it inherits full awareness of what
was just implemented. Its task prompt must explicitly tell it to:

- Apply the `doc-conventions` skill's rules (terminology, glossary placement, README structure,
  markdown/mermaid rendering).
- Follow the "Documentation update phase" checklist in `instructions.md` (README files, `docs/*.md`,
  `docs/glossary.md`, removing the completed wave's section from `implementation_plan.md`, `CHANGELOG.md`
  if a package was released).

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

Mark the wave done (remove its section from `implementation_plan.md`, per Wave 3's own instructions) only
after verification has actually passed.
