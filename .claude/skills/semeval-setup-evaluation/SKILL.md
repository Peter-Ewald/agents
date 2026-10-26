---
name: semeval-setup-evaluation
description: Sets up offline evaluation and regression tests for an LLM agent, in an existing project or a new, empty one, with the semantic-evaluation SDK, the shared scoring service and Langfuse datasets. Use it when asked to add evaluation, regression tests, a regression gate, evals or an evaluation dataset to an agent, chatbot, assistant or LLM workflow that has none yet, or to wire its evaluation into CI. Not for a project that already has evaluation/evaluation_manifest.yaml; changing such a project's agent is semeval-maintain.
---

# Set up offline evaluation for an agent

The end state: the project holds the configuration layout every project uses, a first dev
dataset is in Langfuse, a first run has been scored and published, `evaluation/coverage.md`
says what it covers, and the always-on rule tells the next agent to keep it current.

```
evaluation/
  __init__.py
  evaluation_manifest.yaml          the metric catalogue, the dataset of each scope, baselines
  evaluation_manifest.schema.json   written by `eval-dataset schemas`
  runs/
    regression.yaml                 the regression run
    run_file.schema.json            written by `eval-dataset schemas`
  predictor.py                      plays each item through the agent
  run.py                            runs one evaluation
  coverage.md                       what the evaluation covers
  datasets/
    archive/                        one snapshot per release, committed (.gitkeep until then)
    incoming/                       working copies, gitignored
```

Templates for every file are in `references/` next to this file. `uv run eval-docs show
run-config` is the reference for every field; read it before changing a template's shape.

If `evaluation/evaluation_manifest.yaml` already exists, stop: the project is set up. A
change to its agent is `semeval-maintain`, and its datasets are `semeval-datasets`.

## 1. Learn the agent before writing anything

Read the code until you can say:

- **The entry point** a single turn goes through, its input and what it returns.
- **The behaviours** that matter: what it must do, what it must not do, which tools it
  calls and when. The README, the prompts and the tests say most of this.
- **What is deterministic code and what is the agent.** Parsing, arithmetic, formatting
  and tool implementations are code; their tests are unit tests, and they stay unit tests.
  The evaluation checks the agent: which tools it chose, with what, in which order, and
  what it said.

Then ask the person what the code cannot tell, and wait for the answers before writing
anything. These are their decisions; do not choose them yourself, unless the request
already answers them:

1. The **product id**, short and lower_snake (`pathfinder`, `drainage`): it starts every
   dataset name and every item id, because Langfuse ids are unique across a whole project.
2. **How the project will maintain its datasets** (`uv run eval-docs show
   datasets-lifecycle`, section Curation workflow): curated in Langfuse (items come from
   traces, review and hand-written cases), or built from sources in the repository (the
   agent is tested on fixtures the repository holds, by a committed recipe). It decides
   where an item is edited from now on.
3. Which **Langfuse project** to use, if `.env` does not already name one.

## 2. Install

Check the prerequisites first, and say which one is missing rather than working around it:
a token for `artifactory.ramboll.com` in `~/.netrc`, the VPN, and the Langfuse keys. Where
each comes from: `uv run eval-docs show access-and-credentials` (load `semeval-guide` for
access questions).

- **`uv.toml`**: add the internal index and `prerelease = "allow"` from
  `references/uv.toml`, keeping whatever is there.
- **`uv add semantic-evaluation`**. It brings `semantic-tracing`, `python-dotenv` and
  `eval-docs`. From here on, check facts with `uv run eval-docs` rather than from memory.
- **`.gitignore`**: add the lines in `references/gitignore.txt` that are missing.
- **`.env.example`**: add the variables in `references/env.example`, names only. The real
  values go in `.env`, which you never read, print or commit. If `.env` lacks a value, ask
  the person to add it.

## 3. Trace each turn

The runner links every prediction to its Langfuse trace and refuses a prediction without a
`trace_id`. `references/predictor.py` traces each turn with `@step` and `get_trace_id()`,
and calls `setup_tracing` when the project does not. If the project already sets up
tracing, call its setup instead, so the evaluation traces look like production's. Full
tracing of a project (framework spans, model calls as generations, users and sessions,
cost) is a separate job, `semeval-setup-tracing`: say so rather than doing it here.

## 4. The configuration

1. Copy `evaluation_manifest.yaml`, `runs/regression.yaml`, `predictor.py`, `run.py` and
   `coverage.md` from `references/` and fill in every `<placeholder>`. Add an empty
   `evaluation/__init__.py` and `evaluation/datasets/archive/.gitkeep`.
2. Point `predictor.py` at the agent's real entry point, and make the prediction a dict
   whose keys the metrics read. Tool-call metrics read `prediction["tool_calls"]`, a list
   of `{"name", "args", "output"}`; if the agent does not return its calls, collect them
   from the trace or from the framework's run result. Where the agent takes settings an
   experiment would vary (model, reasoning effort, a feature switch), hand them on from
   `run_config` in `_turn`, so `run.py --config` changes what the agent does.
3. **Choose the metrics from the live catalogue**, never from memory or a copy:
   `curl -s "$OFFLINE_SCORING_BASE_URL/evaluators"` lists every evaluator and the
   parameters it accepts; `uv run eval-docs show evaluator-catalogue` says what each does.
   - `builtin_deterministic` checks the agent's path: a tool called or not called, the
     order of two tools, their arguments and output, the URLs and policies it used. Use one
     for every behaviour that is a decision about a tool.
   - A check that only exercises deterministic code is a unit test. Write the pytest test
     instead of a metric.
   - What the agent says is judged by an LLM (`custom_rubric`, `deepeval`,
     `azure_ai_evaluation`), which needs a connection profile on the scoring service. If
     none is registered, start with deterministic metrics only and say that a judge needs
     one (`semeval-guide`).
   - Thresholds are on the normalized 1 to 5 scale. Deterministic metrics are binary: 5.0.
     A judge's threshold leaves margin for its variability: 4.0 rather than 5.0.
   - A judge, a custom rubric, or any later change to the metrics is `semeval-metrics`.
4. `uv run eval-dataset schemas` writes both schema files. Then
   `uv run eval-dataset resolve-run --run-file evaluation/runs/regression.yaml --manifest
   evaluation/evaluation_manifest.yaml` must print every metric of every scope.

## 5. The first dataset

Name it `{product}_{schema type}_{scope}_dev` (`eval-docs show datasets-lifecycle`, Naming
convention); `end_to_end` is the usual first scope. Write items for every behaviour from
step 1, with at least one item per behaviour, the item that must *not* do something
included. Item ids are `{product}-{scope}-{nnn}`, or a name that says what the item is.

- **Curated in Langfuse:** write them into the working copy
  `evaluation/datasets/incoming/{scope}_dev.json`, in the shape `eval-dataset pull`
  writes (`eval-docs show datasets-cli`, section The working copy), then
  `uv run eval-dataset validate --source <file>`.
- **Built from sources:** write the recipe (a small command under `evaluation/` that builds
  the items from the fixtures) and the working copy it writes, and add a row per source to
  the coverage map. A fixture is where such an item is true; it is never edited in Langfuse.

Push it with `create_on_missing: true` in `dataset_sync`:

```bash
uv run eval-dataset push-all --manifest evaluation/evaluation_manifest.yaml --version-label 0.1 --dry-run
uv run eval-dataset push-all --manifest evaluation/evaluation_manifest.yaml --version-label 0.1
```

Then set `create_on_missing: false`, so a later typo in a dataset name fails instead of
creating a dataset, and delete the working copy: Langfuse holds the dataset now.

## 6. The first run

```bash
uv run python -m evaluation.run
```

This run is on the dev dataset, so it shows that the pieces work; it is not yet a gate.
Read the report it prints (`eval-report`): every item predicted, every metric scored. A metric that fails on an
item may be the agent, or the item, or the metric's parameters. Find out which before
changing anything, and never lower a threshold to make a run pass. The Langfuse dataset
run is named `{name}_{timestamp}`.

## 7. The coverage map, the rule, CI

- **`evaluation/coverage.md`**: one row per behaviour, the items that prove it and the
  metric that checks it, the datasets, and the "you changed, so update" table adapted to
  this project. It is what `semeval-maintain` reads first on every later change.
- **The always-on rule**: append the section in `references/rules/CLAUDE.md.snippet` to
  the project's `CLAUDE.md` (create it if there is none), and copy
  `references/rules/eval.instructions.md` to `.github/instructions/eval.instructions.md`,
  which is where Copilot reads it. Narrow its `applyTo` to the agent's
  folder when the agent has one (`"src/my_agent/**"`; one glob only).
- **CI**, when the project has a pipeline or asks for one: `references/ci.md`. The gate
  (`--fail-on-gate`) runs on a released dataset only. Until the first release
  (`semeval-datasets`, after at least 20 reviewed items per scope), the job runs without
  failing on the gate, and the person is told so.

## Report back

Say what was created, the dev dataset's name and item count, the first run's result per
metric with its Langfuse run name, what is not covered yet, and what the person has to do
(a connection profile for a judge, the first release, the CI secrets).
