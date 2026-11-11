#!/usr/bin/env python3
"""Make an Atlas email HTML file XHTML well-formed so Stripo's importer accepts it.

Stripo parses strict XML on import. Unescaped `&` and non-self-closed void elements
cause a SILENT import hang — the file renders fine in a browser and simply fails to
import. Run this as the ABSOLUTE LAST STEP of the build, from the build script, never
by hand: any edit made afterwards re-introduces the problem.

Usage:
    from xhtml_pass import xhtml_pass
    html = xhtml_pass(html)          # raises if it cannot be made well-formed

    python xhtml_pass.py file.html   # in place, prints a report
"""

import re
import sys

VOID = ("img", "meta", "br", "hr", "input", "link", "area", "base", "col",
        "embed", "source", "track", "wbr")

# `&` that is already part of a valid entity
ENTITY = re.compile(r"&(?:#[0-9]+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]{1,31});")


def escape_amps(html: str) -> tuple[str, int]:
    """Escape every raw & that is not already an entity. UTM query strings are the
    usual source."""
    out, last, n = [], 0, 0
    for m in re.finditer(r"&", html):
        i = m.start()
        if i < last:
            continue
        e = ENTITY.match(html, i)
        if e:
            out.append(html[last:e.end()])
            last = e.end()
        else:
            out.append(html[last:i] + "&amp;")
            last = i + 1
            n += 1
    out.append(html[last:])
    return "".join(out), n


def self_close_voids(html: str) -> tuple[str, int]:
    n = 0

    def fix(m):
        nonlocal n
        inner = m.group(2).rstrip()
        if inner.endswith("/"):
            return m.group(0)
        n += 1
        return f"<{m.group(1)}{inner} />"

    return re.sub(r"<(" + "|".join(VOID) + r")((?:\s[^<>]*)?)>", fix, html, flags=re.I), n


def drop_valueless_attrs(html: str, attrs=("referrerpolicy",)) -> tuple[str, int]:
    """Valueless attributes are valid HTML but invalid XML."""
    n = 0
    for a in attrs:
        html, k = re.subn(r"\s" + a + r"(?=[\s>/])(?!\s*=)", "", html, flags=re.I)
        n += k
    return html, n


def verify(html: str) -> None:
    """Strict XML parse. `&nbsp;` is valid under the declared DTD but unknown to a
    non-DTD-aware parser, so substitute it FOR VERIFICATION ONLY."""
    from lxml import etree
    etree.fromstring(html.replace("&nbsp;", "&#160;").encode(),
                     etree.XMLParser(resolve_entities=False))


def xhtml_pass(html: str, report: bool = False):
    html, a = escape_amps(html)
    html, v = self_close_voids(html)
    html, d = drop_valueless_attrs(html)
    verify(html)
    stats = {"amps_escaped": a, "voids_closed": v, "attrs_dropped": d,
             "tables_open": html.count("<table"), "tables_close": html.count("</table>"),
             "kb": round(len(html) / 1024, 1)}
    return (html, stats) if report else html


if __name__ == "__main__":
    p = sys.argv[1]
    out, stats = xhtml_pass(open(p).read(), report=True)
    open(p, "w").write(out)
    print("XHTML pass OK:", stats)
    if stats["tables_open"] != stats["tables_close"]:
        print("WARNING: table tags unbalanced — structural damage likely")
    if stats["kb"] > 102:
        print(f"WARNING: {stats['kb']} KB — Gmail clips at ~102 KB")
