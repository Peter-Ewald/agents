# Implementation Plan

Forward-looking backlog for turning `instructions.md` / `CLAUDE.md` from shared prose into a real Claude
Code harness — native plan mode, skills, subagents, and hooks doing the enforcement that prose currently
only asks for. Detailed enough to implement directly; anything still genuinely open is called out inline.

Cross-repo distribution is already in place: shared subagents, skills, and hooks live under this repo's
`.claude/` (see [`.claude/README.md`](.claude/README.md)), exposed to other repos via `~/.claude/agents`
and a per-repo `.claude/skills` symlink. Whether Claude Code also honors a user-level `~/.claude/skills`
directory (which would let the per-repo symlinks collapse into one) is still unverified — see
`~/.claude/skills/test-probe/SKILL.md` for the pending manual check.

Known repos in scope for repo-root changes (Wave 1): this repo (`agents`), `Task Force Evaluation`
(contains `sdk/semantic_tracing`, `sdk/semantic_evaluation`), `LLM Evaluation Architecture`, `Project Green`,
`ramgpt-next`, `Litellm-Model integration layer`. Extend to other repos as they come up.

## Suggested processing order

| Step | Wave | Depends on |
|---|---|---|
| 1 | CLAUDE.md import + compaction resilience | — |
| 2 | Plan mode integration | — |
| 3 | Documentation handling | — |
| 4 | Verification approach | — |
| 5 | Web search rate limiting | — |
| 6 | Dependency and release hooks | — |
| 7 | `/wave` skill | 2, 3, 4, 6 |
| 8 | Statusline | 7 |
| 9 | Instruction trimming | 1, 2, 3, 4, 6, 7 |
| 10 | Permission allowlist | 5, 6, 7 |

## Wave 1: CLAUDE.md import + compaction resilience

Tasks:

1. In this repo's `CLAUDE.md`, replace the line *"Before doing anything else this session, read
   `instructions.md`."* with a structural import: `@instructions.md`.
2. Create a root `CLAUDE.md` in each of the other repos listed at the top of this file, containing exactly
   one line: `@~/Projects/agents/CLAUDE.md`. Today none of those repos have a root `CLAUDE.md` at all, so
   Claude Code currently has nothing to auto-load there — this is the actual fix for "I have to remind
   Claude to re-read the instructions," not just a cleanup.
3. Add `agents/.claude/hooks/reinject-instructions.sh`: concatenates `~/Projects/agents/CLAUDE.md` and
   `~/Projects/agents/instructions.md` (following the one-level `@import` manually, since a hook is a plain
   script and doesn't get Claude Code's import resolution) and returns the result as
   `hookSpecificOutput.additionalContext`.
4. Register that script in `~/.claude/settings.json` under both `PreCompact` and `SessionStart` (matcher:
   `source == "compact"`) — belt-and-suspenders, independent of whatever the automatic root-`CLAUDE.md`
   re-injection does with the `@import` on its own (undocumented whether re-injection re-resolves imports).

Exit criteria: triggering compaction mid-session still leaves the full instructions content, not just the
one-line stub, visibly present in context afterward.

## Wave 2: Plan mode integration

Instruction-only wave, no new files:

1. In `instructions.md`'s "Working Mode" section, describe the trigger behavior: on cues like "let's plan
   X" / "let's discuss X," call `EnterPlanMode`; on cues like "let's implement X," call `ExitPlanMode`.
   Plan mode natively supports iterative refinement (discuss, revise, discuss again) via its own
   "keep planning with feedback" option — only an explicit approval ends the phase, so no extra scaffolding
   is needed to support back-and-forth before implementation starts.
2. Rewrite `CLAUDE.md`'s "Chat vs. file updates" section to point at plan mode instead of the manual
   "wait for me to say 'update code'" convention it currently describes.

Exit criteria: next session, saying "let's plan X" results in the agent calling `EnterPlanMode` without
being told to; saying "let's implement Y" results in `ExitPlanMode` being called and a real approval prompt
appearing.

## Wave 3: Documentation handling

Tasks:

1. Create `agents/.claude/skills/doc-conventions/SKILL.md`:
   - Frontmatter: `name: doc-conventions`, `paths: ["**/*.md"]`, description covering terminology,
     glossary placement, README structure, and markdown/mermaid rendering rules.
   - Body: the current "Documentation" section of `instructions.md`, relocated (terminology and
     definitions, glossary placement and linking, READMEs and local explanations, markdown preview
     compatibility including the 10 mermaid rendering rules).
2. Create `agents/.claude/agents/doc-sweep.md`:
   - Frontmatter: `name: doc-sweep`, `tools: Read, Grep, Glob, Edit` (no Bash), `skills: [doc-conventions]`.
   - Description: ad hoc full documentation consistency sweep, triggered by "update documentation" without
     further scope — deliberately fresh (no wave/implementation context), re-derives doc-vs-code accuracy
     from scratch.
   - Body: the current "Documentation Sweeps" procedure from `instructions.md` (re-read READMEs/docs/
     glossaries; check for stale references, undefined/duplicate terms, inconsistent naming, completed
     waves still listed, broken links, mermaid violations; cross-check against source; propose fixes as a
     plan before applying).
3. Remove the relocated "Documentation" and "Documentation Sweeps" sections from `instructions.md` once
   copied over — this is a move, not a duplication.
4. The end-of-wave documentation-update phase (built in Wave 7) uses a **forked** agent instead of
   `doc-sweep`, so it inherits full awareness of what was just implemented. Its task prompt explicitly
   points at `doc-conventions`'s content so the conventions apply even if no `.md` file was touched yet
   during implementation (which is what would normally trigger the skill).

Exit criteria: editing a README triggers `doc-conventions` to load; saying "update documentation" invokes
`doc-sweep`; a `/wave` documentation phase produces output consistent with `doc-conventions` even when the
skill wasn't separately triggered during implementation.

## Wave 4: Verification approach

Tasks:

1. Create `agents/.claude/hooks/lint-changed-lines.sh`:
   - `PostToolUse` hook, matcher: `Edit|Write` on `*.py`.
   - Logic: run `ruff check` on the file, determine which line ranges the tool call actually changed, and
     block (exit 2) only if a reported violation falls within a changed range. Pre-existing violations
     elsewhere in the same file are reported but never block — confirmed preference, since blocking on
     debt you didn't introduce would be disruptive across repos with varying lint history.
   - Registered in `~/.claude/settings.json` under `PostToolUse`.
2. The `/wave` verification phase (Wave 7) runs the test suite as a **step** — the main agent runs it
   inline with its own tools, compares failures against a baseline, and explicitly separates pre-existing
   failures from new ones in its report. No subagent for this yet; only introduce a forked subagent later
   if test output volume starts crowding the main thread's context.

Exit criteria: a new lint violation on a line the edit actually touched blocks with a clear message; a
pre-existing violation elsewhere in the same file does not.

## Wave 5: Web search rate limiting

Applies to both the main agent and subagents: no more than 10 `WebSearch` calls in a single round, where a
round runs from one handoff to the next (a new user prompt, or a new subagent task, until that agent
reports back). Scoped to the `WebSearch` tool specifically for now, not `WebFetch`.

Tasks:

1. Create `agents/.claude/hooks/limit-web-search.sh` with two modes:
   - **Reset**: zero a per-round counter file (keyed by session/agent id, e.g.
     `/tmp/claude-search-count-<session_id>-<agent_id>`).
   - **Check**: increment the counter; if the new count exceeds 10, block (exit 2) with a message telling
     the agent to report findings back before continuing, per the confirmed hard-block preference.
2. Register in `~/.claude/settings.json`:
   - `UserPromptSubmit` → reset mode
   - `SubagentStart` → reset mode
   - `PreToolUse` (matcher: `WebSearch`) → check mode

Exit criteria: an 11th `WebSearch` call within one round is blocked with a clear message; the counter
resets cleanly on the next user turn or new subagent task.

## Wave 6: Dependency and release hooks

Tasks:

1. `agents/.claude/hooks/flag-new-dependency.sh`:
   - `PreToolUse` hook, matcher: `Edit|Write` on `pyproject.toml` / `package.json` / `requirements*.txt`.
   - Logic: diff the proposed content (from `tool_input`) against the file on disk; if a dependency name
     appears that wasn't present before (not just a version-string change on an existing entry), block
     (exit 2) asking for the addition to be flagged in chat with reason + alternatives first.
2. `agents/.claude/hooks/require-changelog-before-commit.sh`:
   - `PreToolUse` hook, matcher: `Bash` commands matching `git commit`.
   - Logic: if `git diff --cached` shows a version bump in a staged `pyproject.toml`, require that
     package's `CHANGELOG.md` to also be staged; block if not.
3. `agents/.claude/skills/sdk-release/SKILL.md` + `scripts/release.sh <package> <version>`:
   - Assumes invocation from within the `Task Force Evaluation` repo, where `sdk/<package>/` lives.
   - Steps: bump `sdk/<package>/pyproject.toml` version → verify `CHANGELOG.md` already has an entry for
     that version (fail if not — changelog-before-commit ordering, confirmed) → `rm -rf sdk/<package>/dist/`
     → `uv sync` → `uv build` → `uv publish --index ramtech-pypi dist/<package>-<version>*` (no explicit
     auth handling needed — `uv` reads credentials from `~/.netrc`, confirmed already configured) → stage
     `pyproject.toml`, `CHANGELOG.md`, and `uv.lock` together, leaving them for the normal commit-proposal
     flow rather than committing itself.
4. Cross-repo version-alignment step (used inside `/wave` or invoked standalone): greps the workspace's
   other mounted repos for `semantic_tracing` / `semantic_evaluation` pins in their `pyproject.toml` /
   lockfiles and flags mismatches against the version just released. Discovers repos dynamically from the
   current session's working directories rather than a hardcoded list.

Exit criteria: adding a new dependency blocks with a flag reminder; a version-only change does not;
committing a version bump without a changelog entry blocks; `sdk-release` runs the full sequence
end-to-end.

## Wave 7: `/wave` skill

`agents/.claude/skills/wave/SKILL.md` — ties Waves 2, 3, 4, 6 together into the five wave phases, driving
`TodoWrite` itself at each phase transition instead of relying on being reminded:

1. **Plan** — call `EnterPlanMode`, read `implementation_plan.md`, draft/refine the session plan for as
   long as discussion continues, call `ExitPlanMode` when ready (Wave 2's mechanism).
2. **Implement** — normal coding against the approved plan; the lint hook (Wave 4) and dependency hook
   (Wave 6) fire automatically during this phase without the skill needing to invoke them.
3. **Documentation update** — fork the conversation (Wave 3) and apply `doc-conventions`.
4. **Verification** — run tests as a step (Wave 4), triage pre-existing vs. new failures.
5. **Commit proposal** — draft the message per the template in `instructions.md`; wait for explicit
   confirmation before the real `git commit` runs.

Exit criteria: invoking `/wave` on a real pending wave runs all five phases with the right gating at each
step, with no phase requiring a manual reminder.

## Wave 8: Statusline

1. `/wave` writes the current phase to a small state file per session (e.g.
   `/tmp/claude-wave-phase-<session_id>`) at each phase transition.
2. A statusline script reads that file and prints the current wave name and phase; registered under
   `statusLine` in `~/.claude/settings.json`.

Exit criteria: the statusline shows the current wave phase during a `/wave` run and updates as phases
progress.

## Wave 9: Instruction trimming

After Waves 1–7 land:

1. Consistency pass over `CLAUDE.md` / `instructions.md` to confirm nothing relocated to a skill/subagent/
   hook was left behind as stale duplicate prose.
2. Remove rules that duplicate Claude Code's own default harness behavior (git safety protocol,
   confirm-before-destructive-command, no `Co-Authored-By` trailers, propose-before-running) — keep only
   the deltas from default behavior.
3. Apply the native rewrite check to both files afterward, since this will be a substantial edit.

Exit criteria: both files contain only genuinely foundational, non-duplicated, tool-agnostic content.

## Wave 10: Permission allowlist

Run `fewer-permission-prompts` once the Wave 5/6/7 hooks and skills have been exercised a few times and
generated their own repeated approval prompts. Given auto-mode has been reliable in practice (the one
incident was the unbounded web-search loop, now mechanically capped by Wave 5), lean toward accepting its
suggested allowlist broadly rather than hand-pruning it.

Exit criteria: routine read-only commands used by the new hooks/skills stop prompting for approval.
