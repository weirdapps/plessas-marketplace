# Workflow: decks

Create branded presentations using the multi-agent pipeline.

## Commands

| Command | What it does |
|---|---|
| `/create-presentation <topic>` | Full pipeline: storyline → storyboard → graphics → QA |
| `/redesign-deck <path>` | Redesign an existing .pptx to brand standards |
| `/polish-slides <content>` | Quick formatting polish on existing slides |
| `/create-infographic <desc>` | Generate a data visualisation |
| `/create-icon <desc>` | Generate an SVG icon |
| `/create-mockup <path>` | Create a device mockup from a screenshot |

## Example session

```
You: /create-presentation Q4 Digital Banking results for the Board
Claude: [runs storyline → storyboard → graphics → QA pipeline]
Claude: Presentation saved to ~/Downloads/202605091200_q4_digital_banking.pptx
```

## Tips

- Be specific about your audience — "for the Board" vs "for the team standup" changes the entire narrative structure
- Decks uses McKinsey Pyramid Principle and SCQA framework by default
- All charts use doughnut format (never pie) per brand guidelines
- The QA agent checks 17 brand compliance rules before delivery
