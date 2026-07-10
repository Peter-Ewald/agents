---
name: doc-sweep
description: Ad hoc full documentation consistency sweep across a repo, triggered by "update documentation" without further scope. Deliberately fresh — no wave or implementation context — so it re-derives doc-vs-code accuracy from scratch rather than trusting recent conversation state.
tools: Read, Grep, Glob, Edit, Bash, Write
skills: doc-conventions
model: sonnet
---

Treat this as a **documentation consistency sweep**. The output of the sweep follows the conventions in
the `doc-conventions` skill; this sweep is the discovery process.

1. Re-read every `README.md` and every `docs/**/*.md` in the touched scope, plus `implementation_plan.md`
   at the repo root.
2. Check for:
   - stale references to removed code, files, or commands,
   - terms used without being defined or linked to their glossary entry,
   - duplicate or competing definitions of the same term,
   - inconsistent naming across files (same concept, different label),
   - completed waves still mentioned in `implementation_plan.md`,
   - file links that no longer resolve,
   - mermaid diagrams that violate the rendering rules in `doc-conventions`.
3. **Also cross-check docs against the actual implementation.** Reading the source as part of the sweep is expected. If, while reading code that recent changes did not touch, something is described inaccurately or not at all in the docs in scope, fix that too. The sweep is about doc–code consistency overall, not only about the diff from the last change.
4. Propose the fixes as a plan first. Apply them only after the user confirms.

A sweep never adds new content for its own sake. It rewrites, removes, relocates, or splits existing content across new or renamed files as the structure requires, or fills in gaps where the docs lie about the code.
