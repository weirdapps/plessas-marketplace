"""nbg_measure: a box sized from its answer must pass the builder's own fit check."""

from __future__ import annotations

import json

import nbg_build
import nbg_measure
import pytest
from PIL import Image
from testkit import deck, passing_validator, write_spec

TEXT = "Recurring reports run as automated flows and the analyst signs off each one"


@pytest.mark.parametrize(
    ("role", "size", "bold"),
    [("card_body", 16, False), ("card_title", 14, True), ("body", 14, False)],
)
def test_a_text_box_sized_from_measure_builds_clean(tmp_path, monkeypatch, role, size, bold):
    passing_validator(monkeypatch, nbg_build)
    m = nbg_measure.measure_text(TEXT, 3.2, size=size, bold=bold, role=role)
    assert m["lines"] >= 2 and len(m["wrapped"]) == m["lines"]
    el = {
        "kind": "text",
        "role": role,
        "x": 1,
        "y": 2,
        "w": 3.2,
        "h": m["h"],
        "size": size,
        "bold": bold,
        "text": TEXT,
    }
    spec = deck([{"type": "custom", "content": {"title": "Measured"}, "elements": [el]}])
    nbg_build.build_presentation(write_spec(tmp_path, spec), tmp_path / "ok.pptx")

    short = {
        **el,
        "h": m["h"] - nbg_build.text_height(1, nbg_build.Style(size, bold, "000000")) - 0.05,
    }
    spec = deck([{"type": "custom", "content": {"title": "Too short"}, "elements": [short]}])
    with pytest.raises(Exception, match="does not fit"):
        nbg_build.build_presentation(write_spec(tmp_path, spec, "short.yaml"), tmp_path / "no.pptx")


def test_an_image_keeps_its_shape_and_aligns_in_its_box(tmp_path):
    Image.new("RGB", (800, 400), "#007B85").save(tmp_path / "wide.png")
    m = nbg_measure.fit_image("wide.png", [1, 1, 4, 4], spec_dir=tmp_path, valign="top")
    assert (m["x"], m["y"], m["w"], m["h"]) == (1, 1, 4, 2)
    m = nbg_measure.fit_image("wide.png", [1, 1, 4, 4], spec_dir=tmp_path, halign="right")
    assert (m["x"], m["y"]) == (1, 2) and "warning" not in m, "800 px across 4 in is 200 DPI"
    m = nbg_measure.fit_image("wide.png", [0, 0, 8, 4], spec_dir=tmp_path)
    assert "warning" in m, "800 px across 8 in is under the builder's 150 DPI"


def test_a_library_path_resolves_like_the_builders(tmp_path):
    m = nbg_measure.fit_image("illustrations/Growth.png", [0, 0, 3, 3], spec_dir=tmp_path)
    assert m["w"] == 3 and m["px"][0] == 800


def test_batch_answers_each_request_and_a_missing_image_exits_2(tmp_path, capsys):
    Image.new("RGB", (900, 900), "white").save(tmp_path / "sq.png")
    reqs = tmp_path / "r.json"
    reqs.write_text(
        json.dumps(
            [{"text": "One line", "w": 4, "size": 14}, {"image": "sq.png", "box": [0, 0, 2, 1]}]
        ),
        encoding="utf-8",
    )
    assert nbg_measure.main(["batch", str(reqs), "--deck", str(tmp_path / "deck.yaml")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["lines"] == 1 and out[1]["w"] == 1
    assert nbg_measure.main(["image", "nope.png", "--box", "0", "0", "1", "1"]) == 2
