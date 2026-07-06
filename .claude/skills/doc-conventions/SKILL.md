---
name: doc-conventions
description: Documentation conventions for this user's repos — terminology, glossary placement, README structure, and markdown/mermaid rendering rules. Auto-loads whenever a markdown file is being read or edited.
paths: ["**/*.md"]
---

The rules in this skill apply to **every** `.md` and `README.md` edit — one-off changes, wave end-of-phase
doc updates, and on-demand doc sweeps all follow the same conventions.

## Folder READMEs

Every meaningful folder (per repository, service, app, package, …) has a `README.md`. It explains the
folder's purpose and how it fits the bigger picture. It is tailored for human readers and is an overview
of the more detailed technical docs in the folder's `docs/` directory (which are tailored for and
maintained by implementation agents).

## Terminology and definitions

- Prefer simple, explicit language over shorthand, agent jargon, or architecture slogans.
- Treat not only technical terms but also repository-specific wording, overloaded everyday words, and
  process labels as terms that may require explanation.
- If a term could reasonably create different mental models for different readers, do one of these:
	- replace it with a clearer phrase,
	- explain it at the first important use in simpler language and with enough surrounding context,
	- or link to its source-of-truth definition.
- Definitions may be a little longer than a terse label. Prefer short explanations that describe what the
  term means in this repository, why it matters, and what it does not mean.
- Before introducing or reusing a term, actually search the codebase and documentation for existing usage
  and existing definitions.
- When a term already has a source-of-truth definition elsewhere, reuse the same wording and link to that
  definition instead of creating a competing explanation.
- If a term still feels vague after naming it, rewrite the sentence to describe the actual responsibility,
  action, boundary, or flow instead of relying on the label alone.

## Glossary placement and linking

- Every `docs/` folder should contain a `glossary.md`.
- Use `glossary.md` as the default place to define terms that belong to that documentation scope.
- Repository-wide terms belong in the repository-level `docs/glossary.md`.
- Package-local or service-local terms belong in that package or service `docs/glossary.md`.
- If a local document uses a term defined in another scope, link to that source-of-truth definition
  instead of redefining it differently.
- Prefer relative Markdown links so links work in the editor, in preview, and after repository moves.
- When linking to a definition in another file, prefer linking directly to the heading anchor for that
  term.

## READMEs and local explanations

- README files should remain readable for humans unfamiliar with the current implementation vocabulary.
- Inline explanations and inline definition boxes between paragraphs are completely fine when they improve
  comprehension at the point where the term first matters.
- If a page depends on only one or two non-obvious terms, explain them briefly inline on the page and link
  to the source-of-truth glossary entry.
- If a page uses many non-obvious terms, still prefer short inline explanations at the points where they
  matter most instead of pushing all explanations into a separate section far away from the relevant
  paragraph.
- Use a direct glossary link when the reader can keep going without stopping, the term is secondary on
  that page, the sentence is already understandable without the definition, or the same term appears many
  times and one consistent glossary target is enough.
- Use a local inline definition box when the term is central to understanding the page, the term is easy
  to misread, the page's main purpose depends on that term, or the sentence becomes vague or slogan-like
  without an explanation.
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
- If visual callout boxes are required, use only syntax and extensions that are confirmed to work in the
  repository's agreed VS Code setup.
- For mermaid diagrams, the following syntax is confirmed to work in VS Code with the "Markdown Preview
  Mermaid Support" extension and is fully compatible with Azure DevOps Wiki rendering:
	1. Use `graph TD` (top-down direction).
	2. Wrap all node labels in double quotes inside square brackets: `["Label text"]`.
	3. Do not use parentheses `()` or special characters in node labels.
	4. Do not use quotes (`"`) inside edge labels.
	5. Use plain ASCII hyphens (e.g., `real time`, not `real‑time` or `real-time`) in edge labels.
	6. Avoid naming a node the same as its subgraph.
	7. Use `subgraph` for logical groupings (e.g., Frontend, Backend, AzureFluidRelay).
	8. To control node stacking within a subgraph, use phantom links (`~~~`) between nodes rather than a
	   `direction` directive inside the subgraph — the inner `direction` directive is unreliable across
	   renderer versions. In a `flowchart LR` diagram, phantom links between nodes within a subgraph force
	   vertical stacking; in a `flowchart TD` diagram, they force horizontal stacking. Example:
	   `A ~~~ B ~~~ C` stacks A, B, C vertically inside a `flowchart LR` subgraph. Phantom links affect
	   layout but render as invisible — no edge is drawn.
	9. Always add an explicit `style` directive for every subgraph (`fill`, `stroke`, `stroke-width:2px`).
	   Without it, subgraph borders are invisible in dark mode. Place all `style` lines at the bottom of
	   the diagram block, after all edges.
	10. Use color to signal identity, not decoration. Before picking colors, identify which concepts must
	    be tracked across multiple diagrams in the same document — assign a distinct color to each of
	    those, and use neutral gray (`stroke:#888888`) for any grouping that is just a container with no
	    special tracked meaning. The same concept always gets the same color within a document; colors do
	    not carry between documents. Pick 3–5 mid-luminance colors (e.g. `#5588cc`, `#55aa77`, `#cc8844`,
	    `#9966cc`) for tracked concepts — saturated enough to distinguish, not so bright they dominate.
	11. Keep node labels short — a few words or a function signature. Use surrounding prose for
	    explanation rather than long sentences inside boxes.
