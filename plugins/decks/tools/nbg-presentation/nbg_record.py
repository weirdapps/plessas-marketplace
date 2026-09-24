#!/usr/bin/env python3
"""Write the draft record /presentation-review later compares a finished deck against.

    decks-py record deck.pptx deck.yaml --data "${CLAUDE_PLUGIN_DATA}" [--topic T]

Writes <data>/presentations/pending/<YYYYMMDDHHMM>_<slug>.yaml and prints
{"record": <path>, "id": <id>, "slides": <n>} on stdout. The record used to be
prose an agent was told to write by hand, into the plugin folder or the current
directory, with no copy of the content; this is the same record as code, in the
per-user data folder that survives version bumps.

Record keys:
    id          <YYYYMMDDHHMM>_<slug>, the file's stem
    created     ISO 8601 with the local UTC offset
    status      pending (a review moves the record to presentations/reviewed/)
    topic       --topic, else presentation.title, else the cover title
    file_path   the .pptx, absolute
    file_hash   sha256:<hex> of the .pptx as built
    spec_path   the deck spec, absolute
    slides      [{index (1-based), id, type, title}]
    spec        the whole deck spec after legacy-name normalisation

Exit codes: 0 record written; 2 it could not be written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbg_spec  # noqa: E402

EXIT_OK = 0
EXIT_ERROR = 2

# Greek to Latin for file names (ELOT 743, simplified): a slug stays readable in
# every file system and in a URL.
_GREEK = dict(
    zip(
        "αβγδεζηθικλμνξοπρσςτυφχψω",
        ["a", "v", "g", "d", "e", "z", "i", "th", "i", "k", "l", "m", "n", "x", "o",
         "p", "r", "s", "s", "t", "y", "f", "ch", "ps", "o"],
        strict=True,
    )
)  # fmt: skip


class RecordError(Exception):
    pass


def slugify(text: str, limit: int = 60) -> str:
    """lower_case_ascii words joined by underscores; Greek transliterated."""
    folded = unicodedata.normalize("NFD", text.lower())
    out = []
    for ch in folded:
        if unicodedata.combining(ch):
            continue
        out.append(_GREEK.get(ch, ch))
    ascii_text = unicodedata.normalize("NFKD", "".join(out)).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return slug[:limit].rstrip("_") or "deck"


def _title(slide: dict[str, Any]) -> str | None:
    content = slide.get("content")
    if isinstance(content, dict) and isinstance(content.get("title"), str):
        return str(content["title"])
    return None


def build_record(deck: Path, spec_path: Path, topic: str | None, now: datetime) -> dict[str, Any]:
    if not deck.is_file():
        raise RecordError(f"deck not found: {deck}")
    data, issues = nbg_spec.load_yaml(spec_path)
    if issues:
        raise RecordError(issues[0].format())
    spec, _ = nbg_spec.normalise(data)
    if not isinstance(spec, dict):
        raise RecordError(f"{spec_path.name} is not a deck spec (the top level is not a mapping)")
    slides = nbg_spec.slide_list(spec)
    raw = spec.get("presentation")
    presentation: dict[str, Any] = raw if isinstance(raw, dict) else {}
    cover = next((s for s in slides if isinstance(s, dict) and s.get("type") == "cover"), {})
    topic = topic or presentation.get("title") or _title(cover) or deck.stem
    record_id = f"{now.strftime('%Y%m%d%H%M')}_{slugify(str(topic))}"
    return {
        "id": record_id,
        "created": now.isoformat(timespec="seconds"),
        "status": "pending",
        "topic": str(topic),
        "file_path": str(deck),
        "file_hash": "sha256:" + hashlib.sha256(deck.read_bytes()).hexdigest(),
        "spec_path": str(spec_path),
        "slides": [
            {
                "index": i + 1,
                "id": s.get("id") if isinstance(s, dict) else None,
                "type": s.get("type") if isinstance(s, dict) else None,
                "title": _title(s) if isinstance(s, dict) else None,
            }
            for i, s in enumerate(slides)
        ],
        "spec": spec,
    }


def write_record(
    deck: Path,
    spec_path: Path,
    data_dir: Path,
    topic: str | None = None,
    now: datetime | None = None,
) -> tuple[Path, dict[str, Any]]:
    now = now or datetime.now().astimezone()
    record = build_record(deck.resolve(), spec_path.resolve(), topic, now)
    folder = data_dir.expanduser() / "presentations" / "pending"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{record['id']}.yaml"
    path.write_text(yaml.safe_dump(record, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path, record


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # a Greek path on a Windows code page
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="nbg_record.py", description="Write the draft record /presentation-review learns from."
    )
    parser.add_argument("deck", help="the built .pptx")
    parser.add_argument("spec", help="the deck spec it was built from")
    parser.add_argument(
        "--data", required=True, help='the per-user data folder, "${CLAUDE_PLUGIN_DATA}"'
    )
    parser.add_argument("--topic", help="what the deck is about (defaults to its title)")
    args = parser.parse_args(argv)
    data = Path(args.data.strip()).expanduser() if args.data.strip() else None
    if data is None or not data.is_absolute():
        # An unset ${CLAUDE_PLUGIN_DATA} arrives as "": the record, the whole spec and its
        # absolute paths included, would land in whatever folder happens to be current.
        print(
            f"nbg_record.py: --data {args.data!r} is not an absolute folder. Pass "
            '"${CLAUDE_PLUGIN_DATA}", which the plugin runtime sets; if it is empty, run '
            "from the plugin command rather than by hand",
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        path, record = write_record(Path(args.deck), Path(args.spec), data, args.topic)
    except (RecordError, nbg_spec.CannotRun, OSError) as e:
        print(f"nbg_record.py: {e}", file=sys.stderr)
        return EXIT_ERROR
    print(
        json.dumps(
            {"record": str(path), "id": record["id"], "slides": len(record["slides"])},
            ensure_ascii=False,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
