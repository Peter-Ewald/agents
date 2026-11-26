# .claude/

Shared Claude Code assets for this user's repos: subagents, skills, hook scripts and coordination scripts
that other repositories reference instead of duplicating. See
[`../docs/00-agents-overview.md`](../docs/00-agents-overview.md) for how these pieces fit together, and
[`../backlog.md`](../backlog.md) for what's still being added.

| Path | Purpose | Distributed via |
|---|---|---|
| [`agents/`](agents/README.md) | Subagent definitions | symlinked from `~/.claude/agents` |
| [`skills/`](skills/README.md) | Skills | each skill symlinked into `~/.claude/skills/` |
| [`hooks/`](hooks/README.md) | Hook scripts | referenced by absolute path from `~/.claude/settings.json` |
| [`scripts/`](scripts/) | `board.py` (the coordination board), `new-wave-worktree.sh` (creates a wave's worktree), `sync_main.py` (fast-forwards a main checkout to `origin/main`), `render_deck.py` (renders a deck's slides through PowerPoint) and their tests | called by absolute path from the `wave` and `coordinate` skills, the `deck-visual-check` agent and the hooks |
| [`rules/integration.md`](rules/integration.md) | This repo's own `Integration: push` rule | not distributed: it applies to this repo only |
| [`statusline.py`](statusline.py) | Shows the current wave phase | referenced under `statusLine` in `~/.claude/settings.json` |
