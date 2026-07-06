# Working Instructions

Shared conventions for all AI coding assistants. Tool-specific adapters (`CLAUDE.md`, `copilot_instructions.md`) extend this file with mechanics that differ per tool. Read this file first.

---

# Working Mode

- Default mode is **plan mode**: on cues like "let's plan X" or "let's discuss X," enter plan mode before touching code, configuration, or `.md` files, and stay in it for as long as the discussion continues — refining the plan, answering open questions, revising direction — regardless of how many turns that takes. Only exit on cues like "let's implement X" or an equivalent explicit go-ahead in the same conversation. Plan mode's own approval step ("keep planning with feedback" vs. approve and proceed) is the gate; no separate confirmation ritual is needed on top of it. For changes too small to warrant planning (a typo, an obvious one-line fix, a narrowly and explicitly specified instruction), skip plan mode and just make the change.
- Do not preserve backward compatibility unless I explicitly ask for it. **Exception — published packages** (`semantic_tracing`, `semantic_evaluation`): these are distributed via Artifactory and installed by external clients; follow SemVer within the major version. Patch and minor releases must be backward compatible drop-in replacements. Breaking changes require a major-version bump and a CHANGELOG entry. "Public API" means any symbol exported from `__init__.py` and documented in `docs/`. Clients should declare `>=x.y.z,<{next_major}` (e.g. `>=0.2.2,<1`) so they receive updates automatically but are protected from breaking changes.
- When changing code, comments, or documentation, **rewrite or remove** obsolete material instead of appending paragraphs that refer to earlier states. The final result should read as if it had been written this way from the start, not as an accumulation of edits.
- In chat, address me directly and may use first person. In any committed file (code comment, `.md`, commit message), write for a future repo reader who has no access to this conversation — no "as we discussed", no "per your request".
- Increase readability with tables, lists, and (in `.md` files only — not chat) mermaid diagrams. Keep prose concise. Build mermaid diagrams vertically; use swim lanes whenever an additional dimension improves separation.

## Native rewrite check

After any non-trivial edit to an existing `.md` file, re-read the whole file once and ask: "would a new reader notice this was patched in?" If yes — the surrounding paragraphs reference the old shape, the new section's tone differs, terms shift mid-document, headings break the rhythm — rewrite the surroundings until the answer is no.

---

# Clarifying Questions (Both Directions)

The same shape applies whether I am asking you for clarification, or you are asking me for guidance during planning, discussion, or while drafting `implementation_plan.md` or `/memories/session/plan.md`:

- Explain the broader context first: the goal, the design principles in play, what the choice influences.
- Define any term that could create different mental models.
- Spell out the implications of each option in light of the bigger picture, not just the local code.
- When more than two reasonable options exist, present them as a small table with columns *option / impact / reversibility* so the other side can choose at a glance.

A bare question without that scaffolding is rarely useful in either direction.

---

# Implementation Waves

Non-trivial work is organised into **waves**. A wave is one coherent slice of change that lands as a single completed objective (not a single commit). Sub-waves (`0.A`, `0.B`, …) split a wave when parts can land independently.

Every wave runs through fixed phases in order:

1. **Plan** — before any code change, write a detailed plan to `/memories/session/plan.md`. The plan names every file to touch, every verification step, and the wave's exit criteria. Track the current phase explicitly throughout the work — see your tool's adapter file for the mechanism.
2. **Implement** — code, config, fixtures, tests.
3. **Documentation update** — first-class part of the wave, not a follow-up. See *Documentation update phase* below.
4. **Verification** — run the test suites and any smoke commands listed in the plan. Distinguish failures caused by this wave from pre-existing failures, and call the pre-existing ones out by name when reporting.
5. **Commit message proposal** — for a larger landing (e.g. all of Wave 2, not just sub-wave 2.1) automatically draft a commit message at the end. See *Commit messages* below.

Mark a wave done only after verification passes.

## Plan files: cross-session vs session-scoped

| File | Lifetime | Purpose |
|---|---|---|
| `implementation_plan.md` (repo root) | Persistent across sessions | The forward-looking backlog. Lists pending and in-progress waves. Updated regularly as work lands or priorities shift. The cross-session memory for what is left to do. |
| `/memories/session/plan.md` | One conversation | The detailed playbook for the wave currently being implemented. Created right before implementation by picking the next priorities from `implementation_plan.md` and expanding them into concrete steps. Discarded when the conversation ends. |

`/memories/session/plan.md` always derives from `implementation_plan.md`. Never start implementing without it.

## Implementation plan maintenance

Every repository has a single **`implementation_plan.md` at the repository root**, alongside the top-level `README.md`. It is a planning artifact, not documentation, which is why it lives at the root and not under `docs/`. Other planning-shaped top-level files (executive summaries, programme plans) live next to it for the same reason.

The plan is strictly forward-looking:

- It lists **pending and in-progress waves only**.
- When a wave completes, its entire section is **removed**, not marked "done" or struck through. Anything still relevant from a completed wave belongs in `docs/` or `README.md` instead.
- Cross-references to completed waves in remaining sections are rewritten to drop the dependency language ("requires Wave X" becomes a plain statement of what is already true).
- The "suggested processing order" table is renumbered after every removal so step numbers are dense.

Read this way, the plan always answers one question: *what is left to do?*

## Documentation update phase

Every wave finishes with a documentation pass. Not optional, not a follow-up task — part of the wave's definition of done. All rewrites follow the `doc-conventions` skill (terminology, glossary placement, markdown/mermaid rules) and the native rewrite check above.

The pass covers:

- **README files** in every folder the wave touched, rewritten so they read as if the new shape was the original shape.
- **`docs/*.md`** files whose subject the wave changed, rewritten the same way. Never append "as of wave N…" paragraphs.
- **`docs/glossary.md`** in each affected scope — add new terms, remove retired ones, update definitions that drifted.
- **`implementation_plan.md`** — remove the completed wave's section entirely. If the wave revealed something that conflicts with or changes the shape of other pending waves, also update *those* sections so the backlog stays accurate. If the right update is unclear or large, raise it in chat after the wave instead of guessing.
- **`CHANGELOG.md`** if the wave ships a released package — one entry under the new version, written for future users of the package, not for me. Use this structure:

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

Saying **"update documentation"** without further scope invokes the `doc-sweep` subagent for a full
documentation consistency sweep, rather than touching only what a recent wave changed.
