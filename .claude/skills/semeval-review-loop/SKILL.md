---
name: semeval-review-loop
description: Sets up and runs human review of an LLM agent's traces in Langfuse, so reviewed and corrected answers become evaluation dataset items, with Langfuse annotation queues, score configs and the review-sync service (eval-review). Use it when asked to let domain experts or reviewers check, score or correct the agent's answers, to set up annotation queues or a review queue, to turn reviewed or corrected production traces into dataset items, to register a review binding or Langfuse profile with the review-sync service, to run or schedule a review sync, or when a sync fails, for example with 404 "Annotation queue not found" or with items not promoted. Not for writing dataset items by hand (semeval-maintain, semeval-datasets).
---

# Human review into the dataset

The end state: per scope that needs it, a Langfuse annotation queue with the score configs
reviewers give; the project's Langfuse profile registered with the review-sync service; a
binding file in `evaluation/review/` registered with the service; a dry-run and a real sync
that promote completed reviews into the scope's dev dataset; and the person knows the
routine from here.

```bash
uv run eval-docs show evaluation/06-review-sync      # Setting up review in Langfuse, the eval-review command, When a sync fails
uv run eval-docs show review-sync-service/01-bindings
uv run eval-docs show access-and-credentials          # REVIEW_SYNC_API_KEY
```

## 1. Decide what is reviewed

With the person, per scope: which turns get reviewed (sampled production traces, low
scores from a run, user complaints), and which **observation** a queue item is. The binding
reads that object's input and output, so queue the observation whose input and output are
the scope's: the root trace for `end_to_end`, a step's span for a step's scope. Read
`evaluation/coverage.md` for the scopes and what `expected_output` holds; the reviewer
will correct exactly those fields.

## 2. Queues and score configs

One queue per scope, named `<product>-<scope>-review`, and one score config per judgement
the reviewer gives (`NUMERIC`, 1 to 5, a name a reviewer understands: "Correct tool
calls", "Correct reply"), attached to the queue. Create them in the Langfuse UI or through
the API (`06-review-sync`, Setting up review in Langfuse); with the API, note the ids it
returns. The queue id is the queue's, never an item's.

The score config names go into the binding's `review_policy.required_score_names`
exactly. Tell the person what a reviewer does: open the queue, score each item, write a
corrected output whenever a score is 3 or lower, and mark the item complete.

## 3. Register the project's Langfuse profile

Once per Langfuse project. It needs `REVIEW_SYNC_API_KEY` in `.env`; if it is missing, ask
the person (the access page says where it comes from; the contact is Peter Ewald, Teams or
`peter.ewald@ramboll.com`).

```bash
uv run eval-review profiles                              # already registered?
uv run eval-review register-profile --profile-id <product>
```

It sends the project's Langfuse keys from `.env`. Never read or print `.env` to see what it
holds: `eval-review` names any variable that is missing, and the person adds it.

## 4. The binding file

`evaluation/review/<scope>.binding.yaml`, from `references/binding.yaml`:

- `queue_id`, `langfuse_profile_id`, `dataset_scope`, `product_id`;
- `dataset_target.name`: the scope's dev dataset from the manifest's
  `dataset_sync.scope_to_dataset`, so reviewed items join the curated ones;
- the schemas and projections: **read one real queue item first** (add a trace, or ask the
  person to) and map its paths (`original_input.*`, `selected_output.*`) to the fields the
  scope's items have. `selected_output` is the reviewer's corrected output when there is
  one, the agent's otherwise. An `expected_output` field the agent's output does not
  contain (an expected tool call list, say) needs the reviewer to write it in the
  corrected output; say so to the person.

## 5. Validate, then register

```bash
uv run eval-review validate evaluation/review/<scope>.binding.yaml
uv run eval-review register-binding evaluation/review/<scope>.binding.yaml
```

Re-registering the same `binding_id` replaces the binding; that is how it is changed.

## 6. Dry run, then sync

```bash
uv run eval-review sync --file evaluation/review/<scope>.binding.yaml --dry-run
uv run eval-review sync --file evaluation/review/<scope>.binding.yaml
```

Read the dry run's summary first: `completed_reviewed_items`, `promotable_items`,
`policy_skipped_items` and each outcome's message. Sync for real only when it promotes
what the reviews say it should. A sync promotes each reviewed version once, so running it
again is safe.

When it fails, `06-review-sync` (When a sync fails) has the causes. `404 Annotation queue
not found` has three, checked in this order: an item id used as the queue id, a binding
naming the wrong profile, a queue recreated since the binding was registered.

## 7. After the sync

- The promoted items are in the dev dataset. Pull it and check two of them against their
  traces (`semeval-datasets`); they count toward the next release.
- The coverage map: which behaviours the reviewed items prove, and that the scope is
  maintained through review.
- How often to sync is the person's choice (after each review session, or on a schedule
  their CI runs); `eval-review sync` is the whole command.

## Report back

The queues and score configs and their ids, the profile id, the binding files, the dry run
and real sync summaries, the dataset the items went into, what a reviewer does, and what
is left: items to review, a key to get, a release to make.
