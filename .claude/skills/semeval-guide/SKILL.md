---
name: semeval-guide
description: Answers questions about the semantic-evaluation and semantic-tracing Python SDKs, the shared scoring and review-sync services, Langfuse datasets and dataset runs, and how to get access (Artifactory token, VPN, Langfuse keys, service API keys, LLM-judge connection profiles). Use it when someone asks how something in this evaluation system works, where a setting is documented, whom to ask for a key, or when an install, a dataset command or an evaluation run fails with an error such as HTTP 401 from artifactory.ramboll.com, HTTP 401 "Invalid or missing API key", HTTP 400 for an LLM-judge metric, RunManifestResolutionError, a refused predictor_adapter, or a prediction missing trace_id.
---

# Questions and errors about the evaluation system

Answer from the documentation the installed packages ship, not from memory. The pages match
the installed version and need no network:

```bash
uv run eval-docs list                     # every page, by name and title
uv run eval-docs show run-config          # one page; a unique part of its name is enough
uv run eval-docs search "predictor_adapter"   # matching lines, as page:line: text
uv run eval-docs version                  # installed versions, and the commit the docs come from
```

`eval-docs` comes with `semantic-evaluation`; in a project that has only `semantic-tracing`,
use `uv run python -m semantic_tracing.docs` with the same subcommands. If neither is
installed, say so and offer to add the package (load `semeval-setup-evaluation`).

Quote the page you answer from (`eval-docs show <page>` names it), so the person can read on.

## The system in one table

| Part | What it owns | Where it runs |
|---|---|---|
| `semantic-tracing` | `setup_tracing`, `@step`, spans and events, framework adapters, reading traces back | In the project, a package from Artifactory |
| `semantic-evaluation` | Item and run contracts, the `eval-dataset` CLI, the offline evaluation runner, clients for both services, `eval-docs` | In the project, a package from Artifactory |
| Scoring service | Which evaluators exist (`GET /evaluators`), scoring jobs, LLM-judge connection profiles | Deployed and shared; reached over the VPN |
| Review-sync service | Turning reviewed Langfuse annotation-queue items into dataset items, by a binding's policy | Deployed and shared; reached over the VPN |
| Langfuse | Traces, datasets, dataset runs and their scores, annotation queues: the single source of truth for datasets | The project's Langfuse project |

Policy belongs to the services, not to projects: which metrics exist is the scoring
service's catalogue, and how a reviewed item becomes a dataset item is the review-sync
service's. A project configures; it does not reimplement.

## Where each kind of question is answered

| Question | Page |
|---|---|
| Keys, VPN, Artifactory token, who can get what | `eval-docs show access-and-credentials` |
| Installing, the first predictor, the first run | `eval-docs show evaluation/01-getting-started` |
| `evaluation_manifest.yaml`, run files, metrics, the gate, `predictor_adapter` | `eval-docs show run-config` |
| The runner, `PredictionRunner`, repeats, `run_config`, trace metrics | `eval-docs show offline-evaluation` |
| Dataset names, `_dev` and releases, promote, archive | `eval-docs show datasets-lifecycle` |
| Every `eval-dataset` command and flag | `eval-docs show datasets-cli` |
| Item shapes (QA, RAG, Agent, RAG-Agent) | `eval-docs show schema-types` |
| Which evaluators exist and their parameters | `GET {scoring}/evaluators` live, then `eval-docs show evaluator-catalogue` for what each does |
| LLM-judge connection profiles | `eval-docs show connection-profiles` |
| Custom rubrics | `eval-docs show custom-rubric-and-registration` |
| Service URLs and routes | `eval-docs show scoring-service/04-api-reference`, `eval-docs show review-sync-service/04-api-reference` |
| Human review, annotation queues, `eval-review`, review sync | `eval-docs show evaluation/06-review-sync`, then `review-sync-service/01-bindings` |
| Tracing setup | `eval-docs show tracing/01-tracing-setup` |
| Cost in Langfuse, model prices, Azure deployments | `eval-docs show tracing-model-prices` |
| A run's artifacts, `eval-report` | `eval-docs show offline-evaluation`, sections Run artifacts and Reporting runs |
| A term | `eval-docs show glossary`, or `eval-docs search "<term>"` |

When the question turns into work, load the skill that does it:

| The person wants to | Skill |
|---|---|
| Set evaluation up in a project that has none | `semeval-setup-evaluation` |
| Set up or fix tracing, tokens, cost, users and sessions | `semeval-setup-tracing` |
| Price a model deployment, or fix a missing or wrong cost | `semeval-model-pricing` |
| Choose, add or change a metric, a judge, a rubric, a threshold | `semeval-metrics` |
| Compare configurations, tune, establish or promote a baseline | `semeval-experiment` |
| Set up human review, queues, bindings; run or fix a review sync | `semeval-review-loop` |
| Change the agent and keep its evaluation current | `semeval-maintain` |
| Pull, push, release or archive a dataset | `semeval-datasets` |

The evaluator list changes while the docs in a release do not, so read it from the
service, never from a copy:

```bash
curl -s "$OFFLINE_SCORING_BASE_URL/evaluators"
```

## Access: whom to ask

Everything a person can get alone is on the access page. For anything else (joining the
Langfuse organisation, a service key without Key Vault access, registering a connection
profile, choosing an Azure region) the contact is **Peter Ewald**, on Microsoft Teams or
at `peter.ewald@ramboll.com`. Name him rather than guessing at a process.

Never read, print or commit a key. Name the variable (`LANGFUSE_SECRET_KEY`,
`SCORING_SERVICE_API_KEY`) and say it belongs in the project's gitignored `.env`.

## When something fails

Check reachability first; a service that does not answer is not a bug in the project:

```bash
curl -s -m 10 "$OFFLINE_SCORING_BASE_URL/health"      # {"status":"ok"}
curl -s -m 10 "$REVIEW_SYNC_SERVICE_BASE_URL/health"
```

| Symptom | Usual cause | What to do |
|---|---|---|
| HTTP 401 from `artifactory.ramboll.com` during `uv sync` | No token in `~/.netrc`, or an expired one | The access page's Artifactory row; the token goes in `~/.netrc`, never in `uv.toml` |
| `artifactory.ramboll.com` or a service URL does not resolve or times out | Not on the VPN | Connect, then retry |
| `No solution found` for `semantic-evaluation` | The project's `uv.toml` lacks the internal index `ramtech-pypi-internal` | `eval-docs show evaluation/01-getting-started`, section Install |
| HTTP 401 `Invalid or missing API key.` | A route behind the key: connection profiles, evaluator backends, rubric registration, Langfuse profiles | Scoring and syncing need no key; only these admin routes do. The access page says who has the key |
| HTTP 400 from the scoring service for an LLM-judge metric | No connection profile registered for that evaluator backend | `eval-docs show connection-profiles`; registering one needs the scoring key, so usually ask the contact |
| `404 Annotation queue not found` | Three causes with one message: the queue *item* id was used instead of the queue id (both are in the URL `.../annotation-queues/<QUEUE_ID>/items/<ITEM_ID>`); the binding names the wrong Langfuse profile; or the queue was recreated and the binding is stale | Check them in that order; re-registering the binding with the current queue id replaces the old one. `eval-docs show evaluation/06-review-sync`, When a sync fails; `semeval-review-loop` |
| `RunManifestResolutionError` | A scope in the run file has no dataset (`scope_to_dataset` or the run's `datasets`), or resolves to no metric | `uv run eval-dataset resolve-run --run-file evaluation/runs/<run>.yaml --manifest evaluation/evaluation_manifest.yaml` shows what resolves |
| `predictor_adapter` refused when the file loads | A bare label instead of `module.path:ClassName` | Name the class, for example `evaluation.predictor:MyPredictor` |
| `... which cannot be imported` | The module of `predictor_adapter` is not importable from where the run starts | Start from the project root, or fix the module path |
| `TypeError` naming two predictor classes | The predictor passed to `execute_offline_evaluation()` is not an instance of the class the run names | Build it from `resolve_predictor_class(manifest)` |
| `Prediction for evaluation item ... is missing trace_id` | The predictor does not trace the agent call, or does not put the trace id on the record | Trace the call with `semantic_tracing` and set `trace_id=get_trace_id()`; `eval-docs show tracing/01-tracing-setup` |
| `setup_tracing(require_langfuse=True)` fails to authenticate | Wrong keys, or `LANGFUSE_BASE_URL` names another instance | `LANGFUSE_BASE_URL` is the variable the Langfuse SDK reads first; `LANGFUSE_HOST` is its old name |
| `push` refuses a dataset that does not exist | `create_on_missing` is off, which is right after the first push | Turn it on for the first push of a new dataset only (load `semeval-datasets`) |

If the cause is none of these, search the docs for the exact message
(`eval-docs search "<part of the message>"`) before reading source code.
