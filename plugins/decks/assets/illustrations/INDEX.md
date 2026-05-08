# NBG Illustrations Library — Index

**Base path:** `plugins/presentation-maker/assets/illustrations/`
**Total:** 22 illustrations (21 PNG + 1 PDF)
**Format:** PNG with transparent background (RGBA), ~1125px wide
**Style:** Teal line-art on transparent/light background — consistent with NBG digital apps visual language

---

## Illustration Directory

| Filename | Dimensions | What it shows | Use when |
|----------|-----------|---------------|----------|
| `Account.png` | 1125×534 | Glassmorphic NBG account card with balance (masked) and NBG emblem | Account overview, balance display, account management slides |
| `Application.png` | 1125×696 | 5 floating app-style tiles: calculator, coins+stack, credit card, bar chart, shield | Digital banking product suite, onboarding, feature overview |
| `Application Approved.png` | 1125×717 | Loan/financial document with coin stack + teal checkmark badge | Loan approval, successful application, positive outcome |
| `Application rejected.png` | 1125×717 | Same document with coin stack + red X badge | Loan rejection, failed application, error state |
| `Appointment.png` | 1125×552 | Flat calendar illustration, slightly tilted | Scheduling, appointments, branch visits, calendar features |
| `Approval.png` | 1125×540 | Stacked clipboard cards with teal checkmark | General approval, verification, sign-off, completed process |
| `card.png` | 1125×666 | Single contactless bank card, vertical, glassmorphic teal outline | Card products, card issuance, virtual/physical card features |
| `Gift.png` | 1125×906 | Gift box on glassmorphic tile with teal check + red X badges | Rewards, offers, promotions, bonus eligibility, accept/decline flows |
| `go for more.png` | 1125×534 | "GO FOR MORE" logo inside a glassmorphic rounded-square tile | Go For More rewards program feature slides |
| `Growth.png` | 1125×594 | Bar chart + rising line chart with upward arrow | Business growth, portfolio performance, increasing metrics, KPIs |
| `insurance.png` | 1125×660 | Open umbrella with rain falling — full-width landscape | Insurance products, protection, coverage, risk management |
| `investments.png` | 1125×552 | 3D-style bar chart with rising bars, glassmorphic render | Investment products, portfolio overview, market data |
| `Investments check.png` | 528×504 | Line+bar chart with prominent teal checkmark badge | Confirmed investment, portfolio verified, investment completion |
| `Loan application.png` | 1125×717 | Financial document with €€€ header and coin stack (no status badge) | Loan application in progress, pending review, apply for loan |
| `moneybox.png` | 1125×648 | Open cardboard box with euro coins floating above it | Savings, deposits, money collection, piggy bank concept |
| `notification.png` | 1125×630 | Two overlapping envelopes, glassmorphic teal | Notifications, email alerts, messages, push notifications |
| `Tasks.png` | 1125×906 | Checklist card with 3 checked rows + large teal checkmark badge | Task completion, to-do lists, onboarding steps, compliance checklist |
| `Teens card.png` | 1125×906 | Vertical bank card with 2 teen avatar circles (boy + girl) | Teens/youth card product, family banking, under-18 accounts |
| `Teens card horizotal.png` | 1125×696 | Horizontal bank card with same 2 teen avatars | Same as above — use when landscape orientation is needed |
| `Transfer.png` | 1125×992 | Two phones exchanging euro symbol with arrows, IRIS logo visible | P2P transfers, IRIS payments, send/receive money, mobile payments |
| `unfriend.png` | 1125×630 | Person silhouette with minus/remove badge — red outline | Remove beneficiary, unlink account, delete contact, negative action |
| `Wallet virtual card.pdf` | PDF | Virtual wallet card illustration | Virtual card, digital wallet — use only in PDF-compatible contexts |

---

## Style Notes

All illustrations share the same visual language:
- **Teal line-art** (`RGB(4, 122, 133)`) on transparent or very light background
- **Glassmorphic panels** — frosted glass-effect cards and tiles
- **Soft depth** — subtle shadows and gradients give 3D feel without being heavy
- **Exception:** `unfriend.png` and `Application rejected.png` use **red** to signal negative/error states

## Rules for Using Illustrations

1. **Never crop illustrations** — always show the full image, preserving aspect ratio
2. **Always preserve aspect ratio** — fix one dimension, calculate the other from actual PNG dimensions
3. **Light backgrounds only** — these illustrations are designed for white or very light backgrounds (`RGB(245,249,246)`). They will not read well on dark navy or teal backgrounds
4. **One illustration per slide** — never combine multiple illustrations on the same slide
5. **Use with image-left or image-right layouts** (slides 5–8 in the template) — illustrations work best as the visual anchor alongside explanatory text
6. **Do not use illustrations on the same slide as screenshots** — they serve different purposes and clash visually
7. **Status variants are a pair** — `Application Approved.png` and `Application rejected.png` are designed to be used in before/after or comparison contexts; `Loan application.png` is the neutral "pending" state of the same scene
8. **Teens card variants** — use `Teens card.png` (portrait) for portrait-dominant layouts and `Teens card horizotal.png` for landscape-dominant layouts; never use both on the same slide

## How to Insert an Illustration

```python
from pptx.util import Emu
from PIL import Image

def add_illustration(slide, illustration_path, left, top, target_width_emu=None, target_height_emu=None):
    """
    Insert an illustration preserving exact aspect ratio. Never crops, never stretches.
    Provide either target_width_emu OR target_height_emu — the other is calculated.
    """
    img = Image.open(illustration_path)
    img_w, img_h = img.size

    if target_width_emu:
        final_w = target_width_emu
        final_h = int(target_width_emu * img_h / img_w)
    elif target_height_emu:
        final_h = target_height_emu
        final_w = int(target_height_emu * img_w / img_h)
    else:
        raise ValueError("Provide target_width_emu or target_height_emu")

    slide.shapes.add_picture(illustration_path, left, top, Emu(final_w), Emu(final_h))

# Example: place Transfer illustration in the right half of a slide
add_illustration(
    slide,
    "plugins/presentation-maker/assets/illustrations/Transfer.png",
    left=Emu(6400000),
    top=Emu(1200000),
    target_width_emu=4800000
)
```
