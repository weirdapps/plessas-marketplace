# nbg-html: editable HTML decks

One self-contained HTML file per deck: the NBG design system, an in-browser editor and every
picture inlined. The reader edits it in Chrome or Edge, saves it, presents it and prints it to PDF,
one page per slide. The component guide is
[`shared/brand-system/html-decks.md`](../../shared/brand-system/html-decks.md); the command is
`/create-html-deck`.

| File | Role |
|---|---|
| `nbg_html.py` | `build`, `check`, `pdf` (run as `decks-py html-build`, `html-check`, `html-pdf`) |
| `runtime/deck.css` | the design system: classes only, every value a variable |
| `runtime/editor.js` | the editor, presenter, print hooks and the headless layout report |
| `example/deck.src.html` | a seven-slide sample using most components |
| `example/keynote.src.html` | a nine-slide HTML keynote, every archetype; its photographs go in `example/photos/` (ignored by git) |
| `test_nbg_html.py` | tokens to CSS, build, static check; with a browser, layout check and PDF |

```bash
decks-py html-build example/deck.src.html /tmp/deck.html
decks-py html-check /tmp/deck.html
decks-py html-pdf /tmp/deck.html --png /tmp/deck-png
```

## Design notes

- **One brand.** `root_block()` turns `tokens.yaml` into the `:root` custom properties at every
  build (inches x 144 = px, points x 2 = px on the 1920 x 1080 artboard). `deck.css` holds no hex
  value of its own, and a test fails if one appears.
- **Print is the slide box.** `@page { size: 1920px 1080px; margin: 0 }` and a print stylesheet
  that shows every slide at zoom 1, so the in-deck PDF button and `html-pdf` print the same pages.
  No print-time scaling, no shadows (PDF viewers draw Chrome's shadow masks as grey blocks).
- **Edits are layered, not baked.** Moving writes the CSS `translate` property, resizing
  `width` / `height`, styling inline properties; Reset removes them and the design-system layout
  is back. Save serialises the live page minus the editor's own nodes and classes.
- **Rebuild is an upgrade.** `build` strips every block marked `data-nbg-runtime` and inlines the
  current ones, so an edited deck gets a newer editor and keeps its slides; building twice
  changes nothing. The charset is re-emitted first, inside the first 1024 bytes.
- **Two-stage check.** The static check needs no browser (external resources, scripts, handlers,
  palette, fonts, shadows, em dashes). The layout check opens the deck with `?nbg-check` through
  `--dump-dom`; the runtime then shows no UI and writes a JSON report into the page.
- **Keynote is a theme, not a second tool.** `<main class="deck keynote">` switches to `--k-*`
  variables: keynote.md's 2560 px chassis x 0.75, its dark palette and gutter from the tokens. The
  check adds the keynote rules (a note on every slide, at most two chart slides of seven bars, a
  photograph on the cover, dividers and closing) and uses the keynote gutter, footer and floor.
- **Contrast is measured where it can be.** The layout report computes WCAG contrast against the
  nearest solid fill behind each text run; over a photograph or an unknown gradient it cannot,
  and those slides are judged on their PNG.
- **Offline and plain.** The runtime makes no network call and holds no keys. The browser runs
  headless with a throwaway profile. Edits wait in the browser's `localStorage` until saved.
