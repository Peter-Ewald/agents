#!/usr/bin/python3
"""PostToolUse hook (matcher: Edit|Write) — runs `ruff check --fix` (safe fixes only —
never --unsafe-fixes) then `ruff format` on a just-edited Python file, whole-file, before
lint-changed-lines.py's block-check runs. Fix runs BEFORE format, not after: removing an
unused import can leave blank lines behind that only `ruff format` cleans up, so
formatting first would leave that cleanup stranded until the next edit. Whole-file rather
than changed-lines-scoped because ruff has no partial-file/line-range autofix mode (it's
AST/statement-based, not a text-range patcher) — and safe fixes are safe precisely because
they can't change program behavior, so whole-file scope costs only extra diff noise, not
correctness risk.

Never blocks (always exits 0) — this hook only fixes; lint-changed-lines.py is the one
that gates. Fails open (does nothing) if uvx/ruff aren't available or anything else goes
wrong, same as every other hook in this repo.

Registered ahead of lint-changed-lines.py in settings.json so its fixes land first, but
hook execution order for hooks sharing one matcher is undocumented — lint-changed-lines.py
re-derives everything fresh from disk on every run with no cached state, so order affects
only how much friction an edit hits before landing a clean file, never whether a block
verdict was ever actually wrong.
"""

import difflib
import json
import subprocess
import sys
from pathlib import Path

UVX = str(Path.home() / ".local/bin/uvx")


def ruff_violation_count(file_path: str):
    try:
        result = subprocess.run(
            [UVX, "ruff", "check", "--output-format=json", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not result.stdout.strip():
            return 0
        return len(json.loads(result.stdout))
    except Exception:
        return None


def lines_changed(before: str, after: str) -> int:
    if before == after:
        return 0
    sm = difflib.SequenceMatcher(a=before.splitlines(), b=after.splitlines())
    return sum(
        max(i2 - i1, j2 - j1)
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag != "equal"
    )


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("tool_name") not in ("Edit", "Write"):
        sys.exit(0)

    file_path = event.get("tool_input", {}).get("file_path", "")
    if not file_path.endswith(".py"):
        sys.exit(0)

    try:
        before_fix_count = ruff_violation_count(file_path)
        subprocess.run(
            [UVX, "ruff", "check", "--fix", file_path], capture_output=True, timeout=30
        )
        after_fix_count = ruff_violation_count(file_path)
        after_fix = Path(file_path).read_text()

        subprocess.run(
            [UVX, "ruff", "format", file_path], capture_output=True, timeout=30
        )
        after_format = Path(file_path).read_text()
        formatted_lines = lines_changed(after_fix, after_format)
    except Exception:
        sys.exit(0)  # uvx/ruff unavailable, file vanished, etc. — fail open

    if before_fix_count is None or after_fix_count is None:
        resolved_note = "an unknown number of"
    else:
        resolved_note = str(max(before_fix_count - after_fix_count, 0))

    if formatted_lines == 0 and resolved_note in ("0", "an unknown number of"):
        sys.exit(0)  # nothing changed — stay silent, no noise

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"ruff-autofix: `ruff format` reformatted {formatted_lines} line(s) and "
                        f"`ruff check --fix` (safe fixes only) resolved {resolved_note} issue(s) "
                        f"in {file_path}, beyond your intended edit. Review the full diff before "
                        "committing."
                    ),
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
