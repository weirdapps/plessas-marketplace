# NBG Presentation Tools

Tools for creating National Bank of Greece (NBG) formatted presentations.

## Installation

`requirements.txt` is the list: pyyaml, python-pptx, lxml and defusedxml. Python 3.12+ is a hard
floor, not a preference.

`installers/install.sh` already creates `.venv` in this directory and installs `requirements.txt`
into it, so **the interpreter to script against is `.venv/bin/python3`**:

```bash
# from the repository root
plugins/decks/tools/nbg-presentation/.venv/bin/python3 \
    plugins/decks/tools/nbg-presentation/nbg_build.py outline.yaml output.pptx
```

To redo the venv by hand, or on a machine where the installer has not run:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

A bare `pip install -r requirements.txt` fails on a PEP 668 system (Homebrew Python, most Linux
distributions). For a throwaway run with nothing installed:

```bash
uv run --with pyyaml --with python-pptx --with lxml --with defusedxml \
    python nbg_build.py outline.yaml output.pptx
```

## Tools

### 1. nbg_build.py - Presentation Builder

Creates complete NBG-formatted presentations from YAML outlines.

```bash
python nbg_build.py outline.yaml output.pptx
python nbg_build.py outline.yaml -o output.pptx   # same thing
```

Exit code 0 means the deck was written **and** passed `nbg_validate.py`. Non-zero means either a
brand violation or a validator that could not run; both print why. The build no longer reports
success on an unvalidated deck.

**Example outline.yaml:**

```yaml
template: GR  # or EN

slides:
  - type: covers/simple_white
    content:
      title: "National Bank of Greece"
      subtitle: "Competitive Analysis"
      location: "Athens, Greece"
      date: "February 2026"

  - type: content/text_with_bullets
    content:
      title: "Market Overview"
      paragraphs:
        - text: "Four systemic banks dominate the market"
          bullet: true
        - text: "Total assets exceed EUR 280 billion"
          bullet: true

  - type: charts/pie_single
    content:
      title: "Market Share"
    chart:
      type: doughnut
      labels: ["NBG", "Eurobank", "Piraeus", "Alpha", "Others"]
      values: [27, 23, 21, 19, 10]

  # Multi-series charts use chart.data. This is the canonical shape and the one
  # all three files in examples/ use; chart.labels + chart.values above is the
  # single-series shorthand.
  - type: chart
    content:
      title: "Digital channel adoption"
      description: "Digital transaction share by segment"
      source:
        name: "NBG MIS"
        as_of: "31 December 2025"
        basis: "excludes cash advances"   # optional
    chart:
      type: bar          # bar | bar_stacked | bar_horizontal | line | doughnut | pie
      data:
        categories: ["Retail", "Affluent", "Business"]
        series:
          - name: "Q4 2024"
            values: [68, 72, 45]
          - name: "Q4 2025"
            values: [78, 85, 58]

  - type: tables/half_page
    content:
      title: "Key Metrics"
      source:
        name: "Published peer disclosures"
        as_of: "31 December 2025"
    table:
      headers: ["Metric", "NBG", "Eurobank", "Piraeus", "Alpha"]
      rows:
        - ["Assets (B)", "78.5", "82.1", "75.3", "71.2"]
        - ["CET1 %", "17.2%", "15.8%", "14.9%", "15.2%"]
      highlight_column: 1

  - type: back_covers/plain_logo
```

`content.description`, where present, renders as a 12pt caption under the title and pushes the body
down; it is not decoration and it is not dropped.

**`content.source` is required on every chart and table slide, and the build fails without it.** An
unsourced number in a board pack cannot be re-derived, cannot be challenged in the room and cannot
be defended to a supervisor afterwards, so `nbg_validate.py`'s Exhibit Sources check is an error
rather than a warning. The field is a mapping:

| Key | Required | What it carries |
|---|---|---|
| `name` | yes | Where the number came from |
| `as_of` | yes | When it was true. A source without one is only half a source |
| `basis` | no | The definitional caveat: constant currency, restated, scope |

It renders as a single 11pt Caption Gray footnote on the content floor at y=6.55", below the
exhibit, per `brand-system/typography.md` ("Table Notes (footnote)") and Standard #11's 11pt floor
for sources. `source: "Source: NBG MIS, 30 June 2026"` is accepted as a plain string and taken as
the finished line, but the mapping is the shape to write: it is what makes the as-of date hard to
forget.

**A `source` mapping with no `as_of` fails the build here, before the validator sees the deck.**
The two halves are deliberately asymmetric. `nbg_build` can read the mapping, so it can tell a
missing field from a badly worded sentence and is strict. `nbg_validate` reads a finished PPTX and
can only search the rendered line for a four-digit year, which a year inside a `basis` caveat
("restated for the 2025 change") satisfies without dating anything. Tightening the validator to
match would false-fail hand-authored and third-party decks this builder never made, so it stays
lenient on purpose: airtight on the path that produces almost every deck, a reasonable backstop on
the ones it does not. A plain-string `source` carries no structure to check and is taken as written,
on the same principle.

Note on the example above: a slide that names two or more of the four Greek systemic banks trips the
Bank Branding check unless each bank's official colour and logo are present. That check is doing its
job; the snippet is schema documentation, not a deck that ships as-is.

### 2. inject_chart_data.py - Chart Data Injection

Injects real data into chart placeholders.

```bash
python inject_chart_data.py input.pptx chart_config.json output.pptx
```

**Example chart_config.json:**

```json
{
  "charts": [
    {
      "slide": 2,
      "chart_index": 0,
      "type": "doughnut",
      "title": "Market Share",
      "data": {
        "labels": ["NBG", "Eurobank", "Piraeus", "Alpha"],
        "values": [27, 23, 21, 19]
      }
    }
  ]
}
```

### 3. inject_table_data.py - Table Data Injection

Injects real data into table placeholders.

```bash
python inject_table_data.py input.pptx table_config.json output.pptx
```

**Example table_config.json:**

```json
{
  "tables": [
    {
      "slide": 1,
      "table_index": 0,
      "data": {
        "headers": ["Metric", "NBG", "Eurobank"],
        "rows": [
          ["Assets", "78.5B", "82.1B"],
          ["CET1", "17.2%", "15.8%"]
        ]
      },
      "highlight_column": 1
    }
  ]
}
```

### 4. nbg_validate.py - Brand Validation

Validates presentations against NBG brand guidelines.

```bash
python nbg_validate.py presentation.pptx
```

**Output:**

```
NBG Brand Validation Report
==================================================
File: quarterly-report.pptx
==================================================

✓ Slides: 11 slide(s) in presentation
✓ Dimensions: 13.33" x 7.50" (NBG standard = LAYOUT_WIDE)
✓ Colors: All 8 colors within NBG palette
✓ Fonts: Fonts used: Aptos
✓ Logo: 2 media file(s) found (verify NBG logo manually)
✓ Back Cover: Last slide appears to be a plain back cover
✓ Boundaries: 44 positioned element(s), all within slide boundaries
✓ Contrast: 62 run(s) measured, all clear WCAG AA; 7 brand-mandated exception(s)
    - Slide 1: #939793 on #FFFFFF is 2.96:1 (needs 4.5:1 at 14.0pt) [Medium Gray, brand-mandated for page numbers and cover dates]
    - Slide 10: #939793 on #FFFFFF is 2.96:1 (needs 4.5:1 at 10.0pt) [Medium Gray, brand-mandated for page numbers and cover dates]
    - Slide 3: #939793 on #FFFFFF is 2.96:1 (needs 4.5:1 at 10.0pt) [Medium Gray, brand-mandated for page numbers and cover dates]
    - Slide 4: #939793 on #FFFFFF is 2.96:1 (needs 4.5:1 at 10.0pt) [Medium Gray, brand-mandated for page numbers and cover dates]
    - Slide 5: #939793 on #FFFFFF is 2.96:1 (needs 4.5:1 at 10.0pt) [Medium Gray, brand-mandated for page numbers and cover dates]
✓ Decorative: 44 preset shape(s), none decorative
✓ Chart Types: 2 chart(s), no pie/doughnut
✓ Thank You Check: 11 slide(s) scanned, no "Thank You" text (correct)
✓ Text Margins: 33 text box(es), all with zero margins
✓ Safe Zones: 38 element(s) across 11 slides, all within safe zones
✓ Font Sizes: 62 sized run(s) all meet minimum sizes. Sizes used: 9.0pt, 10.0pt, 11.0pt, 12.0pt, 14.0pt, 24.0pt, 36.0pt, 48.0pt, 60.0pt
✓ Content Spacing: 8 slide(s) with body content, all adequately spaced below the title
✓ Title Length: 6 title(s) all fit within the 80-char single-line limit
○ Bank Branding: 0 bank name(s) found, so no multi-bank comparison to check
✓ Slide Titles: 10 slide(s) titled, all present and unique, 1 text-free slide(s) exempt
✓ Exhibit Sources: 3 exhibit slide(s), all carrying a dated source line
✓ Alt Text: 3 object(s) carry descriptive alt text, 11 brand logo(s) exempt as decorative
✓ Zero Baseline: 1 bar/column value axis/axes, all based at zero, 1 non-bar chart(s) not subject to the rule
✓ Number Formats: 11 currency amount(s), consistent notation and precision
✓ AI Slop: 10 slide(s) scanned against 13 lexicon terms, none clustering 2+
✓ Action Titles: 6 content title(s), all assertions within 15 words

==================================================
Summary: 23 passed, 0 failed, 0 warning(s), 1 examined nothing
No blocking failures; 1 check(s) marked with a circle examined nothing.
==================================================
```

Every check reports **how many candidate elements it looked at**, and a check that looked at none
prints a circle rather than a tick. It is not counted as a pass. Three checks used to iterate
`a:rPr`, which `nbg_build.py` never writes (it sets fonts at paragraph level, `a:defRPr`), so they
examined an empty set on every deck this repo produces and printed green. `Font Sizes` gave itself
away by printing `Sizes used:` with nothing after it.

`Contrast` measures a real WCAG ratio for every run against the fill actually behind it: the
nearest ancestor shape fill, then the slide background, then white. Chart data labels are measured
against their series or point fill when the label sits on the mark, and against the slide
background when it sits outside. One colour is listed as a brand-mandated exception rather than a
failure, with its measured ratio shown on every run: see `BRAND_CONTRAST_EXCEPTIONS`.

**Exit codes.** 0 clean, 1 a check failed, 2 the validator could not finish. `nbg_build.py` keeps
those apart, so a validator that dies on a missing import is no longer indistinguishable from a
clean deck.

## Slide Catalog

Available slide types (see `assets/slide-catalog.yaml`):

`nbg_build.py` has six renderers, and every catalog path routes to one of them. The prefix is what
decides; the suffix is a hint for a human, not a distinct layout.

| Prefix or type | Renderer | What it draws |
|---|---|---|
| `cover`, `covers/*` | `create_cover_slide` | Title, subtitle, location, date, large logo |
| `divider`, `dividers/*` | `create_divider_slide` | Two-digit number plus section title |
| `contents`, `toc` | `create_contents_slide` | Numbered section list with teasers |
| `chart`, `charts/*`, `*_chart` | `create_chart_slide` | Bar, stacked bar, horizontal bar, line, doughnut |
| `waterfall`, `waterfall_chart` | `create_waterfall_slide` | Stacked-bar waterfall, cyan up and red down |
| `table`, `tables/*` | `create_table_slide` | Header row, zebra body, right-aligned numbers |
| `back_cover`, `back_covers/*` | `create_back_cover_slide` | Centred oval logo, nothing else |
| anything else | `create_content_slide` | Title plus cyan bullets |

Two consequences worth knowing before you write a spec:

- **`infographics/*` has no renderer.** It falls through to the content slide. `content.items`
  (a list of `{title, description}`) degrades to bullets rather than being dropped, which is what
  used to happen, but it is not a numbered grid.
- **The suffix is ignored.** `charts/bar_dual` and `charts/bar_single` both draw one chart; the
  number of series in `chart.data.series` is what varies. `tables/half_page` and `tables/full_page`
  both size the table from its row count, shrinking the rows to stay inside the body area.

## NBG Brand Guidelines

### Dimensions

- Width: 13.33 inches (LAYOUT_WIDE)
- Height: 7.5 inches
- Matches LAYOUT_WIDE standard

### Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Dark Teal | #003841 | Titles, headings |
| NBG Teal | #007B85 | Primary brand |
| Bright Cyan | #00DFF8 | Accents |
| Cyan | #00ADBF | Charts, bullets |
| Dark Text | #202020 | Body text |
| White | #FFFFFF | Background |

### Chart Colors (in order)

1. #00ADBF - Cyan
2. #003841 - Dark Teal
3. #007B85 - NBG Teal
4. #939793 - Medium Gray
5. #BEC1BE - Light Gray
6. #00DFF8 - Bright Cyan

### Fonts

- Primary: Aptos
- Bullets: Arial
- Fallback: Calibri, Tahoma

### Rules

- Always use white or off-white backgrounds
- **Never include "Thank You" slides**
- Always end with plain back cover with logo
- Section numbers: "01", "02" format in NBG Teal
- Bullets use Cyan #00ADBF
- All text boxes: margin = 0
