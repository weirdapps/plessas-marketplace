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
    two_slide_deck, tmp_path, fake_soffice, monkeypatch, capsys
):
    out = tmp_path / "out"
    nbg_render.main([str(two_slide_deck), str(out)])
    assert (out / "slide-02.png").exists()
    monkeypatch.setenv("FAKE_PAGES", "1")
    nbg_render.main([str(two_slide_deck), str(out)])
    assert not (out / "slide-02.png").exists(), "the earlier render's page 2 is stale"


def test_render_never_deletes_or_overwrites_files_it_did_not_write(
    two_slide_deck, tmp_path, fake_soffice, capsys
):
    """SECURITY-PUBLIC-5: render deleted every slide-*.png in the folder and overwrote a
    <deck>.pdf it had not written. It now deletes only what its manifest says it
    wrote, and refuses to write over anything else."""
    out = tmp_path / "out"
    out.mkdir()
    (out / "slide-09.png").write_bytes(b"someone else's")
    (out / "deck.pdf").write_bytes(b"an unrelated pdf")
    assert nbg_render.main([str(two_slide_deck), str(out)]) == 2
    body = json.loads(capsys.readouterr().out)
    assert "deck.pdf" in body["error"] and "empty folder" in body["fix"]
    assert (out / "deck.pdf").read_bytes() == b"an unrelated pdf"
    assert not fake_soffice.exists(), "nothing ran"
    (out / "deck.pdf").unlink()
    (out / "slide-01.png").write_bytes(b"a page someone kept")
    assert nbg_render.main([str(two_slide_deck), str(out)]) == 2
    assert (out / "slide-01.png").read_bytes() == b"a page someone kept"
    (out / "slide-01.png").unlink()
    nbg_render.main([str(two_slide_deck), str(out)])
    assert (out / "slide-09.png").read_bytes() == b"someone else's", "not render's to delete"


def test_a_failed_conversion_exits_2(two_slide_deck, tmp_path, fake_soffice, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_SOFFICE_FAIL", "1")
    code = nbg_render.main([str(two_slide_deck), str(tmp_path / "out")])
    assert code == 2
    assert "could not convert" in json.loads(capsys.readouterr().out)["error"]


def test_a_missing_deck_exits_2(tmp_path, capsys):
    assert nbg_render.main([str(tmp_path / "nope.pptx"), str(tmp_path / "out")]) == 2


def test_a_zip_bomb_is_refused_before_libreoffice_sees_it(tmp_path, fake_soffice, capsys):
    """SECURITY-PUBLIC-2: render opened third-party decks with no package limits."""
    import zipfile

    bomb = tmp_path / "bomb.pptx"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("ppt/slides/slide1.xml", " " * (3 * 2**20))
    assert nbg_render.main([str(bomb), str(tmp_path / "out")]) == 2
    assert "zip bomb" in json.loads(capsys.readouterr().out)["error"]
    assert not fake_soffice.exists(), "LibreOffice must never open the file"


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


def test_the_font_check_compares_the_decks_fonts_with_the_pdfs(two_slide_deck):
    """BUILDER-CODE-10: the guard asked only whether any Aptos was embedded, so a deck
    whose Arial was swapped for Liberation Sans passed, and a Calibri deck drawn in
    Carlito was reported as 'Aptos is not embedded'. It now names what was swapped."""
    assert "Aptos" in nbg_render.requested_fonts(two_slide_deck)
    pdf = [{"name": "Aptos-Bold", "embedded": True}, {"name": "LiberationSans", "embedded": True}]
    assert nbg_render.substituted(["Aptos", "Arial"], pdf) == ["Arial"]
    assert nbg_render.substituted(["Calibri"], [{"name": "Carlito", "embedded": True}]) == [
        "Calibri"
    ]
    assert nbg_render.substituted(["Aptos"], [{"name": "Aptos", "embedded": False}]) == ["Aptos"]
    assert (
        nbg_render.substituted(["Aptos Display"], [{"name": "AptosDisplay", "embedded": True}])
        == []
    )


def test_hidden_slides_keep_their_numbers_and_every_warning_is_kept(
    tmp_path, fake_soffice, monkeypatch, capsys
):
    """BUILDER-CODE-10: LibreOffice skips a hidden slide, so slide-02.png showed deck
    slide 3, and the font warning overwrote the hidden-slide warning."""
    prs = nbg_build.new_presentation()
    nbg_build.create_cover_slide(prs, {"title": "Deck"})
    nbg_build.create_cover_slide(prs, {"title": "Hidden"})
    nbg_build.create_back_cover_slide(prs)
    prs.slides[1]._element.set("show", "0")
    deck = tmp_path / "hidden.pptx"
    prs.save(str(deck))
    code = nbg_render.main([str(deck), str(tmp_path / "out"), "--dpi", "20"])
    summary = json.loads(capsys.readouterr().out)
    assert code == 4
    assert summary["hidden_slides"] == [2]
    assert [Path(p).name for p in summary["pngs"]] == ["slide-01.png", "slide-03.png"]
    assert len(summary["warnings"]) == 2, summary["warnings"]
    assert "hidden" in summary["warning"] and "Aptos" in summary["warning"]


def test_a_substitute_font_is_a_fallback(tmp_path):
    fonts = nbg_render.embedded_fonts(_pdf_with_font(tmp_path / "c.pdf", "/QWERTY+Carlito", True))
    assert not nbg_render.aptos_embedded(fonts)
    assert os.path.exists(tmp_path / "c.pdf")
