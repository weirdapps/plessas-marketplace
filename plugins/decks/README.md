# decks v1.0

Branded presentation system. Multi-agent pipeline producing board-ready PPTX with NBG brand compliance. Icons, infographics, and device mockups are bundled inside.

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
       (bundled)      (bundled)      (bundled)
```

## Commands

| Command | Description |
|---------|-------------|
| `/create-presentation` | Create new branded presentation from content |
| `/redesign-deck` | Redesign existing presentation to brand standards |
| `/polish-slides` | Quick formatting polish |
| `/create-infographic` | Generate data visualisation (bundled creative agent) |
| `/create-icon` | Create SVG icon (bundled creative agent) |
| `/create-mockup` | Create device mockup from screenshot (bundled creative agent) |

## Directory Structure

```
decks/
├── .claude-plugin/plugin.json
├── README.md
├── orchestrator/nbg-presenter/AGENT.md   # Master orchestrator
├── agents/                                # Core presentation agents (flat)
│   ├── storyline-architect.md
│   ├── storyboard-designer.md
│   ├── graphics-renderer.md
│   └── presentation-qa.md
├── commands/                              # Slash commands
│   ├── create-presentation.md
│   ├── redesign-deck.md
│   ├── polish-slides.md
│   └── presentation-review.md
├── bundled/creative/                      # Bundled creative agents (was creative-toolkit)
│   ├── agents/
│   │   ├── icon-designer.md
│   │   ├── infographic-specialist.md
│   │   └── device-mockup.md
│   ├── commands/
│   │   ├── create-icon.md
│   │   ├── create-infographic.md
│   │   └── create-mockup.md
│   ├── tools/device-mockup/
│   └── assets/device-frames/
├── shared/                                # Plugin-internal shared resources
│   ├── brand-system/                      # Brand specs (colours, fonts, layouts)
│   └── presentation-style-guide.md        # Optional user-customisable style preferences
├── assets/                                # Brand assets (logos, icons, templates, mockups)
├── examples/                              # Sample YAML storylines
└── tools/nbg-presentation/                # Python build/validation tools
```

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
python tools/nbg-presentation/nbg_validate.py presentation.pptx
```

## License

MIT
