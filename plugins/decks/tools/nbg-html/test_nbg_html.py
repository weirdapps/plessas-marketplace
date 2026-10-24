"""Tests for the HTML deck tool: tokens to CSS, build, static check, and (with a
browser on the machine, as on the CI runner) the layout check and the PDF export."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import nbg_html  # noqa: E402

EXAMPLE = HERE / "example" / "deck.src.html"
# Custom properties set on an element (by the author, the runtime or a scrim
# variant), never defined at :root; each use carries a fallback.
AUTHOR_VARS = {"v", "nbg-zoom", "swatch", "hbar-label-w", "k-scrim"}

DECK = """<!doctype html>
<html lang="en"><head><title>T</title>{head}</head>
<body><main class="deck">
<section class="slide"><h1>Title</h1><div class="body">{body}</div></section>
</main></body></html>
"""


def write(
    tmp_path: Path, body: str = "<p>Text</p>", head: str = "", name: str = "src.html"
) -> Path:
    p = tmp_path / name
    p.write_text(DECK.format(body=body, head=head), encoding="utf-8")
    return p


def built(tmp_path: Path, **kw: str) -> Path:
    out = tmp_path / "deck.html"
    nbg_html.build(write(tmp_path, **kw), out)
    return out


# --------------------------------------------------------------- design system
def test_every_css_variable_is_defined_from_tokens() -> None:
    css = nbg_html.RUNTIME_CSS.read_text(encoding="utf-8")
    js = nbg_html.RUNTIME_JS.read_text(encoding="utf-8")
    defined = set(re.findall(r"--([\w-]+):", nbg_html.root_block()))
    # A name ending in "-" is a prefix the runtime completes ('var(--c-' + name).
    used = {u for u in re.findall(r"var\(--([\w-]+)", css + js) if not u.endswith("-")}
    assert used, "found no var() uses: the scan examined nothing"
    missing = used - defined - AUTHOR_VARS
    assert not missing, f"used but never defined from tokens.yaml: {sorted(missing)}"


def test_css_holds_no_brand_value_of_its_own() -> None:
    css = nbg_html.RUNTIME_CSS.read_text(encoding="utf-8")
    assert not re.findall(r"#[0-9a-fA-F]{3,6}\b", css), (
        "colours belong in tokens.yaml, not deck.css"
    )
    assert "box-shadow" not in css and "drop-shadow" not in css


def test_tokens_map_to_the_1920_artboard() -> None:
    root = nbg_html.root_block()
    # 0.374 in gutter and the 24pt title, at 144 px per inch and 2 px per point
    assert "--gutter: 53.86px;" in root
    assert "--fs-title: 48px;" in root
    assert "--c-dark-teal: #003841;" in root
    assert 'url("data:image/svg+xml;base64,' in root  # the Greek wordmark, inlined


def test_runtime_is_safe_to_inline_and_offline() -> None:
    js = nbg_html.RUNTIME_JS.read_text(encoding="utf-8")
    assert "</script" not in js.lower()
    assert nbg_html.EM_DASH not in js
    for banned in (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "sendBeacon",
        "http://",
        "https://",
        "eval(",
    ):
        assert banned not in js, f"the runtime must not reach the network or eval: {banned}"


# ----------------------------------------------------------------------- build
def test_build_inlines_design_system_runtime_and_pictures(tmp_path: Path) -> None:
    (tmp_path / "pic.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"/>', encoding="utf-8"
    )
    out = built(
        tmp_path, body='<img src="pic.svg" alt=""><div style="background:url(pic.svg)"></div>'
    )
    text = out.read_text(encoding="utf-8")
    assert text.count('id="nbg-deck-css"') == 1
    assert text.count('id="nbg-deck-runtime"') == 1
    assert 'src="data:image/svg+xml;base64,' in text
    assert "url('data:image/svg+xml;base64," in text
    assert "pic.svg" not in text


def test_rebuilding_a_built_deck_replaces_the_runtime_and_keeps_the_slides(tmp_path: Path) -> None:
    first = built(tmp_path, body="<p>Kept</p>")
    again = tmp_path / "again.html"
    nbg_html.build(first, again)
    a, b = first.read_text(encoding="utf-8"), again.read_text(encoding="utf-8")
    assert a == b
    assert b.count("data-nbg-runtime") == 3  # generator meta, design system, runtime
    assert "<p>Kept</p>" in b
    # Greek must not depend on the browser guessing: charset in the first 1024 bytes.
    assert b.count("<meta charset") == 1 and b.index("<meta charset") < 1024


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('<img src="https://example.com/a.png">', "external picture"),
        ('<img src="missing.png">', "picture not found"),
        ('<div style="background:url(https://example.com/b.png)"></div>', "external picture"),
    ],
)
def test_build_refuses_pictures_it_cannot_inline(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(nbg_html.DeckError, match=message):
        built(tmp_path, body=body)


def test_build_needs_one_deck(tmp_path: Path) -> None:
    p = tmp_path / "x.html"
    p.write_text(
        "<html><head></head><body><section class='slide'></section></body></html>", encoding="utf-8"
    )
    with pytest.raises(nbg_html.DeckError, match="main"):
        nbg_html.build(p, tmp_path / "out.html")


# ---------------------------------------------------------------- static check
def errors(path: Path) -> list[str]:
    return [
        i["what"]
        for i in nbg_html.static_check(path.read_text(encoding="utf-8"))
        if i["level"] == "error"
    ]


def test_the_example_deck_is_clean(tmp_path: Path) -> None:
    out = tmp_path / "example.html"
    nbg_html.build(EXAMPLE, out)
    assert errors(out) == []
    assert nbg_html.count_slides(out.read_text(encoding="utf-8")) == 7


@pytest.mark.parametrize(
    ("kw", "message"),
    [
        ({"body": '<p style="color:#123456">x</p>'}, "not an NBG colour"),
        ({"body": '<p style="color:#595959">x</p>'}, "retired caption grey"),
        ({"body": '<svg><rect fill="#4F81BD"/></svg>'}, "Office 2007"),
        ({"body": '<div style="box-shadow:0 2px 4px var(--c-black)">x</div>'}, "shadow"),
        ({"body": '<p style="font-family:Comic Sans MS">x</p>'}, "Comic Sans"),
        (
            {"head": '<link rel="stylesheet" href="https://fonts.example/x.css">'},
            "external resource",
        ),
        ({"head": "<script>alert(1)</script>"}, "author <script>"),
        ({"body": '<p onclick="go()">x</p>'}, "onclick"),
        ({"body": "<p>one " + nbg_html.EM_DASH + " two</p>"}, "em dash"),
    ],
)
def test_static_check_catches(tmp_path: Path, kw: dict[str, str], message: str) -> None:
    out = built(tmp_path, **kw)
    found = errors(out)
    assert any(message in e for e in found), found


def test_static_check_catches_network_css_added_after_the_build(tmp_path: Path) -> None:
    # build refuses it; a hand edit to a built file is what check has to catch
    out = built(tmp_path)
    out.write_text(
        out.read_text(encoding="utf-8").replace(
            "</head>", "<style>@import 'https://x/y.css';</style></head>"
        ),
        encoding="utf-8",
    )
    assert any("network" in e for e in errors(out))


def test_static_check_accepts_brand_colours_and_token_names(tmp_path: Path) -> None:
    out = built(
        tmp_path,
        body='<p style="color:#007B85;background:var(--c-off-white)">x</p><svg><rect fill="#00ADBF"/></svg>',
    )
    assert errors(out) == []


def test_an_unbuilt_source_is_reported(tmp_path: Path) -> None:
    assert any("not built" in e for e in errors(write(tmp_path)))


# --------------------------------------------------------------------- browser
BROWSER = nbg_html.find_browser()
needs_browser = pytest.mark.skipif(
    BROWSER is None, reason="no Chrome, Edge or Chromium on this machine"
)


@needs_browser
def test_layout_check_passes_the_example(tmp_path: Path) -> None:
    out = tmp_path / "example.html"
    nbg_html.build(EXAMPLE, out)
    report = nbg_html.check(out, static_only=False, browser=None)
    assert report["layout"] and len(report["layout"]["slides"]) == 7
    assert report["errors"] == 0, report["issues"]


@needs_browser
def test_layout_check_finds_overflow_small_text_and_gutter(tmp_path: Path) -> None:
    body = (
        "<ul>" + "<li>A long line of body text that keeps the slide busy</li>" * 30 + "</ul>"
        '<p style="font-size:14px">tiny</p>'
        '<p class="free" style="position:absolute;left:-200px;top:0">off</p>'
    )
    report = nbg_html.check(built(tmp_path, body=body), static_only=False, browser=None)
    text = " | ".join(i["what"] for i in report["issues"])
    assert "past the bottom of the body area" in text or "footer zone" in text, text
    assert "under the 10pt floor" in text, text
    assert "runs off the slide" in text or "crosses the side gutter" in text, text


@needs_browser
def test_pdf_has_one_artboard_page_per_slide(tmp_path: Path) -> None:
    out = tmp_path / "example.html"
    nbg_html.build(EXAMPLE, out)
    res = nbg_html.export_pdf(out, tmp_path / "example.pdf", None, tmp_path / "png", 20)
    assert res["problems"] == [], res
    assert res["pages"] == 7 and res["page_px"] == [1920, 1080]
    assert len(res["pngs"]) == 7


def test_pdf_without_a_browser_says_so(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nbg_html, "find_browser", lambda explicit=None: None)
    out = built(tmp_path)
    assert nbg_html.main(["pdf", str(out)]) == nbg_html.NO_BROWSER


@needs_browser
def test_layout_check_measures_contrast(tmp_path: Path) -> None:
    body = '<p style="color:var(--c-light-grey)">Light grey on white fails AA</p>'
    report = nbg_html.check(built(tmp_path, body=body), static_only=False, browser=None)
    assert any("contrast" in i["what"] for i in report["issues"]), report["issues"]


def test_pictures_named_in_comments_are_left_alone(tmp_path: Path) -> None:
    out = built(tmp_path, body='<!-- use <img src="photo.jpg"> over a scrim --><p>x</p>')
    assert 'src="photo.jpg"' in out.read_text(encoding="utf-8")


# --------------------------------------------------------------------- keynote
KEYNOTE = HERE / "example" / "keynote.src.html"


def keynote_example(tmp_path: Path) -> Path:
    """The keynote example built in tmp_path, its photographs dark stand-ins
    (real ones are never committed)."""
    from PIL import Image

    src = tmp_path / "keynote.src.html"
    src.write_text(KEYNOTE.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "photos").mkdir()
    for name in ("cover", "divider", "closing"):
        Image.new("RGB", (192, 108), (20, 40, 46)).save(tmp_path / "photos" / f"{name}.jpg")
    out = tmp_path / "keynote.html"
    nbg_html.build(src, out)
    return out


def keynote_deck(tmp_path: Path, slides: str) -> Path:
    src = tmp_path / "k.src.html"
    src.write_text(
        '<!doctype html><html lang="el"><head><title>K</title></head><body>'
        f'<main class="deck keynote">{slides}<section class="slide k-back"></section></main>'
        "</body></html>",
        encoding="utf-8",
    )
    out = tmp_path / "k.html"
    nbg_html.build(src, out)
    return out


def test_keynote_tokens_scale_from_2560() -> None:
    root = nbg_html.root_block()
    assert "--k-gutter: 116.25px;" in root  # 155 px at 2560
    assert "--k-ground-from: #00161B;" in root
    assert "--logo-wordmark-white: url(" in root


def test_white_wordmark_has_no_colour_left() -> None:
    import base64

    svg = base64.b64decode(nbg_html.white_wordmark().split(",", 1)[1]).decode("utf-8")
    fills = {f.upper() for f in re.findall(r'fill="(#[0-9A-Fa-f]{3,6})"', svg)}
    assert fills == {"#FFFFFF"}


def test_the_keynote_example_is_clean(tmp_path: Path) -> None:
    assert errors(keynote_example(tmp_path)) == []


def test_keynote_needs_a_note_on_every_slide_but_the_back(tmp_path: Path) -> None:
    out = keynote_deck(tmp_path, '<section class="slide"><p class="statement">x</p></section>')
    assert any("no speaker note" in e for e in errors(out))


def test_keynote_caps_charts_and_bars(tmp_path: Path) -> None:
    bars = '<div class="kbar" style="--v:.5"><b>1</b><i></i><span>a</span></div>' * 8
    chart = f'<section class="slide"><div class="kbars many">{bars}</div><aside class="notes">n</aside></section>'
    found = errors(keynote_deck(tmp_path, chart * 3))
    assert any("8 bars" in e for e in found), found
    assert any("3 chart slides" in e for e in found), found


def test_keynote_palette_is_dark_only_in_a_keynote(tmp_path: Path) -> None:
    dark = '<p style="color:#96A6A8;background:#00161B">x</p>'
    assert any("colour" in e for e in errors(built(tmp_path, body=dark)))
    ok = keynote_deck(
        tmp_path, f'<section class="slide">{dark}<aside class="notes">n</aside></section>'
    )
    assert not [e for e in errors(ok) if "colour" in e]


@needs_browser
def test_keynote_layout_check_passes_the_example(tmp_path: Path) -> None:
    out = keynote_example(tmp_path)
    report = nbg_html.check(out, static_only=False, browser=None)
    assert report["layout"]["keynote"] is True
    assert report["errors"] == 0, report["issues"]


def test_keynote_cover_divider_and_closing_need_a_photograph(tmp_path: Path) -> None:
    note = '<aside class="notes">n</aside>'
    slides = (
        f'<section class="slide k-cover"><div class="k-head"><h1>T</h1></div>{note}</section>'
        f'<section class="slide k-divider"><h1>D</h1>{note}</section>'
        f'<section class="slide k-closing"><p class="closing-line">C</p>{note}</section>'
    )
    found = errors(keynote_deck(tmp_path, slides))
    for kind in ("cover", "divider", "closing"):
        assert any(f"a {kind} slide needs a photograph" in e for e in found), found


def test_paths_outside_home_work_and_temp_are_refused(tmp_path: Path) -> None:
    with pytest.raises(nbg_html.DeckError, match="outside"):
        nbg_html.safe_path("/etc/hosts")
    with pytest.raises(nbg_html.DeckError, match="picture"):
        built(tmp_path, body='<img src="/etc/hosts">')
    with pytest.raises(nbg_html.DeckError, match="expected"):
        nbg_html.safe_path(tmp_path / "deck.txt", suffixes=nbg_html.HTML_SUFFIXES)
    assert nbg_html.main(["build", "/etc/hosts", str(tmp_path / "x.html")]) == 2
