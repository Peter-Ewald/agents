#!/usr/bin/env python3
"""Render a .pptx deck's slides to PNGs through Microsoft PowerPoint.

PowerPoint does the rendering so the fonts look as they do on screen. The original deck is never
opened: a copy goes into PowerPoint's sandbox folder (so no file-access dialog appears), is saved
there as a PDF, and the temporary folder is deleted afterwards. pdftoppm turns the PDF pages into PNGs.

Usage:
    render_deck.py DECK OUT_DIR [--dpi N] [--slides SPEC]

    DECK      the .pptx file
    OUT_DIR   where slide-NN.png files go; created if needed, earlier slide-*.png in it are removed
    --dpi     resolution, default 100
    --slides  1-based slides to render: "3", "2,5", "4-6", "1,3-4"; default every slide

stdout: the absolute PNG paths, one per line, in slide order. Errors go to stderr: exit 1 for a
deck, slide or tool problem, exit 2 for an invalid command line. Needs macOS, Microsoft PowerPoint and
pdftoppm (poppler). Stdlib only.
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import uuid
import zipfile

POWERPOINT_TMP = os.path.expanduser(
    "~/Library/Containers/com.microsoft.Powerpoint/Data/tmp"
)
OSASCRIPT_TIMEOUT = 120
SLIDE_ENTRY = re.compile(r"^ppt/slides/slide\d+\.xml$")

APPLESCRIPT = """
on run argv
    set deckPath to item 1 of argv
    set pdfPath to item 2 of argv
    tell application "Microsoft PowerPoint"
        open POSIX file deckPath
        set pres to active presentation
        try
            save pres in POSIX file pdfPath as save as PDF
        on error errMsg number errNum
            close pres saving no
            error errMsg number errNum
        end try
        close pres saving no
    end tell
end run
"""


class RenderError(Exception):
    """A problem the user can act on; main() prints it and exits 1."""


def parse_slides(spec):
    """Turn "1,3-4" into [1, 3, 4]; raise argparse.ArgumentTypeError for an invalid spec."""
    slides = []
    for part in spec.split(","):
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not match:
            raise argparse.ArgumentTypeError(f"invalid slide spec {spec!r}")
        first = int(match.group(1))
        last = int(match.group(2) or first)
        if first < 1 or last < first:
            raise argparse.ArgumentTypeError(
                f"invalid slide spec {spec!r}: slides count from 1 and ranges go upwards"
            )
        slides.extend(range(first, last + 1))
    return sorted(set(slides))


def check_deck(deck):
    """Return the deck's slide count; raise RenderError if it is not a readable .pptx."""
    if not deck.lower().endswith(".pptx"):
        raise RenderError(f"not a .pptx file: {deck}")
    if not os.path.isfile(deck):
        raise RenderError(f"deck not found: {deck}")
    try:
        with zipfile.ZipFile(deck) as archive:
            return sum(1 for name in archive.namelist() if SLIDE_ENTRY.match(name))
    except zipfile.BadZipFile:
        raise RenderError(f"not a valid .pptx (bad zip): {deck}")


def check_slides(slides, count):
    for slide in slides:
        if slide > count:
            raise RenderError(
                f"slide {slide} is past the end: the deck has {count} slides"
            )


def export_pdf(deck, folder):
    """Copy the deck into folder, have PowerPoint save the copy as a PDF, return the PDF path.

    The copy is named after the unique folder: PowerPoint refuses to open a file whose name matches
    a presentation that is already open, such as the original deck.
    """
    name = os.path.basename(folder)
    copy = os.path.join(folder, name + ".pptx")
    pdf = os.path.join(folder, name + ".pdf")
    shutil.copy2(deck, copy)
    try:
        result = subprocess.run(
            ["osascript", "-e", APPLESCRIPT, copy, pdf],
            check=False,
            capture_output=True,
            text=True,
            timeout=OSASCRIPT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise RenderError(
            f"PowerPoint did not finish within {OSASCRIPT_TIMEOUT} s; a PowerPoint "
            "dialog may be waiting for an answer"
        )
    except FileNotFoundError:
        raise RenderError("osascript not found; this script needs macOS")
    if result.returncode != 0 or not os.path.isfile(pdf):
        raise RenderError(
            "PowerPoint could not export the deck; it may not be installed, or a "
            f"dialog may be waiting for an answer. osascript said: {result.stderr.strip()}"
        )
    return pdf


def render_pngs(pdf, out_dir, slides, dpi):
    """Run pdftoppm once per slide and return the PNG paths in slide order."""
    paths = []
    for slide in slides:
        prefix = os.path.join(out_dir, f"slide-{slide:02d}")
        try:
            result = subprocess.run(
                [
                    "pdftoppm",
                    "-png",
                    "-r",
                    str(dpi),
                    "-f",
                    str(slide),
                    "-l",
                    str(slide),
                    "-singlefile",
                    pdf,
                    prefix,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            raise RenderError(
                "pdftoppm not found; install poppler (brew install poppler)"
            )
        if result.returncode != 0:
            raise RenderError(
                f"pdftoppm failed for slide {slide}: {result.stderr.strip()}"
            )
        paths.append(prefix + ".png")
    return paths


def render_deck(deck, out_dir, slides, dpi):
    count = check_deck(deck)
    slides = slides or list(range(1, count + 1))
    check_slides(slides, count)
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for old in glob.glob(os.path.join(glob.escape(out_dir), "slide-*.png")):
        os.remove(old)
    folder = os.path.join(POWERPOINT_TMP, f"render-{uuid.uuid4().hex}")
    os.makedirs(folder)
    try:
        pdf = export_pdf(deck, folder)
        return render_pngs(pdf, out_dir, slides, dpi)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="render_deck.py", description="Render a .pptx deck's slides to PNGs."
    )
    parser.add_argument("deck", metavar="DECK", help="the .pptx file")
    parser.add_argument("out_dir", metavar="OUT_DIR", help="folder for slide-NN.png")
    parser.add_argument("--dpi", type=int, default=100, help="resolution (default 100)")
    parser.add_argument(
        "--slides",
        type=parse_slides,
        default=None,
        help='slides to render, e.g. "3", "2,5", "4-6", "1,3-4" (default: all)',
    )
    args = parser.parse_args(argv)
    if args.dpi < 1:
        parser.error(f"--dpi must be positive, got {args.dpi}")
    try:
        paths = render_deck(
            os.path.abspath(args.deck), args.out_dir, args.slides, args.dpi
        )
    except RenderError as error:
        print(f"render_deck.py: {error}", file=sys.stderr)
        return 1
    print("\n".join(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
