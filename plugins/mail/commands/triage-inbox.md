---
description: "Triage unread inbox: rule-match, LLM-classify, batch-move with safety contract and undo"
argument-hint: "[--dry-run] [--undo]"
allowed-tools: Agent, Read, Write, Bash, Glob, Grep, mcp__plugin_mail_outlook-bridge__*
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

1. Call `mcp__plugin_mail_outlook-bridge__outlook_auth_check`. If not ok, surface auth flow.
2. Read `~/.claude/triage/rules.yaml`. Validate against schema. On failure: report and abort.
3. Read `~/.claude/triage/locked-senders.txt`. Build lockset.

### Stage 1: rule match

4. Call `mcp__plugin_mail_outlook-bridge__outlook_list_mail` with `folder: "Inbox", top: 100, select: "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,HasAttachments,IsRead,WebLink,ConversationId"`.
5. Filter to unread (`IsRead == false`).
6. For each: invoke `agents/triage-engine`, instructing it to apply its Stage 1 specification (`${CLAUDE_PLUGIN_ROOT}/docs/triage-engine/rule-matcher.md`) against rules.yaml. Tag as `matched_by: rule | unmatched`.

### Stage 2: LLM classify unmatched

7. Call `mcp__plugin_mail_outlook-bridge__outlook_list_folders` with `recursive: true`. Build folder list (paths only).
8. For each unmatched email: invoke `agents/triage-engine`, instructing it to apply its Stage 2 specification (`${CLAUDE_PLUGIN_ROOT}/docs/triage-engine/llm-classifier.md`) with folder list + email metadata + body excerpt (fetch body via `mcp__plugin_mail_outlook-bridge__outlook_get_mail` only if not already in metadata).
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
    - Call `mcp__plugin_mail_outlook-bridge__outlook_find_folder`. If null: `outlook_create_folder` with `createParents: true, idempotent: true`.
    - Split `ids` into batches of 20.
    - For each batch: `mcp__plugin_mail_outlook-bridge__outlook_move_mail` with `continueOnError: true`.
    - Append per-message audit entries to `~/.claude/triage/audit-log.jsonl`.

### Stage 3: promotion

15. Invoke `agents/triage-engine`, instructing it to apply its Stage 3 specification (`${CLAUDE_PLUGIN_ROOT}/docs/triage-engine/promote-rule.md`). Surface any pending promotions for user confirmation.

## Safety contract

Two clauses are enforced in the MCP server. The other three are rules this command must
follow, and nothing outside this file checks them.

- **Enforced in code**: `outlook_move_mail` rejects a batch of more than 20 ids before the call is made. The MCP server validates every argument against the declared inputSchema at dispatch, so required fields, types, enums and bounds are checked server-side, not merely documented.
- **Enforced in code (by folder name)**: `outlook_move_mail` refuses destinations whose leaf is Deleted Items, Junk Email, Junk, Trash or Recoverable Items, in any spelling or casing. A raw `id:<folder-id>` destination cannot be checked this way and is not covered.
- Model compliance: no move without explicit per-session confirmation.
- Model compliance: refuse to move emails whose sender matches a `keep_locked` rule. The bridge is a stateless wrapper with no access to the lock list, so this check exists only here.
- Model compliance: audit-log every move with original folder Id (so undo can reverse).

## Undo (--undo flag)

1. Read last `triage-inbox` entry from audit-log.jsonl.
2. Group reversal moves by `from_folder`.
3. Confirm with user: "Reverse 14 moves from /triage-inbox at 2026-04-22T14:23?"
4. On confirm: batch `outlook_move_mail` calls in reverse direction.
