---
description: "Summarise a Microsoft Teams chat or thread: decisions, action items, key points."
argument-hint: "[chat_id] [hours]"
allowed-tools: Read, Bash, mcp__plugin_chat_teams-bridge__teams_auth_check, mcp__plugin_chat_teams-bridge__teams_list_chats, mcp__plugin_chat_teams-bridge__teams_list_messages, mcp__plugin_chat_teams-bridge__teams_resolve_mri
---

# Teams Chat Summarise

Produce a concise summary of a Microsoft Teams chat conversation.

## Workflow

1. **If no chat_id provided**: list recent chats and let the user pick.

2. **Fetch messages** via `mcp__plugin_chat_teams-bridge__teams_list_messages` with `top` (default 50). The tool has no server-side time filter, so fetch by count and, when the user asks for a time window, filter the returned messages client-side by timestamp.

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
