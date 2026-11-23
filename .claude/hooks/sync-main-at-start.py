#!/usr/bin/python3
"""SessionStart hook — brings the active repos' main checkouts up to date with `origin/main`.

Registered for the `startup`, `resume` and `clear` events (the matcher lives in the global
settings, not here); not for `compact`, which does not start new work. It runs
`sync_main_checkout` for every active repo in parallel and waits for the fetches (capped at
8 s each), so the first file the session reads is current. It reports only what moved or was
left behind, as context for the agent; it is silent when every repo was already up to date.
See `.claude/scripts/sync_main.py` for the sync rules.
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts")
)
import sync_main

HEADER = "Main checkouts synced at session start:"


def main():
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass
    paths = sync_main.active_repo_paths()
    if not paths:
        sys.exit(0)
    with ThreadPoolExecutor(max_workers=len(paths)) as pool:
        results = list(pool.map(sync_main.sync_main_checkout, paths))
    lines = [line for line in results if not line.endswith(": up to date")]
    if not lines:
        sys.exit(0)
    text = HEADER + "\n" + "\n".join(f"- {line}" for line in lines)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": text,
                }
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"sync-main-at-start: {exc}", file=sys.stderr)
        sys.exit(0)
