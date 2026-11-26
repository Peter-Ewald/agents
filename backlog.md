
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
| 2 | Every skill has a stated home and reaches the sessions that need it |

Step 2 depends on nothing and may land before step 1.

### Pilot: parallel waves on a real release

The harness can run waves in parallel ([`docs/05-parallel-waves.md`](docs/05-parallel-waves.md)), but no
batch wave has yet run across two repos with a hold between them. The pilot runs a real pair as batch
waves and adjusts the harness to what it shows: an SDK release in `Semantic_Evaluation` and the pin bump
in a pod repo that waits on it with a `merge` hold.

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

### Every skill has a stated home and reaches the sessions that need it

A skill that the admin of a repo uses is offered only inside that repo. `onboard-newcomer` lives in
`Semantic_Evaluation/.claude/skills/`, and Claude Code offers a repo's own skills only once a session
works on files in that repo. On the newcomer walk of `Semantic_Evaluation` (2026-11), a fresh session
opened on `~/Projects` was told "onboard testuser for the workshop" and answered without the skill. It
rebuilt the procedure from the script and the workshop pages and left out what only the runbook says:
organisation role None, the invitation from the project's own settings, the output path in a OneDrive
folder, and the message to send. The location is the probable cause; confirm it first, in a fresh session
on `~/Projects` and in one opened inside another repo.

Nothing in this repo says where a new skill belongs. [`docs/03-cross-repo-distribution.md`](docs/03-cross-repo-distribution.md)
describes how the harness's own skills and the nine `semeval-*` skills reach a session, but not how to
choose between the homes, and not how each kind stays current.

What the wave delivers:

- **The admin's skills reach every session.** `~/.claude/skills/onboard-newcomer` links to the skill's
  folder in `Semantic_Evaluation/.claude/skills/`, which stays the source, as for the `semeval-*` links.
  Check when planning how Claude Code treats a skill that is then offered twice inside
  `Semantic_Evaluation` (personal and project location under one name). Checked by a fresh session on
  `~/Projects`, told "onboard <name>", that invokes the skill.
- **One table of homes**, in `docs/03-cross-repo-distribution.md`, that a person adding a skill chooses
  from:

  | Kind of skill | Used by | Source of truth | Reaches a session through |
  |---|---|---|---|
  | Harness skill (`wave`, `coordinate`, `sdk-release`) | The agent in any repo on this machine | This repo's `.claude/skills/` | Its own link in `~/.claude/skills/` |
  | Skill for a consumer project's coding agent (`semeval-*`) | Any project that installs the SDK | `Semantic_Evaluation/agent_skills/`, shipped in the `semantic-evaluation` wheel | In a project: `eval-skills update` writes it to `.claude/skills/`. On this machine: a link to the checkout |
  | A repo's admin skill (`onboard-newcomer`) | The admin, from any session | That repo's `.claude/skills/` | A link in `~/.claude/skills/` |
  | Personal skill | One person | A real folder in `~/.claude/skills/` | Nothing to set up |

- **How each kind stays current**, as a section next to that table. It states the mechanism and links to
  the document that owns it, without repeating it:

  | Kind | Kept current by |
  |---|---|
  | Harness and admin skills | The link reads the checkout, so `sync_main.py` is the update; a session reloads a skill when its mechanics matter (`CLAUDE.md`, "Skill freshness") |
  | `semeval-*` in a consumer project | `eval-skills update` and its `--check`, and the `semeval-upgrade` skill, which a coding agent runs for an SDK release or for a service API version that is being retired; a release reaches the project as a `notice` on the board. Owned by the SDK's `docs/10-agent-skills.md` |
  | `semeval-*` on this machine | The links read the `main` checkout, which can be ahead of the newest release; say what that means for a session that works in a project pinned to an older SDK |

- **A check of the chain for a version bump**, from both ends: an SDK release and a retired service API
  version each lead a consumer project's coding agent to the upgrade without a person relaying the steps
  (changelog `To upgrade`, the `Deprecation` and `Sunset` headers, the board notice, `semeval-upgrade`).
  A link in the chain that the SDK or its documentation does not state becomes a `request` to
  `Semantic_Evaluation`, not a fix in this repo.

Wanted before the next onboarding from a fresh session, at the latest the closing walk of
`Semantic_Evaluation`'s workshop rebuild, which onboards the test user again.

Done when a fresh session on `~/Projects` invokes `onboard-newcomer` on "onboard <name>", and
`docs/03-cross-repo-distribution.md` answers "where does this skill go" and "how does it stay current" for
each kind.
