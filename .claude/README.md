# .claude/

Shared Claude Code assets for this user's repos — subagents, skills, and hook scripts that other
repositories reference instead of duplicating. See [`../implementation_plan.md`](../implementation_plan.md)
for the rollout plan.

| Folder | Purpose | Distributed via |
|---|---|---|
| [`agents/`](agents/README.md) | Subagent definitions | symlinked from `~/.claude/agents` |
| [`skills/`](skills/README.md) | Skills | symlinked from each repo's `.claude/skills` (or `~/.claude/skills`, pending verification) |
| [`hooks/`](hooks/README.md) | Hook scripts | referenced by absolute path from `~/.claude/settings.json` |

Currently empty except for structural placeholders — populated as the waves in
[`../implementation_plan.md`](../implementation_plan.md) land.
