# decks v1.0

Branded presentation system. Multi-agent pipeline producing board-ready PPTX with NBG brand compliance. Eight agents and nine commands, including icon, infographic and device-mockup generation.

## Architecture

```
                    NBG PRESENTER
                  (Master Orchestrator)
                          |
        +-----------------+-----------------+
        v                 v                 v
  STORYLINE         STORYBOARD         GRAPHICS
  ARCHITECT          DESIGNER          RENDERER
                          |
            +-------------+-------------+
            v             v             v
       INFOGRAPHIC      ICON         DEVICE
       SPECIALIST     DESIGNER       MOCKUP
```

All eight agents live in `agents/`, dispatched by name (`decks:storyline-architect`,
`decks:presentation-qa`, and so on). Presentation QA is a **gate**: `/create-presentation` and
`/redesign-deck` do not ship a deck until it returns PASS.

## Commands

| Command | Description |
|---------|-------------|
| `/create-presentation` | Create new branded presentation from content |
| `/create-keynote` | Build a dark full-bleed keynote for a stage talk (Standard #21, external or bank-wide audience only) |
| `/redesign-deck` | Redesign existing presentation to brand standards |
| `/polish-slides` | Quick formatting polish |
| `/presentation-review` | Compare a finalised presentation against its draft to learn style preferences |
| `/create-infographic` | Generate data visualisation (creative toolkit) |
| `/create-icon` | Create SVG icon (creative toolkit) |
| `/create-mockup` | Create device mockup from screenshot (creative toolkit) |

## Directory Structure

```
decks/
├── .claude-plugin/plugin.json
├── README.md
├── agents/                                # ALL agents live here (flat).
│   │                                      # Only this directory is auto-discovered;
│   │                                      # an agent placed anywhere else never loads.
│   ├── nbg-presenter.md                   # Master orchestrator
│   ├── storyline-architect.md
│   ├── storyboard-designer.md
│   ├── graphics-renderer.md
│   ├── presentation-qa.md
│   ├── icon-designer.md
│   ├── infographic-specialist.md
│   └── device-mockup.md
├── commands/                              # Slash commands
│   ├── create-presentation.md
│   ├── create-keynote.md
│   ├── redesign-deck.md
│   ├── polish-slides.md
│   └── presentation-review.md
├── bundled/creative/                      # Bundled creative toolkit (was creative-toolkit)
│   ├── commands/                          # Registered via plugin.json "commands" array
│   │   ├── create-icon.md
│   │   ├── create-infographic.md
│   │   └── create-mockup.md
│   ├── tools/device-mockup/
│   └── assets/device-frames/
├── shared/                                # Plugin-internal shared resources
│   ├── brand-system/                      # Brand specs (colours, fonts, layouts)
│   └── presentation-style-guide.md        # Optional user-customisable style preferences
├── assets/                                # Brand assets (logos, icons, screenshots, templates)
├── examples/                              # Sample YAML storylines
├── tools/nbg-presentation/                # Python build/validation tools (light mode)
└── tools/nbg-keynote/                     # Keynote compositor (dark mode, Standard #21)
```

`installers/install.sh` builds a separate Python venv for each of the three tool directories
(`tools/nbg-presentation`, `tools/nbg-keynote`, `bundled/creative/tools/device-mockup`) and
installs that directory's `requirements.txt` into it. Always invoke a tool through its own
`.venv/bin/python3`; a bare `python3` will not have the dependencies. **Python 3.12+ is a hard
floor**, not a preference: `numpy>=2.5.2` declares `requires-python >=3.12`, so on 3.11 the
install cannot resolve at all.

## Brand Quick Reference

### Primary Colours

| Name | Hex | Usage |
|------|-----|-------|
| Dark Teal | `003841` | Titles, icons |
| NBG Teal | `007B85` | Brand, section numbers |
| Cyan | `00ADBF` | Primary chart colour |
| Dark Text | `202020` | Body text |

### Quality Standards

Every presentation must pass:

- Dimensions: 13.33" x 7.5" (LAYOUT_WIDE)
- Background: white (#FFFFFF)
- Font: Aptos throughout
- No pie charts (use doughnut)
- No "Thank You" slides (plain back cover with logo)
- One key message per slide

## Validation

```bash
"${CLAUDE_PLUGIN_ROOT}/tools/nbg-presentation/.venv/bin/python3" \
  "${CLAUDE_PLUGIN_ROOT}/tools/nbg-presentation/nbg_validate.py" presentation.pptx
```

## License

MIT
