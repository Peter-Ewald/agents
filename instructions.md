# Working Instructions

Shared conventions for all AI coding assistants. Tool-specific adapters (`CLAUDE.md`, `copilot_instructions.md`) extend this file with mechanics that differ per tool. Read this file first.

---

# Working Mode

- Default mode is normal conversation: discuss, research, and curate `backlog.md` freely — adding, reordering, and reprioritizing entries directly, no permission boundary needed, since a backlog entry stays high-level by design (see "Backlog tiers") rather than a concrete session plan. Enter plan mode specifically when you're ready to lock in a concrete implementation approach for one specific change — "let's plan X," "let's start wave N," or an equivalent explicit signal — not for general discussion. Once entered, stay in plan mode only as long as *that specific plan* is being finalized; if discussion has already converged in normal mode first, this should be a short closing step, not a restart of the whole conversation. Only exit on an explicit go-ahead in the same conversation. Plan mode's own approval step ("keep planning with feedback" vs. approve and proceed) is the gate; no separate confirmation ritual is needed on top of it. For changes too small to warrant planning (a typo, an obvious one-line fix, a narrowly and explicitly specified instruction), skip plan mode and just make the change.
- Do not preserve backward compatibility unless I explicitly ask for it. **Exception — published packages** (`semantic_tracing`, `semantic_evaluation`): these are distributed via Artifactory and installed by external clients; follow SemVer within the major version. Patch and minor releases must be backward compatible drop-in replacements. Breaking changes require a major-version bump and a CHANGELOG entry. "Public API" means any symbol exported from `__init__.py` and documented in `docs/`. Clients should declare `>=x.y.z,<{next_major}` (e.g. `>=0.2.2,<1`) so they receive updates automatically but are protected from breaking changes.
- When changing code, comments, or documentation, **rewrite or remove** obsolete material instead of appending paragraphs that refer to earlier states. The final result should read as if it had been written this way from the start, not as an accumulation of edits.
- In chat, address me directly and may use first person. In any committed file (code comment, `.md`, commit message), write for a future repo reader who has no access to this conversation — no "as we discussed", no "per your request".
- Increase readability with tables, lists, and (in `.md` files only — not chat) mermaid diagrams. Keep prose concise. Build mermaid diagrams vertically; use swim lanes whenever an additional dimension improves separation.

---

# Clarifying Questions (Both Directions)

The same shape applies whether I am asking you for clarification, or you are asking me for guidance during planning, discussion, or while drafting `backlog.md` or the session plan:

- Explain the broader context first: the goal, the design principles in play, what the choice influences.
- Define any term that could create different mental models.
- Spell out the implications of each option in light of the bigger picture, not just the local code.
- When more than two reasonable options exist, present them as a small table with columns *option / impact / reversibility* so the other side can choose at a glance.

A bare question without that scaffolding is rarely useful in either direction.

---

# Talking to the User

Applies to every chat message, the wave report's `For the user:` field, and everything the coordinator
relays. Commit messages and the PR description keep their own detailed formats.

**Attention first, in plain words.** What needs a decision or should change my picture of the work comes
first, with enough context to act on it without opening a file: what happened, why it matters for the
wave's goal, the relevant part of the backlog (only that part), and the options with a recommendation
(the table from *Clarifying Questions* when there are more than two). These always count as attention
items and get that context:

- a failed run or a missed gate, and a failure that is not this wave's
- an inconsistency between plan, code, docs, backlog or another wave
- a deviation from the approved plan, a new dependency, a breaking change
- anything that changes another wave's assumptions or order

**Everything else gets one line, at outcome level.** Verification is a result, not a procedure:
"Copilot eval set copilot-dev v3 passed", not the commands, files and run ids behind it. Process steps
that went as planned (worktree, rebase, backlog edit, plan archive, lock) are not mentioned at all.
Define a term on first use when it could be read two ways.

## Reporting level

Report at the level I review at, which depends on what the work produces: behaviour for code, text for
design and documentation. Name the units of the output, one level above the individual edits. An
attention item goes as deep as I need to act on it, down to the test or line if that is what decides.

| Kind of work | Report at | Example |
|---|---|---|
| Implementation wave | Modules or capabilities, grouped by service, package or repo | "Scoring service: judge evaluators, catalogue. SDK: run-file loader, `eval-run`." |
| Refactor that keeps behaviour | The same, plus one line that behaviour is unchanged | "SDK dataset module split in two; behaviour unchanged, suite passed." |
| Experiment | Configurations and their metrics, and the decision they support | "gpt-5-mini vs gpt-5: correctness 4.1 vs 4.3, cost −60 %." |
| Architecture or concept work in files | Document and section, with what each section now decides | "architecture/03-scoring.md § Gate: gates compare normalized scores only." |
| Documentation sweep | File, with the false claim and its correction | "docs/05-runs.md said resume needs a run id; it reads the manifest. Fixed." |
| Harness or instruction changes | File and rule | "instructions.md § Talking to the User: new reporting levels." |
| Backlog curation | Entry and tier | "The split-library wave moved to Next Up, step 2." |
| Coordinator | One line per wave; attention items in full | "The repeat-the-Copilot-eval-runs wave (41) merged; eval set v3 passed." |

Work that mixes kinds is reported by its main output: documentation upkeep in an implementation wave is
housekeeping and goes unmentioned, while in a sweep wave the documents are the output. A wave plan
follows the default for its kind and states a `Reporting level:` line only when it differs.

## Naming waves

Name a wave by what it does, with its number in brackets: "the *repeat the Copilot eval runs* wave (41)
should land before the *split the knowledge library* wave (45), because …". The description comes from
the plan's title, or else the branch slug. Add the repo only when the number alone is ambiguous:
"(Semantic_Evaluation 63)". Never a bare "wave 41".

---

# Repositories and their roles

Every session starts in `~/Projects`, the folder that holds each repository as a subfolder, opened as one
window. A repository's role sets what an agent does there by default.

| Role | Repositories | What an agent does there |
|---|---|---|
| Active | `Semantic_Evaluation`, `Checkmate`, `agents` | Waves, backlog, coordination board |
| Context | `ramgpt-next`, `Project-Green-HR-MVP`, `IDP` (Keel, the developer platform), `Chapter_Repos` (one git repository; all its project folders) | Read, `git fetch`, read other branches with `git show` or `git diff origin/<branch>` (switch the checkout only when asked). No commit, no push |
| Later | `Training`, `Website`, `Drainage 2.0` | Nothing until this table promotes it |
| Ignored | `Archive`, `MLDEC-CC-harness` | Never read (denied in the global settings) |

A context repository's own `CLAUDE.md` describes that repository. Its workflow, commands, skills and
agents belong to its owning team and apply only to an agreed contribution.

**A role is a default; one piece of work can override it.**

| Override | How | What changes |
|---|---|---|
| A contribution to a context repository | The wave plan carries `Role: contribution, agreed with <team>`; for small work outside a wave, the user says so in chat | The change lands through a pull request (`integration: pr`) and follows the owning team's branch, pull request and code conventions. No file of this harness (`backlog.md`, `docs/history/`, `.claude/rules/`) is committed there; the plan and its archive stay in the active repository the work serves |
| A lasting change of role | Edit the table above | Every later session |

## A repo's inbox

A repo's open `request` and `notice` entries on the coordination board are its **inbox**: work another
repo asked for, and steps a release asks of this one. The coordinator never acts on them; the agent whose
session works on the repo does. `board.py` below is `~/Projects/agents/.claude/scripts/board.py`.

- **When.** The first time in a session that the work concerns a repo, before proposing that work, run
  `board.py inbox --repo <repo>` and raise each entry with the user. The work concerns a repo when the
  session runs inside it, when the user names it in a session opened on `~/Projects`, or when a plan
  starts there. Once per repo per session; entries marked `STALE` (past their `expires` date) first.
- **A request:** offer to turn it into a `backlog.md` entry (backlog curation, see *Backlog
  maintenance*). Once that entry is committed, delete the request.
- **A notice:** offer to act on it, now or as part of the planned work, or to close it because it is done
  or no longer applies, saying why (for example "already pins `>=4.5.0`"). Delete it once acted on or
  closed. In a context repo, acting means passing it to the owning team: offer a draft message, and close
  the notice once it is passed on (or do an agreed contribution).
- **Deferred:** an entry the user defers stays, and is raised again in the next session.

Delete an entry with `board.py rm <repo>/<name>`. A wave that acts on a notice names it in its plan and
deletes it after the merge.

---

# Implementation Waves

Non-trivial work is organised into **waves**. A wave is one coherent slice of change that lands as a single completed objective (not a single commit). Sub-waves (`0.A`, `0.B`, …) split a wave when parts can land independently.

Every wave runs through fixed phases in order:

1. **Plan** — before any code change, write a detailed plan to the session plan (see your tool's adapter file for exactly where this lives). The plan names every file to touch, every verification step, the wave's exit criteria and its **acceptance cases** (see *Tests first*), and splits the work into sub-tasks, each with the files it owns and the check that proves it done. Before finalizing the approach, invoke the `design-conventions` skill fresh (see your tool's adapter file's "Skill freshness" note) and check the plan against it. Approving the plan is the approval for everything after it, up to the merge. Track the current phase explicitly throughout the work — see your tool's adapter file for the mechanism.
2. **Specify** — the acceptance cases become failing tests and eval items, written by an agent that does not implement them, and are committed as the wave's first commit. See *Tests first*.
3. **Implement** — code, config, fixtures, until the frozen tests pass.
4. **Documentation upkeep** — first-class part of the wave, not a follow-up, but scoped to what the wave actually changed rather than to `docs/` as a whole. See *Documentation update phase* below.
5. **Verification** — run the test suites, the regression run for an LLM agent, and any smoke commands listed in the plan. Distinguish failures caused by this wave from pre-existing failures, and call the pre-existing ones out by name when reporting.
6. **Done check** — every acceptance case passes, the frozen tests and eval items are unchanged (or each change is listed with its reason), verification passed, documentation upkeep, `backlog.md`, the plan archive and any `CHANGELOG.md` entry are done. A failing check sends the wave back to Implement.
7. **Integrate** — rebase on the current `main`, re-verify, and land the change with its commit message (see *Commit messages* below); then report. See *Worktrees and integration*.

Mark a wave done only after the done check passes. Nobody approves the commit, push or PR separately: the plan approval and the done check together replace that.

## Tests first

The tests are what the plan's approval relies on, so the expected behaviour is fixed **before** implementation, by agents that do not write the code:

| Role | Writes |
|---|---|
| Planning, with me | **Acceptance cases** in the plan: for each behaviour the situation, the action and the expected outcome, in words and data I can check. For an LLM agent, the eval item's input and expected output |
| A test author, not the implementer | The cases as unit or integration tests and as eval items. Each test must fail, for the reason the case states, before any implementation exists |
| Implementers | Code until the tests pass. They may add tests for details they introduce |

The committed tests (the **tests-first commit**) and the eval items are then **frozen**: an implementer who believes one is wrong stops and asks. Eval items live in the dev dataset in Langfuse, the single source of truth: they are pushed right after they are written, tagged as pending for their wave until it merges, and not run until the behaviour exists. Every push pulls the dataset first and merges what changed in Langfuse since, so parallel waves never overwrite each other.

Documentation and sweep waves have no acceptance cases; a refactor that keeps behaviour uses the existing suite; an experiment measures rather than asserts. The plan says which applies.

## Worktrees and integration

- Every wave runs in its own git worktree on a branch `wave-<NN>-<slug>`, so several waves run at the same time without touching each other's files.
- History on `main` stays linear: rebase and fast-forward, never a merge commit created by a wave. A repo with a branch policy integrates through a pull request; a repo whose instructions (its `CLAUDE.md` or an untracked `.claude/rules/*.md`) carry an `Integration: push` line pushes `main` directly.
- Integration is serial per repo: a wave holds the repo's integration lock from its rebase to its merge. Dependencies between waves are explicit **holds** ("may not start" or "may not merge before"), never a planned order.

## Plan files: lifetime and purpose

| File | Lifetime | Purpose |
|---|---|---|
| `backlog.md` (repo root) | Persistent across sessions | The forward-looking backlog. Lists pending and in-progress waves. Updated regularly as work lands or priorities shift. The cross-session memory for what is left to do. |
| Session plan (path varies by tool — see your tool's adapter file) | One conversation | The detailed playbook for the wave currently being implemented. Created right before implementation by picking the next priorities from `backlog.md` and expanding them into concrete steps. Archived to `docs/history/` when the wave concludes — see *Plan history* below — where the tool supports it; otherwise discarded when the conversation ends. |
| `docs/history/` (repo root) | Persistent across sessions | The backward-looking record of concluded plans — completed, dropped, or superseded. The cross-session memory for what was already tried and why. See *Plan history* below. |

The session plan always derives from `backlog.md`. Never start implementing without it.

## Backlog maintenance

Every repository has a single **`backlog.md` at the repository root**, alongside the top-level `README.md`. It is a planning artifact, not documentation, which is why it lives at the root and not under `docs/`. Other planning-shaped top-level files (executive summaries, programme plans) live next to it for the same reason.

The backlog is strictly forward-looking:

- It lists **pending and in-progress waves only**.
- When a wave completes, its entire section is **removed**, not marked "done" or struck through. Anything still relevant from a completed wave belongs in `docs/` or `README.md` instead.
- Cross-references to completed waves in remaining sections are rewritten to drop the dependency language ("requires Wave X" becomes a plain statement of what is already true).
- The Next Up tier's ordering table is renumbered after every removal so step numbers are dense.

Read this way, the backlog always answers one question: *what is left to do?* `docs/history/` (below) answers the complementary question: *what was already tried, and why did it end up this way?*

**Write entries with enough detail to stand alone.** When a wave or topic is added — freshly from discussion, or promoted from another tier — capture the reasoning behind it in the entry itself: the motivation, constraints, and dependencies developed in conversation, not a compressed title. A `/compact` or a fresh session has only the backlog to reconstruct the idea from; anything that stayed in chat and never made it into the entry is gone. This applies even to a Next Up row — pair it with enough surrounding detail that the entry alone, with no conversation context, explains why it's worth doing and what shape it should take.

### Backlog tiers

`backlog.md` groups pending work into three tiers, ordered by descending certainty and immediacy:

- **Next Up** — ordered, will land soon (today/this week/this month). The processing-order table lives
  here, and only here.
- **Planned** — committed to eventually building, not yet sequenced. Grouped by topic via headings; no
  ordering implied between or within topics.
- **Later Considerations** — ideas, techniques, or features that may never be built. Kept so a good idea
  isn't lost; revisit when its stated trigger condition becomes true, not on a schedule.

Promoting an item between tiers (e.g. a Later Considerations idea becomes Planned once its trigger fires,
or a Planned item gets sequenced into Next Up) means moving its text to the new section and rewriting it
to fit that tier's tone — no note is left behind recording which tier it came from, per the rewrite-not-
append rule. An item is only ever planned (gets a session plan) after it reaches Next Up — nothing jumps
straight from Later Considerations into a wave.

Omit a tier's heading entirely when it has no items. Add topic sub-headings (`###`) within Planned and
Later Considerations once more than one distinct thread accumulates; Next Up stays a flat ordered table.

Optionally, add a `## Context for planning agents` table before the tiers — links to docs an agent should
read before expanding a backlog item into a session plan.

Add a `## Contents` section once scanning the file to find the right tier or topic takes real effort — no
fixed heading count triggers this, the same judgment call as everywhere else in this convention. Remove it
again if the backlog shrinks back down.

**Tier disclosure.** When asked about the backlog conversationally, surface only the tier the question's
horizon implies — don't dump the whole file by default:

| Question shape | Tiers to surface |
|---|---|
| "what's next", "what should we work on", "what's queued" | Next Up only |
| "what's in the backlog" (bare, no qualifier) | Next Up + Planned |
| "what's deferred", "later considerations", "any ideas for later" | Later Considerations only |
| "show me the whole backlog", or reading `backlog.md` directly | all three tiers, verbatim |

## Plan history

Every repository that uses waves keeps a `docs/history/` folder: a backward-looking record of concluded
plans, so an agent planning new work can check whether a direction was already tried and dropped for a
good reason, instead of re-discovering the same dead end.

- **`docs/history/index.md`** — one line per concluded plan: date, topic title, outcome
  (`completed` / `dropped` / `superseded`), and a link to the detail file. Small and cheap to read in full
  before planning.
- **`docs/history/YYYY-MM-DD-<slug>.md`** — one file per concluded plan: the session plan as it stood when
  it concluded, with a short header (date, title, outcome, and — if dropped — the reason).

Both are committed to git. This is project history for human readers too, not agent scratch state.

**Token efficiency**: read `index.md` first — it's one small file. Only open a specific detail file whose
title looks relevant to the current task; don't open every entry on the chance one might matter.

**Every wave** checks this history before planning (Plan phase). A completed wave adds to it during
Documentation update (see below). A plan that gets dropped instead of approved adds to it right there, in
the Plan phase, rather than waiting for a Documentation update phase that a dropped plan will never reach.
The exact mechanism (where the session plan file lives, how the archive step is triggered) is tool-specific;
see your tool's adapter file.

**Guardrail — history informs, it never narrates.** Reading `docs/history/` must never change what code or
docs *say*. The rewrite-not-append rule above already forbids narrating a file's evolution; that holds with
equal force now that a real history exists to narrate from. An agent may read that per-request caching was
rejected for a race condition, and use that *reason* to write a present-tense justification — "the cache is
shared across requests to avoid the race described in §X" — in the current docs. It must not write "we
first tried per-request caching, then switched to a shared cache." This is symmetric with the backlog:
future intent (the backlog) must not leak into code or docs as a roadmap unless explicitly asked for; past
intent (the history) must not leak in as a timeline either. A `CHANGELOG.md` entry is the one form that
tolerates more temporal language by convention (it's inherently "what changed in this version") — but it
still describes this release's change, not a replay of earlier rejected approaches.

## Documentation update phase

Every wave includes documentation upkeep. Not optional, not a follow-up task — part of the wave's definition of done. All rewrites follow the `doc-conventions` skill (terminology, glossary placement, markdown/mermaid rules, and the native rewrite check).

**Upkeep is scoped to what this wave made wrong.** It always covers:

- **README files** in every folder the wave touched, rewritten so they read as if the new shape was the original shape.
- **Individual claims in `docs/*.md`** that this wave falsified — the specific statements, not the documents around them. Never append "as of wave N…" paragraphs.
- **`backlog.md`** — remove the completed wave's section entirely. If the wave revealed something that conflicts with or changes the shape of other pending waves, also update *those* sections so the backlog stays accurate. If the right update is unclear or large, raise it in chat after the wave instead of guessing.
- **`docs/history/`** — archive this wave's session plan (see *Plan history* above) and append its line to
  `docs/history/index.md`. A dropped plan is archived earlier, in the Plan phase, not here — see *Plan
  history* for why.
- **`CHANGELOG.md`** if the wave ships a released package — one entry under the new version, written for future users of the package, not for me. Check `docs/history/index.md` for the plan(s) behind this release and ground the narrative paragraph in the documented intent rather than re-deriving it from the diff alone. Use this structure:

  ```markdown
  ## [x.y.z] - YYYY-MM-DD

  One or two sentences explaining the purpose of this release: what capability it adds or what problem it fixes, written for a user deciding whether to upgrade. Omit if the changes are fully described by the bullets below.

  ### Added
  - …

  ### Changed
  - …

  ### Fixed
  - …

  ### Removed
  - …

  ### To upgrade
  - …

  ### Recommended
  - …
  ```

  Omit sections that have no entries, except that a major release always has `### To upgrade`. Agents read these two sections when they upgrade a project, so write them for an agent working in that project's repo. `### To upgrade` lists the steps a project must take, each named by what can be found in a repo (the old field, file, command or pin, and what replaces it). `### Recommended` lists optional moves the release makes possible, which the agent raises with the user once. A nudge that belongs to one release goes there, never into an agent skill. The narrative paragraph is required when the version introduces a meaningful feature or a non-obvious breaking change; it is optional for patch releases that are purely bug fixes. Write the narrative from the user's perspective ("pods can now limit…"), not from the implementation's perspective ("added a `sample_rate` parameter to…").

**A wave never runs a full sweep of `docs/`** — re-deriving every document per wave is expensive, and while a planned sequence is still in progress it rewrites transitional descriptions into successively less wrong states instead of once, correctly, at the end. A sweep covers what upkeep does not: `docs/*.md` read as wholes rather than claim by claim, and `docs/glossary.md` in each affected scope — new terms added, retired ones removed, drifted definitions corrected.

**A sweep is its own wave**, a *sweep wave*: a backlog entry with a plan that names the scope (a path or the whole repo). It runs like any wave, with the sweep in place of Specify and Implement. Propose one when a sequence of waves in one area ends, or when the backlog names one.

No "Migration notes" sections in repo docs unless I explicitly ask. Backward-compat shims are not preserved, so migration notes describe nothing.

## Commit messages

For trivial single-purpose changes, a one-line imperative commit message is enough. For a wave or comparable landing, automatically propose a structured message at the end:

```
<short imperative one-line summary>

<one short paragraph: purpose, larger context, impact — whatever applies>

- <file or folder>: <what changed>
- <file or folder>: <what changed>
- …
```

Don't make lines longer than 95 characters. Bullets are grouped by file or folder, whichever keeps the message readable. Avoid one bullet per line of diff. No `Co-Authored-By` trailers. Inside a wave the wave agent writes and commits the message itself; outside a wave, propose it first and commit after confirmation.

## No new dependencies without flagging

Adding a third-party dependency is a decision, not a side effect of implementation. Flag the addition in chat with the reason and an alternatives note before installing it.

## Documentation update: choosing the mechanism

Three shapes, chosen by scope — not interchangeable, each exists for a specific reason:

- **Small, user-scoped edit** ("update the README to mention X") — the main agent does it inline,
  directly. No subagent: the edit is narrow enough that the current conversation's context is enough.
- **A wave's routine documentation upkeep** — inside the wave, scoped to what that wave changed.
- **A documentation sweep** — the bare phrase "update documentation" with no further scope, an explicit
  request for a sweep, or a sweep wave — the `doc-sweep` subagent, deliberately **fresh** (no inherited
  context), because it needs to re-derive doc-vs-code accuracy from scratch rather than trust what the
  conversation currently believes. Asked ad hoc it proposes its fixes first; in a sweep wave the approved
  plan is the confirmation.
