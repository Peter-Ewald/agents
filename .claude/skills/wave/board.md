# The coordination board

The board holds the rules between waves that must outlast a session: plans, holds, requests, notices and
locks. It lives at `~/.claude/coordination/`, one folder per repo, named after the main checkout's
directory (`board.py repo` prints it), so every worktree of a repo maps to the same folder. Each entry is
one small file with a front matter header, so parallel sessions never edit the same file. Read and write
it only through `board.py`; `board.py list` shows the open entries.

| Kind | Filed under | Meaning | Removed by |
|---|---|---|---|
| `plan` | The repo the wave runs in | An approved plan: the wave's brief, its status and, while `waiting`, its handover | The wave agent, after the merge |
| `hold` | The waiting repo | The waiting wave may not start, or may not merge, until the condition is true | The waiting wave, once it has used the result |
| `request` | The repo asked to build something | One wave asks another repo for a feature | The agent working on that repo, once it is a `backlog.md` entry and, if needed, a hold |
| `notice` | Each repo it concerns | A fact with the steps it asks of the repo, for example "SDK 0.9.0 released" or a change the next release's `CHANGELOG.md` must cover | The agent working on that repo, once it acted on it or closed it as done or not applicable |
| `lock` (`lock.md`) | The repo being integrated | One wave is integrating; others wait before pushing to `main` or completing a PR | The holding wave, after the merge |
| `lock` (`lock-dataset-<name>.md`) | The repo that owns the dev dataset | One wave is pulling, merging and pushing that dataset | The holding wave, right after its push |

Every entry but a lock has an `expires` date. An expired entry and a lock older than two hours are shown
as `STALE`, never dropped silently.
The board holds only work in flight: history belongs in `docs/history/`, pending work in `backlog.md`.

## Wave identity

On the board a wave is `<repo> / wave-<NN>`. Its key `wave-<NN>` comes from its branch
`wave-<NN>-<slug>` (`board.py wave` prints it). The `coordination-guard.py` hook identifies a session's
wave the same way. Messages to the user name a wave by its plan's `title` with the number in brackets
instead, per `instructions.md`'s "Talking to the User".

## Filing a plan

On approval, write the session plan to a file and file it:

```sh
board.py file plan wave-12-batch-upload --repo Project-Green-HR-MVP --body-file <plan file> \
  repo=Project-Green-HR-MVP wave=wave-12-batch-upload "title=Batch upload" mode=batch status=ready \
  integration=pr "holds=[w12-needs-sdk-0.9]" "exclusive=[ports 8001 8002]" "new_dependencies=[httpx]" \
  approved=2026-11-16 expires=2026-11-30
```

| Field | Values |
|---|---|
| `title` | What the wave does, in a few words; messages to the user name the wave by it |
| `mode` | `batch` (the coordinator runs it) or `interactive` (a session the user drives) |
| `status` | `ready`, `running`, `waiting` (parked on a merge hold), `blocked`, `interrupted` |
| `integration` | `pr` or `push` |
| `exclusive` | Resources no other wave may use at the same time, for example service ports |
| `new_dependencies` | Approved with the plan; any other is a stop condition |
| `tests_first` | SHA of the tests-first commit, set in Specify |

The body is the plan as approved: goal, acceptance cases, sub-task table, exit criteria, verification
commands. Keep the status current with `board.py set <repo>/<name> status=<status>`.

A wave that stops on a stop condition appends its question, and the coordinator later the user's answer,
so the question survives a lost report or a restart:

```sh
board.py set <repo>/<name> status=blocked --append-body-file <file>   # ## Question, then Options
board.py set <repo>/<name> status=running --append-body-file <file>   # ## Answer
```

`board.py list --kind plan --status blocked` lists the plans waiting for an answer; the statusline of
every session shows them too.

## Holds

A hold is a "not before" rule between two waves, filed under the waiting repo:

```sh
board.py file hold w12-needs-sdk-0.9 --repo Project-Green-HR-MVP \
  "waiting=Project-Green-HR-MVP / wave-12" "on=Semantic_Evaluation / wave-58" \
  "condition=semantic-evaluation 0.9.0 published to Artifactory" \
  blocks=merge status=open expires=2026-11-27
```

| `blocks` | Used when | Effect |
|---|---|---|
| `start` | The waiting wave needs the other wave's code to be built at all | The coordinator does not start it until the hold is satisfied; it then starts from the new `main` |
| `merge` | It can be built on its own but must land after the other | It runs up to the done check and parks |

The wave that meets the condition sets `status=satisfied` (`board.py satisfy <repo>/<name>`) right after
its merge; the waiting wave deletes the hold once it has used the result. Every order you want without a
technical dependency is a hold too. The guard blocks pushing to `main` and completing a PR while an open
`merge` hold names the session's wave.

## Locks

```sh
board.py lock <repo> --wave wave-12                    # integration lock
board.py lock <repo> --wave wave-12 --dataset hr_dev   # dataset lock
board.py unlock <repo> --wave wave-12 [--dataset hr_dev]
```

`lock` exits 1 and names the holder when another wave holds it: wait and retry. Re-locking a lock you hold
succeeds. The integration lock covers rebase, re-verify, push or PR completion and cleanup; the dataset
lock only one pull and push. The guard blocks pushing to `main`, completing a PR and
`eval-dataset push` while another wave holds the matching lock.

## Parking and the handover

A wave whose `merge` hold is still open after the done check parks:

1. Push the branch; for `integration: pr` open the PR as a draft.
2. Append the handover to the plan entry (`board.py set <repo>/<name> status=waiting --append-body-file
   <file>`), so a fresh agent can integrate without the parked one's context:

   ```markdown
   ## Handover
   - Branch: wave-12-batch-upload, worktree <path>
   - PR: <link> (draft)
   - Verified on main at: <sha>
   - Waiting on: w12-needs-sdk-0.9
   - Integration still needs: <for example: bump the semantic-evaluation pin to 0.9.0, rerun the regression>
   - Report so far: <the report's acceptance cases and done check>
   ```
3. Return the report with status `waiting`. The worktree stays.

A parked wave costs nothing and does not count against the coordinator's limit of parallel waves. When the
hold is satisfied, the coordinator starts a fresh `wave-runner` briefed with the plan entry and its
handover, which runs only Integrate.

## Requests and notices

A repo's requests and notices are its **inbox**. The coordinator never acts on them; the agent whose
session works on the repo raises them with the user and closes them, per `instructions.md`'s "A repo's
inbox". The `coordination-inject.py` hook shows each line with its content (`from <from>: <need>` for a
request, the `text` of a notice) and the statusline counts them per repo (`inbox: Checkmate 3`).

File one with its content in the fields the inbox shows; for a notice, `expires` is the date by which the
repo must have acted, after which it is shown as `STALE`:

```sh
board.py file request from-green-w12-batch-api --repo Semantic_Evaluation \
  "from=Project-Green-HR-MVP / wave-12" "need=a batch upload endpoint" expires=2026-11-30
board.py file notice sdk-0.9.0-released --repo Project-Green-HR-MVP \
  "text=semantic-evaluation 0.9.0 is on Artifactory; raise the pin to >=0.9.0,<1" expires=2026-12-07
```

List and close them:

```sh
board.py inbox --repo Checkmate     # one repo; without --repo, every repo
board.py rm Checkmate/sdk-4.4.1-released
```

A handled notice is deleted, not marked done: each repo has its own copy, and the commit that acted on it
is the record. A wave that acts on a notice names it in its plan and deletes it after the merge.
