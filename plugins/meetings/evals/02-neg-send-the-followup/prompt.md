---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write, mcp__outlook-bridge__outlook_auth_check, mcp__outlook-bridge__outlook_list_calendar, mcp__outlook-bridge__outlook_get_event, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_get_mail, mcp__outlook-bridge__outlook_reply, mcp__outlook-bridge__outlook_reply_all, mcp__outlook-bridge__outlook_send_mail]
runs: 3
tags: [negative, meetings]
---

Send everyone who was in the room this morning a note with what we agreed and who
owns what. I already have the notes, they just need to go out.
