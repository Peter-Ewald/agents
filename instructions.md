# Working Instructions

Shared conventions for all AI coding assistants. Tool-specific adapters (`CLAUDE.md`, `copilot_instructions.md`) extend this file with mechanics that differ per tool. Read this file first.

---

# Working Mode

- Default mode is **plan mode**: on cues like "let's plan X" or "let's discuss X," enter plan mode before touching code, configuration, or `.md` files, and stay in it for as long as the discussion continues — refining the plan, answering open questions, revising direction — regardless of how many turns that takes. Only exit on cues like "let's implement X" or an equivalent explicit go-ahead in the same conversation. Plan mode's own approval step ("keep planning with feedback" vs. approve and proceed) is the gate; no separate confirmation ritual is needed on top of it. For changes too small to warrant planning (a typo, an obvious one-line fix, a narrowly and explicitly specified instruction), skip plan mode and just make the change.
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

# Implementation Waves

Non-trivial work is organised into **waves**. A wave is one coherent slice of change that lands as a single completed objective (not a single commit). Sub-waves (`0.A`, `0.B`, …) split a wave when parts can land independently.

Every wave runs through fixed phases in order:

1. **Plan** — before any code change, write a detailed plan to the session plan (see your tool's adapter file for exactly where this lives). The plan names every file to touch, every verification step, and the wave's exit criteria. Before finalizing the approach, invoke the `design-conventions` skill fresh (see your tool's adapter file's "Skill freshness" note) and check the plan against it. Track the current phase explicitly throughout the work — see your tool's adapter file for the mechanism.
2. **Implement** — code, config, fixtures, tests.
3. **Documentation update** — first-class part of the wave, not a follow-up. See *Documentation update phase* below.
4. **Verification** — run the test suites and any smoke commands listed in the plan. Distinguish failures caused by this wave from pre-existing failures, and call the pre-existing ones out by name when reporting.
5. **Commit message proposal** — for a larger landing (e.g. all of Wave 2, not just sub-wave 2.1) automatically draft a commit message at the end. See *Commit messages* below.

Mark a wave done only after verification passes.

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

Every wave finishes with a documentation pass. Not optional, not a follow-up task — part of the wave's definition of done. All rewrites follow the `doc-conventions` skill (terminology, glossary placement, markdown/mermaid rules, and the native rewrite check).

The pass covers:

- **README files** in every folder the wave touched, rewritten so they read as if the new shape was the original shape.
- **`docs/*.md`** files whose subject the wave changed, rewritten the same way. Never append "as of wave N…" paragraphs.
- **`docs/glossary.md`** in each affected scope — add new terms, remove retired ones, update definitions that drifted.
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
  ```

  Omit sections that have no entries. The narrative paragraph is required when the version introduces a meaningful feature or a non-obvious breaking change; it is optional for patch releases that are purely bug fixes. Write the narrative from the user's perspective ("pods can now limit…"), not from the implementation's perspective ("added a `sample_rate` parameter to…").

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

Don't make lines longer than 95 characters. Bullets are grouped by file or folder, whichever keeps the message readable. Avoid one bullet per line of diff. No `Co-Authored-By` trailers. Propose the commit message text before it is committed, and only proceed after confirmation — see your tool's adapter file for the exact mechanism.

## No new dependencies without flagging

Adding a third-party dependency is a decision, not a side effect of implementation. Flag the addition in chat with the reason and an alternatives note before installing it.

## Documentation update: choosing the mechanism

Three shapes, chosen by scope — not interchangeable, each exists for a specific reason:

- **Small, user-scoped edit** ("update the README to mention X") — the main agent does it inline,
  directly. No subagent: the edit is narrow enough that the current conversation's context is enough,
  and forking or a fresh read would only add overhead.
- **A wave's own Documentation update phase** — a **forked** agent (inherits the full conversation, so
  it knows exactly what the wave just built) — see the `wave` skill's Phase 3.
- **A full consistency sweep** — the bare phrase "update documentation" with no further scope, or an
  explicit request for a full sweep — invokes the `doc-sweep` subagent, deliberately **fresh** (no
  inherited context), because it needs to re-derive doc-vs-code accuracy from scratch rather than trust
  what the conversation currently believes.
