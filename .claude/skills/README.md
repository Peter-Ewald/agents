# skills/

Skills shared across repos. Each folder here is symlinked individually into `~/.claude/skills/`, which
stays a real directory (see [`../../docs/03-cross-repo-distribution.md`](../../docs/03-cross-repo-distribution.md)).
See [`../../docs/02-skills-and-subagents.md`](../../docs/02-skills-and-subagents.md) for what each does.

| Skill | Purpose |
|---|---|
| `wave` | Runs a wave through its phases; supporting files `tiers.md`, `board.md`, `report.md` |
| `coordinate` | Turns a session into the coordinator that starts and tracks batch waves |
| `implementer-contract` | The brief, working rules and report of the implementer subagents; preloaded, not invoked directly |
| `doc-conventions` | Documentation conventions, loaded on every markdown edit |
| `design-conventions` | Design and architecture principles |
| `ruff-cleanup` | Fixes the ruff violations the autofix hook leaves |
| `sdk-release` | Releases `semantic_tracing` or `semantic_evaluation` |
| `langfuse-upgrade` | Investigates a new langfuse release against both SDKs |

The nine `semeval-*` skills are not in this folder: their `~/.claude/skills/semeval-<name>` links point at
`~/Projects/Semantic_Evaluation/agent_skills/<name>`.
