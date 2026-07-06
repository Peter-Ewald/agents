# Skills and subagents

Four pieces so far, each chosen for a different reason — see [glossary.md](glossary.md) for what
distinguishes a skill from a subagent from a fork.

## `wave` (skill)

[`../.claude/skills/wave/SKILL.md`](../.claude/skills/wave/SKILL.md)

Drives a wave from `implementation_plan.md` through instructions.md's five phases end-to-end: plan,
implement, documentation update, verification, commit proposal. Runs inline in the main agent rather than
forking itself, since Plan and Implement need to actually happen in the calling conversation — only the
Documentation update phase spins off a fork, for the reason `doc-conventions` below explains. At each
phase transition it updates `TodoWrite` and overwrites `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}`, which
the statusline script reads to show the current phase. That path — not the session's own scratchpad
directory — is deliberate: the statusline runs as a separate process that only receives a session ID on
its own stdin, not this session's scratchpad path, so the hand-off point has to be something derivable
from the session ID alone.

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

Triggered by saying "update documentation" without further scope. Tools restricted to `Read`, `Grep`,
`Glob`, `Edit` — no `Bash` — since it's meant to be a pure audit. Deliberately a **fresh** subagent, not a
fork: a full documentation consistency sweep is supposed to re-derive doc-vs-code accuracy from scratch,
cross-checking docs against the actual current implementation, not trust whatever the recent conversation
happened to already believe. Preloads `doc-conventions` via its `skills:` frontmatter field so the same
rules apply without needing a markdown file to be touched first.

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
