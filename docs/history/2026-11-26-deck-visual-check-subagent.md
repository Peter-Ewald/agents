---
date: 2026-11-26
title: A deck's visual check runs in a subagent
outcome: completed
---

# Wave 08 (agents): A deck's visual check runs in a subagent

## Summary

| | |
|---|---|
| **Goal** | A deck's slide images never enter the main session: the visual check runs in a Sonnet subagent that returns only a list of defects. Serves the backlog entry *A deck's visual check runs in a subagent* (Next Up, step 3). |
| **Kind** | Harness change: one agent definition, one script, one rule in `CLAUDE.md`. |
| **Changes** | New agent `deck-visual-check`. New script `render_deck.py` (PowerPoint's own PDF export, then `pdftoppm`). `CLAUDE.md` § Token economy: when the check runs and on which slides. Docs: the agents list and the skills-and-subagents page. |
| **Behaviour** | `render_deck.py` turns a deck (or chosen slides) into PNGs through PowerPoint and leaves the original file untouched. The agent renders the slides it is given, looks at them, and reports each slide's defects in words. A deck built by a script gets every slide checked first, then only the changed slides; a deck you maintain that the agent edited gets only the changed slides checked; a deck you edit yourself gets no check. |
| **Decisions** | D1 agent + `CLAUDE.md` line, D2 Sonnet, D3 edited decks: changed slides only (all three as you chose); D4 rendering through `pdftoppm`, no new dependency; D5 a script holds the render steps. |
| **Risks and holds** | PowerPoint may show a file-access dialog in a batch run; the script works inside PowerPoint's own sandbox folder to avoid it, and times out with a clear message otherwise (the wave then stops `blocked`). No holds; touches only `agents`. Wave 07 also edits `backlog.md` (mechanical rebase). |

## Context

The synced `pptx` skill requires a visual check ("Visual QA (required)"): render every slide and look
at it. In the main session the images stay in context and are re-sent with every later call: about
1,500 tokens per slide at 110 dpi. Checkmate's *the stream's deck for the platform owner* wave (09) spent
about 35k tokens on the first pass of a 21-slide deck and 15k to 20k on re-renders, a large part of why
that session ran out of context. The check found layout defects only (overlapping text, a box past the
slide edge, ids wrapping mid-word, a non-breaking hyphen U+2011 that PowerPoint's Calibri renders blank,
centred titles); content errors are a separate fact check.

The `pptx` skill cannot carry the rule: it is synced from claude.ai and a sync overwrites a local edit.
Its rendering path uses LibreOffice, which is not installed here; only PowerPoint shows how its own
fonts render. `pdftoppm` 26.06 is installed (Homebrew); PyMuPDF is not.

## Decisions

| # | Decision | Alternative |
|---|---|---|
| D1 | `.claude/agents/deck-visual-check.md` carries the procedure and report format; one bullet in `CLAUDE.md` § Token economy says when to use it, overriding the `pptx` skill's in-session check | `CLAUDE.md` paragraph only, with a general-purpose subagent briefed each time |
| D2 | The agent runs on Sonnet | Haiku: cheaper, misses small defects |
| D3 | A deck the user maintains that the agent edited (XML editing path): only the changed slides are checked | No check |
| D4 | PDF to PNG through `pdftoppm` (installed) | PyMuPDF: a new dependency |
| D5 | The render steps live in `.claude/scripts/render_deck.py`, which the agent runs | AppleScript inline in the agent file: retyped each run, untestable, and not covered by the scripts folder's allow rule in auto mode |

## Contracts

**`.claude/scripts/render_deck.py`** (stdlib, executable, runs under `/usr/bin/python3` 3.9):

```
render_deck.py DECK OUT_DIR [--dpi N] [--slides SPEC]
```

- `DECK`: a `.pptx`; missing or not `.pptx` → exit 1, stderr names it.
- `OUT_DIR`: created if needed; earlier `slide-*.png` in it are removed first.
- `--dpi`: default 100. `--slides`: `3`, `2,5`, `4-6` (1-based); invalid → exit 2 (argparse) naming it;
  a slide past the deck's end → exit 1 naming the slide count.
- Steps: copy the deck into `~/Library/Containers/com.microsoft.Powerpoint/Data/tmp/render-<uuid>/`
  (PowerPoint's sandbox, so no file-access dialog), open it in PowerPoint via `osascript`, save as PDF,
  close without saving, `pdftoppm -png -r <dpi> -f N -l N` per requested slide, write
  `OUT_DIR/slide-<NN>.png`, delete the temp folder. The original deck is never opened, so a file someone
  has open is untouched.
- The `osascript` call has a 120 s timeout; on timeout or a PowerPoint error → exit 1 with a message that
  names the likely cause (a PowerPoint dialog, PowerPoint not installed).
- stdout: the absolute PNG paths, one per line, in slide order.

**`.claude/agents/deck-visual-check.md`**: `model: sonnet`, `effort: medium`, tools `Read, Bash`.

- Brief: the deck path, which slides (`all` or a list), and optionally fonts the deck uses outside the
  safe list, whose fit is approximate.
- Runs `~/Projects/agents/.claude/scripts/render_deck.py <deck> <its scratch dir> --slides …`, reads each PNG,
  compares slides of the same type with each other.
- Looks for: text overflowing or cut off at a box or slide edge (first); overlapping elements; footers
  or sources colliding with content; gaps under 0.3" or margins under 0.5"; uneven spacing; misaligned
  columns; titles at different heights across slides of one type; low contrast; a word, id or number
  broken across lines; a character rendered blank or as a box (for example U+2011); centred titles where
  the other slides are left-aligned; leftover placeholders.
- Report, nothing else, never an image:

  ```
  Deck: <path>   Checked: <slides>   Render: PowerPoint, <dpi> dpi
  Slide 3: <defect, where, quoting the affected text>
  Slide 7: <defect>
  No defects: 1, 2, 4-6, 8
  ```

  On a render failure: `Render failed: <script's message>` and nothing else.

**`CLAUDE.md` § Token economy**, one bullet:

- **A deck's visual check runs in `deck-visual-check`**, never in the main session, whatever the `pptx`
  skill's Visual QA says: a deck built by a script gets every slide on the first round and only the
  changed slides after a fix; a deck the user maintains that the agent edited gets only the changed
  slides; a deck the user edits in PowerPoint gets no check. The main session acts on the defect list.

## Acceptance cases

| ID | Behaviour | Given | When | Then | Checked by |
|---|---|---|---|---|---|
| AC1 | Missing deck refused | no file at the path | `render_deck.py missing.pptx out/` | exit 1, stderr names the path; `out/` not created | unit |
| AC2 | Bad slide spec refused | a deck | `--slides 3-a` | exit 2 naming `3-a` | unit |
| AC3 | Whole deck rendered | a 3-slide fixture deck | `render_deck.py deck.pptx out/` | stdout lists 3 absolute paths `out/slide-01.png` … `slide-03.png`, each a PNG about 1333 px wide (16:9 at 100 dpi) | unit (needs PowerPoint; skipped with a stated reason where it is absent) |
| AC4 | Chosen slides only | the same deck, `out/` holding an old `slide-01.png` | `--slides 2` | only `slide-02.png` exists | unit (needs PowerPoint) |
| AC5 | Original untouched | the same deck | any render | the deck's bytes and mtime unchanged; no `render-*` folder left in PowerPoint's tmp | unit (needs PowerPoint) |
| AC6 | Slide past the end refused | the same deck | `--slides 5` | exit 1 naming the slide count 3 | unit (needs PowerPoint) |
| AC7 | The agent finds a planted defect | a copy of the fixture with slide 2's body text grown until it overflows its box | brief `deck-visual-check` with the deck, `all` | report names slide 2 with an overflow, lists 1 and 3 under no defects, contains no image data, stays in the report format | smoke, run by the wave agent |
| AC8 | Rule reaches every session | — | read `CLAUDE.md` § Token economy and `~/.claude/agents/deck-visual-check.md` | the bullet is there; the agent file resolves through the existing `~/.claude/agents` link | review |

The fixture deck: a 3-slide 16:9 `.pptx` committed under `.claude/scripts/fixtures/`, built once by the
test author by a means that adds no dependency to the repo (PowerPoint via AppleScript, or a one-off
`uv run --with python-pptx`); the generator is not committed.

## Sub-tasks

| ID | Goal | Owned files | Depends on | Acceptance check | Runs as |
|---|---|---|---|---|---|
| S0 | Tests first: AC1–AC6, fixture deck | `.claude/scripts/test_render_deck.py` (runs like `test_coordination.py`: `python3 <file>`), `.claude/scripts/fixtures/three-slides.pptx` | — | each test fails for the reason its case states | `test-author` (medium) |
| S1 | `render_deck.py` per the contract | `.claude/scripts/render_deck.py` | S0 | AC1–AC6 pass under `python3` and `/usr/bin/python3` | medium |
| S2 | Agent definition and `CLAUDE.md` bullet | `.claude/agents/deck-visual-check.md`, `CLAUDE.md` | S1 | AC7 smoke, AC8 | inline |
| S3 | Documentation upkeep | `.claude/agents/README.md` (table row), `docs/02-skills-and-subagents.md` (a `deck-visual-check (subagent)` section), `docs/00-agents-overview.md` (the agents list), `backlog.md` (remove the entry), `docs/history/` | S2 | `doc-conventions` loaded; claims match the files | inline |

## Verification

- `python3 .claude/scripts/test_render_deck.py` and `/usr/bin/python3 .claude/scripts/test_render_deck.py`.
- `python3 .claude/scripts/test_coordination.py` (unchanged suite still passes).
- `ruff check .claude` and `ruff format --check .claude`.
- AC7 smoke as above.

## Exit criteria

AC1–AC8 hold, suites and lint pass, docs and backlog updated, plan archived.

## Board fields

`repo=agents wave=wave-08-deck-visual-check-subagent "title=A deck's visual check runs in a subagent" mode=batch status=ready integration=push approved=2026-11-26 expires=2026-12-10`. No holds, no exclusive resources, no new dependencies.
