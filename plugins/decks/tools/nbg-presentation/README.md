# NBG presentation tools

`nbg_build.py` turns a deck spec (YAML) into an NBG-branded `.pptx` and checks it;
`nbg_validate.py` checks any `.pptx` against the brand; `nbg_render.py` draws the
slides as PNGs; `nbg_extract.py` reads a deck back as markdown; `nbg_record.py`
writes the draft record `/presentation-review` learns from. Every brand value comes
from `shared/brand-system/tokens.yaml`; the spec contract is
[`deck.schema.json`](deck.schema.json) (JSON Schema 2020-12).

## Running the tools

Always through the launcher, which builds and caches its own Python environment on
first use (in `~/.cache/nbg-decks/`, keyed by `requirements.txt`) and needs Python
3.12+ or [uv](https://docs.astral.sh/uv/):

```bash
# inside Claude Code (agents and commands)
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" check deck.yaml

# by hand, from the repository root
bash plugins/decks/bin/decks-py check plugins/decks/examples/strategy-deck.yaml
bash plugins/decks/bin/decks-py build plugins/decks/examples/strategy-deck.yaml ~/Downloads/strategy-deck.pptx
bash plugins/decks/bin/decks-py render ~/Downloads/strategy-deck.pptx ~/Downloads/strategy-deck-render
bash plugins/decks/bin/decks-py extract ~/Downloads/strategy-deck.pptx
bash plugins/decks/bin/decks-py doctor
```

| Command | What it does | Exit codes |
|---|---|---|
| `check <spec.yaml> [--format json]` | Normalises legacy names, validates the schema and the semantics, lays every slide out in a dry run. Writes nothing. | 0 valid (warnings allowed); 1 errors; 2 could not run |
| `build <spec.yaml> <out.pptx>` | Runs `check`, renders, saves, then runs `nbg_validate.py`. Nothing is written when `check` fails. | 0 built and valid; 1 spec errors or brand violations; 2 could not run |
| `validate <deck.pptx>` | Brand compliance of any deck: see [VALIDATOR.md](VALIDATOR.md). | 0 clean; 1 a check failed; 2 could not run |
| `render <deck.pptx> <outdir> [--dpi N]` | LibreOffice to PDF, one PNG per slide, and a font check. | 0 rendered with Aptos; 4 fonts substituted; 3 LibreOffice missing; 2 error |
| `extract <file.pptx or .pdf>` | Titles, text, bullets, tables, chart data, alt text and notes as markdown on stdout. | 0; 2 error |
| `record <deck.pptx> <spec.yaml> --data <dir> [--topic T]` | Writes the draft record for `/presentation-review`. | 0; 2 error |

### check output

Each issue names the slide (1-based position, id and type), the path in the spec and
the fix. Text mode prints one line per issue:

```text
ERROR slide 4 (S04, chart) slides[3].chart.data.series[0].values: 3 value(s) for 4 categories. Fix: give one value per category (null for a gap).
```

`--format json` prints one object:

```json
{"spec": "/abs/deck.yaml", "ok": false,
 "errors": [{"slide": 4, "id": "S04", "type": "chart", "path": "slides[3].chart.data.series[0].values",
             "message": "3 value(s) for 4 categories", "fix": "give one value per category (null for a gap)"}],
 "warnings": []}
```

Errors stop a build: a schema violation, a missing source on an exhibit, series that
do not match their categories, a missing image, a custom element outside the body
area, an unknown colour name, a deck that does not end on its back cover, duplicate
titles, and anything that cannot fit (bullets that need more room than the body has
at 14pt, a table taller than the body, a cover title or subtitle that does not stay on
one line, Standard #13). Warnings do not: a legacy name, an unquoted number or date, a
slide title that wraps to two lines, more than six chart series, a waterfall total that
does not add up, an em dash.

## The deck spec

The whole contract is [`deck.schema.json`](deck.schema.json). A spec is a mapping
with a `slides:` list and optional `presentation:` metadata (`title`, `author`,
`purpose`, `audience`, `language: en | el`, ...). Every slide takes `type` and may
take `id` (so QA findings can name it), `key_message`, `so_what` and `notes` (speaker
notes). Titled slides put their text under `content`: `title` (an action title, one
line), `bumper` (the section pill, shown in capitals), `description` (a 12pt caption),
`takeaway` (the pale-teal strip) and `source`.

`content.source` is required on every exhibit (chart, waterfall, table, kpi, and any
two-column or custom slide that holds one): `{name, as_of, basis?}`. It renders as
"Source: name, as of as_of; basis" on one 11pt line ending at 6.5", or
"Πηγή: name, στοιχεία as_of" in a Greek deck.

| Type | Required | Optional | Draws |
|---|---|---|---|
| `cover` | `content.title` | `subtitle`, `location`, `date` | Title on one line at 48pt (down to 44pt), subtitle 24pt below it, large logo |
| `contents` | `content.sections[]` (`title`) | `content.title`, section `number`, `description` | Standard #18 list; unnumbered page when the deck is under 10 slides |
| `divider` | `content.number`, `content.title` | | Number and title on one baseline, large logo |
| `content` | `content.title`, `content.points[]` | `bumper`, `description`, `takeaway`, `source`; a point may be `{text, level: 2}` | Bullets at 16pt, down to 14pt to fit |
| `chart` | `content.title`, `content.source`, `chart.type`, `chart.data` | `number_format`, `unit`, `highlight_category`, `show_legend`, `alt_text` | One native chart |
| `waterfall` | `content.title`, `content.source`, `chart.data.items[]` (`label`, `value`) | item `total`; first and last items are totals | A bridge; step labels above the bars |
| `table` | `content.title`, `content.source`, `table.headers`, `table.rows` | `highlight_column`, `column_align` | Header in dark teal, zebra rows, figures right-aligned |
| `kpi` | `content.title`, `content.source`, `kpis[]` (`value`, `label`) | `delta`, `sentiment: positive or negative or neutral` | 1 to 4 tiles |
| `cards` | `content.title`, `cards[]` (`title`) | `layout: row or grid`, card `body`, `icon`, `number`, `highlight`, `recommended` | 2 to 6 cards; the recommended one gets a gold border and tab |
| `process` | `content.title`, `steps[]` (`title`) | step `body`, `icon` | 2 to 6 steps with arrows |
| `two_column` | `content.title`, `left`, `right` | `split: 50/50, 40/60 or 60/40`, column `heading` | Each column is `bullets`, `text`, `chart`, `table`, `image` or `kpis` |
| `image` | `content.title`, `image.path`, `image.alt_text` | `fit: contain or cover`, `caption` | One picture |
| `custom` | `content.title`, `elements[]` (`kind`, `x`, `y`, `w`, `h`) | per element: `text`, `points`, `shape`, `fill`, `border`, `text_color`, `role`, `size`, `path`, `chart`, `table` | Positioned elements inside the body area (x 0.374 to 12.959, y 1.3 to 6.5) |
| `back_cover` | | | The centred oval emblem only |

Chart types: `bar`, `bar_stacked`, `bar_horizontal`, `line`, `area_line` (the default
for a time series, Standard #2.8) and `doughnut` (there is no pie). Element kinds:
`text`, `bullets`, `shape` (`rect`, `rounded_rect`, `oval`, `chevron`, `arrow_right`),
`image`, `chart`, `table`, `line`. Colours are token names from `tokens.yaml`
(`teal`, `dark_teal`, `off_white`, ...), never hex.

Images are PNG, JPEG or SVG (SVG is rasterised with resvg). A relative path resolves
against the spec's folder first, then the plugin's `assets/` folder, so
`illustrations/Growth.png` works from anywhere.

Legacy names (`thankyou`, `toc`, `bar_chart`, `pie_chart`, `charts/pie_single`,
`covers/*`, `infographic`, `hyper_title`, `paragraphs`, `items`, `waterfall_items`,
`recommended_visual`, `template`) still build, each with a warning naming its
replacement. The full list is [`assets/slide-catalog.yaml`](../../assets/slide-catalog.yaml).

A minimal spec that checks and builds as written (the tests build it):

<!-- readme-example -->
```yaml
presentation:
  title: "Card payments review"
slides:
  - type: cover
    content:
      title: "Card payments review"
      subtitle: "Payments | Q2 2026"
      date: "July 2026"
  - type: chart
    id: S02
    content:
      title: "Contactless now carries most in-store card payments"
      source:
        name: "Card management information"
        as_of: "30 June 2026"
    chart:
      type: bar
      data:
        categories: ["Q3 25", "Q4 25", "Q1 26", "Q2 26"]
        series:
          - name: "Contactless share, %"
            values: [78, 81, 84, 86]
  - type: back_cover
```

The four specs in [`examples/`](../../examples) exercise every slide type, a waterfall
and a Greek deck.

## Greek decks

`presentation.language: el` gives Greek boilerplate ("Περιεχόμενα", "Πηγή"), capitals
without the tonos in the pill ("Ευρήματα" becomes "ΕΥΡΗΜΑΤΑ"), and `el-GR`
on every run so PowerPoint proofs the text as Greek. Specs are always read as UTF-8.

## render

```bash
bash plugins/decks/bin/decks-py render deck.pptx outdir --dpi 110
```

Writes `outdir/<deck>.pdf` and `outdir/slide-01.png`, `slide-02.png`, ... LibreOffice
runs headless in a throwaway profile; it is found on `PATH`, at
`/Applications/LibreOffice.app/Contents/MacOS/soffice`, under `Program Files` on
Windows or `/usr/lib/libreoffice/program`, or at `DECKS_SOFFICE`. stdout:

```json
{"pdf": "/abs/outdir/deck.pdf", "pngs": ["/abs/outdir/slide-01.png"], "slides": 1,
 "deck_slides": 1, "dpi": 110, "fonts": [{"name": "Aptos", "embedded": true}],
 "font_fallback": false, "soffice": "/opt/homebrew/bin/soffice"}
```

Exit 4 (`font_fallback: true`) means Aptos was not embedded: LibreOffice drew the
slides in a substitute font, so text widths differ from PowerPoint and fit judgements
made from the PNGs are unreliable. On 2 and 3, stdout is `{"error", "fix"}`.

## extract

```bash
bash plugins/decks/bin/decks-py extract deck.pptx > deck.md
```

For a `.pptx`: `## Slide N: <title>`, then the text in reading order with bullets as
`- ` (indented by level), tables as markdown tables, charts as `Chart (<type>):` and a
categories-by-series table (a waterfall as its steps and signed values), pictures as
`[image: <alt text>]`, and `Notes: ...`. For a `.pdf`: `## Page N` and the page text.
A `.docx` is refused (python-docx is not a dependency): save it as PDF first.

## record

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" record deck.pptx deck.yaml --data "${CLAUDE_PLUGIN_DATA}"
```

Writes `<data>/presentations/pending/<YYYYMMDDHHMM>_<slug>.yaml` and prints
`{"record": <path>, "id": <id>, "slides": <n>}`. The record:

| Key | Value |
|---|---|
| `id` | `<YYYYMMDDHHMM>_<slug>`, the file's stem |
| `created` | ISO 8601 with the local UTC offset |
| `status` | `pending`; a review moves the record to `presentations/reviewed/` |
| `topic` | `--topic`, else `presentation.title`, else the cover title |
| `file_path` | the `.pptx`, absolute |
| `file_hash` | `sha256:<hex>` of the `.pptx` as built |
| `spec_path` | the deck spec, absolute |
| `slides` | `[{index, id, type, title}]`, index 1-based |
| `spec` | the whole spec after legacy-name normalisation |

## Updating an existing deck

`inject_chart_data.py` and `inject_table_data.py` replace the data in charts and
tables of a deck that was not built from a spec. They are not behind the launcher; run
them with its requirements, for example with uv:

```bash
uv run --no-project --with-requirements plugins/decks/tools/nbg-presentation/requirements.txt \
    python plugins/decks/tools/nbg-presentation/inject_chart_data.py in.pptx charts.json out.pptx
```

`slide` counts from 0 in presentation order, `chart_index` and `table_index` from 0
in the slide's shape order; the config formats are in each script's docstring. A
chart's embedded workbook is rewritten with it, series are added or removed to match,
table data must match the table's shape, and nothing is written unless every entry
matched (exit 1 names the ones that did not).

## Tests

```bash
uv run --no-project --python 3.12 \
    --with-requirements plugins/decks/tools/nbg-presentation/requirements.txt \
    --with pytest python -m pytest plugins/decks/tools/nbg-presentation scripts/test_ooxml_schema.py -q
```

`scripts/test_ooxml_schema.py` validates every slide and chart part of every built
example against the ISO/IEC 29500 schemas in `scripts/ooxml-xsd/`: PowerPoint drops
schema-invalid XML that LibreOffice and python-pptx both accept.
