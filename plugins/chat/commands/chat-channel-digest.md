---
description: "Digest a Microsoft Teams channel — executive summary of recent activity across threads."
argument-hint: "[team_id] [channel_id] [hours]"
allowed-tools: Read, Write, Bash, mcp__teams-bridge__teams_auth_check, mcp__teams-bridge__teams_list_teams, mcp__teams-bridge__teams_list_channels, mcp__teams-bridge__teams_list_messages, mcp__teams-bridge__teams_resolve_mri
---

# Teams Channel Digest

Produce an executive digest of recent activity in a Microsoft Teams channel.

## Workflow

1. **If no team_id**: list teams via `mcp__teams-bridge__teams_list_teams`, let user pick.

2. **If no channel_id**: list channels via `mcp__teams-bridge__teams_list_channels` with the team_id, let user pick.

3. **Fetch channel messages** via `mcp__teams-bridge__teams_list_messages` with team_id + channel_id, `top: 50`, and `since` (computed from hours arg, default 48h).

4. **Resolve participants** for MRI-format senders.

5. **Produce digest**:
   - **Channel**: [team name] / [channel name]
   - **Period**: last N hours, M messages from K participants
   - **Top threads** (grouped by topic if discernible):
     - Thread 1: [topic] — [key point] — [who participated]
     - Thread 2: ...
   - **Decisions & action items** (if any)
   - **Highlights**: anything urgent, escalated, or requiring attention

## Output Format

Executive-style: a busy manager should be able to read this in 60 seconds and know whether they need to engage with the channel. Keep under 400 words.

## Notes

- Channel message sends are NOT supported (scope limitation). This command is read-only.
- If the channel is quiet (< 3 messages in the window), say so explicitly.
