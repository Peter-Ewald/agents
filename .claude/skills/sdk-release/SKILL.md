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
   and `uv publish --index ramtech-pypi` (credentials come from `~/.netrc`, already configured — no token
   handling needed), then stages `pyproject.toml`, `CHANGELOG.md`, and `uv.lock` together.
3. Do not commit automatically — leave the staged files for the normal commit-proposal flow, so the
   commit message can be reviewed first like any other wave landing.
4. After a successful release, check whether other repos in the workspace pin the released package (grep
   their `pyproject.toml` / lockfiles for `semantic_tracing` or `semantic_evaluation`) and flag any that
   are now behind the version just published — don't bump those repos automatically, just report them.
