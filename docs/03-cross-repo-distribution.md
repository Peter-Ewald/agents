# Cross-repo distribution

How one copy of a skill, subagent, hook script or the shared conventions reaches every repo without being
copied into any of them, what each repo still sets up for itself, and the gotchas this ran into.

## The mechanism, per kind

| Kind | Distributed via | Why this works |
|---|---|---|
| Subagents | `~/.claude/agents` symlinked once to [`../.claude/agents/`](../.claude/agents/README.md) | Documented, user-level location. It applies to every repo automatically. |
| Skills | Each skill folder in [`../.claude/skills/`](../.claude/skills/README.md) symlinked individually into `~/.claude/skills/` | Documented: a `<skill-name>` entry in the personal skills location may be a symlink to a directory elsewhere. `~/.claude/skills/` itself stays a real directory, see Gotcha 3. |
| Hooks | Registered once in `~/.claude/settings.json` (global) | Global settings already apply everywhere, so there is nothing to symlink. |
| Shared conventions (`CLAUDE.md`, `instructions.md`) | `~/.claude/rules/agents-harness.md`, which holds the single line `@~/Projects/agents/CLAUDE.md` | Claude Code loads every file in `~/.claude/rules/` in every project and resolves its `@`-imports at session start, so each session behaves as if the shared file were pasted in. |

The shared conventions therefore reach every project on this machine, including repos that never asked
for them, and every worktree, whether Claude Code or plain `git worktree add` created it. No repo carries
a file for them.

Claude Code loads a file once even when two places import it: it deduplicates by path. A repo that still
imports `~/Projects/agents/CLAUDE.md` itself, and this repo, whose own `CLAUDE.md` is the import target,
get one copy, not two. Measured input tokens confirm this: the rule adds about 8k tokens to a session, a
second import of the same file adds only its own line.

## What each repo still sets up: `.worktreeinclude`

A worktree is a fresh checkout, so gitignored files such as `.env` are missing from it. A
`.worktreeinclude` at the repo root lists, in `.gitignore` syntax, which gitignored files Claude Code
copies from the main checkout into each worktree it creates.

| Property | Behaviour |
|---|---|
| Scope | Per repo, at the repo root. There is no user-level version, so the harness cannot set it once for all repos. |
| Which worktrees | Only the ones Claude Code creates (`--worktree`, `isolation: worktree`, desktop parallel sessions). A plain `git worktree add` copies nothing, so `.env` goes into such a worktree by hand. |
| Committed or not | Either works: an untracked `.worktreeinclude` is read from the main checkout's disk. Listing it in `.git/info/exclude` keeps it out of `git status` without touching a shared `.gitignore`. |
| Disabled by | A `WorktreeCreate` hook, which replaces worktree creation entirely. |

`Semantic_Evaluation` and `Checkmate` carry an untracked `.worktreeinclude` with `**/.env`, excluded per
clone in `.git/info/exclude`.

## Gotcha 1: a monorepo subdirectory is not a separate repo

`LLM Evaluation Architecture` and `Litellm-Model integration layer` look like separate project folders,
but they are subdirectories of one shared git repository, `Chapter_Repos`. Running
`git rev-parse --show-toplevel` from either returns `Chapter_Repos`, not the subdirectory itself.

This matters because a `.gitignore` pattern with a slash in it (like `.claude/*`) is anchored to the
directory of the `.gitignore` file that contains it. It does not cascade into subdirectories. A
"Personal Claude Code state" block in `Chapter_Repos/.gitignore` without a `**/` prefix protects only a
`.claude/` folder placed directly at the `Chapter_Repos` root, which does not exist. A `**/`-prefixed
pattern once at the shared root (`**/.claude/*`) reaches every subdirectory, present and future, instead of
a duplicated, drift-prone copy of the same block in each one. A commit touching gitignore rules for both
subdirectories is one commit in `Chapter_Repos`, not two.

## Gotcha 2: a repo shared with colleagues gets nothing committed

Repos other than this one are not all personal. `Project Green`, `Semantic Evaluation` and `Checkmate`
have colleagues with their own working style and their own `CLAUDE.md`. The user rule keeps the shared
conventions out of those repos entirely, so the committed `CLAUDE.md` stays the team's. Anything personal
that does live in such a repo, like `.worktreeinclude`, is excluded per clone in `.git/info/exclude`
rather than in the team's `.gitignore`.

A repo whose committed `.claude/settings.json` enables a plugin this harness replaces also needs that
plugin set to `false` in its `.claude/settings.local.json`. A project setting outranks the user one, so
disabling it in `~/.claude/settings.json` alone leaves it loaded.

## Gotcha 3: `~/.claude/skills/` is not this repo's to own

Claude Code writes into `~/.claude/skills/` itself: skills synced from claude.ai land in its `synced/`
folder, and third-party installers (e.g. Graphify's `graphify install`) write to
`~/.claude/skills/<name>/`. With the whole folder symlinked to this repo, all of that would land in this
repo's tracked `.claude/skills/` and show up in `git status` here. Symlinking each skill individually keeps
`~/.claude/skills/` a real directory that other writers can use, and keeps this repo holding only its own
skills. A new skill added here needs its own link:

```sh
ln -s ~/Projects/agents/.claude/skills/<name> ~/.claude/skills/<name>
```

On Windows `ln -s` needs an elevated shell, and without one Git Bash silently copies the folder, which then
drifts from the repo. Without elevation use a directory junction instead, which Claude Code follows the same:

```bat
mklink /J %USERPROFILE%\.claude\skills\<name> %USERPROFILE%\Projects\agents\.claude\skills\<name>
```
