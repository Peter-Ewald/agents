"""The predictor the offline evaluation runs: plays each dataset item through the agent.

A run file names this class in `predictor_adapter` as `evaluation.predictor:AgentPredictor`.
`evaluation/run.py` builds it with the run's `run_config`, the configuration under test
(a model deployment, a reasoning effort, a feature switch), and the predictor hands each
value the agent understands to the agent. Each item becomes one traced agent turn; the
trace id goes on the record, which is how Langfuse links the scores to the turn.
"""

from __future__ import annotations

from collections.abc import Mapping

from semantic_evaluation.contracts import EvaluationItem, PredictionRecord
from semantic_tracing import flush, get_trace_id, setup_tracing, step

from my_agent import handle  # the agent's entry point


@step("agent_turn")
def _turn(message: str, run_config: Mapping) -> tuple[dict, str | None]:
    """One agent turn, inside its own trace, with that trace's id."""
    # Pass on the configuration keys the agent takes, for example
    # handle(message, reasoning_effort=run_config.get("reasoning_effort")).
    return handle(message), get_trace_id()


class AgentPredictor:
    name = "agent"

    def __init__(self, run_config: Mapping | None = None) -> None:
        self.run_config = dict(run_config or {})
        # Only when the project does not set tracing up elsewhere; otherwise call
        # the project's own setup here instead.
        setup_tracing(service_name="my-agent-evaluation", environment="evaluation")

    async def predict_items(
        self, items: list[EvaluationItem]
    ) -> list[PredictionRecord]:
        records = []
        for item in items:
            prediction, trace_id = _turn(item.input["message"], self.run_config)
            records.append(
                PredictionRecord(
                    item_id=item.item_id,
                    scope=item.scope,
                    dataset_name=item.dataset_name,
                    predictor_name=self.name,
                    input=item.input,
                    expected_output=item.expected_output,
                    prediction=prediction,
                    trace_id=trace_id,
                )
            )
        flush()
        return records
