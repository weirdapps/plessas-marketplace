---
name: meeting-workflows
description: Anything to do with meetings either side of the meeting itself: working out what is coming up and what the user needs to know before walking in, who the attendees are and what the history with them is, and afterwards capturing what was decided and what everyone owes. Use this whenever the subject is a meeting, a call or the user's schedule, however the request is phrased, for example "who am I seeing tomorrow", "what do I need before this call", "what did we actually agree", "who owns what now", or in Greek «τι έχω αύριο», «τι πρέπει να ξέρω πριν τη σύσκεψη», «τι αποφασίσαμε τελικά», «κράτα τα action items». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for sending the follow-up email itself (use outlook-mail), for Teams chats and channels (use teams-chat), or for building the deck shown in the meeting (use presentations).
---

# Meeting workflows

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| to be ready for something coming up | `/meetings:meeting-prep` |
| to capture what came out of something that happened | `/meetings:meeting-debrief` |

Tense decides: before the meeting is prep, after it is debrief. If the user
refers to a meeting without making the tense clear, ask which they mean rather
than inferring from the calendar.

## When nothing fits

If the request is clearly about a meeting but neither row serves it, say what
this plugin can do and ask. Do not pick the nearer row.

Writing and sending the follow-up mail is mail work: hand it to outlook-mail
once the debrief has captured the content.
