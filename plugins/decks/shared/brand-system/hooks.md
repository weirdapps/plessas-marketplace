# Suggested Hooks for Communications Marketplace

Claude Code hooks are configured at the user level (`~/.claude/hooks.json`). Below are recommended hook configurations for quality assurance.

## Presentation Maker — PPTX Validation

After generating a PPTX file, remind to validate against NBG brand guidelines:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT\" | grep -q '\\.pptx'; then echo 'Reminder: Run nbg_validate.py on the generated PPTX to verify brand compliance.'; fi"
          }
        ]
      }
    ]
  }
}
```

## Creative Toolkit — SVG Validation

After creating an SVG icon, validate it follows NBG icon rules:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT\" | grep -q '\\.svg'; then echo 'Reminder: Validate SVG uses solid fills, no strokes, 64x64 viewBox.'; fi"
          }
        ]
      }
    ]
  }
}
```

## Installation

To add these hooks, merge the configurations into your `~/.claude/hooks.json` file. These are recommendations — adjust patterns and messages to match your workflow.
