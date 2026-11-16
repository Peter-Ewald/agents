# hooks/

Scripts referenced by absolute path from `~/.claude/settings.json` hook configuration: reinjecting
CLAUDE.md/instructions.md on compaction or a direct edit, ruff autofixing, changed-lines linting,
web-search rate limiting, new-dependency flagging, changelog-before-commit ordering, Excalidraw
binding validation, and the three coordination-board hooks (`coordination-inject.py`,
`coordination-watch.py`, `coordination-guard.py`, backed by [`../scripts/board.py`](../scripts/board.py)). See
[`../../docs/01-hooks.md`](../../docs/01-hooks.md) for what each one does and how to test it standalone.
