---
date: 2026-11-23
title: An inbox for board requests and notices
outcome: completed
---

# Wave 04 (agents) — An inbox for board requests and notices

## Summary

| | |
|---|---|
| **Goal** | Every repo's open requests and notices get raised with the user and closed once handled, instead of depending on chance. Serves `backlog.md` Next Up step 2, *An inbox for board requests and notices*. |
| **Kind** | Implementation (harness). Reported by script, rule and skill. |
| **Changes** | **Board script:** a `board.py inbox` command; request and notice lines show their content; expired notices are no longer deleted. **Session-start hook:** keeps expired notices, marks them `STALE`, and ends with one line pointing to the inbox rule. **Statusline:** an `inbox: <repo> <n>, …` part. **Rules:** `instructions.md` gets a new section, *A repo's inbox*. The `wave` skill's Plan phase reads the inbox, and its Integrate phase deletes the notices the wave handled. `board.md` covers the inbox and closing, and the `coordinate` skill gets one line saying requests and notices are not its job. **Docs:** the claims about notice expiry and the statusline in `docs/01-hooks.md` and `docs/05-parallel-waves.md`, plus a glossary entry for *inbox*. |
| **Behaviour** | The statusline counts requests and notices per repo and is silent when there are none. A notice deleted with `board.py rm` leaves both the count and the injected context. An expired notice is no longer deleted: it stays, marked `STALE` and counted, until someone closes it. Injected lines show what a notice says and what a request needs. The rule tells the agent when to list a repo's inbox and what to offer for each entry. |
| **Decisions** | **D1** A handled notice is deleted (`board.py rm`), with no `done` status. **D2** An expired notice stays, marked `STALE`, until someone closes it, instead of being deleted with a one-time report. **D3** There is a dedicated `board.py inbox` command, not just `list --kind`. **D4** For a context repo (Project-Green-HR-MVP), acting on a notice means passing it to the owning team; the agent offers a draft message and then closes the notice. **D5** The injected context ends with one line pointing to the rule. Alternatives are in *Decisions* below. |
| **Risks and holds** | No holds: no other plan is on the board. **Overlap:** the *Wave eval runs use `eval-run` item selection* entry (Next Up 1, not yet planned) also edits `wave/SKILL.md` and `docs/05-parallel-waves.md`, but different sections, so a rebase is mechanical. **Visible at once:** after the merge, the statusline shows `inbox: Checkmate 3, Project-Green-HR-MVP 6`, the current backlog of unhandled notices. That is the point, but expect it. |

## Context

- The board has five kinds of entry. The coordinator acts on `plan` and `hold` only, and stays that way. A `request` (another repo asks for a feature) and a `notice` (a fact with steps, such as an SDK release) reach only the agent: `coordination-inject.py` adds them to its context at session start.
- Those injected lines say nothing useful. `board.summary()` reads a `summary` field or the first body line, but requests carry `from`/`need` and notices carry `text`. The lines end after `status=-` (see this session's start).
- No rule tells an agent to raise them. `statusline.py` shows only blocked plans.
- `board.delete_expired_notices()`, called by the inject hook, deletes an expired notice without a word. A notice that was acted on stays until it expires. Example: Checkmate's 4.4.1 notice asks for `>=4.4.1,<5`, and Checkmate already pins `>=4.5.0`.
- History: none of the three archived plans tried an inbox. The parallel-waves plan (2026-11-16) set the rule that a notice is removed automatically after `expires`. D2 reverses that one rule and leaves the other kinds as they are.

## Decisions

| # | Decision | Alternative | Why this one |
|---|---|---|---|
| D1 | **A handled notice is deleted** with `board.py rm <repo>/<name>` by the agent that acted on it or closed it | A `status=done` field: the file stays, and every reader (hook, statusline, `list`) has to filter it out | The board holds only work in flight, and every entry has an owner who deletes it (`board.md`). Holds have `satisfied` because two parties need to see it. A notice is filed once per repo it concerns, so its copy has a single reader, and the record of the action is the commit that acted on it. |
| D2 | **An expired notice stays**, marked `STALE`, counted in the inbox and raised first, until someone closes it. `delete_expired_notices()` is removed | Keep deleting it and print "expired unhandled: …" once in the injected context | "Reported once" lands in whatever session starts first, often one in `~/Projects` about something else, where the agent has no reason to mention it. Staying visible matches every other kind ("never dropped silently"). A notice's `expires` is usually its deadline: the 5.0.0 notice expires on the sunset date, so an expired one is exactly what has to be loud. |
| D3 | **`board.py inbox [--repo R]`** lists the requests and notices. `board.inbox_entries(repo)` is the one definition, used by the CLI, the hook and the statusline | `board.py list --repo R --kind request` plus a second call for `notice`: two calls in the rule and a duplicated filter in the statusline | One named concept, owned by the module that owns the board. The rule can say it in one command. |
| D4 | **Context repos:** the rule says that for a context repo, acting on a notice means passing it to the owning team (the agent offers a draft) or doing an agreed contribution. The notice is closed once it has been passed on | Leave context repos out of the inbox | Project-Green-HR-MVP holds six SDK notices that only its team can act on. Leaving them out would hide them for good. |
| D5 | **The hook ends with one pointer line** when any shown repo has requests or notices: `Requests and notices are the repo's inbox: raise them per instructions.md § "A repo's inbox" once the session's work concerns that repo.` | Rely on the rule in `instructions.md` alone | One line at the place where the entries appear, at no cost when the inbox is empty. |

Checked against `design-conventions`:
- *Boundary*: the inbox definition lives in `board.py`, which already owns entry kinds.
- *Fail loud*: D2 removes a silent deletion, and the statusline keeps its existing rule that a broken entry never breaks it.
- *Minimum contract*: `inbox_entries()` returns `Entry` objects like `entries()`, with no new types.
- *Naming*: `inbox_entries` names what it returns.

## The rule (text for `instructions.md`)

New section `## A repo's inbox` at the end of *Repositories and their roles*, wording close to:

> A repo's open `request` and `notice` entries on the coordination board are its **inbox**: work another
> repo asked for, and steps a release asks of this one. The coordinator never acts on them; the agent whose
> session works on the repo does.
>
> - **When.** The first time in a session that the work concerns a repo, before proposing that work, run
>   `board.py inbox --repo <repo>` and raise each entry with the user. "Concerns a repo" means the session
>   runs inside it, the user names it in a session opened on `~/Projects`, or a plan starts there. Once per
>   repo per session; entries marked `STALE` first.
> - **A request:** offer to turn it into a `backlog.md` entry (backlog curation, see *Backlog
>   maintenance*); once that entry is committed, delete the request.
> - **A notice:** offer to act on it, now or as part of the planned work, or to close it because it is done
>   or no longer applies, saying why (for example "already pins `>=4.5.0`"). Delete it once acted on or
>   closed. In a context repo, acting means passing it to the owning team: offer a draft message.
> - An entry the user defers stays, and is raised again in the next session.
>
> Delete with `board.py rm <repo>/<name>`. A wave that acts on a notice names it in its plan and deletes it
> after the merge.

## Acceptance cases

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | Statusline counts the inbox per repo | Repo_X: 2 notices, 1 request, 1 plan (`ready`), 1 hold; Repo_Y: 1 notice | the statusline runs with `{}` | it prints exactly `inbox: Repo_X 3, Repo_Y 1` | unit |
| AC2 | Inbox sits after blocked plans and the phase | AC1's board plus a `blocked` plan `p1` in Repo_X, and a phase file `wave-12 — Implement` | the statusline runs with the session id | `wave-12 — Implement  \|  ⚠ 1 blocked: Repo_X/p1  \|  inbox: Repo_X 3, Repo_Y 1` | unit |
| AC3 | Silent when the inbox is empty | only plans and holds on the board, none blocked | the statusline runs | it prints nothing | unit (the existing blocked-plans test keeps asserting `""`) |
| AC4 | A closed notice leaves count and context | AC1's board | `board.py rm Repo_X/<one notice>`, then the statusline and the inject hook (cwd in Repo_X) run | the count reads `Repo_X 2`, and the notice's name is not in the injected context | unit |
| AC5 | An unhandled expired notice is kept and flagged | a notice in Repo_X with `expires=2000-01-01` and `text=raise the pin` | the inject hook runs, inside the repo and from outside every repo | the file still exists; its line in the context contains `raise the pin` and ends with `STALE`; the statusline counts it | unit |
| AC6 | Injected lines carry the content | a request with `from=Repo_Y / wave-7` and `need=a batch endpoint`, and a notice with `text=SDK 1.2 released` | the inject hook runs | the request's line contains `from Repo_Y / wave-7: a batch endpoint`; the notice's line contains `SDK 1.2 released` | unit |
| AC7 | `board.py inbox` lists only requests and notices | Repo_X and Repo_Y as in AC1 | `board.py inbox --repo Repo_X`, then `board.py inbox` | the first prints Repo_X's 3 lines and no plan or hold; the second also prints Repo_Y's notice; both exit 0 | unit |
| AC8 | Pointer line only with an inbox | (a) AC1's board; (b) a board with one `ready` plan only | the inject hook runs from outside every repo | (a) the context ends with the line from D5; (b) the context has no such line | unit |
| AC9 | The rule's wording | — | read `instructions.md` § *A repo's inbox* and the `wave` skill's Plan and Integrate steps | they state (1) the trigger, including a `~/Projects` session that names a repo and a plan starting there; (2) the command; (3) the offer per kind (request → backlog entry, notice → act or close, with the reason); (4) deletion with `board.py rm` after acting or closing; (5) `STALE` first; (6) once per repo per session; (7) context repos; (8) a wave deletes the notices it handled after the merge | review in the done check, element by element |

The existing tests that assert the old expiry deletion (`test_inject`, `test_inject_outside_repo_shows_all_boards`, `test_inject_outside_repo_silent_when_nothing_open`) are rewritten in Specify to AC5's behaviour. That is listed in the tests-first commit message.

## Contracts

- `board.py`:
  - `INBOX_KINDS = ("request", "notice")`
  - `inbox_entries(repo: str) -> list[Entry]`: entries of those kinds, in name order.
  - `summary()`: for a request, `from <from>: <need>`; for a notice, `<text>`. Either falls back to the `summary` field, then the first body line.
  - `is_stale()`: also covers `notice` (expired by date).
  - `delete_expired_notices()` is removed.
  - The CLI gets `inbox [--repo R]`, which prints `format_line()` per entry and exits 0.
- `coordination-inject.py`: deletes nothing. It shows the open entries as today, and adds the D5 line after the blocks when any shown entry is in the inbox.
- `statusline.py`: a third part, `inbox()`, joined with `"  |  "` after `blocked()`. Its format is `inbox: <repo> <n>[, <repo> <n>…]`, in `all_repos()` order, with repos at 0 left out, and `""` when there is nothing. Any exception gives `""`.

## Sub-tasks

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| S0 | Tests for AC1–AC8; rewrite the three expiry tests | `.claude/scripts/test_coordination.py` | — | The new tests fail for the stated reason; all others pass | `test-author` (medium) |
| S1 | Board script per the contract | `.claude/scripts/board.py` | S0 | AC4–AC7 tests pass | medium |
| S2 | Hook and statusline per the contract, docstrings included | `.claude/hooks/coordination-inject.py`, `.claude/statusline.py` | S1 | AC1–AC8 pass; full suite passes | medium |
| S3 | The rule, plus the skill and board text | `instructions.md`, `.claude/skills/wave/SKILL.md` (Plan: read the inbox; Integrate step 7: delete the notices the plan handles), `.claude/skills/wave/board.md` (kinds table, expiry paragraph, *Requests and notices* incl. the inbox and closing), `.claude/skills/coordinate/SKILL.md` (one line: requests and notices are each repo's inbox, not the coordinator's) | — | AC9, reviewed by me | inline |
| S4 | Documentation upkeep | `docs/01-hooks.md` (inject row, statusline section), `docs/05-parallel-waves.md` (the board's three rules: notice expiry), `docs/glossary.md` (*Inbox*), `backlog.md` (remove the entry), `docs/history/` | S1–S3 | `doc-conventions` loaded; the claims match the code | inline |
| S5 | Review of the diff | — | S1–S4 | No correctness findings left | `implementer-strong` |

## Verification

- `python3 .claude/scripts/test_coordination.py`, under `/usr/bin/python3` (3.9) and under the venv's 3.12: all pass.
- Smoke against the real board:
  - `echo '{}' | .claude/statusline.py` shows `inbox: Checkmate 3, Project-Green-HR-MVP 6`.
  - `echo '{"cwd":"/Users/peter/Projects"}' | .claude/hooks/coordination-inject.py` shows the notice texts and the pointer line, and deletes nothing.
  - `board.py inbox --repo Checkmate` shows its 3 notices.
- No acting on the real notices inside the wave. Closing Checkmate's obsolete 4.4.1 notice is the rule's first use, in a later session, with the user.

## Exit criteria

AC1–AC9 hold; suite green on 3.9 and 3.12; docs and board text match; backlog entry removed; plan archived.

## Board fields

`repo=agents wave=wave-04-inbox "title=An inbox for board requests and notices" mode=batch status=ready integration=push holds=[] exclusive=[] new_dependencies=[] approved=2026-11-23 expires=2026-12-07`
