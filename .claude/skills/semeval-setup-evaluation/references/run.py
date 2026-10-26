"""Runs one offline evaluation of the agent, publishes it to Langfuse and prints its report.

    uv run python -m evaluation.run                                   # the regression run
    uv run python -m evaluation.run --fail-on-gate                    # in CI
    uv run python -m evaluation.run --run-file evaluation/runs/<run>.yaml --run-label <label> \
        --config reasoning_effort=high --repeats 3                    # one configuration of an experiment

Run from the project root, so `predictor_adapter` imports. The Langfuse keys and the
scoring service's URL come from `.env` there. `--config` values reach the agent through
the predictor, and label the run in Langfuse.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from semantic_evaluation.orchestration.config import load_resolved_run_manifest
from semantic_evaluation.orchestration.reporting.run_report import (
    load_run_report,
    render_markdown,
)
from semantic_evaluation.orchestration.runner import (
    execute_offline_evaluation,
    resolve_predictor_class,
    resolve_run_config,
)

EVALUATION = Path(__file__).resolve().parent


def _config_value(text: str) -> str | int | float | bool:
    """`true`, `3` and `0.5` as the type they read as; anything else as text."""
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            pass
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.run")
    parser.add_argument(
        "--run-file", type=Path, default=EVALUATION / "runs" / "regression.yaml"
    )
    parser.add_argument(
        "--run-label", help="The experiment label in the Langfuse run name."
    )
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="One setting of the configuration under test; repeat for several.",
    )
    parser.add_argument(
        "--repeats", type=int, help="Predict each item this many times."
    )
    parser.add_argument(
        "--fail-on-gate", action="store_true", help="Exit 1 when the gate fails."
    )
    arguments = parser.parse_args(argv)

    load_dotenv(EVALUATION.parent / ".env")
    scoring = os.environ.get("OFFLINE_SCORING_BASE_URL")
    if not scoring:
        print(
            "OFFLINE_SCORING_BASE_URL names no scoring service; set it in .env.",
            file=sys.stderr,
        )
        return 2
    overrides = {}
    for setting in arguments.config:
        key, separator, value = setting.partition("=")
        if not separator or not key:
            parser.error(f"--config takes KEY=VALUE, got {setting!r}")
        overrides[key] = _config_value(value)

    manifest, run_path = load_resolved_run_manifest(
        arguments.run_file, EVALUATION / "evaluation_manifest.yaml"
    )
    run_config = resolve_run_config(manifest.run_config, overrides)
    result = asyncio.run(
        execute_offline_evaluation(
            manifest=manifest,
            manifest_path=run_path,
            scope_override=None,
            run_label=arguments.run_label,
            scoring_service_base_url=scoring,
            scoring_service_timeout_seconds=float(
                os.environ.get("OFFLINE_SCORING_TIMEOUT_SECONDS", "120")
            ),
            outputs_dir=EVALUATION / "outputs",
            run_config=run_config,
            repeats=arguments.repeats,
            predictor=resolve_predictor_class(manifest)(run_config=run_config),
        )
    )
    run_dir = Path(result.summary["artifact_paths"]["run_summary"]).parent
    print(render_markdown([load_run_report(run_dir)]))
    if not result.publication_succeeded:
        print(
            f"Langfuse publication failed: {result.publication_error}", file=sys.stderr
        )
        return 1
    return 1 if arguments.fail_on_gate and not result.gate_passed else 0


if __name__ == "__main__":
    raise SystemExit(main())
