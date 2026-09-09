---
description: "Compare a finalized presentation against its draft to learn style preferences"
argument-hint: "[path/to/final.pptx]"
allowed-tools: Agent, Read, Write, Bash, Skill(document-skills:pptx), mcp__plugin_mail_outlook-bridge__outlook_list_mail, mcp__plugin_mail_outlook-bridge__outlook_get_mail, mcp__plugin_mail_outlook-bridge__outlook_download_attachments
---

<objective>
Compare a user-finalized presentation against its original draft to learn presentation style preferences.

User request: $ARGUMENTS
</objective>

<process>
## Presentation Review Workflow

### Setup: Ensure Persistence Directories Exist

```bash
mkdir -p ~/.claude/presentations/pending ~/.claude/presentations/reviewed
```

This is idempotent: it does nothing if the directories already exist.

### 1. Locate Draft Record

- Check `~/.claude/presentations/pending/` for a draft record matching the filename
- If no exact match, list available draft records and ask the user to confirm
- If no draft records exist, inform the user and offer to do a standalone style analysis

### 2. Extract Final Content

- Extract slide content from the final PPTX (use python-pptx or unzip + XML parsing)
- Parse each slide: title, content, layout, chart types, element positioning
- Compute SHA-256 hash and compare against draft record hash to confirm changes were made

### 3. Slide-by-Slide Comparison

Compare draft vs final for each slide:

- **Title rewrites**: Draft title vs actual title (wording, style, length)
- **Slide reordering**: Draft sequence vs actual sequence
- **Content additions/removals**: New points added, existing points removed or reworded
- **Chart type swaps**: e.g., bar replaced with doughnut, line replaced with waterfall
- **Layout changes**: e.g., full-width changed to two-column, 50/50 changed to 40/60
- **Slides added or removed**: New slides not in draft, draft slides deleted

### 4. Classify Each Slide

Assign a classification to each slide:

| Classification | Criteria |
|---------------|----------|
| `USED_AS_IS` | No meaningful changes (minor formatting only) |
| `MODIFIED` | Title reworded, points edited, or layout tweaked |
| `HEAVILY_REWRITTEN` | Substantially different content, structure, or visual approach |
| `NOT_USED` | Draft slide removed entirely from final |
| `NEW` | Slide in final that was not in draft |

### 5. Save Comparison Record

Save detailed comparison to `~/.claude/presentations/reviewed/`:

```json
{
  "id": "review-YYYY-MM-DD-NNN",
  "draft_id": "pres-YYYY-MM-DD-NNN",
  "reviewed_at": "ISO-8601",
  "draft_path": "/path/to/draft.pptx",
  "final_path": "/path/to/final.pptx",
  "draft_hash": "sha256:...",
  "final_hash": "sha256:...",
  "summary": {
    "total_draft_slides": N,
    "total_final_slides": N,
    "used_as_is": N,
    "modified": N,
    "heavily_rewritten": N,
    "not_used": N,
    "new": N
  },
  "slides": [
    {
      "draft_index": 1,
      "final_index": 1,
      "classification": "MODIFIED",
      "changes": {
        "title": { "draft": "...", "final": "..." },
        "content_delta": "...",
        "layout_change": null,
        "chart_swap": null
      }
    }
  ],
  "patterns_detected": [
    "User prefers data-driven titles over narrative titles",
    "User consistently adds more detail to bullet points"
  ]
}
```

### 6. Update Presentation Style Guide

Read `shared/presentation-style-guide.md` and update with learned preferences:

- Aggregate patterns across all reviews (not just this one)
- Only update a preference if it appears in 2+ reviews (avoid one-off noise)
- Add confidence levels based on consistency of the pattern

### 7. Show Delta Report

Display a clear summary to the user:

- Overall statistics (how many slides changed)
- Notable patterns detected
- Specific examples of changes made
- New preferences added to style guide (if any)

### Auto-Detection (when no path is provided)

When no path is provided, find the finalized version automatically:

**Priority 1, Email (primary):** The user sends finalized decks via email and CCs himself, so sent decks land in Archive. Scan it for PPTX attachments:

1. `mcp__plugin_mail_outlook-bridge__outlook_list_mail` on the Archive folder, bounded by the draft record's creation date and a sane result cap. Never enumerate the whole archive.
2. `mcp__plugin_mail_outlook-bridge__outlook_get_mail` on each candidate to read the body and the attachment list.
3. `mcp__plugin_mail_outlook-bridge__outlook_download_attachments` for the messages whose attachment filename matches a pending draft record, saving to a temp dir for comparison.

These tools come from the `mail` plugin's bundled outlook-bridge MCP. If they are absent from your tool list, `mail` is not installed: say so and ask the user to install it. Do NOT read from macOS Mail via AppleScript. It is a separate local store that is not synced with M365, so it silently returns stale or missing mail.

- Analyze email body to classify intent (final delivery vs review request vs draft for feedback)
- Only use attachments from "final delivery" emails

**Priority 2, Local file (fallback):** If PPTX still exists locally, compare SHA-256 hash against draft record.

**Priority 3, Sent Items (recent only):** Fall back to Sent Items for emails sent in the last few hours (user regularly empties Sent Items).

Present findings and ask user to confirm before proceeding.
</process>

<success_criteria>

- [ ] Draft record found and loaded
- [ ] Final PPTX content extracted successfully
- [ ] Slide-by-slide comparison completed
- [ ] Each slide classified accurately
- [ ] Comparison record saved to ~/.claude/presentations/reviewed/
- [ ] Draft record status updated from "pending" to "reviewed"
- [ ] Presentation style guide updated with new patterns (if sufficient data)
- [ ] Delta report displayed to user
</success_criteria>
