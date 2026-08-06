# nbg-keynote

Builds an NBG **keynote**: a dark, full-bleed, cinematic deck for a talk given from a stage.
YAML in, PPTX + PDF out, with per-slide speaker notes.

This is **not** the tool for normal decks. Committee, board and ExCo decks use
`../nbg-presentation/nbg_build.py`. Keynote mode is Standard #21 in
`../../shared/presentation-style-guide.md` and is fenced by four entry criteria — read them before
you start.

Format spec: **`../../shared/brand-system/keynote.md`**.

## Install

```bash
pip install -r requirements.txt
```

Aptos must be installed (all four weights: Light, Regular, SemiBold, ExtraBold). The compositor
falls back to Calibri and then DejaVu Sans with a warning, but the deck will not look right.

## Use

```bash
python3 nbg_keynote.py talk.yaml --validate      # check the spec, render nothing
python3 nbg_keynote.py talk.yaml                 # build PPTX + PDF
python3 nbg_keynote.py talk.yaml --slides 4,12   # re-render only slides 4 and 12
python3 nbg_keynote.py talk.yaml --out ~/Downloads/202601011200_talk
```

Rendered JPEGs are kept in `<output>_frames/` so `--slides` can rebuild one slide without
re-rendering the deck. A 16-slide deck takes about 5 seconds.

Start from `example.yaml` — it exercises every archetype and every option.

## How it works

1. Each slide is composed at 2560×1440 with Pillow: photograph or house gradient, directional teal
   scrim, vignette, bottom band, film grain, then type.
2. Before each text block is drawn, the compositor measures the 90th-percentile luminance beneath
   it and deepens a feathered scrim patch until the text clears WCAG (4.5:1 under 48px, 3:1 above).
   If it cannot, it warns — change the photograph.
3. Frames are saved as JPEG q92 4:4:4, placed full-bleed into a 13.333×7.5" PPTX, and written again
   as a PDF at 192 DPI.

The raster path is deliberate. It buys scrims, grain and vignettes that native PPTX cannot do; it
costs editability. A keynote is regenerated from its YAML, never edited in PowerPoint.

## Validation

`--validate` fails the build on: unknown slide type, missing required key, **a slide without
speaker notes**, more than 2 chart slides, more than 7 bars, an unknown scrim, or a missing image.

## Tests

```bash
python3 -m pytest test_nbg_keynote.py -v
```

No CI workflow runs Python tests in this repo, so this is a by-hand check. Run it after touching
the compositor.

## Photographs

Never committed. Supply your own and point `meta.assets` at the directory, or use absolute paths.
Generated artefacts belong in `~/Downloads`, not in the repo.
