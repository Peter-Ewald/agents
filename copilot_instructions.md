# GitHub Copilot — Working Instructions

**Before doing anything else this session, read [`instructions.md`](instructions.md).** That file is the shared source of truth for all conventions. The sections below add Copilot-specific mechanics that extend or override it.

Claude Code gets a lot of behavior automatically: a skill that auto-loads when a matching file is touched, a subagent it can spawn with a fresh context, a hook that blocks a tool call outright. Copilot has none of that machinery — no skill auto-loading, no subagents, no hooks, no shell access. So this file's job is to spell the same behavior out as a direct instruction wherever Claude would otherwise get it for free. Where the underlying content already lives in a skill or subagent file under `.claude/`, the section below points at it rather than duplicating it — Copilot can still read any file when told to; it just has nothing that loads one automatically.

---

## Phase tracking

Copilot has no persistent tool for tracking state between responses. At the start of each response during a wave, state the current phase explicitly — e.g. `**Phase: Implement**` — so the conversation stays oriented.

## Shell commands and git

Copilot cannot execute shell commands. Write out the exact command text to copy-paste, formatted as a code block. For commit messages, write the full formatted message as a code block to copy-paste; apply the commit message format from `instructions.md`.

## Documentation conventions

Before editing any `.md` file, read `.claude/skills/doc-conventions/SKILL.md` and apply its rules directly — terminology, glossary placement, README structure, mermaid rendering. Claude Code gets this automatically via path-triggered skill loading (`paths: ["**/*.md"]`); Copilot has no such trigger, so treat this as a deliberate step taken before every markdown edit, never an assumption that the rules are already "loaded."

## Waves

When starting or continuing a wave, read `.claude/skills/wave/SKILL.md` for the five-phase sequence (Plan → Implement → Documentation update → Verification → Commit proposal) and follow it, with these substitutions for tools Copilot doesn't have:

- No `EnterPlanMode`/`ExitPlanMode` — announce "Entering planning discussion" / "Plan approved, moving to Implement" in chat instead, tying into *Phase tracking* above.
- No `TodoWrite` or statusline — phase is only ever visible via the in-response `**Phase: X**` line, as already stated.
- No forked subagent for the Documentation update phase — do that phase's checklist (README files, `docs/*.md`, `docs/glossary.md`, backlog tier cleanup, the `docs/history/` note, `CHANGELOG.md`) inline in the same conversation instead of spawning anything.
- The Plan phase's `docs/history/index.md` check still applies as-is — reading a file needs no special tooling. Only the *writing* side stays unavailable, per *Plan history archiving* below.

## Documentation sweep

When asked to "update documentation" without further scope, read `.claude/agents/doc-sweep.md` and follow its checklist directly in the current conversation — same content, no subagent to spawn.

## Linting, dependencies, changelog ordering

Claude Code gets automatic post-edit linting and pre-commit blocks via hooks (`lint-changed-lines.py`, `flag-new-dependency.py`, `require-changelog-before-commit.py`). Copilot has none of these, and can't run shell to self-check either — so the underlying rules (`instructions.md`'s "No new dependencies without flagging", changelog-before-release ordering) rely purely on remembering, with nothing catching a miss. If lint correctness matters for a given change, ask the user to run `ruff check <file>` themselves and report the result back, rather than assuming a file is clean.

## Plan history archiving

Copilot has no persistent session-plan file to archive (per *Phase tracking* above, phase state lives only in response text) — `docs/history/` (see `instructions.md`, Plan history) stays unpopulated by Copilot sessions for now. Checking `docs/history/index.md` before planning still applies; there's just nothing to add to it from this side yet.
