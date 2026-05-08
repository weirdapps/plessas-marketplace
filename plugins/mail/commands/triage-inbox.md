---
description: "Triage unread inbox: rule-match, LLM-classify, batch-move with safety contract and undo"
argument-hint: "[--dry-run] [--undo]"
allowed-tools: Agent, Read, Write, Bash, Glob, Grep, mcp__outlook-bridge__outlook_auth_check, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_list_folders, mcp__outlook-bridge__outlook_find_folder, mcp__outlook-bridge__outlook_create_folder, mcp__outlook-bridge__outlook_move_mail, mcp__outlook-bridge__outlook_get_mail
---

# /triage-inbox

Suggest folder moves for unread inbox messages, then execute the user-approved batch.

## Usage

```
/triage-inbox                    # default: scan all unread, suggest moves, prompt
/triage-inbox --dry-run          # classify only, don't prompt for moves
/triage-inbox --undo             # reverse the last batch
```

## Implementation

### Pre-flight
1. Call `mcp__outlook-bridge__outlook_auth_check`. If not ok, surface auth flow.
2. Read `~/.claude/triage/rules.yaml`. Validate against schema. On failure: report and abort.
3. Read `~/.claude/triage/locked-senders.txt`. Build lockset.

### Stage 1 — rule match
4. Call `mcp__outlook-bridge__outlook_list_mail` with `folder: "Inbox", top: 100, select: "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,HasAttachments,IsRead,WebLink,ConversationId"`.
5. Filter to unread (`IsRead == false`).
6. For each: invoke `agents/triage-engine` rule-matcher with rules.yaml. Tag as `matched_by: rule | unmatched`.

### Stage 2 — LLM classify unmatched
7. Call `mcp__outlook-bridge__outlook_list_folders` with `recursive: true`. Build folder list (paths only).
8. For each unmatched email: invoke llm-classifier with folder list + email metadata + body excerpt (fetch body via `mcp__outlook-bridge__outlook_get_mail` only if not already in metadata).
9. Validate LLM suggestions: drop `MOVE: <folder>` if folder not in folder list.

### Display + confirm
10. Group proposed moves by destination folder. Print:
```
Inbox/Newsletters       (12) ← rule "NBG newsletters"
Inbox/Vendors/Microsoft  (3) ← LLM (suggest promote? appears 3rd time)
...
```
11. Prompt: `[a]ccept all  [e]dit  [s]kip  [q]uit  [u]ndo last run`
12. If `e`: enter interactive edit (per-email accept/reject).
13. If `a`: continue. If `s`/`q`: exit without moving.

### Execute
14. For each destination folder:
    - Call `mcp__outlook-bridge__outlook_find_folder`. If null: `outlook_create_folder` with `createParents: true, idempotent: true`.
    - Split `ids` into batches of 20.
    - For each batch: `mcp__outlook-bridge__outlook_move_mail` with `continueOnError: true`.
    - Append per-message audit entries to `~/.claude/triage/audit-log.jsonl`.

### Stage 3 — promotion
15. Run promote-rule agent. Surface any pending promotions for user confirmation.

## Safety contract (enforced by code, not just docs)

- No move without explicit per-session confirmation.
- Refuse to move into folder paths matching `(Deleted Items|Junk Email|Junk|Trash)$`.
- Refuse to move emails whose sender matches a `keep_locked` rule.
- Audit-log every move with original folder Id (so undo can reverse).
- Cap batch size at 20 per `outlook_move_mail` call.

## Undo (--undo flag)

1. Read last `triage-inbox` entry from audit-log.jsonl.
2. Group reversal moves by `from_folder`.
3. Confirm with user: "Reverse 14 moves from /triage-inbox at 2026-04-22T14:23?"
4. On confirm: batch `outlook_move_mail` calls in reverse direction.
