# HTML decks: the component guide

An HTML deck is the NBG light deck written as one self-contained web page: it opens in any
browser, the person who receives it edits it in place (text, layout, pictures, slides) and saves
it, and it prints one page per slide to PDF. Same brand as the PowerPoint decks: every colour,
size and position comes from [`tokens.yaml`](tokens.yaml), and the numbered Standards in
`presentation-style-guide.md` apply unchanged. Only the medium differs.

| You want | Format |
|---|---|
| a deck to edit in PowerPoint, the bank's default | PowerPoint (`/decks:create-presentation`) |
| a deck to edit in the browser and send as PDF | **HTML** (`/decks:create-html-deck`) |
| a dark full-bleed deck for a stage | Keynote (`/decks:create-keynote`) |
| a dark full-bleed stage deck, editable in the browser | **HTML keynote** (`/decks:create-html-deck --keynote`) |

## How it is made

```text
deck.src.html  (you write: slides only, classes below)
   |  decks-py html-build     inlines the design system, the editor, every picture
deck.html      (one file, ~150 KB plus pictures)
   |  decks-py html-check     brand rules, then a headless-Chrome layout check per slide
   |  decks-py html-pdf       verified PDF (one 1920x1080 page per slide) + PNGs to look at
deck.pdf
```

`html-build` on an already built or user-edited deck swaps in the current editor and keeps the
slides: that is how an old deck gets a newer runtime.

## The artboard

Each slide is a 1920 x 1080 px box, the 13.333 x 7.5 in slide at 144 px per inch. So **inches x 144
= px, points x 2 = px**: the 0.374 in gutter is 54 px, the 24pt title 48 px, the 16pt body 32 px.
Write sizes through the variables, never as numbers, and never below the 10pt floor (20 px).

## The skeleton

```html
<!doctype html>
<html lang="el">            <!-- el or en: the deck's language -->
<head><title>Short deck name</title></head>
<body>
<main class="deck">
  <section class="slide cover">...</section>
  <section class="slide">...</section>
  <section class="slide back"></section>
</main>
</body>
</html>
```

No `<script>`, no `<link>`, no web fonts, no remote pictures: `html-check` fails all of them. A
`<style>` block of your own is allowed for a one-off, after the design system, using only the
variables. Pictures are local paths (relative to `deck.src.html`, or absolute), inlined at build.

## Chrome (automatic)

The logo and the page number are drawn by CSS, so nobody can move or delete them by accident.

| Slide class | Logo | Page number |
|---|---|---|
| `slide` (content) | small wordmark, bottom left | yes |
| `slide cover`, `slide divider` | large wordmark | no |
| `slide back` | the emblem, centred | no |
| add `no-number` / `no-chrome` | as is / none | no |

## Content slide

```html
<section class="slide">
  <span class="pill">Section</span>                   <!-- optional; moves the title down -->
  <h1>Action title: the message in one sentence</h1>
  <p class="subtitle">Owner or scope line</p>         <!-- optional -->
  <div class="body"> ... components, top to bottom ... </div>
  <p class="source">Source: ..., as of Q2 2026</p>     <!-- every exhibit has one -->
  <aside class="notes">Speaker notes: never shown or printed</aside>
</section>
```

`.body` is a column from the body top (1.3 in) to the source line, with the grid gap between
children. `class="grow"` on a child takes the free height; `class="takeaway"` sits at the bottom.

## Components

| Need | Markup |
|---|---|
| Bullets (cyan glyph; level 2 by nesting) | `<ul><li>Point<ul><li>Sub-point</li></ul></li></ul>` |
| Columns | `<div class="cols-2">` / `cols-3` / `cols-4` / `cols-5`; uneven: `split-60`, `split-40` |
| Column heading | `<div class="col-head">Heading</div>` |
| Card | `<div class="card"><img class="icon" src="..."><h2>Title</h2><p>Text</p></div>` |
| Highlighted / recommended card | `card highlight`; `card recommended` with `<span class="tab">Recommended</span>` |
| Ask of another division / what we lead | `card ask`; `<div class="band">` |
| KPI tiles | `<div class="kpis"><div class="kpi"><span class="value">+12%</span><span class="label">Card spend</span><span class="delta pos">+3pp vs plan</span></div>...</div>` |
| Table (numbers right-aligned, zebra rows) | `<table class="data">`, `<td class="num">`, `<tr class="total">` |
| Process | `<div class="process"><div class="step"><div class="tile">01</div><h2>Step</h2><p>Line</p></div>...</div>` |
| Takeaway strip | `<p class="takeaway">The one thing to remember</p>` |
| Number badge | `<span class="badge">3</span>` |
| Picture with caption | `<figure><img src="..." alt="..."><figcaption>Caption</figcaption></figure>` |
| Text roles | `lead`, `caption`, `footnote`, `dense` (14pt); colour `teal`, `dark`, `muted`, `pos`, `neg` |

## Charts

Bars in CSS, each value as a fraction of the largest (`--v`), data label above, no gridlines, no
value axis (Standard #5):

```html
<div class="chart-bars-wrap">
  <div class="chart-bars highlight">                  <!-- highlight: the .hl bar in cyan, the rest grey -->
    <div class="bar" style="--v:0.58"><b>58</b><i></i><span>2024</span></div>
    <div class="bar hl" style="--v:1"><b>100</b><i></i><span>2025</span></div>
  </div>
</div>

<div class="chart-hbars">
  <div class="row" style="--v:0.4"><span>Label</span><div><i></i><b>40</b></div></div>
</div>
```

Anything else (line and area, doughnut, waterfall, stacked) is inline `<svg>` drawn to the chart
tokens: series in `var(--chart-1)` to `var(--chart-6)` (or the hex values of `charts.palette`),
lines 7 px (3.5pt) with hollow 12 px markers, data labels 24 px bold dark teal, category labels
24 px, no gridlines, a doughnut never a pie, a time series as an area-line. `viewBox` in artboard
px so text sizes are real. Peer banks always in their own colour (`extended_palettes.peer_banks`).

## Cover, contents, divider, back

```html
<section class="slide cover">
  <div class="heading"><h1>Deck title</h1><p class="subtitle">Unit A | Unit B</p></div>
  <p class="location">Athens</p><p class="date">October 2026</p>
</section>

<section class="slide contents">
  <h1>Contents</h1>
  <ol class="toc"><li><span class="t">Section</span><span class="d">One-line teaser</span></li></ol>
</section>

<section class="slide divider"><span class="num">01</span><h1>Section title</h1></section>

<section class="slide back"></section>
```

## Free placement

The layout above is the default and it is what keeps decks consistent. When a slide needs an
element somewhere the grid does not put it, add `class="free"` with
`style="position:absolute; left:...px; top:...px; width:...px"`: the same thing the editor writes
when the user drags a shape. `class="bleed"` on an element exempts it from the gutter and footer
checks (a full-width picture band, for example); use it for nothing else.

## Keynote: `<main class="deck keynote">`

The dark stage format of [keynote.md](keynote.md) (Standard #21) on the same 1920 x 1080 artboard:
every keynote measure is its 2560 px value x 0.75, generated as `--k-*` variables, so the gutter
is 116 px, an action title 40.5 px Light, a hero number 315 px ExtraBold. The house gradient with a
faint bloom and grain is the default ground; the white Greek wordmark sits bottom left (bottom
right on the cover, centred on the back cover); there are no page numbers. Text ends above the
footer row (960 px); the source note sits in it, right of the logo, never under 18 px (24 px at 2560).

| Archetype | Markup |
|---|---|
| Cover | `<section class="slide k-cover"><div class="k-head"><h1>Title</h1><p class="subtitle">...</p></div><div class="speaker"><span class="name">..</span><span class="role">..</span><span class="venue">..</span></div>` |
| Kicker (on every slide but cover and back) | `<div class="kicker">Section</div>` |
| Action title | `<h2 class="ktitle">...</h2>` |
| Statement | `<p class="statement">One sentence, <em>the emphasis in accent</em></p><p class="coda">...</p>` |
| Hero stat | `<div class="hero"><span class="value">3,3 εκ.</span><span class="caption">..</span><span class="support">..</span></div>`; `hero neg` for a decline (red number, white caption), `hero right` for the open side of a photograph |
| Duo stat | `<div class="duo"><div><div class="value">..</div><div class="caption">..</div></div><div>...</div></div>` |
| Bars (at most 2 slides, 7 bars) | `<div class="kbars highlight"><div class="kbar hl" style="--v:0.81"><b>81%</b><i></i><span>2025</span></div>...</div>`; add `many` for 4 to 7 bars; `<p class="axis-label">unit note</p>` |
| Points | `<ul class="points"><li><b>Lead</b>, the rest</li>...</ul><p class="ktakeaway">...</p>` |
| Divider | `<section class="slide k-divider">` kicker and `<h1>` on the open right side; `k-divider left` for the left |
| Closing | `<section class="slide k-closing">` kicker, `<p class="closing-line">`, `<p class="coda">` |
| Back cover | `<section class="slide k-back"></section>` |
| Source | `<p class="ksource">Source: ...</p>` |
| Speaker note (required) | `<aside class="notes">What the speaker says</aside>` |

### Photographs

A keynote is a photographic format. The cover, every divider (`k-divider`) and the closing
(`k-closing`) stand on a photograph, and `html-check` fails a keynote where one of them does not;
it warns when fewer than a third of the slides carry one. Data slides (hero, duo, bars) usually
stay on the gradient, where a number reads best.

The photographs are cinematic, dark and blue-teal graded: night or dusk, architecture, interiors
with practical lights, close detail, people only as distant figures or from behind, never posed
stock smiles, never bright daylight, never readable text or logos. Each one leaves calm, dark
space on the side the text will sit.

- **Drawn for the deck**, with a Gemini key: `decks-py illustrate --photo left --brief "<scene in
  words>" --out <WORK>/images/cover.jpg`. Draw the cover first; it is the style anchor, so pass
  `--ref <WORK>/images/cover.jpg` for every other one and the deck reads as one series. The brief
  goes to Google and may hold no digit, amount or the bank's name.
- **Your own**, any JPEG or PNG at 1920 px or wider. Photographs are never committed to a repo
  (keynote.md hard rule 6).

A photograph goes first in the slide: `<div class="bg scrim-left"><img src="photo.jpg" alt=""></div>`,
with `scrim-right`, `scrim-upperleft`, `scrim-bottom` or `scrim-full`, the dark side being where the
text sits. Over a photograph the statement and hero columns narrow, as keynote.md prescribes.
The check measures contrast on the gradient; over a photograph it cannot, so judge it on the PNG:
where a line runs into the bright part of the picture, narrow that element with an inline
`style="max-width:900px"` (keynote.md's per-slide `maxw`), or move the scrim to the other side.

## What the reader can do in the browser

- **Text**: double-click to edit; B / I / U, size, brand colour and alignment on the toolbar;
  paste arrives as plain text.
- **Shapes**: click selects (a second click goes one level in, Tab one level out), Shift+click
  adds, a box drawn on empty space selects what it covers. Drag to move, with snapping to the
  gutter, the slide centre and other shapes (Alt to place freely); handles resize (Shift keeps
  proportions); arrows nudge. The shape toolbar sets X / Y / W / H, fill, border, corners,
  opacity, text size, colour and alignment, front / back, align and distribute, duplicate,
  delete and reset.
- **Slides and items**: right-click to add a text box, a box or a picture; to duplicate, move or
  delete a bullet, card, row or slide; to add a slide.
- **Undo / redo**, and edits survive a reload in that browser until saved.
- **Save** writes the edited deck as the same kind of file; **PDF** prints one page per slide
  (choose Save as PDF); **Present** shows it full screen.

Nothing in a deck reaches the network: no fonts, scripts, analytics or AI calls.

## Rules the check enforces

`html-check` fails a deck for: anything external; any script but the runtime; an inline event
handler; a colour outside `tokens.yaml` (retired colours name their replacement); a shadow (the
brand has none, and PDF viewers draw them as grey blocks); a font other than Aptos (Calibri,
Tahoma as fallbacks); an em dash in the text. Then per slide, in Chrome: a picture that did not
load, text under 10pt (the pill's 9pt excepted), anything off the slide, across the side gutter,
into the footer zone or past the bottom of the body area, and clipped text. Text overlapping
other text is a warning.
