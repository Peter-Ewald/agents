
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
