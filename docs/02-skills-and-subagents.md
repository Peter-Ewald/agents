# Skills and subagents

Four pieces so far, each chosen for a different reason — see [glossary.md](glossary.md) for what
distinguishes a skill from a subagent from a fork.

## `wave` (skill)

[`../.claude/skills/wave/SKILL.md`](../.claude/skills/wave/SKILL.md)

Drives a wave from `backlog.md` through instructions.md's five phases end-to-end: plan, implement,
documentation update, verification, commit proposal. Runs inline in the main agent rather than forking
itself, since Plan and Implement need to actually happen in the calling conversation — only the
Documentation update phase spins off a fork, for the reason `doc-conventions` below explains. At each
phase transition it updates `TodoWrite` and overwrites `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}`, which
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
