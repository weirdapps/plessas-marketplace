---
description: "Digest a Microsoft Teams channel: executive summary of recent activity across threads."
argument-hint: "[team_id] [channel_id] [hours]"
allowed-tools: Read, Write, Bash, mcp__plugin_chat_teams-bridge__teams_auth_check, mcp__plugin_chat_teams-bridge__teams_list_teams, mcp__plugin_chat_teams-bridge__teams_list_channels, mcp__plugin_chat_teams-bridge__teams_list_messages, mcp__plugin_chat_teams-bridge__teams_resolve_mri
---

# Teams Channel Digest

Produce an executive digest of recent activity in a Microsoft Teams channel.

## Workflow

1. **If no team_id**: list teams via `mcp__plugin_chat_teams-bridge__teams_list_teams`, let user pick.

2. **If no channel_id**: list channels via `mcp__plugin_chat_teams-bridge__teams_list_channels` with the team_id, let user pick.

3. **Fetch channel messages** via `mcp__plugin_chat_teams-bridge__teams_list_messages` with team_id + channel_id and `top` (default 50). The tool has no server-side time filter, so fetch by count and, when the user asks for a time window, filter the returned messages client-side by timestamp.

4. **Resolve participants** for MRI-format senders.

5. **Produce digest**:
   - **Channel**: [team name] / [channel name]
   - **Period**: the actual timestamp range of the messages retrieved, M messages from K participants
   - **Top threads** (grouped by topic if discernible):
     - Thread 1: [topic], [key point], [who participated]
     - Thread 2: ...
   - **Decisions & action items** (if any)
   - **Highlights**: anything urgent, escalated, or requiring attention

## Output Format

Executive-style: a busy manager should be able to read this in 60 seconds and know whether they need to engage with the channel. Keep under 400 words.

## Notes

- Channel message sends are NOT supported (scope limitation). This command is read-only.
- If the channel is quiet (< 3 messages in the window), say so explicitly.
