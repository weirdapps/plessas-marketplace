# decks: Quickstart

A 5-minute path from zero to "my Cards Q1 deck for ExCo is on screen, on brand, on message."

## What it does

Turns a brief, a PDF or an existing deck, an email thread, or a few rough bullets into a board-ready PowerPoint that already obeys NBG brand standards: Aptos throughout, NBG Teal `#007B85` and Dark Teal `#003841`, white background, no pie charts (doughnut only), no "Thank You" slide, one key message per slide. Behind the scenes an agent pipeline writes the storyline, a tested builder renders it, a brand validator checks it, and a QA agent looks at every slide, applying McKinsey-quality discipline (action titles, MECE structure, Pyramid Principle, the 5-7 second test on every slide). You get the polished file, not a half-finished outline.

It is not a clip-art generator. It assumes the deck will be read by people who matter and judges itself accordingly.

## Prerequisites

- Claude Code installed
- Python 3.12 or newer, or [uv](https://docs.astral.sh/uv/). The deck tools build their own environments on first use; you install nothing else by hand
- Aptos installed (Office for Mac and Windows already ship it)
- Optional: LibreOffice, so QA can render and look at every slide before it passes the deck
- For redesigning an existing deck: the source `.pptx` accessible on disk

The full table, with how to check each one, is in [README.md → Requirements](README.md#requirements).

## Install

Inside Claude Code:

```text
/plugin marketplace add weirdapps/plessas-marketplace
/plugin install decks@plessas-marketplace
```

That's it. No configuration files to edit. The first deck takes about a minute longer while the
tools build their environments; to do that now and check the machine, run from a terminal:

```bash
bash ~/.claude/plugins/marketplaces/plessas-marketplace/plugins/decks/bin/decks-py doctor
```

## Authenticate

`decks` needs no authentication; it works fully offline.

The `manage-nano-banana` image generator is **optional**. It is only present if you have also installed the `plessas-lab` marketplace. Without it, infographics are drawn as brand-compliant charts and diagrams; either way, you get a finished deck.

## Your first command

```text
/create-presentation Cards Q1 results for ExCo: revenue +12%, fee mix shifting to credit, NPL stable, recommend doubling down on premium card acquisition
```

It stops once before it builds anything, at the outline (Standard #14): one line per slide with
its id, type and action title, and every open question, such as the source of a figure you gave.
Agree, or say what to change. Output (typical):

```text
read-through:
  S01 cover     Cards Q1 2026: premium acquisition is the unlock
  S02 content   Three messages, three numbers
  S03 divider   Where we landed in Q1
  S04 chart     Revenue +12% vs plan, driven by credit fees
  ...
open questions:
  S04: which report, and as of which date, gives the +12% revenue figure?
```

Once the deck has passed QA, the reply is one line:

```text
~/Downloads/202605101422_cards_q1_results_exco.pptx: 14 slides, QA PASS
```

A deck that still fails QA after two fix cycles is not copied to your folder; the reply says what
is wrong.

If the result is 90% there but you want a tighter cover or a different chart on slide 5, edit the file in PowerPoint and run `/presentation-review` (see Common patterns below): the system learns your preferences.

## Top commands

| Command | What it does | When to use |
|---|---|---|
| `/create-presentation` | New branded deck from a brief, content, or rough notes | ExCo packs, quarterly reviews, Board updates, sector reviews |
| `/redesign-deck` | Take an existing PPTX and rebuild it to NBG standards | Slides inherited from a partner, a consultancy, or another unit |
| `/polish-slides` | Fast formatting pass: fonts, colours, alignment, spacing | A deck you wrote yourself that just needs to look the part |
| `/review-deck` | Check any deck before it ships; changes nothing | The night before the board |

The rest (`/presentation-review`, `/create-keynote`, `/create-icon`, `/create-infographic`,
`/create-mockup`) are in the [which-command-when table](README.md#which-command-when).

## Common patterns

**Build an ExCo pack from scratch** (10-15 min):

```text
/create-presentation <one-paragraph brief or paste content here>
# … review the generated PPTX in ~/Downloads …
# … edit anything that's off …
/presentation-review ~/Downloads/202605101422_cards_q1_results_exco.pptx
# … your edits become learned preferences for next time …
```

**Rescue a partner deck before a board meeting**:

```text
/redesign-deck ~/Downloads/partner_proposal.pptx
# Every figure, source and speaker note kept; storyline and layout rebuilt to NBG standards
```

**Quick polish on something you wrote yourself**:

```text
/polish-slides ~/Downloads/sector_offsite_draft.pptx
# Fonts → Aptos, colours → NBG palette, spacing → grid, no structural changes
```

**Check a deck before it goes out**:

```text
/review-deck ~/Downloads/202605101422_cards_q1_results_exco.pptx
# A verdict and a fix list per slide; the file is not touched
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `decks-py: no Python 3.12+ found` | Install Python 3.12 or newer, or uv, then retry. The message names both |
| `decks-py: could not install ...` | The first run downloads the tools' packages; check network access or the proxy, then retry |
| QA says it could not render the slides | LibreOffice is not installed. Install it, or accept a QA based on the validator report alone (it says so) |
| "fonts substituted" from a render (exit 4) | LibreOffice cannot see Aptos, so text-fit judgements are off. Install Aptos where LibreOffice looks and render again |
| Infographics look like plain charts, not illustrations | `manage-nano-banana` not installed. Install the `plessas-lab` marketplace, or keep the charts; both are brand-compliant |
| No deck appeared in `~/Downloads` | It failed QA after two fix cycles, so it was not copied; the reply says what is wrong. Fix the brief, or ask to ship it anyway |
| Output landed in an unexpected folder | The finished deck goes to the folder you named, else `~/Downloads/`; working files stay under `~/.claude/plugins/data/decks-plessas-marketplace/work/`. Name the folder in your request |
| Charts came out as pie charts | Re-run: pie charts are blocked by the builder and at QA. If one slipped through, file an issue |
| "Thank You" slide appeared | Same as above, blocked at QA. Re-run |
| Generated deck has too many slides for a 10-min slot | Add a length hint: `/create-presentation … keep it to 8 slides for a 10-min ExCo slot` |
| The system keeps using a layout you don't like | After editing the file, always run `/presentation-review`; that's how preferences are learned |

## Where things live

- **Generated decks**: `~/Downloads/YYYYMMDDHHMM_<descriptive_name>.pptx` unless you name another folder (never inside a repo)
- **Working files of a build** (deck spec, slide renders, QA output): `~/.claude/plugins/data/decks-plessas-marketplace/work/`
- **Drafts the system is watching for your edits**: `~/.claude/plugins/data/decks-plessas-marketplace/presentations/pending/`
- **Your learned style preferences**: `~/.claude/plugins/data/decks-plessas-marketplace/style-preferences.md`, written by `/presentation-review`; it survives plugin updates and never reaches the repo
- **NBG brand specs** (colours, fonts, layouts): `shared/brand-system/`, with every value in `shared/brand-system/tokens.yaml`
- **The Standards** every deck follows: `shared/presentation-style-guide.md`

## Want more?

- The pipeline, the launcher and the deck spec: [ARCHITECTURE.md](ARCHITECTURE.md)
- Every command, and which one to use when: [README.md](README.md)
- Sample deck specs (YAML): `examples/`
- For Excel-driven decks (monthly packs, variance reviews): `/excel-to-deck` from the `excel` plugin turns a workbook into a deck spec and, with `decks` installed, runs `/create-presentation` on it for you
