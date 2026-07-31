"""Does every plate this pipeline builds actually reach the paper?

    python figures/check_figure_citations.py
    python figures/check_figure_citations.py --self-test

## Why this file exists

The paper carries its own parity gate,
``papers/phase1-workshop/figures/check_figure_parity.py``. That gate is good at
what it does -- it makes two independent implementations of one figure answer the
same questions -- but its scope is a **hard-coded map of three**::

    FIGURE_MAP = {
        "fig1_concept_timeline":  "fig06_concept_timeline",
        "fig2_coverage_accuracy": "fig07_a0_vs_a0prime",
        "fig3_loop_ledger":       "fig05_a2_repair_loop",
    }

Three entries, written when the pipeline drew three plates. The pipeline now
draws six, and that gate stays green no matter how many more it grows, because
the figures it does not name are figures it cannot notice. Today
``fig02_bill_shape``, ``fig03_capability_spectrum`` and ``fig04_a3_transfer``
are cited **zero** times anywhere under ``papers/`` and nothing goes red.

A figure nobody cites is not free. It is built on every run, hashed into
``SOURCES.sha256``, published in ``release/MANIFEST.jsonl`` (six entries each:
the script, the CSV, four images), and it drifts there -- 14 stale ``figures/``
entries in that manifest on 2026-07-29, eight of them plates of exactly this
kind. So the pipeline needs its own gate, on its own side of the fence, that
enumerates **its actual figure set** rather than a copy of it.

## The rule

``build_all.FIGURES`` is the figure set -- imported, not re-globbed, because the
directory and the build order are two different things and only one of them is
the pipeline's declaration of what it draws. Every name in it must be either:

* **cited** -- its full slug appears in the paper's prose (see ``paper_files``); or
* **declared** in ``NOT_CITED_ON_PURPOSE`` below, with a one-line reason.

A figure that is neither fails this gate, by name. So does a declaration that
has gone stale in either direction: naming a figure the pipeline no longer
builds, or claiming a figure is uncited when the paper in fact cites it. A
declaration is a statement about the world and this repository does not let
those rot quietly.

Nothing here edits ``papers/``. This gate reads it and reports; whether a plate
gets a sentence is the paper author's call, and three of the six are recorded
below as exactly that -- pending, named, and visible on every run.
"""

from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

REPO_ROOT = os.path.dirname(_HERE)

import build_all  # noqa: E402

#: Where a citation counts. The paper's *prose* -- the body, the outline, the
#: sections. Deliberately not everything under ``papers/``:
#:
#: * ``papers/**/runs/`` is review and run notes. ``fig02``'s single mention in
#:   the whole tree lives there, inside the range-phrase "the full fig02-fig07
#:   dark set is present" in a note about a *different* figure's broken path.
#:   Calling that a citation would have turned this gate green on a string that
#:   nobody wrote about fig02 at all.
#: * ``papers/**/figures/`` is the paper's own figure tooling (``PARITY.md``,
#:   ``check_figure_parity.py``). A gate mentioning a figure is not the paper
#:   citing it, and letting tooling satisfy this check would let the two gates
#:   hold each other up.
#:
#: The remaining surface is what a reader of the paper actually sees.
EXCLUDED_DIRS: tuple[str, ...] = ("runs", "figures")

#: Extensions that carry prose. ``.py`` is excluded on purpose: ``verify_paper.py``
#: names fig05/06/07 in a list, which is a gate's expectation and not a sentence.
PROSE_SUFFIXES: tuple[str, ...] = (".md", ".tex")

#: Figures the pipeline builds that the paper does not cite, **on purpose**, each
#: with the reason. One line each. This is the only way a figure is allowed to be
#: uncited; anything not here and not cited fails the gate by name.
#:
#: All three entries below are *pending a citation decision*, not a ruling that
#: they should stay uncited. That decision belongs to the paper author -- it means
#: writing a sentence in `papers/phase1-workshop/sections/`, and this side of the
#: fence does not write the paper. What this gate can honestly do is stop the
#: omission from being invisible, which is the state it was in until now:
#: `check_figure_parity.py`'s three-entry map could not see these figures, so
#: nothing anywhere reported that half the pipeline's output reaches no reader.
#:
#: Delete an entry the moment its figure is cited -- the gate will tell you, and
#: fail, if you forget.
# Empty on 2026-07-31, and that is a finding of this gate's own staleness rule:
# the three plates declared "pending a citation decision" (fig02_bill_shape,
# fig03_capability_spectrum, fig04_a3_transfer) are all cited by
# papers/phase1-workshop/REVIEW-2026-07-30.md, and a declaration that no longer
# describes the tree is a false statement in a gate. The mechanism stays: a
# figure that loses its last citation goes back in here, with a reason.
NOT_CITED_ON_PURPOSE: dict[str, str] = {}


def paper_files() -> list[str]:
    """Every prose file under ``papers/`` where a citation would count, sorted."""
    root = os.path.join(REPO_ROOT, "papers")
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for name in sorted(filenames):
            if name.endswith(PROSE_SUFFIXES):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def citations(figures: tuple[str, ...]) -> dict[str, list[str]]:
    """``{figure: [repo-relative file, ...]}`` -- where each figure is cited.

    Matched on the **full slug** (``fig06_concept_timeline``), never the stem
    (``fig06``). The stem matches range-phrases, other figures' filenames and
    prose about numbering; the slug is what a citation of this pipeline's plate
    literally contains, in every form it can take (the CSV path, either image
    path, or the name itself).
    """
    found: dict[str, list[str]] = {f: [] for f in figures}
    for path in paper_files():
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:  # a file we cannot read is not a file we may skip
            raise RuntimeError(f"cannot read {path}: {exc!r}") from exc
        rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        for fig in figures:
            if fig in text:
                found[fig].append(rel)
    return found


def audit(
    figures: tuple[str, ...],
    declared: dict[str, str],
    cited: dict[str, list[str]],
) -> tuple[list[str], list[str]]:
    """``(report lines, failure lines)``. Empty failures means the gate is green."""
    lines: list[str] = []
    failures: list[str] = []

    for fig in figures:
        where = cited.get(fig, [])
        note = declared.get(fig)
        if where and note is None:
            lines.append(f"CITED       {fig}: {len(where)} file(s) -- {', '.join(where)}")
        elif where and note is not None:
            failures.append(
                f"{fig} is declared 'not cited on purpose' and IS cited, in "
                f"{', '.join(where)}. Remove it from NOT_CITED_ON_PURPOSE: a "
                "declaration that no longer describes the tree is a false statement "
                "in a gate, which is worse than no declaration."
            )
        elif note is not None:
            lines.append(f"DECLARED    {fig}: uncited on purpose -- {note}")
        else:
            failures.append(
                f"{fig} is built by the pipeline, is cited nowhere in the paper's "
                "prose, and is not declared in NOT_CITED_ON_PURPOSE. Either cite it "
                "in papers/, or add it to NOT_CITED_ON_PURPOSE with a one-line "
                "reason. It is currently built on every run and published in "
                "release/MANIFEST.jsonl for no reader."
            )

    for fig, note in declared.items():
        if fig not in figures:
            failures.append(
                f"NOT_CITED_ON_PURPOSE names {fig!r}, which build_all.FIGURES does not "
                "build. The declaration outlived its figure; delete it."
            )
        elif not note.strip():
            failures.append(
                f"NOT_CITED_ON_PURPOSE[{fig!r}] has an empty reason. A declaration "
                "without a reason is a suppression."
            )
    return lines, failures


# --------------------------------------------------------------------------
# the negative control
# --------------------------------------------------------------------------
#
# A gate that has never been seen to fail is a green light with nothing behind
# it -- the same argument check_coverage.py and reconcile_cost.py make for their
# own self-tests, and the exact defect this file was written to fix: the paper's
# parity gate had been green for its whole life and it was green *because* it
# could not see three of the six figures.
#
# So: run the real audit against a figure set with one extra, invented name in
# it, and require that the audit fails and names it.


def self_test() -> int:
    real = build_all.FIGURES
    fake = "fig99_undeclared_newcomer"
    grown = real + (fake,)

    # The fake figure is cited nowhere and declared nowhere: the gate must fail.
    cited = citations(grown)
    if cited[fake]:
        print(f"SELF-TEST INCONCLUSIVE: {fake} is somehow cited in {cited[fake]}")
        return 1
    _, failures = audit(grown, NOT_CITED_ON_PURPOSE, cited)
    named = [f for f in failures if fake in f]
    if not named:
        print(
            f"SELF-TEST FAILED: a new figure ({fake}) with no citation and no "
            "declaration did NOT fail the gate. The gate is not enforcing anything."
        )
        for line in failures:
            print(f"  (other failure) {line}")
        return 1
    print(f"  negative control 1/3: an undeclared, uncited new figure FAILS, by name:")
    for line in named:
        print(f"    {line}")

    # Declaring it silences it -- the declaration is the whole escape hatch, and
    # it has to be shown working or the gate is unsatisfiable rather than strict.
    _, failures = audit(grown, {**NOT_CITED_ON_PURPOSE, fake: "invented by --self-test"}, cited)
    if any(fake in f for f in failures):
        print(f"SELF-TEST FAILED: {fake} still fails after being declared.")
        return 1
    print("  negative control 2/3: declaring it with a reason clears it")

    # A declaration with no figure behind it must fail too, or declarations rot.
    _, failures = audit(real, {**NOT_CITED_ON_PURPOSE, fake: "invented by --self-test"}, cited)
    if not any(fake in f for f in failures):
        print(f"SELF-TEST FAILED: a declaration for a figure the pipeline does not build ({fake}) passed.")
        return 1
    print("  negative control 3/3: a declaration naming a figure the pipeline does not build FAILS")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument(
        "--self-test",
        action="store_true",
        help="show the gate failing on an undeclared figure, then exit",
    )
    args = ap.parse_args(argv)

    if args.self_test:
        rc = self_test()
        print("self-test: PASS" if rc == 0 else "self-test: FAIL")
        return rc

    figures = build_all.FIGURES
    files = paper_files()
    cited = citations(figures)
    lines, failures = audit(figures, NOT_CITED_ON_PURPOSE, cited)

    print(
        f"figure citations: {len(figures)} figure(s) from build_all.FIGURES, "
        f"against {len(files)} prose file(s) under papers/"
    )
    for line in lines:
        print(f"  {line}")
    for line in failures:
        print(f"  FAIL        {line}")
    n_cited = sum(1 for f in figures if cited[f] and f not in NOT_CITED_ON_PURPOSE)
    n_declared = sum(1 for f in figures if f in NOT_CITED_ON_PURPOSE and not cited[f])
    print(f"\n{n_cited} cited, {n_declared} uncited by declaration, {len(failures)} unaccounted for.")
    if failures:
        print(
            "\nEvery figure this pipeline builds has to be accounted for: cited in the "
            "paper, or declared here with a reason. Neither is not an option."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
