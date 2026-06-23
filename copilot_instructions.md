# GitHub Copilot — Working Instructions

**Before doing anything else this session, read [`instructions.md`](instructions.md).** That file is the shared source of truth for all conventions. The sections below add Copilot-specific mechanics that extend or override it.

---

## Phase tracking

Copilot has no persistent tool for tracking state between responses. At the start of each response during a wave, state the current phase explicitly — e.g. `**Phase: Implement**` — so the conversation stays oriented.

## Shell commands and git

Copilot cannot execute shell commands. Write out the exact command text to copy-paste, formatted as a code block. For commit messages, write the full formatted message as a code block to copy-paste; apply the commit message format from `instructions.md`.
