# NBG Logos Library: Index

**Base path:** `${CLAUDE_PLUGIN_ROOT}/assets/logos/` (a deck spec writes `logos/<file>`)
**Total:** 10 PNG logos, plus 3 SVG reference boards
**Format:** PNG (some with transparent background, some with solid app icon background)

---

## Logo Directory

### NBG Brand Logos

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `NBG.png` | NBG emblem only, the oval building icon in teal/cyan, no text | Transparent | Compact spaces, app icons, watermarks, decorative use alongside text |
| `National_Bank_of_Greece_Light.png` | English wordmark, "NATIONAL BANK OF GREECE" in Dark Navy with teal emblem | Transparent (light version) | Never on a slide (Standard #10). English-language material outside decks, on light backgrounds |
| `National_Bank_of_Greece_Light_dark.png` | English wordmark, "NATIONAL BANK OF GREECE" in near-white/cream with teal emblem | Transparent (dark version) | Never on a slide, keynote mode included (it uses a white Greek wordmark). English-language material outside decks, on dark backgrounds |

### App Logos: Mobile

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `Retail_Mobile_Banking.png` | Retail Mobile Banking app icon, teal oval emblem on light/white rounded square | Light app icon bg | Slides about the Retail Mobile Banking app on light backgrounds |
| `Retail_Mobile_Banking_dark.png` | Retail Mobile Banking app icon, teal oval emblem on Dark Navy rounded square | Dark Navy | Slides about the Retail Mobile Banking app on dark backgrounds |
| `Business_Mobile_Banking.png` | Business Mobile Banking app icon, overlapping blue/cyan/green ovals on Dark Navy rounded square | Dark Navy | Slides about the Business Mobile Banking app |
| `Next.png` | Next app icon, cream and cyan overlapping ovals on Dark Navy rounded square | Dark Navy | Slides about the Next app (next-generation banking) |
| `NBG_authenticator.png` | NBG Authenticator app icon, abstract building in white lines on teal square | Teal | Slides about security, authentication, 2FA, the NBG Authenticator app |

### Rewards Program Logos

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `go_for_more_light.png` | "GO FOR MORE" wordmark with pink double-arrow motif, Dark Navy text | Transparent (light version) | Light backgrounds; slides about Go For More rewards program |
| `go_for_more_dark.png` | "GO FOR MORE" wordmark with pink double-arrow motif, cream/off-white text | Transparent (dark version) | Dark backgrounds; slides about Go For More on dark slides |

### Reference Boards (SVG)

Pillar design-system sheets that show each logo family and its variants. They are for looking up
which variant exists, not for placing on a slide: place the PNGs above.

| Filename | Description | Background | Use when |
|----------|-------------|------------|----------|
| `app.svg` | "App Logos" board: the NBG app icons side by side | White sheet | Checking which app icon variants exist |
| `go4more.svg` | "Go4more Logos" board: Go For More wordmarks, standard and premium, light and dark | White sheet | Checking Go For More variants |
| `nbg.svg` | "NBG Logos" board: favicon, mobile logo, horizontal Greek and English wordmarks | White sheet | Checking NBG logo variants; on slides the Greek wordmark is always the plugin's nbg-logo-gr.png, one folder up (brand-system/README.md, Logo Assets) |

---

## Rules for Using Logos

1. **Never stretch or crop logos**: always preserve aspect ratio exactly. Scale by fixing one dimension and calculating the other proportionally.
2. **Always match logo variant to background**: use Light versions on light backgrounds, Dark/white versions on dark backgrounds. Never place a dark-text logo on a dark background.
3. **Never place app icon logos as decorative elements**: app icons (Retail Mobile, Business Mobile, Next, Authenticator) are only used when the slide content is specifically about that app.
4. **NBG wordmark placement**: on a slide the builder places the Greek wordmark itself, at the small or large logo position (brand-system/README.md, Logo Assets). Never add an English wordmark to a slide: the validator fails it (Standard #10). The `NBG.png` emblem-only is for compact placements.
5. **Go For More logo**: only use when the slide content relates to the rewards/loyalty program. Never use as a generic decorative element.
6. **Minimum size**: never display logos smaller than 80px on their longest dimension; they become illegible.
7. **Clearance**: always leave at least half the logo's height as whitespace around it on all sides.

## How to Insert a Logo

Through the deck spec, never with hand-written python-pptx: `nbg_build.py` embeds the file and
writes the alt text. Set the box to the logo's own aspect ratio (Standard #4): read the PNG's pixel
size, fix one dimension, derive the other.

```yaml
- type: custom
  id: S07
  content:
    title: "Retail Mobile Banking leads daily use"
  elements:
    - kind: image
      path: logos/Retail_Mobile_Banking.png   # relative paths resolve against the spec, then assets/
      alt_text: "Retail Mobile Banking app icon"
      x: 0.374
      y: 1.3
      w: 0.8
      h: 0.8        # a square app icon; a wordmark keeps its own width-to-height ratio
```
