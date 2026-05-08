---
description: "Move a conversation thread to Inbox/Archive-<current-year>, creating the folder if needed"
argument-hint: "[subject or ConversationId] [--undo]"
allowed-tools: Bash, Read, Write, mcp__outlook-bridge__outlook_find_folder, mcp__outlook-bridge__outlook_create_folder, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_move_mail
---

# /archive-thread

Move all messages in a conversation thread to `Inbox/Archive-<current-year>`, creating the folder if it doesn't exist.

## Usage

```
/archive-thread "Re: Q1 budget review"
/archive-thread <ConversationId>
```

## Implementation

1. Determine current year via `TZ='Europe/Athens' date +%Y`. Compute `archive_path = "Inbox/Archive-${YEAR}"`.
2. Call `mcp__outlook-bridge__outlook_find_folder` with `path: archive_path`. If returns null, call `mcp__outlook-bridge__outlook_create_folder` with `path: archive_path, createParents: true, idempotent: true`.
3. Resolve target messages:
   - If input looks like a ConversationId (base64-ish, >50 chars): call `mcp__outlook-bridge__outlook_list_mail` with `select: "Id,Subject,ConversationId,ReceivedDateTime"` and filter client-side by ConversationId.
   - Otherwise: call `outlook_list_mail` with the subject as a filter (TODO: needs $search support upstream — for now, use top 100 + client-side subject normalization).
4. Display to user: count, date range, sample subjects. Wait for confirmation.
5. On confirmation: split message Ids into batches of 20, call `mcp__outlook-bridge__outlook_move_mail` per batch with `continueOnError: true`.
6. Append batch summary to `~/.claude/triage/audit-log.jsonl`:
```json
{"ts":"<iso>","action":"archive-thread","subject":"...","conversation_id":"...","moved_count":N,"to_folder":"Inbox/Archive-2026","from_folder":"Inbox","ids":["..."]}
```

## Undo

`/archive-thread --undo` reverses the last archive operation by reading the audit log's most recent `archive-thread` entry and moving the recorded ids back to the recorded `from_folder`.
