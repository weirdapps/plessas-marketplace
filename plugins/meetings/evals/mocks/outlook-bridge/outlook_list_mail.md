{
  "_mock": "eval stand-in for outlook_list_mail: it ignores folder, folderId, since, until, top, all, max and select, and always returns every stored message. Each message carries its own \"folder\", so filter client-side. Bodies are not in this listing; outlook_get_mail returns them.",
  "folders": [
    "Inbox",
    "Archive-2026",
    "Sent Items"
  ],
  "total": 12,
  "messages": [
    {
      "id": "m-1001",
      "folder": "Inbox",
      "from": "anna.vidal@northgate-audit.example.com",
      "fromName": "Anna Vidal",
      "to": ["you@example.com"],
      "subject": "evidence pack - outstanding items",
      "received": "2026-09-08T16:41:00+03:00",
      "unread": true,
      "preview": "Three of the eleven controls are still missing sign-off. We need them before Friday or the interim opinion slips."
    },
    {
      "id": "m-1002",
      "folder": "Inbox",
      "from": "payments-ops@example.com",
      "fromName": "Payments Operations",
      "to": ["you@example.com"],
      "subject": "settlement break 07/09 - resolved",
      "received": "2026-09-08T09:12:00+03:00",
      "unread": true,
      "preview": "The 42k break on the 7th reconciled overnight. No action needed, logging for the record."
    },
    {
      "id": "m-1003",
      "folder": "Inbox",
      "from": "t.marek@vendorco.example.com",
      "fromName": "Tomas Marek",
      "to": ["you@example.com"],
      "subject": "contract renewal - revised pricing",
      "received": "2026-09-07T18:03:00+03:00",
      "unread": true,
      "preview": "Attaching the revised schedule. We need your position by the 15th to hold the current rate."
    },
    {
      "id": "m-1004",
      "folder": "Inbox",
      "from": "noreply@travelportal.example.com",
      "fromName": "Travel Portal",
      "to": ["you@example.com"],
      "subject": "your September itinerary",
      "received": "2026-09-07T07:00:00+03:00",
      "unread": true,
      "preview": "Your booking reference is TRV-88213."
    },
    {
      "id": "m-1005",
      "folder": "Inbox",
      "from": "l.osei@example.com",
      "fromName": "Lydia Osei",
      "to": ["you@example.com"],
      "subject": "Re: dormant card reactivation pilot",
      "received": "2026-09-05T14:22:00+03:00",
      "unread": false,
      "preview": "Happy with the approach. Do you want me to take this to the steering group or will you?"
    },
    {
      "id": "m-1006",
      "folder": "Inbox",
      "from": "all-staff@example.com",
      "fromName": "Internal Communications",
      "to": ["you@example.com"],
      "subject": "office closure - 12 September",
      "received": "2026-09-04T11:00:00+03:00",
      "unread": false,
      "preview": "The building will be closed for scheduled maintenance."
    },
    {
      "id": "m-0912",
      "folder": "Archive-2026",
      "from": "t.marek@vendorco.example.com",
      "fromName": "Tomas Marek",
      "to": ["you@example.com"],
      "subject": "Re: June session - volume tiers and the SLA credit",
      "received": "2026-06-22T10:14:00+03:00",
      "unread": false,
      "preview": "Noted on both. My understanding is you are holding the tiers as they stand for the full renewal term."
    },
    {
      "id": "m-0911",
      "folder": "Archive-2026",
      "from": "t.marek@vendorco.example.com",
      "fromName": "Tomas Marek",
      "to": ["you@example.com"],
      "subject": "SLA credit claim - June outage",
      "received": "2026-06-30T17:40:00+03:00",
      "unread": false,
      "preview": "We are claiming 18k against the June outage. The clause is unambiguous from our side."
    },
    {
      "id": "m-0904",
      "folder": "Archive-2026",
      "from": "l.osei@example.com",
      "fromName": "Lydia Osei",
      "to": ["you@example.com"],
      "subject": "dormant card reactivation pilot - proposal",
      "received": "2026-08-20T09:05:00+03:00",
      "unread": false,
      "preview": "Proposing a 12-week pilot on 40k dormant cards. Assumed reactivation 8%."
    },
    {
      "id": "m-0801",
      "folder": "Sent Items",
      "from": "you@example.com",
      "fromName": "You",
      "to": ["t.marek@vendorco.example.com"],
      "subject": "Re: June session - volume tiers and the SLA credit",
      "received": "2026-06-19T16:55:00+03:00",
      "unread": false,
      "preview": "To be precise about what I did and did not commit to in the room yesterday."
    },
    {
      "id": "m-0802",
      "folder": "Sent Items",
      "from": "you@example.com",
      "fromName": "You",
      "to": ["t.marek@vendorco.example.com"],
      "subject": "SLA credit - our position",
      "received": "2026-07-02T12:20:00+03:00",
      "unread": false,
      "preview": "Our position on the June outage, and when you will have the renewal answer."
    },
    {
      "id": "m-0803",
      "folder": "Sent Items",
      "from": "you@example.com",
      "fromName": "You",
      "to": ["l.osei@example.com"],
      "subject": "Re: dormant card reactivation pilot",
      "received": "2026-09-01T08:35:00+03:00",
      "unread": false,
      "preview": "Approach is fine. Hold the steering group until we have the reactivation number."
    }
  ]
}
