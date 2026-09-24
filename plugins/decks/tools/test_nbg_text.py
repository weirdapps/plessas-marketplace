"""Tests for nbg_text.py: Greek capitals, font discovery and text measurement."""

from __future__ import annotations

import nbg_text  # noqa: E402  (sits next to this file)
import pytest

# ---------------------------------------------------------------- greek_upper


@pytest.mark.parametrize(
    "given,expected",
    [
        ("η συναίνεση", "Η ΣΥΝΑΙΝΕΣΗ"),
        ("το πρόβλημα", "ΤΟ ΠΡΟΒΛΗΜΑ"),
        ("Άγιος Ιωάννης", "ΑΓΙΟΣ ΙΩΑΝΝΗΣ"),
        ("ευθύνη", "ΕΥΘΥΝΗ"),
        ("the consensus", "THE CONSENSUS"),
        ("ΕΤΕ και NBG", "ΕΤΕ ΚΑΙ NBG"),
    ],
)
def test_greek_upper(given, expected):
    assert nbg_text.greek_upper(given) == expected


def test_greek_upper_keeps_the_dialytika():
    assert nbg_text.greek_upper("προϊόν") == "ΠΡΟΪΟΝ"


@pytest.mark.parametrize(
    "given,expected",
    [
        ("Μάιος", "ΜΑΪΟΣ"),
        ("άυλες", "ΑΫΛΕΣ"),
        ("ρολόι", "ΡΟΛΟΪ"),
        ("νεράιδα", "ΝΕΡΑΪΔΑ"),
        ("καΐκι", "ΚΑΪΚΙ"),
        ("είναι", "ΕΙΝΑΙ"),
        ("υιός", "ΥΙΟΣ"),
        ("Ευρώπη", "ΕΥΡΩΠΗ"),
    ],
)
def test_dropping_a_tonos_adds_the_dialytika_that_keeps_two_vowels_apart(given, expected):
    """E2E-OUTPUT-06: in Μάιος the tonos on α says α and ι are two sounds. Dropped in
    capitals, ΜΑΙΟΣ reads as the diphthong αι, so Greek writes ΜΑΪΟΣ. A tonos on the
    second letter of a real diphthong (είναι) needs nothing."""
    assert nbg_text.greek_upper(given) == expected


def test_plain_upper_keeps_the_tonos_which_is_the_bug():
    assert "η συναίνεση".upper() != "Η ΣΥΝΑΙΝΕΣΗ"


def test_greek_upper_leaves_a_latin_accent_alone():
    """Only a tonos on a Greek letter goes; "café" in a Greek deck keeps its é."""
    assert nbg_text.greek_upper("café") == "CAFÉ"


def test_caps_follows_the_deck_language():
    assert nbg_text.caps("πρόβλημα", "el") == "ΠΡΟΒΛΗΜΑ"
    assert nbg_text.caps("key finding", "en") == "KEY FINDING"


def test_numbers_take_the_deck_languages_separators():
    """E2E-OUTPUT-02: Greek writes 1.234.567,89 where English writes 1,234,567.89."""
    assert nbg_text.format_number(1234567.891, 2, "el") == "1.234.567,89"
    assert nbg_text.format_number(1234567.891, 2, "en") == "1,234,567.89"
    assert nbg_text.format_number(-1250.5, 1, "el") == "-1.250,5"
    assert nbg_text.localise_number("12%", "el") == "12%"


def test_a_number_can_be_written_without_grouping_and_rounds_half_up():
    """A year is not 2,023; and PowerPoint rounds 12.5 to 13 where Python's format
    rounds half to even (BUILDER-CODE-01, -02)."""
    assert nbg_text.format_number(2023, 0, "en", group=False) == "2023"
    assert nbg_text.format_number(1234.5, 1, "el", group=False) == "1234,5"
    assert nbg_text.format_number(12.5, 0) == "13"
    assert nbg_text.format_number(-0.125, 2) == "-0.13"


# ---------------------------------------------------------------- font discovery


def test_find_font_file_searches_the_override_and_one_subfolder(tmp_path, monkeypatch):
    flat = tmp_path / "flat"
    nested = tmp_path / "nested" / "aptos"
    flat.mkdir()
    nested.mkdir(parents=True)
    (nested / "Aptos-Bold.ttf").write_bytes(b"x")
    (flat / "Aptos.ttf").write_bytes(b"x")
    monkeypatch.setenv("DECKS_FONT_DIRS", f"{flat}{nbg_text.os.pathsep}{tmp_path / 'nested'}")
    assert nbg_text.find_font_file("Aptos.ttf") == flat / "Aptos.ttf"
    assert nbg_text.find_font_file("Aptos-Bold.ttf") == nested / "Aptos-Bold.ttf"
    assert nbg_text.find_font_file("Missing.ttf") is None


def test_find_font_file_reaches_two_folder_levels_and_ignores_case(tmp_path, monkeypatch):
    """Debian and Ubuntu file fonts by format and family, two levels down
    (/usr/share/fonts/truetype/aptos/), and a case-sensitive Linux file system sees
    aptos.ttf and Aptos.ttf as different names (found by docs on the keynote side)."""
    root = tmp_path / "fonts"
    deep = root / "truetype" / "aptos"
    deep.mkdir(parents=True)
    (deep / "aptos.TTF").write_bytes(b"x")
    monkeypatch.setenv("DECKS_FONT_DIRS", str(root))
    assert nbg_text.find_font_file("Aptos.ttf") == deep / "aptos.TTF"
    (root / "Aptos.ttf").write_bytes(b"x")
    assert nbg_text.find_font_file("Aptos.ttf") == root / "Aptos.ttf", "a flat hit wins"


def test_default_font_dirs_include_office_bundles_and_windows(monkeypatch):
    monkeypatch.delenv("DECKS_FONT_DIRS", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", "/tmp/localappdata")
    dirs = [str(d) for d in nbg_text.font_dirs()]
    assert any("Microsoft PowerPoint.app/Contents/Resources/DFonts" in d for d in dirs)
    assert any(d.endswith("Fonts") and "indows" in d for d in dirs)
    assert any("localappdata" in d and "Microsoft" in d for d in dirs)
    assert any(d.endswith(".local/share/fonts") for d in dirs)


# ---------------------------------------------------------------- measurement


@pytest.fixture
def table_metrics(tmp_path, monkeypatch):
    """A TextMetrics that cannot find any font, so it measures with the table."""
    monkeypatch.setenv("DECKS_FONT_DIRS", str(tmp_path))
    m = nbg_text.TextMetrics()
    assert not m.uses_real_font
    return m


def test_table_widths_are_plausible_and_accents_measure_as_their_base(table_metrics):
    m = table_metrics
    assert m.width("W", 10) > m.width("i", 10)
    assert m.width("é", 12) == pytest.approx(m.width("e", 12))
    assert m.width("Ά", 12) == pytest.approx(m.width("Α", 12))
    # 48pt: an em is 48/72 inch, and "M" is ~0.85 em in Aptos.
    assert 0.5 < m.width("M", 48) < 0.62
    assert m.width("漢", 12) == pytest.approx(12 / 72)


def test_table_overestimates_an_average_line(table_metrics):
    """Aptos Regular sets this pangram at 0.437 em per character; the table must not
    come in under it, or a fit decision made without the fonts would clip."""
    text = "The quick brown fox jumps over the lazy dog"
    real_regular = 0.4374 * len(text) * 24 / 72
    assert table_metrics.width(text, 24) >= real_regular


def test_real_font_path_uses_the_font_advance(tmp_path, monkeypatch):
    class Font:
        @staticmethod
        def getlength(text):
            return 500.0 * len(text)

    monkeypatch.setenv("DECKS_FONT_DIRS", str(tmp_path))
    m = nbg_text.TextMetrics()
    m._fonts = {False: Font()}
    assert m.uses_real_font
    assert m.width("ab", 72) == pytest.approx(1.0)
    # Bold falls back to the regular face rather than to the table.
    assert m.width("ab", 72, bold=True) == pytest.approx(1.0)


def test_line_height_is_aptos_ascent_plus_descent():
    assert nbg_text.TextMetrics.line_height(72) == pytest.approx(2500 / 2048)
    assert nbg_text.TextMetrics.line_height(72, 0.9) == pytest.approx(0.9 * 2500 / 2048)


def test_wrap_never_returns_a_line_wider_than_the_box(table_metrics):
    m = table_metrics
    text = "Digital channels exceeded every target this year, led by mobile adoption growth"
    lines = m.wrap(text, 3.0, 24)
    assert len(lines) > 1
    assert all(m.width(line, 24) <= 3.0 for line in lines)
    assert " ".join(lines) == text


def test_wrap_breaks_a_word_longer_than_the_line(table_metrics):
    m = table_metrics
    lines = m.wrap("Supercalifragilisticexpialidocious", 1.0, 24)
    assert len(lines) > 1
    assert "".join(lines) == "Supercalifragilisticexpialidocious"
    assert all(m.width(line, 24) <= 1.0 for line in lines)


def test_wrap_keeps_explicit_newlines(table_metrics):
    assert table_metrics.wrap("one\ntwo", 10, 12) == ["one", "two"]
    assert table_metrics.wrap("fits on one line", 10, 12) == ["fits on one line"]
