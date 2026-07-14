# GitHub Copilot — Working Instructions

**Before doing anything else this session, read [`instructions.md`](instructions.md).** That file is the shared source of truth for all conventions. The sections below add Copilot-specific mechanics that extend or override it.

---

## Phase tracking

Copilot has no persistent tool for tracking state between responses. At the start of each response during a wave, state the current phase explicitly — e.g. `**Phase: Implement**` — so the conversation stays oriented.

## Shell commands and git

Copilot cannot execute shell commands. Write out the exact command text to copy-paste, formatted as a code block. For commit messages, write the full formatted message as a code block to copy-paste; apply the commit message format from `instructions.md`.

## Plan history archiving

Copilot has no persistent session-plan file to archive (per *Phase tracking* above, phase state lives only in response text) — `docs/history/` (see `instructions.md`, Plan history) stays unpopulated by Copilot sessions for now. Checking `docs/history/index.md` before planning still applies; there's just nothing to add to it from this side yet.
