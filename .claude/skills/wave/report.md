# The wave report

Every wave agent, batch or interactive, ends with this report. It goes back to the coordinator (a batch
wave's final message, nothing else) and into the PR description, so it stays with the change.

```
Status: merged | waiting | blocked | failed
Question: <only when blocked: one question that stands on its own: the case or plan row, what was tried>
Options: <only when blocked: two to four answers, the recommended one first>
Wave: <repo> / <wave name>
PR: <link>, merged as <sha>          (or: pushed to main as <sha>)

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

The question comes right after the status so the coordinator can ask it without reading further; the
coordinator puts it to the user as a dialog, with the options as the choices. `[x]` passed, `[ ]` failed,
`[-]` not applicable. A `waiting` report carries the done check as it stood
when the wave parked; a `blocked` or `failed` report says which phase it stopped in.
