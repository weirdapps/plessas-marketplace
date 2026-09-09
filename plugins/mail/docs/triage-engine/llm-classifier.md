# llm-classifier

Stage 2 of the triage cascade. For emails not matched by any rule, classify inline: the model already running `/triage-inbox` picks the best destination from the user's existing folder list. There is no separate API call, no SDK dependency, and no second model; this plugin has no network path of its own.

## Prompt

System: "You are an email triage assistant. Given the user's existing folder list and a new email, suggest the best destination folder. Reply with EXACTLY one of these formats:

- `MOVE: <folder-path>` moves to an existing folder
- `KEEP` leaves it in the inbox (action required)
- `ARCHIVE` moves to Inbox/Archive-<current-year>

You may not invent new folders. Only suggest folders that appear in the provided list."

User: "Existing folders: <comma-separated list from outlook_list_folders>

Email:
From: <sender>
To: <to>
Subject: <subject>
Date: <ReceivedDateTime>
Body (first 500 chars): <body excerpt>
"

## Guardrails

- Classify inline. Never call the public Anthropic HTTP endpoint directly, and never add an `anthropic` SDK dependency.
- Emit exactly one line per email, in one of the three formats above. No commentary.
- Classify the unmatched emails in as few passes as possible rather than reasoning about each one in isolation.
- Within a run, reuse a verdict already produced for the same (sender, subject) pair instead of re-deriving it. Persistent caching across runs is not implemented; do not claim it in output.
- Skip classification entirely when the rules.yaml lock-list (`keep_locked` rule for that sender) matches; these never get LLM-routed.

## Validation

- Parse response: regex `^(MOVE: (.+)|KEEP|ARCHIVE)$`
- For MOVE: verify suggested path appears in the supplied folder list. If not, treat as KEEP (don't surface a non-existent folder to the user).
