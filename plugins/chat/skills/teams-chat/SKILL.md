---
name: teams-chat
description: Anything to do with the user's Microsoft Teams conversations: seeing what came in, catching up on a thread or a channel, working out who is waiting on a response, and replying. Use this whenever a request concerns Teams, chats, channels or direct messages, however it is phrased, for example "what did I miss", "is anyone waiting on me", "catch me up on the project channel", "tell them I am running late", or in Greek «τι έγινε όσο έλειπα», «με έχει ψάξει κανείς», «τι λέει το κανάλι», «πες τους ότι θα αργήσω». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for email (use outlook-mail), for preparing or debriefing a meeting (use meeting-workflows), or for building presentations or documents.
---

# Microsoft Teams chat

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| see what came in and what is unread | `/chat:chat-inbox` |
| catch up on one conversation | `/chat:chat-summarize` |
| catch up on a channel over a period | `/chat:chat-channel-digest` |
| answer someone | `/chat:chat-reply` |
| fix Teams access or authentication | `/chat:chat-doctor`, `/chat:auth-setup` |

## When nothing fits

`/chat:chat-reply` sends the message. Never route to it on inference.

Reach it only when the request unambiguously asks to answer someone and the
target conversation is unambiguous. If either is unclear, run
`/chat:chat-inbox` or `/chat:chat-summarize` so the user can see the context
and say what they want, then ask. Showing the user their messages is always a
safe wrong answer; sending on a guess is not.
