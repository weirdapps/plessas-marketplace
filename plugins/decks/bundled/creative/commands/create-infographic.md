---
description: "Create an infographic or data visualization (NBG brand defaults)"
argument-hint: "[data or description of infographic]"
allowed-tools: Task, Skill(manage-nano-banana), Bash
---

<objective>
Create a professional infographic or data visualization. Uses NBG brand defaults unless a different brand is specified.

User request: $ARGUMENTS
</objective>

<process>
## Infographic Creation Workflow

1. **Analyze Request**
   - Identify data type (comparison, timeline, process, KPIs)
   - Determine best visualization pattern
   - Note any specific requirements

2. **Select Pattern**
   Based on content type:
   - **Comparison**: Side-by-side, bar chart
   - **Time series**: Line chart, timeline
   - **Proportions**: Doughnut (NEVER use pie charts)
   - **Process**: Sequential steps, flow diagram
   - **KPIs**: Dashboard grid (2x3, 3x3)
   - **List**: Numbered grid, vertical list

3. **Generate Visual**
   Using manage-nano-banana skill with these specifications:
   - Style: Clean, modern, professional
   - Primary color: #007B85 (NBG Teal)
   - Accent color: #00DFF8 (Bright Cyan)
   - Text color: #003841 (Dark Teal headings), #202020 (body)
   - Background: White (#FFFFFF) or transparent
   - Font: Roboto or Aptos
   - Orientation: Landscape (16:9)

4. **Quality Check**
   - Colors match NBG palette
   - Clean, professional appearance
   - Data is clear and readable
   - No visual clutter
</process>

<nbg_colors>
## Infographic Colors (NBG Defaults)

### Chart Color Sequence (in order)
1. #00ADBF - Cyan (primary)
2. #003841 - Dark Teal
3. #007B85 - NBG Teal
4. #939793 - Medium Gray
5. #BEC1BE - Light Gray
6. #00DFF8 - Bright Cyan

### Status Colors
- Success: #73AF3C
- Alert: #AA0028
- Gold: #D9A757
- Blue: #0D90FF
</nbg_colors>

<success_criteria>
- [ ] Infographic generated successfully
- [ ] Colors match target brand palette (NBG default)
- [ ] Clean, professional appearance
- [ ] Content is clear and informative
- [ ] Correct orientation and aspect ratio
</success_criteria>
