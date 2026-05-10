"""Basic tests for nbg_build.py."""

import sys
from pathlib import Path

import pytest

# nbg_build requires yaml at import time
pytest.importorskip("yaml")

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent))
import nbg_build  # noqa: E402


def test_normalize_slide_type_passthrough():
    """Catalog paths with slashes pass through unchanged."""
    assert (
        nbg_build.normalize_slide_type("covers/simple_white") == "covers/simple_white"
    )
    assert (
        nbg_build.normalize_slide_type("content/text_with_bullets")
        == "content/text_with_bullets"
    )


def test_normalize_slide_type_mckinsey_mapping():
    """McKinsey types map to catalog paths."""
    assert nbg_build.normalize_slide_type("cover") == "covers/quiet"
    assert nbg_build.normalize_slide_type("content") == "content/text_only"
    assert nbg_build.normalize_slide_type("back_cover") == "back_covers/quiet"
    assert nbg_build.normalize_slide_type("divider") == "dividers/quiet_white"


def test_normalize_slide_type_with_visual():
    """recommended_visual hint overrides base type."""
    assert nbg_build.normalize_slide_type("content", "bar_chart") == "charts/bar_single"
    assert nbg_build.normalize_slide_type("content", "table") == "tables/half_page"
    assert (
        nbg_build.normalize_slide_type("content", "kpi_dashboard")
        == "content/text_only"
    )


def test_normalize_slide_type_unknown_defaults():
    """Unknown types default to content/text_with_bullets."""
    assert nbg_build.normalize_slide_type("unknown_type") == "content/text_only"


def test_load_catalog_returns_valid_structure():
    """Catalog loads and has expected top-level keys."""
    catalog = nbg_build.load_catalog()
    assert "templates" in catalog
    assert "GR" in catalog["templates"] or "EN" in catalog["templates"]


def test_example_yaml_files_parse():
    """All example YAML files parse without errors."""
    import yaml

    examples_dir = Path(__file__).parent.parent.parent / "examples"
    if not examples_dir.exists():
        pytest.skip("Examples directory not found")

    yaml_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
    assert len(yaml_files) > 0, "No example YAML files found"

    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        assert data is not None, f"{yf.name} parsed as empty"
