---
description: "Draft and auto-send a reply to a Microsoft Teams chat message. Prefixes [Claude]; falls back to draft-and-confirm when the target chat is ambiguous."
argument-hint: "[chat_id]"
allowed-tools: Read, Write, Bash, mcp__teams-bridge__teams_auth_check, mcp__teams-bridge__teams_list_chats, mcp__teams-bridge__teams_list_messages, mcp__teams-bridge__teams_resolve_mri, mcp__teams-bridge__teams_send_message
---

# Teams Chat Reply

Draft and auto-send a reply to a Microsoft Teams chat. Every message carries a `[Claude]` prefix; falls back to draft-and-confirm when the target chat is ambiguous.

## Workflow

1. **If no chat_id provided**: list recent chats via `mcp__teams-bridge__teams_list_chats` (top 10) and present them for the user to pick.

2. **Fetch context**: get the last 10 messages from the selected chat via `mcp__teams-bridge__teams_list_messages`.

3. **Resolve participants** via `mcp__teams-bridge__teams_resolve_mri` if needed.

4. **Draft a reply** matching the thread's language and tone:
   - If prior messages are in Greek, reply in Greek
   - Match the formality level of the conversation
   - Keep it concise — Teams messages are shorter than emails
   - Reference specific points from recent messages if relevant

5. **Show the draft** inline for transparency, then send it via `mcp__teams-bridge__teams_send_message`. Every message MUST start with the `[Claude]` prefix so recipients know they are reading the agent and not the account owner typing personally.

6. **Before sending**: verify the target chat resolves to the intended, known recipient. If the target chat is ambiguous or unfamiliar, fall back to draft-and-confirm.

## Important

- Auto-send is the default for this plugin. Draft-and-confirm only when the target chat is ambiguous or unfamiliar. If you would rather approve every message, say so at the start of the session and this command will draft instead.
- The `[Claude]` prefix is required on ALL Teams messages — no exceptions.
- Channel sends are not supported (Graph scope limitation). Only chat replies work.
- Keep replies shorter than emails — Teams is a messaging medium, not email.
