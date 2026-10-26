# agents

A shared Claude Code harness for one user's repos: conventions, skills, subagents, and hooks that make
Claude Code follow the same working style everywhere, without copy-pasting instructions into every repo.

## What's in here

| File / folder | Purpose |
|---|---|
| [`instructions.md`](instructions.md) | Tool-agnostic conventions (working mode, documentation rules, how waves are structured). Shared with other AI coding assistants, not just Claude Code. |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code-specific mechanics that extend `instructions.md` (imports it directly). |
| [`copilot_instructions.md`](copilot_instructions.md) | The GitHub Copilot adapter, parallel to `CLAUDE.md`. |
| [`backlog.md`](backlog.md) | The forward-looking backlog for this repo itself — what's still being built. |
| [`.claude/`](.claude/README.md) | The actual skills, subagents, and hook scripts, distributed to every other repo. |
| [`docs/`](docs/00-agents-overview.md) | Detailed reference docs — start at [`docs/00-agents-overview.md`](docs/00-agents-overview.md). |

## How a repo picks this up

A repo picks up the shared conventions through one import line:

```
@~/Projects/agents/CLAUDE.md
```

In a personal repo, that line is the root `CLAUDE.md` (or its first line, above project-specific content).
In a repo shared with colleagues, it goes in `CLAUDE.local.md` instead — never committed, excluded via
`.git/info/exclude` — so the team's `CLAUDE.md` stays untouched. Claude Code resolves the import at
session start, so the session behaves as if `CLAUDE.md` and `instructions.md` were copied in.

Everything else is per machine, not per repo: `~/.claude/agents` is symlinked to
[`.claude/agents/`](.claude/README.md), each skill is symlinked into `~/.claude/skills/`, and hooks,
statusline, and the subagent model are set once in `~/.claude/settings.json`. See
[`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md) for the details and gotchas.

## Where to go next

- New to this setup? Start with [`docs/00-agents-overview.md`](docs/00-agents-overview.md).
- What's it actually like to use, and what does it standardize?
  [`docs/04-working-with-the-harness.md`](docs/04-working-with-the-harness.md).
- Looking up a specific term? [`docs/glossary.md`](docs/glossary.md).
- Want to know what a specific hook or skill does? [`docs/01-hooks.md`](docs/01-hooks.md) and
  [`docs/02-skills-and-subagents.md`](docs/02-skills-and-subagents.md).
- Curious how the cross-repo symlink setup actually works, including the monorepo gotchas it ran into?
  [`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md).
- What's left to build? [`backlog.md`](backlog.md).
- What was already tried, and why did it end up this way? A consuming repo's own `docs/history/` — see
  `instructions.md`'s *Plan history* section for the convention (this repo has no history yet of its own).
