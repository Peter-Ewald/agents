---
name: design-conventions
description: Design and architecture principles for this user's repos — naming, module boundaries,
  error-handling philosophy, interface discipline. Use when designing a new feature, choosing between
  architectural approaches, or reviewing a proposed design for principle fit. Complements
  doc-conventions (documentation quality) and ruff-cleanup's RULES.md (lint-fix quality) — this is the
  code-design equivalent.
---

These principles apply on top of whatever Claude Code's own baseline instructions already cover — they
don't repeat "avoid unnecessary abstraction" or "search for reuse first," which are already stated
elsewhere. Each entry here is something this user has found worth stating explicitly, not a restatement
of general best practice.

## Naming clarity

A name should describe responsibility, not just label it. If a term still feels vague after naming it,
rewrite it to describe the actual boundary, action, or flow instead of relying on the label alone —
`process()` and `handle()` are labels; `reconcile_pending_orders()` is a responsibility.

## Boundary and ownership clarity

New logic goes where its responsibility already lives. Before adding a new module or file, check whether
an existing one already owns this concern — a new file should exist because a genuinely new
responsibility exists, not because splitting felt tidy.

## Fail loud, not silent

When a failure is handled, it's surfaced — logged, re-raised, or reported — never swallowed into a bare
`pass` or a `|| true`-style silence that hides the next real bug. A caught exception that does nothing
is indistinguishable from a bug nobody noticed yet.

## Consistency over cleverness

Match the codebase's existing pattern for a given kind of problem unless that pattern is demonstrably
wrong. A novel approach needs a stated reason — "this pattern doesn't handle X" — not just a preference
for a different style.

## Interfaces expose the minimum contract

A function, class, or API surface should commit to no more than callers actually need. Don't leak
internal representation through a public signature — a caller that depends on incidental structure turns
every future refactor into a breaking change.
