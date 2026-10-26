---
name: semeval-model-pricing
description: Prices a project's Azure model deployments in Langfuse at Azure's own retail meters, with python -m semantic_tracing.pricing, and keeps those prices current. Use it when Langfuse traces or generations show tokens but no cost, when a cost looks lower than the Azure bill or than expected, when a model deployment is added, renamed or moved to another deployment type or region, when Azure changes a price, or before an experiment or evaluation compares configurations on cost. Covers finding what is unpriced, reading the deployment's type and region, the definition to write and which names it matches, writing it, verifying it on a new trace, and the pricing record to commit. Not for choosing a model, a deployment type or a region, and not for reducing what the agent spends.
---

# Price model deployments in Langfuse

The end state: every model deployment the project's traces report has a Langfuse model
definition in each Langfuse project it reports to, priced at Azure's meter for its deployment
type and region; a new trace's cost has been recomputed and agrees; the pricing record is
committed; and the person knows when to check again.

The facts are on one page; read it first:

```bash
uv run python -m semantic_tracing.docs show tracing-model-prices   # or: uv run eval-docs show ...
```

The command needs `semantic-tracing` 0.9.0 or later (`uv add "semantic-tracing>=0.9,<1"`).
Every run below reads the Langfuse keys from the project's `.env` through uv:

```bash
uv run --env-file .env python -m semantic_tracing.pricing <subcommand> ...
```

Never read or print `.env` to see what it holds; the command names any variable that is
missing, and the person adds it. It needs a **project** key pair; an organisation key gets 403.

## 1. Find what is unpriced

```bash
uv run --env-file .env python -m semantic_tracing.pricing unpriced --days 7
```

It names three problems; write down each `model` value it reports:

| It says | Meaning |
|---|---|
| No definition matches | Those generations have no cost at all |
| Usage keys the definition does not price | Those tokens cost 0, so the cost is too low |
| Priced by a Langfuse-managed definition | The provider's list price. Right only for a Global Standard deployment; a Data Zone or regional deployment costs more |

If the project has no traces yet, run one turn the way the project runs first.

## 2. Read each deployment

For each deployment behind those names, read its type and region; never assume them:

```bash
uv run --env-file .env python -m semantic_tracing.pricing azure-prices --account <resource> --deployment <deployment>
```

Find the resource and deployment names in the project's model configuration (an endpoint
`https://<resource>.services.ai.azure.com/...` or `.openai.azure.com`), or ask the person.
When `az` cannot see the resource (another subscription, not logged in), ask the person for the
model, its version, the region and the deployment type, and pass `--model`, `--model-version`,
`--region` and `--deployment-type` instead.

- **Never choose, suggest or change a region or deployment type.** Pricing one does not approve
  it.
- **Provisioned throughput** is billed per hour: it stays unpriced; `apply` records why.
- **Meters it cannot read** are listed, not used. If the meters a deployment needs are among
  them, stop and report them rather than pricing by hand.

## 3. Read the plan

```bash
uv run --env-file .env python -m semantic_tracing.pricing plan --account <resource> --deployment <deployment> \
  --match <each other model value step 1 reported for it>
```

Check, and tell the person:

- the standard input, cached input and output prices per million tokens, and which tiers came
  from the ratio rather than a meter;
- any warning: input and output ratios that differ, another definition whose pattern matches
  the same name (two definitions for one name make the price depend on which wins), meters left
  out;
- `--include-bare-model` only when no other deployment of that model, at another price, reports
  to the same Langfuse project;
- what it differs in from the project's current definition.

## 4. Apply, once the person agrees

It writes to their Langfuse project, so show the plan and ask first (a prompt that already
says to apply it counts):

```bash
uv run --env-file .env python -m semantic_tracing.pricing apply --account <resource> --deployment <deployment> --match ...
```

Every Langfuse project the deployment reports to (dev, prod, another pod's) needs its own
definition: run `apply` once with each project's keys. The record keeps one line per project.

## 5. Verify on a new generation

Cost is fixed when a generation is ingested, so only generations after `apply` carry the new
price. Run one turn the way the project runs, take its trace id, and:

```bash
uv run --env-file .env python -m semantic_tracing.pricing verify --trace-id <trace id>
```

Every generation must say `agrees`, priced by the new definition. `verify` uses the
definition's current prices, so a trace from before `apply` reads as differing; that is
expected. Then say which earlier runs
were priced differently: runs from before the change are not comparable on cost with runs
after it.

## 6. Commit the record

Commit `telemetry/model_prices.json` with a message naming the deployments. It is the evidence
behind any cost the project reports.

## 7. Keeping it current

Tell the person to run `check` when a deployment is added, renamed or moved, when `unpriced`
reports anything, and before an experiment compares configurations on cost:

```bash
uv run --env-file .env python -m semantic_tracing.pricing check
```

It writes nothing and exits 1 when anything changed; `plan` then shows the whole definition and
`apply` replaces it for generations from then on; earlier ones keep their cost. Never edit
Langfuse's managed definitions.

## Report back

Per deployment: its type and region, the prices per million tokens and where they came from,
the definition's id in each Langfuse project, and the verified trace. Then what is left
unpriced and why (provisioned throughput, a meter it cannot read, a Langfuse project not yet
done), and which past runs are not comparable on cost.
