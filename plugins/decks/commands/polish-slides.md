---
description: "Quick polish of existing slides to NBG standards"
argument-hint: "[slide content or path to file]"
allowed-tools: Read, Task, Write, Skill(document-skills:pptx)
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
   - Bullets: #00DFF8 (Bright Cyan)
   - Accents: #007B85 (NBG Teal)

4. **Apply Typography**
   - Page titles: 24pt
   - Body text: 11-12pt
   - Section numbers: 60pt, format "01"

5. **Add Brand Elements**
   - Small logo in bottom-left (0.374", 7.071")
   - Large logo for covers/dividers (0.374", 6.271")
   - Page numbers bottom-right (12.71", 7.1554") - content slides only
   - Proper margins (0.37" sides)

6. **Output**
   - Generate formatted PPTX
</process>

<nbg_quick_reference>
## NBG Formatting Specs

### Dimensions
- 13.33" x 7.5" (LAYOUT_WIDE) (NOT default)

### Colors (no # for PptxGenJS)
- darkTeal: '003841' (titles)
- teal: '007B85' (section numbers)
- brightCyan: '00DFF8' (bullets)
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
- [ ] Professional appearance
</success_criteria>
