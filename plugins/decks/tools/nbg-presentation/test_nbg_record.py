"""Tests for nbg_record.py: the draft record format /presentation-review reads."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import nbg_record
import pytest
import yaml
from testkit import write_spec

ATHENS = timezone(timedelta(hours=3))
NOW = datetime(2026, 9, 23, 12, 45, 7, tzinfo=ATHENS)


def _deck(tmp_path) -> tuple[Path, Path]:
    spec = write_spec(
        tmp_path,
        {
            "presentation": {"title": "Quarterly Business Review"},
            "slides": [
                {"type": "cover", "id": "S01", "content": {"title": "Quarterly Business Review"}},
                {
                    "type": "toc",
                    "id": "S02",
                    "content": {"sections": [{"title": "A"}, {"title": "B"}]},
                },
                {"type": "back_cover", "id": "S03"},
            ],
        },
    )
    pptx = tmp_path / "deck.pptx"
    pptx.write_bytes(b"pretend this is a deck")
    return pptx, spec


def test_the_record_has_every_documented_key(tmp_path):
    pptx, spec = _deck(tmp_path)
    path, record = nbg_record.write_record(pptx, spec, tmp_path / "data", now=NOW)
    assert (
        path
        == tmp_path
        / "data"
        / "presentations"
        / "pending"
        / "202609231245_quarterly_business_review.yaml"
    )
    on_disk = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert on_disk == record
    assert list(record) == [
        "id",
        "created",
        "status",
        "topic",
        "file_path",
        "file_hash",
        "spec_path",
        "slides",
        "spec",
    ]
    assert record["id"] == "202609231245_quarterly_business_review"
    assert record["created"] == "2026-09-23T12:45:07+03:00"
    assert record["status"] == "pending"
    assert record["topic"] == "Quarterly Business Review"
    assert record["file_path"] == str(pptx.resolve())
    assert record["file_hash"] == "sha256:" + hashlib.sha256(pptx.read_bytes()).hexdigest()
    assert record["spec_path"] == str(spec.resolve())
    assert record["slides"] == [
        {"index": 1, "id": "S01", "type": "cover", "title": "Quarterly Business Review"},
        {"index": 2, "id": "S02", "type": "contents", "title": None},
        {"index": 3, "id": "S03", "type": "back_cover", "title": None},
    ]
    # The snapshot is normalised: the legacy "toc" is stored as "contents".
    assert record["spec"]["slides"][1]["type"] == "contents"


def test_topic_overrides_the_title_and_greek_slugs_transliterate(tmp_path):
    pptx, spec = _deck(tmp_path)
    path, record = nbg_record.write_record(
        pptx, spec, tmp_path, topic="Ψηφιακή τραπεζική 2025", now=NOW
    )
    assert record["id"] == "202609231245_psifiaki_trapeziki_2025"
    assert path.name == "202609231245_psifiaki_trapeziki_2025.yaml"
    assert "Ψηφιακή" in path.read_text(encoding="utf-8")


def test_slugify_keeps_names_short_and_safe():
    assert nbg_record.slugify("Q4 2025: Cards & Digital!") == "q4_2025_cards_digital"
    assert nbg_record.slugify("") == "deck"
    assert len(nbg_record.slugify("word " * 40)) <= 60


def test_the_cli_prints_the_record_path_as_json(tmp_path, capsys):
    pptx, spec = _deck(tmp_path)
    code = nbg_record.main([str(pptx), str(spec), "--data", str(tmp_path / "data")])
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert set(body) == {"record", "id", "slides"}
    assert Path(body["record"]).is_file() and body["slides"] == 3


@pytest.mark.parametrize("data", ["", "  ", "relative/data"])
def test_an_empty_or_relative_data_folder_exits_2_naming_the_variable(
    tmp_path, monkeypatch, capsys, data
):
    """SECURITY-PUBLIC-4: an empty --data (an unset ${CLAUDE_PLUGIN_DATA}) wrote the whole
    deck, figures and absolute paths included, into whatever folder was current."""
    pptx, spec = _deck(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert nbg_record.main([str(pptx), str(spec), "--data", data]) == 2
    assert "CLAUDE_PLUGIN_DATA" in capsys.readouterr().err
    assert not (tmp_path / "presentations").exists()
    assert not (tmp_path / "relative").exists()


def test_a_missing_deck_or_a_broken_spec_exits_2(tmp_path, capsys):
    pptx, spec = _deck(tmp_path)
    assert nbg_record.main([str(tmp_path / "nope.pptx"), str(spec), "--data", str(tmp_path)]) == 2
    broken = tmp_path / "broken.yaml"
    broken.write_text("slides: [\n", encoding="utf-8")
    assert nbg_record.main([str(pptx), str(broken), "--data", str(tmp_path)]) == 2
    assert "YAML syntax" in capsys.readouterr().err
