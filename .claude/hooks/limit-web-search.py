#!/usr/bin/python3
"""Web search rate limit, two modes selected by argv[1]:

  reset  - UserPromptSubmit, SubagentStart: zero the per-round counter.
  check  - PreToolUse (matcher: WebSearch): increment the counter, block the 11th call
           in a round with a hard stop (exit 2) rather than a soft warning.

A "round" runs from one handoff to the next: a new user prompt, or a new subagent task,
until that agent reports back. Scoped to the WebSearch tool specifically, not WebFetch.
"""
import json
import sys
import tempfile
from pathlib import Path

LIMIT = 10


def counter_path(event: dict) -> Path:
    session_id = event.get("session_id", "unknown-session")
    agent_id = event.get("agent_id", "main")
    return Path(tempfile.gettempdir()) / f"claude-search-count-{session_id}-{agent_id}"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}

    path = counter_path(event)

    if mode == "reset":
        path.write_text("0")
        sys.exit(0)

    if event.get("tool_name") != "WebSearch":
        sys.exit(0)

    try:
        count = int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        count = 0
    count += 1
    path.write_text(str(count))

    if count > LIMIT:
        print(
            f"{LIMIT} web searches already used this round. Report findings back to "
            "the user (or parent agent) before continuing, or ask for more budget "
            "explicitly, rather than continuing to search.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
