# The wave report

Every wave agent, batch or interactive, ends with this report. It goes back to the coordinator (a batch
wave's final message, nothing else) and into the PR description, so it stays with the change. It has two
parts: a head for the user, above the line, and the evidence for the PR, below it.

```
Status: merged | waiting | blocked | failed
Wave: the <plan title> wave (<NN>), <repo>
Question: <only when blocked: one question that stands on its own, see below>
Options: <only when blocked: two to four answers, the recommended one first, each with its effect>
For the user: <attention items in plain words, or "nothing">
Outcome: <one to three lines at the wave's reporting level>
PR: <link>, merged as <sha>          (or: pushed to main as <sha>)
---
Acceptance cases
  AC1  tests/test_upload.py::test_duplicate_id_rejected  pass
  AC3  item green-hr-routing-014                         pass 3 of 3

Done check
  [x] verification: ruff check, ruff format --check, pytest -q   pass
  [x] regression run <Langfuse run name>                        gate passed
  [x] frozen tests unchanged since <sha>
  [x] frozen eval items unchanged since <version label>
  [x] docs upkeep: README.md, docs/03-upload.md
  [x] backlog section removed
  [x] plan archived: docs/history/2026-11-17-batch-upload.md
  [-] CHANGELOG: no released package
  [x] no open hold; rebased on <main sha> and re-verified

Exit criteria: <each, met or not, with its evidence>
Tests added beyond the cases: <list, or none>
Deviations from the plan: <list, or none>
Board: <holds satisfied, notices and requests filed>
Follow-ups for the backlog: <list, or none>
```

## The head

The head follows `instructions.md`'s "Talking to the User": it is what the user reads, and the
coordinator relays it unchanged.

- **Question** stands on its own, because the dialog may be all the user sees: what the wave is for, the
  acceptance case or plan row in plain words, what was tried, why it cannot go on, and what each option
  changes for the wave and for other waves.
- **For the user** holds every attention item: a failed or flaky run, a missed gate, a failure that is not
  this wave's, an inconsistency, a deviation from the plan, a new dependency, a breaking change, a
  follow-up that changes another backlog entry or wave. Each says what happened, why it matters for the
  wave's goal and what the user may want to do. "nothing" when everything went as planned.
- **Outcome** names what the wave produced at its reporting level (modules grouped by service or package
  for code; documents and sections for design work; files for a sweep), and verification as one result:
  "acceptance cases pass; Copilot eval set copilot-dev v3 passed 3 of 3". No file lists, no process
  steps.

## The evidence

Below the line is the record for the PR: `[x]` passed, `[ ]` failed, `[-]` not applicable. A `waiting`
report carries the done check as it stood when the wave parked; a `blocked` or `failed` report says which
phase it stopped in.
