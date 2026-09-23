# NBG Presentation Style Guide

This file holds the **Required NBG Brand Standards**: the numbered, non-negotiable rules every
NBG-branded deck follows. It ships with the plugin, is the same for every colleague, and is never
edited by a tool. Each user's learned preferences live beside it, in their own overlay (see
"Per-user style preferences" at the end).

---

# Required NBG Brand Standards

These are hard rules enforced for every NBG deck. Brand-system files (`brand-system/colors.md`, `brand-system/layouts.md`, `brand-system/charts.md`, `brand-system/typography.md`) carry the detailed specs, and `brand-system/tokens.yaml` holds every value in machine-readable form; this section codifies the must-follow rules. Where a Standard and a brand-system file disagree, the Standard wins, and tokens.yaml encodes the outcome.

Where a Standard reaches into a file it does not own, it states the requirement rather than describing what that file currently says, and it pins any value it cites inline. A normative claim stays true when the other file changes; a descriptive one goes silently false the moment someone edits the target, and a Standard citing a source that now contradicts it is worse than no Standard.

## 1. Primary brand color is NBG Teal `#007B85`, not Green

In every NBG artifact (deck, doc, email, RTF, SVG, chart), use **`#007B85` (NBG Teal)** wherever previous guidance specified **`#006141` (NBG Green)**. Green is retired. The earlier `#003841` (Dark Teal) remains valid for accents like table footers/totals; only the green → teal swap is universal.

After generating any NBG-branded artifact, scan output for `006141` or `0, 97, 65`. None should remain.

## 2. PPTX brand rules: non-negotiable defaults

1. **White backgrounds on ALL slides**: cover, dividers, content, back cover. Never dark teal or colored backgrounds.
2. **No accent/separator lines under titles**: no thin teal lines, no decorative rules. Clean whitespace only.
3. **No tiny text**: body content ≥14pt, and nothing below the floor. Standard #11 states the one floor and the per-element minimums. Vision/summary slides go large (16-18pt+).
4. **Org charts show the level the decision needs**: the full hierarchy down to the units the audience acts on, not just the top boxes.
5. **Staffing tables show both directions**: departures AND hiring needs, at the level where the decision is taken.
6. **Project tables need structure**. Columns: `#`, Name, Description, Status, Deadline. Not just name + status dot.
7. **Fill the slide**: content should use 60-85% of safe area. Half-empty slides waste attention. If there's space, increase font size.
8. **Area-line charts for time-series**: never plain line charts. Use area chart with subtle fill (15% opacity), hollow circle markers (Standard #5), no grid/axis lines, muted gray value-axis labels. Pair with KPI callout (large metric value + change delta) beside the chart.

## 3. Section dividers: minimal, no decorations

NBG section divider slides contain ONLY:
- The large section number (e.g., `01` / `02` / `03`) in NBG Teal `#007B85`
- The section title text in Dark Teal `#003841`
- **Number and title sit on the SAME ROW (horizontal layout)**: number on the left starting at the gutter (x=0.374), title immediately to its right, both sharing the same baseline. **Never stack the title under the number.**
- White background
- **Large NBG logo bottom-left** (same position as the cover slide, `(0.374, 6.271)`, `2.191"×0.630"`), NOT a small top-right logo
- **NO decorative line, rectangle, half-oval, or other brand shape anywhere**
- No page number on divider slides

Brand discipline = restraint, not decoration. A divider is always "horizontal number-and-title, large logo bottom-left, no decorative element"; verify it in the QA pass.

## 4. Logo proportions: preserve native aspect ratio

When inserting any logo (NBG, peer banks, partners) into a deck, ALWAYS preserve the source asset's native aspect ratio.

- Read the actual PNG/SVG dimensions before placing
- Set either height OR width and let the other auto-scale
- For peer-comparison charts: pick a consistent height (e.g., 24-32 px) and let widths vary
- Never set both dimensions independently
- Especially important for peer comparisons: NBG's logo is oval; other Greek banks (Eurobank, Alpha, Piraeus) have rectangular logos with different aspect ratios. Forcing uniform square distorts identity

## 5. Line charts: hollow circle markers

All line charts in NBG presentations use hollow circle markers: white fill center with a colored outline ring whose stroke width matches the line itself (typically 3.5pt / 44450 EMU).

- `marker.symbol = circle`, `marker.size = 6`
- For python-pptx, set marker `spPr`: `<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>` for fill, `<a:ln w="44450"><a:solidFill><a:srgbClr val="{LINE_COLOR}"/></a:solidFill></a:ln>` for outline
- Apply to ALL line chart series, including area-line charts (NPE convergence style)
- 3.5pt is the width for every **data line**, which is any stroke a reader traces to read a value
- It does **not** cover an area **fill boundary**. On a stacked-area chart the stroke outlines a region rather than carrying the data, and `brand-system/charts.md` sets it at 2.5pt. That is correct and deliberate, not drift. A single-series area-line chart is still a data line: 3.5pt.

Hollow markers maintain distinction where lines converge or cross. Solid-fill markers merge visually at close proximity.

## 6. PPTX media preservation: verify on every round-trip

When a user manually edits a PPTX in PowerPoint and re-saves, embedded media files (logos, images) can be silently stripped, leaving empty placeholder shapes that render as blank rectangles.

**Before any incremental render that opens a user-edited PPTX**, check media file count:
```bash
unzip -l <file> | grep "ppt/media/" | wc -l
```

If media count is 0 OR significantly lower than the previous version: **FLAG to the user immediately** and offer to restore media from a known-good earlier version.

After saving any incremental render, verify media count is preserved. For round-trip workflows where the user will edit in PowerPoint and return, keep a reference master with full media as the restore source.

## 7. No em-dashes

Never use em-dashes (`—` or `--`) in slide text, titles, callouts, footnotes, or table cells. They read as AI-generated and signal Claude authorship, which is unacceptable in executive deliverables, especially decks shared internally at NBG and externally.

Replace with: comma, colon (introducing a list/explanation), semicolon (joining two clauses), or full stop (when the second clause stands alone). Same restraint for en-dashes used parenthetically; date/number ranges with en-dash are fine (`2024-2025`).

The rule binds this guide and every other prompt file in the plugin, not only the slides they produce. A model imitates the punctuation it reads far more reliably than it obeys a rule it reads once.

## 8. Never invent NBG names

Do not guess or fabricate names of NBG executives, division heads, or organisational roles. If a name isn't known from your personal shared memory, email history, or current conversation, **ASK**, never guess.

Acceptable framings when name is unknown: `NBG [Division] leadership`, `the relevant [Division] head`, `the NBG [Division] team`.

## 9. No version suffixes in filenames

Never append `_v1`, `_v2`, `_v1_0`, `_final`, `_revised`, `_draft` suffixes to filenames. The `YYYYMMDDHHMM_` timestamp prefix IS the version. Iterating on `202604271045_quarterly_review.pptx`? Save the next version as `202604271203_quarterly_review.pptx`, NOT `202604271045_quarterly_review_v2.pptx`.

Applies to ALL file types: PPTX, PDF, SVG, HTML, RTF, PNG, JPG, CSV, MD, JSON.

## 10. Logo language: Greek only

Use `nbg-logo-gr.png` (Greek `ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ`), never the English fallback.

## 11. Composition standards (partly enforced by nbg_validate.py)

- **Minimum font sizes.** The absolute floor for content text is **10pt**. Named minimums above it:

  | Element | Minimum |
  |---|---|
  | Body bullets, card/pillar body text | 14pt |
  | Card titles | 16pt |
  | Metric card labels | 12pt |
  | Callout text | 12pt |
  | Table cells | 12pt |
  | Table headers | 12pt |
  | Footnotes, sources, phase/badge labels | 11pt |

  These are minimums, not targets; where a slide has room left, spend it on size. The 8pt footnote allowance is retired: a footnote is 11pt like any source line. One element sits below the floor and stays there, because it is chrome rather than content: the section pill (bumper/eyebrow) at 9pt, per `brand-system/README.md`. The page number sits on the floor at 10pt. This table is the single source for font floors; Standard #2 item 3 defers to it.
- **Titles fit one line**: 24pt Aptos across the 12.59" content width, at most 80 characters (`tokens.yaml` `type.title.max_chars`). Overflow to a second line looks amateurish.
- **Breathing room below titles**: first body element at y≥1.3" (the title box ends at 0.9", or 1.15" under a section pill).
- **Fill the slide**: use 60–85% of safe area.

`nbg_validate.py` checks these programmatically; its checks are listed in `tools/nbg-presentation/README.md`. The builder gets sizes right on the first pass rather than leaning on the check.

## 12. Tight rounded-rect corners

Rounded rectangle shapes in NBG presentations (cards, KPI boxes, callout containers) use **tight corner radius**, not the default large rounding.

- Cards, KPI tiles and callouts: corner radius **0.04"** whatever the card's size (`tokens.yaml` `components.card.radius_in`). In python-pptx that is `shape.adjustments[0] = 0.04 / min(width, height)`, both in inches; a flat `adjustments[0] = 0.04` would round a tall card several times more
- **Exception**: section pills have fully rounded ends, radius **0.15"**, half their 0.3" height (`components.pill.radius_in`, `adjustments[0] = 0.5`), since they're small accent elements

Default radius (~0.167) looks amateur and "bubbly." Tight corners give a more mature, design-professional appearance appropriate for executive decks.

## 13. Cover slide titles on one line

Cover slide titles and subtitles must each fit on **one line**. Never allow them to wrap to two lines when there is clearly enough horizontal space.

- Use the full available width (up to 12.0" for titles) so even long titles stay on one line
- If a title genuinely cannot fit in one line at 48pt across 12", **shorten the text** rather than wrap
- The subtitle follows the same rule: single line

A wrapped cover title looks unpolished and wastes the wide 13.33" slide. The cover is the first impression; it must look deliberate and clean, not like text overflow.

## 14. Presentation preparation workflow

For executive-level decks, follow an outline-first collaborative approach:

1. **Research phase**: query knowledge sources (second brain, email history, decision logs) for content
2. **Outline phase**: present a detailed slide-by-slide outline with proposed action titles and bullet content. Note what data is available and what gaps remain.
3. **Iterate**: review with stakeholder, add/remove slides, adjust emphasis, fill in missing numbers
4. **Build**: only invoke `/create-presentation` after the outline is agreed
5. **Brand compliance**: read ALL NBG brand system files before building

## 15. Titles ALWAYS left-aligned at x=0.374" (logo gutter)

Every slide title (cover, contents, divider, content, back cover) must left-align at **x = 0.374 inches**, the same vertical line as the bottom-left NBG logo. This creates a single consistent left gutter across the whole deck that the eye locks onto.

Do not start a gutter-anchored title at `x=0.5` or `x=0.37`. Do not center them. Do not right-align them. The only correct value is **0.374"**.

The gutter binds the **leftmost element on the slide**. On a section divider that element is the section number, not the title: per Standard #3 the number sits at 0.374 and the title sits immediately to its right, sharing the baseline. A divider title is therefore the one title that does not start at 0.374, and that is correct.

Applies to:
- Cover title and subtitle
- Contents page title and the section list rows
- Section divider: the **number** anchors at 0.374" and the title follows it on the same row (the pair is vertically centred as one block)
- Content slide titles (action titles, page headers)
- Back cover text if any

Subtitles, eyebrows, footnotes, and the first body element on the slide follow the same x=0.374 gutter. The right edge is the mirror of it, and `brand-system/dimensions.md` is where that value lives; do not restate it here or in an agent.

The bottom-left NBG logo is the anchor. Its x is always 0.374; only its y and size change by slide type, per Standard #17: `(0.374, 6.271)` for the large logo on covers and dividers, `(0.374, 7.071)` for the small logo on contents and content slides. Every text block on the left of the slide must align with that shared left edge. When in doubt, draw an imaginary vertical line up from the logo's left edge; titles touch it.

## 16. Titles are NEVER bold, always Regular weight

Slide titles use Aptos **Regular (400)**, never Bold (700). This applies to:
- Cover titles (44–48pt Regular)
- Contents page heading (24pt Regular)
- Section divider numbers + section titles (Regular: 60pt numbers, 48pt titles)
- Content slide titles / action titles (24pt Regular)
- Back cover title if any

Bold is reserved for elements that need to pop **within** the body, not for titles. The allowed bold elements are:
- KPI big numbers (50pt Bold #007B85, the canonical NBG executive pattern)
- Table headers (12pt Bold)
- Chart data labels above bars (12pt Bold #003841)
- Chart titles (12pt Bold #202020)
- Status pills text (white Bold on filled background)
- Inline emphasis within paragraph text where genuinely needed

In code: every title-class textbox is created Regular (`bold=False`, or no bold at all), which is what `tokens.yaml` `type.*.bold` says for every title role. Code-review checklist: grep the builder for `bold=True` and confirm none of the matches are on a title element.

Regular weight at the large title sizes (24–48pt) reads as confident and modern; bold at the same sizes reads as shouting. The NBG executive aesthetic is restraint.

## 17. Logo sizing: large on cover/dividers, small everywhere else

Two logo positions exist; pick the right one based on slide type. **Never use the small logo on a cover or a divider.**

| Slide type | Logo position | Size | EMU spec |
|---|---|---|---|
| Cover | bottom-left, LARGE | 2.191"×0.630" | `(0.374, 6.271)` |
| Section divider | bottom-left, LARGE | 2.191"×0.630" | `(0.374, 6.271)` |
| Contents | bottom-left, small | 0.822"×0.236" | `(0.374, 7.071)` |
| Content slides | bottom-left, small | 0.822"×0.236" | `(0.374, 7.071)` |
| Back cover | centred, oval emblem | 2.45"×1.54" | `(5.44, 2.98)` |

The asymmetry is intentional: cover and dividers are statement slides where the brand mark should carry weight; content slides are working pages where the brand should anchor without competing with data. **There is no "small logo on a divider" or "large logo on a content slide" exception.**

Use `nbg-logo-gr.png` (Greek wordmark) for the large variant, never the English fallback (Standard #10).

## 18. Contents page: discreet, no page numbers, no separator lines

The contents page is a quiet wayfinder, not a feature slide. Conventions:

- **Header**: "Contents" at 24pt Regular `#003841`, x=0.374, y=0.40 (Standards #15 + #16 apply)
- **Section rows**: a compact list, typically 3–7 items. Each row carries:
  - Section number (e.g. `01`) at NBG Teal `#007B85`, Regular weight, 18–24pt, left-anchored at x=0.374
  - Section title at Dark Teal `#003841`, Regular weight, 16–22pt, indented to align with the number's right edge
  - Optional one-line teaser at Caption Gray `#5A5F5A`, Regular 12pt, on the same row or just below
- **DO NOT include page references** (`p. 3`, `p. 5`, etc.). The contents page communicates the shape of the deck, not navigation hints.
- **DO NOT add separator lines, rules, or boxes between rows**. Whitespace alone separates rows.
- **DO NOT add bullets, dots, or arrows in front of numbers**. The number itself is the marker.
- **Small NBG logo bottom-left** (per Standard #17), no page number on the contents page itself if the deck is short; otherwise it gets one like any content slide.

The contents page is a moment of pause, not a heatmap. If it looks designed, it is over-designed.

## 19. Back cover: white slide, centred oval emblem only

Every NBG deck closes with a back cover. The pattern is fixed and minimal:

- White background, full bleed
- **Only one element**: the oval NBG emblem (`nbg-back-cover-logo.png`), centred at `(5.44, 2.98)`, sized `2.45"×1.54"`
- **No text**: no "Thank you", no "Questions?", no closing tagline, no date, no department line
- **No page number**
- **No bottom-left logo** (the centred oval IS the logo for this slide)
- **No decorative elements**

The back cover is a clean exit. If a closing sentiment is needed, put it on the second-to-last content slide ("Next steps", "Decisions for ExCo"), never on the back cover.

This is non-negotiable and applies even to short showcase/demo decks. A 3-slide deck still gets a back cover. A 30-slide deck gets the same back cover. There is exactly one shape per back cover, and it is the oval emblem.

## 20. ONE format, elements chosen by message, never a per-use-case format

There is a single NBG deck format. Do NOT build a different format for a different use case: there is no "business-case format", no "CEO-deck format", no "strategy-deck format". Every deck, whatever its purpose, uses the SAME chassis:

- 13.333"×7.5" canvas, white background, 0.374" left gutter (Standard #15)
- Aptos throughout; titles Regular weight (Standard #16)
- Section pill / eyebrow, action title, subtitle
- Bottom-left Greek logo + page number (Standards #10, #17)
- `#F5F8F6` cards with tight corners (Standard #12), NBG palette (`brand-system/colors.md`)

What changes between decks is which **elements** you place on that chassis, chosen by what each slide needs to SAY, not by a deck-type template:

| The slide needs to say... | Element to use |
|---|---|
| a journey / who-owns-what | process flow (icon tiles + arrows + ownership legend) |
| here are the alternatives | parallel comparison cards/slides (identical layout, only labels/colour-coding change) |
| here are the headline numbers | KPI / stat tiles |
| this is the pick | recommended-option highlight |
| these are the risks | warning flags (orange square + ALL-CAPS label) |
| the bottom line | takeaway strip |

Each element's spec (geometry, colours, type) is in `brand-system/layouts.md` → "Element Specs".

Assemble elements freely: one deck can mix stat tiles, option cards, and a takeaway strip if the argument needs all three. The format holds the deck together; the elements carry the message.

**Exactly one exception exists, Standard #21 (keynote mode), and the list is closed.** Do not read #21 as permission to add a third.

## 21. Keynote mode: the one exception, and it is fenced

A keynote is a talk given from a stage, not a deck. For that case only, NBG has a second, **dark full-bleed** format: cinematic photography, teal scrims, a huge type scale, no page numbers. It deliberately breaks four rules in `brand-system/README.md`: white backgrounds only, no dark bg with light text, no shadows, content titles at 24pt.

Full spec: **`brand-system/keynote.md`**. Generator: `tools/nbg-keynote/nbg_keynote.py`, run as `decks-py keynote`.

**Entry criteria (all four must hold). If any fails, use the light format:**

1. Audience is **external or bank-wide** (conference, town hall, industry panel), not a committee, board or ExCo working session.
2. **Delivered live from a stage by a speaker**, not read alone, not circulated as a document.
3. **Projected large, in a darkened room.**
4. The slides are the **backdrop, not the record**: the argument lives in the speaker notes.

Never for ExCo, board, credit committee, or any deck someone else will edit: keynote slides are flattened images and can only be regenerated from their YAML, never edited in PowerPoint.

**What keynote mode does NOT change**: Greek wordmark always (#10), Aptos always, the teal family, left-gutter alignment, action titles, no em-dashes (#7), no invented NBG names (#8), no version suffixes (#9), accessibility (#22). It is the same brand inverted, not a second identity.

## 22. Accessibility: measured contrast, and colour is never the only signal

NBG decks are projected, printed, and read by colleagues with colour-vision deficiency, and liability for an inaccessible deliverable sits with the bank as service provider, not with any tooling vendor: the first EU suits were filed in the French Commercial Court on 12 November 2025, and in June 2026 a court ordered Carrefour France to remediate within six months under a daily penalty.

**Which standard to build to, as of today.** EN 301 549 V4.1.1 was published on 2 September 2026 and adopts WCAG 2.2 AA for web, non-web documents and software. It does **not** yet carry presumption of conformity; that arrives only on citation in the EU Official Journal, scheduled for 30 November 2026. So: **certify against EN 301 549 V3.2.1 / WCAG 2.1 AA today, and gap-test against WCAG 2.2 now** so nothing has to be rebuilt in December. Build to the WCAG 2.x relative-luminance ratio in every case. Both rules below apply to the light format and to keynote mode. This is a standard, not a third format.

**Contrast.** Text on a filled shape (pill, card, KPI tile, table header, chart bar) needs **4.5:1** against its fill, or **3:1** only when it is 18pt regular or 14pt bold and above. Note what that excludes: a 12pt bold chart data label is **not** WCAG large text, so it is held to 4.5:1. Ratios below are WCAG 2.1 relative luminance computed against `brand-system/colors.md`:

| Text on fill | Ratio | Verdict |
|---|---|---|
| White on Dark Teal `#003841` | 12.79:1 | safe |
| White on NBG Teal `#007B85` | 5.03:1 | safe |
| White on `#008000` (OK pill) | 5.14:1 | safe |
| White on `#CC0000` (Warn pill) | 5.89:1 | safe |
| `#202020` on Cyan `#00ADBF` | 6.00:1 | the data-label colour for cyan bars |
| `#202020` on Bright Cyan `#00DFF8` | 10.02:1 | safe |
| White on Cyan `#00ADBF` | 2.72:1 | FAILS, use `#202020` (6.00:1) |
| White on Bright Cyan `#00DFF8` | 1.63:1 | FAILS, use `#202020` (10.02:1) |
| White on `#CC9900` (TBD pill) | 2.58:1 | FAILS, use `#202020` (6.30:1) |
| White on Gold `#D9A757` | 2.18:1 | FAILS, use `#202020` (7.46:1) |
| White on `#73AF3C` (corporate Success) | 2.65:1 | FAILS, use `#202020` (6.15:1) |
| `#939793` on white | 2.96:1 | page numbers and muted axis labels only, never body or label text |

**When a light fill needs dark text, the answer is `#202020`, the body-text colour.** It beats `#003841` on every fill above; `#003841` also clears, at 4.71:1 to 5.86:1, but with far less headroom. Do not introduce a third dark.

Three brand-system specs used to put white on a light fill and have been corrected to `#202020`: the amber TBD pill and the gold RECOMMENDED tab in `colors.md`, and the waterfall data label in `charts.md`, which keeps `FFFFFF` on `#003841` and `#007B85` bars but never on `#00ADBF`. In each case the fix was the text colour, not a new fill. Keep it that way: inventing a fill to solve a contrast problem pushes the palette toward the ceiling below.

**Picking a label colour automatically.** The black-or-white decision threshold is relative luminance **0.179**, exactly `sqrt(0.0525) - 0.05`. That is where white-on-fill and black-on-fill contrast are equal at `sqrt(21)` = 4.58:1, so always taking the better of **pure** black and **pure** white clears AA on any fill. The guarantee is fragile in two specific ways, both of which this repo has hit:

- **It evaporates the moment the dark option is softened.** With `#202020` (L=0.01444) instead of pure black, the crossover moves to L=0.2101 where the best available ratio is only **4.036:1**, under the AA floor. `tools/nbg-presentation/nbg_build.py` must therefore use pure black as the dark candidate in its label picker specifically. That is a property of the automatic picker, not a new brand colour: hand-specified dark text on a brand fill stays `#202020`. Do not "tidy" the two back together.
- **The naive formulas skip gamma and misclassify exactly this palette.** `(R+G+B)/3`, HSL lightness and `YIQ > 128` produce **17 wrong picks across 27 NBG colours**, including `#00ADBF`, the primary chart series colour, which all three send white text onto a fill that needs dark. Compute real relative luminance; never approximate.

**Colour is never the only carrier of meaning.** Every status, series, or segment distinction must also carry a word, a shape, or a position. To a deuteranope the DIY status colours are one swatch: `#008000` simulates to `#6A6A12` and `#CC0000` to `#7B7B00`, a luminance ratio of 1.15:1. So a status pill carries its word ("Delivered", "At risk"), a risk flag keeps the orange square AND the ALL-CAPS label (Standard #20), a traffic-light table puts the status word in the cell or keeps its legend row, and chart series get direct labels rather than a colour-only legend.

**Categorical series ceiling: six practical, eight absolute.** Beyond eight, keeping fills distinguishable under colour-vision-deficiency simulation is not achievable. There is an OOXML trap on top of that: a native PowerPoint chart auto-generates lighter and darker variants of theme Accent 1-6 once you exceed six series, so a palette validated at six silently degrades into eight near-identical tints with no code change and no warning. Past six categories, use small multiples or group the tail into "other".

**Deuteranopia-safe pairings inside the palette.** The teal chart sequence survives simulation because it separates on lightness rather than hue: `#00ADBF` against `#003841` is 4.71:1 and holds. `#007B85` against `#939793` is 1.70:1 and does not, and the chart sequence (`tokens.yaml` `charts.palette`) puts them consecutive as series 3 and 4, so never let those two alone carry a distinction: label the series directly. When two fills must be told apart by colour, take them from opposite ends of the lightness range (`#003841`, `#007B85`, `#BEC1BE`, `#FFFFFF`).

---

# Per-user style preferences

What a user teaches the system lives outside the plugin, in
`${CLAUDE_PLUGIN_DATA}/style-preferences.md` (for this plugin,
`~/.claude/plugins/data/decks-plessas-marketplace/style-preferences.md`). The agents read it after
this guide, on every deck. It survives plugin updates, belongs to one person, and is never
committed to this repository. It has three parts:

- **Defaults**: what the user writes by hand, such as the units on their cover subtitle, a
  preferred sign-off, recurring audiences, their team's deck conventions.
- **Learned**: what `/presentation-review` found by comparing a shipped draft with the version the
  user finalised, with how often each pattern has been seen. One review is a hint to lean toward;
  two or more make it a rule for that user.
- **Not applied**: patterns in the user's edits that a Standard rules out, recorded so they are
  not relearned.

It is an overlay, never an override:

- **The Standards above win on every conflict.** A preference can pick among options a Standard
  leaves open (a density, a chart type, a phrasing, a default layout); it cannot break a Standard.
- **Personal context goes there, not here.** This guide is public and serves every colleague.
- **A preference reaches this guide only by a deliberate commit** that turns it into a numbered
  Standard for everyone.
