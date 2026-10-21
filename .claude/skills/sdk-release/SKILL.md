---
name: sdk-release
description: Release a new version of semantic_tracing or semantic_evaluation — bumps the version, verifies the changelog, builds, and publishes to the ramtech-pypi index. Use when the user asks to release/publish/ship a new SDK version.
argument-hint: <package> <version>
disallowed-tools: WebSearch, WebFetch
---

Runs the SDK release sequence for `semantic_tracing` or `semantic_evaluation`. Must be invoked from the
`Task Force Evaluation` repo root, where `sdk/<package>/` lives.

1. Confirm `sdk/<package>/CHANGELOG.md` already has a `## [<version>]` entry — changelog before release,
   never the other way around. If it doesn't, stop and write the changelog entry first (per the
   CHANGELOG format in `instructions.md`'s Documentation update phase), then re-run.
2. Run `${CLAUDE_SKILL_DIR}/scripts/release.sh <package> <version>`. It bumps
   `sdk/<package>/pyproject.toml`'s version, removes `sdk/<package>/dist/`, runs `uv sync`, `uv build`,
   the slow `tests/test_packaged_docs.py` (it builds the package again and checks that the wheel carries
   every docs page), and `uv publish --index ramtech-pypi` (credentials come from `~/.netrc`, already
   configured — no token handling needed), then stages `pyproject.toml`, `CHANGELOG.md`, and `uv.lock`
   together. The docs need no step of their own: the package's `hatch_build.py` stages them into
   `src/<package>/_docs/` during the build, and keeps that copy when `uv build` makes the wheel from the
   sdist, where files outside the project directory no longer exist. If the docs test fails, nothing was
   published; fix the cause rather than skipping the test.
3. Do not commit automatically — leave the staged files for the normal commit-proposal flow, so the
   commit message can be reviewed first like any other wave landing.
4. After a successful release, check whether other repos in the workspace pin the released package (grep
   their `pyproject.toml` / lockfiles for `semantic_tracing` or `semantic_evaluation`) and flag any that
   are now behind the version just published — don't bump those repos automatically, just report them.
