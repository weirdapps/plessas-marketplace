# NBG Illustrations Library: Index

**Base path:** `${CLAUDE_PLUGIN_ROOT}/assets/illustrations/` (a deck spec writes `illustrations/<file>`)
**Total:** 22 illustrations (21 PNG + 1 PDF), plus a 9-piece SVG splash set in `splash/`
**Format:** PNG with transparent background (RGBA), 800px wide (heights in the table)
**Style:** Teal line-art on transparent/light background, consistent with NBG digital apps visual language

---

## Illustration Directory

| Filename | Dimensions | What it shows | Use when |
|----------|-----------|---------------|----------|
| `Account.png` | 800×380 | Glassmorphic NBG account card with balance (masked) and NBG emblem | Account overview, balance display, account management slides |
| `Application.png` | 800×495 | 5 floating app-style tiles: calculator, coins+stack, credit card, bar chart, shield | Digital banking product suite, onboarding, feature overview |
| `Application_Approved.png` | 800×510 | Loan/financial document with coin stack + teal checkmark badge | Loan approval, successful application, positive outcome |
| `Application_rejected.png` | 800×510 | Same document with coin stack + red X badge | Loan rejection, failed application, error state |
| `Appointment.png` | 800×393 | Flat calendar illustration, slightly tilted | Scheduling, appointments, branch visits, calendar features |
| `Approval.png` | 800×384 | Stacked clipboard cards with teal checkmark | General approval, verification, sign-off, completed process |
| `card.png` | 800×474 | Single contactless bank card, vertical, glassmorphic teal outline | Card products, card issuance, virtual/physical card features |
| `Gift.png` | 800×644 | Gift box on glassmorphic tile with teal check + red X badges | Rewards, offers, promotions, bonus eligibility, accept/decline flows |
| `go_for_more.png` | 800×380 | "GO FOR MORE" logo inside a glassmorphic rounded-square tile | Go For More rewards program feature slides |
| `Growth.png` | 800×420 | Bar chart + rising line chart with upward arrow | Business growth, portfolio performance, increasing metrics, KPIs |
| `insurance.png` | 800×469 | Open umbrella with rain falling, full-width landscape | Insurance products, protection, coverage, risk management |
| `investments.png` | 800×393 | 3D-style bar chart with rising bars, glassmorphic render | Investment products, portfolio overview, market data |
| `Investments_check.png` | 800×764 | Line+bar chart with prominent teal checkmark badge | Confirmed investment, portfolio verified, investment completion |
| `Loan_application.png` | 800×510 | Financial document with €€€ header and coin stack (no status badge) | Loan application in progress, pending review, apply for loan |
| `moneybox.png` | 800×461 | Open cardboard box with euro coins floating above it | Savings, deposits, money collection, piggy bank concept |
| `notification.png` | 800×448 | Two overlapping envelopes, glassmorphic teal | Notifications, email alerts, messages, push notifications |
| `Tasks.png` | 800×644 | Checklist card with 3 checked rows + large teal checkmark badge | Task completion, to-do lists, onboarding steps, compliance checklist |
| `Teens_card.png` | 800×644 | Vertical bank card with 2 teen avatar circles (boy + girl) | Teens/youth card product, family banking, under-18 accounts |
| `Teens_card_horizotal.png` | 800×495 | Horizontal bank card with same 2 teen avatars | Same as above; use when landscape orientation is needed |
| `Transfer.png` | 800×705 | Two phones exchanging euro symbol with arrows, IRIS logo visible | P2P transfers, IRIS payments, send/receive money, mobile payments |
| `unfriend.png` | 800×448 | Person silhouette with minus/remove badge, red outline | Remove beneficiary, unlink account, delete contact, negative action |
| `Wallet_virtual_card.pdf` | PDF | Virtual wallet card illustration | Virtual card, digital wallet; use only in PDF-compatible contexts |

---

## Style Notes

All illustrations share the same visual language:

- **Teal line-art** (`RGB(4, 122, 133)`) on transparent or very light background
- **Glassmorphic panels**: frosted glass-effect cards and tiles
- **Soft depth**: subtle shadows and gradients give 3D feel without being heavy
- **Exception:** `unfriend.png` and `Application_rejected.png` use **red** to signal negative/error states

## Rules for Using Illustrations

1. **Never crop illustrations**: always show the full image, preserving aspect ratio
2. **Always preserve aspect ratio**: fix one dimension, calculate the other from actual PNG dimensions
3. **Light backgrounds only**: these illustrations are designed for white or very light backgrounds (`#FFFFFF`, `#F5F8F6`). They will not read well on dark navy or teal backgrounds
4. **One illustration per slide**: never combine multiple illustrations on the same slide
5. **Use beside explanatory text**: an `image` slide, or a `two_column` slide with an image column, where the illustration is the visual anchor
6. **Do not use illustrations on the same slide as screenshots**: they serve different purposes and clash visually
7. **Status variants are a pair**: `Application_Approved.png` and `Application_rejected.png` are designed to be used in before/after or comparison contexts; `Loan_application.png` is the neutral "pending" state of the same scene
8. **Teens card variants**: use `Teens_card.png` (portrait) for portrait-dominant layouts and `Teens_card_horizotal.png` for landscape-dominant layouts; never use both on the same slide

## Splash Set (SVG)

Internet Banking promo-style illustrations in `splash/`, rasterised by the builder when placed:

| Filename | What it shows |
|----------|---------------|
| `splash/auto_insurance.svg` | Car insurance |
| `splash/cyber_protection.svg` | Cyber protection |
| `splash/express_loan.svg` | Express loan |
| `splash/health_insurance.svg` | Health insurance |
| `splash/investments.svg` | Investments |
| `splash/maintenance.svg` | Maintenance |
| `splash/moneybox.svg` | Savings |
| `splash/p2p.svg` | Person-to-person payments |
| `splash/remote_service.svg` | Remote service |

## How to Insert an Illustration

Through the deck spec, never with hand-written python-pptx: `nbg_build.py` places the file, keeps
its aspect ratio (`fit: contain`) and writes the alt text.

```yaml
- type: image
  id: S05
  content:
    title: "Payments move from the branch to the phone"
  image:
    path: illustrations/Transfer.png   # relative paths resolve against the spec, then assets/
    alt_text: "Two phones exchanging a payment over IRIS"
```

For an illustration beside text, use a `two_column` slide with `{kind: image, image: {path: ...,
alt_text: ...}}` as one column.
