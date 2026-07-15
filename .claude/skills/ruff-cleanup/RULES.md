# ruff-cleanup rules

One entry per ruff code this project has actually hit — not a copy of ruff's own rule catalogue. Grows
only by confirmed human guidance (see `SKILL.md` step 3), never bulk-authored speculatively ahead of a
real case.

## F401 — unused import

**Ruff fix:** safe — already handled by the `ruff-autofix` hook in the common case. Reaching this skill
usually means the special case: an import kept for re-export (e.g. in `__init__.py`) that ruff still
flags because nothing in that file appears to use it.

**Default fix:** add the name to that module's `__all__` instead of removing the import. If `__all__`
doesn't exist yet, don't invent one from scratch — flag it for a human call on the module's public
surface first.

**Do not:** blanket `# noqa` — always scope to `# noqa: F401` if a suppression is genuinely needed.

## F841 — unused variable

**Ruff fix:** unsafe (`--fix --unsafe-fixes --select F841`) when the assignment is truly dead.

**Default fix:** if the value is never read, delete the assignment (and any computation that fed only
it). If it exists purely for readability while debugging or documenting an intermediate step, rename
with a leading underscore (`_debug_value = ...`) instead of deleting.

## E501 — line too long

**Ruff fix:** none — `ruff check` has no autofix for this; `ruff format` occasionally shortens a line
as a side effect but isn't reliable for it.

**Default fix:** reflow at a natural operator/argument boundary; check the repo's `pyproject.toml`
`[tool.ruff]` `line-length` for its configured limit (else ruff's default of 88).

**Do not:** suppress inline unless the line is a URL or a string literal that must not be wrapped (e.g.
a regex) — then `# noqa: E501` with a one-line reason.

## B006 — mutable default argument

**Ruff fix:** none.

**Default fix:** replace `def f(x=[])` with `def f(x=None)` and initialize inside the body:
`x = x if x is not None else []`. Never share one mutable object across calls.
