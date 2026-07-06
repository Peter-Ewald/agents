# Cross-repo distribution

How one copy of a skill, subagent, or hook script reaches every repo without being copied into any of
them, and the two real gotchas this ran into.

## The mechanism, per kind

| Kind | Distributed via | Why this works |
|---|---|---|
| Subagents | `~/.claude/agents` symlinked once to [`../.claude/agents/`](../.claude/agents/README.md) | Documented, user-level location — applies to every repo automatically. |
| Skills | `~/.claude/skills` symlinked once to [`../.claude/skills/`](../.claude/skills/README.md) | Undocumented, but empirically confirmed working the same way as agents — verified by placing a throwaway probe skill and starting a fresh session in an unrelated repo. |
| Hooks | Registered once in `~/.claude/settings.json` (global) | Hooks were never per-repo to begin with — global settings already apply everywhere, so there's nothing to symlink. |
| Shared conventions (`CLAUDE.md`, `instructions.md`) | A one-line `@~/Projects/agents/CLAUDE.md` import in each repo's own root `CLAUDE.md` | Claude Code resolves `@`-imports at session start, so the repo behaves as if the shared file were pasted in, without it actually being copied. |

Skills briefly went through an intermediate step — a `.claude/skills` symlink in each individual repo,
before user-level `~/.claude/skills` was confirmed to work — which is why some repos' `.gitignore` still
mentions `.claude/skills` defensively even though no repo has that symlink anymore.

## Gotcha 1: a monorepo subdirectory is not a separate repo

`Task Force Evaluation`, `LLM Evaluation Architecture`, and `Litellm-Model integration layer` look like
three project folders, but they're subdirectories of one shared git repository, `Chapter_Repos` — running
`git rev-parse --show-toplevel` from any of them returns `Chapter_Repos`, not the subdirectory itself.

This matters because a `.gitignore` pattern with a slash in it (like `.claude/*`) is anchored to the
directory of the `.gitignore` file that contains it — it does not cascade into subdirectories. Placing the
"Personal Claude Code state" block in `Chapter_Repos/.gitignore` without a `**/` prefix protected nothing
in the three subdirectories; it silently only would have protected a `.claude/` folder placed directly at
the `Chapter_Repos` root, which doesn't exist. The fix is a `**/`-prefixed pattern once at the shared root
(`**/.claude/*`, `**/CLAUDE.md`, etc.), which reaches every subdirectory — present and future — instead of
needing a duplicated, drift-prone copy of the same block in each one.

Each subdirectory still gets its own `CLAUDE.md` stub, though — Claude Code sessions are opened per
subdirectory in this setup, so each needs the import even though git treats them as one repo. A commit
touching gitignore rules for any of the three is one commit in `Chapter_Repos`, not three.

## Gotcha 2: a repo shared with colleagues needs CLAUDE.md kept local

Repos other than this one aren't all personal — `Project Green`, for instance, has colleagues who each
have their own working style and their own `CLAUDE.md` preferences. Two things follow from that:

- The shared-conventions import (`@~/Projects/agents/CLAUDE.md`) is an absolute path specific to this
  machine. Committing it would be meaningless for a colleague who doesn't have that exact directory, so
  every repo that isn't purely personal needs `CLAUDE.md` gitignored, not committed.
- **Gitignoring a file does not retroactively untrack it.** `Project Green/CLAUDE.md` had already been
  committed (with real project architecture content, not just Claude Code preferences) before the import
  line was added — adding `CLAUDE.md` to `.gitignore` stopped *future* edits from being tracked, but the
  file still showed up in `git status` until it was explicitly removed from the index with
  `git rm --cached CLAUDE.md`. The local file is untouched by that command; only git's tracking of it
  stops. Anything in a to-be-untracked file that colleagues should keep receiving needs to move to
  `README.md` or `docs/` (which stay shared) before the file is untracked, not after.

Both `Chapter_Repos` and `ramgpt-next` avoided this because their `CLAUDE.md` files were created fresh in
this repo's own session and never committed — gitignoring them before the first commit meant there was
nothing to untangle.
