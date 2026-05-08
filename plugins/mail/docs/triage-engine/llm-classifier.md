# llm-classifier

Stage 2 of the triage cascade. For emails not matched by any rule, ask Claude Haiku 4.5 to suggest a folder.

## Prompt

System: "You are an email triage assistant. Given the user's existing folder list and a new email, suggest the best destination folder. Reply with EXACTLY one of these formats:
- `MOVE: <folder-path>` — move to an existing folder
- `KEEP` — leave in inbox (action required)
- `ARCHIVE` — move to Inbox/Archive-<current-year>

You may not invent new folders. Only suggest folders that appear in the provided list."

User: "Existing folders: <comma-separated list from outlook_list_folders>

Email:
From: <sender>
To: <to>
Subject: <subject>
Date: <ReceivedDateTime>
Body (first 500 chars): <body excerpt>
"

## Cost guardrails

- Use Haiku 4.5 (`claude-haiku-4-5`)
- max_tokens: 50
- Cache by SHA256(sender + subject) for 30 days — same sender + same subject pattern usually has the same answer
- Skip LLM call if rules.yaml lock-list (`keep_locked` rule for that sender) matches — these never get LLM-routed

## Validation

- Parse response: regex `^(MOVE: (.+)|KEEP|ARCHIVE)$`
- For MOVE: verify suggested path appears in the supplied folder list. If not, treat as KEEP (don't surface a non-existent folder to the user).
