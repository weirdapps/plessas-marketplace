# decks architecture

How the presentation system is put together, and the contracts between its parts.
Read this before changing an agent, a command or a tool: every part below relies on
the others honouring these contracts.

## One path from brief to deck

```text
brief
  -> storyline-architect   writes deck.yaml (the deck spec, deck.schema.json)
  -> decks-py check        schema + semantic check of the spec, no build
  -> storyboard-designer   refines deck.yaml: slide types, layouts, visuals
  -> [icon-designer, infographic-specialist, device-mockup]   produce image assets
                           referenced from deck.yaml (optional, in parallel)
  -> decks-py build        nbg_build.py renders deck.yaml to .pptx and runs the
                           validator; exit 1 = brand violations
  -> decks-py render       LibreOffice -> PDF -> one PNG per slide, font check
  -> presentation-qa       reads the validator JSON AND every slide PNG; returns a
                           verdict plus a fix list addressed to deck.yaml slide ids
  -> the main loop edits deck.yaml and rebuilds (at most 2 fix cycles)
  -> decks-py record       writes the draft record /presentation-review learns from
```

There is exactly one renderer for light-mode decks: `nbg_build.py`. No agent writes
PptxGenJS, python-pptx or OOXML by hand. A layout the named slide types cannot express
uses the `custom` slide type (positioned elements), which the builder still renders
with brand tokens and the validator still checks.

`/create-keynote` is the one exception to the light-mode rules (Standard #21): it
renders with `nbg_keynote.py`, a Pillow compositor, through `decks-py keynote`.

The main conversation orchestrates. Commands dispatch the specialist agents one level
deep; no agent dispatches another agent (subagents cannot spawn subagents when
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`, and nesting is never required).

## The launcher: `bin/decks-py`

Every prompt calls every Python tool through one launcher, always as
`bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command> ...` (the `bash` prefix works
whether or not the install kept the executable bit).

| Command | Tool | Exit codes |
|---|---|---|
| `build <spec.yaml> <out.pptx>` | nbg_build.py | 0 built and valid; 1 spec or brand violations; 2 could not run |
| `check <spec.yaml>` | nbg_build.py --check | 0 valid; 1 violations (each with slide id and path) |
| `validate <deck.pptx> [--format json]` | nbg_validate.py | 0 clean; 1 a check failed; 2 could not run |
| `render <deck.pptx> <outdir>` | nbg_render.py | 0 rendered with Aptos; 4 rendered but fonts substituted (fit judgements unreliable); 3 LibreOffice missing; 2 error |
| `extract <file>` | nbg_extract.py | 0 markdown on stdout; 2 error |
| `record <deck.pptx> <spec.yaml> --data <dir>` | nbg_record.py | 0 record written; 2 error |
| `keynote ...` | nbg-keynote/nbg_keynote.py | its own |
| `mockup ...` | device-mockup/iphone_mockup.py | its own |
| `setup` / `doctor` | the launcher | 0 ok; 2 environment problem |

Environments are caches, kept outside the plugin in
`${DECKS_VENV_HOME:-~/.cache/nbg-decks}/<tool>-<requirements hash>`, built on first use
with uv when present, else Python 3.12+ `venv` and pip. Exit 2 always prints the fix.

## The deck spec

`tools/nbg-presentation/deck.schema.json` (JSON Schema 2020-12) is the single contract
between the agents and the builder. Slide types: `cover`, `contents`, `divider`,
`content`, `chart`, `waterfall`, `table`, `kpi`, `cards`, `process`, `two_column`,
`image`, `custom`, `back_cover`. Every exhibit (chart, waterfall, table, kpi, and any
column or element holding one) carries `content.source: {name, as_of, basis?}`.
Every slide may carry `id`, `key_message`, `so_what` and `notes` (speaker notes).
`presentation.language` (`en` | `el`) drives boilerplate, number formats and
accent-free Greek capitals. The builder accepts legacy aliases with a warning and
normalises them before the schema applies.

## Brand tokens

`shared/brand-system/tokens.yaml` is the machine-readable brand: colours, type scale,
geometry, components, chart styling, keynote dark tokens. `tools/nbg_tokens.py` loads
it. The builder renders with it, the validator checks against it, the keynote reads
its dark tokens, and tests assert the brand-system prose quotes it. A brand value
changes in tokens.yaml first. The numbered Standards in
`shared/presentation-style-guide.md` decide conflicts; tokens.yaml encodes the outcome.

## Where state lives

| What | Where |
|---|---|
| Shipped brand, standards, agents, tools | the plugin directory (`${CLAUDE_PLUGIN_ROOT}`), read-only, replaced at every version bump |
| Tool environments | `~/.cache/nbg-decks/` |
| Per-user learned preferences | `${CLAUDE_PLUGIN_DATA}/style-preferences.md`, an overlay on the shipped Standards; never written into the plugin |
| Draft and reviewed deck records | `${CLAUDE_PLUGIN_DATA}/presentations/{pending,reviewed}/` |
| Working files for a build (deck.yaml, renders, QA output) | `${CLAUDE_PLUGIN_DATA}/work/<deck id>/` |
| The finished deck | the folder the user names; default `~/Downloads/`, named `YYYYMMDDHHMM_<slug>.pptx` |

Personal context (a unit list for cover subtitles, a preferred sign-off, recurring
audiences) belongs in the user's `style-preferences.md`, never in a shipped prompt or
brand file. The plugin is public and serves every colleague.

## Paths inside prompts

Plugin files are referenced as `${CLAUDE_PLUGIN_ROOT}/...` (Claude Code substitutes it
in agent, command and skill bodies). Bare `shared/...`, `assets/...` or `tools/...`
paths resolve against whatever directory the session happens to be in, so they are
forbidden; `scripts/validate_consistency.py` rejects them.

## Quality gates

1. `decks-py check`: the spec is complete (titles, sources, data) before anything renders.
2. `decks-py build`: the builder refuses what it cannot render faithfully and runs the
   validator; exit code is the brand gate.
3. `decks-py render` + presentation-qa: a human-level look at every slide image, with
   a font-substitution guard so fit judgements are not made on a fallback font.
4. CI: tests for every builder slide type, a FAIL and a PASS fixture for every validator
   check, OOXML schema validation of built decks, and the examples built and validated.
