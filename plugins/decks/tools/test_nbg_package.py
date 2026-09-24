"""Tests for nbg_package.py: the zip-bomb limits on decks the tools did not write."""

from __future__ import annotations

import zipfile

import nbg_package  # noqa: E402  (sits next to this file)
import pytest


def _zip(path, members, compression=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, "w", compression) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def test_an_ordinary_package_passes(tmp_path):
    deck = _zip(
        tmp_path / "ok.pptx",
        {
            "[Content_Types].xml": "<Types/>",
            "ppt/slides/slide1.xml": "<p:sld>" + "x" * 5000 + "</p:sld>",
        },
    )
    nbg_package.check_package(deck)


def test_a_part_that_inflates_thousands_of_times_is_refused(tmp_path):
    """The reviewer's 406 KB file drove one extract to 583 MB before lxml gave up."""
    bomb = _zip(tmp_path / "bomb.pptx", {"ppt/slides/slide1.xml": " " * (3 * nbg_package.MIB)})
    with pytest.raises(nbg_package.PackageError, match="zip bomb"):
        nbg_package.check_package(bomb)


def test_a_renamed_xml_part_still_counts_as_xml(tmp_path, monkeypatch):
    monkeypatch.setattr(nbg_package, "MAX_XML_PART_BYTES", 1000)
    renamed = _zip(tmp_path / "renamed.pptx", {"ppt/data.dat": "<a>" + "b" * 2000 + "</a>"})
    with pytest.raises(nbg_package.PackageError, match="XML"):
        nbg_package.check_package(renamed)


def test_media_parts_do_not_count_against_the_xml_limits(tmp_path, monkeypatch):
    monkeypatch.setattr(nbg_package, "MAX_XML_PART_BYTES", 1000)
    picture = _zip(tmp_path / "picture.pptx", {"ppt/media/image1.png": b"\x89PNG" + bytes(5000)})
    nbg_package.check_package(picture)


def test_the_total_xml_and_the_member_count_are_capped(tmp_path, monkeypatch):
    monkeypatch.setattr(nbg_package, "MAX_XML_TOTAL_BYTES", 3000)
    many = _zip(tmp_path / "many.pptx", {f"ppt/slides/slide{i}.xml": "x" * 1000 for i in range(4)})
    with pytest.raises(nbg_package.PackageError, match="MiB of XML"):
        nbg_package.check_package(many)
    monkeypatch.setattr(nbg_package, "MAX_MEMBERS", 3)
    with pytest.raises(nbg_package.PackageError, match="members"):
        nbg_package.check_package(many)


def test_a_file_that_is_not_a_zip_is_refused(tmp_path):
    fake = tmp_path / "fake.pptx"
    fake.write_bytes(b"this is not a zip")
    with pytest.raises(nbg_package.PackageError, match="not a readable zip"):
        nbg_package.check_package(fake)
