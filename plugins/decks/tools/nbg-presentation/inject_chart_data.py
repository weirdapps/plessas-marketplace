#!/usr/bin/env python3
"""
NBG Chart Data Injection Tool

Injects real data into chart placeholders in NBG presentations.
Works by editing the OOXML chart XML files directly.

Usage:
    python inject_chart_data.py presentation.pptx chart_config.json output.pptx

chart_config.json format:
{
    "charts": [
        {
            "slide": 0,
            "chart_index": 0,
            "type": "doughnut",
            "title": "Market Share",
            "data": {
                "labels": ["NBG", "Eurobank", "Piraeus", "Alpha", "Others"],
                "values": [27, 23, 21, 19, 10]
            }
        },
        {
            "slide": 1,
            "chart_index": 0,
            "type": "bar",
            "title": "Digital Adoption",
            "data": {
                "categories": ["NBG", "Eurobank", "Alpha", "Piraeus"],
                "series": [
                    {"name": "2024", "values": [70, 68, 65, 62]},
                    {"name": "2025", "values": [75, 72, 70, 68]}
                ]
            }
        }
    ]
}
"""

import json
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree.ElementTree import (  # nosemgrep: python.lang.security.use-defused-xml.use-defused-xml - only non-parsing helpers, all parse() calls use defusedxml
    SubElement,
    register_namespace,
)

import defusedxml.ElementTree as ET

# NBG Chart Colors (without # prefix)
NBG_CHART_COLORS = [
    "00ADBF",  # Cyan (primary)
    "003841",  # Dark Teal
    "007B85",  # NBG Teal
    "939793",  # Medium Gray
    "BEC1BE",  # Light Gray
    "00DFF8",  # Bright Cyan
]

# XML Namespaces
NAMESPACES = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

# Register namespaces
for prefix, uri in NAMESPACES.items():
    register_namespace(prefix, uri)


def find_chart_files(unpacked_dir: Path) -> dict[str, Path]:
    """Find all chart XML files and map them to slides."""
    charts: dict[str, Path] = {}
    charts_dir = unpacked_dir / "ppt" / "charts"

    if not charts_dir.exists():
        return charts

    for chart_file in charts_dir.glob("chart*.xml"):
        chart_name = chart_file.stem
        charts[chart_name] = chart_file

    return charts


def find_slide_charts(unpacked_dir: Path, slide_num: int) -> list:
    """Find chart references in a specific slide."""
    unpacked_dir / "ppt" / "slides" / f"slide{slide_num + 1}.xml"
    slide_rels = (
        unpacked_dir / "ppt" / "slides" / "_rels" / f"slide{slide_num + 1}.xml.rels"
    )

    chart_refs = []

    if slide_rels.exists():
        tree = ET.parse(slide_rels)
        root = tree.getroot()

        for rel in root.findall(
            ".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
        ):
            target = rel.get("Target", "")
            if "charts/chart" in target:
                chart_name = Path(target).stem
                chart_refs.append(chart_name)

    return chart_refs


def update_pie_chart(chart_file: Path, data: dict, title: str | None = None):
    """Update pie/doughnut chart data."""
    tree = ET.parse(chart_file)
    root = tree.getroot()

    # Find pie chart data
    for pie in root.findall(".//c:pieChart", NAMESPACES) + root.findall(
        ".//c:doughnutChart", NAMESPACES
    ):
        ser = pie.find(".//c:ser", NAMESPACES)
        if ser is None:
            continue

        # Update categories (labels)
        cat = ser.find(".//c:cat", NAMESPACES)
        if cat is not None:
            str_ref = cat.find(".//c:strRef", NAMESPACES)
            if str_ref is not None:
                str_cache = str_ref.find(".//c:strCache", NAMESPACES)
                if str_cache is not None:
                    # Clear existing points
                    for pt in str_cache.findall(".//c:pt", NAMESPACES):
                        str_cache.remove(pt)

                    # Update count
                    pt_count = str_cache.find(".//c:ptCount", NAMESPACES)
                    if pt_count is not None:
                        pt_count.set("val", str(len(data["labels"])))

                    # Add new points
                    for i, label in enumerate(data["labels"]):
                        pt = SubElement(str_cache, "{{{}}}pt".format(NAMESPACES["c"]))
                        pt.set("idx", str(i))
                        v = SubElement(pt, "{{{}}}v".format(NAMESPACES["c"]))
                        v.text = str(label)

        # Update values
        val = ser.find(".//c:val", NAMESPACES)
        if val is not None:
            num_ref = val.find(".//c:numRef", NAMESPACES)
            if num_ref is not None:
                num_cache = num_ref.find(".//c:numCache", NAMESPACES)
                if num_cache is not None:
                    # Clear existing points
                    for pt in num_cache.findall(".//c:pt", NAMESPACES):
                        num_cache.remove(pt)

                    # Update count
                    pt_count = num_cache.find(".//c:ptCount", NAMESPACES)
                    if pt_count is not None:
                        pt_count.set("val", str(len(data["values"])))

                    # Add new points
                    for i, value in enumerate(data["values"]):
                        pt = SubElement(num_cache, "{{{}}}pt".format(NAMESPACES["c"]))
                        pt.set("idx", str(i))
                        v = SubElement(pt, "{{{}}}v".format(NAMESPACES["c"]))
                        v.text = str(value)

    # Update title if provided
    if title:
        title_elem = root.find(".//c:title", NAMESPACES)
        if title_elem is not None:
            for t in title_elem.findall(".//a:t", NAMESPACES):
                t.text = title

    tree.write(chart_file, xml_declaration=True, encoding="UTF-8")


def update_bar_chart(chart_file: Path, data: dict, title: str | None = None):
    """Update bar/column chart data."""
    tree = ET.parse(chart_file)
    root = tree.getroot()

    # Find bar chart
    for bar in root.findall(".//c:barChart", NAMESPACES):
        series_list = bar.findall(".//c:ser", NAMESPACES)

        for idx, ser in enumerate(series_list):
            if idx >= len(data.get("series", [])):
                break

            series_data = data["series"][idx]

            # Update series name
            tx = ser.find(".//c:tx", NAMESPACES)
            if tx is not None:
                for v in tx.findall(".//c:v", NAMESPACES):
                    v.text = series_data.get("name", f"Series {idx + 1}")

            # Update categories
            cat = ser.find(".//c:cat", NAMESPACES)
            if cat is not None and "categories" in data:
                str_ref = cat.find(".//c:strRef", NAMESPACES)
                if str_ref is not None:
                    str_cache = str_ref.find(".//c:strCache", NAMESPACES)
                    if str_cache is not None:
                        for pt in str_cache.findall(".//c:pt", NAMESPACES):
                            str_cache.remove(pt)

                        pt_count = str_cache.find(".//c:ptCount", NAMESPACES)
                        if pt_count is not None:
                            pt_count.set("val", str(len(data["categories"])))

                        for i, cat_label in enumerate(data["categories"]):
                            pt = SubElement(
                                str_cache, "{{{}}}pt".format(NAMESPACES["c"])
                            )
                            pt.set("idx", str(i))
                            v = SubElement(pt, "{{{}}}v".format(NAMESPACES["c"]))
                            v.text = str(cat_label)

            # Update values
            val = ser.find(".//c:val", NAMESPACES)
            if val is not None:
                num_ref = val.find(".//c:numRef", NAMESPACES)
                if num_ref is not None:
                    num_cache = num_ref.find(".//c:numCache", NAMESPACES)
                    if num_cache is not None:
                        for pt in num_cache.findall(".//c:pt", NAMESPACES):
                            num_cache.remove(pt)

                        pt_count = num_cache.find(".//c:ptCount", NAMESPACES)
                        if pt_count is not None:
                            pt_count.set("val", str(len(series_data["values"])))

                        for i, value in enumerate(series_data["values"]):
                            pt = SubElement(
                                num_cache, "{{{}}}pt".format(NAMESPACES["c"])
                            )
                            pt.set("idx", str(i))
                            v = SubElement(pt, "{{{}}}v".format(NAMESPACES["c"]))
                            v.text = str(value)

    # Update title if provided
    if title:
        title_elem = root.find(".//c:title", NAMESPACES)
        if title_elem is not None:
            for t in title_elem.findall(".//a:t", NAMESPACES):
                t.text = title

    tree.write(chart_file, xml_declaration=True, encoding="UTF-8")


def update_line_chart(chart_file: Path, data: dict, title: str | None = None):
    """Update line chart data."""
    tree = ET.parse(chart_file)
    root = tree.getroot()

    for line in root.findall(".//c:lineChart", NAMESPACES):
        series_list = line.findall(".//c:ser", NAMESPACES)

        for idx, ser in enumerate(series_list):
            if idx >= len(data.get("series", [])):
                break

            series_data = data["series"][idx]

            # Update series name
            tx = ser.find(".//c:tx", NAMESPACES)
            if tx is not None:
                for v in tx.findall(".//c:v", NAMESPACES):
                    v.text = series_data.get("name", f"Series {idx + 1}")

            # Update categories
            cat = ser.find(".//c:cat", NAMESPACES)
            if cat is not None and "categories" in data:
                str_ref = cat.find(".//c:strRef", NAMESPACES)
                if str_ref is not None:
                    str_cache = str_ref.find(".//c:strCache", NAMESPACES)
                    if str_cache is not None:
                        for pt in str_cache.findall(".//c:pt", NAMESPACES):
                            str_cache.remove(pt)

                        pt_count = str_cache.find(".//c:ptCount", NAMESPACES)
                        if pt_count is not None:
                            pt_count.set("val", str(len(data["categories"])))

                        for i, cat_label in enumerate(data["categories"]):
                            pt = SubElement(
                                str_cache, "{{{}}}pt".format(NAMESPACES["c"])
                            )
                            pt.set("idx", str(i))
                            v = SubElement(pt, "{{{}}}v".format(NAMESPACES["c"]))
                            v.text = str(cat_label)

            # Update values
            val = ser.find(".//c:val", NAMESPACES)
            if val is not None:
                num_ref = val.find(".//c:numRef", NAMESPACES)
                if num_ref is not None:
                    num_cache = num_ref.find(".//c:numCache", NAMESPACES)
                    if num_cache is not None:
                        for pt in num_cache.findall(".//c:pt", NAMESPACES):
                            num_cache.remove(pt)

                        pt_count = num_cache.find(".//c:ptCount", NAMESPACES)
                        if pt_count is not None:
                            pt_count.set("val", str(len(series_data["values"])))

                        for i, value in enumerate(series_data["values"]):
                            pt = SubElement(
                                num_cache, "{{{}}}pt".format(NAMESPACES["c"])
                            )
                            pt.set("idx", str(i))
                            v = SubElement(pt, "{{{}}}v".format(NAMESPACES["c"]))
                            v.text = str(value)

    if title:
        title_elem = root.find(".//c:title", NAMESPACES)
        if title_elem is not None:
            for t in title_elem.findall(".//a:t", NAMESPACES):
                t.text = title

    tree.write(chart_file, xml_declaration=True, encoding="UTF-8")


def inject_chart_data(pptx_path: str, config_path: str, output_path: str):
    """Main function to inject chart data into presentation."""
    pptx_file = Path(pptx_path).expanduser()
    config_file = Path(config_path).expanduser()
    output_file = Path(output_path).expanduser()

    # Load configuration
    with open(config_file) as f:
        config = json.load(f)

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        unpacked_dir = temp_path / "unpacked"

        # Unpack PPTX
        with zipfile.ZipFile(pptx_file, "r") as zf:
            zf.extractall(unpacked_dir)

        # Find all charts
        all_charts = find_chart_files(unpacked_dir)

        # Process each chart configuration
        for chart_config in config.get("charts", []):
            slide_num = chart_config["slide"]
            chart_index = chart_config.get("chart_index", 0)
            chart_type = chart_config["type"]
            title = chart_config.get("title")
            data = chart_config["data"]

            # Find charts in this slide
            slide_charts = find_slide_charts(unpacked_dir, slide_num)

            if chart_index < len(slide_charts):
                chart_name = slide_charts[chart_index]
                chart_file = all_charts.get(chart_name)

                if chart_file and chart_file.exists():
                    print(
                        f"Updating {chart_type} chart on slide {slide_num + 1}: {chart_name}"
                    )

                    if chart_type in ("pie", "doughnut"):
                        update_pie_chart(chart_file, data, title)
                    elif chart_type in ("bar", "column"):
                        update_bar_chart(chart_file, data, title)
                    elif chart_type == "line":
                        update_line_chart(chart_file, data, title)
                    else:
                        print(f"  Warning: Unsupported chart type '{chart_type}'")
                else:
                    print(f"  Warning: Chart file not found for {chart_name}")
            else:
                print(
                    f"  Warning: Chart index {chart_index} not found on slide {slide_num + 1}"
                )

        # Repack PPTX
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in unpacked_dir.rglob("*"):
                if file_path.is_file():
                    arc_name = file_path.relative_to(unpacked_dir)
                    zf.write(file_path, arc_name)

    print(f"\nSaved to: {output_file}")


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python inject_chart_data.py <input.pptx> <config.json> <output.pptx>"
        )
        print("\nExample config.json:")
        print(
            json.dumps(
                {
                    "charts": [
                        {
                            "slide": 0,
                            "chart_index": 0,
                            "type": "doughnut",
                            "title": "Market Share",
                            "data": {"labels": ["A", "B", "C"], "values": [40, 35, 25]},
                        }
                    ]
                },
                indent=2,
            )
        )
        sys.exit(1)

    inject_chart_data(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
