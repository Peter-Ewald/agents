---
date: 2026-11-23
title: Wave eval runs use eval-run item selection
outcome: completed
---

# Wave 05 (agents): Wave eval runs use eval-run item selection

## Summary

| | |
|---|---|
| Goal | A wave's eval runs follow `semantic_evaluation` 4.3.0's item selection. Its Implement run picks its own items with `eval-run --items … --repeats 3`. Its regression run includes its own pending items with `--include-pending` and leaves other waves' pending items out by default. Serves backlog Next Up step 1 and unblocks step 3, the pilot. |
| Kind | Documentation (harness instructions); reported by file and rule |
| Changes | agents: the `wave` skill (Implement § 3, Verification § 5), the `test-author` brief (tag line), `docs/05-parallel-waves.md` (eval table), `docs/02-skills-and-subagents.md` ("In a wave" paragraph) |
| Behaviour | None in code. No acceptance cases: each changed step is read against the 4.3.0 changelog and the SDK's "Selecting items on the command line" section |
| Decisions | (1) The pending tag stays `pending:<repo>/<wave key>`, not semeval-maintain's `pending:<repo>/<branch>`. (2) The wave skill gives the two flag lines itself and points to `semeval-maintain` step 5 for the rest. (3) A one-line prerequisite: a wave that runs evals needs `semantic-evaluation` 4.3.0 or later |
| Risks and holds | No holds. Wave 04 (inbox) also edits `wave/SKILL.md`, `docs/05-parallel-waves.md` and `backlog.md`, but in other sections; the integration lock serializes the two waves, and the rebase is mechanical |

## Context

`semantic_evaluation` 4.3.0 (Semantic_Evaluation wave 63) added item selection: the run-file fields
`items`, `include_tags`, `exclude_tags` and `include_pending`, the matching `eval-run` flags (comma lists,
each replacing the run file's value), and a new default that leaves out every item tagged `pending:`.
The `wave` skill still describes the selection as it was planned before that release:

- **§ 3 Implement**: "a run file that selects them by id (`items:`), with three repeats". This means
  writing a wave-specific run file, which `--items` makes unnecessary. `semeval-maintain` step 5 also says
  never to commit the selection in a run file.
- **§ 5 Verification**: "leaving out every other wave's `pending:` tag (`exclude_tags:` in the run
  file); this wave's own items run with it". Under the new default the opposite happens. Other waves'
  items are already left out, and this wave's own items, still tagged pending until the merge, are
  silently left out too. The regression run would then pass without ever running the new behaviour.

## Decisions

1. **Tag format stays `pending:<repo>/<wave key>`** (for example `pending:Checkmate/wave-12`).
   `semeval-maintain` uses `<branch>` for the single-session case. A wave uses its board key, which the
   board, the guard hook and `test-author` already use, and which matches the SDK's own example
   (`pending:support-agent/wave-63`). The alternative, the full branch `wave-12-batch-upload`, would also
   work but would change three files that agree today.
2. **The wave skill carries the two flag lines.** A `wave-runner` acts on the wave skill alone. The tag
   in `--include-pending` is wave-specific, so the skill shows that one line and points to
   `semeval-maintain` step 5 for reading the results. The selection rules stay with the SDK (ownership:
   the SDK docs own the mechanics).
3. **Prerequisite line in § 3**: the flags need `semantic-evaluation` 4.3.0 or later. A repo pinned
   lower upgrades as a sub-task of its own plan (`semeval-upgrade`); without that the wave stops, because
   it needs an unnamed dependency. Alternative: put the check in § 1 Plan. That is where it belongs in
   principle, but § 1 is the section wave 04 is rewriting, so § 3 avoids a conflict.

## Changes

| ID | File | Change | Runs as |
|---|---|---|---|
| S1 | `.claude/skills/wave/SKILL.md` § 3 | Replace the run-file sentence with: run the wave's own items once the code is in place, `eval-run --run-file <the project's regression run file> --items <ids> --repeats 3`; an item named by id runs although it is pending. Add the 4.3.0 prerequisite sentence | inline |
| S2 | `.claude/skills/wave/SKILL.md` § 5 | Replace the `exclude_tags:` sentence with: the full regression per `semeval-maintain` step 5 with `--include-pending pending:<repo>/<wave key>`; other waves' pending items are left out by default; the selection is never written into a committed run file | inline |
| S3 | `.claude/agents/test-author.md` step 4 | Tag line made explicit: `pending:<repo>/<wave key>` *in place of* semeval-maintain's `pending:<repo>/<branch>` | inline |
| S4 | `docs/05-parallel-waves.md` § Eval items and the dev dataset | Implement and Verification rows rewritten to the flags. Specify row: `<wave>` → `<wave key>` for consistency | inline |
| S5 | `docs/02-skills-and-subagents.md` "In a wave" | Rewrite: `semeval-maintain` already tags, leaves out and later untags pending items. A wave adds the wave-key tag, the dataset lock, no runs in Specify, three repeats with `--items` in Implement, and `--include-pending` with its own tag in Verification | inline |

All of these rows are short edits to prose, so a brief would cost more than doing the edit. The wave agent
does them itself.

## Documentation upkeep

- `backlog.md`: remove the "Wave eval runs use `eval-run` item selection" section and its Next Up row,
  renumber, and rewrite the pilot's "Starts once … (step 1)" sentence as a plain statement.
- `docs/history/`: archive this plan and add an index line.
- No CHANGELOG (no released package).

## Verification

- `grep -rn "exclude_tags\|items:" .claude docs instructions.md CLAUDE.md` in the worktree finds no
  instruction that tells a wave to write selection into a run file.
- Read each changed step against `sdk/semantic_evaluation/CHANGELOG.md` § 4.3.0 and
  `sdk/semantic_evaluation/docs/04-offline-evaluation.md` § Selecting items on the command line: the
  flag names, the comma-list form, "named by id runs although pending" and "pending left out by default"
  all match.
- `doc-conventions` check on the four edited markdown files.

## Exit criteria

Every file in the change table says the same thing about selection, and none contradicts
`semeval-maintain` step 5 except for the deliberate tag format (decision 1). The backlog and history
updates are done. The wave is pushed to `main`.

## Board fields

| Field | Value |
|---|---|
| repo / wave | `agents` / `wave-05-eval-run-selection` |
| title | Wave eval runs use eval-run item selection |
| mode | batch |
| integration | push (`.claude/rules/integration.md`) |
| holds | none |
| exclusive | none |
| new_dependencies | none |
| expires | 2026-12-07 |
