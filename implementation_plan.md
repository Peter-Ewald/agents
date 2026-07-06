# Implementation Plan

Forward-looking backlog for turning `instructions.md` / `CLAUDE.md` from shared prose into a real Claude
Code harness — native plan mode, skills, subagents, and hooks doing the enforcement that prose currently
only asks for. Detailed enough to implement directly; anything still genuinely open is called out inline.

Everything through the `wave` skill and statusline is already built — see
[`docs/00-agents-overview.md`](docs/00-agents-overview.md) for how the pieces fit together,
[`docs/01-hooks.md`](docs/01-hooks.md) and [`docs/02-skills-and-subagents.md`](docs/02-skills-and-subagents.md)
for what each one does, and [`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md) for
how distribution works and the two gotchas it ran into.

## Suggested processing order

| Step | Wave | Depends on |
|---|---|---|
| 1 | Instruction trimming | — |
| 2 | Permission allowlist | — |

## Wave 1: Instruction trimming

1. Consistency pass over `CLAUDE.md` / `instructions.md` to confirm nothing relocated to a skill/subagent/
   hook was left behind as stale duplicate prose.
2. Remove rules that duplicate Claude Code's own default harness behavior (git safety protocol,
   confirm-before-destructive-command, no `Co-Authored-By` trailers, propose-before-running) — keep only
   the deltas from default behavior.
3. Apply the native rewrite check to both files afterward, since this will be a substantial edit.

Exit criteria: both files contain only genuinely foundational, non-duplicated, tool-agnostic content.

## Wave 2: Permission allowlist

Run `fewer-permission-prompts` once the hooks and skills built so far have been exercised a few times and
generated their own repeated approval prompts. Given auto-mode has been reliable in practice (the one
incident was the unbounded web-search loop, now mechanically capped), lean toward accepting its suggested
allowlist broadly rather than hand-pruning it.

Exit criteria: routine read-only commands used by the new hooks/skills stop prompting for approval.
