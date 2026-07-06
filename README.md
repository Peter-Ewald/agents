# agents

A shared Claude Code harness for one user's repos: conventions, skills, subagents, and hooks that make
Claude Code follow the same working style everywhere, without copy-pasting instructions into every repo.

## What's in here

| File / folder | Purpose |
|---|---|
| [`instructions.md`](instructions.md) | Tool-agnostic conventions (working mode, documentation rules, how waves are structured). Shared with other AI coding assistants, not just Claude Code. |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code-specific mechanics that extend `instructions.md` (imports it directly). |
| [`copilot_instructions.md`](copilot_instructions.md) | The GitHub Copilot adapter, parallel to `CLAUDE.md`. |
| [`implementation_plan.md`](implementation_plan.md) | The forward-looking backlog for this repo itself — what's still being built. |
| [`.claude/`](.claude/README.md) | The actual skills, subagents, and hook scripts, distributed to every other repo. |
| [`docs/`](docs/00-agents-overview.md) | Detailed reference docs — start at [`docs/00-agents-overview.md`](docs/00-agents-overview.md). |

## How a repo picks this up

Every other repo gets a one-line root `CLAUDE.md`:

```
@~/Projects/agents/CLAUDE.md
```

Claude Code resolves that import at session start, so the repo's session behaves exactly as if
`CLAUDE.md` and `instructions.md` were copied in — without actually copying them. Skills and subagents
reach every repo the same way, via `~/.claude/skills` and `~/.claude/agents` each symlinked once to the
folders in [`.claude/`](.claude/README.md) here. Hooks need no distribution step at all — they're
registered once in `~/.claude/settings.json`, which already applies globally.

If a repo already has its own `CLAUDE.md` with project-specific content (as opposed to one of these thin
stubs), the import line is added to the top of that file instead of replacing it — see that repo's
`CLAUDE.md` for the split between shared and project-specific guidance.

## Where to go next

- New to this setup? Start with [`docs/00-agents-overview.md`](docs/00-agents-overview.md).
- Looking up a specific term? [`docs/glossary.md`](docs/glossary.md).
- Want to know what a specific hook or skill does? [`docs/01-hooks.md`](docs/01-hooks.md) and
  [`docs/02-skills-and-subagents.md`](docs/02-skills-and-subagents.md).
- Curious how the cross-repo symlink setup actually works, including the monorepo gotchas it ran into?
  [`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md).
- What's left to build? [`implementation_plan.md`](implementation_plan.md).
