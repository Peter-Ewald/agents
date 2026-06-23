# Claude Code — Working Instructions

**Before doing anything else this session, read [`instructions.md`](instructions.md).** That file is the shared source of truth for all conventions. The sections below add Claude Code-specific mechanics that extend or override it.

---

## Phase tracking

Use Claude Code's **TodoWrite tool** to mirror wave phases. Create one todo item per phase (Plan, Implement, Documentation update, Verification, Commit message proposal) and mark each one complete as it finishes — do not batch-update at the end.

## Shell commands and git

Propose the exact command in chat before running it. Only run after explicit confirmation.

For wave commit messages, draft the full message in chat first. Pass it via `-m "…"` directly — no HEREDOC in the `git commit` invocation. Only run `git commit` after I say OK.

## Chat vs. file updates

Do not update any file (code, .md, implementation plan) until I explicitly say so — for example "update the implementation plan" or "write that down."

This applies per topic: in a single conversation I may have already said to update files for some topics while we're still discussing others. Apply file updates only to topics where I gave the explicit instruction.

## Chat answer style

After updating files: summarize what changed at the end of your turn using a bullet list.
During discussion: answer in chat. For each topic or question, name it explicitly and give enough context that the answer stands on its own.
Always: visually separate distinct topics with headings, blank linesg, or bullet points — don't run multiple topics together in one paragraph.