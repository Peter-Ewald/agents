# What the evaluation covers

The living map of what this agent's offline evaluation proves, and how. **Update it in the
same change that changes the agent:** a new or changed behaviour adds or edits a row under
[Behaviours](#behaviours), its items, and the metric that checks it. How to run the
evaluation: `uv run python -m evaluation.run`.

## Datasets

Langfuse holds them. The repository keeps only the snapshot of each release, under
`evaluation/datasets/archive/`.

| Scope | Dev dataset | Judged on (release) | Items | Maintained |
|---|---|---|---|---|
| `end_to_end` | `<product>_agent_end_to_end_dev` | none yet | 0 | Curated in Langfuse, or built from sources in the repository (say which) |

## Behaviours

One row per behaviour the agent must keep. A behaviour without items is not tested.

| Behaviour | Items that prove it | Checked by |
|---|---|---|
| <what the agent must do, in one sentence> | `<item ids>` | `<metric names>` |

## Metrics

| Metric | Kind | Passes when | Threshold |
|---|---|---|---|
| `<metric>` | Deterministic: the agent's path / LLM judge: what it says | <one sentence> | <on the normalized 1 to 5 scale> |

## You changed, so update

| You changed | So update |
|---|---|
| A prompt, or how the agent decides | The items of every behaviour it affects; add one for the new behaviour; run the regression run |
| A tool: its name, arguments or output | The metrics that name it, and the items whose expected calls change |
| A bug in how the agent behaves, fixed | One item that fails without the fix |
| The shape of an item's `input` or `expected_output` | Every item, the predictor, and the next release is a new major version |
