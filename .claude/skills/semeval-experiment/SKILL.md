---
name: semeval-experiment
description: Runs an experiment that compares an LLM agent's configurations on its offline evaluation, in a project that already has evaluation/evaluation_manifest.yaml. Use it when asked to compare models, deployments, prompts, reasoning effort, temperature or feature switches, to find out whether a change makes the agent better, cheaper or faster, to tune the agent, to repeat runs to see how much results vary, or to establish, compare against or promote a baseline. Covers making the configuration reach the agent, a run file with repeats and trace metrics, running each configuration, the eval-report comparison table, recording the experiment and its decision in the repository, and promote-baseline. Not for a regression check after an ordinary change (semeval-maintain).
---

# Run an experiment

The end state: every configuration was run on the same dataset with repeats, the
comparison table is in the chat, the experiment is recorded in
`evaluation/experiments/` with its question, configurations, results and decision, and a
baseline was promoted only if the person asked.
Never open, print or search `.env`, not even for the names it sets; `.env.example` lists them, and the commands read it themselves.

```bash
uv run eval-docs show offline-evaluation    # Comparing configurations, Run artifacts, eval-report, Local tuning workflow
uv run eval-docs show run-config            # run files, run_label, baseline
uv run eval-docs show datasets-cli          # promote-baseline
```

## 1. Write the question down first

One sentence the experiment answers ("Does reasoning effort `low` keep tool choice at 5.0
while halving cost?"), the configurations (the baseline first), the dataset, and what
result would decide it. Ask the person if the request leaves any of these open; an
experiment without a decision rule ends in a table nobody acts on.

## 2. Make the configuration reach the agent

`run_config` only labels a run unless the predictor passes it on
(`offline-evaluation`, Configurations reach the agent through the predictor). Check
`evaluation/predictor.py`:

- it takes `run_config` in `__init__`, and `evaluation/run.py` builds it with the run's
  configuration and accepts `--config KEY=VALUE` (the templates in
  `semeval-setup-evaluation/references/` do both);
- every key the experiment varies reaches the agent: the model deployment, reasoning
  effort, temperature, a switch. Trace one turn per configuration and look at the
  generation's model and parameters before running the whole dataset.

A key the agent does not read makes two configurations run the same agent with different
labels. Fix that before anything else.

## 3. One run file per experiment

`evaluation/runs/<experiment>.yaml`, from `references/runs/experiment.yaml`: the scopes
and the dataset under test, `repeats` (3 or more: one execution per item says nothing about
spread), `trace_metrics` for what the question is about (`wall_time_s`, tokens,
`cost_usd`, `tool_calls`), and `score_publication` to keep repeats from multiplying the
scores Langfuse bills. The configurations themselves go on the command line, so one run
file serves them all.

Compare on a released dataset when one exists; a dev dataset changes between runs. Every
configuration runs on the same dataset version.

## 4. Before comparing on cost

Cost comes from Langfuse's model prices. A model Langfuse cannot price reads as free, and
`eval-report` flags a run with no cost. A model Langfuse prices at the provider's list price reads
cheaper than Azure bills it. Load `semeval-model-pricing` to check that each configuration's
model is priced at its deployment's price before the first run; prices apply only to runs
after they are set. If a model cannot be priced, tell the person and leave cost out of the
decision.

## 5. Run each configuration

```bash
uv run python -m evaluation.run --run-file evaluation/runs/<experiment>.yaml \
  --run-label <label> --config <key>=<value> [--config ...]
```

The baseline first, then each candidate, each with a label that names its configuration.
A run calls the agent items × repeats times and calls judges as often: say the count
before starting a large one.

## 6. Read the results

```bash
uv run eval-report evaluation/outputs/<run file name> --latest <number of configurations>
```

Show the person the comparison table. Judge each metric on its mean and spread together:
a difference smaller than the spread of either side is no difference. Read the gate and
the failing metrics of each configuration, and the trace metrics against the question. One
item's score decides nothing; open the items behind a surprising aggregate in Langfuse
(the report links each run).

## 7. Record the experiment

`evaluation/experiments/YYYY-MM-DD-<name>.md`, from `references/experiment_record.md`: the
question, the configurations, the dataset and its version, the run names, the
`eval-report` table, what the results mean, and the decision, or that the person decides.
Commit it with the run file; the next person asking the same question reads it first.

## 8. Baselines, only when asked

`eval-dataset promote-baseline --run-name <execution name>` writes a run's aggregates into
the manifest's `baselines`. Do it only when the person asks to adopt a configuration; with
`--update-gates` (which raises thresholds) only when they ask for that too. With
`score_publication.aggregates_on: last_repeat`, the run name is the last repeat's,
`<execution name>_r<repeats>`.

## Report back

The question, the table, the answer in one sentence, the decision or the open question, the
record's path, and anything that weakens the result: an unpriced model, a dev dataset,
fewer than 3 repeats, a metric with too few scored items.
