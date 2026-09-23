#!/usr/bin/env python3
"""Render a deck the way a reviewer sees it: PDF, one PNG per slide, and a font check.

    decks-py render deck.pptx outdir [--dpi 110]

LibreOffice converts the deck to PDF in a throwaway profile (so a user's own
LibreOffice settings and a stale lock never interfere), pypdfium2 draws each page
to outdir/slide-NN.png, and pypdf reads which fonts the PDF embeds. When Aptos is
not among them LibreOffice substituted another face, text runs to different
widths, and any judgement about fit made from these images is unreliable: that is
exit 4, not 0, so presentation-qa can say so instead of passing a slide it cannot
see properly.

stdout is one JSON object:
    {"pdf", "pngs", "slides", "deck_slides", "dpi", "fonts", "font_fallback", "soffice"}
or, when nothing was rendered, {"error", "fix"}.

Exit codes: 0 rendered with Aptos embedded; 4 rendered with substituted fonts;
3 LibreOffice is not installed; 2 any other error.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

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


def pdf_to_pngs(pdf: Path, outdir: Path, dpi: int) -> list[Path]:
    import pypdfium2 as pdfium

    for stale in outdir.glob("slide-*.png"):
        stale.unlink()
    doc = pdfium.PdfDocument(str(pdf))
    try:
        paths = []
        for i in range(len(doc)):
            page = doc[i]
            image = page.render(scale=dpi / 72).to_pil()
            path = outdir / f"slide-{i + 1:02d}.png"
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


def deck_slide_count(deck: Path) -> int:
    with zipfile.ZipFile(deck) as zf:
        return sum(
            1 for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")
        )


def render(deck: Path, outdir: Path, dpi: int = DEFAULT_DPI) -> tuple[dict[str, Any], int]:
    """(summary, exit code). Raises RenderError when nothing could be rendered."""
    if not deck.is_file():
        raise RenderError(f"deck not found: {deck}", "check the path")
    soffice = find_soffice()
    if soffice is None:
        raise RenderError(
            "LibreOffice is not installed",
            "install LibreOffice (https://www.libreoffice.org/download/) or set DECKS_SOFFICE "
            "to its soffice binary; the render-and-look QA step needs it",
        )
    outdir.mkdir(parents=True, exist_ok=True)
    pdf = convert_to_pdf(soffice, deck, outdir)
    pngs = pdf_to_pngs(pdf, outdir, dpi)
    fonts = embedded_fonts(pdf)
    fallback = not aptos_embedded(fonts)
    summary: dict[str, Any] = {
        "pdf": str(pdf),
        "pngs": [str(p) for p in pngs],
        "slides": len(pngs),
        "deck_slides": deck_slide_count(deck),
        "dpi": dpi,
        "fonts": fonts,
        "font_fallback": fallback,
        "soffice": soffice,
    }
    if summary["slides"] != summary["deck_slides"]:
        summary["warning"] = (
            f"{summary['deck_slides']} slides in the deck but {summary['slides']} pages rendered "
            "(hidden slides are not exported)"
        )
    if fallback:
        summary["warning"] = (
            "Aptos is not embedded in the PDF: LibreOffice substituted another font, so text "
            "widths in these images differ from PowerPoint. Install Aptos where LibreOffice "
            "can find it before judging text fit."
        )
    return summary, (EXIT_FONT_FALLBACK if fallback else EXIT_OK)


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
