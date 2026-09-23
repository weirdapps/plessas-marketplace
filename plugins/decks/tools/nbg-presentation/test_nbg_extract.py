"""Tests for nbg_extract.py: a built deck read back as markdown, the way
/redesign-deck reads a colleague's deck."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import nbg_build
import nbg_extract
import pytest
from PIL import Image
from testkit import EXAMPLES_DIR, deck, passing_validator, write_spec

SCRIPT = Path(__file__).parent / "nbg_extract.py"
SOURCE = {"name": "Management accounts", "as_of": "30 June 2026"}


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    tmp: Path = tmp_path_factory.mktemp("extract")
    spec = deck(
        [
            {
                "type": "content",
                "content": {
                    "title": "Three things moved",
                    "points": ["One", {"text": "Two", "level": 2}],
                },
                "notes": "Say the three things.",
            },
            {
                "type": "table",
                "content": {"title": "Fees grew", "source": SOURCE},
                "table": {"headers": ["Line", "2026"], "rows": [["Cards", "EUR 12M"]]},
            },
            {
                "type": "chart",
                "content": {"title": "Volumes rose", "source": SOURCE},
                "chart": {
                    "type": "bar",
                    "data": {
                        "categories": ["Q1", "Q2"],
                        "series": [{"name": "2026", "values": [3, 4]}],
                    },
                },
            },
            {
                "type": "waterfall",
                "content": {"title": "The bridge", "source": SOURCE},
                "chart": {
                    "type": "waterfall",
                    "data": {
                        "items": [
                            {"label": "Start", "value": 10},
                            {"label": "Up", "value": 5},
                            {"label": "End", "value": 15},
                        ]
                    },
                },
            },
            {
                "type": "image",
                "content": {"title": "A picture"},
                "image": {
                    "path": "illustrations/Growth.png",
                    "alt_text": "A rising savings balance",
                },
            },
        ]
    )
    out = tmp / "deck.pptx"
    nbg_build.build_presentation(write_spec(tmp, spec), out, validate=False)
    return out


def test_titles_bullets_notes_tables_charts_and_images(built):
    text = nbg_extract.extract(built)
    assert "## Slide 1: Test deck" in text
    assert "## Slide 2: Three things moved" in text
    assert "- One" in text and "  - Two" in text
    assert "Notes: Say the three things." in text
    assert "| Line | 2026 |" in text and "| Cards | EUR 12M |" in text
    assert "Chart (bar):" in text and "| Q1 | 3 |" in text
    assert "Chart (waterfall):" in text and "| Up | +5 |" in text
    assert "[image: A rising savings balance]" in text
    assert "Source: Management accounts, as of 30 June 2026" in text


def test_the_title_and_the_page_number_are_not_repeated_as_body_text(built):
    text = nbg_extract.extract(built)
    assert text.count("Three things moved") == 1
    assert "\n2\n" not in text and "\n3\n" not in text


def test_logos_are_not_reported_as_content(built):
    assert "[image: ]" not in nbg_extract.extract(built)


def test_every_example_extracts(tmp_path, monkeypatch):
    passing_validator(monkeypatch, nbg_build)
    for spec in sorted(EXAMPLES_DIR.glob("*.yaml")):
        out = tmp_path / f"{spec.stem}.pptx"
        nbg_build.build_presentation(spec, out)
        text = nbg_extract.extract(out)
        assert text.count("## Slide ") >= 5, spec.name


def test_a_pdf_extracts_page_by_page(tmp_path):
    pdf = tmp_path / "doc.pdf"
    pages = [Image.new("RGB", (200, 100), "white") for _ in range(2)]
    pages[0].save(pdf, save_all=True, append_images=pages[1:])
    text = nbg_extract.extract(pdf)
    assert "## Page 1" in text and "## Page 2" in text


def test_docx_is_refused_with_the_way_round_it(tmp_path, capsys):
    doc = tmp_path / "memo.docx"
    doc.write_bytes(b"PK")
    assert nbg_extract.main([str(doc)]) == 2
    assert "save the document as pdf" in capsys.readouterr().err.lower()


def test_a_missing_or_damaged_file_exits_2(tmp_path, capsys):
    assert nbg_extract.main([str(tmp_path / "nope.pptx")]) == 2
    broken = tmp_path / "broken.pptx"
    broken.write_bytes(b"not a zip")
    assert nbg_extract.main([str(broken)]) == 2


def test_the_cli_writes_greek_as_utf8(tmp_path):
    out = tmp_path / "greek.pptx"
    nbg_build.build_presentation(EXAMPLES_DIR / "greek-deck.yaml", out, validate=False)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(out)],
        capture_output=True,
        env={"PYTHONIOENCODING": "cp1252", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "Περιεχόμενα" in proc.stdout.decode("utf-8")
