---
name: sdk-release
description: Release a new version of semantic_tracing or semantic_evaluation — bumps the version, verifies the changelog, relocks the projects that install it editable, builds, and publishes to the ramtech-pypi index. Use when the user asks to release/publish/ship a new SDK version.
argument-hint: <package> <version>
disallowed-tools: WebSearch, WebFetch
---

Runs the SDK release sequence for `semantic_tracing` or `semantic_evaluation`. Must be invoked from the
`Semantic Evaluation` repo root (`~/Projects/Semantic_Evaluation`), where `sdk/<package>/` lives.

1. Confirm `sdk/<package>/CHANGELOG.md` already has a `## [<version>]` entry — changelog before release,
   never the other way around. If it doesn't, stop and write the changelog entry first (per the
   CHANGELOG format in `instructions.md`'s Documentation update phase), then re-run. A major release
   (`x.0.0`) also needs a `### To upgrade` section in that entry, because the upgrade skill reads it.
   If the section is missing, stop in the same way.
2. Run `${CLAUDE_SKILL_DIR}/scripts/release.sh <package> <version>`. It bumps
   `sdk/<package>/pyproject.toml`'s version, then relocks every project in the repo that installs the
   package editable (`scripts/relock-editable.sh <package>`: each git-tracked `uv.lock` that records the
   package with an editable source gets `uv lock` and must then record the new version). Before any
   relock it checks that each of these projects' declared ranges on the package (dependencies, optional
   dependencies, dependency groups) admits the new version, with `scripts/declared_range.py`, because uv
   ignores a range on an editable path source and would relock past it. A range that excludes the
   version, or one the check cannot read (`~=`, a wildcard, a pre-release), stops the release with no
   lock changed, naming every such project. Raise that project's range, apply the release's
   `### To upgrade` steps to it for a major release, and run the script again. A pre-release version
   (`6.0.0rc1`) always stops the check. Then it removes
   `sdk/<package>/dist/`, runs `uv sync`, `uv build`, the slow `tests/test_packaged_docs.py` (it builds the
   package again and checks that the wheel carries every docs page), and `uv publish --index
   ramtech-pypi` (credentials come from `~/.netrc`, already configured; no token handling needed). Last it
   stages `pyproject.toml`, `CHANGELOG.md` and every relocked `uv.lock` together and lists them. If the
   relock fails, nothing was published: the error names the project; fix it and run the script again.
   The docs need no step of their own: the package's `hatch_build.py` stages them into
   `src/<package>/_docs/` during the build, and keeps that copy when `uv build` makes the wheel from the
   sdist, where files outside the project directory no longer exist. If the docs test fails, nothing was
   published; fix the cause rather than skipping the test.
3. Do not commit automatically — leave the staged files for the normal commit-proposal flow, so the
   commit message can be reviewed first like any other wave landing.
4. After a successful release, check whether other repos in the workspace pin the released package (grep
   their `pyproject.toml` / lockfiles for `semantic_tracing` or `semantic_evaluation`) and flag any that
   are now behind the version just published — don't bump those repos automatically, just report them.
