# Skills and subagents

Eight pieces so far, each chosen for a different reason — see [glossary.md](glossary.md) for what
distinguishes a skill from a subagent from a fork.

## `wave` (skill)

[`../.claude/skills/wave/SKILL.md`](../.claude/skills/wave/SKILL.md)

Drives a wave from `backlog.md`'s Next Up tier through instructions.md's five phases end-to-end: plan, implement,
documentation update, verification, commit proposal. The main agent keeps the judgment — plan, contracts
between sub-tasks, review, verification, backlog and history, commit — and hands each scoped sub-task in
the plan's sub-task table to the `implementer` subagent below. Only a documentation sweep the backlog
assigns to that specific wave spins off a fork, for the reason `doc-sweep` below explains (needs full
conversation context, unlike `doc-sweep`'s deliberate freshness). Forking requires
`CLAUDE_CODE_FORK_SUBAGENT=1` — set in `~/.claude/settings.json`'s `env` block; without it,
`Agent(subagent_type="fork")` fails outright ("Agent type 'fork' not found"), confirmed by direct testing.
At each phase transition it overwrites `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}`, which
the statusline script reads to show the current phase. That path — not the session's own scratchpad
directory — is deliberate: the statusline runs as a separate process that only receives a session ID on
its own stdin, not this session's scratchpad path, so the hand-off point has to be something derivable
from the session ID alone.

Before writing the session plan (Phase 1), it checks `docs/history/index.md` for prior plans on a related
topic, so it doesn't re-propose a direction already tried and dropped — and if the plan itself gets dropped
instead of approved, it's archived right there in Phase 1, not left to a Documentation update phase it will
never reach. A plan that *does* get approved and completed is archived at Phase 3 instead, alongside the
rest of the Documentation update checklist. See `instructions.md`'s *Plan history* section for the
convention.

## `doc-conventions` (skill)

[`../.claude/skills/doc-conventions/SKILL.md`](../.claude/skills/doc-conventions/SKILL.md)

`paths: ["**/*.md"]` — loads automatically whenever a markdown file is being read or edited, anywhere.
Contains the terminology, glossary-placement, README-structure, and mermaid-rendering conventions that
used to live as always-on prose in `instructions.md`. Moving it into a path-scoped skill means it only
enters context when a markdown edit is actually happening, instead of competing for attention the entire
session regardless of whether any docs are being touched — and it's the single definition both `doc-sweep`
(below) and the eventual `/wave` documentation phase apply, rather than two competing copies.

## `implementer` (subagent)

[`../.claude/agents/implementer.md`](../.claude/agents/implementer.md)

Carries out one sub-task from an approved wave plan: the files it owns, the contract the plan fixed, and
the acceptance check that proves it. Runs on Sonnet at medium effort with a fresh context, so the many
edit-and-test calls of implementation re-read a small context on a cheaper model instead of the main
agent's full conversation on Opus — the context size is the larger part of that saving. It never plans or
widens its scope: an ambiguous contract or a needed file outside its brief is a `blocked` report, which
sends the decision back to the main agent. The report has a fixed five-line shape with no diffs, because
the main agent reviews the diff itself and every line of report stays in its context for the rest of the
wave. No `Agent` tool, so it cannot delegate further.

## `doc-sweep` (subagent)

[`../.claude/agents/doc-sweep.md`](../.claude/agents/doc-sweep.md)

Triggered by saying "update documentation" without further scope, or invoked directly for a scoped
documentation rewrite. Full tool access (`Read`, `Grep`, `Glob`, `Edit`, `Bash`, `Write`) — a sweep can
rename, split, merge, or create documentation files as the reorganization requires, not just edit content
in place. Deliberately a **fresh** subagent, not a fork: a full documentation consistency sweep is supposed
to re-derive doc-vs-code accuracy from scratch, cross-checking docs against the actual current
implementation, not trust whatever the recent conversation happened to already believe. Preloads
`doc-conventions` via its `skills:` frontmatter field so the same rules apply without needing a markdown
file to be touched first — this is also why it's the right subagent for a documentation-restructuring task
in general, not just the bare "update documentation" trigger phrase: a `general-purpose` agent has the same
tool access but doesn't get `doc-conventions` preloaded, so it would need the rules pasted into its prompt
by hand.

Also checks `docs/history/index.md` (if present) for entries relevant to the area being swept, to write a
better-grounded "why" for existing patterns — but per the *Plan history* guardrail in `instructions.md`,
that history is synthesized into a present-tense explanation, never narrated as a timeline in the doc
itself.

See `instructions.md`'s "Documentation update: choosing the mechanism" for how this fits alongside a
small inline edit and `wave`'s own forked Documentation update phase — three distinct shapes, not
interchangeable.

## `design-conventions` (skill)

[`../.claude/skills/design-conventions/SKILL.md`](../.claude/skills/design-conventions/SKILL.md)

Design and architecture principles — naming, module boundaries, error-handling philosophy, interface
discipline — the code-design equivalent of `doc-conventions` (documentation quality) and
`ruff-cleanup/RULES.md` (lint-fix quality). One file, not split like `ruff-cleanup`: design principles
are narrative/read-and-apply, not a growing per-code lookup table. No `paths:` trigger — there's no
file-glob that means "about to make a design decision" the way `**/*.md` means "editing a markdown
file" — so it relies on natural-language matching plus explicit invocation from `instructions.md`'s Plan
phase bullet and `wave/SKILL.md`'s Phase 1, both of which invoke it via the Skill tool per `CLAUDE.md`'s
"Skill freshness" note rather than working from a remembered read.

Seeded with five starter principles (naming clarity, boundary and ownership clarity, fail loud not
silent, consistency over cleverness, minimum-contract interfaces) deliberately avoiding overlap with
Claude Code's own baseline instructions — expected to grow from real cases the same way `RULES.md` does.

## `ruff-cleanup` (skill)

[`../.claude/skills/ruff-cleanup/SKILL.md`](../.claude/skills/ruff-cleanup/SKILL.md)

Triggered by "clean up remaining ruff issues" or similar, or invoked directly (`/ruff-cleanup`). A
**skill**, not a subagent like `doc-sweep` — runs inline in the main conversation, the same reason
`wave`'s Implement phase stays inline: `doc-sweep` needs to be fresh specifically to avoid the agent's
own potential self-serving read of "is this doc still accurate," but `ruff check`'s output is an
external, objective source of truth regardless of what the conversation believes, so there's no
analogous bias risk here — and the skill benefits from the conversation's own context on why recent
edits were made.

Defaults to PR-diff scope (files changed vs. the base branch, not the whole repo) — matches "minimal
changes" and the literal "clean up before a PR" framing; whole-repo only runs if explicitly requested.
Everything it finds already survived the `ruff-autofix` hook's safe fixes on every edit along the way,
so by definition it needs either an unsafe fix or actual code judgment. Consults
[`RULES.md`](../.claude/skills/ruff-cleanup/RULES.md) — a house-rules file mapping specific ruff codes
to this codebase's fix guidance — and refuses to improvise a fix for a code with no entry: it drafts a
proposed entry, waits for confirmation, appends it, then applies it. `RULES.md` is seeded with F401,
F841, E501, and B006 on day one and is expected to grow the same way S_Factory's break-agent checklist
grew — one confirmed real case at a time, never bulk-authored ahead of an actual encounter. Bounded
retry (three attempts total) rather than an unbounded loop, consistent with this harness being
interactive/human-reviewed at every step rather than an autonomous pipeline. Finishes by pointing at
`wave/SKILL.md`'s existing test-command-detection instruction rather than restating it.

## `sdk-release` (skill)

[`../.claude/skills/sdk-release/SKILL.md`](../.claude/skills/sdk-release/SKILL.md)

Releases `semantic_tracing` or `semantic_evaluation`: checks the changelog has an entry for the target
version, then runs the bundled [`scripts/release.sh`](../.claude/skills/sdk-release/scripts/release.sh)
(version bump, `rm -rf dist/`, `uv sync`, `uv build`, `uv publish --index ramtech-pypi`, then stages
`pyproject.toml` + `CHANGELOG.md` + `uv.lock` together — it does not commit). Bundled as an actual script
rather than prose instructions the model reproduces from memory each time, since the exact command and
flags (`uv publish --index ramtech-pypi dist/<package>-<version>*`) are exactly the kind of thing that's
easy to mistype once and shouldn't depend on being remembered correctly. After a successful release it
also checks other repos in the workspace for stale version pins and reports them — it doesn't bump those
repos automatically.

## `langfuse-upgrade` (skill)

[`../.claude/skills/langfuse-upgrade/SKILL.md`](../.claude/skills/langfuse-upgrade/SKILL.md)

Triggered by pasting a langfuse changelog/release notes, mentioning a new langfuse version, or asking to
check/upgrade the langfuse dependency — both `semantic_tracing` and `semantic_evaluation` wrap the
`langfuse` Python SDK directly, and it has a track record of removing REST client methods inside otherwise
normal minor releases, so a new release is worth checking deliberately rather than just bumping the
version constraint.

Investigates via a **forked** agent with `isolation: "worktree"` — a fork rather than a fresh subagent
because it needs the session's existing understanding of both SDKs without re-explaining the repo, and a
worktree because it bumps a dependency and runs real installs/tests, which must never touch the actual
working directory or its uncommitted changes. The fork reads the real changelog, temporarily pins the
target version in both packages, runs both test suites, greps for every langfuse surface each package
actually uses, and returns per-package findings: what broke, why, a proposed fix, and a SemVer
classification (patch if the fix stays internal, major if it forces a public-API change) per
`instructions.md`'s published-package policy.

Nothing is applied from the worktree — the main conversation presents the findings and versioning
consequence in chat and waits for explicit agreement (mirroring a wave's Plan-phase gate) before applying
anything for real in the actual checkout. Ends by writing each affected package's `CHANGELOG.md` entry
under the agreed next version — the exact entry `sdk-release` (above) checks for — and drafting a commit
message, but deliberately stops short of bumping `pyproject.toml`'s version number or publishing: that
handoff to `sdk-release` is intentional, since `sdk-release` already expects the changelog entry this skill
just wrote.
