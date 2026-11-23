
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
| 1 | An inbox for board requests and notices |
| 2 | Pilot: parallel waves on a real release |

### An inbox for board requests and notices

The board carries two kinds of entry that nobody is sure to act on. A `request` is another repo's wave
asking this repo to build something, and it should become a `backlog.md` entry. A `notice` is a plain
fact with steps for the repos it concerns, such as an SDK release with its pin bump. The coordinator acts
only on plans and holds, and should stay that way. Today the two kinds reach only the agent's context at
session start (`coordination-inject.py`), where they show without their text. No rule tells an agent to
raise them with the user, and the statusline shows only blocked plans. An expired notice is deleted
without a word, and a notice that was already acted on stays until it expires: for example, Checkmate's
4.4.1 notice asks for a pin of `>=4.4.1,<5` while Checkmate already pins `>=4.5.0`. Work other repos
asked for, and upgrade steps from SDK releases, get forgotten.

What the inbox needs, decided together:

- **The planning agent raises them.** Add a rule to `instructions.md`, and a matching step to the `wave`
  skill's Plan phase. When a session's work concerns a repo, the agent first lists that repo's open
  requests and notices. It offers to turn each request into a backlog entry and to act on or close each
  notice. This also applies in a session opened on `~/Projects` that names a repo.
- **The statusline counts them per repo**, for example `inbox: Checkmate 3, agents 1`, next to the
  blocked-plans display, and stays silent when nothing is open.
- **Notices close once handled**, and leave both the count and the injected context. A notice that
  expires unhandled is reported, not dropped silently.

Out of scope: the coordinator does not take on requests or notices.

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
- Whether four parallel waves is the right limit in the `coordinate` skill: usage limits, and how often a
  later wave has to rebase over the files every wave touches (`CHANGELOG.md`, `backlog.md`, the package
  version).

The wave skill's eval runs already use `eval-run` item selection, so the pod wave's Implement and
Verification runs follow the SDK's current defaults.

Done when both waves have merged as batch waves without manual help, or each place that needed help is a
harness fix or a backlog entry.
