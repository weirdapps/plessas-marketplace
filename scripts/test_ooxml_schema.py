"""Every example deck, built, validates against the ISO/IEC 29500 schemas.

PowerPoint drops XML that breaks the schema without a word, while LibreOffice and
python-pptx both accept it. The builder's bullets were written out of schema order
for months: every bullet and its spacing vanished in PowerPoint, and the previews,
the validator and 81 green tests all showed a correct slide. This test reads the
parts the way PowerPoint does.

The schemas are the Ecma ECMA-376 Part 4 transitional set in scripts/ooxml-xsd/
(see its README for source and licence).
"""

from __future__ import annotations

import re
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

import pytest

etree = pytest.importorskip("lxml.etree")

ROOT = Path(__file__).resolve().parent.parent
XSD_DIR = ROOT / "scripts" / "ooxml-xsd"
BUILDER_DIR = ROOT / "plugins" / "decks" / "tools" / "nbg-presentation"
EXAMPLES = sorted((ROOT / "plugins" / "decks" / "examples").glob("*.yaml"))

SLIDE_PART = re.compile(r"^ppt/slides/slide\d+\.xml$")
CHART_PART = re.compile(r"^ppt/charts/chart\d+\.xml$")


@lru_cache(maxsize=2)
def schema(name: str):
    return etree.XMLSchema(etree.parse(str(XSD_DIR / name)))


def _builder():
    sys.path.insert(0, str(BUILDER_DIR))
    import nbg_build

    return nbg_build


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> dict[str, Path]:
    """Each example built once (validation off: this test is about the XML)."""
    nbg_build = _builder()
    out_dir = tmp_path_factory.mktemp("ooxml")
    decks = {}
    for spec in EXAMPLES:
        out = out_dir / f"{spec.stem}.pptx"
        nbg_build.build_presentation(spec, out, validate=False)
        decks[spec.stem] = out
    return decks


def _schema_errors(xml: bytes, xsd: str) -> list[str]:
    s = schema(xsd)
    doc = etree.fromstring(xml)
    if s.validate(doc):
        return []
    return [f"line {e.line}: {e.message}" for e in list(s.error_log)[:5]]


def test_there_are_examples_to_validate():
    assert len(EXAMPLES) >= 4, [p.name for p in EXAMPLES]


@pytest.mark.parametrize("name", [p.stem for p in EXAMPLES])
def test_every_slide_and_chart_part_is_schema_valid(built, name):
    checked = {"slides": 0, "charts": 0}
    problems = []
    with zipfile.ZipFile(built[name]) as zf:
        for part in zf.namelist():
            if SLIDE_PART.match(part):
                kind, xsd = "slides", "pml.xsd"
            elif CHART_PART.match(part):
                kind, xsd = "charts", "dml-chart.xsd"
            else:
                continue
            checked[kind] += 1
            for error in _schema_errors(zf.read(part), xsd):
                problems.append(f"{part} {error}")
    assert checked["slides"] > 0, "no slide parts: the test looked at nothing"
    assert not problems, "\n".join(problems)


def test_the_schema_check_catches_a_bullet_written_out_of_order(built):
    """The test must be able to fail: put buChar before buClr, as the old builder
    did, and the slide must stop validating."""
    deck = next(iter(built.values()))
    with zipfile.ZipFile(deck) as zf:
        slides = [n for n in zf.namelist() if SLIDE_PART.match(n)]
        xml = next(
            (zf.read(n) for n in slides if b"<a:buChar" in zf.read(n)),
            None,
        )
    assert xml is not None, "no bulleted slide in the first example"
    assert not _schema_errors(xml, "pml.xsd")
    root = etree.fromstring(xml)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    ppr = next(p for p in root.iter(f"{a}pPr") if p.find(f"{a}buChar") is not None)
    bu_char = ppr.find(f"{a}buChar")
    ppr.remove(bu_char)
    ppr.find(f"{a}buClr").addprevious(bu_char)
    assert _schema_errors(etree.tostring(root), "pml.xsd"), "out-of-order bullet XML validated"
