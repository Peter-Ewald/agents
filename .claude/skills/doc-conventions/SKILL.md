---
name: doc-conventions
description: Documentation conventions for this user's repos — terminology, glossary placement, README structure, and markdown/mermaid rendering rules. Auto-loads whenever a markdown file is being read or edited.
paths: ["**/*.md"]
---

The rules in this skill apply to **every** `.md` and `README.md` edit — one-off changes, wave end-of-phase
doc updates, and on-demand doc sweeps all follow the same conventions.

## Rewrite, don't append

Docs are rewritten to read as if they were written this way from the start — never patched with appended
paragraphs that refer to an earlier state ("as of the recent change...", "previously this was..."). After
any non-trivial edit to an existing `.md` file, re-read the whole file once and ask: "would a new reader
notice this was patched in?" If yes — the surrounding paragraphs reference the old shape, the new
section's tone differs, terms shift mid-document, headings break the rhythm — rewrite the surroundings
until the answer is no.

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

## Mermaid diagrams

The syntax below is confirmed to work in VS Code with the "Markdown Preview Mermaid Support" extension
and is compatible with Azure DevOps Wiki rendering.

### Direction and layout

1. Default to `graph TD`. Switch to `graph LR` when the diagram is a wide branching flow: several parallel
   lanes that each hit a step or two and then converge. Top down turns that shape into a very tall, narrow
   column that no longer fits a slide or a page.
2. `direction LR` or `direction TB` as the first line inside a `subgraph` block controls how that
   subgraph's own children are laid out, independently of the diagram's direction. This is the reliable
   way to run one group across the page while the rest of the diagram runs top down.
3. Phantom links (`~~~`) reorder siblings, but the axis they stack on is not consistent between diagrams:
   the same `A ~~~ B ~~~ C` produced a horizontal row in one diagram and a vertical column in another.
   Reach for `direction` first, and use `~~~` only to fix the order of nodes that are already laid out on
   the axis you want. Phantom links render as invisible, so no edge is drawn.
4. Where two subgraphs sit next to each other, their order comes from declaration order and from the edges
   between their children, not from anything settable. The second subgraph declared often renders first.
   If the order is wrong, swap the declarations and re-render.
5. Keep an edge inside the subgraph that owns both of its endpoints. An edge crossing into a nested
   subgraph from outside pushes the layout apart, leaves a large empty gap, and can make the inner
   subgraph's border overflow the outer one. If a diagram needs that edge, move the outside node into the
   group or drop it and say it in prose instead.
6. Avoid naming a node the same as its subgraph.
7. Use `subgraph` for logical groupings (e.g., Frontend, Backend, AzureFluidRelay).

### Labels

8. Wrap every plain node label in double quotes inside square brackets: `["Label text"]`.
9. **Every subgraph title is bold**, written as a markdown string with backticks inside the quotes:

   ```
   subgraph Content["`**Instruction and knowledge**`"]
   ```

   The backticks route the label through mermaid's markdown renderer, so `**…**` renders bold and the
   title box is still measured correctly. Leaf node labels and edge labels stay plain. Bold is what marks
   a box that contains other boxes, so it reads as the heading of that group.
10. **Never set `font-size` in a `style` directive.** Mermaid measures the title and sizes the box before
    that CSS is applied, so an enlarged title overflows and its last words are cut off. The narrower the
    box, the worse it is. Bold through a markdown string is measured during layout and therefore fits, so
    bold is the only size cue available: there is no reliable way to enlarge label text.
11. Do not use parentheses `()` or special characters in node labels.
12. Do not use quotes (`"`) inside edge labels.
13. Use plain ASCII hyphens (e.g., `real time`, not `real‑time` or `real-time`) in edge labels.
14. Keep node labels short, a few words or a function signature. Long titles on two adjacent subgraphs
    overlap each other's text. Use surrounding prose for explanation rather than long sentences inside
    boxes.

### Colour

15. Always add an explicit `style` directive for every subgraph (`fill`, `stroke`, `stroke-width:2px`).
    Without it, subgraph borders are invisible in dark mode. Place all `style` lines at the bottom of
    the diagram block, after all edges.
16. Use color to signal identity, not decoration. Before picking colors, identify which concepts must
    be tracked across multiple diagrams in the same document, assign a distinct color to each of
    those, and use neutral gray (`stroke:#888888`) for any grouping that is just a container with no
    special tracked meaning. The same concept always gets the same color within a document; colors do
    not carry between documents. Pick 3 to 5 mid-luminance colors (e.g. `#5588cc`, `#55aa77`, `#cc8844`,
    `#9966cc`) for tracked concepts, saturated enough to distinguish, not so bright they dominate.
    If the repository has its own corporate/brand color palette (a `color_guidelines.md`, brand
    style guide, or similar source of truth), pick from that palette instead of the generic example
    colors above: use each brand color's own light tint for `fill` and its full-strength value for
    `stroke`. In that case the same role-to-color mapping should carry across every diagram in the
    repository (not just within one document), since a brand palette is a small, deliberately reused
    set of colors rather than an arbitrary per-document choice.

### Verify before shipping

17. A diagram that parses can still be unreadable. Render it before calling it done, for example with
    `npx @mermaid-js/mermaid-cli -i diagram.mmd -o diagram.png`, and look at the result for clipped
    titles, overlapping boxes and large empty gaps. These are layout faults that no amount of reading the
    source will reveal.

## Style and Tone

- don't use "-" or "—" characters generally. In headings use alternatives, for example ":". In paragraphs, build shorter sentences instead of using dashes, or use commas, colons, or semicolons to separate clauses instead.
