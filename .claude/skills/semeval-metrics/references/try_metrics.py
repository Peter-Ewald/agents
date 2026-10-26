"""Scores a few hand-made cases with the metrics a run file resolves to, before relying on them.

    uv run python try_metrics.py cases.json --run-file evaluation/runs/regression.yaml \
        [--manifest evaluation/evaluation_manifest.yaml] [--metric tone --metric refunded_orders]

`cases.json` is a list of cases, each the agent's real output on one input with what it
should have done:

    [{"id": "polite-refund", "scope": "end_to_end", "should_pass": true,
      "input": {...}, "expected_output": {...}, "prediction": {...}}]

Write at least one case that must pass and one that must fail per metric. A metric that
scores both the same is configured wrong (a field name, a parameter), or checks nothing.
Nothing is published to Langfuse; the scoring service only scores. Its URL is
OFFLINE_SCORING_BASE_URL, from the environment or `.env`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from semantic_evaluation.contracts import (
    EvaluationItem,
    EvaluationItemMetadata,
    PredictionRecord,
    ScoreRequest,
)
from semantic_evaluation.orchestration.config import load_resolved_run_manifest
from semantic_evaluation.scoring import ScoringServiceClient


def main() -> int:
    parser = argparse.ArgumentParser(prog="try_metrics")
    parser.add_argument("cases", type=Path)
    parser.add_argument("--run-file", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path, default=Path("evaluation/evaluation_manifest.yaml")
    )
    parser.add_argument(
        "--metric", action="append", default=[], help="Only these metrics."
    )
    args = parser.parse_args()
    load_dotenv()

    manifest, _ = load_resolved_run_manifest(args.run_file, args.manifest)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    evaluators = {}
    for scope, config in manifest.evaluators.items():
        metrics = {
            name: metric
            for name, metric in config.metrics.items()
            if not args.metric or name in args.metric
        }
        if metrics:
            evaluators[scope] = config.model_copy(update={"metrics": metrics})
    if not evaluators:
        raise SystemExit(f"No metric of {args.metric} in {args.run_file}.")

    items, predictions = [], []
    for case in cases:
        common = {
            "item_id": case["id"],
            "scope": case["scope"],
            "dataset_name": "try_metrics",
            "input": case["input"],
            "expected_output": case["expected_output"],
        }
        items.append(EvaluationItem(**common, metadata=EvaluationItemMetadata()))
        predictions.append(
            PredictionRecord(
                **common, predictor_name="try_metrics", prediction=case["prediction"]
            )
        )

    client = ScoringServiceClient(base_url=os.environ["OFFLINE_SCORING_BASE_URL"])
    response = asyncio.run(
        client.score(
            ScoreRequest(
                items=items,
                predictions=predictions,
                evaluators=evaluators,
                scopes=sorted({case["scope"] for case in cases}),
            )
        )
    )
    should_pass = {case["id"]: case.get("should_pass") for case in cases}
    surprises = 0
    for result in sorted(
        response.metric_results, key=lambda r: (r.metric_name, r.item_id)
    ):
        expected = should_pass.get(result.item_id)
        surprise = (
            expected is not None
            and result.passed is not None
            and result.passed != expected
        )
        surprises += surprise
        print(
            f"{'UNEXPECTED ' if surprise else ''}{result.metric_name:28} {result.item_id:28} "
            f"score={result.normalized_score}  passed={result.passed}  "
            f"{(result.justification or '')[:150]}"
        )
    print(f"\n{surprises} result(s) not as the cases expect.")
    return 1 if surprises else 0


if __name__ == "__main__":
    raise SystemExit(main())
