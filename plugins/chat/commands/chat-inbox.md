---
description: "Summarise unread Microsoft Teams chats. Lists recent chats, highlights unread, surfaces urgent items."
allowed-tools: Read, Bash, mcp__teams-bridge__teams_auth_check, mcp__teams-bridge__teams_list_chats, mcp__teams-bridge__teams_list_messages, mcp__teams-bridge__teams_resolve_mri
---

# Teams Chat Inbox

Summarise the user's recent Microsoft Teams chats, highlighting chats with unread messages and surfacing urgent or action-required items.

## Workflow

1. **Check auth** first via `mcp__teams-bridge__teams_auth_check`. If status is not `ok`, tell the user to run `teams-cli login` and stop.

2. **List recent chats** via `mcp__teams-bridge__teams_list_chats` with `top: 20`.

3. **For each chat with recent activity** (last 24 hours), fetch the last 5 messages via `mcp__teams-bridge__teams_list_messages` with the chat_id and `top: 5`.

4. **Resolve sender identities** if needed via `mcp__teams-bridge__teams_resolve_mri` for any MRI-format sender IDs.

5. **Synthesise a briefing** with:
   - Total chats with recent activity
   - Unread count (if discernible from message metadata)
   - Per-chat summary: participants, last message preview, urgency assessment
   - Action items surfaced from message content

## Output Format

Present as a concise briefing — not a raw dump. Group by urgency:
1. **Needs response** — someone asked you a question or tagged you
2. **FYI** — informational messages, no action needed
3. **Low priority** — group chats with ambient activity

## Auth Error Handling

If `teams_auth_check` returns `missing` or `expired`:
```
Teams auth is not active. Please run:
  teams-cli login
Then retry /chat-inbox.
```
