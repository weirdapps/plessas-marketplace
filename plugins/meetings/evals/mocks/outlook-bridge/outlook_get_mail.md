{
  "_mock": "eval stand-in for outlook_get_mail: a fixed responder cannot select by id, so it returns every stored message with its full body instead of one. The id requested was \"{{input.id}}\". Use the entry whose \"id\" matches it, and say so plainly if none does.",
  "requested_id": "{{input.id}}",
  "messages": [
    {
      "id": "m-1001",
      "folder": "Inbox",
      "from": "anna.vidal@northgate-audit.example.com",
      "fromName": "Anna Vidal",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "evidence pack - outstanding items",
      "received": "2026-09-08T16:41:00+03:00",
      "body": "Three of the eleven controls are still missing sign-off: AC-04, AC-07 and AC-11. We need them before Friday or the interim opinion slips to the next cycle. Can you confirm today who is chasing each one?"
    },
    {
      "id": "m-1002",
      "folder": "Inbox",
      "from": "payments-ops@example.com",
      "fromName": "Payments Operations",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "settlement break 07/09 - resolved",
      "received": "2026-09-08T09:12:00+03:00",
      "body": "The 42k break on the 7th reconciled overnight against the correspondent file. Root cause was a duplicated batch, not a shortfall. No action needed, logging for the record."
    },
    {
      "id": "m-1003",
      "folder": "Inbox",
      "from": "t.marek@vendorco.example.com",
      "fromName": "Tomas Marek",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "contract renewal - revised pricing",
      "received": "2026-09-07T18:03:00+03:00",
      "body": "Attaching the revised schedule. We need your position by the 15th to hold the current rate; after that it reprices. I have assumed the volume tiers stay as agreed in June and that the SLA credit claim is still open. Tell me now if either of those is wrong."
    },
    {
      "id": "m-1004",
      "folder": "Inbox",
      "from": "noreply@travelportal.example.com",
      "fromName": "Travel Portal",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "your September itinerary",
      "received": "2026-09-07T07:00:00+03:00",
      "body": "Your booking reference is TRV-88213. No action is required."
    },
    {
      "id": "m-1005",
      "folder": "Inbox",
      "from": "l.osei@example.com",
      "fromName": "Lydia Osei",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "Re: dormant card reactivation pilot",
      "received": "2026-09-05T14:22:00+03:00",
      "body": "Happy with the approach. Do you want me to take this to the steering group or will you? I would rather we agree the widen-or-hold call at one of the weekly reviews before anyone else sees the numbers."
    },
    {
      "id": "m-1006",
      "folder": "Inbox",
      "from": "all-staff@example.com",
      "fromName": "Internal Communications",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "office closure - 12 September",
      "received": "2026-09-04T11:00:00+03:00",
      "body": "The building will be closed for scheduled maintenance on Saturday 12 September. No action is required."
    },
    {
      "id": "m-0912",
      "folder": "Archive-2026",
      "from": "t.marek@vendorco.example.com",
      "fromName": "Tomas Marek",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "Re: June session - volume tiers and the SLA credit",
      "received": "2026-06-22T10:14:00+03:00",
      "body": "Noted on both. My understanding is you are holding the tiers as they stand for the full renewal term, and that you will not contest the credit. I will proceed on that basis unless I hear otherwise."
    },
    {
      "id": "m-0911",
      "folder": "Archive-2026",
      "from": "t.marek@vendorco.example.com",
      "fromName": "Tomas Marek",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "SLA credit claim - June outage",
      "received": "2026-06-30T17:40:00+03:00",
      "body": "We are claiming 18k against the June outage. The clause is unambiguous from our side. Confirm and we will net it off the next invoice."
    },
    {
      "id": "m-0904",
      "folder": "Archive-2026",
      "from": "l.osei@example.com",
      "fromName": "Lydia Osei",
      "to": ["you@example.com"],
      "cc": [],
      "subject": "dormant card reactivation pilot - proposal",
      "received": "2026-08-20T09:05:00+03:00",
      "body": "Proposing a 12-week pilot on 40k dormant cards, targeted reactivation offer, assumed reactivation rate 8%. If it clears 8% we widen; below that we stop. Weekly review slot from 1 September."
    },
    {
      "id": "m-0801",
      "folder": "Sent Items",
      "from": "you@example.com",
      "fromName": "You",
      "to": ["t.marek@vendorco.example.com"],
      "cc": [],
      "subject": "Re: June session - volume tiers and the SLA credit",
      "received": "2026-06-19T16:55:00+03:00",
      "body": "To be precise about what I did and did not commit to in the room yesterday. I said I would come back to you on the volume tiers before the renewal date, not that they stay as they are for the term. On pricing I said our position is the current rate or better, with no commitment on term length. On the SLA credit I said we would look at the outage window and revert; I did not accept the claim."
    },
    {
      "id": "m-0802",
      "folder": "Sent Items",
      "from": "you@example.com",
      "fromName": "You",
      "to": ["t.marek@vendorco.example.com"],
      "cc": [],
      "subject": "SLA credit - our position",
      "received": "2026-07-02T12:20:00+03:00",
      "body": "Our position on the June outage is that it sits outside the credit window by roughly two hours on our monitoring, so we are not accepting the 18k as claimed. I will give you a written position on the renewal, tiers included, by mid-September."
    },
    {
      "id": "m-0803",
      "folder": "Sent Items",
      "from": "you@example.com",
      "fromName": "You",
      "to": ["l.osei@example.com"],
      "cc": [],
      "subject": "Re: dormant card reactivation pilot",
      "received": "2026-09-01T08:35:00+03:00",
      "body": "Approach is fine. Hold the steering group until we have a reactivation number we trust. We take the widen-or-hold decision at a weekly review, not by mail."
    }
  ]
}
