
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
| 1 | Local `main` follows `origin/main` |
| 2 | Pilot: parallel waves on a real release |

### Local `main` follows `origin/main`

Every landing moves `origin/main` and leaves the local `main` behind. A wave lands from its worktree
(`git push origin HEAD:main`, or a pull request completed on the server). Backlog curation in a repo with
a branch policy lands through a pull request. Teammates merge on the server. Nothing in the harness
fast-forwards the local `main` afterwards. Wave worktrees are unaffected: `new-wave-worktree.sh` fetches
and branches from `origin/main`, and Integrate rebases on it. Everything that reads the main checkout is
affected:

- The Plan phase reads `backlog.md`, `CLAUDE.md`, `.claude/rules/` and `docs/history/index.md` there. A
  plan can build on an entry that a merged wave already removed, or miss one added since. A chat about
  the backlog reads the same stale file.
- The live harness is the main checkout. `~/.claude/agents` and the skill links point into `agents/`,
  and the `semeval-*` skills into `Semantic_Evaluation/agent_skills/`. The global hooks run from
  `agents/.claude/hooks/`, and `instructions.md` and `CLAUDE.md` are imported from there. A merged
  harness wave is therefore live only after someone pulls.

Shape:

- A script `.claude/scripts/sync-main.sh <repo path>`, run as is like the other scripts so the allow rule
  covers it in auto mode. It fetches `origin`, then fast-forwards `main` to `origin/main` when the main
  checkout is on `main`. It never stashes, resets, rebases or switches branch. It leaves the checkout as
  it is and prints one line saying why when any of these holds:
  - the checkout is on another branch
  - `main` has commits that `origin/main` lacks
  - an uncommitted file is in the way of the fast-forward

  It fetches with `GIT_TERMINAL_PROMPT=0` and a timeout, so an expired Azure DevOps login fails fast
  rather than hanging a hook, and exits 0 in every case.
- It is called wherever `main` is known to have moved or is about to be read:

  | When | Where |
  |---|---|
  | After a wave lands (batch and interactive) | `wave` skill, Integrate step 7 |
  | After backlog curation lands through a pull request | `CLAUDE.md`, "Shell commands and git" |
  | Before the Plan phase reads a repo | `wave` skill, Plan, for each affected repo |
  | At session start, for each active repo, in parallel and bounded in time | A SessionStart hook; this also covers merges made outside the harness |

- Context repos are only fetched: their checkout may sit on another branch on purpose (`instructions.md`,
  "Repositories and their roles").
- The statusline shows a repo whose `main` is behind the last fetched `origin/main` (`main ↓3`), so a
  refused fast-forward stays visible.
- Tests in `test_coordination.py`, whose git fixture already has an origin: the fast-forward, each refusal
  case, and an unreachable remote.

A fast-forward of the main checkout never disturbs a wave. Each worktree has its own branch and files, and
the coordination guard governs only pushes to `main`. After a fast-forward of `agents`, a running session
uses the changed hooks on its next tool call and a changed skill the next time it loads it.

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

## Planned

### Board entries survive their content

Two parsing problems in `.claude/scripts/board.py` hide or cut what the board shows, and matter most for
the inbox, whose content lives in front matter fields (`need=` of a request, `text=` of a notice):

- `_parse_value` treats ` #` inside a value as the start of a comment, so `need=fix #42 soon` is stored
  as `need: fix`. The rest is lost at filing time, without a warning. A value written as `[a, b]` is
  parsed as a list.
- One unreadable entry (no closing `---`, or not UTF-8) makes `entries()` raise. Then the statusline's
  inbox and blocked parts go blank for every repo, the `coordination-inject.py` hook injects nothing
  outside a repo, and `board.py inbox` and `list` stop at the broken repo (a non-UTF-8 file gives a
  traceback, since `main()` catches only `BoardError` and `OSError`). `_watch_scan` already skips a bad
  entry and reports it; the other readers should do the same, so one broken file never hides the rest.

Shape: quote values on filing (or stop stripping comments from values the script itself wrote), and give
`entries()` callers a way to skip and name unreadable entries. Tests in `test_coordination.py`.
