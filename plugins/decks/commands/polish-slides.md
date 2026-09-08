---
description: "Quick polish of existing slides to NBG standards"
argument-hint: "[slide content or path to file]"
allowed-tools: Read, Agent, Write, Edit, Bash, Skill(document-skills:pptx)
---

<objective>
Apply NBG formatting and brand standards to existing slide content without full restructuring.

User request: $ARGUMENTS
</objective>

<process>
## Quick Polish Workflow

1. **Take Content As-Is**
   - Accept the existing structure
   - Focus on formatting, not narrative

2. **Apply NBG Formatting**
   - Dimensions: 13.33" x 7.5" (LAYOUT_WIDE)
   - Background: white (#FFFFFF)
   - Font: Aptos throughout
   - All text boxes: margin: 0

3. **Apply NBG Colors**
   - Titles: #003841 (Dark Teal)
   - Body text: #202020 (Dark Text)
   - Bullets: #00ADBF (Cyan)
   - Accents: #007B85 (NBG Teal)

4. **Apply Typography**
   - Page titles: 24pt Regular (never bold, Standard #16)
   - Body text: 14pt minimum. `shared/presentation-style-guide.md` Standard #11 carries the floor
     and the per-element minimums; polishing is the moment to raise undersized text, not preserve it
   - Section numbers: 60pt, format "01"

5. **Add Brand Elements**
   - Small logo in bottom-left (0.374", 7.071")
   - Large logo for covers/dividers (0.374", 6.271")
   - Page numbers bottom-right (12.71", 7.1554") - content slides only
   - Left gutter at 0.374" (Standard #15)

6. **Output and check**
   - Generate the formatted PPTX
   - Run the brand validator on it and report the result:
     ```bash
     "${CLAUDE_PLUGIN_ROOT}/tools/nbg-presentation/.venv/bin/python3" \
       "${CLAUDE_PLUGIN_ROOT}/tools/nbg-presentation/nbg_validate.py" <output.pptx>
     ```
   - A polish that leaves validator failures behind has not polished anything. Fix them, or say
     plainly which ones remain and why. For a full two-layer review dispatch `decks:presentation-qa`
     instead; this command is the light path and the validator is its floor.
</process>

<nbg_quick_reference>

## NBG Formatting Specs

### Dimensions

- 13.33" x 7.5" (LAYOUT_WIDE) (NOT default)

### Colors (no # for PptxGenJS)

- darkTeal: '003841' (titles)
- teal: '007B85' (section numbers)
- cyan: '00ADBF' (bullets)
- darkText: '202020' (body)
- white: 'FFFFFF' (background)

### Fonts

- Primary: Aptos
- Fallback: Arial, Calibri

### Logo (from Template)

- Small (content): x=0.374", y=7.071", 0.822" x 0.236"
- Large (covers): x=0.374", y=6.271", 2.191" x 0.630"
- Back cover: centered oval logo (5.44", 2.98"), NO text

### Text Box Rule

- margin: 0 (always)
</nbg_quick_reference>

<success_criteria>

- [ ] Correct dimensions applied
- [ ] NBG colors used
- [ ] Aptos font throughout
- [ ] Logo on every slide
- [ ] Text boxes with margin: 0
- [ ] No text below the Standard #11 floor
- [ ] `nbg_validate.py` run, and its result reported
- [ ] Professional appearance
</success_criteria>
