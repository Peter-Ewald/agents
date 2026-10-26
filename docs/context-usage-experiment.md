# Context usage experiment

Raw `/context` snapshots collected at different points within a wave, across machines and sessions, to
see where context budget actually goes and whether an intervention (`/compact` cadence, JFrog Boost, …)
changes it. Data collection only — analysis happens when asked for, not as snapshots come in.

## Session 1 — Drainage-2.0, Windows machine

Model: `claude-opus-5-5`. JFrog Boost: not installed on this machine for this run (Windows — availability
to be confirmed separately; see harness notes).

### Snapshot A — session start

32.5k / 1.0M tokens (3%)

| Category | Tokens | Usage |
|---|---|---|
| System prompt | 3.5k | 0.4% |
| System tools | 20.9k | 2.1% |
| Custom agents | 221 | <0.1% |
| Memory files | 608 | <0.1% |
| Skills | 7.1k | 0.7% |
| Messages | 130 | <0.1% |
| Autocompact buffer | 33.0k | 3.3% |
| Free space | 934.5k | 93.4% |

Memory files (`/memory`):
- `~\.claude\projects\c--Users-PTEW-Projects-Drainage-2-0\memory\MEMORY.md` — 323
- `~\Projects\Drainage-2.0\.claude\rules\evaluation.md` — 250
- `~\Projects\Drainage-2.0\CLAUDE.md` — 35

Custom agents (`/agents`):
- `implementer` — 119
- `doc-sweep` — 102

### Snapshot B — after a while of planning, mostly having read files (documentation, code)

93.6k / 1.0M tokens (9%)

| Category | Tokens | Usage |
|---|---|---|
| System prompt | 3.5k | 0.4% |
| System tools | 21.5k | 2.2% |
| Custom agents | 221 | <0.1% |
| Memory files | 608 | <0.1% |
| Skills | 7.2k | 0.7% |
| Messages | 60.5k | 6.1% |
| Autocompact buffer | 33.0k | 3.3% |
| Free space | 873.4k | 87.3% |

Memory files and custom agents unchanged from Snapshot A.

## Later sessions

More snapshots to be appended below as they come in.
