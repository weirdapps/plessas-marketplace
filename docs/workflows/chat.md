# Workflow: chat

Read, summarise, and reply to Microsoft Teams chats and channels.

## Commands

| Command | What it does |
|---|---|
| `/chat-inbox` | Summarise recent Teams chats, highlight urgent |
| `/chat-reply [chat_id]` | Draft and auto-send a reply to a chat; prefixes `[Claude]`; falls back to draft-and-confirm when the target is ambiguous |
| `/chat-summarize [chat_id]` | Summarise a chat thread: decisions, actions, key points |
| `/chat-channel-digest [team_id] [channel_id]` | Executive digest of channel activity |

## Example session

```
You: /chat-inbox
Claude: [reads chats via teams-bridge MCP]
Claude: 5 chats with recent activity. 2 need response...
```

## Tips

- `/chat-reply` auto-sends by default; the draft is shown inline for transparency before it goes. Fall-back to draft-and-confirm applies when the target chat is ambiguous.
- Channel message sends are not supported (Graph scope limitation)
- Chat summaries include decisions and action items by default
