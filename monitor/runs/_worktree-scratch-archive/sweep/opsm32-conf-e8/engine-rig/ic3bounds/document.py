"""Put the measured tables into `IC3_BOUNDS.md`, and check they are still true.

    cd engine-rig
    python -m ic3bounds.document --write     # regenerate the tables in place
    python -m ic3bounds.document --check     # exit 1 if any table is stale

E8 asks for "`engine-rig/IC3_BOUNDS.md` and a regenerable table".  Regenerable is
the load-bearing word.  A document whose numbers were typed in by hand is a
document that is true on the afternoon it is written and drifts silently
afterwards, and `tools/engine_table.py` exists because that had already happened
once to `ENGINE_TABLE.md` -- three of its figures turned out to be unsubstituted
placeholders that four guards were too narrow to see.

So the tables in `IC3_BOUNDS.md` are not written, they are *injected*, between
markers, from the run artefacts, by the same `markdown()` functions the axes use
to print themselves, and `--check` fails the run if the file on disk and the
artefacts on disk have parted company.

**What that does and does not cover, stated exactly, because an earlier draft of
this paragraph overstated it.**  It covers the marked regions.  It does not cover
the prose, and it does not cover a table that has no markers -- and the draft
that claimed "every number a reader could check is generated" was sitting beside
a hand-typed summary table every one of whose figures was wrong.  Two things came
out of that: the summary table is now generated too (`table:blocks`), and the
document carries a rule that removes the *class* of error rather than the
instance -- prose quotes only deterministic numbers, and every timing lives in a
generated table and is referred to rather than retyped.  The two tables that
remain authored are labelled as authored where they appear.

The markers are HTML comments so they render as nothing:

    <!-- table:size begin --> ... <!-- table:size end -->

`--check` is what `verify.sh` and any release gate should call.  It says nothing
about whether the *prose* is still true; nothing can.  What it rules out is the
one failure that is invisible to a reader: a table that used to be the artefact.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from ic3bounds import axis_compose, axis_predicates, axis_size

DOCUMENT = "IC3_BOUNDS.md"

# Which artefact feeds which marked region, and which renderer draws it.
# `axis_compose.json` and `axis_size.json` come from the run a previous session
# left; `axis_predicates.json` from this one.  Both paths are relative to
# `engine-rig/` and are recorded here rather than in the document so the
# document cannot claim a provenance the generator does not read.
SOURCES: Dict[str, Tuple[str, object]] = {
    "size": ("runs/20260729T120000Z-E8-ic3-scale/axis_size_dense/axis_size.json",
             axis_size.markdown),
    "predicates": ("runs/20260729T120000Z-E8-ic3-scale/axis_predicates.json",
                   axis_predicates.markdown),
    "blocks": ("runs/20260729T120000Z-E8-ic3-scale/axis_predicates.json",
               axis_predicates.blocks_markdown),
    "compose": ("runs/20260729T120000Z-E8-ic3-scale/axis_compose.json",
                axis_compose.markdown),
}

BEGIN = "<!-- table:%s begin -->"
END = "<!-- table:%s end -->"


class DocumentError(Exception):
    """The document does not have the shape the generator needs."""


def _engine_rig_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render(name: str, root: Optional[str] = None) -> str:
    path = os.path.join(root or _engine_rig_dir(), SOURCES[name][0])
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return SOURCES[name][1](payload)


def _region(text: str, name: str) -> Tuple[int, int]:
    begin, end = BEGIN % name, END % name
    start = text.find(begin)
    stop = text.find(end)
    if start < 0 or stop < 0 or stop < start:
        raise DocumentError(
            "%s has no %r/%r pair, so there is nowhere to put the %s table"
            % (DOCUMENT, begin, end, name))
    return start + len(begin), stop


def inject(text: str, root: Optional[str] = None) -> str:
    for name in SOURCES:
        start, stop = _region(text, name)
        text = text[:start] + "\n" + render(name, root) + "\n" + text[stop:]
    return text


def stale(text: str, root: Optional[str] = None) -> List[str]:
    problems: List[str] = []
    for name in SOURCES:
        start, stop = _region(text, name)
        on_disk = text[start:stop].strip()
        fresh = render(name, root).strip()
        if on_disk != fresh:
            problems.append(
                "the %s table in %s is not what %s renders -- it was edited by "
                "hand, or the artefact was re-measured and the document was not "
                "regenerated" % (name, DOCUMENT, SOURCES[name][0]))
    return problems


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ic3bounds.document")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--path", default=None, help="the document to work on")
    args = parser.parse_args(argv)

    root = _engine_rig_dir()
    path = args.path or os.path.join(root, DOCUMENT)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print("could not read %s: %s" % (path, exc))
        return 3

    if args.check:
        problems = stale(text, root)
        for line in problems:
            print("  - %s" % line)
        print("%s  %s" % ("STALE" if problems else "ok   ", path))
        return 1 if problems else 0

    updated = inject(text, root)
    if updated == text:
        print("ok    %s (already current)" % path)
        return 0
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
