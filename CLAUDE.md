# Claude Code — Working Instructions

@instructions.md

The file above is the shared source of truth for all conventions. The sections below add Claude
Code-specific mechanics that extend or override it.

---

## Phase tracking

Use Claude Code's **TodoWrite tool** to mirror wave phases. Create one todo item per phase (Plan, Implement, Documentation update, Verification, Commit message proposal) and mark each one complete as it finishes — do not batch-update at the end.

## Shell commands and git

Propose the exact command in chat before running it. Only run after explicit confirmation.

For wave commit messages, draft the full message in chat first. Pass it via `-m "…"` directly — no HEREDOC in the `git commit` invocation. Only run `git commit` after I say OK.

## Chat vs. file updates

File changes are gated by plan mode (see `instructions.md`, Working Mode), not by a separate verbal
go-ahead: stay in plan mode while discussing, and only touch files after exiting it — either through plan
mode's own approval prompt, or for changes small enough that plan mode was skipped entirely.

This still applies per topic: in a single conversation some topics may already be past approval while
others are still being discussed. Only touch files for topics that have actually cleared plan mode.

## Chat answer style

After updating files: summarize what changed at the end of your turn using a bullet list.
During discussion: answer in chat. For each topic or question, name it explicitly and give enough context that the answer stands on its own.
Always: visually separate distinct topics with headings, blank linesg, or bullet points — don't run multiple topics together in one paragraph.

At the very end of every turn, add to your output an empty line followed by two horizontal rules.