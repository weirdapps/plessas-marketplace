# NBG Logos Library — Index

**Base path:** `plugins/decks/assets/logos/`
**Total:** 10 logos
**Format:** PNG (some with transparent background, some with solid app icon background)

---

## Logo Directory

### NBG Brand Logos

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `NBG.png` | NBG emblem only — the oval building icon in teal/cyan, no text | Transparent | Compact spaces, app icons, watermarks, decorative use alongside text |
| `National Bank of Greece Light.png` | Full wordmark — "NATIONAL BANK OF GREECE" in Dark Navy with teal emblem | Transparent (light version) | Light slide backgrounds, covers, title slides |
| `National Bank of Greece Light dark.png` | Full wordmark — "NATIONAL BANK OF GREECE" in near-white/cream with teal emblem | Transparent (dark version) | Dark slide backgrounds (navy, teal), dark divider slides, back cover |

### App Logos — Mobile

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `Retail Mobile Banking.png` | Retail Mobile Banking app icon — teal oval emblem on light/white rounded square | Light app icon bg | Slides about the Retail Mobile Banking app on light backgrounds |
| `Retail Mobile Banking dark.png` | Retail Mobile Banking app icon — teal oval emblem on Dark Navy rounded square | Dark Navy | Slides about the Retail Mobile Banking app on dark backgrounds |
| `Business Mobile Banking.png` | Business Mobile Banking app icon — overlapping blue/cyan/green ovals on Dark Navy rounded square | Dark Navy | Slides about the Business Mobile Banking app |
| `Next.png` | Next app icon — cream and cyan overlapping ovals on Dark Navy rounded square | Dark Navy | Slides about the Next app (next-generation banking) |
| `NBG authenticator.png` | NBG Authenticator app icon — abstract building in white lines on teal square | Teal | Slides about security, authentication, 2FA, the NBG Authenticator app |

### Rewards Program Logos

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `go for more light.png` | "GO FOR MORE" wordmark with pink double-arrow motif — Dark Navy text | Transparent (light version) | Light backgrounds; slides about Go For More rewards program |
| `go for more dark.png` | "GO FOR MORE" wordmark with pink double-arrow motif — cream/off-white text | Transparent (dark version) | Dark backgrounds; slides about Go For More on dark slides |

---

## Rules for Using Logos

1. **Never stretch or crop logos** — always preserve aspect ratio exactly. Scale by fixing one dimension and calculating the other proportionally.
2. **Always match logo variant to background** — use Light versions on light backgrounds, Dark/white versions on dark backgrounds. Never place a dark-text logo on a dark background.
3. **Never place app icon logos as decorative elements** — app icons (Retail Mobile, Business Mobile, Next, Authenticator) are only used when the slide content is specifically about that app.
4. **NBG wordmark placement** — the full "National Bank of Greece" wordmark is for covers, title slides, and where the bank brand needs prominent identity. The `NBG.png` emblem-only is for compact placements.
5. **Go For More logo** — only use when the slide content relates to the rewards/loyalty program. Never use as a generic decorative element.
6. **Minimum size** — never display logos smaller than 80px on their longest dimension; they become illegible.
7. **Clearance** — always leave at least half the logo's height as whitespace around it on all sides.

## How to Insert a Logo

```python
from pptx.util import Emu
from PIL import Image

def add_logo(slide, logo_path, left, top, target_width_px=None, target_height_px=None):
    """
    Insert a logo preserving exact aspect ratio. Never crops, never stretches.
    Provide either target_width_px OR target_height_px — the other dimension is calculated.
    """
    img = Image.open(logo_path)
    img_w, img_h = img.size

    if target_width_px:
        final_w_px = target_width_px
        final_h_px = int(target_width_px * img_h / img_w)
    elif target_height_px:
        final_h_px = target_height_px
        final_w_px = int(target_height_px * img_w / img_h)
    else:
        raise ValueError("Provide either target_width_px or target_height_px")

    EMU_PER_PX = 9144
    slide.shapes.add_picture(
        logo_path,
        left, top,
        Emu(final_w_px * EMU_PER_PX),
        Emu(final_h_px * EMU_PER_PX)
    )

# Example: place Retail Mobile Banking app icon at 80x80px
add_logo(
    slide,
    "plugins/decks/assets/logos/Retail Mobile Banking.png",
    left=Emu(500000), top=Emu(500000),
    target_width_px=80
)
```
