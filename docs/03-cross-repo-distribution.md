# Cross-repo distribution

How one copy of a skill, subagent, or hook script reaches every repo without being copied into any of
them, and the two real gotchas this ran into.

## The mechanism, per kind

| Kind | Distributed via | Why this works |
|---|---|---|
| Subagents | `~/.claude/agents` symlinked once to [`../.claude/agents/`](../.claude/agents/README.md) | Documented, user-level location — applies to every repo automatically. |
| Skills | Each skill folder in [`../.claude/skills/`](../.claude/skills/README.md) symlinked individually into `~/.claude/skills/` | Documented: a `<skill-name>` entry in the personal skills location may be a symlink to a directory elsewhere. `~/.claude/skills/` itself stays a real directory, see Gotcha 3. |
| Hooks | Registered once in `~/.claude/settings.json` (global) | Hooks were never per-repo to begin with — global settings already apply everywhere, so there's nothing to symlink. |
| Shared conventions (`CLAUDE.md`, `instructions.md`) | A one-line `@~/Projects/agents/CLAUDE.md` import — in the repo's root `CLAUDE.md` for a personal repo, in `CLAUDE.local.md` for a shared one | Claude Code resolves `@`-imports at session start, so the repo behaves as if the shared file were pasted in, without it actually being copied. |

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

## Gotcha 2: a repo shared with colleagues keeps the import out of git

Repos other than this one aren't all personal — `Project Green` and `Task Force Evaluation`, for instance,
have colleagues with their own working style and their own `CLAUDE.md`. The import is an absolute path
specific to this machine, so committing it would be meaningless for anyone else.

The import goes into `CLAUDE.local.md` instead: Claude Code loads it alongside `CLAUDE.md` in the same
directory, and it is never committed. The repo's committed `CLAUDE.md` stays the team's, untouched.
`CLAUDE.local.md` must be ignored without touching the team's `.gitignore` — `.git/info/exclude` does
that per clone (`Chapter_Repos` excludes `**/CLAUDE.local.md` there, which reaches every subdirectory).

The first session that meets an import from outside the working directory asks once to approve it;
declining disables the import for that project.

A repo whose committed `.claude/settings.json` enables a plugin this harness replaces — `Task Force
Evaluation` enables the team plugin `team-ai-layer` — also needs that plugin set to `false` in its
`.claude/settings.local.json`. A project setting outranks the user one, so disabling it in
`~/.claude/settings.json` alone leaves it loaded.

## Gotcha 3: `~/.claude/skills/` is not this repo's to own

Claude Code writes into `~/.claude/skills/` itself — skills synced from claude.ai land in its `synced/`
folder — and third-party installers (e.g. Graphify's `graphify install`) write to
`~/.claude/skills/<name>/`. With the whole folder symlinked to this repo, all of that would land in this
repo's tracked `.claude/skills/` and show up in `git status` here. Symlinking each skill individually keeps
`~/.claude/skills/` a real directory that other writers can use, and keeps this repo holding only its own
skills. A new skill added here needs its own link:

```sh
ln -s ~/Projects/agents/.claude/skills/<name> ~/.claude/skills/<name>
```
