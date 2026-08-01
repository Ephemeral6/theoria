# -*- coding: utf-8 -*-
"""exam/u3_census.py — the U3 census: find every book, adjudicate none of them.

`freeze/u3.py` is E1, the frozen U3 adjudicator (STATS_RULES.md §1.2/§1.2.1).
It answers "did THIS directory attain U3".  It does not answer "which
directories are there", and on 2026-07-31 that difference was doing real
damage: the E1 sweep that produced `freeze/runs/20260731T1546Z-U3-E1-IMPL/`
was invoked with a **hand-written list of paths**, so its denominator was
whatever the author happened to type.  Sixteen of the twenty-two Lean
developments on disk were never put in front of the adjudicator at all.

This module is the missing half and nothing more:

    discovery + enumeration   -> here (exam, the exam instruments)
    the U3 judgment itself    -> `freeze.u3`, called, never reimplemented

Every verdict in the census output is the return value of a `freeze.u3`
function.  There is no second opinion in this file, deliberately: a census
that re-decided attainment would be a fork of a frozen endpoint, which is
exactly the "scattering" the U-ladder must not do.  If a verdict here is
wrong, the bug is in `freeze/u3.py` and belongs to the freeze territory.

Why the census belongs in `exam/`
---------------------------------
`exam/` is where the instruments that *grade* the fleet live (`grading/`,
`leakage.py`, `drill_certificates.py`).  A census is a grading instrument: it
fixes a denominator and refuses to let it drift.  Putting it in `freeze/`
would put the thing that chooses the denominator inside the thing whose
denominator is frozen -- and §1.2's denominator (19 / 12 sealed games) is
*not* this denominator anyway.  See `DENOMINATORS` below; conflating the two
is the single easiest way to misread this file's output.

Two discovery defects this census exists to catch
-------------------------------------------------
D1. **`u3.evaluate()` only looks for `path/theory.lean`.**  A Lean development
    under any other filename (`Level.lean` in `theory-compiler/
    handover_packages/`, `A0.lean` outside the a0-report path, `corner.lean`)
    is invisible to it: `evaluate()` returns `no_evidence`, which is
    indistinguishable from "there was no proof layer".  That is a
    false-negative on a **primary endpoint**, and it silently shrinks both the
    numerator and the denominator at once.  The census therefore finds books
    by extension and hands the entry file to `u3.eval_lean_source` directly.
    `test_u3_census.py::test_level_lean_book_is_discovered` is the regression.

D2. **`u3.expand_targets()` descends exactly one level.**  Books nested deeper
    (`cold-start-a3/runs/<run>/generated/<variant>/theory.lean`) are never
    reached.  The census walks.

Both were reported as findings, not patched here -- `freeze/u3.py` is not this
territory's file.  See `exam/runs/<utc>-U3-CENSUS/RUN_STATE.md`.

**Both were repaired in freeze on 2026-08-01**, along with F1 (the (c) gate
keyed on theorem NAMES).  `u3.find_books` now takes any `.lean` that states a
theorem and `u3.expand_targets` walks to depth 12, so the adjudicator alone can
now see a `Level.lean` and a book four levels down.  The census's own discovery
and its direct-source fallback are kept anyway, and kept tested: they are
belt-and-braces on a **primary endpoint**, they cost nothing when the walker
works, and a census whose enumeration is the adjudicator's enumeration cannot
be the independent check on it that catching D1/D2 required.  What changed is
the tests' claim, not the code's job -- `test_u3_census.py` no longer asserts
that E1 is blind, it asserts that the census agrees with E1 and would still
find the books if E1 went blind again.

Exclusions are declared, never silent
-------------------------------------
A census whose exclusions are invisible is a census you cannot audit.  Every
skipped path is recorded in the output under `excluded` with the rule that
skipped it, so the difference between "no book there" and "we chose not to
look" is always on the record.  `monitor/runs/_worktree-scratch-archive/` is
the one that matters: it holds byte-copies of *other territories'* trees, and
counting them would double-count books that are already counted at their real
home -- inflating the denominator with duplicates of the numerator's
neighbours.

Usage
-----
    python -m exam.u3_census                       # census to stdout
    python -m exam.u3_census --json out.json --md out.md
    python -m exam.u3_census --probe               # + Lean constancy probes
    python -m exam.u3_census --root <dir>          # census a subtree

Exit code is 0 for a completed census.  **A census does not fail on a low
attainment rate** -- 0/22 is a measurement, not a broken build, and an
instrument that went red on a bad number would create a reason not to run it.
It exits 2 only when discovery itself is broken (see `--expect-books`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO = str(Path(__file__).resolve().parents[1])
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from freeze import u3  # noqa: E402  -- the frozen adjudicator, by import only
from freeze import theorem_shape as _shape  # noqa: E402  -- its kind vocabulary

__all__ = [
    "BookSite",
    "discover_books",
    "adjudicate_site",
    "census",
    "attainment_rate",
    "to_markdown",
]

# --------------------------------------------------------------- exclusions

#: (path fragment, reason).  Matched against the POSIX-style path relative to
#: the census root.  Every match is recorded in the output, never dropped.
EXCLUSION_RULES: Tuple[Tuple[str, str], ...] = (
    (".git/", "git internals"),
    (".worktrees/", "worktree checkouts are copies of the same tracked books"),
    ("__pycache__/", "build cache"),
    (".lake/", "Lean build cache, not authored source"),
    ("node_modules/", "vendored dependency"),
    ("environment_files/", "upstream game source; sealed-pile discipline "
                           "(CLAUDE.md) forbids opening it"),
    ("monitor/runs/_worktree-scratch-archive/",
     "archived byte-copies of other territories' trees; counting them "
     "double-counts books already counted at their real home"),
)

#: Filenames that are Lean *project scaffolding*, not a development to judge.
#: `lakefile.lean` declares a build; it states no theorem, so putting it in
#: front of the adjudicator would manufacture a `no_evidence` row that looks
#: like a failed manual.
SCAFFOLD_NAMES = frozenset({"lakefile.lean"})

#: Preferred entry filenames, best first.  A directory with several Lean files
#: is one book with several modules; the census adjudicates every file and
#: keeps the best verdict (u3's own stage rank), because "the arm produced at
#: least one machine-checkable theorem" (§1.2) is satisfied by any one of them.
ENTRY_PREFERENCE = ("theory.lean",)


# ------------------------------------------------------------- denominators

DENOMINATORS = {
    "census": (
        "Every Lean development on disk, one row per directory.  This is an "
        "ENGINEERING denominator -- it says what the repo contains.  It is "
        "NOT STATS_RULES.md §1.2's denominator."
    ),
    "frozen_e1": (
        "STATS_RULES.md §1.2: the U3 attainment rate's denominator is fixed at "
        "19 sealed games (12 at the clean layer), with no exclusions and no "
        "cap.  Nothing on disk today is a sealed game, so the frozen rate is "
        "not computable from this census and this census does not claim to "
        "compute it."
    ),
}


# ------------------------------------------------------------------- model

class BookSite:
    """One directory holding at least one authored Lean development."""

    __slots__ = ("directory", "lean_files", "route", "territory")

    def __init__(self, directory: Path, lean_files: List[Path], route: str,
                 territory: str) -> None:
        self.directory = directory
        self.lean_files = lean_files
        self.route = route          # how discovery found it
        self.territory = territory  # top-level dir it belongs to

    def entry(self) -> Path:
        for preferred in ENTRY_PREFERENCE:
            for f in self.lean_files:
                if f.name == preferred:
                    return f
        return self.lean_files[0]

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "BookSite(%s, %d files)" % (self.directory, len(self.lean_files))


# --------------------------------------------------------------- discovery

def _excluded_by(rel_posix: str) -> Optional[str]:
    """Return the reason `rel_posix` is excluded, or None."""
    probe = rel_posix if rel_posix.endswith("/") else rel_posix + "/"
    for fragment, reason in EXCLUSION_RULES:
        if fragment in probe:
            return reason
    return None


def discover_books(root: Path,
                   record_exclusions: Optional[List[Dict[str, str]]] = None,
                   ) -> List[BookSite]:
    """Walk `root` and return every directory containing an authored `.lean`.

    Unlike `u3.expand_targets`, this recurses to arbitrary depth and does not
    require the file to be named `theory.lean` -- the two assumptions that hid
    sixteen books from the 2026-07-31 sweep.
    """
    root = Path(root).resolve()
    by_dir: Dict[Path, List[Path]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        rel = here.relative_to(root).as_posix()
        rel = "" if rel == "." else rel
        reason = _excluded_by(rel) if rel else None
        if reason is not None:
            if record_exclusions is not None:
                record_exclusions.append({"path": rel, "reason": reason})
            dirnames[:] = []       # do not descend
            continue
        # Prune excluded children before descending, so the record names the
        # subtree once instead of every leaf inside it.
        keep = []
        for d in sorted(dirnames):
            child_rel = (rel + "/" + d) if rel else d
            child_reason = _excluded_by(child_rel)
            if child_reason is None:
                keep.append(d)
            elif record_exclusions is not None:
                record_exclusions.append({"path": child_rel,
                                          "reason": child_reason})
        dirnames[:] = keep

        leans = sorted(here / f for f in filenames
                       if f.endswith(".lean") and f not in SCAFFOLD_NAMES)
        if leans:
            by_dir[here] = leans

    sites: List[BookSite] = []
    for directory in sorted(by_dir):
        rel = directory.relative_to(root)
        territory = rel.parts[0] if rel.parts else "."
        names = {f.name for f in by_dir[directory]}
        route = "theory.lean" if "theory.lean" in names else "non-standard-name"
        sites.append(BookSite(directory, by_dir[directory], route, territory))
    return sites


# ------------------------------------------------------------ adjudication

def _rank(label: str) -> int:
    return u3._STAGE_RANK.get(label, -1)


def adjudicate_site(site: BookSite, probe: bool = False,
                    lean_bin: Optional[str] = None) -> Dict[str, Any]:
    """Adjudicate one book site.  EVERY verdict here comes from `freeze.u3`.

    Order of attempts, best verdict wins by u3's own stage rank:

    1. `u3.evaluate(dir)` -- the run-dir route.  Picks up `certify.json`,
       `transfer.json`, `artifacts/a0_report.json`, the Lean cert JSON.
    2. `u3.eval_lean_source(f)` for each authored `.lean` in the directory --
       the route `u3.evaluate` cannot take when the file is not `theory.lean`.

    Step 2 is why a `Level.lean` book stops reading as `no_evidence`.
    """
    if probe and lean_bin is None:
        lean_bin = u3.find_lean()

    best: Optional[Dict[str, Any]] = None

    def consider(v: Dict[str, Any], how: str) -> None:
        nonlocal best
        v = dict(v)
        v["census_route"] = how
        if best is None or _rank(v["label"]) > _rank(best["label"]):
            best = v

    dir_verdict = u3.evaluate(site.directory, probe=probe, lean_bin=lean_bin)
    consider(dir_verdict, "u3.evaluate")

    # The direct-source route.  Run it whenever `u3.evaluate` did not already
    # reach the proof layer, which is precisely the D1/D2 blind spot.
    if _rank(dir_verdict["label"]) <= _rank("no_proof_layer"):
        bin_ = lean_bin or u3.find_lean()
        for lean_file in site.lean_files:
            consider(
                u3.eval_lean_source(lean_file, probe=probe, lean_bin=bin_,
                                    recorded={}),
                "u3.eval_lean_source:%s" % lean_file.name,
            )

    assert best is not None
    best["run"] = str(site.directory)
    best["territory"] = site.territory
    best["discovery_route"] = site.route
    best["lean_files"] = [f.name for f in site.lean_files]
    return best


# ------------------------------------------------------------------ census

def attainment_rate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Numerator, denominator, rate -- and the denominator's meaning, inline.

    The meaning travels with the number on purpose.  §1.2's rate and this rate
    share a name and share nothing else; a bare `3/22` in a report is an
    invitation to quote it as the endpoint.
    """
    attained = [r for r in rows if r.get("verdict") == "attained"]
    n = len(rows)
    return {
        "numerator": len(attained),
        "denominator": n,
        "rate": (len(attained) / n) if n else None,
        "denominator_meaning": DENOMINATORS["census"],
        "not_the_frozen_endpoint": DENOMINATORS["frozen_e1"],
        "attained_paths": sorted(r["run"] for r in attained),
    }


#: Artefacts that mean "a run reached the certify stage", whether or not it
#: emitted a Lean development.
CERTIFY_MARKERS = ("certify.json", "transfer.json")


def discover_claimants(root: Path,
                       book_dirs: Iterable[Path] = (),
                       ) -> List[Path]:
    """Run directories that reached certify but produced NO Lean book.

    The book census answers "of the manuals that exist, how many prove
    something".  On its own that is a flattering question: a run that never
    wrote a manual at all simply does not appear, and the rate goes up.  The
    four live carried legs of 2026-07-31 are exactly this case -- they have
    `certify.json`, they have no `.lean`, and a book-only census silently drops
    all four.

    So the census reports them too, in their own section with their own
    denominator.  They are NOT folded into the book rate: a run with no book
    and a book that proves a tautology fail U3 for different reasons, and
    §1.2's own denominator is neither of these.
    """
    root = Path(root).resolve()
    books = {Path(b).resolve() for b in book_dirs}
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        rel = here.relative_to(root).as_posix()
        rel = "" if rel == "." else rel
        if rel and _excluded_by(rel) is not None:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in sorted(dirnames)
                       if _excluded_by((rel + "/" + d) if rel else d) is None]
        if here in books:
            continue
        names = set(filenames)
        if names & set(CERTIFY_MARKERS):
            out.append(here)
    return sorted(out)


#: The kinds E1 writes a §1.2.1 (c) check for, read from freeze's own frozen
#: constant rather than restated here.  Reading it is the whole point: the
#: previous version of this table sniffed for the substring `"no executable"`
#: in E1's `why` text, and when freeze repaired the adjudicator on 2026-08-01
#: that sentence stopped being written.  The table did not go red.  It went
#: **empty** -- `kinds_that_can_never_attain: []`, a clean bill of health
#: manufactured by a lookup miss, which is precisely the failure a coverage
#: report may not have.  Keying on an exported name means the next such change
#: is an ImportError, not a silent all-clear.
CHECKED_KINDS = frozenset(_shape.KINDS_WITH_A_C_CHECK)

#: Kinds with no (c) check that will never get one, and should not.  A
#: `point_claim` (`I s₀ = true`) and a `witness` (`∃ s, …`) are *supporting
#: obligations* -- material for another theorem's (c), not claims about the
#: world -- and §1.2.1 writes no non-vacuity requirement for either.  They are
#: permanent non-attainers by design, so reporting them in the same list as a
#: genuine gap would make the gap unfindable.  (freeze → exam, 2026-08-01: "for
#: the first two that is correct and permanent".)
PERMANENT_NON_ATTAINERS = frozenset({_shape.POINT_KIND, _shape.WITNESS_KIND})


def kind_coverage(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Which theorem KINDS exist on disk, and which have no (c) check at all.

    This is the census's most load-bearing output and the reason it is worth
    running before 开跑.  It answers one question: if the sealed campaign emits
    theorems of kind K, can E1 ever award U3 for them?

    **History, because the answer changed today and the table's meaning changed
    with it.**  Until 2026-08-01 E1 decided (c) with a prefix matcher over
    theorem NAMES (`u3.classify_theorem`), so a fully discharged theorem whose
    name the matcher did not recognise came back kind `unknown` and its
    development was labelled `vacuous` -- the word §1.2.1 reserves for a manual
    that proved a tautology.  The sokoban deadlock development at
    `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify/` was the
    case that made it undeniable: it compiles, reports an EMPTY axiom set on all
    nine theorems, carries `pat_witness` and `level_is_winnable`, and
    STATS_RULES.md:123 names it as the *paradigm* of what U3 means.  E1 called
    it vacuous.  freeze repaired it (`freeze/theorem_shape.py`): the kind is now
    read off the STATEMENT, `unknown` no longer exists, and that development
    reads `discharged`.

    So this table no longer reports a name-matching hazard.  What it reports now
    is a two-way split, and the split is the point:

    * `coverage_gaps` -- kinds E1 could not classify at all (`unclassified`).
      A theorem here fails closed and its development cannot attain through it,
      whatever the proof contains.  **This is the only entry that is a defect.**
    * `permanent_non_attainers` -- `point_claim` and `witness`.  No check, no
      gap: §1.2.1 asks nothing of a supporting obligation, and it never will.

    `kinds_that_can_never_attain` is retained as the union of the two, because
    the field is read by the report renderer and by the 2026-08-01 run record,
    and a field that quietly narrows is worse than one that is renamed.
    """
    kinds: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        # `per_theorem` lives under `criteria`, not at the row's top level.
        # Reading it from the wrong place returns {} — an empty coverage table,
        # which renders as "no kind is unreachable", i.e. a clean bill of
        # health produced by a lookup miss.  That is exactly the failure a
        # coverage report must not have, and it is why
        # `test_kind_coverage_splits_permanent_non_attainers_from_gaps`
        # asserts on a populated table rather than on the absence of problems.
        per_theorem = (r.get("criteria") or {}).get("per_theorem") or {}
        for tname, t in per_theorem.items():
            # `unclassified` is E1's own word for "the shape could not be
            # read", and is the right default for a row that carries no kind
            # at all.  It used to be `unknown`, a kind E1 no longer produces.
            k = t.get("kind") or _shape.UNCLASSIFIED_KIND
            slot = kinds.setdefault(k, {"theorems": 0, "c_ok": 0,
                                        "c_unchecked": 0,
                                        "no_check_implemented":
                                            k not in CHECKED_KINDS,
                                        "permanent": k in PERMANENT_NON_ATTAINERS,
                                        "examples": []})
            slot["theorems"] += 1
            c = t.get("c") or {}
            if c.get("ok") is True:
                slot["c_ok"] += 1
            elif c.get("ok") is None and (t.get("b") or {}).get("ok"):
                # (b) passed and (c) still returned neither yes nor no: nothing
                # ran.  Counted, so the table shows the gap in theorems and not
                # only in vocabulary.
                slot["c_unchecked"] += 1
            if len(slot["examples"]) < 4:
                slot["examples"].append("%s::%s" % (r["run"], tname))

    unreachable = sorted(k for k, v in kinds.items()
                         if v["no_check_implemented"] and v["c_ok"] == 0)
    gaps = sorted(k for k in unreachable if k not in PERMANENT_NON_ATTAINERS)
    permanent = sorted(k for k in unreachable if k in PERMANENT_NON_ATTAINERS)
    return {
        "kinds": dict(sorted(kinds.items())),
        "kinds_with_a_c_check": sorted(CHECKED_KINDS),
        "kinds_that_can_never_attain": unreachable,
        "coverage_gaps": gaps,
        "permanent_non_attainers": permanent,
        "note": (
            "A kind in `coverage_gaps` has no implemented §1.2.1 (c) check in "
            "freeze/u3.py, so every theorem of that kind fails closed and "
            "cannot carry its development to `discharged`, no matter what it "
            "proves. A kind in `permanent_non_attainers` (`point_claim`, "
            "`witness`) is a supporting obligation rather than a claim about "
            "the world; §1.2.1 writes no requirement for it and none is "
            "missing. Only the first list is a defect."
        ),
    }


def census(root: Path, probe: bool = False,
           lean_bin: Optional[str] = None) -> Dict[str, Any]:
    """Discover every book under `root`, adjudicate each, summarise."""
    root = Path(root).resolve()
    exclusions: List[Dict[str, str]] = []
    sites = discover_books(root, record_exclusions=exclusions)
    if probe and lean_bin is None:
        lean_bin = u3.find_lean()

    rows: List[Dict[str, Any]] = []
    for site in sites:
        row = adjudicate_site(site, probe=probe, lean_bin=lean_bin)
        row["run"] = site.directory.relative_to(root).as_posix()
        rows.append(row)

    # Runs that reached certify without emitting a book.  No Lean is invoked
    # for these (there is nothing to compile), so this pass is cheap.
    claimant_rows: List[Dict[str, Any]] = []
    for cdir in discover_claimants(root, [s.directory for s in sites]):
        v = u3.evaluate(cdir, probe=False, lean_bin=lean_bin)
        v["run"] = cdir.relative_to(root).as_posix()
        claimant_rows.append(v)
    claimant_labels: Dict[str, int] = {}
    for r in claimant_rows:
        claimant_labels[r["label"]] = claimant_labels.get(r["label"], 0) + 1

    labels: Dict[str, int] = {}
    for r in rows:
        labels[r["label"]] = labels.get(r["label"], 0) + 1

    by_territory: Dict[str, Dict[str, int]] = {}
    for r in rows:
        slot = by_territory.setdefault(r["territory"],
                                       {"books": 0, "attained": 0})
        slot["books"] += 1
        if r.get("verdict") == "attained":
            slot["attained"] += 1

    return {
        "root": root.as_posix(),
        "lean_available": bool(lean_bin or u3.find_lean()),
        "probe": probe,
        "summary": attainment_rate(rows),
        "kind_coverage": kind_coverage(rows),
        "labels": dict(sorted(labels.items())),
        "by_territory": dict(sorted(by_territory.items())),
        "bookless_claimants": {
            "count": len(claimant_rows),
            "attained": sum(1 for r in claimant_rows
                            if r.get("verdict") == "attained"),
            "labels": dict(sorted(claimant_labels.items())),
            "note": ("Runs that reached the certify stage and emitted no Lean "
                     "development. Reported separately and NEVER folded into "
                     "the book rate: a run with no book fails U3 for a "
                     "different reason than a book that proves a tautology, "
                     "and folding them would let 'the arm stopped writing "
                     "manuals' raise the attainment rate."),
            "rows": u3.sanitize_paths(claimant_rows),
        },
        "excluded": sorted(exclusions, key=lambda e: e["path"]),
        "rows": u3.sanitize_paths(rows),
    }


# ------------------------------------------------------------------ report

def to_markdown(result: Dict[str, Any]) -> str:
    s = result["summary"]
    out = [
        "# U3 census",
        "",
        "Discovery: `exam/u3_census.py`.  Every verdict below is the return "
        "value of a `freeze/u3.py` function -- this census decides *which* "
        "books exist, never *whether* one attained.",
        "",
        "**%d / %d books attained U3.**" % (s["numerator"], s["denominator"]),
        "",
        "> %s" % s["not_the_frozen_endpoint"],
        "",
        "| book | territory | verdict | label | route | files |",
        "|---|---|---|---|---|---|",
    ]
    for r in result["rows"]:
        out.append("| `%s` | %s | %s | %s | %s | %s |" % (
            r["run"], r["territory"],
            "**attained**" if r.get("verdict") == "attained" else "not attained",
            r["label"], r.get("census_route", "-"),
            ", ".join(r.get("lean_files", [])) or "-",
        ))
    out += ["", "## labels", ""]
    for k, v in result["labels"].items():
        out.append("* `%s` — %d" % (k, v))
    kc = result.get("kind_coverage") or {}
    out += ["", "## theorem-kind coverage of the (c) check", "",
            "| kind | theorems seen | (c) passed | (c) never ran | "
            "check implemented? |",
            "|---|---|---|---|---|"]
    for k, v in (kc.get("kinds") or {}).items():
        out.append("| `%s` | %d | %d | %d | %s |" % (
            k, v["theorems"], v["c_ok"], v.get("c_unchecked", 0),
            ("no — permanent, §1.2.1 asks nothing of this shape"
             if v.get("permanent") else
             "no — fails closed") if v["no_check_implemented"] else "yes"))
    gaps = kc.get("coverage_gaps") or []
    permanent = kc.get("permanent_non_attainers") or []
    out += ["", "**Coverage gaps (a defect): %s.**"
            % (", ".join("`%s`" % k for k in gaps) if gaps else "none"), ""]
    if permanent:
        out += ["**Permanent non-attainers (not a defect): %s.**"
                % ", ".join("`%s`" % k for k in permanent), ""]
    out += [kc.get("note", ""), ""]
    bc = result.get("bookless_claimants") or {}
    if bc:
        out += ["", "## runs that reached certify with no book", "",
                "**%d runs, %d attained.** %s"
                % (bc["count"], bc["attained"], bc["note"]), "",
                "| label | runs |", "|---|---|"]
        for k, v in (bc.get("labels") or {}).items():
            out.append("| `%s` | %d |" % (k, v))

    out += ["", "## excluded subtrees (declared, not silent)", ""]
    for e in result["excluded"]:
        out.append("* `%s` — %s" % (e["path"], e["reason"]))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- CLI

def _write_lf(path: Path, text: str) -> None:
    """Write with LF endings whatever the platform thinks it wants."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Census every Lean book on disk and adjudicate each "
                    "through freeze/u3.py (E1).")
    ap.add_argument("--root", type=Path, default=Path(REPO))
    ap.add_argument("--probe", action="store_true",
                    help="run Lean constancy probes (slower, stronger (c))")
    ap.add_argument("--lean", default=None, help="path to the lean binary")
    ap.add_argument("--json", dest="json_out", type=Path, default=None)
    ap.add_argument("--md", dest="md_out", type=Path, default=None)
    ap.add_argument("--expect-books", type=int, default=None,
                    help="fail (exit 2) if discovery finds fewer books than "
                         "this.  Discovery silently finding nothing is the "
                         "failure mode a census cannot afford; a low "
                         "attainment RATE is not.")
    args = ap.parse_args(argv)

    result = census(args.root, probe=args.probe, lean_bin=args.lean)

    # newline="\n" is load-bearing, not style.  `exam/.gitattributes` pins
    # `* text eol=lf`, so git stores LF; Python's text mode on Windows would
    # write CRLF, and a MANIFEST sha256 taken over the working copy would then
    # fail to reproduce after a fresh checkout on any machine.  Determinism is
    # a requirement here (CLAUDE.md), and this is where it would have leaked.
    if args.json_out:
        _write_lf(args.json_out, json.dumps(result, indent=1, sort_keys=True,
                                            ensure_ascii=False) + "\n")
    if args.md_out:
        _write_lf(args.md_out, to_markdown(result))

    s = result["summary"]
    print("%d / %d books attained U3 (census denominator, NOT STATS_RULES "
          "§1.2's 19/12)" % (s["numerator"], s["denominator"]))
    print("labels: " + ", ".join("%s %d" % kv for kv in result["labels"].items()))
    for p in s["attained_paths"]:
        print("  attained: %s" % p)

    if args.expect_books is not None and s["denominator"] < args.expect_books:
        print("DISCOVERY REGRESSION: found %d books, expected at least %d"
              % (s["denominator"], args.expect_books), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
