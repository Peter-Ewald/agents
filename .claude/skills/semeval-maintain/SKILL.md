---
name: semeval-maintain
description: Keeps an LLM agent's offline evaluation in step with a change to how the agent behaves, the way a unit test is written with a change to deterministic code. Use it whenever you change, or are asked to change, an agent's system prompt or instructions, a prompt template, a tool (its name, arguments, description or output), the workflow or graph, a routing or decision rule, the model or its settings, or when you fix a bug in what the agent does or says, in a project that has evaluation/evaluation_manifest.yaml. Also before calling such a change done. Not for edits that cannot change the agent's behaviour, such as a README, a comment, formatting, or deterministic code already covered by unit tests.
---

# Keep the evaluation in step with the change

A change to how the agent behaves is done when the evaluation proves the new behaviour
and still proves the old ones. Do this as part of the change, without being asked, the way
the unit test is part of a change to deterministic code.
Never open, print or search `.env`, not even for the names it sets; `.env.example` lists them, and the commands read it themselves.

Start by reading `evaluation/coverage.md`: the behaviours the evaluation covers, the items
that prove each, the metrics that check them, and the project's "you changed, so update"
table. It says how this project maintains its datasets: curated in Langfuse, or built from
sources in the repository. If the project has no `evaluation/evaluation_manifest.yaml`,
the evaluation is not set up; say so and offer `semeval-setup-evaluation`.

## 1. Name what changed

Answer these four before touching a dataset, and say the answers in one short list:

1. **Which behaviour changed**, in one sentence of what the agent now does. A refactor
   that changes no behaviour needs no new item, but still needs step 5.
2. **Which items prove the new behaviour.** New items for what is new; at least one that
   would have failed before the change. A behaviour bug gets the item that would have
   caught it.
3. **Which existing items are now wrong**: their expected output describes the old
   behaviour. Find them in the coverage map's rows for the behaviour, and by searching the
   dataset for the tool, field or phrase that changed.
4. **Which metric checks it.** An existing one, or a new one (step 3).

If the change's intent is unclear enough that the expected output of an item cannot be
written, ask; do not guess an expected output.

## 2. Change the items where they live

The dev dataset (`*_dev`) is the one to change; a release (`*_v{M.m}`) is never edited.

- **Curated in Langfuse:** pull a working copy, edit, validate, push, delete the copy:

  ```bash
  uv run eval-dataset pull-all --manifest evaluation/evaluation_manifest.yaml
  # edit evaluation/datasets/incoming/{scope}_dev.json
  uv run eval-dataset validate --source evaluation/datasets/incoming/{scope}_dev.json
  uv run eval-dataset push-all --manifest evaluation/evaluation_manifest.yaml --version-label <next dev label> --dry-run
  uv run eval-dataset push-all --manifest evaluation/evaluation_manifest.yaml --version-label <next dev label>
  ```

  The dev label counts up from the dataset's current one (`0.1`, `0.2`, ...; the dry run
  and `eval-dataset pull` show it). `push` never deletes: an item to remove shows under
  `would_delete`, and is removed in the Langfuse UI after a person agrees.
- **Built from sources:** edit the fixture or recipe the item is built from, run the
  project's own build command, and push it as that command does. Never edit such an item
  in Langfuse; the next build would overwrite it.

Item ids carry the product and the scope (`{product}-{scope}-{nnn}`, or a name that says
what the item is), because Langfuse ids are unique across the whole Langfuse project.
`semeval-datasets` has the mechanics in full.

## 3. A new metric, only when no existing one checks it

- A decision about a tool (called, not called, its arguments, the order of two tools, its
  output) is a `builtin_deterministic` metric. The live list of evaluators and their
  parameters: `curl -s "$OFFLINE_SCORING_BASE_URL/evaluators"`; what each does:
  `uv run eval-docs show evaluator-catalogue`.
- Something only deterministic code decides is a unit test, not a metric. Write the test.
- What the agent says is an LLM judge, which needs a connection profile on the scoring
  service.

Add it to the catalogue in `evaluation/evaluation_manifest.yaml` with the scopes it
scores, and check the run still resolves:

```bash
uv run eval-dataset resolve-run --run-file evaluation/runs/regression.yaml --manifest evaluation/evaluation_manifest.yaml
```

Never lower a threshold to make a change pass. A threshold changes only when the person
decides the old one was wrong, and the coverage map's metric row says why.

## 4. Update the coverage map

In `evaluation/coverage.md`: the behaviour's row (new or edited), its item ids and
metrics, the item count per dataset, and a new line in the "you changed, so update" table
when this change was a kind the table did not have yet.

## 5. Run the regression run before calling the work done

```bash
uv run python -m evaluation.run          # or the project's own run command, as coverage.md names it
```

Read the result per metric and per item, not only the gate:

- The new items pass: the change works.
- An old item fails: either the change broke a behaviour, which is a bug to fix before the
  work is done, or the item describes behaviour the change replaced on purpose (step 1.3),
  so its expected output is updated.
- A judge's score moved a little on an item that did not change: judges vary. Compare the
  metric's aggregate, not one item, and repeat the run before concluding.

If the run cannot start (no scoring service, no Langfuse keys, the system the agent drives
is not running), say exactly what is missing and that the change is not verified yet. Do
not report the work as done.

## 6. Releasing, when the change is meant to be judged on

A gate and an experiment run on a released dataset, never on `_dev`. When the change is
finished and the person wants it judged (or CI gates on the release), promote the dev
dataset to the next version and file the snapshot: `semeval-datasets`, Releasing. A change
to the shape of an item's `input` or `expected_output` makes the next release a new major
version.

## Report back

One short list: the behaviour that changed, the items added and edited (ids), the metric
added if any, the dev dataset's new label, the regression run's result per metric with its
Langfuse run name, and anything not verified.
