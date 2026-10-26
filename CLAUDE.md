# Claude Code — Working Instructions

@instructions.md

The file above is the shared source of truth for all conventions. The sections below add Claude
Code-specific mechanics that extend or override it.

---

## Adding a skill, subagent, or hook

This repo's content doesn't reach other repos by itself — see `docs/03-cross-repo-distribution.md` for
the mechanism and its gotchas. A new skill needs its own symlink into `~/.claude/skills/`; subagents and
hooks are already covered by the existing `~/.claude/agents` symlink and global `~/.claude/settings.json`
registration, so only skills need this per-addition step.

## Phase tracking

The `wave` skill writes the current phase to a file the statusline shows; see that skill for the
mechanism. There is no separate todo list to keep in step.

## Token economy

Every tool call re-sends the whole conversation, so cost grows with context size times call count.

- **Locate before reading.** Grep or Glob for the symbol first, then read the relevant line range of a
  large file rather than the whole file. The same applies to commands and API calls: prefer a filtered or
  quiet form (`pytest -q`, `git log --oneline`, a `jq` filter on JSON) over raw verbose output; for
  anything fetched over HTTP (a Langfuse trace, an API response), write it to a scratch file first and
  filter before reading, rather than letting the raw payload enter context. Delegate a payload you must
  read in full (a large diff, a trace with no obvious filter) to a subagent so the raw data lives in its
  context, not this one's.
- **Delegate execution, keep judgment.** Scoped implementation goes to the `implementer` subagent (see the
  `wave` skill); open-ended searches go to `Explore` or a `general-purpose` agent, which run on Sonnet by
  default (`CLAUDE_CODE_SUBAGENT_MODEL`). Forks inherit this conversation and its model, so use one only
  when the full context is the point.
- **One session per piece of work.** After a wave commits, or when switching topic, suggest `/clear`:
  `backlog.md`, `docs/history/`, and the code carry everything across sessions.

## Skill freshness

`doc-conventions` is `paths`-triggered — Claude Code reloads its full content automatically on every
markdown read/edit, so it's structurally guaranteed fresh. Every other skill (`wave`, `ruff-cleanup`,
`sdk-release`, `design-conventions`, `langfuse-upgrade`, and the nine `semeval-*` skills) has no file-glob trigger — it's matched by
natural language or invoked explicitly — and its content is NOT reinjected across context compaction the way
`instructions.md`/`CLAUDE.md` are via `reinject-instructions.py`. A memory of having read one of these
early in a long conversation is not the same as it actually being loaded now.

Don't work from that memory. Invoke the skill via the Skill tool at the moment its specific mechanics
actually matter — starting a wave's Implement phase, running a cleanup, cutting a release, finalizing a
design decision — so the exact procedure loads fresh rather than being reconstructed from a fading
impression of an earlier read.

## Session plan location

Claude Code's native plan mode already writes the session plan to a durable, per-session file at
`~/.claude/plans/<slug>.md` — not the scratchpad, and not discarded when the session ends. Write (and
revise) the session plan there, the same file plan mode already manages; no separate scratchpad copy is
needed.

## Plan history archiving

When a wave's Documentation update phase reaches the `docs/history/` step (see `instructions.md`, Plan
history), copy the session plan from `~/.claude/plans/<slug>.md` into `docs/history/YYYY-MM-DD-<slug>.md`
in the target repo, prefixed with the date/title/outcome header, and append its line to
`docs/history/index.md`. Do this whether the wave completed or was dropped partway through — a dropped
plan still archives at the point the user decides not to proceed, with outcome `dropped` and the stated
reason, rather than waiting for a wave that will never reach its Documentation update phase.

## Shell commands and git

Draft the full wave commit message in chat first. Pass it via `-m "…"` directly — no HEREDOC in the `git commit` invocation, and no `Co-Authored-By` trailer — and only run `git commit` after I say OK. (Both diverge from Claude Code's own default git behavior, which uses a HEREDOC and adds a trailer — everything else about routine shell commands already follows the default permission system, nothing extra to state here.)

## Chat vs. file updates

File changes are gated by plan mode's approval (see `instructions.md`, Working Mode) once a concrete plan
is being finalized — not by a separate verbal go-ahead. Discussion, research, and backlog curation happen
in normal mode and don't need this gate at all. Once a topic reaches the point of finalizing a concrete
plan, only touch files after exiting plan mode — either through plan mode's own approval prompt, or for
changes small enough that plan mode was skipped entirely.

This still applies per topic: in a single conversation some topics may already be past approval while
others are still being discussed. Only touch files for topics that have actually cleared plan mode.

## Chat answer style

After updating files: summarize what changed at the end of your turn using a bullet list.
During discussion: answer in chat. For each topic or question, name it explicitly and give enough context that the answer stands on its own.
Always: visually separate distinct topics with headings, blank linesg, or bullet points — don't run multiple topics together in one paragraph.

At the very end of every turn, add to your output an empty line followed by two horizontal rules.