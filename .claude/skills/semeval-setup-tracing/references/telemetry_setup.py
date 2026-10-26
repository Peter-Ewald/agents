"""Tracing for the whole process: call `initialize_telemetry()` once, at startup.

The agent's entry point, its CLI and the evaluation's predictor all call it; only the
first call sets tracing up. The Langfuse keys come from the environment
(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL), and APP_ENVIRONMENT names
the Langfuse environment the traces go to.
"""

from __future__ import annotations

import os

from semantic_tracing import InputFilter, flush, setup_tracing

_initialized = False


def initialize_telemetry() -> None:
    global _initialized
    if _initialized:
        return
    setup_tracing(
        service_name="my-agent",
        environment=os.environ.get("APP_ENVIRONMENT", "development"),
        # Arguments that are not data: never captured as a span's input.
        input_filter=InputFilter(
            exclude_arg_names=["self", "client", "ctx"],
        ),
        # Microsoft Agent Framework: its workflow spans, as tracing/05-tracing-frameworks
        # lists them. LangChain and plain Python: leave both out.
        # drop_span_names=[...],
        # drop_span_name_prefixes=[...],
        # When an evaluation in this process reads trace metrics from local traces.
        # capture_local_traces=True,
    )
    _initialized = True


def flush_telemetry() -> None:
    """Send what is buffered; call before a short-lived process exits."""
    flush()
