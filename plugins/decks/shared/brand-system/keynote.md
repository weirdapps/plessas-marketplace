# NBG Keynote Mode

**Single source of truth for the dark, full-bleed keynote format.**

Keynote mode is the one sanctioned exception to the light-mode NBG deck format
(`presentation-style-guide.md` Standard #21). It exists for talks delivered live to an external or
bank-wide audience. Everything else — every committee, board and ExCo deck — uses the light format
and `tools/nbg-presentation/nbg_build.py`.

Generator: `tools/nbg-keynote/nbg_keynote.py` (YAML in, PPTX + PDF out).

## When you may use it

All four must hold. If any fails, use light mode.

1. Audience is **external or bank-wide** — conference, town hall, industry panel. Not a committee,
   board or ExCo working session.
2. **Delivered live from a stage by a speaker.** Not read alone, not circulated as a document.
3. **Projected large, in a darkened room.**
4. The slides are the **backdrop, not the record** — the argument lives in the speaker notes.

Never for: ExCo, board, credit committee, or any deck someone else will edit. Keynote slides are
flattened images; they cannot be edited downstream, only regenerated from the YAML.

## What does not change

Greek wordmark on every slide, always. Aptos throughout. The teal family. Left-gutter alignment.
Action titles. No em-dashes, no invented NBG names, no version suffixes in filenames. Keynote is the
same brand inverted, not a second identity.

## Palette — dark tokens

Each token maps to a light-mode colour in `colors.md`. Do not introduce new colours.

| Token | Hex | ← light-mode | Use |
|---|---|---|---|
| `ink` | `#FFFFFF` | `003841` | primary text, hero numbers |
| `ink-2` | `#DFE6E6` | `202020` | body and support text |
| `ink-3` | `#96A6A8` | `5A5F5A` | source notes, metadata |
| `accent` | `#00DFF8` | `007B85` | kicker, emphasis line, highlighted stat or bar |
| `accent-bar` | `#00BED2` | `00ADBF` | default bar fill |
| `accent-mute` | `#008292` | `BEC1BE` | non-highlighted bars |
| `ground-top` | `#00161B` | `FFFFFF` | gradient top, scrim base |
| `ground-bot` | `#003841` | `F5F8F6` | gradient bottom (brand Dark Teal) |
| `negative` | `#FF5263` | `AA0028` | negative statistic |
| `rule` | `#788C8E` | `BEC1BE` | chart baseline |

`00DFF8` is flagged in `colors.md` as too bright for backgrounds. That rule still holds: in keynote
mode it is never a background, only text or a mark on dark ground.

## Chassis

Render at 2560×1440, export full-bleed into the standard 13.333×7.5" canvas (192 DPI effective).
All values below are pixels at 2560 wide. 1px = 0.375pt.

| Element | Value | Note |
|---|---|---|
| Side gutter | 155 (0.807") both sides | Wider than the business 0.374" on purpose — read from 20m |
| Safe area | 100 from every edge | Nothing critical outside it |
| Kicker | y=150; 22×22 `accent` square at x=155; ALL-CAPS SemiBold 30, +6 tracking, from x=199 | The keynote's section pill |
| Action title | y=250, Light 52–56 | |
| Footer logo | (155, 1300), height 46, white Greek wordmark | Cover: height 60, bottom-right. Back: height 150, centred |
| Source note | baseline 1312, Regular 24, `ink-3` | Never smaller than 24 |
| Page numbers | none | A live audience does not need them |
| Grain | Gaussian σ=4, seeded per slide | Also what stops the dark gradient banding |

### Ground

Either the house gradient (`ground-top` → `ground-bot`, with a faint cyan bloom lower-left) or a
full-bleed photograph with a directional scrim: `left`, `right`, `upperleft`, `bottom`, `full`.
Every scrim also lays a bottom band so the footer reads, and a vignette.

### Type scale

| Role | Weight | Size | Colour |
|---|---|---|---|
| Cover title | ExtraBold | 150 | `ink` |
| Divider title | ExtraBold | 96 | `ink` |
| Hero stat | ExtraBold | 400–440 | `ink`, or `accent` / `negative` |
| Duo stat | ExtraBold | 260–300 | left `ink`, right `accent` |
| Statement | Light | 72–86 | `ink`, emphasis in `accent` |
| Action title | Light | 52–56 | `ink` |
| Stat caption | Light | 48–60 | `accent` — but `ink` when the number is `negative` |
| Body / support | Regular | 34–38 | `ink-2` |
| Kicker | SemiBold | 30 | `accent` |
| Speaker name / role / venue | SemiBold 30 / Regular 27 / Regular 24 | | `accent` / `ink-2` / `ink-3` |
| Source | Regular | 24 | `ink-3` |

Cyan against a red number is two loud colours fighting for the same eye, so a `negative` hero stat
takes a white caption.

## Archetypes

| Type | Says | Anchors |
|---|---|---|
| `cover` | who is speaking and about what | photo + scrim; title y=300; subtitle y=500; speaker block y=1140; logo bottom-right |
| `statement` | one sentence, nothing else | kicker; text y=470; optional `emphasis` in accent below it; optional `coda` y=980 |
| `hero-stat` | one number carries the slide | kicker; value y=250–300; caption below; support below that. `align: right` puts the block on the open side of a photograph |
| `duo-stat` | two numbers in tension | kicker; title y=250; left at x=155, right at x=1360; right value in `accent` |
| `bars` | a comparison across categories | kicker; title y=250; bars baseline y=1170 |
| `points` | three things a regulator or a market did | kicker; title y=250; 18×18 accent squares from y=500; optional `takeaway` in accent |
| `divider` | the talk turns here | photo + scrim; kicker; ExtraBold title on the open side; logo only, no source |
| `closing` | the line they should repeat afterwards | photo + scrim; kicker; text y=330; coda y=1130 |
| `back` | end | gradient, centred wordmark, nothing else |

## Hard rules

1. **Every slide except `back` carries a speaker note.** A keynote slide without one is half a
   slide. `--validate` fails the build.
2. **Contrast is measured, not eyeballed.** The compositor samples the 90th-percentile luminance
   under every text box and deepens a feathered scrim patch until the text clears WCAG — 4.5:1 for
   text under 48px, 3:1 at or above it. If it cannot get there it warns; change the photograph.
3. **Charts are a bounded concession.** Keynote charts are drawn primitives, not native PPTX
   charts, which contradicts the light-mode rule. The bound: **at most 2 chart slides, at most 7
   bars, no axes, no gridlines, no legend.** A slide needing a real chart is not a keynote slide.
4. **Bars keep a true zero baseline**, and are capped at 380px wide so two bars read as a
   comparison rather than a wall.
5. **Greek all-caps drops the tonos.** Set `meta.language: el` and the kicker uses `greek_upper()`.
   `'ή'.upper()` yields `'Ή'`, which is a visible typo on a two-metre screen.
6. **Photographs are never committed.** They are author-supplied and referenced by path.
7. **JPEG at quality 92, 4:4:4 chroma.** 4:2:0 smears the grain and the fine type.
8. **Ship the PDF too.** The PDF is what goes on the conference AV laptop.

## Usage

```bash
cd plugins/decks/tools/nbg-keynote
pip install -r requirements.txt
python3 nbg_keynote.py talk.yaml --validate      # check the spec, render nothing
python3 nbg_keynote.py talk.yaml                 # build PPTX + PDF
python3 nbg_keynote.py talk.yaml --slides 4,12   # re-render two slides only
```

See `example.yaml` for the full YAML surface.
