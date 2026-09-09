---
name: meeting-workflows
description: "Anything to do with meetings either side of the meeting itself: working out what is coming up and what the user needs to know before walking in, who the attendees are and what the history with them is, including digging out the record of what was actually said to them before, and afterwards capturing what was decided and what everyone owes and filing that record somewhere structured and findable. Use this whenever the subject is a meeting, a call or the user's schedule, equally when the user simply recounts how one ended and wants it written down rather than asking a question about it, and equally when a meeting is named with no clear tense at all, however the request is phrased, for example \"who am I seeing tomorrow\", \"what do I need before this call\", \"go and find what I actually promised them\", \"what did we actually agree\", \"who owns what now\", \"put that somewhere I can find it\", \"log where this landed, structured\", \"deal with the session on X\", or in Greek «τι έχω αύριο», «τι πρέπει να ξέρω πριν τη σύσκεψη», «βρες τι του είχα υποσχεθεί», «τι αποφασίσαμε τελικά», «κράτα τα action items», «κράτα το κάπου δομημένα», «τακτοποίησε τη σύσκεψη με τον Χ». Three shapes that are easy to mistake for other work and are not: a request that dictates outcomes and asks only for them to be saved is this skill and not a plain file write, because the house structure is the point; a request to go and retrieve what was said to someone before you next see them is this skill and not a generic search, because it is preparation; and a request that names a meeting without saying which side of it you are on is this skill above all, because asking which is this skill's job and nothing else knows to ask. These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for sending the follow-up email itself (use outlook-mail), for Teams chats and channels (use teams-chat), or for building the deck shown in the meeting (use presentations)."
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
