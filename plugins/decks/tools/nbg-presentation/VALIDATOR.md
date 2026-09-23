# nbg_validate.py: the brand gate

`nbg_validate.py` checks any `.pptx` against the NBG brand and exits non-zero when the
deck breaks a rule. `nbg_build.py` runs it on every build, presentation-qa reads its JSON
as Layer 1, and `/redesign-deck` and `/polish-slides` run it on decks somebody else made.

Every brand value (colours, fonts, type floors, geometry, chart limits) is read from
`shared/brand-system/tokens.yaml` through `tools/nbg_tokens.py`. The validator holds rules,
never a second copy of the brand: change a value in `tokens.yaml` and the gate follows.

## Running it

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate deck.pptx                 # text report
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate deck.pptx --format json   # for agents and CI
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate deck.pptx --strict        # a skipped universal check fails
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate --list-checks --format json
```

Scope: light-mode decks. A keynote (Standard #21) is a dark, full-bleed, rasterised deck that
breaks the light-mode rules on purpose; validate it with the keynote tool instead
(`decks-py keynote ... --validate`).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | No check failed. Warnings and skipped checks may be present. |
| 1 | At least one check failed. With `--strict`, also a skipped check marked universal below. |
| 2 | The validator could not run: file missing, not a zip or not a PowerPoint package, a part over the size limits, a missing Python dependency, or a crash. Exit 2 is never a pass: Layer 1 did not execute. |

## Statuses and the meaning of "examined"

Each check reports one status:

| Status | Meaning |
|---|---|
| `pass` | Examined at least one candidate and found nothing. |
| `fail` | At least one error finding. Blocks the build (exit 1). |
| `warn` | Only warning findings. Reported, never blocking. |
| `skipped` | Passed having examined **zero** candidates. It proves nothing; report it as unverified, never as clean. |

`examined` is the number of candidates the check actually inspected, as defined in the
Candidates column below, and it is set on failures as well as passes. `not_examined`
counts what a check saw but could not judge, with the reason (for example text over a
picture, whose background colour is unknown).

A check can carry findings of both severities. Title Style reports a bold title as an
error and a trailing period as a warning; Chart Data warns past 6 series and fails past 8;
Em Dashes fails an em dash and warns on a spaced en dash.

Slides are numbered by their position in the deck (`p:sldIdLst`), which is also their index
in `deck.yaml`. File names (`slide7.xml`) are ignored: a reordered deck no longer matches them.

## JSON format

`--format json` prints one object on stdout:

```json
{
  "file": "/abs/path/deck.pptx",
  "strict": false,
  "summary": {"passed": 30, "failed": 1, "warnings": 1, "skipped": 2, "checks": 34},
  "checks": [
    {
      "name": "Colors",
      "status": "fail",
      "severity": "error",
      "examined": 41,
      "message": "1 off-palette colour use(s) among 41 colour reference(s)",
      "details": [
        {"slide": 3, "severity": "error", "message": "#FF0000 is not in the NBG palette (tokens.yaml) (in chart chart2)"}
      ],
      "not_examined": {}
    }
  ]
}
```

- `checks` lists every check in the order of the table below.
- `details` is the complete fix list for the check, ordered by slide. `slide` is `null` for a
  deck-level finding (slide size, theme).
- The text report prints the same findings, then a fix list grouped by slide. ANSI colour is
  used only when stdout is a terminal and `NO_COLOR` is unset.

## Check inventory

Sev: E = error (blocks), W = warning (reports). U = universal: applies to every deck, so
`--strict` fails it when skipped.

| Check | Rule | Source | Sev | Candidates (what "examined" counts) | U |
|---|---|---|---|---|---|
| Slides | The deck has at least one slide and every slide-list entry resolves. | implicit | E | slide-list entries | U |
| Dimensions | Slide size is exactly 12192000 x 6858000 EMU (13.333 x 7.5 in, PowerPoint Widescreen), within 635 EMU. | dimensions.md; tokens `geometry.slide` | E | the `p:sldSz` element | U |
| Theme | Theme colour slots are NBG colours and the major/minor fonts are Aptos or Aptos Display. | colors.md; tokens `colors`, `fonts` | W | theme colour slots and font slots | |
| Background | Every slide's effective background (slide, else layout, else master) is white. | Standard #2 | E | slides | U |
| Colors | Every colour in slide shapes and chart parts is in tokens.yaml, including theme (`schemeClr`) references and the outline or fill a shape takes from its `p:style`. A retired colour fails with its reason. | colors.md; tokens `colors`, `retired_colors` | E | colour references in slide shapes and chart parts | U |
| Fonts | Every typeface (text, symbol, bullet) in slides and charts is in `fonts.allowed`; `+mn`/`+mj` theme references are resolved; Aptos SemiBold is forbidden. | typography.md; tokens `fonts` | E | typeface references | U |
| Font Sizes | Text is at least 10pt; sources and footnotes at least 11pt; only the header pill may be 9pt. Table cells and chart text included. | Standard #11; tokens `accessibility`, `type.source` | E | sized text runs in shapes, table cells and chart parts | U |
| Contrast | Text meets WCAG AA against what is behind it: its own fill, else the topmost filled shape below it containing its centre, else the slide background. Muted grey `939793` (2.96:1 on white) is waived only for the page number (10pt or less at the page-number position) and chart axis labels, on white, as Standard #22 allows; the cover date is caption grey and gets no waiver. Bullet glyphs are not text runs. | Standard #22 | E | text runs with a resolvable colour and background | U |
| Boundaries | No element extends past a slide edge (0.05 in tolerance). | dimensions.md | E | positioned shapes, pictures, charts, tables, connectors, group children | U |
| Safe Zones | Content stays right of the 0.374 in gutter, left of the right boundary, above the 6.85 in footer line; sources and footnotes end by 6.5 in. | dimensions.md; tokens `geometry` | E | content elements (logo footprints and the page number excluded) | U |
| Content Spacing | The first body element starts at 1.3 in or lower (`geometry.body_top`) and at least 0.15 in below the title's measured bottom, with or without a pill. | Standard #11 | E | slides with a content title and body content | |
| Text Fit | Measured text fits its box (half a line of slack when unfilled); unwrapped text fits its filled shape (the pill); cover title and subtitle stay on one line; the measured text of two boxes does not overlap; a table whose rows grow to fit their text stays above the footer. | Standards #11, #13; dimensions.md | E | text frames and tables | U |
| Text Margins | Unfilled text boxes have zero margins on all four sides (0.02 in tolerance). Filled shapes pad on purpose and are exempt. | dimensions.md (Text Box Rules) | E | unfilled text boxes carrying text | |
| Logo | Every slide but the last carries the Greek wordmark at the small or large logo position, unstretched (within 3% of the image's own aspect) and at the brand size; the cover (slide 1) uses the large logo; the English fallback fails. | Standards #4, #10, #17 | E | slides other than the last | U |
| Back Cover | The last slide holds only the centred oval emblem: no text, no page number, no empty text box, no corner logo, no other picture. | Standard #19 | E | the last slide in presentation order | U |
| Thank You Check | No thank-you, closing or Q&A slide. Unambiguous phrases (thank you, thanks but not "thanks to", any questions, merci, and the Greek verb forms ευχαριστώ and ευχαριστούμε, never ευχάριστη, ευχαριστημένοι or ευχαρίστηση) count anywhere on a candidate; "Q&A" and "Ερωτήσεις" count only as the slide's title or largest text. Matching is accent- and case-folded. | Standard #19; layouts.md | E | the last two slides and slides of 12 words or fewer | |
| Decorative | No decorative presets (stars, hearts, moons, clouds, suns, lightning, irregular seals). An ellipse is decorative only when it carries no text, exceeds 0.5 in on a side and carries no icon; numbered badges, triangles, chevrons and arrows pass. | Standards #3, #19 | E | preset-geometry shapes | |
| Shadows | No shape or chart draws a shadow, including one inherited from a theme effect style through `p:style/a:effectRef` when `spPr` sets no effect list. | brand-system README; tokens `components.card.shadow` | E | shapes and charts | U |
| Em Dashes | No em dash (or " -- ") in slide or chart text. A spaced en dash is a warning; a range like 2024-2025 with an en dash is fine. | Standard #7 | E | text items in slides and charts | U |
| Title Style | Titles are Regular weight; a title's text starts on the 0.374 in gutter (box x plus left margin, 0.01 in tolerance) unless it sits beside a gutter-anchored element on the same row (a divider number, a unit pill); a closing period is a warning. | Standards #15, #16; brand-system README | E | slides with a title | U |
| Title Length | A content title fits one line: at most `type.title.max_chars` characters. | Standard #11; tokens `type.title` | E | slides with a content title | |
| Slide Titles | Every slide carrying text has a title, and no two titles are the same (accent- and case-folded). | presentation-qa | E | slides carrying text | U |
| Action Titles | A content title states a finding: not a topic label, at most 15 words. Warning because a noun-phrase title is sometimes a deliberate choice. | presentation-qa 2A | W | slides with a content title | |
| Chart Types | No `pieChart`, `pie3DChart` or `ofPieChart`; part-to-whole is a doughnut. | charts.md | E | chart parts | |
| Chart Data | Every chart has series and categories; more than `charts.max_series` (6) series warns, more than `charts.max_series_absolute` (8) fails. Pie-like charts count slices. | Standard #22; tokens `charts` | E | chart parts | |
| Chart Styling | Line and area series carry an explicit line colour (`c:spPr/a:ln`), area series an explicit fill; a series or point left automatic must resolve to an NBG theme accent; line markers are hollow circles, white fill with a series-colour ring (warning). | Standard #5; charts.md; tokens `charts.line` | E | chart series | |
| Zero Baseline | Bar and column value axes include zero: an explicit minimum above zero or maximum below it fails, and so does an automatic axis on close values (the lowest bar over five sixths of the highest, or the mirror for negative bars), which PowerPoint draws without zero. Set the minimum to 0. | keynote.md; charts.md | E | value axes of bar and column charts | |
| Exhibit Sources | Every slide with a chart or table carries a source line ("Source:", "Sources:", "Πηγή:", "Πηγές:", accent- and case-folded) with an as-of year or date. | `content.source` in deck.schema.json; presentation-qa | E | slides carrying a chart or table | |
| Alt Text | Pictures, charts, tables and groups carry descriptive alt text: not empty, not a file name or autoname, not "image of...", not a caption already on the slide. The three brand logo placements are decorative and exempt. | Standard #22 (EN 301 549) | E | top-level pictures, graphic frames and groups | |
| Bank Branding | A chart whose categories or series names include two or more of the banks in tokens `banks` colours each bank's point or series in its brand colour (`extended_palettes.peer_banks`), and the slide carries each plotted bank's own logo, unstretched. A picture is a bank's logo when it is that bank's `banks.<id>.logo` asset, or names the bank in its alt text or name and keeps the asset's aspect ratio; any other picture counts for no bank. Chart labels match `names` and `label_aliases`; running text matches `names` only, so "alpha release" is not a bank. | presentation-qa 2H; tokens `banks`, `extended_palettes.peer_banks` | E | charts plotting two or more banks | |
| Number Formats | One currency notation per deck (raw digits or abbreviated) and one decimal precision per unit. Greek separators (1.250.000, 2,3) and suffixes (χιλ., εκ., δισ.) are understood. | typography.md | W | currency amounts in slide text | |
| AI Slop | No slide clusters two or more AI-register phrases. Phrases, not words: "leverage ratio", "robust capital base" and "unlock the card" are banking language. | presentation-qa (tone) | W | slides carrying text | |
| Official Name | The bank is «Εθνική Τράπεζα», never «Εθνική Τράπεζα της Ελλάδος». | writing style | W | slides carrying text | |
| OOXML Order | Children of `a:pPr` (and list-style levels), `a:rPr`/`a:defRPr`/`a:endParaRPr`, `p:spPr`/`c:spPr` and `a:bodyPr` follow the DrawingML schema order; out of order, PowerPoint repairs the file or refuses it. | ISO/IEC 29500 DrawingML | E | property elements in slides and charts | U |

## How the rules decide what a thing is

**Title** (one definition, used by every title check): a title placeholder (`p:ph` type
`title` or `ctrTitle`, position and size resolved through its layout and master); otherwise
the largest text of 20pt or more whose top is above 1.2 in (content titles, the contents
header, the 22pt Key Figures title); otherwise the largest text of 40pt or more in the top
3.5 in (cover and divider titles). A bare section number such as "01" is never a title. A
title under 40pt is a content title; Title Length, Action Titles and Content Spacing apply
only to content titles, so a divider's noun-phrase title is left alone (Standard #3).

**Header chrome** (never "first body content"): the title, anything starting above the
title's bottom (a pill above it, a unit pill beside it), and one subtitle directly under it
(an unfilled text box at most 0.5 in tall, starting within 0.35 in of the title's bottom).

**Header pill** (the one 9pt exception): a filled rounded rectangle lying wholly above the
title, or a text box above the title laid over one.

**Sources and footnotes**: text starting "Source:", "Sources:", "Πηγή:", "Πηγές:", "Note",
"Σημείωση", "*" or a superscript digit, accent- and case-folded.

**Bullet glyphs**: the bullet character's colour (`a:buClr`, cyan `00ADBF` in the brand) is
checked by Colors against the palette. Contrast measures text runs only; a bullet glyph is a
marker, not text, so the cyan bullet is not reported as low-contrast text.

**Text measurement**: Text Fit wraps each paragraph with Aptos metrics. It uses Pillow with
the Aptos TTF when one is found in `~/Library/Fonts`, `/Library/Fonts`, the Office app
bundles' `Contents/Resources/DFonts`, the Office cloud-font caches (matched on the font's
own name, since those files are hashed), `C:\Windows\Fonts` or
`%LOCALAPPDATA%\Microsoft\Windows\Fonts`. Otherwise it uses a table of Aptos advance widths
for ASCII, Greek and common punctuation, which gives the same widths, so a laptop and a CI
runner without Aptos agree. `DECKS_FONT_DIRS` (path-separated) replaces the search list. The
check's message says which measurer ran.

**Package safety**: parts are read from the zip one at a time, never extracted, with limits
on member count, part size, total size and XML compression ratio, and XML is parsed with
defusedxml. A deck over a limit exits 2.

## Adding a check

1. Write `check_<name>(deck, out) -> str` in `nbg_validate.py`. Count every candidate you
   inspect with `out.count()`, report each problem with `out.add(slide_position, message)`
   (pass `"warning"` as a third argument for a warning-level finding), record what you
   could not judge with `out.skip(reason)`, and return a one-line summary for both outcomes.
   Read brand values from `brand()` or `nbg_tokens`, never as literals.
2. Declare it in `CHECKS` at the bottom of the file: name, function, severity, rule, source,
   candidates, and `universal=True` if it applies to every deck. `CHECKS` is the only
   registry; `--list-checks`, the JSON order and the text report all follow it.
3. In `test_nbg_validate.py`, add a FAIL fixture to `FAIL_CASES` that breaks exactly one rule
   in a copy of the golden deck. `test_every_registered_check_has_a_fail_fixture` fails
   until you do.
4. Make the golden deck pass it and examine at least one candidate, or, if the golden deck
   cannot exercise it, add a PASS fixture to `PASS_CASES`.
5. Add a row to the inventory above. `test_validator_md_documents_every_check` fails until
   you do.
6. If the rule changes what the builder must emit, tell whoever owns `nbg_build.py`, and
   cite the rule's Standard in `presentation-style-guide.md`.

## Python API

```python
import nbg_validate as nv

results = nv.validate_presentation("deck.pptx")            # all checks, registry order
results = nv.validate_presentation("deck.pptx", only=["Colors", "Fonts"])
for r in results:
    print(r.name, r.status, r.examined, [f.text() for f in r.findings])
code = nv.exit_code(results, strict=False)                  # 0 or 1; exit 2 is main()'s
```

`load_deck(path)` (a context manager) and `find_title(slide)` expose the deck model the
checks share.
