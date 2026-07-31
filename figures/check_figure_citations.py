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
from dataclasses import dataclass

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

#: The same argument as ``papers/**/runs/``, for review documents that sit at the
#: top of the paper directory instead of inside it. ``REVIEW-2026-07-30.md``
#: landed on master after this gate was written, and it names all three of the
#: declared-uncited plates -- in a section headed by their *declaration strings*,
#: while reporting them as "figures no sentence references". A document that says
#: "nobody cites fig02" is the strongest possible evidence that nobody cites
#: fig02, and reading it as a citation does not merely produce a false positive:
#: it makes the gate unsatisfiable in the honest direction, because deleting the
#: three declarations would then turn it *green* on the strength of a review that
#: says they are uncited. A review is a document about the paper, not the paper.
#: Matched on the leading token before any '-' or '.', so REVIEW.md,
#: REVIEW-2026-07-30.md and REVIEW_TRIAGE.md are all one rule.
EXCLUDED_FILE_STEMS: tuple[str, ...] = ("REVIEW", "REVIEW_TRIAGE", "CITECHECK")

#: Extensions that carry prose. ``.py`` is excluded on purpose: ``verify_paper.py``
#: names fig05/06/07 in a list, which is a gate's expectation and not a sentence.
PROSE_SUFFIXES: tuple[str, ...] = (".md", ".tex")

#: Rulings a declaration may carry. ``retire`` is the only one that may name no
#: home section, because it is the only one that says the plate should not have
#: one. The other two are both "this plate belongs in the paper"; they differ in
#: whether the section is ready to receive it.
RULINGS: tuple[str, ...] = ("promote", "hold", "retire")


@dataclass(frozen=True)
class Uncited:
    """One uncited figure's disposition: a ruling, a home section, a reason.

    **Why this is a record and not a string.** It was a string until V23, and the
    gate checked only that the string was non-empty. So the gate was green over
    three reasons, two of which were false statements about the tree:

    * ``fig04_a3_transfer`` -- *"A3 transfer has no section in the workshop
      paper's outline"*. ``papers/phase1-workshop/OUTLINE.md`` declares section 6
      as A3 transfer and ``sections/06_a3_transfer.md`` exists, with a §6.2
      titled "The bill".
    * ``fig03_capability_spectrum`` -- *"is a Phase-4 artefact and the workshop
      paper stops at Phase 1"*. ``sections/07_battery.md`` is 653 lines and is
      entirely the metrics battery, citing
      ``battery/artifacts/capability_spectrum.json`` throughout.

    Both were written by a gate whose whole purpose is to stop a claim about
    figures rotting quietly, and both rotted inside it. The lesson is not "write
    better reasons" -- it is that a free-text reason is the one field here nothing
    could check, so it was the field that went wrong.

    ``home_section`` is the part of a reason that **can** be checked: the file it
    names must exist. That does not make a reason true -- nothing mechanical can
    -- and this gate does not claim otherwise. What it does is make the specific
    false claim that actually occurred *unwritable*: you can no longer say "this
    plate has no home section" without either naming a section that exists or
    ruling ``retire``.
    """

    ruling: str
    home_section: str | None
    reason: str


#: Figures the pipeline builds that the paper does not cite, each with its
#: disposition. This is the only way a figure is allowed to be uncited; anything
#: not here and not cited fails the gate by name.
#:
#: The rulings are `figures/STATUS.md` D-F-007's, which is the authority for them
#: and carries the evidence and the dissent. They are deliberately **not uniform**
#: across the three: the first draft of that ruling was uniform, on a premise
#: about the paper's reviewers that turned out to be backwards.
#:
#: Delete an entry the moment its figure is cited -- the gate will tell you, and
#: fail, if you forget.
#:
#: **Known, and larger than any of the three.** The paper embeds no figure at all
#: -- no markdown image, no `\includegraphics`, no `<img>`, nowhere under
#: `papers/`. So "cited" and "reaching a reader" are still different things here,
#: and the three plates below are not the only ones invisible to a reader of
#: `PAPER.md`: all six are. This gate measures citation because citation is what
#: it can measure; it must not be read as measuring readership. Handed to
#: `papers/` in `figures/STATUS.md`'s open-handover table.
NOT_CITED_ON_PURPOSE: dict[str, Uncited] = {
    "fig02_bill_shape": Uncited(
        ruling="promote",
        home_section="papers/phase1-workshop/sections/07_battery.md",
        reason=(
            "promote into §7.8 (STATUS.md D-F-007): E2 and E3 are two of Phase 4's "
            "three pre-registered primary endpoints and §7.8 argues about them in "
            "prose only. Awaiting the paper-side edit; this side does not write the "
            "paper"
        ),
    ),
    "fig03_capability_spectrum": Uncited(
        ruling="promote",
        home_section="papers/phase1-workshop/sections/07_battery.md",
        reason=(
            "promote into §7.1 (STATUS.md D-F-007): §7.1 states the battery matrix as "
            "a bare list of totals and this plate draws exactly that, with absence "
            "hatched rather than zeroed. Awaiting the paper-side edit"
        ),
    ),
    "fig04_a3_transfer": Uncited(
        ruling="hold",
        home_section="papers/phase1-workshop/sections/06_a3_transfer.md",
        reason=(
            "hold, do not promote yet (STATUS.md D-F-007): the plate is a faithful "
            "redraw of §6.2's own table, but §6 is under live recommendation to be cut "
            "or demoted to an appendix by two independent P12 seats. Promoting a figure "
            "into a section two reviewers want gone is a bet, not a disposition; its "
            "fate follows §6's"
        ),
    ),
}


def paper_files() -> list[str]:
    """Every prose file under ``papers/`` where a citation would count, sorted."""
    root = os.path.join(REPO_ROOT, "papers")
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for name in sorted(filenames):
            if not name.endswith(PROSE_SUFFIXES):
                continue
            if name.split(".")[0].split("-")[0] in EXCLUDED_FILE_STEMS:
                continue
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
    declared: dict[str, Uncited],
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
            home = note.home_section or "(none -- retired)"
            lines.append(
                f"DECLARED    {fig}: {note.ruling} -> {home} -- {note.reason}")
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
            continue
        # The three fields, each checked as far as it can be. `reason` is the one
        # nothing mechanical can validate, which is exactly why it is not the only
        # field any more -- see Uncited's docstring.
        if note.ruling not in RULINGS:
            failures.append(
                f"NOT_CITED_ON_PURPOSE[{fig!r}] carries ruling {note.ruling!r}, which is "
                f"not one of {RULINGS}. A disposition nobody defined is not a disposition."
            )
        if not note.reason.strip():
            failures.append(
                f"NOT_CITED_ON_PURPOSE[{fig!r}] has an empty reason. A declaration "
                "without a reason is a suppression."
            )
        if note.ruling == "retire":
            if note.home_section is not None:
                failures.append(
                    f"NOT_CITED_ON_PURPOSE[{fig!r}] is ruled 'retire' and still names a "
                    f"home section ({note.home_section}). Retire says the plate should "
                    "not have one; drop the section or change the ruling."
                )
        elif not note.home_section:
            failures.append(
                f"NOT_CITED_ON_PURPOSE[{fig!r}] is ruled {note.ruling!r} and names no home "
                "section. Only 'retire' may do that -- the false claim this gate exists "
                "to make unwritable is 'this plate has no home section' asserted about a "
                "paper that has one."
            )
        elif not os.path.isfile(os.path.join(REPO_ROOT, note.home_section)):
            failures.append(
                f"NOT_CITED_ON_PURPOSE[{fig!r}] names home section {note.home_section!r}, "
                "which is not a file in this tree. Two of the three reasons this record "
                "replaced were false statements about exactly that; naming a section that "
                "does not exist is the same defect with the numbers changed."
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
    _, failures = audit(grown, {**NOT_CITED_ON_PURPOSE, fake: Uncited(ruling="retire", home_section=None,
                                                 reason="invented by --self-test")}, cited)
    if any(fake in f for f in failures):
        print(f"SELF-TEST FAILED: {fake} still fails after being declared.")
        return 1
    print("  negative control 2/3: declaring it with a reason clears it")

    # A declaration with no figure behind it must fail too, or declarations rot.
    _, failures = audit(real, {**NOT_CITED_ON_PURPOSE, fake: Uncited(ruling="retire", home_section=None,
                                                 reason="invented by --self-test")}, cited)
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
