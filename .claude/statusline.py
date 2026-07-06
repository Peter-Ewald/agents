#!/usr/bin/python3
"""Statusline script. Prints the current wave and phase if the `wave` skill has written
one for this session, otherwise prints nothing (no wave in progress).

The wave-phase file lives at /tmp/claude-wave-phase-<session_id> — a fixed path derived
only from the session ID, since this script and the `wave` skill run as separate
processes that don't share any other state.
"""
import json
import sys
from pathlib import Path


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    session_id = event.get("session_id")
    if not session_id:
        return
    phase_file = Path(f"/tmp/claude-wave-phase-{session_id}")
    if phase_file.exists():
        print(phase_file.read_text().strip())


if __name__ == "__main__":
    main()
