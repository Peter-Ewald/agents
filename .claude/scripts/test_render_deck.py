#!/usr/bin/env python3
"""Tests for render_deck.py, which renders a .pptx deck's slides to PNGs through PowerPoint.

Run with `python3 test_render_deck.py` (or pytest). Stdlib only; runs under Python 3.9. Every test
works on a copy of fixtures/three-slides.pptx in a temp dir. The tests that render need Microsoft
PowerPoint and pdftoppm and are skipped, with the reason, where either is absent.
"""

import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "render_deck.py")
FIXTURE = os.path.join(HERE, "fixtures", "three-slides.pptx")
POWERPOINT_APP = "/Applications/Microsoft PowerPoint.app"
POWERPOINT_TMP = os.path.expanduser(
    "~/Library/Containers/com.microsoft.Powerpoint/Data/tmp"
)
# 13.333 in wide at the default 100 dpi.
EXPECTED_WIDTH = 1333
WIDTH_TOLERANCE = 3

try:
    import pytest
except ImportError:
    pytest = None


class Skip(Exception):
    pass


def skip(reason):
    if pytest is not None:
        pytest.skip(reason)
    raise Skip(reason)


def needs_powerpoint():
    if not os.path.isdir(POWERPOINT_APP):
        skip(f"needs PowerPoint: {POWERPOINT_APP} is absent")
    if shutil.which("pdftoppm") is None:
        skip("needs pdftoppm (poppler): not on PATH")


def render(*args):
    assert os.path.isfile(SCRIPT), f"render_deck.py is missing: {SCRIPT}"
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )


def deck_copy(tmp):
    deck = os.path.join(tmp, "deck.pptx")
    shutil.copy2(FIXTURE, deck)
    return deck


def png_width(path):
    with open(path, "rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"not a PNG: {path}"
    assert header[12:16] == b"IHDR", f"no IHDR chunk first: {path}"
    return struct.unpack(">I", header[16:20])[0]


def render_folders():
    if not os.path.isdir(POWERPOINT_TMP):
        return set()
    return {name for name in os.listdir(POWERPOINT_TMP) if name.startswith("render-")}


def test_missing_deck_refused():
    # AC1
    tmp = tempfile.mkdtemp(prefix="render-deck-test-")
    missing = os.path.join(tmp, "missing.pptx")
    out = os.path.join(tmp, "out")
    result = render(missing, out)
    assert result.returncode == 1, (result.returncode, result.stderr)
    assert missing in result.stderr, result.stderr
    assert not os.path.exists(out), "out/ was created for a refused deck"


def test_deck_that_is_not_pptx_refused():
    # AC1 (contract: a DECK that is not a .pptx is refused the same way)
    tmp = tempfile.mkdtemp(prefix="render-deck-test-")
    deck = os.path.join(tmp, "deck.pdf")
    shutil.copy2(FIXTURE, deck)
    out = os.path.join(tmp, "out")
    result = render(deck, out)
    assert result.returncode == 1, (result.returncode, result.stderr)
    assert deck in result.stderr, result.stderr
    assert not os.path.exists(out), "out/ was created for a refused deck"


def test_bad_slide_spec_refused():
    # AC2
    tmp = tempfile.mkdtemp(prefix="render-deck-test-")
    deck = deck_copy(tmp)
    out = os.path.join(tmp, "out")
    result = render(deck, out, "--slides", "3-a")
    assert result.returncode == 2, (result.returncode, result.stderr)
    assert "3-a" in result.stderr, result.stderr


def test_whole_deck_rendered():
    # AC3
    needs_powerpoint()
    tmp = tempfile.mkdtemp(prefix="render-deck-test-")
    deck = deck_copy(tmp)
    out = os.path.join(tmp, "out")
    result = render(deck, out)
    assert result.returncode == 0, (result.returncode, result.stderr)
    lines = result.stdout.splitlines()
    expected = [
        os.path.join(os.path.realpath(out), f"slide-{n:02d}.png") for n in (1, 2, 3)
    ]
    assert [os.path.realpath(line) for line in lines] == expected, lines
    for line in lines:
        assert os.path.isabs(line), f"not an absolute path: {line}"
        assert os.path.isfile(line), f"listed but missing: {line}"
        width = png_width(line)
        assert abs(width - EXPECTED_WIDTH) <= WIDTH_TOLERANCE, (line, width)


_SLIDE_TWO_RENDER = {}


def _render_slide_two():
    """One render shared by AC4 and AC5: --slides 2 into an out/ holding an old slide-01.png."""
    if _SLIDE_TWO_RENDER:
        return _SLIDE_TWO_RENDER
    tmp = tempfile.mkdtemp(prefix="render-deck-test-")
    deck = deck_copy(tmp)
    out = os.path.join(tmp, "out")
    os.makedirs(out)
    with open(os.path.join(out, "slide-01.png"), "wb") as handle:
        handle.write(b"old render")
    with open(deck, "rb") as handle:
        bytes_before = handle.read()
    mtime_before = os.stat(deck).st_mtime_ns
    folders_before = render_folders()
    result = render(deck, out, "--slides", "2")
    with open(deck, "rb") as handle:
        bytes_after = handle.read()
    _SLIDE_TWO_RENDER.update(
        result=result,
        out=out,
        bytes_unchanged=bytes_before == bytes_after,
        mtime_before=mtime_before,
        mtime_after=os.stat(deck).st_mtime_ns,
        folders_before=folders_before,
        folders_after=render_folders(),
    )
    return _SLIDE_TWO_RENDER


def test_chosen_slides_only():
    # AC4
    needs_powerpoint()
    run = _render_slide_two()
    result = run["result"]
    assert result.returncode == 0, (result.returncode, result.stderr)
    assert sorted(os.listdir(run["out"])) == ["slide-02.png"], os.listdir(run["out"])
    listed = [os.path.realpath(line) for line in result.stdout.splitlines()]
    assert listed == [os.path.realpath(os.path.join(run["out"], "slide-02.png"))], (
        listed
    )


def test_original_deck_untouched():
    # AC5
    needs_powerpoint()
    run = _render_slide_two()
    result = run["result"]
    assert result.returncode == 0, (result.returncode, result.stderr)
    assert run["bytes_unchanged"], "the deck's bytes changed during the render"
    assert run["mtime_after"] == run["mtime_before"], (
        "the deck's mtime changed during the render"
    )
    left = run["folders_after"] - run["folders_before"]
    assert not left, f"render folders left in PowerPoint's tmp: {sorted(left)}"


def test_slide_past_end_refused():
    # AC6
    needs_powerpoint()
    tmp = tempfile.mkdtemp(prefix="render-deck-test-")
    deck = deck_copy(tmp)
    out = os.path.join(tmp, "out")
    result = render(deck, out, "--slides", "5")
    assert result.returncode == 1, (result.returncode, result.stderr)
    # Drop the paths so a digit in a temp folder name cannot stand in for the slide count.
    message = result.stderr.replace(deck, "").replace(out, "").replace(tmp, "")
    assert re.search(r"\b3\b", message), result.stderr


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    skipped = 0
    for name, func in tests:
        try:
            func()
            print(f"ok    {name}")
        except Skip as exc:
            skipped += 1
            print(f"skip  {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"{len(tests) - failed - skipped}/{len(tests)} passed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
