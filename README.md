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

Without any file in the repo. The setup is per machine:

| What | How |
|---|---|
| Shared conventions | `~/.claude/rules/agents-harness.md` holds the single line `@~/Projects/agents/CLAUDE.md`. Claude Code loads it in every project and every worktree, so each session behaves as if `CLAUDE.md` and `instructions.md` were copied in |
| Subagents | `~/.claude/agents` is symlinked to [`.claude/agents/`](.claude/README.md) |
| Skills | Each skill is symlinked into `~/.claude/skills/` |
| Hooks, statusline, subagent model | Set once in `~/.claude/settings.json` |

The one per-repo file is an optional `.worktreeinclude`, which copies gitignored files such as `.env` into
the worktrees Claude Code creates. See
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
