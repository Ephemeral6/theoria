"""Demonstrations for the two V20 fixes. Writes nothing; touches no tracked file.

    python figures/runs/20260729T1600Z-V20-fixes/demo.py

Every mutation below is done to an in-memory copy of the log's text or to a
module attribute. `cold-start-a0/THEORIZE_LOG.md` belongs to the other track and
is never opened for writing here; nor is anything under `papers/`.
"""

from __future__ import annotations

import os
import re
import sys

FIGURES = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, FIGURES)

import build_all  # noqa: E402
import check_figure_citations as cite  # noqa: E402
import fig06_concept_timeline as fig06  # noqa: E402
import sources  # noqa: E402

RC = 0


def case(label: str):
    print(f"\n--- {label}")


def expect_raise(label, fn, want_substr):
    global RC
    try:
        got = fn()
    except Exception as exc:  # noqa: BLE001
        ok = want_substr in str(exc)
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        print(f"        {type(exc).__name__}: {str(exc).splitlines()[0][:150]}")
        if not ok:
            RC = 1
        return
    print(f"  FAIL  {label}: returned {got!r} instead of raising")
    RC = 1


def expect(label, cond, detail=""):
    global RC
    print(f"  {'PASS' if cond else 'FAIL'}  {label}{(' -- ' + detail) if detail else ''}")
    if not cond:
        RC = 1


LOG = sources.read_text(fig06.LOG_SOURCE_KEY)

print("=" * 74)
print("FIX 1 -- fig06.expected_ids is derived from the declared source")
print("=" * 74)

case("baseline: the derived set on the real log")
base = fig06.expected_ids(LOG)
print(f"  {len(base)} ids: {', '.join(base)}")
expect("matches the tuple abd8d0cb hand-edited", list(base) == [
    "O-01", "O-02", "O-03", "O-04",
    "R-01", "R-02", "R-03", "R-04", "R-05", "R-06", "R-07", "R-08",
    "L-01", "L-02", "L-03",
    "P-01", "P-02", "P-03",
    "E-01", "E-02", "E-03", "E-04", "E-05", "E-06", "E-07", "E-08", "E-09",
])
expect("read through sources, not open()", "sources.read_text" in
       open(os.path.join(FIGURES, "fig06_concept_timeline.py"), encoding="utf-8").read())

case("the source grows an E-10 row -- the case that broke the build for 14.5h")
e10 = "| E-10 | a fake entry planted by demo.py | **discharged** -- planted | none |\n"
grown = LOG.replace(
    "\n\nE-03 is the one to fix first",
    "\n" + e10 + "\nE-03 is the one to fix first",
)
expect("the scratch text really differs from the source", grown != LOG)
ids = fig06.expected_ids(grown)
expect("E-10 is in the derived set with no code edit", ids[-1] == "E-10", f"tail={ids[-3:]}")
parsed = fig06.parse_log(grown)
expect("the full parse accepts it too", "E-10" in parsed["entries"],
       f"{len(parsed['entries'])} entries")

case("the source is unreadable -- must raise, never truncate")
real_read = sources.read_text
try:
    def boom(key):
        raise FileNotFoundError(f"declared source missing: {key}")
    sources.read_text = boom
    expect_raise("expected_ids() with an unreadable source",
                 lambda: fig06.expected_ids(), "raises on purpose")
finally:
    sources.read_text = real_read
expect("sources.read_text restored", sources.read_text is real_read)

case("the source is empty / has no ids -- must raise, never return ()")
expect_raise("expected_ids('')", lambda: fig06.expected_ids(""), "not a legal answer")
expect_raise("expected_ids(prose with no ids)",
             lambda: fig06.expected_ids("# a log\n\nno entries here at all\n"),
             "not a legal answer")

print("\n  --- the invariants the hand-written tuple was really protecting ---")

case("a GAP in the E sequence (E-05 row deleted)")
gapped = re.sub(r"^\| E-05 \|.*\n", "", LOG, flags=re.M)
expect("the scratch text really differs", gapped != LOG)
expect_raise("expected_ids(log missing E-05)", lambda: fig06.expected_ids(gapped),
             "gap or does not start at 01")

case("a DUPLICATE id (E-04 row stated twice)")
dup = re.sub(r"^(\| E-04 \|.*)\n", r"\1\n\1\n", LOG, count=1, flags=re.M)
expect("the scratch text really differs", dup != LOG)
expect_raise("expected_ids(log with E-04 twice)", lambda: fig06.expected_ids(dup),
             "duplicate entry id")

case("ids OUT OF ORDER (E-08 and E-09 rows swapped)")
rows = re.findall(r"^\| E-0[89] \|.*$", LOG, flags=re.M)
swapped = LOG.replace(rows[0] + "\n" + rows[1], rows[1] + "\n" + rows[0])
expect("the scratch text really differs", swapped != LOG)
expect_raise("expected_ids(log with E-09 above E-08)", lambda: fig06.expected_ids(swapped),
             "out of source order")

case("a family SHRANK below its floor (E-09 and E-08 rows deleted)")
shrunk = re.sub(r"^\| E-0[89] \|.*\n", "", LOG, flags=re.M)
# Demote their elaboration headings to h4 so they leave the scan entirely; the
# point of this case is the floor, and an orphaned elaboration would fire first.
shrunk = shrunk.replace("### E-08, in full", "#### E-08, in full").replace(
    "### E-09, in full", "#### E-09, in full")
expect("the scratch text really differs", shrunk != LOG)
expect_raise("expected_ids(log with 7 E rows, floor 9)", lambda: fig06.expected_ids(shrunk),
             "floor is 9")

case("an '### E-NN, in full' elaboration with no table row")
orphan = LOG + "\n### E-11, in full — planted by demo.py, with no row behind it\n"
expect("the scratch text really differs", orphan != LOG)
expect_raise("expected_ids(log whose E-11 elaboration has no row)",
             lambda: fig06.expected_ids(orphan), "in full' elaborates a row")

case("the scan's [ORLPE] regex and FAMILIES drifting apart")
# `_ID_HEADING` spells the family alphabet literally, so it cannot silently
# follow a change to FAMILIES. The `unknown` branch is what notices. A bare
# `### X-01` is NOT this case and is not caught here: the regex ignores it, and
# so did the hand-written tuple, because `entries` never contained it either.
# What *is* caught at the section level is `## X -- ...`, by parse_log's
# KNOWN_SECTIONS check -- a new family arrives as a section before it arrives
# as a heading.
real_families = fig06.FAMILIES
try:
    fig06.FAMILIES = ("O", "R", "L", "E")  # P dropped
    expect_raise("expected_ids() with P no longer in FAMILIES",
                 lambda: fig06.expected_ids(LOG), "not declared in FAMILIES")
finally:
    fig06.FAMILIES = real_families
expect("FAMILIES restored", fig06.FAMILIES == real_families)
expect_raise("parse_log() on a log with a new '## X' section",
             lambda: fig06.parse_log(LOG + "\n## X — a brand new family\n\n### X-01 a thing\n"),
             "unrecognised section")

print()
print("=" * 74)
print("FIX 2 -- the citation gate enumerates build_all.FIGURES")
print("=" * 74)

case("the gate today")
rc = cite.main([])
expect("green on the real tree", rc == 0, f"exit {rc}")

case("a NEWLY ADDED figure with no citation and no declaration")
real_figs = build_all.FIGURES
try:
    build_all.FIGURES = real_figs + ("fig08_brand_new_plate",)
    print(f"  build_all.FIGURES is now {len(build_all.FIGURES)} long")
    rc = cite.main([])
    expect("the gate goes RED", rc == 1, f"exit {rc}")
finally:
    build_all.FIGURES = real_figs
expect("build_all.FIGURES restored", build_all.FIGURES == real_figs)

case("...and the paper's own parity gate does not notice, which is the defect")
sys.path.insert(0, os.path.join(os.path.dirname(FIGURES), "papers", "phase1-workshop", "figures"))
import check_figure_parity as parity  # noqa: E402
expect("check_figure_parity maps exactly 3 figures, hard-coded",
       len(parity.FIGURE_MAP) == 3, str(sorted(parity.FIGURE_MAP.values())))
expect("and 3 of build_all's 6 are outside its map",
       len(set(build_all.FIGURES) - set(parity.FIGURE_MAP.values())) == 3,
       str(sorted(set(build_all.FIGURES) - set(parity.FIGURE_MAP.values()))))

print("\n" + "=" * 74)
print("DEMO: PASS" if RC == 0 else "DEMO: FAIL")
raise SystemExit(RC)
