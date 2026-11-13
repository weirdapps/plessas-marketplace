---
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, mcp__outlook-bridge__outlook_auth_check, mcp__outlook-bridge__outlook_list_calendar, mcp__outlook-bridge__outlook_get_event, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_get_mail, mcp__outlook-bridge__outlook_reply, mcp__outlook-bridge__outlook_reply_all, mcp__outlook-bridge__outlook_send_mail]
append_system_prompt: "Today is Wednesday 9 September 2026, Europe/Athens time. The user's calendar and mailbox are as of today."
runs: 3
tags: [routing, meetings]
---

I have the vendor in at nine tomorrow and I cannot remember where we left it last
time. What do I need in my head before I walk in?
