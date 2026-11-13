---
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, mcp__outlook-bridge__outlook_auth_check, mcp__outlook-bridge__outlook_list_calendar, mcp__outlook-bridge__outlook_get_event, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_get_mail, mcp__outlook-bridge__outlook_find_folder, mcp__outlook-bridge__outlook_list_folders, mcp__outlook-bridge__outlook_reply, mcp__outlook-bridge__outlook_reply_all, mcp__outlook-bridge__outlook_send_mail]
append_system_prompt: "Today is Wednesday 9 September 2026, Europe/Athens time. The user's calendar and mailbox are as of today."
runs: 1
tags: [recall, meetings]
---

Marek is in tomorrow morning and he will open by telling me what I promised him
last quarter. Before I walk in I want the trail of what I actually put in
writing to him, in my own words, not his summary of them. Go and find it.
