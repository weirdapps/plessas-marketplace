---
description: "Draft and auto-send a reply to a Microsoft Teams chat message. Prefixes [Claude]; falls back to draft-and-confirm when the target chat is ambiguous."
argument-hint: "[chat_id]"
allowed-tools: Read, Write, Bash, mcp__plugin_chat_teams-bridge__*
---

# Teams Chat Reply

Draft and auto-send a reply to a Microsoft Teams chat. Every message carries a `[Claude]` prefix; falls back to draft-and-confirm when the target chat is ambiguous.

## Workflow

1. **If no chat_id provided**: list recent chats via `mcp__plugin_chat_teams-bridge__teams_list_chats` (top 10) and present them for the user to pick.

2. **Fetch context**: get the last 10 messages from the selected chat via `mcp__plugin_chat_teams-bridge__teams_list_messages`.

3. **Resolve participants** via `mcp__plugin_chat_teams-bridge__teams_resolve_mri` if needed.

4. **Draft a reply** matching the thread's language and tone:
   - If prior messages are in Greek, reply in Greek
   - Match the formality level of the conversation
   - Keep it concise; Teams messages are shorter than emails
   - Reference specific points from recent messages if relevant

5. **GATE, verify the recipient. This is a precondition, not a step you may reorder.** Do NOT call `mcp__plugin_chat_teams-bridge__teams_send_message` until you have confirmed that the resolved chat id belongs to the intended, known recipient. If the target chat is ambiguous, unfamiliar, or external, STOP: do not send, show the draft, and ask the user to confirm the target explicitly.

6. **Only once the gate above passes**: show the draft inline for transparency, then send it via `mcp__plugin_chat_teams-bridge__teams_send_message`. Every message MUST start with the `[Claude]` prefix so recipients know they are reading the agent and not the account owner typing personally.

## Important

- Auto-send is the default for this plugin. Draft-and-confirm only when the target chat is ambiguous or unfamiliar. If you would rather approve every message, say so at the start of the session and this command will draft instead.
- The `[Claude]` prefix is required on ALL Teams messages, no exceptions.
- Channel sends are not supported (Graph scope limitation). Only chat replies work.
- Keep replies shorter than emails; Teams is a messaging medium, not email.
