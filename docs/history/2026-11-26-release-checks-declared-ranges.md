---
date: 2026-11-26
title: An SDK release checks the projects' declared version ranges
outcome: completed
---

# Wave 09 (agents): An SDK release checks the projects' declared version ranges

## Summary

| | |
|---|---|
| **Goal** | An SDK release stops before relocking or publishing when a project that installs the package editable declares a range that excludes the new version, naming every such project and its range, so the range is raised in the same release. Serves the backlog entry *An SDK release checks the projects' declared version ranges* (Next Up, step 4). |
| **Kind** | Implementation (harness: the `sdk-release` skill's scripts). |
| **Changes** | `sdk-release`: a new range-check script and a first pass in `relock-editable.sh` that runs it for every editable installer before any `uv lock`; the skill text. Docs: `docs/02-skills-and-subagents.md` § `sdk-release`. |
| **Behaviour** | A range that admits the new version, or no range, lets the release go on as today. A range that excludes it, through `<`, `<=`, `==` or `!=`, stops the release with no lock file changed, naming each project, its range and the version. A range the check cannot read (`~=`, wildcards, pre-releases) also stops it, saying so. A range in an optional dependency or a dependency group counts too. A project that installs the package from the index is not checked. |
| **Decisions** | D1 hand-written, strict parser (your choice); D2 check every editable installer before relocking any; D3 stop and name, never raise the range automatically; D4 a pre-release version stops the check. |
| **Risks and holds** | No holds; touches only `agents`. Needed before the next major release of either SDK. Wave 08 also edits `backlog.md` (mechanical rebase). |

## Context

`release.sh` bumps the version, then `relock-editable.sh <package>` runs `uv lock` in every project
whose tracked `uv.lock` records the package with an editable source, and checks that the lock records
the new version. uv ignores a version range on a dependency that comes from an editable path source: a
project requiring `pkg-a<1.1` relocks to 1.1.0 without an error (checked with uv 0.7.2;
`constraint-dependencies` behaves the same). The reference pods and workshop scaffolds declare
`semantic-evaluation>=5.0.0,<6` and `semantic-tracing>=0.12.0,<1`, so a 6.0.0 release would relock them
silently, and their `pyproject.toml` would exclude the version their lock records. That shows only when
someone installs a pod from Artifactory instead of the local path.

History: the *SDK release relocks every project that installs it editable* plan (2026-11-23) built the
relock and assumed that a range excluding the new version would make `uv lock` fail; the uv behaviour
above shows it does not, which is why this check is separate. Neither changelog has a pre-release.

## Decisions

| # | Decision | Alternative |
|---|---|---|
| D1 | A stdlib parser for `>=`, `>`, `<`, `<=`, `==`, `!=` on plain release numbers (`5`, `5.0`, `5.0.0`; missing parts count as 0). Any other form stops the release as uncheckable | `packaging` via `uv run --with packaging`; upper bound only |
| D2 | One pass over every editable installer before any `uv lock`, reporting all failing projects at once | Check each project right before its relock: a failure would leave earlier locks changed and name one project per run |
| D3 | The release stops; the person raises the range (and applies the release's *To upgrade* steps to that project) and runs it again | Raise the range automatically: would hide that a major release needs the project's code to move too |
| D4 | A new version that is not a plain release number (`6.0.0rc1`) stops the check with `cannot check a pre-release version` | Skip the check for pre-releases with a warning |

## Contracts

**New `.claude/skills/sdk-release/scripts/declared_range.py`** (stdlib, Python 3.11+ for `tomllib`, like the
`lock_info` helper; executable):

```
declared_range.py PYPROJECT DIST VERSION
```

- Collects every requirement string in `[project].dependencies`, each list in
  `[project.optional-dependencies]` and each list in `[dependency-groups]` (string items only; an
  `{include-group = …}` table is skipped) whose name, normalized per PEP 503 (lowercase, runs of `-_.`
  to `-`), equals `DIST` normalized. A requirement's extras (`[azure]`) and marker (`; …`) are dropped.
- For each, the specifier list (comma-separated clauses) must admit `VERSION`.
- exit 0: every such requirement admits it, or none has a range. Prints nothing.
- exit 1: one stderr line per failing requirement, `<requirement> excludes <VERSION>` or
  `cannot check <requirement>: <reason>` (unsupported operator, a version that is not plain,
  `VERSION` itself a pre-release).
- exit 2: usage error or unreadable `PYPROJECT`.

**`relock-editable.sh`**: a first pass over the same editable lock files runs
`declared_range.py "$dir/pyproject.toml" "$DIST" "$VERSION"` for each and collects failures as
`range check failed in <dir>: <line>`. If any failed: print them all to stderr, print nothing on stdout,
exit 1, before any `uv lock`. Otherwise the existing relock pass runs unchanged. `release.sh` is unchanged:
it already stops on a failing relock before publishing.

## Acceptance cases

All unit, in `test_relock_editable.py`, built with its existing helpers (`sdk_package`, `consumer`,
`bump`, `init_repo`); `consumer(repo, name, requirements, sources)` gets a way to add optional
dependencies and dependency groups for AC8.

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | A range that admits the version | `ok/` requires `pkg-a>=1.0.0,<2` editable | bump to 1.1.0, `relock-editable.sh pkg_a` | exit 0; `ok/uv.lock` records 1.1.0 | unit |
| AC2 | An excluding range stops before any relock | `ok/` as AC1; `pinned/` requires `pkg-a>=1.0.0,<1.1` editable | the same | non-zero exit; stderr names `pinned`, `<1.1` and `1.1.0`; stdout empty; both lock files byte-identical to before | unit |
| AC3 | Every failing project named | `pinned/` and `pinned2/` both exclude 1.1.0 | the same | stderr names both | unit |
| AC4 | No range passes | `bare/` requires `pkg-a` editable | the same | exit 0; relocked | unit |
| AC5 | Extras, markers and name spelling | `x/` requires `PKG_A[extra]>=1,<1.1 ; python_version >= "3.8"` editable | the same | non-zero exit naming `x` | unit |
| AC6 | `!=` and `==` | `ne/` requires `pkg-a!=1.1.0`; separately `eq/` requires `pkg-a==1.0.0` | the same | each stops, named | unit |
| AC7 | An unreadable range stops | `tilde/` requires `pkg-a~=1.0` | the same | non-zero exit; stderr `cannot check` naming `tilde` | unit |
| AC8 | Optional dependencies and groups count | `grp/` requires `pkg-a` in `dependencies` and `pkg-a<1.1` in `[dependency-groups] dev` | the same | non-zero exit naming `grp` | unit |
| AC9 | A pre-release version stops | `ok/` as AC1 | bump to `1.1.0rc1` | non-zero exit; `cannot check a pre-release version` | unit |
| AC10 | An index installer is not checked | `remote/` requires `pkg-a<1.1` with no editable source (its lock has no `pkg-a` editable entry) | bump to 1.1.0 | exit 0; `remote/uv.lock` unchanged | unit |

The existing AC1–AC5 tests of the relock keep passing unchanged.

## Sub-tasks

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| S0 | Tests first: AC1–AC10 | `.claude/skills/sdk-release/scripts/test_relock_editable.py` | — | each new test fails for the reason its case states; existing tests pass | `test-author` (medium) |
| S1 | `declared_range.py` and the first pass in `relock-editable.sh` per the contract | `.claude/skills/sdk-release/scripts/declared_range.py`, `.claude/skills/sdk-release/scripts/relock-editable.sh` | S0 | AC1–AC10 pass; `bash -n` clean | medium |
| S2 | Skill text and docs | `.claude/skills/sdk-release/SKILL.md` (step 2: the range check stops a release before any relock; raise the range and rerun), `docs/02-skills-and-subagents.md` § `sdk-release`, `backlog.md` (remove the entry), `docs/history/` | S1 | `doc-conventions` loaded; claims match the scripts | inline |

## Verification

- `python3 .claude/skills/sdk-release/scripts/test_relock_editable.py`.
- `ruff check .claude` and `ruff format --check .claude`; `bash -n` on both shell scripts.
- Smoke, read-only for `Semantic_Evaluation`: `git worktree add --detach` it into a scratch dir, run
  `declared_range.py` on each editable installer's `pyproject.toml` with `semantic-evaluation 6.0.0`
  (expect the pods declaring `<6` named) and `5.9.0` (expect exit 0); remove the worktree.

## Exit criteria

AC1–AC10 pass, the existing relock tests pass, lint clean, smoke as expected, docs and backlog updated,
plan archived.

## Board fields

`repo=agents wave=wave-09-release-checks-declared-ranges "title=An SDK release checks the projects' declared version ranges" mode=batch status=ready integration=push approved=2026-11-26 expires=2026-12-10`. No holds, no exclusive resources, no new dependencies.
