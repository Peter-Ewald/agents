---
name: ruff-cleanup
argument-hint: [scope]
description: Cleans up ruff violations that survived the safe-autofix hook — ones needing
  an unsafe fix or actual code judgment, no automatic fix available. Consults RULES.md for
  this codebase's house guidance per ruff code, applies it, confirms clean, then runs the
  repo's test suite. Use when the user says "clean up remaining ruff issues", "ruff
  cleanup before this PR", or similar.
---

Run inline — do not fork. This needs the main conversation's awareness of why recent edits were made,
the same reason `wave`'s Implement phase stays inline rather than forking.

## 1. Determine scope

Default: **PR-diff** — files changed on the current branch vs. the base branch
(`git diff --name-only <base>...HEAD -- '*.py'`). Only use whole-repo scope (`**/*.py`) if `$ARGUMENTS`
or the conversation explicitly asks for it — a bare invocation always means PR-diff. This matches
"minimal changes" — a PR about one thing shouldn't also carry unrelated pre-existing fixes from files
it never touched.

## 2. Enumerate violations

Run `uvx ruff check --output-format=json` over the resolved scope. Everything reported here already
survived `ruff-autofix.py`'s safe fixes on every edit along the way — by definition these need either
an unsafe fix or actual code judgment.

## 3. Apply guidance per code

For each distinct code found, look it up in `RULES.md`:

- **Entry exists** — apply its "Default fix" exactly. If the entry says the fix is "ruff's own unsafe
  fix for this rule," run `uvx ruff check --fix --unsafe-fixes --select <CODE> <scope>` scoped to that
  one code only — never a blanket `--unsafe-fixes` across every code found.
- **No entry** — stop for that code. Do not improvise a fix. Draft a proposed guidance entry in the
  same format as the existing ones and present it to the user. Only after it's confirmed, append it to
  `RULES.md` verbatim as agreed, then apply it. This is the same pattern by which S_Factory's
  break-agent checklist grew — a small fixed procedure enriched one confirmed real case at a time,
  never bulk-authored guesses.

## 4. Confirm clean, bounded retry

Re-run `uvx ruff check` over the scope. If violations remain, retry step 3 at most **twice more**
(three attempts total), then stop and report the remainder to the user — this harness is
interactive/human-reviewed at every step, not an autonomous pipeline, so a short bounded retry is
enough. Don't loop indefinitely, and don't start guessing at fixes for codes not in `RULES.md`.

## 5. Run tests

Per `wave/SKILL.md`'s Verification phase: detect the repo's own test command (don't hardcode one —
look for `pytest`, `npm test`, a `Makefile` target, etc.) and run it. Report pre-existing failures
separately from anything this cleanup introduced.

## 6. Report

Summarize: codes fixed and by what rule, any new `RULES.md` entries added this run, and the test
result. No automatic commit — that stays a separate, explicit step per the normal commit-proposal flow.
