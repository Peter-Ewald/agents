# Implementer tiers

| Tier | Agent | Model, effort | Typical work |
|---|---|---|---|
| light | `implementer-light` | Haiku, low | Mechanical, fully specified edits; locating code; condensing a large payload |
| medium | `implementer-medium` | Sonnet, medium | A sub-task with a fixed contract and frozen tests; tests from acceptance cases; doc rewrites of touched code |
| strong | `implementer-strong` | Opus, high | Root-cause debugging, risky refactors, whole-repo doc sweeps, independent review |

Built-in agents such as `Explore` keep their own definition and take the tier through the Agent tool's
`model` parameter (`haiku`, `sonnet`, `opus`).

> Pick the cheapest tier that can do the sub-task well, never a cheaper one. Saving on a sub-task that
> needs judgment costs more in failed runs, review and rework than the stronger tier would have. Paying
> for a stronger tier than the sub-task needs buys nothing.

## Mapping task types to tiers

Start from the default and move one step on the signals in the second table.

| Task type | Default | Move down to | Move up to |
|---|---|---|---|
| Mechanical edit to a fixed pattern (rename, version pins, one lint rule across files) | light | | medium if the tests fail for a reason that is not obvious |
| Locate code (`Explore`) | light | | medium across many naming conventions |
| Condense a large payload (trace, log, long diff) | light | | |
| Tests and eval items from acceptance cases (`test-author`) | medium | | strong: concurrency, auth, migrations, published SDK API |
| Implement a sub-task with a fixed contract and frozen tests | medium | light: one file, contract given as a signature and behaviour | strong: concurrency, auth, migrations, published SDK API |
| Refactor across many files, behaviour unchanged | medium | | strong if the area has few tests |
| Debug an unexplained failure | strong | medium if the failing test points at the line | |
| Rewrite READMEs and docstrings of code the wave touched | medium | light: a single factual claim | |
| Documentation sweep (`doc-sweep`) | medium for one path | | strong for a whole repo or a restructuring |
| Research with synthesis (release notes, docs, web) | medium | | strong when the result decides an architecture choice |
| Review of the wave's diff before the done check | strong | medium for a simplification pass only | |
| Design and architecture | not delegated | | strong only as a second opinion on the finished plan |

| Signal | Points to a lighter tier | Points to a stronger tier |
|---|---|---|
| Contract in the plan | Names, signatures and data shapes all fixed | Parts still open |
| Owned files | One or two | Many, or shared modules |
| Acceptance check | Mechanical: tests and lint exist | Needs judgment, or no tests |
| Blast radius | Private module, easy to revert | Published SDK API, service contract, data, security |
| Earlier attempt | | A lower tier reported `blocked` or a failing check |

## Escalation rule

After a `blocked` report or a failed check, brief the sub-task again **one tier up**, once, with what the
first attempt's report says it learned. Never retry the same tier with the same brief, and never resume the
failed agent. If the strong tier blocks too, the problem is in the plan: the wave stops with `blocked`.
