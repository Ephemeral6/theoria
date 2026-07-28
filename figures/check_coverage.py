"""The coverage probe: is everything on disk actually reaching the figure?

    python figures/check_coverage.py

``verify.sh``'s other gates check that the pipeline is *deterministic* and that
the committed tree is *current*. Neither can see the failure P8 found twice:
data sitting in the repository, tracked and committed, that the figure never
reads -- because the figure's list of inputs was written by hand and the
directory grew past it. Both builds are byte-identical, the committed tree
matches a fresh build, every source hash is unchanged, and the picture is
missing two runs' worth of evidence. Green all the way down.

So this is the probe form of that failure. It does not re-derive anything the
figure computes; it asks four questions of the finished build, each of which was
answered wrongly by the tree as committed before P8:

1. **Is every discovery rule at its floor?** A rule that finds nothing looks
   exactly like a family that is empty.
2. **Is every cost-bearing theoria run accounted for?** Either drawn as a curve,
   or named in the notes as a run that billed nothing. Silence is not an answer.
3. **Does every run with a roll-up on disk carry its outcome into the picture?**
   This is drift D-1 exactly: two tracked roll-ups were unread, so two runs were
   drawn as *outcome unknown* -- and one of them was a ``model_error``, which is
   the plate's own warning that a curve stopped because the API died.
4. **Does every drawn run have a shape verdict?** Not a value -- a verdict. A
   run with no E2 must carry the battery's reason for having none, so that an
   absence cannot quietly render as a gap.

A probe and a hand-written judgement disagreeing is a finding, and the probe
wins. That is why this file exists rather than a paragraph in RUN_STATE saying
the coverage was checked once.

**The probe walks the filesystem itself, and that is deliberate.** Everywhere
else in ``figures/`` reaching past ``sources.py`` is the defect; here it is the
whole method. The first version of this file took its disk-side inventory from
``sources.discovered(...)`` -- the same registry the figure reads -- and its own
negative control caught it: narrowing the registry back to the pre-P8 roll-up
list narrowed *both* sides at once, so the probe stayed green over the exact
defect it was written for. An oracle that calls the thing it audits can only
prove that thing self-consistent. So the inventory below comes from
``os.listdir`` and the verdict comes from the registry, and the probe is the
place where the two are made to agree.
"""

from __future__ import annotations

import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fig02_bill_shape as fig02  # noqa: E402
import sources  # noqa: E402


def _abs(rel: str) -> str:
    return os.path.join(sources.REPO_ROOT, *rel.split("/"))


def _walk(rel_dir: str) -> list[str]:
    """Sorted entry names under a repo-relative directory. The oracle's eyes."""
    try:
        return sorted(os.listdir(_abs(rel_dir)))
    except OSError:
        return []


def _theoria_dirs_with_cost() -> list[tuple[str, list, dict]]:
    """``(dir, cost_rows, manifest)`` for every run directory on disk that billed.

    Walked, not read out of the registry. The registry's opinion of which runs
    exist is precisely what is being audited.
    """
    root = sources.rule(fig02.THEORIA_RULE).root
    out: list[tuple[str, list, dict]] = []
    for entry in _walk(root):
        curve_path = _abs(f"{root}/{entry}/cost_curve.json")
        manifest_path = _abs(f"{root}/{entry}/MANIFEST.json")
        if not (os.path.isfile(curve_path) and os.path.isfile(manifest_path)):
            continue
        with open(curve_path, encoding="utf-8") as fh:
            rows = json.load(fh)
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        out.append((entry, rows, manifest))
    return out


def _rollups_on_disk() -> dict[str, str]:
    """``{run_id: file}`` over every roll-up on disk, registry not consulted."""
    rule = sources.rule(fig02.ROLLUP_RULE)
    found: dict[str, str] = {}
    for entry in _walk(rule.root):
        if not fnmatch.fnmatch(entry, rule.pattern):
            continue
        path = _abs(f"{rule.root}/{entry}")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, list):
            continue
        for row in payload:
            if isinstance(row, dict) and row.get("run_id"):
                found[row["run_id"]] = f"{rule.root}/{entry}"
    return found


def check() -> list[str]:
    """Every failure, not just the first. Empty list means green."""
    failures: list[str] = []

    # --- 1. rules at their floors -----------------------------------------
    failures.extend(sources.floor_violations())

    curves, shape, notes = fig02.extract()
    note_blob = "\n".join(notes)
    drawn = {c["run_id"]: c for c in curves}

    # --- 2. every cost-bearing theoria run is drawn or explained ----------
    for entry, rows, manifest in _theoria_dirs_with_cost():
        slug = manifest.get("slug") or entry
        if slug in drawn:
            continue
        if not rows and slug in note_blob:
            continue  # billed nothing, and the notes say so by name
        failures.append(
            f"theoria run {entry} has {len(rows)} billed call(s) on disk and is neither "
            "drawn nor named in the notes. A run that reached disk must reach the picture "
            "or be refused out loud."
        )

    # --- 3. an outcome on disk is an outcome on the plate ------------------
    on_disk = _rollups_on_disk()
    for run_id, curve in sorted(drawn.items()):
        if run_id in on_disk and curve["outcome"] is None:
            failures.append(
                f"{run_id} is drawn with no outcome (dotted: 'outcome unknown') while "
                f"{on_disk[run_id]} records one. This is the exact drift P8 found: a "
                "tracked roll-up that the figure was not reading."
            )

    # --- 4. absence carries a reason --------------------------------------
    for run_id, curve in sorted(drawn.items()):
        for metric in fig02.SHAPE_METRICS:
            cell = (curve.get("shape") or {}).get(metric)
            if cell is None:
                failures.append(f"{run_id}: no {metric} verdict at all, not even an absence")
                continue
            if cell.get("value") is None and not cell.get("reason"):
                failures.append(
                    f"{run_id}: {metric} is absent with no reason. An absence without a "
                    "reason renders as a gap, and a gap reads as a zero."
                )

    return failures


#: The four roll-up files the pre-P8 ``ROLLUP_KEYS`` tuple named. Kept so the
#: probe can be shown failing on the exact tree it was written for.
_PRE_P8_ROLLUPS = (
    "pilot_ar25-0c556536.json",
    "pilot_g50t-5849a774.json",
    "pilot_sk48-d8078629.json",
    "pilot_tn36-ef4dde99.json",
)

#: The two runs that drift D-1 left drawn as outcome-unknown.
_PRE_P8_VICTIMS = ("bare_cc-g50t-claude-sonnet-5-ddabe772", "bare_cc-sk48-claude-sonnet-5-9022a076")


def self_test() -> list[str]:
    """Put the tree back the way it was before P8 and require the probe to fire.

    A check that has never failed is a check nobody has any reason to trust, and
    this repository has already been bitten by one (``fuzzlab``'s first green
    campaign, which proved nothing because the corpus could not generate the
    case). So the negative control is not a comment saying the probe was tried
    once: it reconstructs the defect and fails if the probe stays quiet.

    The defect reconstructed is drift D-1 exactly -- the roll-up rule narrowed
    back to the four filenames the old hand-written tuple listed, which is what
    the tree looked like at commit 98593a0.
    """
    problems: list[str] = []
    rule_name = fig02.ROLLUP_RULE
    original = sources.DISCOVERED[rule_name]
    try:
        sources.DISCOVERED[rule_name] = tuple(
            s for s in original if s.path.rsplit("/", 1)[-1] in _PRE_P8_ROLLUPS
        )
        if len(sources.DISCOVERED[rule_name]) != len(_PRE_P8_ROLLUPS):
            problems.append(
                "self-test could not reconstruct the pre-P8 tree: expected "
                f"{len(_PRE_P8_ROLLUPS)} roll-ups, narrowed to "
                f"{len(sources.DISCOVERED[rule_name])}"
            )
            return problems
        fired = check()
        for victim in _PRE_P8_VICTIMS:
            if not any(victim in f for f in fired):
                problems.append(
                    f"NEGATIVE CONTROL FAILED: with the pre-P8 roll-up list, {victim} is "
                    "drawn with no outcome and the probe did not say so. The probe is "
                    "green because it cannot see the defect, not because there is none."
                )
    finally:
        sources.DISCOVERED[rule_name] = original
    return problems


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        problems = self_test()
        if problems:
            for p in problems:
                print(f"COVERAGE: {p}")
            return 1
        print(
            "coverage self-test ok: narrowed to the pre-P8 roll-up list, the probe "
            f"reports both runs it was written to catch ({', '.join(_PRE_P8_VICTIMS)})."
        )
        return 0

    failures = check()
    n_theoria = len(_theoria_dirs_with_cost())
    n_rollups = len(_rollups_on_disk())
    if failures:
        for f in failures:
            print(f"COVERAGE: {f}")
        return 1
    print(
        f"coverage ok: {n_theoria} billing theoria run(s) and {n_rollups} roll-up run_id(s) "
        "found by walking the tree; every cost-bearing run drawn or explained, every "
        "outcome on disk on the plate, every shape absence carrying its reason."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
