#!/usr/bin/env python3
"""Every `path:line` in the methodological-honesty section must still point there.

The section this guards (`sections/10a_honesty.md`) makes its whole argument out
of code that reads a tool's failure as a fact about the world. Its citations are
therefore load-bearing in a way prose citations are not: if a line drifts, the
paper keeps asserting a defect at a line that no longer holds it, and nothing in
the build notices. So the citations are pinned, not merely written.

Two directions, and both matter:

  forward   every entry in CITATIONS.json resolves — the file exists, the line
            exists, and the line still contains the registered fragment.
  backward  every `path:line` that appears in the section text is registered.
            Without this half, a new citation could be added to the prose and
            never be checked, which is the same failure family the section is
            about: an absent check reading as a passing one.

Exit codes: 0 all citations hold; 1 at least one failed; 2 the checker could not
run (missing section, unreadable registry). 2 is deliberately not 0 — "I could
not check" is not "it is clean", which is finding S23 of the census this section
reports.

Usage:
    python papers/phase1-workshop/check_honesty_citations.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SECTION = HERE / "sections" / "10a_honesty.md"
REGISTRY = HERE / "CITATIONS.json"

# `path/to/file.py:123` or `path/to/file.py:123-456`, inside backticks in the
# prose. Anchored on a suffix that looks like a source or data file so that
# ordinary prose colons and section numbers are not swept in.
CITE = re.compile(
    r"`([A-Za-z0-9_./-]+\.(?:py|sh|json|jsonl|md|dsl|lean|toml|yaml|yml))"
    r":(\d+)(?:-(\d+))?`"
)


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")


def main() -> int:
    if not SECTION.exists():
        print(f"CANNOT-CHECK  section not found: {SECTION}")
        return 2
    if not REGISTRY.exists():
        print(f"CANNOT-CHECK  registry not found: {REGISTRY}")
        return 2

    try:
        entries = json.loads(REGISTRY.read_text(encoding="utf-8"))["citations"]
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as exc:
        print(f"CANNOT-CHECK  registry unreadable: {exc}")
        return 2

    text = SECTION.read_text(encoding="utf-8")
    bad = 0

    # ---- forward: the registry resolves -------------------------------------
    for e in entries:
        path, line, frag = e["path"], e["line"], e["must_contain"]
        target = REPO / path
        if not target.exists():
            fail(f"{path}:{line} — file does not exist")
            bad += 1
            continue
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            fail(f"{path}:{line} — not UTF-8 decodable, so it cannot be checked")
            bad += 1
            continue
        if line > len(lines):
            fail(f"{path}:{line} — file has only {len(lines)} lines")
            bad += 1
            continue
        got = lines[line - 1]
        if frag not in got:
            fail(
                f"{path}:{line} — expected {frag!r}\n"
                f"      found    {got.strip()!r}"
            )
            bad += 1

    # ---- backward: the prose cites nothing unregistered ---------------------
    registered = {(e["path"], e["line"]) for e in entries}
    for m in CITE.finditer(text):
        path, start = m.group(1), int(m.group(2))
        if (path, start) not in registered:
            fail(f"{path}:{start} — cited in the section but not in CITATIONS.json")
            bad += 1

    n_cited = len(set(CITE.findall(text)))
    if bad:
        print(f"\n{bad} citation(s) failed; {len(entries)} registered, "
              f"{n_cited} distinct cited in prose.")
        return 1
    print(f"ok  {len(entries)} registered citations resolve; "
          f"{n_cited} distinct `path:line` in the section, all registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
