
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
| 1 | Wave eval runs use `eval-run` item selection |
| 2 | An inbox for board requests and notices |
| 3 | Pilot: parallel waves on a real release |

### Wave eval runs use `eval-run` item selection

Requested by `Semantic_Evaluation` Wave 63, which shipped item selection in `semantic_evaluation` 4.3.0.
Since that release a run leaves out every item tagged `pending:` by default, and `eval-run` takes the
selection as flags (`--items`, `--include-pending`, comma lists) that replace the run file's values.
The `wave` skill still describes the selection the way it had to be done before: the Verification step
(`.claude/skills/wave/SKILL.md`, § 5) lists every *other* wave's `pending:` tag in `exclude_tags:`, which
the default now does on its own, and which needs the wave agent to find out which other waves are in
flight. Worse, under the new default that regression run silently leaves out this wave's own new items,
which are still tagged pending until the merge.

The change, in the `wave` skill's steps for an LLM agent:

| Phase | Today | After |
|---|---|---|
| Implement (§ 3) | A run file that selects the wave's items by id (`items:`), three repeats | `eval-run --items <ids> --repeats 3` on the existing run file; no wave-specific run file |
| Verification (§ 5) | Full regression with every other wave's `pending:` tag in `exclude_tags:` | Full regression with `--include-pending pending:<repo>/<wave key>`; other waves' pending items stay out by default |

Also correct the same claims in `docs/05-parallel-waves.md` (the eval table under parallel waves) and
`docs/02-skills-and-subagents.md` (the "In a wave" paragraph), and check that `test-author` and the
`semeval-maintain` references the wave skill points to agree. Documentation-shaped: no acceptance cases
beyond reading the changed steps against the 4.3.0 changelog. Lands before the pilot, whose pod wave
runs exactly these steps.

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

Starts once the wave skill's eval runs use `eval-run` item selection (step 1), so the pod wave's
Implement and Verification runs follow the SDK's current defaults.

Done when both waves have merged as batch waves without manual help, or each place that needed help is a
harness fix or a backlog entry.
