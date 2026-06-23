# Working Instructions

Shared conventions for all AI coding assistants. Tool-specific adapters (`CLAUDE.md`, `copilot_instructions.md`) extend this file with mechanics that differ per tool. Read this file first.

---

# Working Mode

- Default mode is **discuss first**: don't change code, configuration, or `.md` files until I say "update code / commentary / documentation" (or an obvious equivalent in the same conversation). However, if I imply in our conversation that you can update what we agreed on directly, do so.
- Do not preserve backward compatibility unless I explicitly ask for it.
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

# Documentation

The rules in this section apply to **every** `.md` and `README.md` edit — one-off changes, wave end-of-phase doc updates, and on-demand doc sweeps all follow the same conventions.

## Folder READMEs

Every meaningful folder (per repository, service, app, package, …) has a `README.md`. It explains the folder's purpose and how it fits the bigger picture. It is tailored for human readers and is an overview of the more detailed technical docs in the folder's `docs/` directory (which are tailored for and maintained by implementation agents).

## Terminology and definitions

- Prefer simple, explicit language over shorthand, agent jargon, or architecture slogans.
- Treat not only technical terms but also repository-specific wording, overloaded everyday words, and process labels as terms that may require explanation.
- If a term could reasonably create different mental models for different readers, do one of these:
	- replace it with a clearer phrase,
	- explain it at the first important use in simpler language and with enough surrounding context,
	- or link to its source-of-truth definition.
- Definitions may be a little longer than a terse label. Prefer short explanations that describe what the term means in this repository, why it matters, and what it does not mean.
- Before introducing or reusing a term, actually search the codebase and documentation for existing usage and existing definitions.
- When a term already has a source-of-truth definition elsewhere, reuse the same wording and link to that definition instead of creating a competing explanation.
- If a term still feels vague after naming it, rewrite the sentence to describe the actual responsibility, action, boundary, or flow instead of relying on the label alone.

## Glossary placement and linking

- Every `docs/` folder should contain a `glossary.md`.
- Use `glossary.md` as the default place to define terms that belong to that documentation scope.
- Repository-wide terms belong in the repository-level `docs/glossary.md`.
- Package-local or service-local terms belong in that package or service `docs/glossary.md`.
- If a local document uses a term defined in another scope, link to that source-of-truth definition instead of redefining it differently.
- Prefer relative Markdown links so links work in the editor, in preview, and after repository moves.
- When linking to a definition in another file, prefer linking directly to the heading anchor for that term.

## READMEs and local explanations

- README files should remain readable for humans unfamiliar with the current implementation vocabulary.
- Inline explanations and inline definition boxes between paragraphs are completely fine when they improve comprehension at the point where the term first matters.
- If a page depends on only one or two non-obvious terms, explain them briefly inline on the page and link to the source-of-truth glossary entry.
- If a page uses many non-obvious terms, still prefer short inline explanations at the points where they matter most instead of pushing all explanations into a separate section far away from the relevant paragraph.
- Use a direct glossary link when the reader can keep going without stopping, the term is secondary on that page, the sentence is already understandable without the definition, or the same term appears many times and one consistent glossary target is enough.
- Use a local inline definition box when the term is central to understanding the page, the term is easy to misread, the page's main purpose depends on that term, or the sentence becomes vague or slogan-like without an explanation.
- Avoid scattering slightly different restatements of the same definition across multiple files.

Recommended inline definition box pattern:

```md
> **Definition: release-facing scoring**
> Scoring used to support release or promotion decisions for evaluated workflow changes.
> In this repository, it refers to the shared scoring path implemented in `scoring_app/`,
> not ad hoc local scoring used for experiments.
> See [release-facing scoring](glossary.md#release-facing-scoring).
```

## Markdown preview compatibility

- Write Markdown that renders acceptably in VS Code built-in Markdown preview.
- Do not assume GitHub-specific callout syntax is supported by the local preview renderer.
- If visual callout boxes are required, use only syntax and extensions that are confirmed to work in the repository's agreed VS Code setup.
- For mermaid diagrams, the following syntax is confirmed to work in VS Code with the "Markdown Preview Mermaid Support" extension and is fully compatible with Azure DevOps Wiki rendering:
	1. Use `graph TD` (top-down direction).
	2. Wrap all node labels in double quotes inside square brackets: `["Label text"]`.
	3. Do not use parentheses `()` or special characters in node labels.
	4. Do not use quotes (`"`) inside edge labels.
	5. Use plain ASCII hyphens (e.g., `real time`, not `real‑time` or `real-time`) in edge labels.
	6. Avoid naming a node the same as its subgraph.
	7. Use `subgraph` for logical groupings (e.g., Frontend, Backend, AzureFluidRelay).
	8. To control node stacking within a subgraph, use phantom links (`~~~`) between nodes rather than a `direction` directive inside the subgraph — the inner `direction` directive is unreliable across renderer versions. In a `flowchart LR` diagram, phantom links between nodes within a subgraph force vertical stacking; in a `flowchart TD` diagram, they force horizontal stacking. Example: `A ~~~ B ~~~ C` stacks A, B, C vertically inside a `flowchart LR` subgraph. Phantom links affect layout but render as invisible — no edge is drawn.
	9. Always add an explicit `style` directive for every subgraph (`fill`, `stroke`, `stroke-width:2px`). Without it, subgraph borders are invisible in dark mode. Place all `style` lines at the bottom of the diagram block, after all edges.
	10. Use color to signal identity, not decoration. Before picking colors, identify which concepts must be tracked across multiple diagrams in the same document — assign a distinct color to each of those, and use neutral gray (`stroke:#888888`) for any grouping that is just a container with no special tracked meaning. The same concept always gets the same color within a document; colors do not carry between documents. Pick 3–5 mid-luminance colors (e.g. `#5588cc`, `#55aa77`, `#cc8844`, `#9966cc`) for tracked concepts — saturated enough to distinguish, not so bright they dominate.
	11. Keep node labels short — a few words or a function signature. Use surrounding prose for explanation rather than long sentences inside boxes.

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

Every wave finishes with a documentation pass. Not optional, not a follow-up task — part of the wave's definition of done. All rewrites follow the conventions in *# Documentation* above (terminology, glossary placement, native rewrite check, etc.).

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

---

# Documentation Sweeps

When I say **"update documentation"** without further scope, treat it as a **documentation consistency sweep**. The output of the sweep follows the rules in *# Documentation* above; the sweep itself is the discovery process.

1. Re-read every `README.md` and every `docs/**/*.md` in the touched scope, plus `implementation_plan.md` at the repo root.
2. Check for:
   - stale references to removed code, files, or commands,
   - terms used without being defined or linked to their glossary entry,
   - duplicate or competing definitions of the same term,
   - inconsistent naming across files (same concept, different label),
   - completed waves still mentioned in `implementation_plan.md`,
   - file links that no longer resolve,
   - mermaid diagrams that violate the rendering rules above.
3. **Also cross-check docs against the actual implementation.** Reading the source as part of the sweep is expected. If, while reading code that the recent changes did not touch, something is described inaccurately or not at all in the docs in scope, fix that too. The sweep is about doc–code consistency overall, not only about the diff from the last wave.
4. Propose the fixes as a plan first. Apply them only after I confirm.

A sweep never adds new content for its own sake. It rewrites, removes, or relocates existing content, or fills in gaps where the docs lie about the code.
