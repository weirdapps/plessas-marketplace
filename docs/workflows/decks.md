# Workflow: decks

Create branded presentations using the multi-agent pipeline. The plugin's own
[README](../../plugins/decks/README.md) has the full which-command-when table, the
requirements and where every file lands.

## Commands

| Command | What it does |
|---|---|
| `/create-presentation <topic>` | Full pipeline: storyline → deck spec → build and brand check → a look at every slide → QA |
| `/redesign-deck <path>` | Rebuild an existing .pptx or .pdf to brand standards: every figure and source kept, storyline and layout redone |
| `/polish-slides <path>` | Quick formatting polish on a deck that is nearly right |
| `/review-deck <path>` | Check any deck before it ships (validator plus a look at every slide); changes nothing |
| `/presentation-review <path>` | Learn your preferences from the edits you made to a generated deck |
| `/create-keynote <topic>` | Dark full-bleed deck for a stage talk (Standard #21, external or bank-wide audience only) |
| `/create-infographic <desc>` | Generate a data visualisation |
| `/create-icon <desc>` | Generate an SVG icon |
| `/create-mockup <path>` | Create a device mockup from a screenshot |

## Example session

```
You: /create-presentation Q4 Digital Banking results for the Board
Claude: [storyline → deck spec] The outline, one action title per slide, and two open questions
You: Agreed. The figures come from the Q4 results pack, as of 31 December
Claude: [build → render → QA]
Claude: ~/Downloads/202605091200_q4_digital_banking.pptx: 12 slides, QA PASS
```

## Tips

- Be specific about your audience: "for the Board" vs "for the team standup" changes the entire narrative structure
- Decks uses McKinsey Pyramid Principle and SCQA framework by default
- Proportions are drawn as doughnuts, never pies, per brand guidelines
- Every deck passes the brand validator and a QA review of each rendered slide before delivery
- Edit a generated deck in PowerPoint, then run `/presentation-review` on it: your changes become preferences for next time, kept in your own plugin data, never in the repo
