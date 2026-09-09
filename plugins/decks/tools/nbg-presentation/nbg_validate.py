#!/usr/bin/env python3
"""
NBG Brand Validation Tool

Validates presentations against NBG brand guidelines.
Checks dimensions, colors, fonts, and other brand elements.

Usage:
    python nbg_validate.py presentation.pptx

Output:
    Lists all validation checks with pass/fail status.
"""

import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET

# nbg_color sits one level up, shared with nbg_build and nbg-keynote. These are
# scripts in hyphenated directories rather than a package, so add the path here.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nbg_color import contrast_ratio, min_ratio  # noqa: E402


def _slide_num(slide_file_name: str) -> str:
    """Extract slide number from 'slideN.xml', guaranteed to match by glob pattern."""
    m = re.search(r"slide(\d+)", slide_file_name)
    if m is None:
        raise ValueError(f"Could not extract slide number from {slide_file_name}")
    return m.group(1)


# NBG Brand Guidelines
NBG_GUIDELINES: dict[str, Any] = {
    "dimensions": {
        # NBG template uses 12192000 x 6858000 EMUs
        # Standard conversion: 914400 EMU = 1 inch
        # Therefore: 12192000/914400 = 13.33" and 6858000/914400 = 7.5"
        # Use LAYOUT_WIDE in PptxGenJS (13.33" x 7.5")
        "width_emu": 12192000,
        "height_emu": 6858000,
        "tolerance": 10000,  # EMU tolerance
    },
    "colors": {
        # Primary colors (hex without #)
        "allowed": {
            "003841": "Dark Teal (Pillar Teal 08)",
            "007B85": "NBG Teal (Pillar Teal 05)",
            "047A85": "Teal Variant",
            "00ADBF": "Cyan",
            "00DFF8": "Bright Cyan",
            "00DEF8": "Bright Cyan Alt",
            "000000": "Black",
            "162020": "Pillar Black",
            "202020": "Dark Text",
            "212121": "Alt Black",
            "252D30": "Dark Charcoal",
            "939793": "Medium Gray",
            "595959": "Gray",
            "5A5F5A": "Caption Gray",
            "6A6C6A": "Pillar Grey 04",
            "A2A6A6": "Pillar Grey 03",
            "BEC1BE": "Light Gray",
            "D9D9D9": "Neutral Gray",
            "E0E6E1": "Pillar Grey 02",
            "F5F8F6": "Off White",
            "F5F9F6": "Off White Alt",
            "F6FAF8": "Off White Template",
            "F8F9F9": "Pillar Grey 01",
            "FFFFFF": "White",
            # Pillar Teal Scale (resynced 2026-05-24 from Tsopanakis pillar-skills)
            "03666F": "Pillar Teal 07",
            "087681": "Pillar Teal 06",
            "1299A2": "Pillar Teal 04",
            "13A4AD": "Pillar Teal 03",
            "56B5BB": "Pillar Teal 02",
            "E6F5F6": "Pillar Teal 01",
            "F1F7F7": "Pillar Teal 00",
            # Status colors
            "CB0030": "Deep Red",
            "F60037": "Red",
            "FF7F1A": "Orange",
            "FFDC00": "Yellow",
            "5D8D2F": "Green",
            "90DC48": "Bright Green",
            "73AF3C": "Success Green",
            "AA0028": "Alert Red (NBG corporate)",
            "BE4B4B": "Pillar Error Red",
            "1D8151": "Pillar Success Green",
            "D08239": "Pillar Warning Orange",
            # Segment colors
            "0D90FF": "Business Blue",
            "D9A757": "Premium Gold",
            "1E478E": "Info Blue",
            "59C3FF": "Followed Link",
            # Competitor bank brand colors (Pillar resync 2026-05-24)
            "DC2646": "Eurobank Red",
            "FFC02D": "Piraeus Yellow",
            "0D488B": "Alpha Bank Blue",
            # Chart colors
            "3EDEF8": "Aqua Light",
            "B5B7B5": "Chart Gray",
            "00E2FC": "Highlight Accent",
            "00A7BA": "Cyan Variant",
            "00A9BD": "Cyan Variant 2",
            # Go For More
            "FA8FE1": "Go For More Pink",
            # DIY status pills and card tints. Documented in colors.md (the
            # Practical Status table, the tint hierarchy, the recommended-option
            # highlight) but missing here, so a deck built to the documented
            # spec failed this check.
            "008000": "Status OK / Delivered green",
            "E8F5E9": "Delivered pale fill",
            "CC9900": "Status TBD amber",
            "FFFFCC": "Status TBD pale fill",
            "CC0000": "Status Warning red",
            "CBFAFF": "Highlight card cyan tint",
            "FBF3E4": "Recommended-option cream tint",
        },
        "primary": ["003841", "007B85", "00ADBF", "00DFF8"],
    },
    "fonts": {
        "allowed": [
            "Aptos",
            "Aptos SemiBold",
            "Aptos Display",
            "Arial",
            "Calibri",
            "Tahoma",
        ],
        "primary": "Aptos",
    },
}

# XML Namespaces
NAMESPACES = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


class ValidationResult:
    """One check's outcome.

    `examined` is how many candidate elements the check actually looked at. A
    check that looked at none is reported as "not applicable" rather than as a
    pass: three checks here walked `a:rPr`, which nbg_build never writes, so
    they iterated an empty set and printed green on every deck this repo makes.

    `severity` defaults to "error", which is every check that predates the 2026
    executive-presentation set, so none of them changes behaviour. A "warning"
    check reports without blocking the build. Three of the new checks are
    warnings, each for a stated reason in its own docstring: a real
    false-positive rate the check cannot design away, or a fix that does not
    exist in this tree yet. A warning that could be an error is a bug; so is an
    error that fires on every deck with no way to satisfy it.
    """

    def __init__(
        self,
        name: str,
        passed: bool,
        message: str,
        details: list[str] | None = None,
        examined: int | None = None,
        severity: str = "error",
    ):
        self.name = name
        self.passed = passed
        self.message = message
        self.details: list[str] = details or []
        self.examined = examined
        self.severity = severity

    @property
    def skipped(self) -> bool:
        """Passed while measuring nothing. Honest, but not evidence of anything."""
        return self.passed and self.examined == 0

    @property
    def warned(self) -> bool:
        """Failed, but reports rather than blocks. Never counted as a pass."""
        return not self.passed and self.severity == "warning"


def _run_props(elem) -> list:
    """Every run-property element under `elem`: run level and paragraph level.

    nbg_build sets fonts and colors on the paragraph (`a:defRPr`) and never on
    the run, so a walk over `a:rPr` alone examines nothing on any deck this repo
    produces (measured: 0 rPr, 37 defRPr across an 11-slide build). A
    hand-edited or PowerPoint-round-tripped deck does carry `a:rPr`, so read both.
    """
    return list(elem.findall(f".//{{{NAMESPACES['a']}}}rPr")) + list(
        elem.findall(f".//{{{NAMESPACES['a']}}}defRPr")
    )


def check_dimensions(unpacked_dir: Path) -> ValidationResult:
    """Check slide dimensions match NBG spec."""
    pres_file = unpacked_dir / "ppt" / "presentation.xml"

    if not pres_file.exists():
        return ValidationResult("Dimensions", False, "presentation.xml not found")

    tree = ET.parse(pres_file)
    root = tree.getroot()

    # Find sldSz element
    sld_sz = root.find(".//{{{}}}sldSz".format(NAMESPACES["p"]))

    if sld_sz is None:
        return ValidationResult("Dimensions", False, "Slide size not found")

    cx = int(sld_sz.get("cx", 0))
    cy = int(sld_sz.get("cy", 0))

    expected_cx = NBG_GUIDELINES["dimensions"]["width_emu"]
    expected_cy = NBG_GUIDELINES["dimensions"]["height_emu"]
    tolerance = NBG_GUIDELINES["dimensions"]["tolerance"]

    width_ok = abs(cx - expected_cx) < tolerance
    height_ok = abs(cy - expected_cy) < tolerance

    # Standard EMU to inch conversion: 914400 EMU = 1 inch
    actual_w = cx / 914400
    actual_h = cy / 914400

    if width_ok and height_ok:
        return ValidationResult(
            "Dimensions",
            True,
            f'{actual_w:.2f}" x {actual_h:.2f}" (NBG standard = LAYOUT_WIDE)',
            examined=1,
        )
    else:
        return ValidationResult(
            "Dimensions",
            False,
            f'{actual_w:.2f}" x {actual_h:.2f}" (expected 13.33" x 7.5" / LAYOUT_WIDE)',
        )


def extract_colors_from_slides(unpacked_dir: Path) -> set[str]:
    """Extract all colors used in slides."""
    colors: set[str] = set()
    slides_dir = unpacked_dir / "ppt" / "slides"

    if not slides_dir.exists():
        return colors

    for slide_file in slides_dir.glob("slide*.xml"):
        tree = ET.parse(slide_file)
        root = tree.getroot()

        # Find srgbClr elements
        for elem in root.findall(".//{{{}}}srgbClr".format(NAMESPACES["a"])):
            color = elem.get("val", "").upper()
            if color:
                colors.add(color)

        # Find solidFill with srgbClr
        for elem in root.findall(
            ".//{{{}}}solidFill/{{{}}}srgbClr".format(NAMESPACES["a"], NAMESPACES["a"])
        ):
            color = elem.get("val", "").upper()
            if color:
                colors.add(color)

    return colors


def check_colors(unpacked_dir: Path) -> ValidationResult:
    """Check all colors are within NBG palette."""
    colors = extract_colors_from_slides(unpacked_dir)
    allowed = {c.upper() for c in NBG_GUIDELINES["colors"]["allowed"].keys()}

    invalid = colors - allowed
    valid = colors & allowed

    if not invalid:
        return ValidationResult(
            "Colors",
            True,
            f"All {len(valid)} colors within NBG palette",
            examined=len(colors),
        )
    else:
        details = [f"#{c} (not in NBG palette)" for c in sorted(invalid)]
        return ValidationResult(
            "Colors", False, f"{len(invalid)} non-standard color(s) found", details
        )


def extract_fonts_from_slides(unpacked_dir: Path) -> set[str]:
    """Extract all fonts used in slides."""
    fonts: set[str] = set()
    slides_dir = unpacked_dir / "ppt" / "slides"

    if not slides_dir.exists():
        return fonts

    for slide_file in slides_dir.glob("slide*.xml"):
        tree = ET.parse(slide_file)
        root = tree.getroot()

        # Find latin font elements
        for elem in root.findall(".//{{{}}}latin".format(NAMESPACES["a"])):
            typeface = elem.get("typeface", "")
            if typeface and not typeface.startswith("+"):
                fonts.add(typeface)

        # Find rPr with font info
        for rPr in root.findall(".//{{{}}}rPr".format(NAMESPACES["a"])):
            latin = rPr.find("{{{}}}latin".format(NAMESPACES["a"]))
            if latin is not None:
                typeface = latin.get("typeface", "")
                if typeface and not typeface.startswith("+"):
                    fonts.add(typeface)

    return fonts


def check_fonts(unpacked_dir: Path) -> ValidationResult:
    """Check all fonts are NBG-approved."""
    fonts = extract_fonts_from_slides(unpacked_dir)
    allowed = set(NBG_GUIDELINES["fonts"]["allowed"])

    invalid = fonts - allowed
    valid = fonts & allowed

    if not invalid:
        return ValidationResult(
            "Fonts",
            True,
            f"Fonts used: {', '.join(sorted(valid)) if valid else 'Theme fonts only'}",
            examined=len(fonts),
        )
    else:
        details = [f"{f} (not NBG-approved)" for f in sorted(invalid)]
        return ValidationResult(
            "Fonts", False, f"{len(invalid)} non-standard font(s) found", details
        )


def check_logo_present(unpacked_dir: Path) -> ValidationResult:
    """Check if NBG logo is present in the presentation."""
    media_dir = unpacked_dir / "ppt" / "media"

    if not media_dir.exists():
        return ValidationResult("Logo", False, "No media folder found")

    # Look for NBG logo files
    images = list(media_dir.glob("image*.*"))

    # Check slide relationships for external image references
    slides_dir = unpacked_dir / "ppt" / "slides"
    has_logo_ref = False

    if slides_dir.exists():
        for rels_file in (slides_dir / "_rels").glob("*.rels"):
            with open(rels_file, encoding="utf-8") as f:
                content = f.read().lower()
                if "logo" in content or "nbg" in content:
                    has_logo_ref = True
                    break

    if images or has_logo_ref:
        return ValidationResult(
            "Logo",
            True,
            f"{len(images)} media file(s) found (verify NBG logo manually)",
            examined=len(images) or (1 if has_logo_ref else 0),
        )
    else:
        return ValidationResult("Logo", False, "No media files or logo references found")


def check_slide_count(unpacked_dir: Path) -> ValidationResult:
    """Check presentation has slides."""
    slides_dir = unpacked_dir / "ppt" / "slides"

    if not slides_dir.exists():
        return ValidationResult("Slides", False, "No slides folder found")

    slide_count = len(list(slides_dir.glob("slide*.xml")))

    if slide_count > 0:
        return ValidationResult(
            "Slides", True, f"{slide_count} slide(s) in presentation", examined=slide_count
        )
    else:
        return ValidationResult("Slides", False, "No slides found")


def check_element_boundaries(unpacked_dir: Path) -> ValidationResult:
    """Check all elements are within slide boundaries."""
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Boundaries", False, "No slides folder found")

    # Slide dimensions in EMUs
    slide_width = NBG_GUIDELINES["dimensions"]["width_emu"]
    slide_height = NBG_GUIDELINES["dimensions"]["height_emu"]

    out_of_bounds = []
    checked = 0

    for slide_file in sorted(slides_dir.glob("slide*.xml")):
        slide_num = _slide_num(slide_file.name)
        tree = ET.parse(slide_file)
        root = tree.getroot()

        # Find all position elements (xfrm = transform)
        for xfrm in root.findall(".//{{{}}}xfrm".format(NAMESPACES["a"])):
            off = xfrm.find("{{{}}}off".format(NAMESPACES["a"]))
            ext = xfrm.find("{{{}}}ext".format(NAMESPACES["a"]))

            if off is not None and ext is not None:
                checked += 1
                x = int(off.get("x", 0))
                y = int(off.get("y", 0))
                cx = int(ext.get("cx", 0))
                cy = int(ext.get("cy", 0))

                # Check if element extends beyond slide
                if x + cx > slide_width + 50000:  # 50000 EMU tolerance (~0.05")
                    out_of_bounds.append(
                        f'Slide {slide_num}: element extends {(x + cx - slide_width) / 914400:.2f}" past right edge'
                    )
                if y + cy > slide_height + 50000:
                    out_of_bounds.append(
                        f'Slide {slide_num}: element extends {(y + cy - slide_height) / 914400:.2f}" past bottom edge'
                    )
                if x < -50000:
                    out_of_bounds.append(
                        f'Slide {slide_num}: element starts {abs(x) / 914400:.2f}" past left edge'
                    )
                if y < -50000:
                    out_of_bounds.append(
                        f'Slide {slide_num}: element starts {abs(y) / 914400:.2f}" past top edge'
                    )

    if not out_of_bounds:
        return ValidationResult(
            "Boundaries",
            True,
            f"{checked} positioned element(s), all within slide boundaries",
            examined=checked,
        )
    else:
        return ValidationResult(
            "Boundaries",
            False,
            f"{len(out_of_bounds)} element(s) outside slide boundaries",
            out_of_bounds[:10],
        )


CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"

# A data label drawn on top of its own mark rather than beside it.
_INSIDE_CHART_TAGS = {"doughnutChart", "pieChart", "pie3DChart", "ofPieChart"}
_INSIDE_LABEL_POS = {"ctr", "inEnd", "inBase"}

# WCAG AA failures the NBG brand mandates. Each is listed with its measured
# ratio on every run and counted apart from the verdict, because the honest
# alternatives are a validator that lies or one that blocks every branded build.
#   #939793 Medium Gray is specified for page numbers (10pt) and cover dates
#   (14pt) by brand-system/colors.md, generation-methods.md and layouts.md. On
#   white it measures 2.96:1 against a 4.5:1 floor. Delete this entry to turn
#   those runs back into hard failures; nothing else has to change.
BRAND_CONTRAST_EXCEPTIONS = {
    "939793": "Medium Gray, brand-mandated for page numbers and cover dates",
}


def _solid_fill_color(elem) -> str | None:
    """The srgbClr of `elem`'s own solidFill. None for noFill, theme colors, absent."""
    if elem is None:
        return None
    fill = elem.find(f"{{{NAMESPACES['a']}}}solidFill")
    if fill is None:
        return None
    srgb = fill.find(f"{{{NAMESPACES['a']}}}srgbClr")
    if srgb is None:
        return None
    return str(srgb.get("val", "")).upper() or None


def _slide_background(root) -> str:
    """The slide's own background fill, defaulting to white.

    python-pptx writes `p:bg/p:bgPr/a:solidFill`. The old check read `p:bgClr`,
    which python-pptx never emits, so it never resolved a background at all.
    """
    color = _solid_fill_color(root.find(f".//{{{NAMESPACES['p']}}}bgPr"))
    if color:
        return color
    bg_clr = root.find(f".//{{{NAMESPACES['p']}}}bgClr")
    if bg_clr is not None:
        srgb = bg_clr.find(f".//{{{NAMESPACES['a']}}}srgbClr")
        if srgb is not None:
            return str(srgb.get("val", "FFFFFF")).upper()
    return "FFFFFF"


def _run_style(rpr):
    """(color, size_pt, bold) from an a:rPr or a:defRPr. color None if unresolvable."""
    sz = rpr.get("sz")
    return _solid_fill_color(rpr), (int(sz) / 100 if sz else None), rpr.get("b") == "1"


def _first_run_style(tx_pr):
    """The run style of a chart text-property block, or None."""
    if tx_pr is None:
        return None
    props = _run_props(tx_pr)
    return _run_style(props[0]) if props else None


def _chart_to_slide_bg(unpacked_dir: Path) -> dict[str, str]:
    """chart stem -> background of the slide that references it."""
    out: dict[str, str] = {}
    slides_dir = unpacked_dir / "ppt" / "slides"
    rels_dir = slides_dir / "_rels"
    if not rels_dir.exists():
        return out
    rel_tag = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
    for rels_file in rels_dir.glob("slide*.xml.rels"):
        slide_file = slides_dir / rels_file.name[: -len(".rels")]
        if not slide_file.exists():
            continue
        background = _slide_background(ET.parse(slide_file).getroot())
        for rel in ET.parse(rels_file).getroot().findall(f".//{rel_tag}"):
            if "charts/chart" in rel.get("Target", ""):
                out[Path(rel.get("Target", "")).stem] = background
    return out


def _chart_label_rows(chart_file: Path, outside_bg: str) -> list:
    """(style, background, where) for every measurable data label in one chart."""
    root = ET.parse(chart_file).getroot()
    rows = []
    for plot_area in root.findall(f".//{{{CHART_NS}}}plotArea"):
        for plot in plot_area:
            tag = plot.tag.split("}")[-1]
            if not tag.endswith("Chart"):
                continue
            grouping = plot.find(f"{{{CHART_NS}}}grouping")
            inside_default = tag in _INSIDE_CHART_TAGS or (
                grouping is not None and grouping.get("val") in ("stacked", "percentStacked")
            )

            def _inside(holder, default=inside_default):
                pos = holder.find(f"{{{CHART_NS}}}dLblPos")
                return pos.get("val") in _INSIDE_LABEL_POS if pos is not None else default

            for ser in plot.findall(f"{{{CHART_NS}}}ser"):
                ser_fill = _solid_fill_color(ser.find(f"{{{CHART_NS}}}spPr"))
                point_fill = {}
                for dpt in ser.findall(f"{{{CHART_NS}}}dPt"):
                    idx = dpt.find(f"{{{CHART_NS}}}idx")
                    fill = _solid_fill_color(dpt.find(f"{{{CHART_NS}}}spPr"))
                    if idx is not None and fill:
                        point_fill[idx.get("val")] = fill

                dlbls = ser.find(f"{{{CHART_NS}}}dLbls")
                if dlbls is None:
                    continue

                for dlbl in dlbls.findall(f"{{{CHART_NS}}}dLbl"):
                    if dlbl.find(f"{{{CHART_NS}}}delete") is not None:
                        continue
                    style = _first_run_style(dlbl.find(f"{{{CHART_NS}}}txPr"))
                    if style is None:
                        continue
                    idx_el = dlbl.find(f"{{{CHART_NS}}}idx")
                    idx = idx_el.get("val") if idx_el is not None else None
                    bg = (point_fill.get(idx) or ser_fill) if _inside(dlbl) else outside_bg
                    rows.append((style, bg, f"{chart_file.stem} label idx {idx}"))

                series_style = _first_run_style(dlbls.find(f"{{{CHART_NS}}}txPr"))
                if series_style is not None:
                    bg = ser_fill if _inside(dlbls) else outside_bg
                    rows.append((series_style, bg, f"{chart_file.stem} series labels"))
    return rows


def check_color_contrast(unpacked_dir: Path) -> ValidationResult:
    """Measure WCAG contrast for every text run against the fill behind it.

    The previous version computed no ratio at all. It tested membership in two
    hardcoded color sets, read only `p:bgClr` (which python-pptx never writes),
    walked `a:rPr` (which nbg_build never writes), and its light-on-light branch
    was a bare `pass` that found the defect and threw it away.

    Background resolution is the nearest ancestor fill, then the slide
    background, then white. Chart data labels are measured against the series or
    data-point fill when the label sits on the mark (doughnut, pie, stacked bar,
    or an explicit inside `c:dLblPos`), and against the slide background when it
    sits outside. A run whose color is a theme reference cannot be resolved to a
    hex value; those are counted and reported, never counted as passes.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Contrast", False, "No slides folder found")

    issues: list[str] = []
    waived: list[str] = []
    examined = 0
    unresolved = 0

    def measure(style, background, where):
        nonlocal examined, unresolved
        color, size, bold = style
        if not color or not background:
            unresolved += 1
            return
        examined += 1
        # An unsized run inherits from the theme; assume body text, the strictest.
        need = min_ratio(size if size is not None else 12, bold)
        ratio = contrast_ratio(color, background)
        if ratio >= need:
            return
        line = (
            f"{where}: #{color} on #{background} is {ratio:.2f}:1 "
            f"(needs {need}:1 at {size or 12}pt{' bold' if bold else ''})"
        )
        if color in BRAND_CONTRAST_EXCEPTIONS:
            waived.append(f"{line} [{BRAND_CONTRAST_EXCEPTIONS[color]}]")
        else:
            issues.append(line)

    for slide_file in sorted(slides_dir.glob("slide*.xml")):
        slide_num = _slide_num(slide_file.name)
        root = ET.parse(slide_file).getroot()
        slide_bg = _slide_background(root)

        for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
            background = _solid_fill_color(sp.find(f"{{{NAMESPACES['p']}}}spPr")) or slide_bg
            for rpr in _run_props(sp):
                measure(_run_style(rpr), background, f"Slide {slide_num}")

        # Table cells live under a:tc, not p:sp, and carry their own fill.
        for tc in root.findall(f".//{{{NAMESPACES['a']}}}tc"):
            background = _solid_fill_color(tc.find(f"{{{NAMESPACES['a']}}}tcPr")) or slide_bg
            for rpr in _run_props(tc):
                measure(_run_style(rpr), background, f"Slide {slide_num} table cell")

    charts_dir = unpacked_dir / "ppt" / "charts"
    if charts_dir.exists():
        chart_bg = _chart_to_slide_bg(unpacked_dir)
        for chart_file in sorted(charts_dir.glob("chart*.xml")):
            outside_bg = chart_bg.get(chart_file.stem, "FFFFFF")
            for style, background, where in _chart_label_rows(chart_file, outside_bg):
                measure(style, background, where)

    notes = []
    if waived:
        notes.append(f"{len(waived)} brand-mandated exception(s)")
    if unresolved:
        notes.append(f"{unresolved} run(s) with no resolvable color or background")
    suffix = f"; {', '.join(notes)}" if notes else ""

    if issues:
        return ValidationResult(
            "Contrast",
            False,
            f"{len(issues)} of {examined} measured run(s) below WCAG AA{suffix}",
            issues[:10] + waived[:3],
            examined=examined,
        )
    return ValidationResult(
        "Contrast",
        True,
        f"{examined} run(s) measured, all clear WCAG AA{suffix}",
        waived[:5],
        examined=examined,
    )


def check_decorative_elements(unpacked_dir: Path) -> ValidationResult:
    """Check for unwanted decorative elements (ellipses, complex shapes)."""
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Decorative", False, "No slides folder found")

    # Shapes that are typically decorative
    decorative_shapes = {
        "ellipse",
        "oval",
        "triangle",
        "star",
        "heart",
        "moon",
        "cloud",
    }

    found_decorations = []
    checked = 0

    for slide_file in sorted(slides_dir.glob("slide*.xml")):
        slide_num = _slide_num(slide_file.name)
        tree = ET.parse(slide_file)
        root = tree.getroot()

        # Check preset geometry shapes
        for prstGeom in root.findall(".//{{{}}}prstGeom".format(NAMESPACES["a"])):
            checked += 1
            shape_type = prstGeom.get("prst", "").lower()
            if shape_type in decorative_shapes:
                found_decorations.append(f"Slide {slide_num}: {shape_type} shape found")

    if not found_decorations:
        return ValidationResult(
            "Decorative",
            True,
            f"{checked} preset shape(s), none decorative",
            examined=checked,
        )
    else:
        return ValidationResult(
            "Decorative",
            False,
            f"{len(found_decorations)} decorative element(s) found (may affect clean design)",
            found_decorations[:10],
        )


def check_pie_charts(unpacked_dir: Path) -> ValidationResult:
    """Check that no pie charts are used (should be doughnut instead)."""
    charts_dir = unpacked_dir / "ppt" / "charts"

    if not charts_dir.exists():
        return ValidationResult("Chart Types", True, "No charts in presentation", examined=0)

    pie_charts_found = []
    doughnut_charts_found = 0
    charts_seen = 0

    for chart_file in sorted(charts_dir.glob("chart*.xml")):
        charts_seen += 1
        chart_name = chart_file.stem
        tree = ET.parse(chart_file)
        root = tree.getroot()

        # Check for pie charts
        pie_elems = root.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/chart}pieChart"
        )
        if pie_elems:
            pie_charts_found.append(f"{chart_name}: pieChart found (use doughnutChart instead)")

        # Count doughnut charts (good)
        doughnut_elems = root.findall(
            ".//{http://schemas.openxmlformats.org/drawingml/2006/chart}doughnutChart"
        )
        doughnut_charts_found += len(doughnut_elems)

    if pie_charts_found:
        return ValidationResult(
            "Chart Types",
            False,
            f"{len(pie_charts_found)} pie chart(s) found (NBG requires doughnut charts)",
            pie_charts_found,
        )
    elif doughnut_charts_found > 0:
        return ValidationResult(
            "Chart Types",
            True,
            f"{doughnut_charts_found} doughnut chart(s) of {charts_seen} (correct)",
            examined=charts_seen,
        )
    else:
        return ValidationResult(
            "Chart Types",
            True,
            f"{charts_seen} chart(s), no pie/doughnut",
            examined=charts_seen,
        )


def check_thank_you_slides(unpacked_dir: Path) -> ValidationResult:
    """Check for any "Thank You" or similar closing text on slides."""
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Thank You Check", False, "No slides folder found")

    # Phrases to look for (case-insensitive)
    forbidden_phrases = [
        "thank you",
        "thanks",
        "any questions",
        "q&a",
        "questions?",
        "thank-you",
        "thankyou",
        "grazie",
        "merci",
        "danke",
        "ευχαριστώ",
        "ευχαριστουμε",
        "ερωτησεις",  # Greek
    ]

    found_issues = []

    for slide_file in sorted(slides_dir.glob("slide*.xml")):
        slide_num = _slide_num(slide_file.name)
        tree = ET.parse(slide_file)
        root = tree.getroot()

        text_elements = root.findall(".//{{{}}}t".format(NAMESPACES["a"]))
        text_content = " ".join(t.text or "" for t in text_elements).strip().lower()

        for phrase in forbidden_phrases:
            if phrase in text_content:
                found_issues.append(f'Slide {slide_num}: contains "{phrase}"')
                break

    if not found_issues:
        scanned = len(list(slides_dir.glob("slide*.xml")))
        return ValidationResult(
            "Thank You Check",
            True,
            f'{scanned} slide(s) scanned, no "Thank You" text (correct)',
            examined=scanned,
        )
    else:
        return ValidationResult(
            "Thank You Check",
            False,
            f'{len(found_issues)} slide(s) with "Thank You" or similar (use plain back cover)',
            found_issues,
        )


def check_text_margins(unpacked_dir: Path) -> ValidationResult:
    """Check that text boxes use zero margins (NBG requirement)."""
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Text Margins", False, "No slides folder found")

    # NBG requirement: all text boxes should have margin: 0
    # In OOXML: lIns, tIns, rIns, bIns should be 0 or very small

    non_zero_margins = []
    checked = 0

    for slide_file in sorted(slides_dir.glob("slide*.xml")):
        slide_num = _slide_num(slide_file.name)
        tree = ET.parse(slide_file)
        root = tree.getroot()

        for sp in root.findall(".//{{{}}}sp".format(NAMESPACES["p"])):
            bodyPr = sp.find(".//{{{}}}bodyPr".format(NAMESPACES["a"]))
            if bodyPr is None:
                continue
            checked += 1

            # Skip shapes with solid fills (bumper pills, cards), they use
            # intentional padding for visual alignment inside the shape
            spPr = sp.find(".//{{{}}}spPr".format(NAMESPACES["p"]))
            if (
                spPr is not None
                and spPr.find(".//{{{}}}solidFill".format(NAMESPACES["a"])) is not None
            ):
                continue

            lIns = int(bodyPr.get("lIns", "91440"))
            rIns = int(bodyPr.get("rIns", "91440"))

            # If any margin is > 50000 EMU (~0.05 inch), flag it
            if lIns > 50000 or rIns > 50000:
                non_zero_margins.append(f"Slide {slide_num}: text box has non-zero margins")
                break

    total_slides = len(list(slides_dir.glob("slide*.xml")))

    if not non_zero_margins:
        return ValidationResult(
            "Text Margins",
            True,
            f"{checked} text box(es), all with zero margins",
            examined=checked,
        )
    elif len(non_zero_margins) < total_slides / 2:
        return ValidationResult(
            "Text Margins",
            True,
            f"{len(non_zero_margins)} slide(s) have default margins (minor issue)",
            non_zero_margins[:3],
            examined=checked,
        )
    else:
        return ValidationResult(
            "Text Margins",
            False,
            f"{len(non_zero_margins)} slide(s) with non-zero margins",
            non_zero_margins[:5],
        )


def check_back_cover(unpacked_dir: Path) -> ValidationResult:
    """Check if presentation ends with a back cover slide."""
    slides_dir = unpacked_dir / "ppt" / "slides"

    if not slides_dir.exists():
        return ValidationResult("Back Cover", False, "No slides folder found")

    # Sort numerically, not alphabetically (slide10.xml > slide2.xml)
    slide_files = sorted(slides_dir.glob("slide*.xml"), key=lambda x: int(_slide_num(x.name)))
    if not slide_files:
        return ValidationResult("Back Cover", False, "No slides found")

    last_slide = slide_files[-1]
    tree = ET.parse(last_slide)
    root = tree.getroot()

    # Check if last slide has minimal text (typical back cover)
    text_elements = root.findall(".//{{{}}}t".format(NAMESPACES["a"]))
    text_content = " ".join(t.text or "" for t in text_elements).strip().lower()

    # Back cover should have minimal or no text (just logo)
    if len(text_content) < 50 and "thank you" not in text_content:
        return ValidationResult(
            "Back Cover",
            True,
            "Last slide appears to be a plain back cover",
            examined=1,
        )
    elif "thank you" in text_content:
        return ValidationResult(
            "Back Cover",
            False,
            'Last slide contains "Thank You" (use plain back cover instead)',
        )
    else:
        return ValidationResult(
            "Back Cover",
            False,
            f"Last slide has significant text ({len(text_content)} chars)",
        )


def _is_footer_logo(x: int, y: int, cx: int, cy: int) -> bool:
    """True if a picture is one of the two NBG footer logo placements.

    Geometry mirrors LOGO_SMALL and LOGO_LARGE in nbg_build.py. Matched on all
    four values rather than size alone, so a genuine content image that happens
    to be logo-sized is still flagged when it runs into the footer.
    """
    EMU = 914400
    TOL = int(0.05 * EMU)
    placements = (
        (0.374, 7.071, 0.822, 0.236),  # LOGO_SMALL: content slides
        (0.374, 6.271, 2.191, 0.630),  # LOGO_LARGE: cover and divider slides
    )
    return any(
        abs(x - int(px * EMU)) <= TOL
        and abs(y - int(py * EMU)) <= TOL
        and abs(cx - int(pw * EMU)) <= TOL
        and abs(cy - int(ph * EMU)) <= TOL
        for px, py, pw, ph in placements
    )


def check_content_safe_zones(unpacked_dir: Path) -> ValidationResult:
    """Check that content elements respect NBG safe zones.

    Zones (in inches):
      Title zone:   0.0"  – 1.1"   (bumper pill, slide title)
      Content area: 1.1"  – 6.85"  (body text, charts, tables, images)
      Footer zone:  6.85" – 7.5"   (logo, page number, no content here)
      Left margin:  0.374"
      Right margin: 12.956" (13.33" - 0.374")

    The two margins are the settled gutter and its mirror. They were 0.37 and
    12.96 here while nbg_build placed its logos at 0.374, so the validator and
    the builder disagreed by 0.004"; nothing failed, because a deck built at the
    real gutter sits inside the stated boundary. brand-system/dimensions.md is
    the single home for both values.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Safe Zones", False, "No slides folder found")

    EMU_PER_INCH = 914400

    # Safe zone boundaries in EMUs. NOTE: these four are bare expression
    # statements whose values are discarded, and the first two are recomputed
    # below as TITLE_Y_MAX and FOOTER_Y_MIN. They are kept, and kept correct, so
    # that anyone who wires them up does not inherit a stale gutter.
    int(1.1 * EMU_PER_INCH)  # 1005840
    int(6.85 * EMU_PER_INCH)  # 6263640
    int(0.374 * EMU_PER_INCH)  # 341986
    int(12.956 * EMU_PER_INCH)  # 11847053

    # Tolerance: ~0.05" = 45720 EMU
    TOLERANCE = 45720

    # Elements in the title zone or footer zone are expected (titles, logos, page nums)
    # We only flag content elements that straddle zone boundaries or sit in the footer zone
    TITLE_Y_MAX = int(1.1 * EMU_PER_INCH)
    FOOTER_Y_MIN = int(6.85 * EMU_PER_INCH)

    violations = []
    total_slides = 0
    checked = 0

    # Count total slides to identify cover (first) and back cover (last)
    all_slide_files = sorted(slides_dir.glob("slide*.xml"), key=lambda x: int(_slide_num(x.name)))
    total_slide_count = len(all_slide_files)

    for slide_file in all_slide_files:
        slide_num = _slide_num(slide_file.name)
        slide_index = int(slide_num)
        total_slides += 1

        # Skip cover (first) and back cover (last), logos in footer zone are expected
        if slide_index == 1 or slide_index == total_slide_count:
            continue

        tree = ET.parse(slide_file)
        root = tree.getroot()

        # Get all shape transforms
        for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
            xfrm = sp.find(f".//{{{NAMESPACES['a']}}}xfrm")
            if xfrm is None:
                continue

            off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
            ext = xfrm.find(f"{{{NAMESPACES['a']}}}ext")
            if off is None or ext is None:
                continue

            y = int(off.get("y", 0))
            cy = int(ext.get("cy", 0))
            bottom_edge = y + cy
            checked += 1

            # Skip elements that are clearly in the title zone (titles, bumpers)
            if y < TITLE_Y_MAX and bottom_edge <= TITLE_Y_MAX + TOLERANCE:
                continue

            # Skip very small elements (likely logos, page numbers, decorative dots)
            if cy < int(0.3 * EMU_PER_INCH):
                continue

            # Check: content element extends into footer zone
            if bottom_edge > FOOTER_Y_MIN + TOLERANCE:
                overflow_inches = (bottom_edge - FOOTER_Y_MIN) / EMU_PER_INCH
                violations.append(
                    f'Slide {slide_num}: element bottom edge at {bottom_edge / EMU_PER_INCH:.2f}" '
                    f'(extends {overflow_inches:.2f}" into footer zone, max 6.85")'
                )

        # Also check picture elements
        for pic in root.findall(f".//{{{NAMESPACES['p']}}}pic"):
            xfrm = pic.find(f".//{{{NAMESPACES['a']}}}xfrm")
            if xfrm is None:
                continue

            off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
            ext = xfrm.find(f"{{{NAMESPACES['a']}}}ext")
            if off is None or ext is None:
                continue

            x = int(off.get("x", 0))
            y = int(off.get("y", 0))
            cx = int(ext.get("cx", 0))
            cy = int(ext.get("cy", 0))
            bottom_edge = y + cy
            checked += 1

            # The footer zone is where the logo BELONGS (see this function's
            # docstring), so a logo sitting in it is not a violation. The old
            # test for that was `cy < 0.5"`, a size heuristic tuned on the small
            # 0.236" logo that never saw the large one: at 2.191 x 0.630 from
            # y=6.271 its bottom edge lands at 6.90", so every divider slide
            # reported a 0.05" overflow and all three shipped examples failed
            # this check. Match the two footer logo footprints by geometry
            # instead, which cannot drift with the artwork's aspect ratio.
            if _is_footer_logo(x, y, cx, cy):
                continue

            if bottom_edge > FOOTER_Y_MIN + TOLERANCE:
                overflow_inches = (bottom_edge - FOOTER_Y_MIN) / EMU_PER_INCH
                violations.append(
                    f'Slide {slide_num}: image bottom edge at {bottom_edge / EMU_PER_INCH:.2f}" '
                    f'(extends {overflow_inches:.2f}" into footer zone, max 6.85")'
                )

    if not violations:
        return ValidationResult(
            "Safe Zones",
            True,
            f"{checked} element(s) across {total_slides} slides, all within safe zones",
            examined=checked,
        )
    else:
        return ValidationResult(
            "Safe Zones",
            False,
            f"{len(violations)} safe zone violation(s) found",
            violations[:10],
        )


BUMPER_PILL_MIN_SIZE = 900  # 9pt, the documented chrome exception below the floor


def _is_bumper_pill(sp) -> bool:
    """True for the bumper/eyebrow pill, the one element allowed under the floor.

    presentation-style-guide.md Standard #11: "One element sits below the floor
    and stays there, because it is chrome rather than content: the bumper /
    eyebrow pill at 9pt." Matched on geometry and fill, mirroring
    _add_bumper_pill in nbg_build.py, so the allowance cannot spread to ordinary
    9pt body text somewhere else on the slide.
    """
    prst = sp.find(f".//{{{NAMESPACES['a']}}}prstGeom")
    if prst is None or prst.get("prst") != "roundRect":
        return False
    if _solid_fill_color(sp.find(f"{{{NAMESPACES['p']}}}spPr")) != "007B85":
        return False
    xfrm = sp.find(f".//{{{NAMESPACES['a']}}}xfrm")
    if xfrm is None:
        return False
    off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
    ext = xfrm.find(f"{{{NAMESPACES['a']}}}ext")
    if off is None or ext is None:
        return False
    emu, tol = 914400, int(0.05 * 914400)
    return (
        abs(int(off.get("y", 0)) - int(0.35 * emu)) <= tol
        and abs(int(ext.get("cy", 0)) - int(0.3 * emu)) <= tol
    )


def check_font_sizes(unpacked_dir: Path) -> ValidationResult:
    """Check that all text meets minimum font size thresholds.

    Minimums:
      - Body text, bullets, labels, table cells: 10pt (1000 hundredths-pt)
      - Footnotes/sources: 8pt (800 hundredths-pt), only exception
      - Page numbers: 9pt (900 hundredths-pt)
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Font Sizes", False, "No slides folder found")

    # In OOXML, font size is in hundredths of a point (sz="1100" = 11pt)
    MIN_BODY_SIZE = 1000  # 10pt, absolute floor for visible text
    MIN_FOOTNOTE_SIZE = 800  # 8pt, only for footnotes/sources

    violations = []
    all_sizes = set()
    sized_runs = 0

    for slide_file in sorted(slides_dir.glob("slide*.xml")):
        slide_num = _slide_num(slide_file.name)
        tree = ET.parse(slide_file)
        root = tree.getroot()

        for rPr in _run_props(root):
            sz = rPr.get("sz")
            if sz is None:
                continue

            sz_int = int(sz)
            pt_size = sz_int / 100
            all_sizes.add(pt_size)
            sized_runs += 1

            # Check if this is a footnote-sized text (8-9pt is OK for sources)
            # We allow 8pt+ for very small text if it's the minority
            if sz_int < MIN_BODY_SIZE:
                # Check if parent text is likely a footnote (small text near bottom)
                # by checking the parent shape position
                parent_sp = None
                for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
                    if rPr in sp.iter():
                        parent_sp = sp
                        break

                if (
                    parent_sp is not None
                    and sz_int >= BUMPER_PILL_MIN_SIZE
                    and _is_bumper_pill(parent_sp)
                ):
                    continue  # documented chrome exception, not body text

                is_footnote = False
                if parent_sp is not None:
                    xfrm = parent_sp.find(f".//{{{NAMESPACES['a']}}}xfrm")
                    if xfrm is not None:
                        off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
                        if off is not None:
                            y_pos = int(off.get("y", 0))
                            # Footnotes are typically near the bottom (y > 5.5")
                            if y_pos > int(5.5 * 914400):
                                is_footnote = True

                if is_footnote and sz_int >= MIN_FOOTNOTE_SIZE:
                    continue  # Footnote at 8-9pt is acceptable

                if sz_int < MIN_FOOTNOTE_SIZE:
                    violations.append(
                        f"Slide {slide_num}: text at {pt_size}pt (below 8pt absolute minimum)"
                    )
                elif not is_footnote:
                    violations.append(
                        f"Slide {slide_num}: body text at {pt_size}pt "
                        f"(minimum 10pt for non-footnote text)"
                    )

    sizes_str = ", ".join(f"{s}pt" for s in sorted(all_sizes))

    if not violations:
        return ValidationResult(
            "Font Sizes",
            True,
            f"{sized_runs} sized run(s) all meet minimum sizes. Sizes used: {sizes_str}",
            examined=sized_runs,
        )
    else:
        # Deduplicate similar violations per slide
        unique = list(dict.fromkeys(violations))
        return ValidationResult(
            "Font Sizes",
            False,
            f"{len(unique)} font size violation(s) found",
            unique[:10],
        )


def check_content_spacing(unpacked_dir: Path) -> ValidationResult:
    """Check that content elements have adequate spacing from the title.

    Title is at y=0.5", h=0.4" → bottom edge = 0.9"
    First content should start at y ≥ 1.05" (minimum 0.15" gap from title bottom)

    A bumper pill (1.3" x 0.3" at y=0.35") shifts the title down to y=0.75", so
    on those slides the title bottom is 1.15" and content starts at 1.3". The
    pill sits above the title and is never itself the first content.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Content Spacing", False, "No slides folder found")

    EMU_PER_INCH = 914400

    TITLE_HEIGHT = int(0.4 * EMU_PER_INCH)
    # Minimum gap = 0.15" = 137160 EMU
    MIN_GAP = int(0.15 * EMU_PER_INCH)
    TOLERANCE = int(0.1 * EMU_PER_INCH)
    BUMPER_Y = int(0.35 * EMU_PER_INCH)
    BUMPER_CY = int(0.3 * EMU_PER_INCH)

    all_slide_files = sorted(slides_dir.glob("slide*.xml"), key=lambda x: int(_slide_num(x.name)))
    total_slide_count = len(all_slide_files)

    violations = []
    checked = 0

    for slide_file in all_slide_files:
        slide_num_int = int(_slide_num(slide_file.name))

        # Skip cover (first) and back cover (last)
        if slide_num_int == 1 or slide_num_int == total_slide_count:
            continue

        tree = ET.parse(slide_file)
        root = tree.getroot()

        boxes = []
        for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
            xfrm = sp.find(f".//{{{NAMESPACES['a']}}}xfrm")
            if xfrm is None:
                continue

            off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
            ext = xfrm.find(f"{{{NAMESPACES['a']}}}ext")
            if off is None or ext is None:
                continue

            boxes.append((int(off.get("y", 0)), int(ext.get("cy", 0))))

        def _is_bumper(y, cy):
            return abs(y - BUMPER_Y) < TOLERANCE and abs(cy - BUMPER_CY) < TOLERANCE

        # A bumper pill shifts the whole header block down by 0.25".
        has_bumper = any(_is_bumper(y, cy) for y, cy in boxes)
        title_y = int((0.75 if has_bumper else 0.5) * EMU_PER_INCH)
        title_bottom = title_y + TITLE_HEIGHT
        min_content_y = title_bottom + MIN_GAP

        # Find all content element Y positions (skip title itself and logo/page number)
        content_tops = []

        for y, cy in boxes:
            # Skip the bumper pill: it sits above the title, not below it
            if has_bumper and _is_bumper(y, cy):
                continue

            # Skip the title itself
            if abs(y - title_y) < TOLERANCE:
                continue

            # Skip very small elements (logos, page numbers)
            if cy < int(0.2 * EMU_PER_INCH):
                continue

            # Skip elements in the footer zone
            if y > int(6.5 * EMU_PER_INCH):
                continue

            content_tops.append(y)

        if content_tops:
            checked += 1
            first_content_y = min(content_tops)
            gap_inches = (first_content_y - title_bottom) / EMU_PER_INCH

            if first_content_y < min_content_y:
                violations.append(
                    f'Slide {slide_num_int}: first content at {first_content_y / EMU_PER_INCH:.2f}" '
                    f'(only {gap_inches:.2f}" gap from title bottom, need ≥0.15")'
                )

    if not violations:
        return ValidationResult(
            "Content Spacing",
            True,
            f"{checked} slide(s) with body content, all adequately spaced below the title",
            examined=checked,
        )
    else:
        return ValidationResult(
            "Content Spacing",
            False,
            f"{len(violations)} spacing issue(s) found",
            violations[:10],
        )


def check_title_overflow(unpacked_dir: Path) -> ValidationResult:
    """Check that slide titles fit in a single line.

    At 22pt Aptos in 12.59" width, roughly 85 chars fit.
    At 24pt Aptos, roughly 75 chars fit.
    We use 80 chars as the safe maximum for single-line titles.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Title Length", False, "No slides folder found")

    MAX_TITLE_CHARS = 80  # Safe single-line limit at 22-24pt Aptos in 12.59" width

    all_slide_files = sorted(slides_dir.glob("slide*.xml"), key=lambda x: int(_slide_num(x.name)))
    total_slide_count = len(all_slide_files)

    violations = []
    titles_found = 0

    for slide_file in all_slide_files:
        slide_num_int = int(_slide_num(slide_file.name))

        # Skip cover (first) and back cover (last)
        if slide_num_int == 1 or slide_num_int == total_slide_count:
            continue

        tree = ET.parse(slide_file)
        root = tree.getroot()

        # Find the title text box, typically the first shape at y~0.5" with large font
        for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
            xfrm = sp.find(f".//{{{NAMESPACES['a']}}}xfrm")
            if xfrm is None:
                continue

            off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
            if off is None:
                continue

            y = int(off.get("y", 0))

            # Title is at y ~ 0.5" (457200 EMU), or 0.75" (685800 EMU) when a
            # bumper pill pushes the header block down. Only the first was
            # matched, so every bumper slide, which is most of them, was skipped.
            if min(abs(y - 457200), abs(y - 685800)) > 100000:  # Not the title
                continue

            # Check font size to confirm it's a title (≥ 20pt = 2000 hundredths)
            rPrs = _run_props(sp)
            is_title = False
            for rPr in rPrs:
                sz = rPr.get("sz")
                if sz and int(sz) >= 2000:
                    is_title = True
                    break

            if not is_title:
                continue

            titles_found += 1

            # Get the title text
            texts = [t.text for t in sp.findall(f".//{{{NAMESPACES['a']}}}t") if t.text]
            title_text = " ".join(texts)

            if len(title_text) > MAX_TITLE_CHARS:
                violations.append(
                    f"Slide {slide_num_int}: title is {len(title_text)} chars "
                    f"(max {MAX_TITLE_CHARS} for single line): "
                    f'"{title_text[:60]}..."'
                )
            break  # Only check the first title-like element

    if not violations:
        return ValidationResult(
            "Title Length",
            True,
            f"{titles_found} title(s) all fit within the {MAX_TITLE_CHARS}-char single-line limit",
            examined=titles_found,
        )
    else:
        return ValidationResult(
            "Title Length",
            False,
            f"{len(violations)} title(s) may overflow to second line",
            violations,
        )


def check_competitor_banks(unpacked_dir: Path) -> ValidationResult:
    """Check that competitor bank references use correct brand colors and logos.

    When systemic Greek banks appear in charts/tables, they must use their
    official brand colors and logos (from assets/bank-logos/).

    Brand colors (resynced 2026-05-24 from Pillar repo):
      NBG:        007B85 (Teal)
      Eurobank:   DC2646 (Red), was CA2029
      Piraeus:    FFC02D (Yellow), was FDB913
      Alpha Bank: 0D488B (Blue), was 02509C

    Logo files:
      nbg.png, eurobank.png, piraeus-bank.png, alpha-bank.png
    """
    BANK_BRAND = {
        "NBG": {"color": "007B85", "logo": "nbg.png"},
        "Eurobank": {"color": "DC2646", "logo": "eurobank.png"},
        "Piraeus": {"color": "FFC02D", "logo": "piraeus-bank.png"},
        "Alpha": {"color": "0D488B", "logo": "alpha-bank.png"},
    }
    # Aliases for matching
    BANK_ALIASES = {
        "alpha bank": "Alpha",
        "alpha": "Alpha",
        "piraeus bank": "Piraeus",
        "piraeus": "Piraeus",
        "eurobank": "Eurobank",
        "nbg": "NBG",
        "national bank": "NBG",
    }

    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Bank Branding", True, "No slides folder found")

    # Detect which bank names appear in the presentation
    banks_found = set()
    for slide_file in slides_dir.glob("slide*.xml"):
        tree = ET.parse(slide_file)
        root = tree.getroot()
        all_text = " ".join(
            t.text.strip()
            for t in root.findall(f".//{{{NAMESPACES['a']}}}t")
            if t.text and t.text.strip()
        ).lower()
        for alias, bank_key in BANK_ALIASES.items():
            if alias in all_text:
                banks_found.add(bank_key)

    # If fewer than 2 banks mentioned, this isn't a bank comparison slide
    if len(banks_found) < 2:
        return ValidationResult(
            "Bank Branding",
            True,
            f"{len(banks_found)} bank name(s) found, so no multi-bank comparison to check",
            examined=0,
        )

    violations = []

    # Check 1: Are the bank brand colors present in the PPTX?
    # Look in slides AND in embedded charts, peer colors typically live in
    # the chart XML when applied as per-data-point fills via <c:dPt>.
    all_colors = set()
    for slide_file in slides_dir.glob("slide*.xml"):
        tree = ET.parse(slide_file)
        root = tree.getroot()
        for srgb in root.findall(f".//{{{NAMESPACES['a']}}}srgbClr"):
            val = srgb.get("val", "").upper()
            if val:
                all_colors.add(val)
    charts_dir = unpacked_dir / "ppt" / "charts"
    if charts_dir.exists():
        for chart_file in charts_dir.glob("chart*.xml"):
            tree = ET.parse(chart_file)
            root = tree.getroot()
            for srgb in root.findall(f".//{{{NAMESPACES['a']}}}srgbClr"):
                val = srgb.get("val", "").upper()
                if val:
                    all_colors.add(val)

    for bank_key in banks_found:
        expected_color = BANK_BRAND[bank_key]["color"].upper()
        if expected_color not in all_colors:
            violations.append(
                f"{bank_key}: brand color #{expected_color} not found in presentation "
                f"(must use official brand color in charts/tables)"
            )

    # Check 2: Are bank logos present in the media folder?
    media_dir = unpacked_dir / "ppt" / "media"
    media_files = set()
    if media_dir.exists():
        media_files = {f.name.lower() for f in media_dir.iterdir()}

    # Also check embedded base64 images by looking at relationship targets
    for bank_key in banks_found:
        expected_logo = BANK_BRAND[bank_key]["logo"].lower()
        # Check if any media file contains the bank logo name pattern
        logo_found = any(expected_logo.replace(".png", "") in fname for fname in media_files)
        # PptxGenJS embeds base64 images as imageN.png, check slide rels
        # for image count as a heuristic (logos add extra images)
        if not logo_found:
            # Count total images, if banks are mentioned and logos aren't
            # embedded as named files, check if enough images exist
            # (4 bank logos = 4 extra images beyond NBG logos)
            image_count = len([f for f in media_files if f.endswith(".png")])
            # We expect at least: NBG logo + back cover logo + 4 bank logos = 6+
            if image_count < len(banks_found) + 2:
                violations.append(
                    f"{bank_key}: logo ({expected_logo}) not found in media files "
                    f"(bank comparison slides must include bank logos)"
                )

    if not violations:
        return ValidationResult(
            "Bank Branding",
            True,
            f"Bank comparison detected ({', '.join(sorted(banks_found))}): "
            f"all brand colors and logos present",
            examined=len(banks_found),
        )
    else:
        return ValidationResult(
            "Bank Branding",
            False,
            f"{len(violations)} bank branding issue(s) found",
            violations,
        )


# ---------------------------------------------------------------------------
# 2026 executive-presentation standards
#
# Every check below reports how many candidates it examined, and none of them
# reports success from an empty scan, for the reason stated on ValidationResult:
# a check that cannot tell "found nothing" from "did not look" is worse than no
# check, because a human stops looking.
# ---------------------------------------------------------------------------

_EMU_PER_INCH = 914400

# nbg_build emits NO title placeholder. Every slide is created from
# `slide_layouts[6]` (blank) and every title goes down as a free text box via
# `_add_textbox`; measured on a built quarterly-report, `p:ph` occurs 0 times
# across all 11 slides. So "does this slide have a title" cannot be answered by
# looking for the built-in Title placeholder, and a check that looked for one
# would fail on 100% of decks while examining a set it never defined. Titles are
# recognised from geometry and type size instead, which is how
# check_title_overflow already recognises one.
TITLE_MIN_SIZE = 2400  # 24pt, the smallest title size nbg_build emits
TITLE_MAX_Y = int(3.5 * _EMU_PER_INCH)  # every title the builder places is above this
# Content-slide title anchors: y=0.5" bare, y=0.75" when a bumper pill pushes the
# header block down. Mirrors create_content_slide / create_chart_slide.
CONTENT_TITLE_Y = (int(0.5 * _EMU_PER_INCH), int(0.75 * _EMU_PER_INCH))
TITLE_Y_TOL = 100000
_SECTION_NUMBER = re.compile(r"^\d{1,3}$")


def _norm_text(value: str) -> str:
    """Whitespace-collapsed text, for comparing two strings a human would call equal."""
    return " ".join(value.split())


def _shape_text(elem) -> str:
    """Every `a:t` under `elem`, joined and whitespace-collapsed."""
    return _norm_text(" ".join(t.text or "" for t in elem.findall(f".//{{{NAMESPACES['a']}}}t")))


def _shape_texts(root) -> list[str]:
    """The text of each shape and each table cell on a slide, separately.

    Table cells live under `a:tc` inside a graphic frame, not under `p:sp`, so a
    walk over shapes alone misses every number in every table. Measured on the
    built quarterly-report, that walk found 3 currency amounts where the deck
    carries 11: the eight in the Card P&L table were invisible to it, which is
    the whole table and the densest numbers in the deck.
    """
    texts = []
    for holder in (f"{{{NAMESPACES['p']}}}sp", f"{{{NAMESPACES['a']}}}tc"):
        for elem in root.findall(f".//{holder}"):
            text = _shape_text(elem)
            if text:
                texts.append(text)
    return texts


def _max_run_size(sp) -> int:
    """The largest run size on a shape in hundredths of a point, 0 if unsized."""
    sizes = [int(s) for s in (rpr.get("sz") for rpr in _run_props(sp)) if s and s.isdigit()]
    return max(sizes, default=0)


def _shape_offset(sp) -> tuple[int, int] | None:
    """(x, y) of a shape's own transform, or None when it carries no transform."""
    xfrm = sp.find(f".//{{{NAMESPACES['a']}}}xfrm")
    if xfrm is None:
        return None
    off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
    if off is None:
        return None
    return int(off.get("x", 0)), int(off.get("y", 0))


def _title_candidates(root) -> list[tuple[int, int, str]]:
    """(y, x, text) for every text box on a slide that reads as a title, topmost first.

    A candidate sits in the top 3.5" and carries a run at TITLE_MIN_SIZE or
    above, which covers all four title placements nbg_build emits: the 24pt
    content title at y=0.5 or 0.75, the 32pt contents heading at 0.36, the 48pt
    cover title at 1.39, and the 48pt divider title at 2.84. A divider's 60pt
    section number matches on size and position and is dropped here, because
    "01" is a marker rather than a title (Standard #3).
    """
    out: list[tuple[int, int, str]] = []
    for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
        position = _shape_offset(sp)
        if position is None:
            continue
        x, y = position
        if y > TITLE_MAX_Y or _max_run_size(sp) < TITLE_MIN_SIZE:
            continue
        text = _shape_text(sp)
        if _SECTION_NUMBER.match(text):
            continue
        out.append((y, x, text))
    return sorted(out)


def _content_slide_title(root) -> str | None:
    """The action title of a body slide, or None when the slide is not one.

    Covers, dividers, the contents page and the back cover carry titles at other
    y positions and are therefore excluded by construction: an action-title rule
    must not be applied to a section divider, whose title is a noun phrase by
    Standard #3.
    """
    for sp in root.findall(f".//{{{NAMESPACES['p']}}}sp"):
        position = _shape_offset(sp)
        if position is None:
            continue
        _, y = position
        if min(abs(y - anchor) for anchor in CONTENT_TITLE_Y) > TITLE_Y_TOL:
            continue
        if _max_run_size(sp) < TITLE_MIN_SIZE:
            continue
        text = _shape_text(sp)
        if text and not _SECTION_NUMBER.match(text):
            return text
    return None


def _sorted_slides(slides_dir: Path) -> list[Path]:
    """Slide files in deck order: slide10.xml after slide2.xml, not before it."""
    return sorted(slides_dir.glob("slide*.xml"), key=lambda p: int(_slide_num(p.name)))


def check_slide_titles(unpacked_dir: Path) -> ValidationResult:
    """Every slide carries a title, and no two slides carry the same one.

    A deck whose slides repeat a title cannot be discussed ("go back to Digital
    Banking Performance" is ambiguous), cannot be cross-referenced in minutes,
    and reads as a copy-paste artifact.

    What counts as a title is decided by geometry and type size, not by the
    built-in Title placeholder: nbg_build never uses one. See TITLE_MIN_SIZE
    above for the measurement behind that.

    A slide with no text at all is exempt and counted separately rather than
    failed. That is the back cover, which by Standard #19 is one centred oval
    emblem and nothing else. A slide that does carry text and has no title-sized
    box in its top 3.5" is a genuine missing title and fails.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Slide Titles", False, "No slides folder found")

    problems: list[str] = []
    seen: dict[str, str] = {}
    examined = 0
    textless = 0

    for slide_file in _sorted_slides(slides_dir):
        slide_num = _slide_num(slide_file.name)
        root = ET.parse(slide_file).getroot()

        if not _shape_text(root):
            textless += 1
            continue

        examined += 1
        candidates = _title_candidates(root)
        if not candidates:
            problems.append(
                f"Slide {slide_num}: no title "
                f'(no text at {TITLE_MIN_SIZE / 100:.0f}pt or larger in the top 3.5")'
            )
            continue

        title = candidates[0][2]
        if not title:
            problems.append(f"Slide {slide_num}: title text box is present but empty")
            continue

        key = title.casefold()
        if key in seen:
            problems.append(
                f'Slide {slide_num}: title "{title}" duplicates slide {seen[key]}; '
                f"disambiguate it (add the segment, period or part number)"
            )
        else:
            seen[key] = slide_num

    exempt = f", {textless} text-free slide(s) exempt" if textless else ""
    if problems:
        return ValidationResult(
            "Slide Titles",
            False,
            f"{len(problems)} title problem(s) across {examined} titled slide(s){exempt}",
            problems[:10],
        )
    return ValidationResult(
        "Slide Titles",
        True,
        f"{examined} slide(s) titled, all present and unique{exempt}",
        examined=examined,
    )


# A source annotation names where a number came from and when it was true.
# Greek decks write "Πηγή:" / "Πηγές:"; both are accepted.
SOURCE_PREFIX = re.compile(r"^\s*(?:sources?|πηγ(?:ή|ές))\s*[:\-–]", re.IGNORECASE)
# The as-of half. A four-digit year is the weakest form that still dates a
# figure; an ISO or slashed date also counts. "Source: NBG MIS" alone does not.
SOURCE_AS_OF = re.compile(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b")


def check_exhibit_sources(unpacked_dir: Path) -> ValidationResult:
    """Every slide carrying a chart or a table carries a dated source line.

    An unsourced number in a board pack is the defect the whole pipeline exists
    to prevent. A figure with no provenance cannot be re-derived, cannot be
    challenged in the room, and cannot be defended to a supervisor afterwards. A
    source without an as-of date is only half of one: "Source: NBG MIS" does not
    say whether the number is this quarter's or last year's.

    Exhibits are found structurally, not by shape name: a chart is a `c:chart`
    reference inside the slide's graphic frame, a table is an `a:tbl`.

    SEVERITY IS WARNING, and this is the one place in this file where that is a
    statement about the repo rather than about the rule. The rule deserves to
    block. It cannot yet, for two reasons that both sit outside this tool: none
    of the three shipped examples in `plugins/decks/examples/` carries source
    data, and nbg_build has no renderer for a `content.source` field. An error
    here would fail every build in the repo with no in-tree fix, and a check
    that cannot be satisfied gets switched off rather than obeyed. Add the field
    to the examples and the renderer to the builder, then change `severity`
    below to "error".
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Exhibit Sources", False, "No slides folder found")

    problems: list[str] = []
    examined = 0

    for slide_file in _sorted_slides(slides_dir):
        slide_num = _slide_num(slide_file.name)
        root = ET.parse(slide_file).getroot()

        kinds = []
        if root.find(f".//{{{CHART_NS}}}chart") is not None:
            kinds.append("chart")
        if root.find(f".//{{{NAMESPACES['a']}}}tbl") is not None:
            kinds.append("table")
        if not kinds:
            continue

        examined += 1
        what = " and ".join(kinds)
        sources = [t for t in _shape_texts(root) if SOURCE_PREFIX.match(t)]
        if not sources:
            problems.append(f"Slide {slide_num}: carries a {what} and no source line")
        elif not any(SOURCE_AS_OF.search(t) for t in sources):
            problems.append(
                f'Slide {slide_num}: source line "{sources[0][:60]}" carries no as-of date'
            )

    if problems:
        return ValidationResult(
            "Exhibit Sources",
            False,
            f"{len(problems)} of {examined} exhibit slide(s) unsourced or undated",
            problems[:10],
            severity="warning",
        )
    return ValidationResult(
        "Exhibit Sources",
        True,
        f"{examined} exhibit slide(s), all carrying a dated source line",
        examined=examined,
        severity="warning",
    )


# The third NBG logo placement, alongside the two _is_footer_logo already knows.
LOGO_BACK_PLACEMENT = (5.44, 2.98, 2.45, 1.54)  # nbg_build.LOGO_BACK, the back-cover emblem

ALT_TEXT_HOSTS = (
    ("pic", "nvPicPr"),
    ("graphicFrame", "nvGraphicFramePr"),
    ("grpSp", "nvGrpSpPr"),
)
# "Image of a bar chart" tells a screen-reader user what they already know from
# the role, and nothing about the content.
ALT_TEXT_LEAD_IN = re.compile(
    r"^\s*(?:image|picture|graphic|photo|screenshot)\s+of\b", re.IGNORECASE
)
# python-pptx seeds `descr` with the source filename (measured: every logo on
# every shipped example carries descr="nbg-logo-gr.png"), and PowerPoint seeds
# the shape autoname. Neither describes anything, and a bare emptiness test
# passes on both, which is exactly the "found nothing / did not look" failure.
ALT_TEXT_PLACEHOLDER = re.compile(
    r"^\s*(?:[\w .\-]+\.(?:png|jpe?g|gif|svg|bmp|tiff?|emf|wmf)"
    r"|(?:image|picture|chart|table|group|object|diagram|graphic|shape)\s*\d*)\s*$",
    re.IGNORECASE,
)


def _is_brand_chrome_picture(x: int, y: int, cx: int, cy: int) -> bool:
    """True for the three NBG logo placements, which are decorative under WCAG.

    The same wordmark sits on every slide. Requiring alt text on it makes a
    screen reader announce "National Bank of Greece logo" once per slide and
    conveys nothing; WCAG puts decorative images on empty alt text, so these are
    exempt rather than required. Geometry reuses _is_footer_logo for the two
    footer placements and adds the centred back-cover emblem.
    """
    if _is_footer_logo(x, y, cx, cy):
        return True
    px, py, pw, ph = LOGO_BACK_PLACEMENT
    tol = int(0.05 * _EMU_PER_INCH)
    return (
        abs(x - int(px * _EMU_PER_INCH)) <= tol
        and abs(y - int(py * _EMU_PER_INCH)) <= tol
        and abs(cx - int(pw * _EMU_PER_INCH)) <= tol
        and abs(cy - int(ph * _EMU_PER_INCH)) <= tol
    )


def _picture_box(pic) -> tuple[int, int, int, int]:
    """(x, y, cx, cy) of a picture, zeros when it carries no transform."""
    xfrm = pic.find(f".//{{{NAMESPACES['a']}}}xfrm")
    if xfrm is None:
        return 0, 0, 0, 0
    off = xfrm.find(f"{{{NAMESPACES['a']}}}off")
    ext = xfrm.find(f"{{{NAMESPACES['a']}}}ext")
    if off is None or ext is None:
        return 0, 0, 0, 0
    return (
        int(off.get("x", 0)),
        int(off.get("y", 0)),
        int(ext.get("cx", 0)),
        int(ext.get("cy", 0)),
    )


def check_alt_text(unpacked_dir: Path) -> ValidationResult:
    """Every non-decorative picture, chart, table and group carries real alt text.

    OOXML carries alt text as the `descr` attribute on the shape's non-visual
    properties (`p:cNvPr`). EN 301 549 V3.2.1 adopts WCAG 2.1 AA for non-web
    documents, and Standard #22 records that liability for an inaccessible
    deliverable sits with the bank, not with any tooling vendor.

    Four things are rejected, because each of them passes a naive emptiness test
    while telling a screen-reader user nothing:
      - missing or blank `descr`
      - a filename or a shape autoname ("nbg-logo-gr.png", "Chart 3"), which is
        what python-pptx and PowerPoint respectively write by default
      - a lead-in of "image of" / "picture of" / "graphic of"
      - text identical to a caption already visible on the slide, which a screen
        reader then reads out twice

    The three NBG logo placements are exempt as decorative brand chrome and are
    counted separately, so the exemption is visible in the report rather than
    silently shrinking the candidate set.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Alt Text", False, "No slides folder found")

    problems: list[str] = []
    examined = 0
    decorative = 0

    for slide_file in _sorted_slides(slides_dir):
        slide_num = _slide_num(slide_file.name)
        root = ET.parse(slide_file).getroot()
        captions = {t.casefold() for t in _shape_texts(root)}

        for tag, holder in ALT_TEXT_HOSTS:
            for shape in root.findall(f".//{{{NAMESPACES['p']}}}{tag}"):
                if tag == "pic" and _is_brand_chrome_picture(*_picture_box(shape)):
                    decorative += 1
                    continue

                nv = shape.find(f"{{{NAMESPACES['p']}}}{holder}/{{{NAMESPACES['p']}}}cNvPr")
                name = (nv.get("name", "") if nv is not None else "") or tag
                examined += 1
                alt = _norm_text(nv.get("descr", "") if nv is not None else "")

                if not alt:
                    problems.append(f"Slide {slide_num}: {name} has no alt text")
                elif ALT_TEXT_PLACEHOLDER.match(alt):
                    problems.append(
                        f'Slide {slide_num}: {name} alt text "{alt}" is a filename or '
                        f"an autoname, not a description"
                    )
                elif ALT_TEXT_LEAD_IN.match(alt):
                    problems.append(
                        f'Slide {slide_num}: {name} alt text "{alt[:50]}" opens with '
                        f'"image of"; describe the content, not the medium'
                    )
                elif alt.casefold() in captions:
                    problems.append(
                        f'Slide {slide_num}: {name} alt text "{alt[:50]}" repeats a '
                        f"caption already on the slide"
                    )

    chrome = f", {decorative} brand logo(s) exempt as decorative" if decorative else ""
    if problems:
        return ValidationResult(
            "Alt Text",
            False,
            f"{len(problems)} of {examined} object(s) without usable alt text{chrome}",
            problems[:10],
        )
    return ValidationResult(
        "Alt Text",
        True,
        f"{examined} object(s) carry descriptive alt text{chrome}",
        examined=examined,
    )


# A bar or column encodes value as length, so a value axis that does not start
# at zero misstates every ratio the reader takes off the chart. The empirical
# work on truncated axes is consistent that annotating the break does not repair
# the misreading, so there is no "marked truncation" exemption here. A line
# chart encodes value as position and may legitimately start elsewhere.
BAR_CHART_TAGS = {"barChart", "bar3DChart"}


def check_zero_baseline(unpacked_dir: Path) -> ValidationResult:
    """Bar and column charts start their value axis at zero.

    The axis minimum lives at `c:valAx/c:scaling/c:min`. Absent, the axis is
    automatic, and PowerPoint auto-scales a bar chart from zero: absent is a
    pass, and every chart nbg_build writes is in that state (measured:
    `<c:scaling><c:orientation val="minMax"/></c:scaling>`, no `c:min`).

    Read by parsing, never by searching the text. The substring "c:min" also
    occurs inside `c:minorTickMark` and `c:minorGridlines`, which every chart
    this builder emits carries, so a grep reports a minimum on charts that have
    none: probed on both shipped chart parts, a text search claims a hit on 100%
    of them where the parsed answer is 0%.

    A chart that mixes bar and line plots is held to the bar rule, the stricter
    of the two.
    """
    charts_dir = unpacked_dir / "ppt" / "charts"
    if not charts_dir.exists():
        return ValidationResult("Zero Baseline", True, "No charts in presentation", examined=0)

    problems: list[str] = []
    examined = 0
    non_bar = 0

    for chart_file in sorted(charts_dir.glob("chart*.xml")):
        root = ET.parse(chart_file).getroot()
        plot_tags = set()
        for plot_area in root.findall(f".//{{{CHART_NS}}}plotArea"):
            for plot in plot_area:
                tag = plot.tag.split("}")[-1]
                if tag.endswith("Chart"):
                    plot_tags.add(tag)

        bar_kinds = plot_tags & BAR_CHART_TAGS
        if not bar_kinds:
            non_bar += 1
            continue

        for val_ax in root.findall(f".//{{{CHART_NS}}}valAx"):
            examined += 1
            minimum = val_ax.find(f"{{{CHART_NS}}}scaling/{{{CHART_NS}}}min")
            if minimum is None:
                continue
            raw = minimum.get("val", "0")
            try:
                value = float(raw)
            except ValueError:
                problems.append(f"{chart_file.stem}: value axis c:min is not a number ({raw!r})")
                continue
            if value != 0:
                problems.append(
                    f"{chart_file.stem}: {'/'.join(sorted(bar_kinds))} value axis starts "
                    f"at {value:g}, not zero; a truncated bar misstates every ratio on "
                    f"the chart"
                )

    skipped_note = f", {non_bar} non-bar chart(s) not subject to the rule" if non_bar else ""
    if problems:
        return ValidationResult(
            "Zero Baseline",
            False,
            f"{len(problems)} truncated value axis/axes of {examined} examined{skipped_note}",
            problems[:10],
        )
    return ValidationResult(
        "Zero Baseline",
        True,
        f"{examined} bar/column value axis/axes, all based at zero{skipped_note}",
        examined=examined,
    )


# A currency marker is required, which is what keeps a year, a page number, a
# headcount and a percentage out of the sample.
CURRENCY_AMOUNT = re.compile(
    r"(?:EUR|USD|GBP|CHF|€|\$|£)\s?(\d[\d,.]*?)\s?(bn|b|m|k)?(?![\w%.,])",
    re.IGNORECASE,
)
_SUFFIX_CANON = {"k": "K", "m": "M", "b": "B", "bn": "B"}
RAW_AMOUNT_MIN_DIGITS = 4  # "EUR 1,250,000" is a raw form; "EUR 500" is just a small number


def _currency_forms(text: str) -> list[tuple[str, int, str]]:
    """(unit, decimal places, the literal) for every currency amount in `text`."""
    found = []
    for match in CURRENCY_AMOUNT.finditer(text):
        number, suffix = match.group(1), match.group(2)
        unit = _SUFFIX_CANON.get(suffix.lower(), "") if suffix else ""
        if not unit and len(number.replace(",", "").replace(".", "")) < RAW_AMOUNT_MIN_DIGITS:
            continue
        decimals = len(number.split(".")[-1]) if "." in number else 0
        found.append((unit or "raw", decimals, _norm_text(match.group(0))))
    return found


def check_number_formatting(unpacked_dir: Path) -> ValidationResult:
    """One currency notation per deck, and one decimal precision per unit.

    Two rules, both deck-global, because the reader compares across slides:

    1. Raw digits and abbreviated amounts must not coexist. "EUR 1,250,000" on
       one slide and "EUR 2.3M" on the next describe the same kind of quantity
       in two notations and make the reader convert in their head.
    2. Within one suffix, decimal precision must be consistent. "EUR 42M" beside
       "EUR 42.0M" beside "EUR 41.75M" reads as three different confidence
       levels about the same kind of figure.

    What this deliberately does NOT flag, narrowing "one unit scale per deck":
    the mere coexistence of K, M and B. A deck carrying EUR 12.5B of volume and
    EUR 42M of fee income is describing quantities three orders of magnitude
    apart, and forcing one scale would print "EUR 0.042B". Both shipped examples
    that use currency are in exactly that state and are correct. Flagging it
    would have produced a check people switch off.

    A currency marker (EUR, USD, GBP, CHF or a symbol) is required for a token
    to enter the sample at all, which is what keeps years, page numbers,
    headcounts, ratios and percentages out of it.

    SEVERITY IS WARNING. Rule 2 in particular reads intent from typography, and
    a deliberately mixed-precision table (a rate to two places beside a total to
    none) is legitimate. It should reach a human, not block a build.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Number Formats", False, "No slides folder found")

    forms: list[tuple[str, str, int, str]] = []  # slide, unit, decimals, literal
    for slide_file in _sorted_slides(slides_dir):
        slide_num = _slide_num(slide_file.name)
        root = ET.parse(slide_file).getroot()
        for text in _shape_texts(root):
            for unit, decimals, literal in _currency_forms(text):
                forms.append((slide_num, unit, decimals, literal))

    problems: list[str] = []
    units = {unit for _, unit, _, _ in forms}

    if "raw" in units and units - {"raw"}:
        raw_example = next(f"slide {s}: {lit}" for s, u, _, lit in forms if u == "raw")
        suffixed = next(f"slide {s}: {lit}" for s, u, _, lit in forms if u != "raw")
        problems.append(
            f"deck mixes raw and abbreviated currency notation ({raw_example}, {suffixed}); "
            f"pick one and use it throughout"
        )

    for unit in sorted(units - {"raw"}):
        widths = {d for _, u, d, _ in forms if u == unit}
        if len(widths) > 1:
            samples = sorted({lit for _, u, _, lit in forms if u == unit})[:4]
            problems.append(
                f"{unit} amounts use {len(widths)} different decimal precisions "
                f"({', '.join(str(w) for w in sorted(widths))} places): {', '.join(samples)}"
            )

    if problems:
        return ValidationResult(
            "Number Formats",
            False,
            f"{len(problems)} formatting inconsistency/ies across {len(forms)} currency amount(s)",
            problems[:10],
            severity="warning",
        )
    return ValidationResult(
        "Number Formats",
        True,
        f"{len(forms)} currency amount(s), consistent notation and precision",
        examined=len(forms),
        severity="warning",
    )


# Edit this list without reading the function. Two families: the register tells
# (words that survive no edit and signal a model wrote the slide), and the
# citation-shaped claims that assert evidence without naming any. "Robust" alone
# in a technical sentence is fine, which is why the check fires on clustering
# rather than on a single hit; flagging a lone hit trains people to ignore the
# check, and a check people ignore is worse than none.
AI_SLOP_TERMS = (
    "in today's fast-paced world",
    "unprecedented change",
    "in the era of digital transformation",
    "leverage",
    "seamless",
    "robust",
    "unlock",
    "elevate",
    "delve",
    "tapestry",
    "studies show",
    "research indicates",
    "experts agree",
)
AI_SLOP_CLUSTER = 2  # distinct terms on one slide before it is a finding
_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "´": "'"})
_AI_SLOP_PATTERNS = tuple(
    (term, re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)) for term in AI_SLOP_TERMS
)


def check_ai_slop(unpacked_dir: Path) -> ValidationResult:
    """Slide text is free of clustered AI register tells and unsourced claims.

    Fires when AI_SLOP_CLUSTER or more DISTINCT terms from the lexicon land on
    one slide. Distinct, not total: a slide that says "robust" twice has used
    one word twice, which is a style preference; a slide that says "leverage"
    and "seamless" has a register problem.

    Matching is word-bounded and apostrophe-normalised, so a curly apostrophe in
    "in today's fast-paced world" does not slip the phrase past the check.

    "Digital transformation" on its own is not in the lexicon and must not be:
    it is the literal name of a strategy programme in this bank, and one shipped
    example is titled with it. The listed phrase is the throat-clearing frame
    "in the era of digital transformation".
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("AI Slop", False, "No slides folder found")

    problems: list[str] = []
    examined = 0

    for slide_file in _sorted_slides(slides_dir):
        slide_num = _slide_num(slide_file.name)
        root = ET.parse(slide_file).getroot()
        text = _shape_text(root).translate(_APOSTROPHES)
        if not text:
            continue

        examined += 1
        hits = [term for term, pattern in _AI_SLOP_PATTERNS if pattern.search(text)]
        if len(hits) >= AI_SLOP_CLUSTER:
            problems.append(
                f"Slide {slide_num}: {len(hits)} lexicon terms clustered "
                f"({', '.join(repr(h) for h in hits)})"
            )

    if problems:
        return ValidationResult(
            "AI Slop",
            False,
            f"{len(problems)} of {examined} slide(s) cluster {AI_SLOP_CLUSTER}+ AI-register terms",
            problems[:10],
        )
    return ValidationResult(
        "AI Slop",
        True,
        f"{examined} slide(s) scanned against {len(AI_SLOP_TERMS)} lexicon terms, "
        f"none clustering {AI_SLOP_CLUSTER}+",
        examined=examined,
    )


# Whole-title matches only. A topic label names the subject; an action title
# states the finding. "Q3 Results" tells the room where it is, not what happened.
TOPIC_LABEL_TITLES = frozenset(
    {
        "agenda",
        "appendix",
        "background",
        "conclusion",
        "conclusions",
        "context",
        "executive summary",
        "financials",
        "introduction",
        "key takeaways",
        "next steps",
        "objectives",
        "our approach",
        "overview",
        "recommendations",
        "results",
        "summary",
        "takeaways",
        "the ask",
        "timeline",
    }
)
TOPIC_LABEL_PATTERN = re.compile(
    r"^(?:q[1-4]|h[12]|fy)\s*(?:20\d{2})?\s*"
    r"(?:results|performance|review|update|summary|numbers|highlights)$",
    re.IGNORECASE,
)
ACTION_TITLE_MAX_WORDS = 15


def check_action_titles(unpacked_dir: Path) -> ValidationResult:
    """A body slide's title asserts a finding rather than naming a topic.

    Two precise rules, both applied to the title of a content slide only:
      - the whole title is a known topic label ("Overview", "Q3 Results")
      - the title runs past ACTION_TITLE_MAX_WORDS words, at which point it is a
        paragraph and no longer an assertion the eye takes in one pass

    Covers, dividers, the contents page and the back cover are excluded by
    construction, because _content_slide_title matches only the two content
    title anchors. That matters: a divider title is a noun phrase by Standard
    #3, and running an action-title rule over one would fail every deck.

    SEVERITY IS WARNING, and the reason is in this repo's own style guide. Part
    2 of presentation-style-guide.md records the user shortening "Transforming
    NBG's Digital Investment Offering" to "NBG Digital Investment Offering", so
    preferring the noun phrase, on a deck they reviewed. A rule the owner has
    already overruled once in writing must report, not block.

    The two rules here are narrow enough not to fire on that title, nor on any
    title in the three shipped examples, including "Total investment of EUR 120M
    over 3 years with 2.5x ROI", which is a perfectly good executive title with
    no finite verb. Verb detection was the obvious implementation and was
    rejected for exactly that reason.
    """
    slides_dir = unpacked_dir / "ppt" / "slides"
    if not slides_dir.exists():
        return ValidationResult("Action Titles", False, "No slides folder found")

    problems: list[str] = []
    examined = 0

    for slide_file in _sorted_slides(slides_dir):
        slide_num = _slide_num(slide_file.name)
        title = _content_slide_title(ET.parse(slide_file).getroot())
        if title is None:
            continue

        examined += 1
        stripped = title.rstrip(".:").strip()
        words = len(title.split())

        if stripped.casefold() in TOPIC_LABEL_TITLES or TOPIC_LABEL_PATTERN.match(stripped):
            problems.append(
                f'Slide {slide_num}: "{title}" is a topic label, not an assertion; '
                f"say what the slide found"
            )
        elif words > ACTION_TITLE_MAX_WORDS:
            problems.append(
                f"Slide {slide_num}: title runs {words} words "
                f'(max {ACTION_TITLE_MAX_WORDS}): "{title[:70]}"'
            )

    if problems:
        return ValidationResult(
            "Action Titles",
            False,
            f"{len(problems)} of {examined} content title(s) are topic labels or overlong",
            problems[:10],
            severity="warning",
        )
    return ValidationResult(
        "Action Titles",
        True,
        f"{examined} content title(s), all assertions within {ACTION_TITLE_MAX_WORDS} words",
        examined=examined,
        severity="warning",
    )


def validate_presentation(pptx_path: str) -> list[ValidationResult]:
    """Run all validation checks on a presentation."""
    pptx_file = Path(pptx_path).expanduser()

    if not pptx_file.exists():
        raise FileNotFoundError(f"Presentation not found: {pptx_file}")

    results = []

    with tempfile.TemporaryDirectory() as temp_dir:
        unpacked_dir = Path(temp_dir) / "unpacked"

        with zipfile.ZipFile(pptx_file, "r") as zf:
            zf.extractall(unpacked_dir)

        # Run all checks
        results.append(check_slide_count(unpacked_dir))
        results.append(check_dimensions(unpacked_dir))
        results.append(check_colors(unpacked_dir))
        results.append(check_fonts(unpacked_dir))
        results.append(check_logo_present(unpacked_dir))
        results.append(check_back_cover(unpacked_dir))
        # Quality control checks
        results.append(check_element_boundaries(unpacked_dir))
        results.append(check_color_contrast(unpacked_dir))
        results.append(check_decorative_elements(unpacked_dir))
        # NBG-specific checks
        results.append(check_pie_charts(unpacked_dir))
        results.append(check_thank_you_slides(unpacked_dir))
        results.append(check_text_margins(unpacked_dir))
        # Safe zone checks
        results.append(check_content_safe_zones(unpacked_dir))
        # Composition checks
        results.append(check_font_sizes(unpacked_dir))
        results.append(check_content_spacing(unpacked_dir))
        results.append(check_title_overflow(unpacked_dir))
        # Bank branding checks
        results.append(check_competitor_banks(unpacked_dir))
        # 2026 executive-presentation standards
        results.append(check_slide_titles(unpacked_dir))
        results.append(check_exhibit_sources(unpacked_dir))
        results.append(check_alt_text(unpacked_dir))
        results.append(check_zero_baseline(unpacked_dir))
        results.append(check_number_formatting(unpacked_dir))
        results.append(check_ai_slop(unpacked_dir))
        results.append(check_action_titles(unpacked_dir))

    return results


def print_results(results: list, pptx_path: str):
    """Print validation results."""
    print("\nNBG Brand Validation Report")
    print(f"{'=' * 50}")
    print(f"File: {pptx_path}")
    print(f"{'=' * 50}\n")

    passed = 0
    failed = 0
    skipped = 0
    warned = 0

    for result in results:
        if result.skipped:
            status = "\033[93m○\033[0m"
        elif result.passed:
            status = "\033[92m✓\033[0m"
        elif result.warned:
            status = "\033[93m!\033[0m"
        else:
            status = "\033[91m✗\033[0m"
        print(f"{status} {result.name}: {result.message}")

        if result.details:
            for detail in result.details[:5]:  # Show max 5 details
                print(f"    - {detail}")
            if len(result.details) > 5:
                print(f"    ... and {len(result.details) - 5} more")

        if result.skipped:
            skipped += 1
        elif result.passed:
            passed += 1
        elif result.warned:
            warned += 1
        else:
            failed += 1

    print(f"\n{'=' * 50}")
    print(
        f"Summary: {passed} passed, {failed} failed, {warned} warning(s), "
        f"{skipped} examined nothing"
    )

    if failed == 0 and warned == 0 and skipped == 0:
        print("\033[92mAll checks passed! Presentation follows NBG guidelines.\033[0m")
    elif failed == 0:
        notes = []
        if warned:
            notes.append(f"{warned} warning(s) marked ! do not block, but are real findings")
        if skipped:
            notes.append(f"{skipped} check(s) marked with a circle examined nothing")
        print(f"\033[93mNo blocking failures; {', and '.join(notes)}.\033[0m")
    else:
        print("\033[93mSome checks failed. Review and fix before publishing.\033[0m")

    print(f"{'=' * 50}\n")

    return failed == 0


def main():
    if len(sys.argv) < 2:
        print("NBG Brand Validation Tool")
        print("=" * 40)
        print("\nUsage: python nbg_validate.py <presentation.pptx>")
        print("\nValidates presentations against NBG brand guidelines.")
        sys.exit(1)

    pptx_path = sys.argv[1]

    # Exit codes are a contract with nbg_build.py: 0 clean, 1 a check failed,
    # 2 the validator could not finish. Without the split, a crash and a failed
    # check were indistinguishable and the build swallowed both.
    try:
        results = validate_presentation(pptx_path)
        success = print_results(results, pptx_path)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\033[91mValidator error: {e}\033[0m", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
