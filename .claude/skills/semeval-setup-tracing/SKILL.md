---
name: semeval-setup-tracing
description: Sets up production tracing to Langfuse for an LLM agent, chatbot or LLM workflow with the semantic-tracing SDK, in a project with Microsoft Agent Framework, LangChain or plain Python calling a model. Use it when asked to add tracing, observability, Langfuse, token or cost tracking, or user and session tracking to an agent, or when its traces miss model calls, tokens, cost or users. Covers one setup module called at startup, spans on the entry points, every model call as a generation with usage, user and session ids, the input filter, and checking one real trace and its cost. Not for evaluation datasets or runs; that is semeval-setup-evaluation.
---

# Set up tracing for an agent

The end state: one module sets tracing up once at startup; every agent turn is one trace
with a span per step that matters and a generation per model call carrying its model and
token usage; the trace names its user and session without personal data; and one real
trace has been read back from Langfuse, with its cost or with the reason it has none.

Facts are in the docs `semantic-tracing` ships; read the page before writing the code it
covers:

```bash
uv run python -m semantic_tracing.docs show tracing/01-tracing-setup   # or: uv run eval-docs show ...
```

| Page | Covers |
|---|---|
| `tracing/01-tracing-setup` | `setup_tracing` and every parameter: environments, sampling, span drops, local capture |
| `tracing/02-tracing-observations` | `@step`, `span()`, `propagate()` (user, session, tags), `update_current_step()` |
| `tracing/03-tracing-generation` | A model call as a generation: model, usage, streaming |
| `tracing/04-tracing-input-capture` | What gets captured, the global input filter, sensitive data |
| `tracing/05-tracing-frameworks` | Microsoft Agent Framework and LangChain: what they emit, what to drop, usage buckets |
| `tracing/06-tracing-example-maf`, `tracing/06-tracing-example-langchain` | A whole project of each kind |
| `tracing/10-tracing-session-sampling` | Session ids and sampling by session |

## 1. Find what the project has

- **The framework.** Microsoft Agent Framework (`agent_framework` imports), LangChain
  (`langchain`), or plain Python calling a provider SDK (`openai`, `AzureOpenAI`). Each is
  traced differently; the matching `05`/`06` page says how.
- **Tracing already there.** Search for `setup_tracing`, `langfuse`, `opentelemetry`. If
  `semeval-setup-evaluation` added the minimum (a `setup_tracing` call in
  `evaluation/predictor.py`, `@step` on the turn), extend it: the project ends with one
  setup, called by the agent and by the predictor, never two.
- **Where the process starts**: the web app's startup, the CLI's `main`, the worker. That is
  where setup is called, before any framework object is built.
- **Every model call**, and where it goes through. A project with one client module (the
  team rule) has one place to trace generations.

## 2. Install

`uv add semantic-tracing`, with the internal index and `prerelease = "allow"` in
`uv.toml` as `semeval-setup-evaluation/references/uv.toml` has them. A project that has
`semantic-evaluation` already has it.

## 3. One setup module

Write `telemetry/setup.py` (or the project's equivalent) from `references/telemetry_setup.py`:
`setup_tracing` with the project's `service_name`, an `environment` read from the
environment, and:

- **An input filter** (`InputFilter`) for arguments that are not data: framework contexts,
  clients, connections, large binary inputs (`04-tracing-input-capture`).
- **The framework's span drops**, as its `05` section lists them. Drop what nobody reads;
  keep the spans a person debugging a wrong answer would open.
- **`capture_local_traces=True`** when an evaluation reads trace metrics from this process.
- **`require_langfuse`**: strict (the default) in production; `False` only where a missing
  key must not stop the program, such as unit tests.

Call it once, at startup. Do not call it at import time of a library module.

## 4. Spans and generations

- **`@step` on the turn's entry point** and on each step a person would want to see
  separately (retrieval, a tool, a sub-agent). Not on every helper: a trace is read by
  people, and every observation is billed.
- **Every model call is a generation**: `@step(..., as_type="generation")` or
  `span(..., as_type="generation")`, then `update_current_step(model=..., usage_details=...,
  model_parameters=...)` (`03-tracing-generation`). Agent Framework and LangChain emit their
  own; plain Python must do it.
- **`model` is the model the provider reports** (`response.model`), not a deployment alias,
  because Langfuse prices a generation by matching that name.
- **Usage buckets must not overlap**: `input` without the cached tokens,
  `input_cached_tokens`, `output` without the reasoning tokens, `output_reasoning_tokens`.
  A provider counts cached input inside input and reasoning inside output; passed on as
  they are, Langfuse charges them twice (`05-tracing-frameworks`, Token usage and cost).

## 5. Users and sessions

`propagate(user_id=..., session_id=...)` around a turn (`02-tracing-observations`). Use an
internal id or a hash, never a name, an email address or anything else that identifies a
person: no personal data goes into a trace. A conversation's turns share one session id.

## 6. Environment variables

Add `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_BASE_URL` (and the
environment variable the setup reads) to `.env.example`, names only. The values go in the
gitignored `.env`; never read, print or commit it. If `.env` lacks one, ask the person.

## 7. Check one real trace

Run one turn the way the project runs (its CLI, a request to its app), then read that
trace back once Langfuse has settled, with `references/check_trace.py`:

```bash
# from the project root, so it uses the project's environment and reads its .env
uv run python <this skill's folder>/references/check_trace.py <trace id>
```

The trace id is `get_trace_id()` inside the turn, or the newest trace in Langfuse.

It prints each observation with its type, model, usage and cost, the trace's total cost,
and what is missing. Fix what it names:

| It says | Meaning | Do |
|---|---|---|
| No generation | A model call is not traced as one | Step 4 |
| A generation without usage | `usage_details` not set, or the framework reports none | Step 4; for a framework, its `05` section |
| Usage but no cost | Langfuse has no price for that model name. Common for Azure deployments | Load `semeval-model-pricing`; never invent a price |
| A cost, for an Azure deployment that is not Global Standard | Probably Langfuse's own definition at the provider's list price, which is below Azure's for a Data Zone or regional deployment | Load `semeval-model-pricing` |
| A user or session missing | `propagate` is not around the turn | Step 5 |

## Report back

Say where tracing is set up, what each turn's trace now contains, the checked trace's
link (`{LANGFUSE_BASE_URL}/project/<project>/traces/<trace id>`, or its id) with its cost,
what was dropped or filtered and why, and what is left: an unpriced model, keys missing
from `.env`, a framework span still noisy.
