#!/usr/bin/env python3
"""Render a deck the way a reviewer sees it: PDF, one PNG per slide, and a font check.

    decks-py render deck.pptx outdir [--dpi 110]

LibreOffice converts the deck to PDF in a throwaway profile (so a user's own
LibreOffice settings and a stale lock never interfere), pypdfium2 draws each page
to outdir/slide-NN.png (NN the deck slide it shows: a hidden slide has no page), and
pypdf reads which fonts the PDF embeds. When a typeface the deck asks for is not
among them LibreOffice substituted another face, text runs to different widths, and
any judgement about fit made from these images is unreliable: that is exit 4, not 0,
so presentation-qa can say so instead of passing a slide it cannot see properly.

stdout is one JSON object:
    {"pdf", "pngs", "slides", "deck_slides", "hidden_slides", "dpi", "fonts",
     "font_fallback", "substituted_fonts", "soffice", "warnings"[, "warning"]}
or, when nothing was rendered, {"error", "fix"}.

Exit codes: 0 rendered with every requested font embedded; 4 rendered with substituted fonts;
3 LibreOffice is not installed; 2 any other error, including a deck past
nbg_package's limits, which LibreOffice never sees.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nbg_package  # noqa: E402

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_NO_SOFFICE = 3
EXIT_FONT_FALLBACK = 4
DEFAULT_DPI = 110

SOFFICE_CANDIDATES = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/lib/libreoffice/program/soffice",
    "/usr/local/lib/libreoffice/program/soffice",
    "/opt/libreoffice/program/soffice",
    "/snap/bin/libreoffice",
]


class RenderError(Exception):
    def __init__(self, message: str, fix: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix


def find_soffice() -> str | None:
    """DECKS_SOFFICE, then PATH, then the usual install locations on each OS."""
    override = os.environ.get("DECKS_SOFFICE")
    if override:
        return override if Path(override).exists() else None
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    candidates = SOFFICE_CANDIDATES + sorted(glob.glob("/opt/libreoffice*/program/soffice"))
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def convert_to_pdf(soffice: str, deck: Path, outdir: Path, timeout: int = 300) -> Path:
    """deck -> outdir/<deck stem>.pdf with an isolated LibreOffice profile."""
    profile = Path(tempfile.mkdtemp(prefix="nbg-render-profile-"))
    try:
        cmd = [
            soffice,
            f"-env:UserInstallation={profile.as_uri()}",
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--nodefault",
            "--convert-to",
            "pdf",
            "--outdir",
            str(outdir),
            str(deck),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise RenderError(
                f"LibreOffice did not finish within {timeout}s",
                "close any LibreOffice window that is waiting on a dialog, then retry",
            ) from e
        pdf = outdir / f"{deck.stem}.pdf"
        if proc.returncode != 0 or not pdf.exists():
            detail = (proc.stderr or proc.stdout or "").strip()[:500]
            raise RenderError(
                f"LibreOffice could not convert {deck.name} (exit {proc.returncode}): {detail}",
                "open the deck in PowerPoint to confirm it is not damaged, then retry",
            )
        return pdf
    finally:
        shutil.rmtree(profile, ignore_errors=True)


MANIFEST = ".nbg-render.json"  # the files the last render wrote into its folder
_OWN_NAME = re.compile(r"slide-\d{2,}\.png|[^/\\]+\.pdf")


def _owned(outdir: Path) -> set[str]:
    """What an earlier render wrote here, by its manifest: only plain file names in
    render's own naming, so a crafted manifest cannot point it at anything else."""
    try:
        listed = json.loads((outdir / MANIFEST).read_text(encoding="utf-8")).get("files", [])
    except (OSError, ValueError, AttributeError):
        return set()
    return {n for n in listed if isinstance(n, str) and _OWN_NAME.fullmatch(n)}


def claim_outdir(outdir: Path, deck: Path) -> None:
    """Make room for this render: delete what the last render wrote, and refuse (before
    anything runs) when a file this render would write is there and render did not
    write it. SECURITY-PUBLIC-5: a render used to delete every slide-*.png in the
    folder and overwrite any <deck>.pdf already there."""
    owned = _owned(outdir)
    planned = {f"{deck.stem}.pdf"} | {
        f"slide-{i:02d}.png" for i in range(1, deck_slide_count(deck) + 1)
    }
    foreign = sorted(n for n in planned if (outdir / n).exists() and n not in owned)
    if foreign:
        raise RenderError(
            f"{outdir} already holds {', '.join(foreign)}, which render did not write",
            "render into an empty folder, or move those files: render deletes and "
            "overwrites only what it wrote itself",
        )
    for name in owned:
        (outdir / name).unlink(missing_ok=True)


def record_outdir(outdir: Path, files: list[Path]) -> None:
    (outdir / MANIFEST).write_text(json.dumps({"files": [p.name for p in files]}), encoding="utf-8")


def pdf_to_pngs(pdf: Path, outdir: Path, dpi: int, numbers: list[int] | None = None) -> list[Path]:
    """One PNG per page, named for the deck slide it shows (numbers, one per page) or,
    without that map, for the page."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf))
    try:
        paths = []
        if numbers is None or len(numbers) != len(doc):
            numbers = list(range(1, len(doc) + 1))
        for i in range(len(doc)):
            path = outdir / f"slide-{numbers[i]:02d}.png"
            if path.exists():  # claim_outdir removed render's own; this one is not
                raise RenderError(
                    f"{path} already exists and render did not write it",
                    "render into an empty folder",
                )
            page = doc[i]
            image = page.render(scale=dpi / 72).to_pil()
            image.save(path)
            paths.append(path)
        return paths
    finally:
        doc.close()


def _descriptor(font: Any) -> Any:
    descriptor = font.get("/FontDescriptor")
    if descriptor is None and "/DescendantFonts" in font:
        descendants = font["/DescendantFonts"].get_object()
        if descendants:
            descriptor = descendants[0].get_object().get("/FontDescriptor")
    return descriptor.get_object() if descriptor is not None else None


def embedded_fonts(pdf: Path) -> list[dict[str, Any]]:
    """Every font the PDF uses: its name without the subset prefix, and whether its
    program is embedded."""
    from pypdf import PdfReader

    found: dict[str, bool] = {}
    for page in PdfReader(str(pdf)).pages:
        resources = page.get("/Resources")
        fonts = resources.get_object().get("/Font") if resources is not None else None
        if fonts is None:
            continue
        for ref in fonts.get_object().values():
            font = ref.get_object()
            base = str(font.get("/BaseFont", "")).lstrip("/")
            name = base.split("+", 1)[1] if len(base) > 7 and base[6] == "+" else base
            descriptor = _descriptor(font)
            embedded = descriptor is not None and any(
                key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")
            )
            found[name] = found.get(name, False) or embedded
    return [{"name": name, "embedded": emb} for name, emb in sorted(found.items())]


def aptos_embedded(fonts: list[dict[str, Any]]) -> bool:
    return any("aptos" in f["name"].lower() and f["embedded"] for f in fonts)


_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def _xml(zf: zipfile.ZipFile, name: str) -> Any:
    from lxml import etree

    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    return etree.fromstring(zf.read(name), parser)


def requested_fonts(deck: Path) -> list[str]:
    """The typefaces the deck's text asks for: the theme's heading and body fonts,
    which every run without its own inherits, and each a:latin typeface on a slide or
    in a chart."""
    names: set[str] = set()
    with zipfile.ZipFile(deck) as zf:
        for part in zf.namelist():
            if part.startswith("ppt/theme/") and part.endswith(".xml"):
                for which in ("majorFont", "minorFont"):
                    latin = _xml(zf, part).find(f".//{_A}{which}/{_A}latin")
                    if latin is not None:
                        names.add(latin.get("typeface", ""))
            elif part.startswith(("ppt/slides/slide", "ppt/charts/chart")) and part.endswith(
                ".xml"
            ):
                names |= {el.get("typeface", "") for el in _xml(zf, part).iter(f"{_A}latin")}
    return sorted(n for n in names if n and not n.startswith("+"))


def _fold_font(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def substituted(requested: list[str], fonts: list[dict[str, Any]]) -> list[str]:
    """The requested typefaces the PDF does not embed under their own name (a subset or
    a style of it, "Aptos-Bold" or "ArialMT", counts): LibreOffice drew those in
    another face, so text widths differ from PowerPoint."""
    embedded = [_fold_font(f["name"]) for f in fonts if f["embedded"]]
    return [r for r in requested if not any(e.startswith(_fold_font(r)) for e in embedded)]


def slide_order(deck: Path) -> list[tuple[int, bool]]:
    """(deck slide number, hidden) in presentation order. LibreOffice exports no page
    for a hidden slide (p:sld show="0")."""
    with zipfile.ZipFile(deck) as zf:
        rels = {
            rel.get("Id"): rel.get("Target", "")
            for rel in _xml(zf, "ppt/_rels/presentation.xml.rels").iter(f"{_REL}Relationship")
        }
        order = []
        for number, sld_id in enumerate(_xml(zf, "ppt/presentation.xml").iter(f"{_P}sldId"), 1):
            target = rels.get(sld_id.get(_R_ID), "")
            name = "ppt/" + target.lstrip("/").removeprefix("ppt/")
            hidden = name in zf.namelist() and _xml(zf, name).get("show") in ("0", "false")
            order.append((number, hidden))
    return order


def deck_slide_count(deck: Path) -> int:
    with zipfile.ZipFile(deck) as zf:
        return sum(
            1 for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")
        )


def render(deck: Path, outdir: Path, dpi: int = DEFAULT_DPI) -> tuple[dict[str, Any], int]:
    """(summary, exit code). Raises RenderError when nothing could be rendered."""
    if not deck.is_file():
        raise RenderError(f"deck not found: {deck}", "check the path")
    try:
        nbg_package.check_package(deck)
    except nbg_package.PackageError as e:
        raise RenderError(
            f"{deck.name} was not opened: {e}",
            "render only decks you trust; rebuild this one with decks-py build",
        ) from e
    soffice = find_soffice()
    if soffice is None:
        raise RenderError(
            "LibreOffice is not installed",
            "install LibreOffice (https://www.libreoffice.org/download/) or set DECKS_SOFFICE "
            "to its soffice binary; the render-and-look QA step needs it",
        )
    outdir.mkdir(parents=True, exist_ok=True)
    claim_outdir(outdir, deck)
    pdf = convert_to_pdf(soffice, deck, outdir)
    order = slide_order(deck)
    hidden = [n for n, is_hidden in order if is_hidden]
    pngs = pdf_to_pngs(pdf, outdir, dpi, [n for n, is_hidden in order if not is_hidden])
    record_outdir(outdir, [pdf, *pngs])
    fonts = embedded_fonts(pdf)
    # BUILDER-CODE-10: the guard asked only whether some Aptos was embedded; it now
    # compares every typeface the deck asks for with what the PDF embeds.
    swapped = substituted(requested_fonts(deck), fonts)
    summary: dict[str, Any] = {
        "pdf": str(pdf),
        "pngs": [str(p) for p in pngs],
        "slides": len(pngs),
        "deck_slides": deck_slide_count(deck),
        "hidden_slides": hidden,
        "dpi": dpi,
        "fonts": fonts,
        "font_fallback": bool(swapped),
        "substituted_fonts": swapped,
        "soffice": soffice,
    }
    warnings = []
    if hidden:
        warnings.append(
            f"slide(s) {', '.join(map(str, hidden))} hidden: LibreOffice exports no page for a "
            "hidden slide, so each PNG is named for the deck slide it shows."
        )
    if summary["slides"] != summary["deck_slides"] - len(hidden):
        warnings.append(
            f"{summary['deck_slides']} slides in the deck ({len(hidden)} hidden) but "
            f"{summary['slides']} pages rendered."
        )
    if swapped:
        warnings.append(
            f"{', '.join(swapped)} not embedded in the PDF: LibreOffice substituted another "
            "font, so text widths in these images differ from PowerPoint. Install the font "
            "where LibreOffice can find it before judging text fit."
        )
    summary["warnings"] = warnings
    if warnings:
        summary["warning"] = " ".join(warnings)  # the one-field form older readers take
    return summary, (EXIT_FONT_FALLBACK if swapped else EXIT_OK)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nbg_render.py", description="Render a deck to PDF and slide PNGs with LibreOffice."
    )
    parser.add_argument("deck", help=".pptx to render")
    parser.add_argument("outdir", help="folder for the PDF and slide-NN.png files")
    parser.add_argument(
        "--dpi", type=int, default=DEFAULT_DPI, help=f"PNG resolution (default {DEFAULT_DPI})"
    )
    args = parser.parse_args(argv)
    try:
        summary, code = render(
            Path(args.deck).expanduser().resolve(),
            Path(args.outdir).expanduser().resolve(),
            args.dpi,
        )
    except RenderError as e:
        code = EXIT_NO_SOFFICE if e.message == "LibreOffice is not installed" else EXIT_ERROR
        print(json.dumps({"error": e.message, "fix": e.fix}, ensure_ascii=False))
        print(f"nbg_render.py: {e.message}. {e.fix}", file=sys.stderr)
        return code
    except Exception as e:  # noqa: BLE001 - a render tool must report, never trace back
        print(json.dumps({"error": f"{type(e).__name__}: {e}", "fix": ""}, ensure_ascii=False))
        print(f"nbg_render.py: {type(e).__name__}: {e}", file=sys.stderr)
        return EXIT_ERROR
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
