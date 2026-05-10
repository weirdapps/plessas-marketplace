#!/usr/bin/env python3
"""
NBG Table Data Injection Tool

Injects real data into table placeholders in NBG presentations.
Works by editing the OOXML table XML in slide files.

Usage:
    python inject_table_data.py presentation.pptx table_config.json output.pptx

table_config.json format:
{
    "tables": [
        {
            "slide": 2,
            "table_index": 0,
            "data": {
                "headers": ["Metric", "NBG", "Eurobank", "Piraeus", "Alpha"],
                "rows": [
                    ["Total Assets (EUR B)", "78.5", "82.1", "75.3", "71.2"],
                    ["Deposits (EUR B)", "58.2", "52.4", "48.7", "45.1"],
                    ["CET1 Ratio (%)", "17.2%", "15.8%", "14.9%", "15.2%"],
                    ["NPL Ratio (%)", "3.8%", "5.2%", "6.1%", "5.8%"]
                ]
            },
            "highlight_column": 1
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
    Element,
    SubElement,
    register_namespace,
)

import defusedxml.ElementTree as ET

# NBG Colors (without # prefix)
NBG_COLORS = {
    "dark_teal": "003841",
    "teal": "007B85",
    "cyan": "00ADBF",
    "bright_cyan": "00DFF8",
    "white": "FFFFFF",
    "dark_text": "202020",
    "light_gray": "BEC1BE",
    "off_white": "F5F8F6",
}

# XML Namespaces
NAMESPACES = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

for prefix, uri in NAMESPACES.items():
    register_namespace(prefix, uri)


def find_tables_in_slide(slide_file: Path) -> list:
    """Find all tables in a slide and return their XML elements."""
    tree = ET.parse(slide_file)
    root = tree.getroot()

    tables = []

    # Look for graphicFrame elements containing tables
    for gf in root.findall(".//{{{}}}graphicFrame".format(NAMESPACES["p"])):
        tbl = gf.find(".//{{{}}}tbl".format(NAMESPACES["a"]))
        if tbl is not None:
            tables.append((gf, tbl, tree, slide_file))

    return tables


def update_table_cell(
    cell: Element, text: str, is_header: bool = False, highlight: bool = False
):
    """Update the text content of a table cell."""
    # Find or create the text body
    txBody = cell.find(".//{{{}}}txBody".format(NAMESPACES["a"]))
    if txBody is None:
        return

    # Find the first paragraph
    p = txBody.find(".//{{{}}}p".format(NAMESPACES["a"]))
    if p is None:
        return

    # Find or create run
    r = p.find(".//{{{}}}r".format(NAMESPACES["a"]))
    if r is None:
        r = SubElement(p, "{{{}}}r".format(NAMESPACES["a"]))

    # Find or create text element
    t = r.find(".//{{{}}}t".format(NAMESPACES["a"]))
    if t is None:
        t = SubElement(r, "{{{}}}t".format(NAMESPACES["a"]))

    t.text = text

    # Apply styling for header or highlight
    if is_header or highlight:
        rPr = r.find(".//{{{}}}rPr".format(NAMESPACES["a"]))
        if rPr is None:
            rPr = Element("{{{}}}rPr".format(NAMESPACES["a"]))
            r.insert(0, rPr)

        if is_header:
            rPr.set("b", "1")  # Bold


def update_table(table_elem: Element, data: dict, highlight_column: int | None = None):
    """Update table with new data."""
    headers = data.get("headers", [])
    rows = data.get("rows", [])

    # Find all rows in the table
    tr_elements = table_elem.findall(".//{{{}}}tr".format(NAMESPACES["a"]))

    all_data = [headers] + rows if headers else rows

    for row_idx, tr in enumerate(tr_elements):
        if row_idx >= len(all_data):
            break

        row_data = all_data[row_idx]
        tc_elements = tr.findall(".//{{{}}}tc".format(NAMESPACES["a"]))

        for col_idx, tc in enumerate(tc_elements):
            if col_idx >= len(row_data):
                break

            is_header = row_idx == 0 and headers
            highlight = highlight_column is not None and col_idx == highlight_column

            update_table_cell(tc, str(row_data[col_idx]), is_header, highlight)


def inject_table_data(pptx_path: str, config_path: str, output_path: str):
    """Main function to inject table data into presentation."""
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

        # Process each table configuration
        for table_config in config.get("tables", []):
            slide_num = table_config["slide"]
            table_index = table_config.get("table_index", 0)
            data = table_config["data"]
            highlight_column = table_config.get("highlight_column")

            slide_file = unpacked_dir / "ppt" / "slides" / f"slide{slide_num + 1}.xml"

            if not slide_file.exists():
                print(f"Warning: Slide {slide_num + 1} not found")
                continue

            tables = find_tables_in_slide(slide_file)

            if table_index < len(tables):
                gf, tbl, tree, file_path = tables[table_index]
                print(f"Updating table {table_index} on slide {slide_num + 1}")
                update_table(tbl, data, highlight_column)
                tree.write(file_path, xml_declaration=True, encoding="UTF-8")
            else:
                print(
                    f"Warning: Table index {table_index} not found on slide {slide_num + 1}"
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
            "Usage: python inject_table_data.py <input.pptx> <config.json> <output.pptx>"
        )
        print("\nExample config.json:")
        print(
            json.dumps(
                {
                    "tables": [
                        {
                            "slide": 2,
                            "table_index": 0,
                            "data": {
                                "headers": ["Metric", "Value A", "Value B"],
                                "rows": [["Row 1", "10", "20"], ["Row 2", "30", "40"]],
                            },
                            "highlight_column": 1,
                        }
                    ]
                },
                indent=2,
            )
        )
        sys.exit(1)

    inject_table_data(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
