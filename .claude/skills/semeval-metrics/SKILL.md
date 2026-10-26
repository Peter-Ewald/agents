---
name: semeval-metrics
description: Chooses and configures the metrics an LLM agent's offline evaluation scores it with, in a project that already has evaluation/evaluation_manifest.yaml. Use it when asked which evaluator, metric, scorer or LLM judge to use, to check a new quality of the agent's answers (tone, correctness, groundedness, completeness, policy), to add, change or remove a metric, write a custom rubric, change a threshold or the gate, or narrow or override metrics in a run file; also when a metric scores wrong, a judge needs a connection profile, or a metric is wanted for something deterministic code does. Not for setting evaluation up in a project that has none (semeval-setup-evaluation) or for comparing configurations (semeval-experiment).
---

# Choose and configure metrics

The end state: each behaviour that needs checking has a metric of the right kind, configured
with parameters that were tried on a passing and a failing case; the manifest resolves; the
coverage map names the metric for each behaviour; and anything that is deterministic code
got a unit test instead of a metric.

Facts come from the live service and the shipped docs, never from memory or a copy:

```bash
curl -s "$OFFLINE_SCORING_BASE_URL/evaluators"            # what exists now, and the params each takes
uv run eval-docs show evaluator-catalogue                  # what each does; Choosing a deterministic check or a judge
uv run eval-docs show run-config                           # the manifest, run files, only:, overrides, the gate
uv run eval-docs show custom-rubric-and-registration       # custom_rubric, inline and registered
uv run eval-docs show connection-profiles                  # what a judge needs on the service
```

## 1. Name what is to be checked

Read `evaluation/coverage.md` and the request. For each behaviour, say in one sentence what
a good result is and what a bad one looks like, with one real example of each from the
agent. A behaviour that cannot be said that way is not ready for a metric; ask.

## 2. Choose the kind

By the rule in `evaluator-catalogue` (Choosing a deterministic check or a judge):

| The behaviour is | Metric |
|---|---|
| A decision about a tool: called or not, arguments, order, output, URLs and policies used | `builtin_deterministic`. Exact, free, and the same every run |
| What the agent says: correct, grounded, complete, polite, asks where it should | An LLM judge: a catalogue evaluator (`deepeval`, `azure_ai_evaluation`) when one measures exactly this, otherwise `custom_rubric` |
| Done by deterministic code: parsing, arithmetic, formatting, a tool's implementation | No metric. A unit test, written now |

Prefer the deterministic check whenever the behaviour can be read off the agent's path; a
judge is for what only reading the answer can tell. Two metrics that check the same thing
are one too many.

## 3. Configure, and try it before relying on it

- **Parameters** come from the evaluator's entry in `GET /evaluators`: field names on the
  prediction and on `expected_output`, the tool names, the pattern kind. A field the metric
  reads must exist in what the predictor returns and in the items.
- **A custom rubric** starts inline (`framework: custom_rubric`, `evaluator: inline`, the
  rubric in `evaluator_params`): `criteria` says what is judged, `scale` describes all five
  levels concretely for this agent, and `input_fields`, `output_fields` and
  `expected_output_fields` name only what the judge needs. Register it
  (`POST /evaluators/requests`) only when another project should use it too.
- **Try it** with `references/try_metrics.py` on at least one case that must pass and one
  that must fail, from the agent's real output:

  ```bash
  uv run python <this skill's folder>/references/try_metrics.py cases.json \
    --run-file evaluation/runs/regression.yaml --metric <name>
  ```

  A metric that scores both cases alike is misconfigured or checks nothing; fix it before it
  goes in. For a judge, run the passing case twice: a score that moves by more than one level
  needs a sharper scale.

## 4. A judge needs a connection profile

Every judge runs on the model a connection profile on the scoring service names, one per
evaluator backend (`deepeval_llm_judge`, `azure_ai_evaluation_llm_judge`,
`custom_rubric_llm_judge`), shared by every project. HTTP 400 from a judge metric, in a run
or in `try_metrics.py`, means its backend has none. Registering one needs
`SCORING_SERVICE_API_KEY` and a model deployment in an approved EU/EEA region, so do not do
it from a project: tell the person, and name **Peter Ewald** (Teams, `peter.ewald@ramboll.com`)
as the contact. Until then, keep the judge out of the regression run (`only:`), and say so.

## 5. Thresholds and the gate

- On the normalized 1 to 5 scale. Deterministic: 5.0. A judge: below what a good answer
  scores, to absorb its variation, usually 4.0.
- Never lower a threshold to make a run pass. A metric that fails is the agent, the item, or
  the metric's configuration; find which first.
- The gate means something only on a released dataset (`semeval-datasets`).

## 6. Wire it

- **The catalogue** in `evaluation/evaluation_manifest.yaml`: the metric with its `scopes`.
  Every run file then gets it, unless the run narrows its scope's metrics.
- **A run file** narrows with `only: [...]` or adjusts one metric's fields by naming it
  (`run-config`, How a run file resolves). Use it for a run that differs on purpose, such as
  a fast run without judges, not to hide a failing metric.
- **Check** that every run still resolves:

  ```bash
  uv run eval-dataset resolve-run --run-file evaluation/runs/regression.yaml --manifest evaluation/evaluation_manifest.yaml
  ```

- **Items**: a new metric needs the `expected_output` fields it reads on the items, and items
  where it must pass and fail. That is `semeval-maintain`'s step 2.

## 7. The coverage map

In `evaluation/coverage.md`, the metric's row (kind, passes when, threshold) and its name in
the row of every behaviour it checks.

## Report back

Per metric: what it checks, its kind and why, its parameters, the tried cases and their
scores, its threshold, and the runs it is in. Name what is left: a connection profile to
register, items to add, a rubric to register.
