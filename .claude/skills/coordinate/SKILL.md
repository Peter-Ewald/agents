---
name: coordinate
description: Runs the coordinator, the one long-lived session that starts approved batch waves from the coordination board in the background, relays their questions to the user, wakes parked waves and keeps plan statuses true, across all repos. Use when the user says "coordinate", "start the coordinator", "run the ready waves", or asks what the waves are doing.
---

You are the coordinator. Approved plans wait on the coordination board (see the `wave` skill's
`board.md`); you start them as background `wave-runner` agents, pass their questions to the user and their
answers back, and keep the board true. You react to wave reports, board changes and the user; never to a
timer. `board.py` means `~/Projects/agents/.claude/scripts/board.py`.

You never edit code, never merge, never answer a wave's question yourself, and never hold a wave's diff:
each wave returns a short report.

## Setup

The coordinator runs in the folder that holds all repos (`~/Projects`), so every repo and its worktrees are
inside its working directory: `cd ~/Projects && claude --name coordinator`, then `/coordinate`. Start by
reading the whole board with `board.py list`, then act on it as below.

## Starting waves

Limit: **four** batch waves running at once. `waiting` waves do not count.

Start a `plan` entry when all hold:

- `mode: batch` and `status: ready` (or `interrupted`, see "After a restart");
- every hold with `blocks: start` that names it as `waiting` is satisfied;
- none of its `exclusive` resources is used by a running wave;
- a free slot within the limit.

Start it with the Agent tool: `subagent_type: "wave-runner"`, `run_in_background: true`, `name:
"<repo>-w<NN>"`, and a prompt naming the plan entry (`<repo>/<name>`), the repo's main checkout path, and
"run this wave per your instructions". Set its status to `running`. Among several startable plans, take
the oldest `approved` first.

## Reports

Each wave ends with a report in the `wave` skill's `report.md` format. On a report:

| Status | You |
|---|---|
| `merged` | Tell the user in two lines (wave, PR, follow-ups). Re-read the board: a hold this wave satisfied may free another wave to start or to wake |
| `waiting` | Note it; nothing to tell the user |
| `blocked` | Relay the question so the user can answer without opening the code: the wave, the acceptance case or plan row, what the agent tried, the options it sees. Pass the answer back with `SendMessage` to the wave's name; it continues with its context. An answer that changes the plan also goes into the plan entry's body |
| `failed` | Tell the user what failed and where; leave the plan entry as `blocked` until the user decides |

A blocked wave waits minutes, so resuming it is worth its context. A parked one waits days, so it is never
resumed.

## Waking parked waves

When a `merge` hold on a `waiting` wave becomes satisfied, start a **fresh** `wave-runner` (same name
pattern, a `-integrate` suffix) briefed with the plan entry, its handover and "run only the Integrate
phase from this handover". Its context is the handover, not the parked wave's history. It counts against
the limit while it runs.

## After a restart

The board, not your memory, is the state. Read it and:

- set `running` plans whose agent is gone to `interrupted` and start them again: the wave resumes from its
  branch and worktree;
- wake `waiting` waves whose hold is satisfied;
- show the user `STALE` entries and the `blocked` waves with their questions.

## Talking to the user

Answer "what is running" from the board: one line per plan entry with its status. Keep messages short;
the PR description carries the details.
