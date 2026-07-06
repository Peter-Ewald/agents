# Implementation Plan

Forward-looking backlog for turning `instructions.md` / `CLAUDE.md` from shared prose into a real Claude
Code harness — native plan mode, skills, subagents, and hooks doing the enforcement that prose currently
only asks for. Detailed enough to implement directly; anything still genuinely open is called out inline.

Everything up through dependency/release hooks is already built — see
[`docs/00-agents-overview.md`](docs/00-agents-overview.md) for how the pieces fit together,
[`docs/01-hooks.md`](docs/01-hooks.md) and [`docs/02-skills-and-subagents.md`](docs/02-skills-and-subagents.md)
for what each one does, and [`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md) for
how distribution works and the two gotchas it ran into.

## Suggested processing order

| Step | Wave | Depends on |
|---|---|---|
| 1 | `/wave` skill | — |
| 2 | Statusline | 1 |
| 3 | Instruction trimming | 1 |
| 4 | Permission allowlist | 1 |

## Wave 1: `/wave` skill

`agents/.claude/skills/wave/SKILL.md` — ties the existing plan-mode behavior, `doc-conventions` /
`doc-sweep`, the lint/dependency/changelog hooks, and `sdk-release` together into the five wave phases,
driving `TodoWrite` itself at each phase transition instead of relying on being reminded:

1. **Plan** — call `EnterPlanMode`, read `implementation_plan.md`, draft/refine the session plan for as
   long as discussion continues, call `ExitPlanMode` when ready.
2. **Implement** — normal coding against the approved plan; the lint hook and dependency hook fire
   automatically during this phase without the skill needing to invoke them.
3. **Documentation update** — fork the conversation and apply `doc-conventions`.
4. **Verification** — run tests as a step, triage pre-existing vs. new failures.
5. **Commit proposal** — draft the message per the template in `instructions.md`; wait for explicit
   confirmation before the real `git commit` runs.

Exit criteria: invoking `/wave` on a real pending wave runs all five phases with the right gating at each
step, with no phase requiring a manual reminder.

## Wave 2: Statusline

1. `/wave` writes the current phase to a small state file per session (e.g.
   `/tmp/claude-wave-phase-<session_id>`) at each phase transition.
2. A statusline script reads that file and prints the current wave name and phase; registered under
   `statusLine` in `~/.claude/settings.json`.

Exit criteria: the statusline shows the current wave phase during a `/wave` run and updates as phases
progress.

## Wave 3: Instruction trimming

1. Consistency pass over `CLAUDE.md` / `instructions.md` to confirm nothing relocated to a skill/subagent/
   hook was left behind as stale duplicate prose.
2. Remove rules that duplicate Claude Code's own default harness behavior (git safety protocol,
   confirm-before-destructive-command, no `Co-Authored-By` trailers, propose-before-running) — keep only
   the deltas from default behavior.
3. Apply the native rewrite check to both files afterward, since this will be a substantial edit.

Exit criteria: both files contain only genuinely foundational, non-duplicated, tool-agnostic content.

## Wave 4: Permission allowlist

Run `fewer-permission-prompts` once the hooks and skills built so far have been exercised a few times and
generated their own repeated approval prompts. Given auto-mode has been reliable in practice (the one
incident was the unbounded web-search loop, now mechanically capped), lean toward accepting its suggested
allowlist broadly rather than hand-pruning it.

Exit criteria: routine read-only commands used by the new hooks/skills stop prompting for approval.
