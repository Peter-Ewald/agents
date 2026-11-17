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

## ISC004 — implicit string concatenation inside a collection

**Ruff fix:** unsafe (`--fix --unsafe-fixes --select ISC004`): wraps the joined literals in parentheses.

**Default fix:** take ruff's fix when the joining is intended, the usual case for a long string split
over lines in a list. If the two literals were meant to be separate items, a comma is missing: that is a
bug, so stop and flag it rather than fixing it either way.

**Do not:** add a comma to silence the rule: it turns one string into two items.

## RUF059 — unpacked variable never used

**Ruff fix:** unsafe (`--fix --unsafe-fixes --select RUF059`): prefixes the name with an underscore.

**Default fix:** take ruff's fix (`status, _body = ...`). Ruff only fixes a name that is not bound again
later in the same scope, and reports a reused name only at its last binding, so each rename can uncover
the previous one. Rename every unused binding of that name in the scope in one pass rather than one per
re-run.

## RUF007 — `zip(x, x[1:])` for successive pairs

**Ruff fix:** unsafe (`--fix --unsafe-fixes --select RUF007`): rewrites to `itertools.pairwise(x)`.

**Default fix:** take ruff's fix, then let the safe `I001` fix sort the added `import itertools`.

## F541 — f-string without placeholders

**Ruff fix:** safe: drops the `f` prefix.

**Default fix:** take ruff's fix. If a placeholder was clearly meant to be there, add it instead and say
so in the report.
