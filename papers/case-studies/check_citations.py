"""Resolve every `path:line` / `path:a-b` citation in the case studies.

The case-study set's red line is that every number and every quotation points
back at a file and a line on the tree.  This script is the executable form of
that rule: it extracts each citation, checks the target exists and is long
enough, and prints the cited lines so the anchor can be eyeballed.

    python check_citations.py            # summary; non-zero exit on any failure
    python check_citations.py --show     # also print the cited text

Citations are written as Markdown links whose text is a backticked relative
path with an optional line or line range:

    [`../../cold-start-a0/THEORIZE_LOG.md:104-109`](../../cold-start-a0/THEORIZE_LOG.md)
    [`:117-118`](../../cold-start-a2/A2_REPORT.md)          <- short form, path from the href

A citation with no line number is a whole-file reference and is checked for
existence only.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = sorted(HERE.glob("*.md"))

# [`<text>`](<href>) -- text may be "path:lines", ":lines", or a bare path.
CITE = re.compile(r"\[`([^`]+)`\]\(([^)]+)\)")
LINES = re.compile(r"^(?P<path>.*?):(?P<a>\d+)(?:-(?P<b>\d+))?$")


def read_lines(path: Path) -> list[str]:
    with io.open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def resolve(doc: Path, text: str, href: str):
    """Return (target, a, b) with 1-indexed inclusive bounds, or (target, None, None)."""
    m = LINES.match(text)
    a = b = None
    if m:
        a = int(m.group("a"))
        b = int(m.group("b")) if m.group("b") else a
    # The href is authoritative for the path; the text may abbreviate it.
    target = (doc.parent / href.split("#")[0]).resolve()
    return target, a, b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="print the cited lines")
    args = ap.parse_args()

    # The tree is UTF-8; the console on the development box is not.  Replace
    # rather than raise, so a citation into a Chinese paragraph is still
    # checkable from a GBK terminal.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - exotic stdout
        pass

    total = ok = 0
    failures: list[str] = []

    for doc in DOCS:
        for lineno, line in enumerate(read_lines(doc), 1):
            for text, href in CITE.findall(line):
                if href.startswith(("http://", "https://")):
                    continue
                total += 1
                target, a, b = resolve(doc, text, href)
                where = f"{doc.name}:{lineno}"

                if not target.exists():
                    failures.append(f"{where}: missing target {href}")
                    continue
                if a is None:
                    ok += 1
                    continue

                body = read_lines(target)
                if b > len(body):
                    failures.append(
                        f"{where}: {href}:{a}-{b} but the file has {len(body)} lines"
                    )
                    continue
                cited = body[a - 1 : b]
                if not any(s.strip() for s in cited):
                    failures.append(f"{where}: {href}:{a}-{b} cites only blank lines")
                    continue
                ok += 1
                if args.show:
                    print(f"\n--- {where} -> {href}:{a}-{b}")
                    for i, s in enumerate(cited, a):
                        print(f"  {i:>4} | {s}")

    print(f"\n{ok}/{total} citations resolve across {len(DOCS)} documents")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
