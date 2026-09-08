---
description: "Create a new NBG-branded presentation from content or brief"
argument-hint: "[topic, content, or brief]"
allowed-tools: Agent, Read, Write, Bash, Skill(manage-nano-banana), Skill(document-skills:pptx), mcp__plugin_mail_outlook-bridge__outlook_list_mail, mcp__plugin_mail_outlook-bridge__outlook_get_mail
---

<objective>
Create a professional, board-ready presentation following NBG brand guidelines.

User request: $ARGUMENTS
</objective>

<process>
## McKinsey-Quality Orchestration Workflow

### Setup: Ensure Persistence Directories Exist

```bash
mkdir -p ~/.claude/presentations/pending ~/.claude/presentations/reviewed
```

This is idempotent: it does nothing if the directories already exist.

### 0. Continuous Learning (automatic)

- Check `~/.claude/presentations/pending/` for drafts the user has modified since generation
- If modified drafts found: quick-compare, extract patterns, update `shared/presentation-style-guide.md`
- Load learned style preferences from the style guide (title style, layout, charts, density, narrative framework)
- Pass preferences to downstream agents in handoff payloads (the envelope shape is defined in `decks:nbg-presenter`)

### 1. Analyze Input & Apply Pyramid Principle

- Determine input type (raw content, brief, data)
- Identify audience and purpose
- **Lead with the answer**: What is the main recommendation?
- Structure using SCQA (Situation-Complication-Question-Answer)

### 2. Storyline Creation (Storyline Architect)

Dispatch `decks:storyline-architect` to create the narrative structure:

- Apply **Pyramid Principle**: Answer first, then support
- Define **ONE key message per slide** (no exceptions)
- Create **insight-driven ACTION TITLES** (full sentences, not labels)
- Apply **"So What?" test**: Why does each slide matter?
- Ensure arguments are **MECE** (Mutually Exclusive, Collectively Exhaustive)
- Recommend slide types and visualizations
- Create executive summary using SCR framework

### 3. Storyboard Design (Storyboard Designer)

Dispatch `decks:storyboard-designer` for visual layout:

- Select appropriate NBG layouts for each slide type
- Specify exact positioning (pixels, not approximations)
- Apply visual hierarchy to emphasize key message
- Identify custom visual needs (charts, icons, infographics)
- Ensure adequate white space (don't crowd slides)

### 4. Asset Generation (if needed)

- Dispatch `decks:infographic-specialist` for charts, diagrams and KPI dashboards (SVG-based)
- Dispatch `decks:icon-designer` for custom NBG-compliant SVG icons
- **manage-nano-banana** (OPTIONAL, only if `plessas-lab` marketplace is installed): Complex AI-generated infographics requiring rasterised image output. If the `Skill(manage-nano-banana)` is not available in your environment, silently skip this step and rely on `decks:infographic-specialist` and `decks:icon-designer` for all visuals; every deck remains fully producible without it.
- Apply semantic colors: green=good, red=bad, gray=neutral

### 5. Final Assembly (Graphics Renderer)

Dispatch `decks:graphics-renderer` to create the pixel-perfect PPTX (it may use `document-skills:pptx` internally):

- Dimensions: 13.33" x 7.5" (LAYOUT_WIDE) (NBG custom, NOT standard)
- Background: white (#FFFFFF) - ALWAYS
- Font: Aptos (Arial fallback)
- Small logo on content slides (0.374", 7.071")
- Large logo on covers/dividers (0.374", 6.271")
- Page numbers on content slides only (12.71", 7.1554")
- Bullets: Cyan (#00ADBF)
- All text boxes: margin: 0
- **NO pie charts** - use doughnut instead
- **NO "Thank You" slides** - use plain back cover with centered logo

### 5B. Cross-Plugin Integration

- **--from-email [subject]**: If provided, read the email thread through the `mail` plugin's outlook-bridge MCP (`mcp__plugin_mail_outlook-bridge__outlook_list_mail`, then `mcp__plugin_mail_outlook-bridge__outlook_get_mail`) and use it as input content. If those tools are absent from your tool list the `mail` plugin is not installed: say so and ask the user to install it. Do not fall back to macOS Mail, which is not synced with M365.
- After completion, offer: "Would you like to email this deck? Use `/send-mail` with the deck attached."

### 6. QA Gate (Presentation QA)

Dispatch `decks:presentation-qa` with the rendered PPTX path. **This is a gate, not a review: nothing ships until it returns PASS.**

It runs both layers, brand compliance via `nbg_validate.py` and then content and composition, and returns either PASS or a per-slide fix list. On a fix list, dispatch `decks:graphics-renderer` with that list and re-run QA. Maximum 2 remediation cycles; if it still fails, stop and present the remaining issues to the user rather than shipping.

The standards it holds you to:

- **Read-Through Test**: Read only titles, do they tell the story?
- **5-7 Second Test**: Is each slide scannable?
- **Brand Compliance**: All NBG specs followed?
- **"So What?" Passed**: Does every slide contribute?
- **Professional Appearance**: Board-ready?

### 7. Draft Record & Learning Prompt

- Graphics Renderer saves a draft record to `~/.claude/presentations/pending/` (JSON with slide content + file hash)
- Display prominently: "After editing, run `/presentation-review path/to/final.pptx` to teach the system your preferences"
</process>

<nbg_essentials>

## NBG Quick Reference

### Dimensions

- EMU: 12,192,000 x 6,858,000
- Inches: 13.33" x 7.5" (use LAYOUT_WIDE)

### Colors (no # for PptxGenJS)

- Title: 003841 (Dark Teal)
- Body: 202020 (Dark Text)
- Section numbers: 007B85 (NBG Teal)
- Bullets: 00ADBF (Cyan)
- Background: FFFFFF (White)

### Logo (from Template)

- Small (content): 0.374", 7.071" (0.822" x 0.236")
- Large (covers): 0.374", 6.271" (2.191" x 0.630")
- Back cover: centered oval (5.44", 2.98"), NO text
</nbg_essentials>

<success_criteria>

## McKinsey Quality Standards

### Structure

- [ ] Pyramid Principle applied: Answer first, then support
- [ ] SCQA framework followed
- [ ] Executive summary uses SCR format
- [ ] Arguments are MECE

### Content

- [ ] Every slide has exactly ONE key message
- [ ] All titles are insight-driven ACTION TITLES (full sentences)
- [ ] Every slide passes "So What?" test
- [ ] Maximum 5 points per slide
- [ ] Read-through test passed (titles tell the story)

### Visual Design

- [ ] NBG dimensions: 13.33" x 7.5" (LAYOUT_WIDE)
- [ ] Aptos font throughout
- [ ] NBG color palette only
- [ ] Logo on every slide (small for content, large for covers)
- [ ] Page numbers on content slides only
- [ ] Plain back cover with centered logo (no "Thank You")
- [ ] Doughnut charts only (NEVER pie)
- [ ] Adequate white space
- [ ] Scannable in 5-7 seconds

### Quality Assurance

- [ ] Brand compliance verified
- [ ] Professional, board-ready appearance
- [ ] No chartjunk - every element serves a purpose
</success_criteria>
