# decks — Quickstart

A 5-minute path from zero to "my Cards Q1 deck for ExCo is on screen, on brand, on message."

## What it does

Turns a brief, a Word doc, an email thread, or a few rough bullets into a board-ready PowerPoint that already obeys NBG brand standards: Aptos throughout, NBG Teal `#007B85` and Dark Teal `#003841`, white background, no pie charts (doughnut only), no "Thank You" slide, one key message per slide. Behind the scenes a four-stage agent pipeline — storyline-architect → storyboard-designer → graphics-renderer → presentation-qa — applies McKinsey-quality discipline (action titles, MECE structure, Pyramid Principle, the 5-7 second test on every slide). You get the polished file, not a half-finished outline.

It is not a clip-art generator. It assumes the deck will be read by people who matter and judges itself accordingly.

## Prerequisites

- Claude Code installed
- The `plessas-marketplace` set up (one-time, via `installers/install.sh`)
- For redesigning an existing deck: the source `.pptx` accessible on disk
- Optional: PowerPoint installed locally if you want to open and review the output (any modern PPTX viewer works)

## Install

Inside Claude Code:

```
/plugin install decks@plessas-marketplace
```

That's it. No further configuration files to edit.

## Authenticate

`decks` needs no authentication — it works fully offline.

The `manage-nano-banana` image generator is **optional**. It is only present if you have also installed the `plessas-lab` marketplace. When available, infographics use AI-generated illustrations; when absent, the system gracefully falls back to clean, brand-compliant SVG infographics. Either way, you get a finished deck.

## Your first command

```
/create-presentation Cards Q1 results for ExCo — revenue +12%, fee mix shifting to credit, NPL stable, recommend doubling down on premium card acquisition
```

Output (typical):

```
═══════════════════════════════════════════════
PRESENTATION GENERATED — 2026-05-10, 14:22
═══════════════════════════════════════════════

File: ~/Downloads/202605101422_cards_q1_results_exco.pptx
Slides: 14   Duration target: 12 min   QA: 17/17 passed

STORYLINE (Pyramid: Situation → Complication → Resolution)
───────────────────────────────────────────────
 1. Cover                            Cards Q1 2026 — Premium acquisition is the unlock
 2. Executive summary                Three messages, three numbers
 3. Section divider                  Where we landed in Q1
 4. Revenue performance              Revenue +12% vs plan, driven by credit fees
 5. Fee mix                          Credit share up 6 pts; debit flat
 6. Portfolio quality                NPL ratio stable at 2.1%, well below peer
 7. Section divider                  What's changing under the surface
 8. Customer mix shift               Premium segment +18% YoY, mass-market flat
 9. Competitive context              Revolut card spend up 24%; we are holding share
10. Section divider                  Recommendation
11. The ask                          Double premium card acquisition spend in H2
12. Investment & payback             €4.2M incremental, 14-month payback
13. Risks & mitigations              Three risks, three owners, three dates
14. Back cover                       NBG logo, no "Thank You"

INSIGHTS
───────────────────────────────────────────────
- Slide 11 is your single decision slide — built for the 5-7 second test
- Charts use NBG Teal + Cyan only (no pie charts, per brand)
- Action titles throughout (every title makes a claim, not a topic)
═══════════════════════════════════════════════
```

If the result is 90% there but you want a tighter cover or a different chart on slide 5, edit the file in PowerPoint and run `/presentation-review` (see Common patterns below) — the system learns your preferences.

## Top 3 commands

| Command | What it does | When to use |
|---|---|---|
| `/create-presentation` | New branded deck from a brief, content, or rough notes | ExCo packs, Cards quarterly, Board updates, sector reviews |
| `/redesign-deck` | Take an existing PPTX and re-render it to NBG standards | Slides inherited from a partner, McKinsey, or another unit |
| `/polish-slides` | Fast formatting pass — fonts, colours, alignment, spacing | A deck you wrote yourself that just needs to look the part |

Other commands: `/presentation-review` (teach the system your style), plus bundled creatives `/create-icon`, `/create-infographic`, `/create-mockup`.

## Common patterns

**Build an ExCo pack from scratch** (10-15 min):

```
/create-presentation <one-paragraph brief or paste content here>
# … review the generated PPTX in ~/Downloads …
# … edit anything that's off …
/presentation-review ~/Downloads/202605101422_cards_q1_results_exco.pptx
# … your edits become learned preferences for next time …
```

**Rescue a partner deck before a board meeting**:

```
/redesign-deck ~/Downloads/mellon_atm_proposal.pptx
# Storyline kept, layout/colour/typography rebuilt to NBG standards
```

**Quick polish on something you wrote yourself**:

```
/polish-slides ~/Downloads/sector_offsite_draft.pptx
# Fonts → Aptos, colours → NBG palette, spacing → grid, no structural changes
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Validator failed: bumper above title" | Known cosmetic issue — bumper at y=0.30/h=0.19/10pt + title at y=0.55 passes 17/17. Re-run `/create-presentation` with the same input |
| Infographics look like flat SVGs, not illustrations | `manage-nano-banana` not installed. Install `plessas-lab` marketplace, or accept the SVG fallback — both are brand-compliant |
| Output landed in the project repo, not Downloads | Should never happen — file path is hard-coded to `~/Downloads/`. If you see otherwise, run `/polish-slides` on the misplaced file to regenerate it correctly |
| Charts came out as pie charts | Re-run — pie charts are blocked at the QA stage. If they slipped through, file an issue |
| "Thank You" slide appeared | Same as above — blocked at QA. Re-run |
| Generated deck has too many slides for a 10-min slot | Add a length hint: `/create-presentation … keep it to 8 slides for a 10-min ExCo slot` |
| The system keeps using a layout you don't like | After editing the file, always run `/presentation-review` — that's how preferences are learned |

## Where things live

- **Generated decks**: `~/Downloads/YYYYMMDDHHMM_<descriptive_name>.pptx` (Athens timezone, never inside a repo)
- **Pending drafts the system is watching for your edits**: `~/.claude/presentations/pending/`
- **Your learned style preferences**: `plugins/decks/shared/presentation-style-guide.md` — updated automatically by `/presentation-review`
- **NBG brand specs** (colours, fonts, layouts): `plugins/decks/shared/brand-system/`
- **Validator**: `plugins/decks/tools/nbg-presentation/nbg_validate.py` — runs automatically; you can invoke it directly on any PPTX

## Want more?

- Architecture and the multi-agent pipeline: see [README.md](README.md)
- Sample storylines (YAML): `examples/`
- All commands: type `/` in Claude Code, scroll to the `decks:` group
- For Excel-driven decks (Cards monthly, VBM): use `/excel-to-deck` from the `excel` plugin — it hands off to `decks` automatically
