#!/usr/bin/python3
"""PreCompact / SessionStart(compact) hook.

Re-injects the shared Claude Code instructions (CLAUDE.md + instructions.md) after
compaction. It's undocumented whether Claude Code's automatic post-compaction
re-injection of a project's root CLAUDE.md re-resolves an @import line or just replays
the literal text, so this re-injects the actual resolved content explicitly, independent
of that behavior either way.

Hardcodes /usr/bin/python3 (the system interpreter) rather than relying on env/PATH,
since hooks can fire with whatever cwd/venv happens to be active in the calling session.
"""
import json
import sys
from pathlib import Path

CLAUDE_MD = Path.home() / "Projects/agents/CLAUDE.md"
INSTRUCTIONS_MD = Path.home() / "Projects/agents/instructions.md"


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}
    hook_event_name = event.get("hook_event_name", "SessionStart")

    claude_md_lines = [
        line
        for line in CLAUDE_MD.read_text().splitlines()
        if not line.strip().startswith("@")
    ]
    content = "\n".join(claude_md_lines).strip() + "\n\n" + INSTRUCTIONS_MD.read_text()

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": hook_event_name,
                    "additionalContext": content,
                }
            }
        )
    )


if __name__ == "__main__":
    main()
