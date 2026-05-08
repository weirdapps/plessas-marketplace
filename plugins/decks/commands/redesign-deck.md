---
description: "Redesign an existing presentation to NBG standards"
argument-hint: "[path to PPTX or paste content]"
allowed-tools: Task, Read, Write, Bash, Skill(document-skills:pptx)
---

<objective>
Analyze and redesign an existing presentation to meet NBG brand standards and executive-level quality.

User request: $ARGUMENTS
</objective>

<process>
## Redesign Workflow

1. **Extract Content with MarkItDown**
   - If the input is a file path (PPTX, PDF, DOCX), run `markitdown <filepath>` via Bash to convert it to structured Markdown
   - This preserves slide structure, tables, headings, and hierarchy as clean Markdown that is easy to analyze
   - Save the extracted Markdown to a temp file for reference: `/tmp/deck_extracted.md`
   - Review the extracted content to identify key messages, slide count, and areas needing improvement

2. **Evaluate Current State**
   - Brand compliance (colors, fonts, dimensions)
   - Visual hierarchy
   - Message clarity
   - Slide-by-slide assessment

3. **Restructure Narrative**
   - Apply Storyline Architect principles
   - One key message per slide
   - Insight-driven titles
   - Logical flow

4. **Redesign Layouts**
   - Apply appropriate NBG layouts
   - Improve visual hierarchy
   - Add proper white space
   - Align with brand guidelines

5. **Regenerate Presentation**
   - Apply NBG specifications:
     - Dimensions: 13.33" x 7.5" (LAYOUT_WIDE)
     - Font: Aptos
     - Colors: NBG palette
     - Small logo: 0.374", 7.071" (content slides)
     - Large logo: 0.374", 6.271" (covers/dividers)
     - Page numbers: 12.71", 7.1554" (content slides only)
     - Back cover: centered oval logo (no text)
     - Charts: doughnut only (NEVER pie)

6. **Quality Assurance**
   - Brand compliance check
   - Scannable in 5-7 seconds
   - Board-ready appearance
</process>

<redesign_principles>
## Executive Design Principles

### Content Refinement (Without Changing Meaning)
- Shorten long sentences
- Turn dense text into sharp, executive bullets
- Replace paragraphs with structured layouts
- Make slides scannable in 5-7 seconds

### Visual Enhancement
- Improve layout balance and spacing
- Reduce visual noise
- Create clear hierarchy
- Use alignment, grids, whitespace properly

### Slide Structure
- ONE clear message per slide
- Strong, insight-driven titles
- Logical flow from slide to slide
</redesign_principles>

<success_criteria>
- [ ] Content meaning preserved
- [ ] NBG branding applied consistently
- [ ] Visual quality improved
- [ ] One message per slide
- [ ] Insight-driven titles
- [ ] Correct dimensions and formatting (13.33" x 7.5")
- [ ] Logo on every slide (correct size/position per type)
- [ ] Page numbers on content slides only
- [ ] Plain back cover with centered logo (no "Thank You")
- [ ] Doughnut charts only (no pie charts)
- [ ] Board-ready appearance
</success_criteria>
