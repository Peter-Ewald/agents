# Skills and subagents

Three pieces so far, each chosen for a different reason — see [glossary.md](glossary.md) for what
distinguishes a skill from a subagent from a fork.

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

## What's still missing

The end-of-wave documentation update phase is supposed to use a **forked** agent (full conversation
context) applying `doc-conventions`, rather than either of the two subagents above — that only exists once
the `/wave` skill itself is built. See [`../implementation_plan.md`](../implementation_plan.md).
