"""Reads one trace back from Langfuse and says what it holds and what is missing.

    uv run python check_trace.py <trace id>

Waits until Langfuse has settled the trace (three agreeing reads, five seconds apart,
at most two minutes): Langfuse ingests a turn's observations out of order and prices them
afterwards, so a trace read at once can lack generations and cost. The keys come from
the environment or `.env` in the current folder.
"""

from __future__ import annotations

import sys
import time

from dotenv import load_dotenv
from langfuse import get_client


def _state(trace) -> tuple:
    observations = trace.observations or []
    return (
        len(observations),
        trace.total_cost,
        tuple(sorted((o.id, o.calculated_total_cost) for o in observations)),
    )


def settled_trace(
    trace_id: str, *, reads: int = 3, pause: float = 5.0, limit: float = 120.0
):
    client = get_client()
    deadline = time.monotonic() + limit
    trace, agreeing = None, 0
    while time.monotonic() < deadline:
        try:
            again = client.api.trace.get(trace_id)
        except Exception:  # noqa: BLE001 - not there yet is a 404
            again = None
        if again is not None and trace is not None and _state(again) == _state(trace):
            agreeing += 1
            if agreeing >= reads:
                return again
        else:
            agreeing = 1 if again is not None else 0
        trace = again
        time.sleep(pause)
    if trace is None:
        raise SystemExit(f"Langfuse has no trace {trace_id} after {limit:.0f} s.")
    print(f"note: the trace was still changing after {limit:.0f} s", file=sys.stderr)
    return trace


def main(trace_id: str) -> int:
    load_dotenv()
    trace = settled_trace(trace_id)
    print(
        f"trace {trace.id}  name={trace.name}  user={trace.user_id}  session={trace.session_id}"
    )
    print(f"total cost: {trace.total_cost}")
    problems = []
    generations = []
    for observation in sorted(trace.observations or [], key=lambda o: o.start_time):
        kind = str(observation.type)
        print(
            f"  {kind:<11} {observation.name}  model={observation.model}  "
            f"usage={observation.usage_details or {}}  cost={observation.calculated_total_cost}"
        )
        if kind == "GENERATION":
            generations.append(observation)
    if not generations:
        problems.append("no generation: a model call is not traced as one")
    for generation in generations:
        if not generation.model:
            problems.append(f"generation {generation.name} has no model")
        if not generation.usage_details:
            problems.append(f"generation {generation.name} has no usage")
        elif not generation.calculated_total_cost:
            problems.append(
                f"generation {generation.name} has usage but no cost: Langfuse has no price "
                f"for model {generation.model!r}"
            )
    if not trace.user_id:
        problems.append("no user id")
    if not trace.session_id:
        problems.append("no session id")
    print(
        "\n".join(["missing:", *(f"  - {p}" for p in problems)])
        if problems
        else "nothing missing"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(sys.argv[1]))
