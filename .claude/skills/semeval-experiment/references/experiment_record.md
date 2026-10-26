# <Experiment title>

**Date:** <YYYY-MM-DD> · **Asked by:** <person> · **Run file:** `evaluation/runs/<experiment>.yaml`

## Question

<One sentence the experiment answers, and the result that would decide it.>

## Configurations

| Label | Configuration | Run name in Langfuse |
|---|---|---|
| <baseline label> | `<key>=<value>` | `<execution name>` |
| <candidate label> | `<key>=<value>` | `<execution name>` |

Dataset: `<dataset name>` (<release or dev, and its version>), <items> items, <repeats>
repeats each.

## Results

<The comparison table `eval-report` printed, unchanged.>

## What it means

<Per metric that matters to the question: the difference, and whether it is larger than
the spread. Anything that weakens the result: an unpriced model, a dev dataset, few items.>

## Decision

<What was decided and by whom, or "open: <what is needed to decide>". Whether a baseline
was promoted.>
