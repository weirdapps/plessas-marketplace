# NBG Presentation Style Guide

This file has two parts:

1. **Required NBG Brand Standards** — non-negotiable rules every NBG-branded deck must follow
2. **Learned Preferences** — additional patterns inferred from `/presentation-review` cycles (lower-confidence, auto-updated)

---

# Part 1 — Required NBG Brand Standards

These are hard rules enforced for every NBG deck. Brand-system files (`brand-system/colors.md`, `brand-system/layouts.md`, `brand-system/charts.md`, `brand-system/typography.md`) carry the detailed specs; this section codifies the must-follow rules.

## 1. Primary brand color is NBG Teal `#007B85` — not Green

In every NBG artifact (deck, doc, email, RTF, SVG, chart), use **`#007B85` (NBG Teal)** wherever previous guidance specified **`#006141` (NBG Green)**. Green is retired. The earlier `#003841` (Dark Teal) remains valid for accents like table footers/totals — only the green → teal swap is universal.

After generating any NBG-branded artifact, scan output for `006141` or `0, 97, 65` — none should remain.

## 2. PPTX brand rules — non-negotiable defaults

1. **White backgrounds on ALL slides** — cover, dividers, content, back cover. Never dark teal or colored backgrounds.
2. **No accent/separator lines under titles** — no thin teal lines, no decorative rules. Clean whitespace only.
3. **Font sizes ≥14pt for body content** — body bullets ≥14pt, table cells ≥11pt minimum (prefer 12pt+). Vision/summary slides go large (16-18pt+).
4. **Org charts go to υδνση level** — show the full hierarchy from Division → Sector → Υδνση, not just sectors.
5. **Staffing tables by υδνση** — show departures AND hiring needs at the sub-division level.
6. **Project tables need structure** — columns: `#`, Name, Description, Status, Deadline. Not just name + status dot.
7. **Fill the slide** — content should use 60-85% of safe area. Half-empty slides waste attention. If there's space, increase font size.
8. **Area-line charts for time-series** — never plain line charts. Use area chart with subtle fill (15% opacity), dot markers, no grid/axis lines, muted gray labels. Pair with KPI callout (large metric value + change delta) in the header.

## 3. Section dividers — minimal, no decorations

NBG section divider slides contain ONLY:
- The large section number (e.g., `01` / `02` / `03`)
- The section title text
- Both vertically centered together as a single visual block, left-aligned
- White background, NBG logo top-right (small)
- **NO decorative line, rectangle, half-oval, or other brand shape on the right side**

Brand discipline = restraint, not decoration. When invoking the graphics-renderer for an NBG deck, explicitly say "no decorative element on right side of dividers" and verify in the QA pass.

## 4. Logo proportions — preserve native aspect ratio

When inserting any logo (NBG, peer banks, partners) into a deck, ALWAYS preserve the source asset's native aspect ratio.

- Read the actual PNG/SVG dimensions before placing
- Set either height OR width and let the other auto-scale
- For peer-comparison charts: pick a consistent height (e.g., 24-32 px) and let widths vary
- Never set both dimensions independently
- Especially important for peer comparisons: NBG's logo is oval; other Greek banks (Eurobank, Alpha, Piraeus) have rectangular logos with different aspect ratios. Forcing uniform square distorts identity

## 5. Line charts — hollow circle markers

All line charts in NBG presentations use hollow circle markers: white fill center with a colored outline ring whose stroke width matches the line itself (typically 3.5pt / 44450 EMU).

- `marker.symbol = circle`, `marker.size = 6`
- For python-pptx, set marker `spPr`: `<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>` for fill, `<a:ln w="44450"><a:solidFill><a:srgbClr val="{LINE_COLOR}"/></a:solidFill></a:ln>` for outline
- Apply to ALL line chart series, including area-line charts (NPE convergence style)
- Same line width (3.5pt) is standard for all series lines

Hollow markers maintain distinction where lines converge or cross. Solid-fill markers merge visually at close proximity.

## 6. PPTX media preservation — verify on every round-trip

When a user manually edits a PPTX in PowerPoint and re-saves, embedded media files (logos, images) can be silently stripped, leaving empty placeholder shapes that render as blank rectangles.

**Before any incremental render that opens a user-edited PPTX**, check media file count:
```bash
unzip -l <file> | grep "ppt/media/" | wc -l
```

If media count is 0 OR significantly lower than the previous version: **FLAG to the user immediately** and offer to restore media from a known-good earlier version.

After saving any incremental render, verify media count is preserved. For round-trip workflows where the user will edit in PowerPoint and return, keep a reference master with full media as the restore source.

## 7. No em-dashes

Never use em-dashes (`—` or `--`) in slide text, titles, callouts, footnotes, or table cells. They read as AI-generated and signal Claude authorship — unacceptable in executive deliverables, especially decks shared internally at NBG and externally.

Replace with: comma, colon (introducing a list/explanation), semicolon (joining two clauses), or full stop (when the second clause stands alone). Same restraint for en-dashes used parenthetically; date/number ranges with en-dash are fine (`2024-2025`).

## 8. Never invent NBG names

Do not guess or fabricate names of NBG executives, division heads, or organisational roles. If a name isn't known from your personal shared memory, email history, or current conversation, **ASK** — never guess.

Acceptable framings when name is unknown: `NBG [Division] leadership`, `the relevant [Division] head`, `the NBG [Division] team`.

## 9. No version suffixes in filenames

Never append `_v1`, `_v2`, `_v1_0`, `_final`, `_revised`, `_draft` suffixes to filenames. The `YYYYMMDDHHMM_` timestamp prefix IS the version. Iterating on `202604271045_credit_expansion.pptx`? Save the next version as `202604271203_credit_expansion.pptx` — NOT `202604271045_credit_expansion_v2.pptx`.

Applies to ALL file types: PPTX, PDF, SVG, HTML, RTF, PNG, JPG, CSV, MD, JSON.

## 10. Logo language — Greek only

Use `nbg-logo-gr.png` (Greek `ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ`), never the English fallback.

## 11. Composition standards (programmatically enforced by nbg_validate.py)

- **No tiny text**: body bullets ≥14pt, metric card labels ≥12pt, callout text ≥12pt. The 10pt floor is a minimum, not a target.
- **Titles fit one line**: at 22pt Aptos in 12.59" width, ≤80 chars. Overflow to a second line looks amateurish.
- **Breathing room below titles**: first body element at y≥1.3" (title bottom is at 0.9").
- **Fill the slide**: use 60–85% of safe area.

`nbg_validate.py` (17 checks as of 2026-04-04) catches these programmatically. The renderer should get them right on the first pass to avoid remediation loops.

## 12. Tight rounded-rect corners

Rounded rectangle shapes in NBG presentations (cards, KPI boxes, callout containers) use **tight corner radius**, not the default large rounding.

- `python-pptx`: `shape.adjustments[0] = 0.04` on every `MSO_SHAPE.ROUNDED_RECTANGLE`
- `PptxGenJS`: `rectRadius: 0.04` (or equivalent)
- **Exception**: bumper pills can stay slightly more rounded (~0.15) since they're small accent elements

Default radius (~0.167) looks amateur and "bubbly." Tight corners give a more mature, design-professional appearance appropriate for executive decks.

## 13. Cover slide titles on one line

Cover slide titles and subtitles must each fit on **one line**. Never allow them to wrap to two lines when there is clearly enough horizontal space.

- Use the full available width (up to 12.0" for titles) so even long titles stay on one line
- If a title genuinely cannot fit in one line at 48pt across 12", **shorten the text** rather than wrap
- The subtitle follows the same rule — single line

A wrapped cover title looks unpolished and wastes the wide 13.33" slide. The cover is the first impression — it must look deliberate and clean, not like text overflow.

## 14. Presentation preparation workflow

For executive-level decks, follow an outline-first collaborative approach:

1. **Research phase**: query knowledge sources (second brain, email history, decision logs) for content
2. **Outline phase**: present a detailed slide-by-slide outline with proposed action titles and bullet content. Note what data is available and what gaps remain.
3. **Iterate**: review with stakeholder, add/remove slides, adjust emphasis, fill in missing numbers
4. **Build**: only invoke `/create-presentation` after the outline is agreed
5. **Brand compliance**: read ALL NBG brand system files before building

---

# Part 2 — Learned Preferences

Learned preferences from comparing draft presentations to user-modified finals. Updated automatically by `/presentation-review`.

> **Confidence**: Preferences marked with (1x) are from a single review. They become confirmed rules after appearing in 2+ reviews.

---

## Font Sizing (1x — 2026-04-03)

The user's most consistent change is increasing font sizes. The generated deck used 8-12pt for body text; the user bumped nearly everything up by 2-4pt.

### Minimum Font Sizes (HARD RULE)

- **Absolute minimum**: 9pt — the user removed ALL 7pt and 8pt text
- **Footnotes**: 10.5pt minimum (not 8pt)
- **Phase/badge labels**: 9-10.5pt (not 7-8pt)

### Target Font Sizes by Element

| Element | Generated | User Preferred | Delta |
|---------|-----------|---------------|-------|
| Card/pillar body text | 11-12pt | **14pt** | +2-3 |
| Card titles | 13-14pt | **16pt** | +2-3 |
| Table cells | 10-11pt | **12-14pt** | +2-3 |
| Table headers | 11-12pt | 12pt (kept) | 0 |
| Phase/badge labels | 8-9pt | **10.5pt** | +1.5-2 |
| Foundation bar text | 12-13pt | **14-16pt** | +2-3 |
| Footnotes | 8pt | **10.5-14pt** | +2.5-6 |
| Bullet point text | 11pt | **14pt** | +3 |
| Metric card values | 24pt | 24pt (kept) | 0 |
| Cover subtitle | 36pt | **28pt** | -8 |

### Key Principle

**Fill the available space.** When there's white space left on a slide, increase font sizes rather than leaving it empty. The user prefers larger, more readable text over compact layouts with breathing room.

---

## Title Style (1x)

- **Style**: Direct, action-oriented — full sentences that tell the story
- **Length**: Prefer concise. The user shortened "Transforming NBG's Digital Investment Offering" to "NBG Digital Investment Offering" (dropped the verb)
- **Cover title width**: Full width (12.24") rather than left-half only (7.86")
- **Quantification**: Use data where accurate, but don't inflate — user corrected "10M+" to "5 M+"
- **Language**: English throughout

---

## Content Density (1x)

- **Bullet count**: Fewer is better. User reduced 4 bullets to 1 on slide 14, keeping only the strategic conclusion
- **Bullet length**: Short sentences are acceptable
- **Data inclusion**: Accuracy over impact — user corrected inflated numbers
- **Footnotes/sources**: Keep if meaningful but increase font size; user removed some and enlarged others
- **Legends**: Remove if the table is self-explanatory (user deleted the traffic-light legend row)

### Less-Is-More Principle

The user consistently simplifies:

- Removed an entire decision card (3 → 2) because one was premature/not needed
- Reduced bullets from 4 to 1, keeping only the strategic punch line
- Removed the legend from a color-coded table (obvious without it)

---

## Chart Preferences (1x)

- **Comparison data**: Tables with traffic-light color coding (kept as-is)
- **KPIs**: Metric cards with large values — 24pt is the right size
- **Chart annotations**: Minimal — user removed some footnotes and legends

---

## Slide Ordering (1x)

- **Opening pattern**: Cover + Executive Summary (kept as-is)
- **Section dividers**: Used for 3 sections (kept as-is)
- **Closing pattern**: Decisions + Back Cover (user approved this pattern)
- **Appendix usage**: No appendix — keep the deck lean

---

## Layout Choices (1x)

- **Default content layout**: Cards and visual layouts preferred over bullet lists
- **Text/chart split**: Visual-first — user approved the insight cards replacing bullets on slide 4
- **Decision cards**: When reducing from 3 to 2, user centered the cards (x: 2.06" and 7.05") with wider spacing rather than left-aligning
- **Card sizing**: Cards at 3.9" wide works well for 2-3 column layouts
- **White space**: Use it by increasing font sizes, not by leaving it empty

---

## Narrative Structure (1x)

- **Framework**: SCQA with Pyramid Principle — user kept the overall structure
- **Executive summary**: Always include — user kept slide 2 exec summary
- **Argument structure**: Reduce to essentials. Trim premature decisions; keep only those the audience can act on now
- **Tone**: Bold and assertive — direct titles, clear recommendations
- **Owner attribution**: Prefer cross-functional ownership labels over single-unit attribution

---

## Logo & Branding (1x)

- **Logo language**: Greek only ("ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ") — use `nbg-logo-gr.png`, never the English fallback
- **Back cover**: Oval logo centered, no text (confirmed)

---

## Review History

| Date | Draft ID | Slides Changed | Key Patterns |
|------|----------|---------------|--------------|
| 2026-04-03 | 202604031945_nbg_digital_investments_exco | 1,2,4,5,6,7,8,10,11,12,13,14,16 | Font sizes +2-4pt across all body text; 3→2 decisions; cover title simplified; legend removed; bullets reduced; Greek logo only |
