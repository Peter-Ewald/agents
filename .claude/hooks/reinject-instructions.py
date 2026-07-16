#!/usr/bin/python3
"""PreCompact / SessionStart(compact) / PostToolUse hook.

Re-injects the shared Claude Code instructions (CLAUDE.md + instructions.md) in three cases:
- PreCompact / SessionStart(compact): the original reason this hook exists — it's undocumented
  whether Claude Code's own automatic post-compaction re-injection of a project's root CLAUDE.md
  re-resolves an @instructions.md import or just replays the literal line — this hook makes that
  question irrelevant by re-injecting the resolved content explicitly either way.
- PostToolUse (matcher Edit|Write) on CLAUDE.md or instructions.md themselves: these two files are
  "always loaded" in spirit, but nothing re-reads them mid-session after we edit them ourselves.
  Unlike a skill (fixed via "Skill freshness" — invoke fresh via the Skill tool), there's no
  equivalent re-invoke mechanism for the core convention files, so a direct edit needs its own
  reinjection or the editing session itself keeps working off a stale in-context copy.

Hardcodes /usr/bin/python3 (the system interpreter) rather than relying on env/PATH, since hooks can
fire with whatever cwd/venv happens to be active in the calling session.
"""

import json
import sys
from pathlib import Path

CLAUDE_MD = Path.home() / "Projects/agents/CLAUDE.md"
INSTRUCTIONS_MD = Path.home() / "Projects/agents/instructions.md"
WATCHED_PATHS = {str(CLAUDE_MD.resolve()), str(INSTRUCTIONS_MD.resolve())}


def resolved_content() -> str:
    claude_md_lines = [
        line
        for line in CLAUDE_MD.read_text().splitlines()
        if not line.strip().startswith("@")
    ]
    return "\n".join(claude_md_lines).strip() + "\n\n" + INSTRUCTIONS_MD.read_text()


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}
    hook_event_name = event.get("hook_event_name", "SessionStart")

    if hook_event_name == "PostToolUse":
        if event.get("tool_name") not in ("Edit", "Write"):
            sys.exit(0)
        try:
            edited = str(
                Path(event.get("tool_input", {}).get("file_path", "")).resolve()
            )
        except Exception:
            sys.exit(0)
        if edited not in WATCHED_PATHS:
            sys.exit(0)
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            "CLAUDE.md/instructions.md was just edited directly — re-injecting the resolved "
                            "content now so this session's own understanding doesn't drift from what the file "
                            "actually says:\n\n" + resolved_content()
                        ),
                    }
                }
            )
        )
        sys.exit(0)

    content = resolved_content()
    # PreCompact does not support hookSpecificOutput — inject via systemMessage
    # so the instructions are available to Claude during the compaction prompt.
    # SessionStart uses hookSpecificOutput.additionalContext (the normal path).
    if hook_event_name == "PreCompact":
        output: dict = {"systemMessage": content}
    else:
        output = {
            "hookSpecificOutput": {
                "hookEventName": hook_event_name,
                "additionalContext": content,
            }
        }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
