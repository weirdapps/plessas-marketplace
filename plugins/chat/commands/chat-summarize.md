---
name: chat-summarize
description: Summarise a Microsoft Teams chat or thread — decisions, action items, key points.
args:
  - name: chat_id
    description: "The chat ID to summarise. If omitted, show recent chats for selection."
    required: false
  - name: hours
    description: "Lookback window in hours (default: 24)."
    required: false
---

# Teams Chat Summarise

Produce a concise summary of a Microsoft Teams chat conversation.

## Workflow

1. **If no chat_id provided**: list recent chats and let the user pick.

2. **Fetch messages** via `mcp__teams-bridge__teams_list_messages` with `top: 50` and optionally `since` (computed from hours arg, default 24h).

3. **Resolve participant identities** for any MRI-format senders.

4. **Analyse the conversation** and produce:
   - **Topic**: what the conversation is about (1 sentence)
   - **Key points**: the 3-5 most important things said (bullet list)
   - **Decisions made**: any explicit agreements or choices (if any)
   - **Action items**: who committed to do what, by when (if any)
   - **Open questions**: unresolved threads or unanswered questions
   - **Participants**: who was active in the window

## Output Format

Structured, scannable. Use bold headers. Keep the total under 300 words unless the conversation was extremely long.

## Edge Cases

- If the chat has < 3 messages in the window, say "Not enough recent activity to summarise."
- If messages are in Greek, produce the summary in Greek.
- If mixed Greek/English, produce in the dominant language of the messages.
