#!/usr/bin/env python3
"""Namespace-preserving OOXML writer for the two injection tools.

`ElementTree.write()` renames every namespace prefix it was not told about and
drops every declaration it does not itself use. A real PowerPoint slide carries
`mc`, `p14`, `a14` and `c16r2` on its root and an `mc:Ignorable="p14 a14"`
attribute that names two of them, so a plain round trip turns

    <p:sld xmlns:mc="..." xmlns:p14="..." mc:Ignorable="p14 a14">

into

    <p:sld xmlns:ns1="..." ns1:Ignorable="p14 a14">

which is a dangling prefix reference and a hard OOXML validity error. It also
loses `standalone="yes"` from the XML declaration. Both injectors survived only
because python-pptx-generated slides declare nothing beyond a, p and r.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree.ElementTree import (  # nosemgrep: python.lang.security.use-defused-xml.use-defused-xml - serialisation helpers only, every parse() goes through defusedxml
    register_namespace,
    tostring,
)

_XMLNS_RE = re.compile(rb'xmlns(?::([\w.\-]+))?\s*=\s*"([^"]+)"')
_DECL_RE = re.compile(rb"^\s*(<\?xml[^>]*\?>)")
_DEFAULT_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def declared_namespaces(raw: bytes) -> list[tuple[str, str]]:
    """Every xmlns declaration in the source, first-seen prefix wins."""
    seen: dict[str, str] = {}
    for prefix, uri in _XMLNS_RE.findall(raw):
        key = prefix.decode("utf-8") if prefix else ""
        seen.setdefault(key, uri.decode("utf-8"))
    return list(seen.items())


def _used_uris(root) -> set[str]:
    """URIs ElementTree will emit a declaration for: those on a tag or attribute."""
    uris = set()
    for el in root.iter():
        for name in (el.tag, *el.keys()):
            if isinstance(name, str) and name.startswith("{"):
                uris.add(name[1:].split("}", 1)[0])
    return uris


def write_preserving_namespaces(tree, path: Path, raw: bytes) -> None:
    """Serialise `tree` over `path`, keeping every prefix and declaration in `raw`.

    `raw` is the original bytes of the same file, read before it was parsed.
    """
    declared = declared_namespaces(raw)
    for prefix, uri in declared:
        register_namespace(prefix, uri)

    # A declaration ElementTree will not re-emit (because nothing in the tree
    # uses that URI) is put back as a literal attribute on the root. mc:Ignorable
    # names p14 and a14 in its *value*, so those two are always in this group.
    root = tree.getroot()
    used = _used_uris(root)
    for prefix, uri in declared:
        if uri in used:
            continue
        root.set(f"xmlns:{prefix}" if prefix else "xmlns", uri)

    m = _DECL_RE.match(raw)
    decl = m.group(1).decode("utf-8") if m else _DEFAULT_DECL
    body = tostring(root, encoding="unicode")
    Path(path).write_text(f"{decl}\n{body}", encoding="utf-8")
