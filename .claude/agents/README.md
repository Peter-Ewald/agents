# agents/

Subagent definitions shared across repos via the `~/.claude/agents` symlink to this folder. See
[`../../docs/02-skills-and-subagents.md`](../../docs/02-skills-and-subagents.md) for what each does.

| Agent | Role |
|---|---|
| `implementer-light`, `implementer-medium`, `implementer-strong` | One sub-task of a wave at the tier its plan row names; all three preload `implementer-contract` |
| `test-author` | Turns a plan's acceptance cases into failing tests and eval items in the Specify phase |
| `wave-runner` | Runs one batch wave in the background for the coordinator |
| `doc-sweep` | A documentation sweep: a sweep wave's work, or an ad hoc request |
