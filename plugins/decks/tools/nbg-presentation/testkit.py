"""Helpers shared by the nbg-presentation test files. Not a test module itself.

Builds a deck from an in-memory spec and reads its parts back as XML, so each test
states the spec it needs and the OOXML it expects, and nothing else.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path
from typing import Any

import yaml
from lxml import etree

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
}
EMU = 914400

HERE = Path(__file__).resolve().parent
EXAMPLES_DIR = HERE.parent.parent / "examples"


def emu(inches: float) -> int:
    return round(inches * EMU)


def inches(value: str | int) -> float:
    return int(value) / EMU


def write_spec(tmp_path: Path, spec: Any, name: str = "spec.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def passing_validator(monkeypatch, module) -> list:
    """Replace the validator subprocess with one that passes; returns the calls made."""
    calls: list = []

    def run(cmd, *args, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", run)
    return calls


def deck(slides: list, **presentation: Any) -> dict:
    """A spec with a cover and a back cover around `slides`."""
    spec: dict[str, Any] = {
        "slides": [
            {"type": "cover", "content": {"title": "Test deck"}},
            *slides,
            {"type": "back_cover"},
        ]
    }
    if presentation:
        spec["presentation"] = presentation
    return spec


def part_names(pptx: Path) -> list[str]:
    with zipfile.ZipFile(pptx) as zf:
        return zf.namelist()


def part_xml(pptx: Path, name: str):
    with zipfile.ZipFile(pptx) as zf:
        return etree.fromstring(zf.read(name))


def slide_xml(pptx: Path, number: int):
    """ppt/slides/slide<number>.xml, 1-based, as an lxml element."""
    return part_xml(pptx, f"ppt/slides/slide{number}.xml")


def chart_parts(pptx: Path) -> list[str]:
    names = [n for n in part_names(pptx) if n.startswith("ppt/charts/chart") and n.endswith(".xml")]
    return sorted(names, key=lambda n: int(n[len("ppt/charts/chart") : -len(".xml")]))


def shape_boxes(root) -> list[tuple[str, float, float, float, float]]:
    """(text, x, y, w, h) in inches for every p:sp carrying an a:xfrm."""
    out = []
    for sp in root.iter(f"{{{NS['p']}}}sp"):
        off = sp.find(".//a:xfrm/a:off", NS)
        ext = sp.find(".//a:xfrm/a:ext", NS)
        if off is None or ext is None:
            continue
        text = "".join(t.text or "" for t in sp.iter(f"{{{NS['a']}}}t"))
        out.append(
            (
                text,
                inches(off.get("x")),
                inches(off.get("y")),
                inches(ext.get("cx")),
                inches(ext.get("cy")),
            )
        )
    return out


def box_with_text(root, text: str):
    for box in shape_boxes(root):
        if box[0] == text:
            return box
    raise AssertionError(f"no shape with text {text!r}: {[b[0] for b in shape_boxes(root)]}")


def run_sizes(sp) -> set[float]:
    sizes = set()
    for tag in ("rPr", "defRPr", "endParaRPr"):
        for rpr in sp.iter(f"{{{NS['a']}}}{tag}"):
            if rpr.get("sz"):
                sizes.add(int(rpr.get("sz")) / 100)
    return sizes


def shape_by_text(root, text: str):
    for sp in root.iter(f"{{{NS['p']}}}sp"):
        if "".join(t.text or "" for t in sp.iter(f"{{{NS['a']}}}t")) == text:
            return sp
    raise AssertionError(f"no shape with text {text!r}")
