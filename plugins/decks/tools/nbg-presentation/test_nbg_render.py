"""Tests for nbg_render.py. LibreOffice is not installed in CI, so a stand-in soffice
exercises the command line, the profile isolation and the PDF-to-PNG path; the font
check runs on PDFs built here with and without an embedded Aptos."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import nbg_build
import nbg_render
import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

FAKE_SOFFICE = """#!{python}
import json, os, sys
from pathlib import Path
from PIL import Image
args = sys.argv[1:]
Path(os.environ["FAKE_SOFFICE_LOG"]).write_text(json.dumps(args), encoding="utf-8")
if os.environ.get("FAKE_SOFFICE_FAIL"):
    sys.exit(1)
outdir = Path(args[args.index("--outdir") + 1])
deck = Path(args[-1])
pages = [Image.new("RGB", (960, 540), "white") for _ in range(int(os.environ["FAKE_PAGES"]))]
pages[0].save(outdir / (deck.stem + ".pdf"), save_all=True, append_images=pages[1:], resolution=72)
"""


@pytest.fixture
def two_slide_deck(tmp_path: Path) -> Path:
    prs = nbg_build.new_presentation()
    nbg_build.create_cover_slide(prs, {"title": "Deck"})
    nbg_build.create_back_cover_slide(prs)
    path = tmp_path / "deck.pptx"
    prs.save(str(path))
    return path


@pytest.fixture
def fake_soffice(tmp_path: Path, monkeypatch) -> Path:
    script = tmp_path / "soffice"
    script.write_text(FAKE_SOFFICE.format(python=sys.executable), encoding="utf-8")
    script.chmod(0o755)
    log = tmp_path / "soffice-args.json"
    monkeypatch.setenv("DECKS_SOFFICE", str(script))
    monkeypatch.setenv("FAKE_SOFFICE_LOG", str(log))
    monkeypatch.setenv("FAKE_PAGES", "2")
    return log


def test_decks_soffice_wins_and_a_missing_binary_is_none(tmp_path, monkeypatch):
    real = tmp_path / "soffice"
    real.write_text("", encoding="utf-8")
    monkeypatch.setenv("DECKS_SOFFICE", str(real))
    assert nbg_render.find_soffice() == str(real)
    monkeypatch.setenv("DECKS_SOFFICE", str(tmp_path / "absent"))
    assert nbg_render.find_soffice() is None


def test_no_libreoffice_exits_3_with_a_fix(two_slide_deck, tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("DECKS_SOFFICE", raising=False)
    monkeypatch.setattr(nbg_render.shutil, "which", lambda name: None)
    monkeypatch.setattr(nbg_render, "SOFFICE_CANDIDATES", [])
    monkeypatch.setattr(nbg_render.glob, "glob", lambda pattern: [])
    code = nbg_render.main([str(two_slide_deck), str(tmp_path / "out")])
    assert code == 3
    body = json.loads(capsys.readouterr().out)
    assert body["error"] == "LibreOffice is not installed"
    assert "libreoffice.org" in body["fix"]


def test_a_render_writes_one_png_per_page_from_an_isolated_profile(
    two_slide_deck, tmp_path, fake_soffice, capsys
):
    out = tmp_path / "out"
    code = nbg_render.main([str(two_slide_deck), str(out), "--dpi", "30"])
    summary = json.loads(capsys.readouterr().out)
    # The stand-in PDF embeds no fonts at all, so this is the fallback exit.
    assert code == 4 and summary["font_fallback"] is True
    assert [Path(p).name for p in summary["pngs"]] == ["slide-01.png", "slide-02.png"]
    assert summary["slides"] == summary["deck_slides"] == 2
    with Image.open(summary["pngs"][0]) as png:
        assert png.size == (400, 225)  # 13.333 x 7.5 in at 30 dpi
    args = json.loads(fake_soffice.read_text(encoding="utf-8"))
    profile = next(a for a in args if a.startswith("-env:UserInstallation="))
    assert profile.startswith("-env:UserInstallation=file:")
    assert not Path(profile.split("file://", 1)[1]).exists(), "the profile outlived the run"
    assert "--headless" in args and args[args.index("--convert-to") + 1] == "pdf"


def test_stale_pngs_from_an_earlier_render_are_removed(
    two_slide_deck, tmp_path, fake_soffice, capsys
):
    out = tmp_path / "out"
    out.mkdir()
    (out / "slide-09.png").write_bytes(b"stale")
    nbg_render.main([str(two_slide_deck), str(out)])
    assert not (out / "slide-09.png").exists()


def test_a_failed_conversion_exits_2(two_slide_deck, tmp_path, fake_soffice, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_SOFFICE_FAIL", "1")
    code = nbg_render.main([str(two_slide_deck), str(tmp_path / "out")])
    assert code == 2
    assert "could not convert" in json.loads(capsys.readouterr().out)["error"]


def test_a_missing_deck_exits_2(tmp_path, capsys):
    assert nbg_render.main([str(tmp_path / "nope.pptx"), str(tmp_path / "out")]) == 2


def _pdf_with_font(path: Path, base_font: str, embedded: bool) -> Path:
    writer = PdfWriter()
    page = writer.add_blank_page(width=960, height=540)
    descriptor = DictionaryObject({NameObject("/Type"): NameObject("/FontDescriptor")})
    if embedded:
        stream = StreamObject()
        stream.set_data(b"not a real font program")
        descriptor[NameObject("/FontFile2")] = writer._add_object(stream)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/TrueType"),
            NameObject("/BaseFont"): NameObject(base_font),
            NameObject("/FontDescriptor"): writer._add_object(descriptor),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    with open(path, "wb") as f:
        writer.write(f)
    return path


def test_the_font_check_sees_an_embedded_subset_of_aptos(tmp_path):
    fonts = nbg_render.embedded_fonts(_pdf_with_font(tmp_path / "a.pdf", "/ABCDEF+Aptos", True))
    assert fonts == [{"name": "Aptos", "embedded": True}]
    assert nbg_render.aptos_embedded(fonts)


def test_a_referenced_but_unembedded_aptos_is_a_fallback(tmp_path):
    fonts = nbg_render.embedded_fonts(_pdf_with_font(tmp_path / "b.pdf", "/Aptos", False))
    assert fonts == [{"name": "Aptos", "embedded": False}]
    assert not nbg_render.aptos_embedded(fonts)


def test_a_substitute_font_is_a_fallback(tmp_path):
    fonts = nbg_render.embedded_fonts(_pdf_with_font(tmp_path / "c.pdf", "/QWERTY+Carlito", True))
    assert not nbg_render.aptos_embedded(fonts)
    assert os.path.exists(tmp_path / "c.pdf")
