# nbg-keynote

Builds an NBG **keynote**: a dark, full-bleed, cinematic deck for a talk given from a stage.
YAML in, PPTX + PDF out, with per-slide speaker notes.

This is **not** the tool for normal decks. Committee, board and ExCo decks use
`../nbg-presentation/nbg_build.py`. Keynote mode is Standard #21 in
`../../shared/presentation-style-guide.md` and is fenced by four entry criteria, read them before
you start.

Format spec: **`../../shared/brand-system/keynote.md`**.

## Install

`installers/install.sh` already does this: it creates `.venv` in this directory and installs
`requirements.txt` into it, so the documented invocation is that interpreter. Python 3.12+ is a
hard floor (`numpy>=2.5.2` declares `requires-python >=3.12`).

```bash
# what the installer runs, if you need to redo it by hand
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

A bare `pip install -r requirements.txt` fails on a PEP 668 system (Homebrew Python, most Linux
distributions). Use the venv, or `uv run --with ...` for a throwaway run.

Aptos must be installed (all four weights: Light, Regular, SemiBold, ExtraBold). The compositor
falls back to Calibri and then DejaVu Sans with a warning, but the deck will not look right.

## Use

From the repository root, using the interpreter the installer built:

```bash
V=plugins/decks/tools/nbg-keynote/.venv/bin/python3
K=plugins/decks/tools/nbg-keynote/nbg_keynote.py

$V $K talk.yaml --validate      # check the spec, render nothing
$V $K talk.yaml                 # build PPTX + PDF
$V $K talk.yaml --slides 4,12   # re-render only slides 4 and 12
$V $K talk.yaml --out ~/Downloads/202601011200_talk
```

`python3 nbg_keynote.py talk.yaml` from inside this directory works too, but only if the
dependencies happen to be on that interpreter. The `.venv` path is the one to script against.

Rendered JPEGs are kept in `<output>_frames/` so `--slides` can rebuild one slide without
re-rendering the deck. A 16-slide deck takes about 5 seconds.

Start from `example.yaml`: it exercises every archetype and every option.

## How it works

1. Each slide is composed at 2560×1440 with Pillow: photograph or house gradient, directional teal
   scrim, vignette, bottom band, film grain, then type.
2. Before each text block is drawn, the compositor measures the 90th-percentile luminance beneath
   it and deepens a feathered scrim patch until the text clears WCAG (4.5:1 under 48px, 3:1 above).
   If it cannot, it warns: change the photograph.
3. Frames are saved as JPEG q92 4:4:4, placed full-bleed into a 13.333×7.5" PPTX, and written again
   as a PDF at 192 DPI.

The raster path is deliberate. It buys scrims, grain and vignettes that native PPTX cannot do; it
costs editability. A keynote is regenerated from its YAML, never edited in PowerPoint.

## Validation

`--validate` fails the build on: unknown slide type, missing required key, **a slide without
speaker notes**, more than 2 chart slides, more than 7 bars, an unknown scrim, or a missing image.

It also fails on the four specs that used to pass it and then abort the render, two of them with a
raw traceback: a required text field that is blank or whitespace-only, `cats` and `vals` of
different lengths, a bar series whose values are all zero or negative (no scale to divide by), and
an unknown colour name in `color`, `caption_color` or a duo-stat half. The renderer no longer
crashes on the first and third either: blank text draws nothing and an unscalable bar series
collapses onto the baseline, so a bad spec is caught by the gate rather than by a stack trace.

## Tests

```bash
python3 -m pytest test_nbg_keynote.py -v
```

This suite runs in CI: `sonarcloud.yml` executes `pytest plugins`, which collects it. Run it
locally after touching the compositor. Without the dependencies installed system-wide:

```bash
uv run --with pytest --with pillow --with numpy --with pyyaml --with python-pptx \
    python -m pytest test_nbg_keynote.py -q
```

## Photographs

Never committed. Supply your own and point `meta.assets` at the directory, or use absolute paths.
Generated artefacts belong in `~/Downloads`, not in the repo.
