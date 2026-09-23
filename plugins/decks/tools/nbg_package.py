#!/usr/bin/env python3
"""Package limits for a deck the decks tools open but did not write.

A .pptx is a zip, and extract, render and the validator open decks from anyone. A
crafted 406 KB file declared parts that inflate to hundreds of megabytes, and
python-pptx and lxml then allocate several times that (SECURITY-PUBLIC-2). The
check below reads only the zip's central directory, inflating nothing, and refuses
a package past these limits. Python's zipfile never inflates a member past its
declared size, so bounding the declared sizes bounds what any reader loads.

"XML" is every member that is not a known binary media type: an SVG, a .rels file
or a renamed part is parsed as XML whatever its name says, so it counts.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

MIB = 2**20
MAX_MEMBERS = 5000
MAX_PART_BYTES = 64 * MIB  # any single member
MAX_XML_PART_BYTES = 16 * MIB
MAX_XML_TOTAL_BYTES = 128 * MIB
MAX_XML_RATIO = 100  # a real deck's XML compresses 3 to 30 times; a bomb, thousands
RATIO_FLOOR_BYTES = MIB  # a smaller part is already bounded by the caps above

MEDIA_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".emf", ".wmf",
    ".mp4", ".m4v", ".mov", ".wav", ".mp3", ".bin",
}  # fmt: skip


class PackageError(ValueError):
    """The file is not a zip package, or it is one past the limits."""


def check_package(path: Path | str) -> None:
    """Raise PackageError, naming the member and the limit, when the package at path
    would make a reader allocate without bound."""
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
    except (zipfile.BadZipFile, OSError) as e:
        raise PackageError(f"{Path(path).name} is not a readable zip package ({e})") from e
    if len(infos) > MAX_MEMBERS:
        raise PackageError(f"{len(infos)} package members, over the limit of {MAX_MEMBERS}")
    xml_total = 0
    for info in infos:
        if info.is_dir():
            continue
        name, size = info.filename, info.file_size
        if size > MAX_PART_BYTES:
            raise PackageError(f"{name} inflates to {size} bytes, over {MAX_PART_BYTES // MIB} MiB")
        if Path(name).suffix.lower() in MEDIA_SUFFIXES:
            continue
        if size > MAX_XML_PART_BYTES:
            raise PackageError(
                f"{name} is {size} bytes of XML, over {MAX_XML_PART_BYTES // MIB} MiB for one part"
            )
        xml_total += size
        if xml_total > MAX_XML_TOTAL_BYTES:
            raise PackageError(f"the package holds over {MAX_XML_TOTAL_BYTES // MIB} MiB of XML")
        if size > RATIO_FLOOR_BYTES and size > MAX_XML_RATIO * max(info.compress_size, 1):
            raise PackageError(
                f"{name} compresses {size // max(info.compress_size, 1)} to 1, which only a zip "
                "bomb does"
            )
