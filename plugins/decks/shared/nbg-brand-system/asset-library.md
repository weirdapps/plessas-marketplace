# NBG Asset Library

Comprehensive library of NBG brand assets for presentations.

**Base path:** `plugins/presentation-maker/assets/`

---

## Asset Summary

| Category | Count | Description |
|----------|-------|-------------|
| Icons | 338 | Brand icons in 20 categories |
| Illustrations | 21 | Digital app illustrations |
| Logos | 10 | App icons and wordmarks |
| Screenshots | 117 | Product UI screenshots |

---

## Icons

**Path:** `assets/icons/`
**Total:** 338 icons across 20 categories

### Categories

| Folder | Count | Best For |
|--------|-------|---------|
| `money/` | 32 | Payments, transfers, loans, wallets |
| `documents/` | 35 | Contracts, IDs, applications, files |
| `devices/` | 26 | Cards, phones, laptops, POS, ATM |
| `media/` | 29 | Browsers, scanning, printing, QR |
| `security/` | 25 | Authentication, protection, fraud |
| `people/` | 19 | Customers, advisors, groups |
| `basics/` | 30 | Actions, UI, transfers, warnings |
| `contact/` | 17 | Email, chat, phone, location |
| `system/` | 16 | Settings, cloud, dashboard |
| `time-date/` | 16 | Calendars, clocks, scheduling |
| `direction/` | 12 | Maps, pins, targets |
| `hands/` | 12 | Touch, gestures, card interactions |
| `buildings/` | 15 | Bank, home, mortgage, property |
| `graphs/` | 8 | Charts, analytics, growth |
| `shopping/` | 13 | Retail, discounts, e-commerce |
| `life-stages/` | 10 | Milestones, achievements, health |
| `travel/` | 9 | Cars, flights, international |
| `entertainment/` | 5 | Dining, lifestyle, tickets |
| `nature/` | 4 | Sustainability, environment |
| `weather/` | 5 | Insurance, protection |

### Icon Usage Rules

1. **Always tint icons to NBG brand colors**
   - Dark Teal `#003841` on light backgrounds
   - White `#FFFFFF` on dark backgrounds
   - NBG Teal `#007B85` for accent icons

2. **Never use icons without text** — always pair with a label or heading

3. **Consistent sizing per slide** — all icons same size
   - Inline/list icons: 48px
   - Feature callouts: 64-80px

4. **One icon per item** — don't stack multiple icons

5. **Never crop icons** — always preserve full image and aspect ratio

### When to Use Icons

- Infographic slides — visual anchors for each item
- Callout slides — pair with each callout
- Benefits lists — one icon per benefit, aligned left
- Section dividers — single large icon for reinforcement

**Do NOT use icons** on text-heavy slides or slides with screenshots.

See `assets/icons/INDEX.md` for complete icon reference.

### Icon Workflow Decision Guide

**When to use EXISTING icons (338 available):**
- Standard banking concepts (cards, payments, accounts)
- Common UI elements (arrows, settings, notifications)
- Status indicators (success, error, warning)
- Business categories (devices, documents, people)

**When to use Icon Designer agent:**
- Highly specific concept not in library (e.g., "AI-powered mortgage analyzer")
- Custom metaphor combining multiple concepts
- Brand-new product or feature without existing icon
- Unique illustration style requirement

**Decision Flowchart:**
```
Need an icon?
    │
    ├─> Check assets/icons/ folders first
    │       │
    │       ├─> Found suitable icon? → USE IT (apply NBG tint)
    │       │
    │       └─> No match? → Use Icon Designer agent
    │
    └─> Always prefer existing icons when possible
        (consistency > novelty)
```

---

## Illustrations

**Path:** `assets/illustrations/`
**Total:** 21 PNG + 1 PDF
**Style:** Teal line-art on transparent background, glassmorphic panels

### Available Illustrations

| Filename | What it Shows | Use When |
|----------|---------------|----------|
| `Account.png` | NBG account card (glassmorphic) | Account overview, balance display |
| `Application.png` | 5-tile app product suite | Product overview, onboarding |
| `Application Approved.png` | Document + coins + checkmark | Loan approval, success |
| `Application rejected.png` | Document + coins + red X | Rejection, error state |
| `Appointment.png` | Calendar illustration | Scheduling, appointments |
| `Approval.png` | Stacked clipboards + checkmark | General approval, verification |
| `card.png` | Contactless bank card | Card products, virtual cards |
| `Gift.png` | Gift box with badges | Rewards, offers, promotions |
| `go for more.png` | Go For More logo tile | Rewards program slides |
| `Growth.png` | Bar + line chart | Performance, KPIs, growth |
| `insurance.png` | Umbrella with rain | Insurance, protection |
| `investments.png` | 3D bar chart | Investment products, portfolio |
| `Investments check.png` | Chart + checkmark | Confirmed investment |
| `Loan application.png` | Document + coins (neutral) | Loan in progress, pending |
| `moneybox.png` | Box with euro coins | Savings, deposits |
| `notification.png` | Two envelopes | Notifications, messages |
| `Tasks.png` | Checklist + checkmark | Task completion, onboarding |
| `Teens card.png` | Card with teen avatars (portrait) | Youth products |
| `Teens card horizotal.png` | Card with teen avatars (landscape) | Youth products |
| `Transfer.png` | Two phones + IRIS | P2P transfers, IRIS payments |
| `unfriend.png` | Person with remove badge | Remove/unlink actions |

### Illustration Rules

1. **Never crop** — always show full illustration
2. **Preserve aspect ratio** — never stretch
3. **Light backgrounds only** — won't work on dark slides
4. **One per slide** — never combine multiple illustrations
5. **Use with image-left/right layouts** — as visual anchor with text
6. **Don't mix with screenshots** — different visual purposes

See `assets/illustrations/INDEX.md` for complete reference.

---

## Logos

**Path:** `assets/logos/`
**Total:** 10 files

### Available Logos

| Filename | What it Is | Use On |
|----------|-----------|--------|
| `NBG.png` | NBG emblem only (oval) | Compact placements |
| `National Bank of Greece Light.png` | Full wordmark, dark text | Light backgrounds |
| `National Bank of Greece Light dark.png` | Full wordmark, light text | Dark backgrounds |
| `Retail Mobile Banking.png` | Retail Mobile app icon | Light backgrounds |
| `Retail Mobile Banking dark.png` | Retail Mobile app icon | Dark backgrounds |
| `Business Mobile Banking.png` | Business Mobile app icon | Dark backgrounds |
| `Next.png` | Next app icon | Dark backgrounds |
| `NBG authenticator.png` | Authenticator app icon | Teal backgrounds |
| `go for more light.png` | Go For More wordmark | Light backgrounds |
| `go for more dark.png` | Go For More wordmark | Dark backgrounds |

### Logo Rules

1. **Never stretch or crop** — preserve aspect ratio
2. **Match variant to background** — light logos on light, dark on dark
3. **App icons only when relevant** — only for slides about that app
4. **Minimum size** — never below 80px on longest dimension
5. **Clearance** — leave at least half logo height as whitespace around it

See `assets/logos/INDEX.md` for complete reference.

---

## Screenshots

**Path:** `assets/screenshots/`
**Total:** 117 screenshots across 5 products

### Product Folders

| Folder | Product | Type |
|--------|---------|------|
| `retail-mobile/` | NBG Retail Mobile Banking App | Mobile (iOS/Android) |
| `retail-internet/` | NBG Retail Internet Banking | Web |
| `next-app/` | NBG Next App | Mobile |
| `business-mobile/` | NBG Business Mobile Banking | Mobile |
| `business-internet/` | NBG Business Internet Banking | Web |

### Screenshot Categories (retail-mobile example)

- `loans/` — Loan products and applications
- `cards/` — Card views and management
- `card-management/` — Card settings and controls
- `accounts/` — Account views and details
- `investments/` — Investment products
- `moneybox/` — Savings features
- `iris/` — IRIS payment flows
- `subscriptions/` — Subscription management
- `profile/` — User profile screens
- `notifications/` — Notification screens
- `onboarding/` — New user flows
- `sole-proprietorship/` — Business features

### Screenshot Rules

1. **Read the INDEX.md** in each product folder before selecting
2. **Match product to context** — if discussing Retail Mobile, use only retail-mobile screenshots
3. **One product per slide** — never mix products
4. **If no relevant screenshot exists**, use solid NBG Teal fill as placeholder

### Aspect Ratio Rules (Critical)

**Never stretch screenshots.** Strategy:
1. **Fit whole screenshot** inside placeholder, centered (preferred)
2. **Crop only as fallback** — if fit looks bad

**NEVER crop these products — always fit:**
- `retail-mobile` (mobile UI would be cut off)
- `next-app` (mobile UI would be cut off)
- `business-mobile` (mobile UI would be cut off)

Crop allowed only for web products (`retail-internet`, `business-internet`) when coverage < 60%.

See `assets/screenshots/*/INDEX.md` for complete reference per product.

---

## Asset Selection Workflow

1. **Identify slide purpose** — what are you communicating?
2. **Choose asset type**:
   - Abstract concept → **Illustration**
   - Specific product feature → **Screenshot**
   - Supporting visual for text → **Icon**
   - Brand presence → **Logo**
3. **Read the INDEX.md** for that asset category
4. **Select specific asset** that matches content
5. **Insert with correct sizing** — preserve aspect ratio

---

## Quick Reference Table

| Need | Asset Type | Path |
|------|-----------|------|
| Visual for loan approval | Illustration | `illustrations/Application Approved.png` |
| Card product visual | Illustration | `illustrations/card.png` |
| Payment flow icon | Icon | `icons/money/Payment.png` |
| Security feature icon | Icon | `icons/security/Shield.png` |
| Mobile app screenshot | Screenshot | `screenshots/retail-mobile/*.png` |
| Next app feature | Screenshot | `screenshots/next-app/*.png` |
| NBG branding | Logo | `logos/National Bank of Greece Light.png` |
