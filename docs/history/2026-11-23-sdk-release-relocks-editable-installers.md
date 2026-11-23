---
date: 2026-11-23
title: An SDK release relocks every project that installs it editable
outcome: completed
---

# Wave 06 (agents): An SDK release relocks every project that installs it editable

## Summary

| | |
|---|---|
| Goal | When `semantic_tracing` or `semantic_evaluation` is released, every `Semantic_Evaluation` project that installs it editable has its `uv.lock` updated to the new version and staged with the version bump. A later `uv run` in those projects then changes no lock file. Serves backlog Next Up step 1 (the inbox request `from-semeval-release-relock`, now a backlog entry) |
| Kind | Implementation (harness script), reported by capability |
| Changes | agents: the `sdk-release` skill (its release script, a new relock script with tests, the skill text), `docs/02-skills-and-subagents.md` § `sdk-release` |
| Behaviour | (1) A project that installs the released package editable is relocked to the new version and listed. (2) A project that does not install it keeps its lock file unchanged. (3) A project that installs only the *other* SDK package is left alone. (4) A project that cannot take the new version stops the release before anything is published, naming the project |
| Decisions | See *Decisions* below: (1) projects are found from the lock files, not from a fixed list; (2) the relock runs before publishing; (3) the six lock files that are already stale get caught up by the next release, not by a separate commit now |
| Risks and holds | No holds. The relock needs Artifactory for the pods' lock files, as publishing already does. A future major release that a pod's version range excludes now stops the release (case 4), which is intended. Wave 06 must merge before the pilot (Next Up step 2) cuts its SDK release; that is backlog order, not yet a filed wave, so no hold |

## Context

`.claude/skills/sdk-release/scripts/release.sh` bumps `sdk/<package>/pyproject.toml`, runs `uv sync` in
that package (which relocks only its own `uv.lock`), builds, publishes and stages
`pyproject.toml`, `CHANGELOG.md` and `sdk/<package>/uv.lock`.

In `Semantic_Evaluation`, ten tracked `uv.lock` files install an SDK package editable through
`[tool.uv.sources]`: the repo root, `sdk/`, `sdk/semantic_evaluation` (installs `semantic_tracing`),
`scoring_app`, `review_sync_app`, `reference_pod_implementations/{agent-framework,langchain}-pod`,
`workshop/scaffold/{agent-framework,langchain}-pod`. `service_auth` installs neither. uv records an
editable package's version in the lock (`name = "semantic-evaluation"`, `version = "5.0.2"`,
`source = { editable = "../sdk/semantic_evaluation" }`), so after a release every one of those lock files
is stale and the next `uv run` there rewrites it. After 5.0.2, `scoring_app` needed a separate commit
(Semantic_Evaluation PR 147); six lock files still record 5.0.0 today.

## Decisions

1. **Find the projects from the lock files.** The relock script takes every tracked `uv.lock`
   (`git ls-files`, so worktrees and `.venv`s are never scanned) whose lock has a package entry with the
   released package's distribution name (`semantic_evaluation` → `semantic-evaluation`) and an
   `editable` source. Alternative: a fixed list in the script (root and `scoring_app`, as the request
   says). Rejected: it already misses seven projects and goes stale with every new pod.
2. **Relock before publishing.** Order in `release.sh`: bump version → relock → `uv sync`, build, docs
   test, publish → stage. A failing relock leaves nothing published; the user fixes the project and
   reruns. Alternative: relock after publishing, which leaves a published version with unstaged locks on
   failure.
3. **No catch-up commit in `Semantic_Evaluation` now.** The six stale lock files get relocked by the
   next release, which the pilot (Next Up step 2) brings soon. Alternative: a one-line relock commit in
   `Semantic_Evaluation` now, a second repo and plan for little gain.
4. **A separate script, `relock-editable.sh <package>`.** Relocking the projects that install a package
   is its own responsibility: it is testable without publishing and can be rerun alone. `release.sh` keeps
   owning the sequence and the staging.

## Contract

`.claude/skills/sdk-release/scripts/relock-editable.sh <package>`

- Run from the `Semantic_Evaluation` root (or any git repo with `sdk/<package>/pyproject.toml`), like
  `release.sh`. `<package>` is the directory name (`semantic_evaluation`, `semantic_tracing`).
- Reads the target version from `sdk/<package>/pyproject.toml` (`version = "…"`).
- For each tracked `uv.lock` that has an editable entry for the package: runs `uv lock` in that
  directory (`uv --directory <dir> lock`), then checks the lock now records the target version.
- **stdout**: the relocked lock files' paths, relative to the repo root, one per line, in `git ls-files`
  order. **stderr**: progress and errors.
- Exits non-zero, naming the project, when `uv lock` fails or the lock still does not record the target
  version afterwards. `set -euo pipefail`; nothing swallowed.

`release.sh` changes: after the version bump, `LOCKS=$(scripts/relock-editable.sh "$PACKAGE")` (path via
the script's own directory); at the end `git add` the three files as now plus every path in `$LOCKS`; the
closing echo lists what it staged.

## Acceptance cases

All unit, in `test_relock_editable.py`, each in a temp git repo built by the test: `sdk/pkg_a` and
`sdk/pkg_b` as minimal projects without dependencies, consumer projects with `[tool.uv.sources]` path
entries, locked with `uv lock` and committed, then `sdk/pkg_a`'s version raised from `1.0.0` to `1.1.0`.
Runs offline (`UV_OFFLINE=1`): only path dependencies.

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | A project installing the package editable is relocked | `app/` installs `pkg_a` editable, its lock records `1.0.0` | `relock-editable.sh pkg_a` | exit 0; `app/uv.lock` records `pkg-a` `1.1.0`; stdout contains `app/uv.lock` | unit |
| AC2 | A project not installing it is left alone | `other/` has no SDK dependency and a committed lock | the same run | `other/uv.lock` byte-identical; not on stdout | unit |
| AC3 | A project installing only the other SDK package is left alone | `b_only/` installs only `pkg_b` editable | the same run | `b_only/uv.lock` byte-identical; not on stdout | unit |
| AC4 | A project that cannot take the new version stops the run | `pinned/` installs `pkg_a` editable and requires `pkg-a<1.1` | `relock-editable.sh pkg_a` | non-zero exit; stderr names `pinned` | unit |
| AC5 | An untracked lock file is ignored | `scratch/uv.lock` installs `pkg_a` editable but is not committed | the same run as AC1 | `scratch/uv.lock` unchanged; not on stdout | unit |

`release.sh`'s new order and staging are checked by reading the diff in the done check (it publishes, so
it is not run in a test).

## Sub-tasks

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| S0 | Tests first: AC1–AC5, stdlib, runnable with `python3 <file>` or pytest, style of `.claude/scripts/test_coordination.py` | `.claude/skills/sdk-release/scripts/test_relock_editable.py` | — | every test fails because `relock-editable.sh` does not exist | test-author |
| S1 | The relock script per the contract | `.claude/skills/sdk-release/scripts/relock-editable.sh` (executable) | S0 | `python3 .claude/skills/sdk-release/scripts/test_relock_editable.py` passes; `bash -n` clean | medium |
| S2 | `release.sh`: call the relock after the bump, stage its lock files | `.claude/skills/sdk-release/scripts/release.sh` | S1 | `bash -n` clean; diff shows relock before `uv sync`/publish and the extra `git add` | inline |
| S3 | Skill text and docs | `.claude/skills/sdk-release/SKILL.md` (step 2), `docs/02-skills-and-subagents.md` § `sdk-release` | S2 | both describe the relock and the new staging; read against the script | inline |

## Documentation upkeep

- `SKILL.md` step 2 and `docs/02-skills-and-subagents.md` § `sdk-release`: the release also relocks and
  stages every project that installs the package editable, before publishing.
- `backlog.md`: remove the entry, renumber Next Up; the pilot's entry needs no change.
- `docs/history/2026-11-23-sdk-release-relocks-editable-installers.md` and its index line.
- No `CHANGELOG.md` (no package released).

## Verification

- `python3 .claude/skills/sdk-release/scripts/test_relock_editable.py`
- `python3 .claude/scripts/test_coordination.py` (unchanged suite still passes)
- `bash -n` on both scripts; `shellcheck` on both if installed
- **Smoke against the real repo, without pushing anything:** `git clone --local
  ~/Projects/Semantic_Evaluation <scratch>/se`, run `relock-editable.sh semantic_evaluation` there
  (version unchanged at 5.0.2). Expected: stdout lists the nine lock files with an editable `semantic-evaluation` entry (the package's
  own included), the six that record 5.0.0 now
  record 5.0.2, `service_auth/uv.lock` unchanged. Then delete the clone.

## Exit criteria

AC1–AC5 pass; verification passes; the smoke run shows the six stale locks caught up; docs, backlog and
history done; landed on `main` by push.

## Board

`agents/wave-06-relock-editable-installers`: `title=An SDK release relocks every project that installs it
editable`, `mode=batch`, `status=ready`, `integration=push` (`.claude/rules/integration.md`), no holds, no
exclusive resources, no new dependencies, `approved=2026-11-23`, `expires=2026-12-07`.


## Question

Blocked in Specify, 2026-11-23. This wave makes an SDK release also update the `uv.lock` files of every
`Semantic_Evaluation` project that installs the SDK editable. Case AC4 says a project whose version range
excludes the new release (`pinned/` requiring `pkg-a<1.1`) stops the release. It cannot be tested as
written: with an editable path source, uv 0.7.2 ignores the version range and relocks to 1.1.0 with exit 0
(reproduced by hand; `constraint-dependencies` behaves the same). The plan's risk line "a future major
release that a pod's version range excludes now stops the release" is therefore false too: the reference
and workshop pods declare `semantic-evaluation>=5.0.0,<6`, and a 6.0.0 release would relock them silently,
just as any `uv run` there does today. Which shape should AC4 take?

Options:
- (a, recommended) Keep AC4 as "a project whose relock fails stops the release before publishing, naming
  the project", with the failure caused by the new version itself (the bumped `pkg_a` 1.1.0 adds a
  dependency that cannot be resolved offline; verified to make `uv lock` exit 1). The script stays as in
  the contract; the plan's version-range claim is dropped from the docs, and a backlog entry records that
  a major release does not check the pods' declared ranges. Reversible; no extra scope.
- (b) Add a range check to `relock-editable.sh`: read each consumer's declared specifier for the package
  and stop when the new version is outside it. Matches the plan's original intent, but needs a PEP 440
  specifier parser (`packaging`, not stdlib, so run through `uv run --with packaging` or a hand-written
  subset), which is new scope and a dependency the plan does not name.
- (c) Drop AC4: the wave ships AC1-AC3 and AC5 only, and the failure path stays covered only by
  `set -euo pipefail`.

## Answer

Option (a): AC4 tests the failure path with a cause uv acts on (the new version adds an unresolvable dependency, so `uv lock` fails). The release stops before anything is published and the error names the project. Drop the version-range claim and the risk line that rests on it; add a backlog entry recording that a release does not check the pods' declared SDK version ranges.
