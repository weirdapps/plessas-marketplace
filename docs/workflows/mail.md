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
| `/forward` | Forward a thread with auto-quoted original |
| `/archive-thread` | Move a thread into the year-stamped archive folder |
| `/folder-tree` | Display the Outlook folder hierarchy with counts |

For corpus-driven analytics (`/comm-report`, `/style-rebuild`), see the [`mail-pro`](mail-pro.md) plugin — it's an optional companion that requires the private `second-brain` knowledge store.

## Example session

```
You: /inbox-briefing
Claude: [reads inbox via outlook-bridge MCP]
Claude: 23 unread messages. 3 need action...
```

## Tips

- The style guide at `plugins/mail/shared/style-guide.md` controls tone, language, and formatting
- After 1-2 weeks of usage, run `/style-rebuild` (in `mail-pro`) to personalise the style guide from your actual sent mail. If you don't have second-brain access, hand-edit the file or work from the template in `shared/email-style-template/style-guide-template.md`.
- Emails are always drafted as Outlook drafts first — never auto-sent
