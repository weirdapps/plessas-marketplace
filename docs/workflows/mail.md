# Workflow: mail

Read, triage, draft, and send Outlook email with style-matching.

## Key commands

| Command | What it does |
|---|---|
| `/inbox-briefing` | Read inbox, summarise, highlight priorities |
| `/mail-review` | Deeper review with draft replies for important messages |
| `/send-mail` | Compose and send a new email |
| `/reply` | Reply to a specific email with style matching |
| `/triage-inbox` | Batch-classify and file unread mail |
| `/style-rebuild` | Regenerate your personal style guide from sent mail |

## Example session

```
You: /inbox-briefing
Claude: [reads inbox via outlook-bridge MCP]
Claude: 23 unread messages. 3 need action...
```

## Tips

- The style guide at `plugins/mail/shared/style-guide.md` controls tone, language, and formatting
- After 1-2 weeks of usage, run `/style-rebuild` to personalise the style guide from your actual sent mail
- Emails are always drafted as Outlook drafts first — never auto-sent
