---
name: semeval-datasets
description: Pulls, edits, validates, diffs, pushes, promotes and archives the Langfuse evaluation datasets of a project that uses the semantic-evaluation SDK and its eval-dataset command. Use it when working with golden or evaluation datasets and their items, dev datasets and releases, dataset names and version labels, working copies under evaluation/datasets, releasing a dataset version, filing a release snapshot, or deciding whether a dataset is ready to release.
---

# Evaluation datasets: the mechanics

`uv run eval-docs show datasets-lifecycle` is the reference for every rule below, and
`uv run eval-docs show datasets-cli` for every command and flag. This skill holds the
order and the judgement calls.

## The rules that do not bend

- **Langfuse is the single source of truth for datasets.** The repository holds
  short-lived working copies (gitignored, deleted after their push) and one archived
  snapshot per release, or, in a project that builds its items from sources in the
  repository, those sources and the recipe.
- **Two states.** `{product}_{schema type}_{scope}_dev` is mutable and is never gated or
  experimented on. `{product}_{schema type}_{scope}_v{M.m}` is a release: immutable,
  created by `promote`, and the only kind a gate, an experiment or a dashboard reads.
- **Item ids carry the product and the scope**, because Langfuse ids are unique across the
  whole Langfuse project, not per dataset.
- **`push` never deletes.** A remote item missing locally is reported under
  `would_delete`; removing it is a deliberate step in the Langfuse UI, agreed with a person.
- **Never read, print or commit Langfuse keys.** `eval-dataset` reads them from `.env`.

Every command runs from the project root with the project manifest:

```bash
M=evaluation/evaluation_manifest.yaml
```

## Change a dev dataset

Which way the project maintains it is in `evaluation/coverage.md`.

**Curated in Langfuse.** Edit small things in the Langfuse UI, or edit in batch:

```bash
uv run eval-dataset pull-all --manifest $M                     # working copies into dataset_sync.scoped_dir
uv run eval-dataset validate --source evaluation/datasets/incoming/<scope>_dev.json
uv run eval-dataset diff --name <dataset>_dev --source evaluation/datasets/incoming/<scope>_dev.json
uv run eval-dataset push-all --manifest $M --version-label <label> --dry-run
uv run eval-dataset push-all --manifest $M --version-label <label>
rm evaluation/datasets/incoming/<scope>_dev.json
```

**Built from sources in the repository.** Edit the fixture or the recipe, rebuild with the
project's own command, push as it does. An item is true in its source; editing it in
Langfuse is undone by the next build.

**Dev labels** count up per push that changes content (`0.1`, `0.2`, ...). Items carry the
label of the push that last changed them (`changed_last_in_dataset_version`); unchanged
items keep theirs, and a repeated push of the same content writes nothing.

**A new dataset** needs `create_on_missing: true` in `dataset_sync` (or
`--create-on-missing` on `push`) for its first push only. Set it back to `false` straight
after, so a misspelled name fails instead of creating a second dataset.

## Release a dataset

**Ready when** all three hold, and say which does not when one does not:

1. the shape of `input` and `expected_output` has settled;
2. the ground truth has been reviewed by someone who knows the domain (each item's
   `ground_truth_status` is `reviewed` or `promoted`, not `seeded`);
3. there are enough items: at least 20 per scope is the recommendation.

**The version.** The first release is `1.0`. After that, no change to the shape of the
items is a minor bump (`1.0` to `1.1`); any shape change, a field added to every item or
removed from any, is a major bump (`1.1` to `2.0`). `promote` checks this against the
previous release and refuses a wrong bump; `--force` is for a person who has looked at the
schema report and disagrees, not for getting past the check.

```bash
uv run eval-dataset promote --dev-name <dataset>_dev --version 1.1 \
  --previous-release-name <dataset>_v1.0 --dry-run
uv run eval-dataset promote --dev-name <dataset>_dev --version 1.1 \
  --previous-release-name <dataset>_v1.0
uv run eval-dataset archive --name <dataset>_v1.1 --manifest $M --scope <scope>
git add evaluation/datasets/archive/<dataset>_v1.1.json
```

`archive` writes the snapshot into `dataset_sync.archive_dir` (by default
`evaluation/datasets/archive/`) and refuses a dev dataset or a snapshot that is already
there: a snapshot is never edited. Commit it with the change that released it.

**Then point the runs at the release.** In `evaluation_manifest.yaml`, set the scope's
`scope_to_dataset` to the release name, or, when only some runs move, the run file's
`datasets.<scope>`. Check with `uv run eval-dataset resolve-run --run-file
evaluation/runs/<run>.yaml --manifest $M`, and update the coverage map's datasets table.

## Other commands

| Need | Command |
|---|---|
| One dataset to a file | `eval-dataset pull --name <dataset> --out <file>` |
| One file to one dataset | `eval-dataset push --name <dataset> --source <file> --version-label <label>` |
| Duplicates in a working copy | `eval-dataset dedupe --source <file>` |
| What a run reads | `eval-dataset resolve-run --run-file <run> --manifest $M` |
| The editor schemas, after an SDK upgrade | `eval-dataset schemas` |

## When a command fails

- `push` refuses an unknown dataset: the name is misspelled, or this is a first push and
  needs `create_on_missing` once.
- `promote` refuses the version: read the schema change it reports. A shape change needs a
  major version.
- `archive` refuses: the name is a `_dev` dataset, or the snapshot already exists.
- Anything about keys, the VPN or Artifactory: `semeval-guide`.
