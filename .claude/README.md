# .claude/

Shared Claude Code assets for this user's repos — subagents, skills, and hook scripts that other
repositories reference instead of duplicating. See [`../docs/00-agents-overview.md`](../docs/00-agents-overview.md)
for how these pieces fit together, and [`../backlog.md`](../backlog.md) for what's still being added.

| Path | Purpose | Distributed via |
|---|---|---|
| [`agents/`](agents/README.md) | Subagent definitions | symlinked from `~/.claude/agents` |
| [`skills/`](skills/README.md) | Skills | each skill symlinked into `~/.claude/skills/` |
| [`hooks/`](hooks/README.md) | Hook scripts | referenced by absolute path from `~/.claude/settings.json` |
| [`statusline.py`](statusline.py) | Shows the current wave phase | referenced under `statusLine` in `~/.claude/settings.json` |
