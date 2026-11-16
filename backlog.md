
# Backlog

Forward-looking backlog for turning `instructions.md` / `CLAUDE.md` from shared prose into a real Claude
Code harness — native plan mode, skills, subagents, and hooks doing the enforcement that prose currently
only asks for.

## Context for planning agents

| Look here for | Doc |
|---|---|
| How the pieces fit together | [`docs/00-agents-overview.md`](docs/00-agents-overview.md) |
| What each hook does | [`docs/01-hooks.md`](docs/01-hooks.md) |
| What each skill/subagent does | [`docs/02-skills-and-subagents.md`](docs/02-skills-and-subagents.md) |
| How cross-repo distribution works, and its gotchas | [`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md) |
| How parallel waves, the board and the coordinator fit together | [`docs/05-parallel-waves.md`](docs/05-parallel-waves.md) |

## Next Up

| Step | Wave |
|---|---|
| 1 | Pilot: parallel waves on a real release |

### Pilot: parallel waves on a real release

The harness can run waves in parallel ([`docs/05-parallel-waves.md`](docs/05-parallel-waves.md)), but no
batch wave has run yet. The pilot runs a real pair as batch waves and adjusts the harness to what it shows:
an SDK release in `Semantic_Evaluation` and the pin bump in a pod repo that waits on it with a `merge`
hold.

What to watch, and fix in the harness where it fails:

- Whether a background `wave-runner` gets every permission it needs in auto mode with the allow rules in
  `~/.claude/settings.json`, or stops on a denied call.
- Whether the guard catches every way the agent lands on `main` (`az repos pr` variants, `gh pr merge`).
- Whether the parked wave's handover is enough for a fresh `wave-runner` to integrate without asking.
- Token use of the coordinator, a `wave-runner` and each tier against the `autoCompactWindow` values set
  in the agent files.
- Whether two parallel waves is the right limit in the `coordinate` skill.

Starts once `Semantic_Evaluation` Waves 64 (`push` merges what changed in Langfuse since the pull) and 63
(a run selects items by id and leaves out other waves' `pending:` tags) have landed: the harness docs and
skills already assume both. `Semantic_Evaluation` PRs complete with rebase and fast-forward only once its
team allows that strategy; until then a wave there completes with the allowed one and says so in its
report.

Done when both waves have merged as batch waves without manual help, or each place that needed help is a
harness fix or a backlog entry.
