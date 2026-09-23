# decks

NBG-branded presentations from Claude Code. A brief, a document or a few rough bullets become a
board-ready PowerPoint: a storyline agent writes a deck spec, one tested renderer builds it, a
brand validator checks it, and a QA agent looks at every rendered slide before the deck ships.
It also builds dark full-bleed keynotes for stage talks, and icons, infographics and iPhone
mockups for slides.

New here? [QUICKSTART.md](QUICKSTART.md) gets you to a first deck in five minutes.

## Requirements

| Need | Why | Check |
|---|---|---|
| Claude Code with this marketplace added | The commands and agents | `/plugin` lists `decks` |
| Python 3.12 or newer, **or** [uv](https://docs.astral.sh/uv/) | The build, validate, render, keynote and mockup tools. The launcher builds their environments itself on first use | `decks-py doctor` |
| Aptos (Light, Regular, SemiBold, Bold, ExtraBold) | The brand font. Office for Mac and Windows already ship it; renders and keynotes fall back to Calibri or DejaVu without it | `decks-py doctor` |
| LibreOffice (optional) | Render-and-look QA: every slide rendered to an image before QA judges it. Without it QA works from the validator report and says so | `decks-py doctor` |

If you use LibreOffice, it must see Aptos too. `decks-py render` reports when it substituted a
font (exit 4); install Aptos where LibreOffice looks and render again.

## Install

Inside Claude Code:

```text
/plugin marketplace add weirdapps/plessas-marketplace
/plugin install decks@plessas-marketplace
```

That is enough: the first command that needs a Python tool builds its environment (about a
minute, once). To build them up front and check the machine, from a terminal:

```bash
bash ~/.claude/plugins/marketplaces/plessas-marketplace/plugins/decks/bin/decks-py setup
bash ~/.claude/plugins/marketplaces/plessas-marketplace/plugins/decks/bin/decks-py doctor
```

`installers/install.sh` (and `install.ps1`) run the same `setup` for you.

## Which command when

| You want | Command |
|---|---|
| A new deck from a brief, notes, a document or an email thread | `/create-presentation` |
| An existing deck rebuilt to NBG standards: content kept, layout redone | `/redesign-deck <file.pptx>` |
| A deck that is nearly right, tightened without restructuring | `/polish-slides <file.pptx>` |
| A deck checked before it ships: brand validator, a look at every slide, a fix list; it changes nothing | `/review-deck <file.pptx>` |
| The system to learn from the edits you made to a deck it generated | `/presentation-review <final.pptx>` |
| A talk from a stage to an external or bank-wide audience: dark, full-bleed, photographs (Standard #21 and its four entry criteria) | `/create-keynote` |
| A new icon in the NBG duotone style | `/create-icon` |
| A chart or diagram as an image for a slide | `/create-infographic` |
| A screenshot placed inside an iPhone frame | `/create-mockup <screenshot>` |

Each command also answers to `/decks:<name>`. You do not have to remember them: ask in plain
words ("I need something for the board on Thursday", «θέλω κάτι για το ΔΣ») and the
`presentations` skill picks the command.

## How it works

```text
brief
  -> storyline-architect   writes deck.yaml (the deck spec)
  -> decks-py check        schema and semantic check, before anything renders
  -> storyboard-designer   picks slide types, layouts and visuals
  -> icon-designer, infographic-specialist, device-mockup   make any images (optional)
  -> decks-py build        nbg_build.py renders the .pptx and runs the brand validator
  -> decks-py render       LibreOffice renders every slide to an image, with a font check
  -> presentation-qa       reads the validator report and every slide image; PASS or a fix list
  -> fixes to deck.yaml and a rebuild (at most two cycles)
  -> decks-py record       keeps the draft /presentation-review later learns from
```

A deck that still fails QA after the two fix cycles is not copied to your folder: you are told
what is wrong and can ask to ship it anyway.

There is one renderer for light-mode decks, `nbg_build.py`; no agent writes PowerPoint by hand.
The main conversation runs the pipeline and dispatches each agent directly. `/create-keynote` is
the one exception, rendered by `tools/nbg-keynote/nbg_keynote.py`. The contracts between the
stages (the launcher, the deck spec, the brand tokens) are in [ARCHITECTURE.md](ARCHITECTURE.md).

## The launcher

Every Python tool runs through `bin/decks-py`, which keeps one environment per tool in
`~/.cache/nbg-decks/` and rebuilds it when that tool's requirements change.

| Command | Does |
|---|---|
| `decks-py build <deck.yaml> <out.pptx>` | Build a deck from a deck spec, then validate it |
| `decks-py check <deck.yaml>` | Validate a deck spec, build nothing |
| `decks-py validate <deck.pptx>` | Brand check of any .pptx |
| `decks-py render <deck.pptx> <outdir>` | Render to PDF and one PNG per slide |
| `decks-py extract <file>` | Text, notes, tables and chart data of a .pptx, .docx or .pdf, as markdown |
| `decks-py keynote <talk.yaml>` | Build a keynote |
| `decks-py mockup <screenshot>` | Build an iPhone mockup |
| `decks-py setup` / `decks-py doctor` | Build every environment now / report what the machine has |

`decks-py --help` lists the arguments; ARCHITECTURE.md lists the exit codes.

## Where things live

| What | Where |
|---|---|
| The finished deck | The folder you name; by default `~/Downloads/YYYYMMDDHHMM_<slug>.pptx` |
| Working files of a build (deck.yaml, renders, QA output) | `${CLAUDE_PLUGIN_DATA}/work/<deck id>/` |
| Your learned style preferences | `${CLAUDE_PLUGIN_DATA}/style-preferences.md`, an overlay on the shipped Standards |
| Drafts waiting for your edits, and reviewed ones | `${CLAUDE_PLUGIN_DATA}/presentations/pending/` and `reviewed/` |
| Tool environments | `~/.cache/nbg-decks/` |
| Brand, Standards, agents, tools | The plugin itself, read-only, replaced at every update |

`${CLAUDE_PLUGIN_DATA}` is `~/.claude/plugins/data/decks-plessas-marketplace/`. It survives plugin
updates and is yours alone: nothing in it is ever committed to this repository.

## Brand

- [shared/presentation-style-guide.md](shared/presentation-style-guide.md): the numbered NBG
  Standards. They decide every conflict.
- [shared/brand-system/README.md](shared/brand-system/README.md): the quick reference, and the
  detailed specs for colours, type, layouts, charts, icons and assets.
- [shared/brand-system/tokens.yaml](shared/brand-system/tokens.yaml): every brand value in
  machine-readable form. The builder, the validator and the keynote compositor read it.
- [shared/brand-system/keynote.md](shared/brand-system/keynote.md): keynote mode, the one
  sanctioned exception.

## Directory Structure

```text
decks/
├── .claude-plugin/plugin.json
├── ARCHITECTURE.md          # the pipeline and its contracts
├── agents/                  # every agent; the only directory the plugin loader scans for them
├── commands/                # slash commands
├── bundled/creative/        # icon, infographic and mockup commands, the mockup tool and device frames
├── skills/presentations/    # routes plain-language requests to a command
├── bin/decks-py             # the tool launcher
├── shared/                  # Standards and brand system (tokens.yaml, colours, type, layouts, ...)
├── assets/                  # logos, icons, illustrations, screenshots (each folder has an INDEX.md)
├── examples/                # sample deck specs
├── tools/nbg-presentation/  # builder, validator and the other light-mode tools
└── tools/nbg-keynote/       # keynote compositor
```

## License

MIT
