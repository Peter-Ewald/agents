# Skills and subagents

Several pieces, each chosen for a different reason. See [glossary.md](glossary.md) for what
distinguishes a skill from a subagent.

## `wave` (skill)

[`../.claude/skills/wave/SKILL.md`](../.claude/skills/wave/SKILL.md)

Drives a wave from `backlog.md`'s Next Up tier through the phases of `instructions.md`'s Implementation
Waves section: Plan, Specify, Implement, Documentation upkeep, Verification, Done check, Integrate, Report.
Every wave runs in its own worktree on a branch `wave-<NN>-<slug>`, created by
`new-wave-worktree.sh` from the current `origin/main`.

| Supporting file | Holds |
|---|---|
| [`tiers.md`](../.claude/skills/wave/tiers.md) | The implementer tiers, which task types map to which, the escalation rule |
| [`board.md`](../.claude/skills/wave/board.md) | Board entry formats, holds, locks, parking and the handover |
| [`report.md`](../.claude/skills/wave/report.md) | The wave report |

**Batch and interactive.** A wave is a batch wave unless you say "run wave N interactively". Both plan in
plan mode with you. A batch wave is then filed on the board as `ready` and the coordinator starts a
`wave-runner` for it; an interactive wave is filed as `running` and the planning session runs it, asking
you its questions directly. Both follow the same phases and neither asks for approval before a commit,
push or pull request: the done check replaces it.

**Plan.** Checks `docs/history/index.md` for prior plans on a related topic, writes the session plan with
acceptance cases (one row per behaviour: given, when, then, checked by), a sub-task table (owned files,
dependencies, acceptance check, `Runs as` tier) and the board fields (holds, exclusive resources, approved
new dependencies, `integration`), and checks it against `design-conventions`. On approval the plan is filed
on the board. A plan dropped instead of approved is archived right there with outcome `dropped`.

**Specify.** `test-author` turns the acceptance cases into failing tests and eval items. The wave agent
checks each against its case and commits the tests as the tests-first commit; from then on they are
frozen. Eval items go to the dev dataset tagged `pending:<repo>/<wave key>` and are not run.

**Implement.** The wave agent briefs one `implementer-<tier>` per sub-task and reviews every diff itself.
A correction or a `blocked` report moves the sub-task one tier up, once.

**Documentation upkeep.** Scoped to what the wave made wrong: the wave's `backlog.md` section, false
claims in docs, the archived plan in `docs/history/`. A wave never runs a documentation sweep; that is a
sweep wave (see `doc-sweep`).

**Verification and done check.** Verification runs in the wave agent. The done check is a table of rows
(acceptance cases, frozen tests unchanged, verification, eval results, documentation, backlog, history,
changelog), each needing evidence; a failing row sends the wave back to Implement.

**Integrate and report.** Parks on an open merge hold, otherwise takes the integration lock, rebases,
re-verifies and lands the wave by rebase and fast-forward: a pull request for `integration: pr`, a direct
push of `main` for `integration: push`. Afterwards it removes its `pending:` tags (under the dataset lock),
satisfies the holds waiting on it, releases the lock and deletes the worktree and branch. The report goes
into the pull request description. See [`05-parallel-waves.md`](05-parallel-waves.md) for the board,
holds, parking and the coordinator.

At each phase transition the skill overwrites `/tmp/claude-wave-phase-${CLAUDE_SESSION_ID}`, which the
statusline script reads to show the current phase. That path, not the session's own scratchpad directory,
is deliberate: the statusline runs as a separate process that only receives a session ID on its own stdin,
so the hand-off point has to be derivable from the session ID alone.

Before writing the plan it checks `docs/history/index.md` so it does not re-propose a direction already
tried and dropped. A completed plan is archived in Documentation upkeep. See `instructions.md`'s *Plan
history* section for the convention.

## `coordinate` (skill)

[`../.claude/skills/coordinate/SKILL.md`](../.claude/skills/coordinate/SKILL.md)

Turns a session into the coordinator: the one long-lived session, started in `~/Projects` with
`claude --name coordinator` and then `/coordinate`, that works through the coordination board across all
repos. It checks at start that background tasks are enabled, keeps `board.py watch-for-work` running as
a Monitor so a newly `ready` plan or a satisfied hold wakes it even when idle, starts `ready` plans as
background `wave-runner` agents (at most four at once, respecting start holds and exclusive resources)
and records each one's agent ID on its plan entry, asks you a blocked wave's question in a dialog of its
own and passes your answer back to that agent ID, wakes parked waves by starting a fresh `wave-runner` on
their handover once the hold is satisfied, and rebuilds its state from the board after a restart. It never edits code, never merges and never answers a wave's
question itself.

## `doc-conventions` (skill)

[`../.claude/skills/doc-conventions/SKILL.md`](../.claude/skills/doc-conventions/SKILL.md)

`paths: ["**/*.md"]` — loads automatically whenever a markdown file under the session's working directory
is being read or edited. The glob is matched relative to that directory, so a session that `cd`s into one
repo stops loading the skill for markdown in the others; `keep-working-directory.py`
([`01-hooks.md`](01-hooks.md)) blocks that `cd` in the main session.
Contains the terminology, glossary-placement, README-structure, and mermaid-rendering conventions that
used to live as always-on prose in `instructions.md`. Moving it into a path-scoped skill means it only
enters context when a markdown edit is actually happening, instead of competing for attention the entire
session regardless of whether any docs are being touched — and it's the single definition both `doc-sweep`
(below) and the eventual `/wave` documentation phase apply, rather than two competing copies.

## Implementer tiers and `implementer-contract`

[`../.claude/agents/implementer-light.md`](../.claude/agents/implementer-light.md),
[`implementer-medium.md`](../.claude/agents/implementer-medium.md),
[`implementer-strong.md`](../.claude/agents/implementer-strong.md),
[`../.claude/skills/implementer-contract/SKILL.md`](../.claude/skills/implementer-contract/SKILL.md)

Each carries out one sub-task of an approved wave plan: the files it owns, the contract the plan fixed,
the frozen tests and the acceptance check. The three agents differ only in model and effort; all preload
the `implementer-contract` skill, which holds the brief an implementer receives, how it works and the
fixed short report it returns.

| Tier | Model, effort | Typical work |
|---|---|---|
| `implementer-light` | Haiku, low | Mechanical, fully specified edits; locating code; condensing a large payload |
| `implementer-medium` | Sonnet, medium | A sub-task with a fixed contract and frozen tests; doc rewrites of touched code |
| `implementer-strong` | Opus, high | Root-cause debugging, risky refactors, independent review, the retry after a lower tier blocked |

The wave agent picks the cheapest tier that can do the sub-task well, never a cheaper one, using the
mapping in the `wave` skill's `tiers.md`. Each implementer is fresh with a small context, so the many
edit-and-test calls re-read little on a cheaper model. It never plans or widens its scope: an ambiguous
contract, a frozen test it believes is wrong or a needed file outside its brief is a `blocked` report. The
report has a fixed short shape with no diffs, because the wave agent reviews the diff itself. An
implementer has no `Agent` tool, so it cannot delegate further, and it runs once: a retry is a new brief,
one tier up.

## `test-author` (subagent)

[`../.claude/agents/test-author.md`](../.claude/agents/test-author.md)

Runs in a wave's Specify phase. It turns the plan's acceptance cases into unit or integration tests and
eval items, from the plan and the codebase only, never from an implementation. Each check must fail now,
for the reason its case states, and will pass once the behaviour exists. For an LLM agent it follows the
`semeval-maintain` and `semeval-datasets` skills plus the wave-only steps: eval items are pushed to the
dev dataset under the dataset lock, tagged `pending:<repo>/<wave key>`, and not run. Runs on Sonnet at
medium effort; the wave agent briefs it with `model: "opus"` for concurrency, auth, migrations or a
published SDK API.

## `wave-runner` (subagent)

[`../.claude/agents/wave-runner.md`](../.claude/agents/wave-runner.md)

The wave agent of one batch wave, started in the background by the coordinator. It preloads the `wave`
skill and runs it from Specify to Report on the plan entry named in its brief, in the wave's worktree,
without asking anyone: a stop condition ends the run with a `blocked` report and one question. Briefed with
a handover instead, it runs only the Integrate phase of a parked wave. Runs on Opus at high effort.

## `doc-sweep` (subagent)

[`../.claude/agents/doc-sweep.md`](../.claude/agents/doc-sweep.md)

The work of a sweep wave, or an ad hoc request ("update documentation" without further scope, or a scoped
documentation rewrite). Inside a sweep wave the approved plan is the confirmation, so it applies its fixes
directly and lists every change in its report. Asked ad hoc in a chat, it proposes the fixes as a plan first
and applies them only after you confirm. Full tool access (`Read`, `Grep`, `Glob`, `Edit`, `Bash`,
`Write`): a sweep can rename, split, merge or create documentation files as the reorganization requires.
Deliberately **fresh**, with no wave or implementation context: a sweep re-derives doc-vs-code accuracy
from scratch and cross-checks docs against the actual implementation instead of trusting what the recent
conversation believes. Preloads `doc-conventions` via its `skills:` frontmatter field so the same rules
apply without a markdown file being touched first. A `general-purpose` agent has the same tool access but no
preloaded conventions.

Also checks `docs/history/index.md` (if present) for entries relevant to the area being swept, to write a
better-grounded "why" for existing patterns. Per the *Plan history* guardrail in `instructions.md`, that
history is synthesized into a present-tense explanation, never narrated as a timeline.

See `instructions.md`'s "Documentation update: choosing the mechanism" for how this fits alongside a small
inline edit and a wave's own documentation upkeep.

## `deck-visual-check` (subagent)

[`../.claude/agents/deck-visual-check.md`](../.claude/agents/deck-visual-check.md)

Checks how a PowerPoint deck's slides look, so their images never enter the main session: a slide image
costs about 1,500 tokens and would be re-sent with every later tool call. The brief names the deck, the
slides (`all` or a list) and, optionally, fonts outside the safe list. The agent renders those slides with
[`../.claude/scripts/render_deck.py`](../.claude/scripts/render_deck.py), reads each image, and returns
only a list of layout defects per slide (overflow, overlap, tight margins, misalignment, broken words,
blank characters, leftover placeholders); content errors are a separate fact check. Runs on Sonnet at
medium effort with `Read` and `Bash` only.

`render_deck.py DECK OUT_DIR [--dpi N] [--slides SPEC]` renders through PowerPoint itself, because only
PowerPoint shows how its own fonts render: it copies the deck into PowerPoint's sandbox folder (so no
file-access dialog appears), exports the copy as PDF via AppleScript, and turns the requested pages into
`slide-NN.png` with `pdftoppm`. The original deck is never opened, so a deck someone has open is safe.

The `pptx` skill's own instructions ask for this check in the session that builds the deck. That skill
is synced from claude.ai, which overwrites a local edit, so the override lives in `CLAUDE.md`'s *Token
economy*: the check always runs in `deck-visual-check`. A deck built by a script gets every slide on the
first round and only the changed slides after a fix; a deck the user maintains that the agent edited gets
only the changed slides; a deck the user edits in PowerPoint gets no check.

## `design-conventions` (skill)

[`../.claude/skills/design-conventions/SKILL.md`](../.claude/skills/design-conventions/SKILL.md)

Design and architecture principles — naming, module boundaries, error-handling philosophy, interface
discipline — the code-design equivalent of `doc-conventions` (documentation quality) and
`ruff-cleanup/RULES.md` (lint-fix quality). One file, not split like `ruff-cleanup`: design principles
are narrative/read-and-apply, not a growing per-code lookup table. No `paths:` trigger — there's no
file-glob that means "about to make a design decision" the way `**/*.md` means "editing a markdown
file" — so it relies on natural-language matching plus explicit invocation from `instructions.md`'s Plan
phase bullet and `wave/SKILL.md`'s Phase 1, both of which invoke it via the Skill tool per `CLAUDE.md`'s
"Skill freshness" note rather than working from a remembered read.

Seeded with five starter principles (naming clarity, boundary and ownership clarity, fail loud not
silent, consistency over cleverness, minimum-contract interfaces) deliberately avoiding overlap with
Claude Code's own baseline instructions — expected to grow from real cases the same way `RULES.md` does.

## `ruff-cleanup` (skill)

[`../.claude/skills/ruff-cleanup/SKILL.md`](../.claude/skills/ruff-cleanup/SKILL.md)

Triggered by "clean up remaining ruff issues" or similar, or invoked directly (`/ruff-cleanup`). A
**skill**, not a subagent like `doc-sweep`: it runs inline in the main conversation. `doc-sweep` needs to
be fresh to avoid the agent's own self-serving read of "is this doc still accurate," but `ruff check`'s
output is an external, objective source of truth regardless of what the conversation believes, so there is
no analogous bias risk, and the skill benefits from the conversation's own context on why recent edits
were made.

Defaults to PR-diff scope (files changed vs. the base branch, not the whole repo) — matches "minimal
changes" and the literal "clean up before a PR" framing; whole-repo only runs if explicitly requested.
Everything it finds already survived the `ruff-autofix` hook's safe fixes on every edit along the way,
so by definition it needs either an unsafe fix or actual code judgment. Consults
[`RULES.md`](../.claude/skills/ruff-cleanup/RULES.md) — a house-rules file mapping specific ruff codes
to this codebase's fix guidance — and refuses to improvise a fix for a code with no entry: it drafts a
proposed entry, waits for confirmation, appends it, then applies it. `RULES.md` is seeded with F401,
F841, E501, and B006 on day one and is expected to grow the same way S_Factory's break-agent checklist
grew — one confirmed real case at a time, never bulk-authored ahead of an actual encounter. Bounded
retry (three attempts total) rather than an unbounded loop. Finishes by running the test command the
repo's `CLAUDE.md` names, the same one a wave's Verification phase uses.

## `sdk-release` (skill)

[`../.claude/skills/sdk-release/SKILL.md`](../.claude/skills/sdk-release/SKILL.md)

Releases `semantic_tracing` or `semantic_evaluation`: checks the changelog has an entry for the target
version, then runs the bundled [`scripts/release.sh`](../.claude/skills/sdk-release/scripts/release.sh):
version bump; relock of every project in the repo that installs the package editable, through
[`scripts/relock-editable.sh`](../.claude/skills/sdk-release/scripts/relock-editable.sh); `rm -rf dist/`,
`uv sync`, `uv build`, `uv publish --index ramtech-pypi`; then it stages `pyproject.toml`, `CHANGELOG.md`
and every relocked `uv.lock` together. It does not commit. The relock finds its projects from the
git-tracked `uv.lock` files that record the package with an editable source, so a new pod is covered
without a list to maintain, and it runs before publishing, so a project whose lock cannot take the new
version stops the release with nothing published. It does not compare the new version with a project's
declared version range: uv ignores that range for an editable path source. Bundled as an actual script
rather than prose instructions the model reproduces from memory each time, since the exact command and
flags (`uv publish --index ramtech-pypi dist/<package>-<version>*`) are exactly the kind of thing that's
easy to mistype once and shouldn't depend on being remembered correctly. After a successful release it
also checks other repos in the workspace for stale version pins and reports them — it doesn't bump those
repos automatically.

## `langfuse-upgrade` (skill)

[`../.claude/skills/langfuse-upgrade/SKILL.md`](../.claude/skills/langfuse-upgrade/SKILL.md)

Triggered by pasting a langfuse changelog/release notes, mentioning a new langfuse version, or asking to
check/upgrade the langfuse dependency — both `semantic_tracing` and `semantic_evaluation` wrap the
`langfuse` Python SDK directly, and it has a track record of removing REST client methods inside otherwise
normal minor releases, so a new release is worth checking deliberately rather than just bumping the
version constraint.

Investigates via a **forked** agent with `isolation: "worktree"` — a fork rather than a fresh subagent
because it needs the session's existing understanding of both SDKs without re-explaining the repo, and a
worktree because it bumps a dependency and runs real installs/tests, which must never touch the actual
working directory or its uncommitted changes. The fork reads the real changelog, temporarily pins the
target version in both packages, runs both test suites, greps for every langfuse surface each package
actually uses, and returns per-package findings: what broke, why, a proposed fix, and a SemVer
classification (patch if the fix stays internal, major if it forces a public-API change) per
`instructions.md`'s published-package policy.

Nothing is applied from the worktree — the main conversation presents the findings and versioning
consequence in chat and waits for explicit agreement (mirroring a wave's Plan-phase gate) before applying
anything for real in the actual checkout. Ends by writing each affected package's `CHANGELOG.md` entry
under the agreed next version — the exact entry `sdk-release` (above) checks for — and drafting a commit
message, but deliberately stops short of bumping `pyproject.toml`'s version number or publishing: that
handoff to `sdk-release` is intentional, since `sdk-release` already expects the changelog entry this skill
just wrote.


## `semeval-*` (nine skills)

`semeval-setup-evaluation`, `semeval-setup-tracing`, `semeval-maintain`, `semeval-datasets`,
`semeval-metrics`, `semeval-experiment`, `semeval-review-loop`, `semeval-model-pricing`, `semeval-guide`.

These are not stored in this repo. Each `~/.claude/skills/semeval-<name>` link points at
`~/Projects/Semantic_Evaluation/agent_skills/<name>`, the source of truth published with the SDK, so they
update with that checkout. They set up and run offline evaluation and Langfuse tracing for an LLM agent
with the `semantic_evaluation` and `semantic_tracing` SDKs, and every repo that builds an agent needs them.
Each skill is self-contained: its `references/` folder holds the templates it copies into a project
(manifest, run files, CI snippet, rules).

What stays in the consuming repo is the **always-on rule**, not the skills. `semeval-setup-evaluation`
writes a short rule into the project (`.claude/rules/evaluation.md` and/or a `CLAUDE.md` section) saying
that a change to the agent's behaviour is not done until its evaluation impact is checked, via the
`semeval-maintain` skill. That rule is project-specific, because it points at the project's
`evaluation/coverage.md`. Without it the skills still work, but nothing asks for them when the agent
changes. Re-run `semeval-setup-evaluation` for the rule in a new repo.

`semeval-maintain` is the one that matters day to day. The others run when evaluation is set up, a dataset
is released, metrics change or an experiment compares configurations.

**In a wave.** The semeval skills describe the single-session case: `semeval-maintain` tags new items
pending, a run leaves pending items out unless they are selected, and the tags come off after the merge.
A wave adds, through the `wave` skill and `test-author`: the tag names the wave key,
`pending:<repo>/<wave key>`, instead of the branch; every pull and push of a dev dataset happens under the
dataset lock; the items are not run in Specify, before the behaviour exists; Implement runs them by id
with three repeats (`eval-run --items <ids> --repeats 3`); and Verification runs the full regression
with the wave's own tag (`--include-pending pending:<repo>/<wave key>`).
