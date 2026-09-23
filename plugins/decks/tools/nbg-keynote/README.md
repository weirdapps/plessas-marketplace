# nbg-keynote

Builds an NBG **keynote**: a dark, full-bleed, cinematic deck for a talk given from a stage.
YAML in, PPTX + PDF out, with per-slide speaker notes.

This is **not** the tool for normal decks. Committee, board and ExCo decks use
`../nbg-presentation/nbg_build.py` (`decks-py build`). Keynote mode is Standard #21 in
`../../shared/presentation-style-guide.md` and is fenced by four entry criteria, read them before
you start.

Format spec: **`../../shared/brand-system/keynote.md`**. Dark tokens (machine source):
`../../shared/brand-system/tokens.yaml`, section `keynote`.

## Install

Nothing to install by hand. The plugin launcher `bin/decks-py` builds this tool's Python
environment on first use (with uv when it is installed, otherwise Python 3.12+ `venv` and pip),
keeps it in `~/.cache/nbg-decks/`, and rebuilds it when `requirements.txt` changes. Python 3.12+
or uv is the only prerequisite (`numpy>=2.5.2` declares `requires-python >=3.12`).

```bash
bash plugins/decks/bin/decks-py setup    # optional: build every decks environment now
bash plugins/decks/bin/decks-py doctor   # Python, environments, LibreOffice, Aptos fonts
```

A bare `pip install -r requirements.txt` fails on a PEP 668 system (Homebrew Python, most Linux
distributions); the launcher avoids it.

### Fonts

Aptos in four weights (Light, Regular, SemiBold, ExtraBold). The compositor looks for them,
ignoring case, in:

- macOS: `~/Library/Fonts`, `/Library/Fonts`, `/System/Library/Fonts/Supplemental`, and the
  `Contents/Resources/DFonts` folder of the Office apps (PowerPoint, Word, Excel, Outlook), which
  is where Office for Mac keeps Aptos and Calibri
- Windows: `%WINDIR%\Fonts` and `%LOCALAPPDATA%\Microsoft\Windows\Fonts`
- Linux: `~/.local/share/fonts`, `~/.fonts`, `/usr/share/fonts/truetype`, `/usr/share/fonts`
  (and one folder level below each)

Without Aptos it falls back to Calibri (`calibri.ttf`, `calibrib.ttf`, `calibril.ttf`) and then
DejaVu Sans, with a warning. `--validate` prints the file behind each weight, so a fallback is
visible before you render.

## Use

From the repository root (inside Claude Code the path is `${CLAUDE_PLUGIN_ROOT}/bin/decks-py`):

```bash
bash plugins/decks/bin/decks-py keynote talk.yaml --validate            # check spec and layout, render nothing
bash plugins/decks/bin/decks-py keynote talk.yaml                       # build PPTX + PDF
bash plugins/decks/bin/decks-py keynote talk.yaml --slides 4,12         # re-render 4 and 12, reuse the rest
bash plugins/decks/bin/decks-py keynote talk.yaml --out ~/Downloads/202601011200_talk
bash plugins/decks/bin/decks-py keynote talk.yaml --placeholder-images  # lay out before the photos exist
```

Start from `example.yaml`: it exercises every archetype and every option. Its photographs are
yours to supply, so until you have them run it with `--placeholder-images`: a missing photograph
is then drawn as a flat dark stand-in under the same scrim, with a warning, instead of failing.

Rendered JPEGs are kept in `<output>_frames/` (with a content-addressed store in `.cache/`
beside them). A frame is reused only when nothing it depends on changed: the slide's YAML, the
grain seed, the photograph on disk and the compositor itself. So `--slides` re-renders the
slides you name plus any slide that changed, and an inserted slide never inherits another
slide's image.

## How it works

1. Each slide is composed at 2560×1440 with Pillow: photograph or house gradient, directional teal
   scrim, vignette, bottom band, film grain, then type.
2. Every slide renders in two passes. The first lays it out: each text block records its box and
   the contrast it needs. The compositor then measures the 90th-percentile luminance beneath each
   box and deepens a feathered scrim patch until the text clears WCAG (4.5:1 under 48px, 3:1 at or
   above), for every text element: kicker, titles, statements, values, captions, bar labels,
   speaker block and source note. The second pass draws. If a patch cannot get there, it warns:
   change the photograph.
3. Frames are saved as JPEG q92 4:4:4, placed full-bleed into a 13.333×7.5" PPTX, and written again
   as a PDF at 192 DPI, also 4:4:4.
4. Each PPTX slide carries a title (behind the frame, for the outline and screen readers) and alt
   text holding everything the slide shows.

The raster path is deliberate. It buys scrims, grain and vignettes that native PPTX cannot do; it
costs editability. A keynote is regenerated from its YAML, never edited in PowerPoint.

## Validation

`--validate` fails the build on: unknown slide type, missing required key, **a slide without
speaker notes**, more than 2 chart slides, more than 7 bars, an unknown scrim, or a missing image
(a warning instead with `--placeholder-images`).

It also fails on specs that used to pass it and then abort the render or ship broken: a required
text field that is blank or whitespace-only, `cats` and `vals` of different lengths, a bar series
whose values are all zero or below, any negative bar value (keynote bars stand on a true zero
baseline; state a decline as a `hero-stat` with `color: negative`), and an unknown colour name in
`color`, `caption_color` or a duo-stat half.

And it lays every slide out with the renderer's own fonts and wrapping, failing when text runs
past the right gutter (x 2405), into the footer row (below y 1280) or outside the 100px safe area,
when a cover title needs more than 2 lines, or when two text blocks overlap.

## Tests

```bash
uv run --no-project --python 3.12 --with-requirements plugins/decks/tools/nbg-keynote/requirements.txt \
    --with pytest python -m pytest plugins/decks/tools/nbg-keynote -q
```

CI runs this suite in `tests.yml` (`pytest plugins scripts`), which fails on any skipped test. The
suite renders every archetype over a bright stand-in photograph, builds the shipped example end
to end, and checks PDF chroma, PPTX titles and alt text, and `--slides` frame pairing.

## Photographs

Never committed. Supply your own and point `meta.assets` (or `--assets`) at the directory, or use
absolute paths. Generated artefacts belong in `~/Downloads`, not in the repo.
