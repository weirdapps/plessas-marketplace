# NBG Keynote Mode — design

**Date:** 2026-08-06
**Status:** approved
**Origin:** `202608022219_the_physical_edge_keynote.pptx` (RBTE Europe talk, Aug 2026). The format is
kept; the content is not.

## Problem

A cinematic, dark, full-bleed presentation format was built ad hoc for a conference keynote. It reads
well from a stage and is unmistakably NBG, but it exists only as a one-off script in `~/Downloads`
alongside 130MB of images. Nothing about it is reusable, and it silently contradicts four hard rules
in the decks brand system.

Two things have to be true at the end:

1. The format is codified so the next keynote is a YAML file, not a rewritten compositor.
2. The main deck format is not weakened. `Standard #20` ("ONE format, elements chosen by message")
   is a deliberate policy and must survive.

## What the source format actually is

Not a PPTX layout system. All 16 slides use the `Blank` layout and contain exactly one full-bleed
picture. The real generator is a Pillow compositor (`compose.py`) that renders 2560×1440 PNGs, and an
assembler (`assemble.py`) that places them into a 13.333×7.5" PPTX with per-slide speaker notes.

The raster path buys directional teal scrims over photography, film grain, vignette and soft text
shadows — none of which native PPTX can do. It costs editability and file size. For a deck spoken
once from a stage that is the right trade; for a deck someone else will edit it is the wrong one.

## Decisions

### D1 — Standard #21, an explicit named exception

Rejected: folding keynote in as an "inverted mode" of the one format. It is more honest to say the
rules are broken and fence the breakage.

`Standard #21` admits keynote mode with four entry criteria that must **all** hold:

1. Audience is external or bank-wide (conference, town hall, industry panel) — not a committee,
   board or ExCo working session.
2. Delivered live from a stage by a speaker — not read alone, not circulated as a document.
3. Projected large, in a darkened room.
4. The slides are the backdrop, not the record — the argument lives in the speaker notes.

If any criterion fails, use light mode. `Standard #20` gains one line: exactly one exception exists,
it is `#21`, and the list is closed.

### D2 — Ship spec + generator + command

- `brand-system/keynote.md` is the single source of truth for the format.
- `tools/nbg-keynote/nbg_keynote.py` is one file, matching the existing flat idiom of
  `tools/nbg-presentation/nbg_build.py`. YAML in, PPTX + PDF out.
- `/create-keynote` is the entry point and enforces the D1 criteria before anything is rendered.

### D3 — Photographs stay out of the repo

Images are author-supplied and referenced by path in the YAML. The compositor handles fit and scrim.
Nothing binary from a specific talk is committed.

## What keynote mode does not change

Greek wordmark always. Aptos always. Teal family always. Left-gutter alignment. Action titles. No
em-dashes, no invented NBG names, no version suffixes in filenames. Keynote is the same brand
inverted, not a second identity.

## Palette — dark tokens, mapped from light

| Token | Hex | ← light-mode | Use |
|---|---|---|---|
| `ink` | `#FFFFFF` | `003841` | primary text, hero numbers |
| `ink-2` | `#DFE6E6` | `202020` | body and support text |
| `ink-3` | `#96A6A8` | `5A5F5A` | source notes, metadata |
| `accent` | `#00DFF8` | `007B85` | kicker, emphasis line, highlighted stat or bar |
| `accent-bar` | `#00BED2` | `00ADBF` | default bar fill |
| `accent-mute` | `#008292` | `BEC1BE` | non-highlighted bars |
| `ground-top` | `#00161B` | `FFFFFF` | gradient top, scrim base |
| `ground-bot` | `#003841` | `F5F8F6` | gradient bottom |
| `negative` | `#FF5263` | `AA0028` | negative statistic |
| `rule` | `#788C8E` | `BEC1BE` | chart baseline |

`00DFF8` is flagged in the light-mode SSOT as too bright for backgrounds. In keynote mode it is never
a background, only text or a mark on dark ground, which is exactly where it works.

## Chassis

Render at 2560×1440, export full-bleed into a 13.333×7.5" canvas (192 DPI effective).

| Element | Value @2560 | Note |
|---|---|---|
| Side gutter | 155px (0.807") | Wider than the business 0.374" on purpose — read from 20m |
| Safe area | 100px from every edge | Nothing critical outside |
| Kicker | y=150; 22×22px `accent` square; ALL-CAPS SemiBold 30px, +6px tracking, x=199 | |
| Action title | y=250, Light 52–56px | |
| Footer logo | (155, 1300), height 46px, white wordmark | |
| Source note | baseline 1312, Regular 24px `ink-3` | |
| Page numbers | none | A live audience does not need them |
| Grain | Gaussian σ=4 | Kills banding on the dark gradient |

Nine archetypes: `cover`, `statement`, `hero-stat`, `duo-stat`, `bars`, `points`, `divider`,
`closing`, `back`.

## Improvements over the source script

| # | Change | Rationale |
|---|---|---|
| 1 | Gradient bottom `#00363D` → `#003841` | Off-brand near-miss; visually identical, ties to the SSOT |
| 2 | Drop dead `CYAN_DIM #005C68`; name the inline `(0,130,146)` as `accent-mute #008292` | Magic number becomes a token |
| 3 | `#FF5263` becomes the sanctioned dark-mode negative in `colors.md` | `AA0028` is unreadable on dark; the replacement was anonymous |
| 4 | Source note 22px → 24px | 22px is 8.25pt, below any readable floor |
| 5 | `greek_upper()` strips tonos, keeps dialytika | `'ή'.upper()` yields `'Ή'`; Greek all-caps drops the accent. `Η ΣΥΝΑΊΝΕΣΗ` is a visible typo |
| 6 | Measured WCAG contrast floor with automatic scrim deepening | 4.5:1 for text ≤38px, 3:1 for hero stats. The scrims currently pass by luck on these photographs |
| 7 | Bar width capped ~380px for n≤3, group centred | n=2 currently yields 1050px bars — a wall, not a comparison |
| 8 | Grain seeded per slide (`base + index`) | Module-level `seed(7)` is only reproducible for a whole run, not one slide |
| 9 | Speaker note mandatory; a slide without one fails `--validate` | Spoken format; the note is the other half of the deliverable |
| 10 | Export PDF alongside PPTX | The PDF is what goes on the conference AV laptop |
| 11 | JPEG q=92 with 4:4:4 chroma | 4:2:0 smears grain and fine type |

## Charts — a bounded concession

Keynote charts are hand-drawn Pillow primitives, not native PPTX charts, contradicting the brand rule
that charts must be native. The concession is bounded: **at most one chart per keynote, at most seven
bars, no axes, no gridlines, no legend.** A slide that needs a real chart is not a keynote slide.

## Files

```
plugins/decks/
  shared/brand-system/keynote.md              NEW — format SSOT
  shared/brand-system/colors.md               + dark-mode token block
  shared/brand-system/README.md               + pointer; white-background rule cites #21
  shared/presentation-style-guide.md          + Standard #21; one line added to #20
  tools/nbg-keynote/
    nbg_keynote.py                            YAML → PNG → PPTX + PDF, plus --validate
    example.yaml   README.md   requirements.txt   test_nbg_keynote.py
  commands/create-keynote.md                  NEW slash command
  agents/storyboard-designer.md               + keynote pointer
  agents/presentation-qa.md                   + keynote pointer
```

`plugins/decks/shared/brand-system/` is canonical; the repo-root `shared/brand-system/` is an
auto-synced mirror. After editing, run `scripts/sync_brand_system.sh` or CI fails on drift.

## YAML interface

```yaml
meta:
  title: ...
  speaker: {name: ..., role: ...}
  venue: ...
  language: el            # enables greek_upper on kickers
  output: ~/Downloads/202608061821_talk_name
slides:
  - {type: cover, image: cover.png, scrim: left, title: ..., subtitle: ..., notes: ...}
  - {type: statement, kicker: ..., text: ..., coda: ..., notes: ...}
  - {type: hero-stat, kicker: ..., value: 68m, caption: ..., support: ..., source: ..., notes: ...}
  - {type: bars, kicker: ..., title: ..., cats: [...], vals: [...], highlight: 4, unit: "%", notes: ...}
  - {type: back}
```

## Verification

The acceptance bar is visual parity with the source deck. The generator is checked by re-rendering an
equivalent deck from YAML using the original images and comparing against
`202608022219_the_physical_edge_keynote.pdf` slide by slide.

`test_nbg_keynote.py` covers `greek_upper`, the WCAG ratio maths, bar geometry under the width cap,
and YAML-to-slide-count. No CI workflow runs Python tests in this repo, so it is a by-hand check.

## Out of scope

- Changing `nbg_validate.py`. It is tuned for light-mode PPTX and would flag every keynote slide.
  Keynote validation lives behind `nbg_keynote.py --validate`.
- Bundling photography, or a stock-image pipeline.
- Animation, transitions or video.
