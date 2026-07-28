---
name: langfuse-upgrade
argument-hint: [langfuse-version]
description: Investigates a new langfuse (Python SDK) release against semantic_tracing and
  semantic_evaluation, proposes what needs to change (code, docs, dependency pins, package
  versions), and — once agreed — applies it and drafts the changelog/commit. Use when the
  user pastes a langfuse changelog/release notes, mentions a new langfuse version, or asks
  to check/upgrade the langfuse dependency.
---

Task Force Evaluation's two published packages both depend on `langfuse` (the Python SDK):
`semantic_tracing` declares it directly, `semantic_evaluation` currently only gets it transitively (a
separate, already-logged gap — see its own backlog entry; fix it here too if still open when this runs).
`langfuse` ships breaking changes inside otherwise-normal minor releases surprisingly often (removed REST
client methods being the recurring pattern so far), and both SDKs wrap it directly (`langfuse.api.*`,
`Langfuse(...)`, span/observation helpers) — so a new release is worth checking deliberately, not just
bumping the version constraint and hoping.

## 1. Determine the target version

From `$ARGUMENTS` if given. Otherwise, a langfuse changelog or release notes pasted in the same message
is the target — read the version number out of it directly rather than re-fetching. If neither is
present, ask which version to investigate.

## 2. Investigate in an isolated fork + worktree

Fork yourself (`Agent` tool, `subagent_type: "fork"`, `isolation: "worktree"`) rather than investigating
inline — this needs to bump a dependency and run installs/tests, which should never touch the actual
working directory or its uncommitted changes. The fork inherits full session context, so it does not need
the repo's structure re-explained.

Task the fork to, inside its isolated worktree:

- Fetch the actual langfuse changelog/release notes for the target version (the pasted content if given
  one, otherwise the `langfuse-python` GitHub repo's release notes/`CHANGELOG.md` for that version) —
  read the real diff, not a summary of it. Watch specifically for removed/renamed methods and deprecation
  warnings (the `langfuse-cli`'s own `--help` output flags some of these directly, a fast cross-check).
- In `sdk/semantic_tracing/` and `sdk/semantic_evaluation/`: temporarily pin `langfuse` to the target
  version (`uv add langfuse==<version>` or edit `pyproject.toml` directly), `uv sync`, and run each
  package's test suite.
- Grep both packages for every langfuse surface actually used (`self.langfuse.api.*`, `Langfuse(`,
  `@observe`, span/observation helpers, anything else the changelog's changes touch) — the concrete usage
  inventory to cross-reference against what changed.
- For every test failure or usage site touched by a changelog item: what broke, why, and a proposed fix.
- For each affected package independently, classify the fix per `instructions.md`'s published-package
  SemVer policy: if the fix stays internal (callers unaffected) it's a patch; if it forces a change to
  that package's own public API/callers, it's a major bump. Propose the new `langfuse` dependency range
  for that package's `pyproject.toml` (matching what was actually tested, per `instructions.md`'s Working
  Mode) and the resulting next version number for the package itself.
- Note any doc pages (`docs/*.md`) whose described behavior the changelog affects.

Return a structured findings summary: per affected package, the proposed code diffs (described, not yet
applied), the dependency range change, the version-bump classification and resulting next version, and
any doc updates needed. The worktree is investigation-only — nothing here is applied for real yet.

## 3. Present the plan and get agreement

Summarize the fork's findings in chat — per `instructions.md`'s "Clarifying Questions" shape: what
changed upstream, what it means for each package, the versioning consequence, and what's proposed for
code/docs/dependencies. Do not apply anything yet. This mirrors a wave's Plan-phase gate: only proceed
once the user explicitly agrees, and only for the packages/changes they agree to — partial agreement
(e.g. fix `semantic_tracing` now, defer `semantic_evaluation`) is fine, apply just that subset.

## 4. Apply for real

In the actual working directory (not the worktree, which was investigation-only and can now be
discarded): make the agreed code changes, update the `langfuse` dependency range in the affected
package(s)' `pyproject.toml`, and update the doc pages identified above (per the `doc-conventions` skill —
invoke it fresh rather than working from memory, per `CLAUDE.md`'s "Skill freshness" note, since this is
exactly the kind of edit it governs). Run the test suite again in the real checkout to confirm.

## 5. Changelog and commit

For each affected package, add a `## [<version>]` entry to its `CHANGELOG.md` under the version number
agreed in step 3, following `instructions.md`'s Documentation update phase CHANGELOG format — this is the
entry `sdk-release` will look for later, so get the version number right here rather than leaving it
open. Draft the commit message per `instructions.md`'s "Commit messages" section and wait for explicit
confirmation before committing, same as any other landing.

Do not bump the version number in `pyproject.toml`'s `version = "..."` field or publish anything here —
that stays `sdk-release`'s job, which already expects the `CHANGELOG.md` entry this step just wrote.
Point the user at `sdk-release <package> <version>` once they're ready to actually release.
