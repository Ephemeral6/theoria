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
figure computes; it asks four questions of the finished build. **Two of them were
answered wrongly by the tree as committed before P8** -- questions 2 and 3 below.
Questions 1 and 4 could not have been asked of that tree at all: it had no
discovery rules and no shape verdicts, so they are not evidence of anything that
went wrong, they are the two places the new machinery could go wrong next:

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
defect it was written for. **The second version was still wrong the same way, one
level up**: it walked the filesystem, but took the root and the pattern it walked
*from the rule it was auditing*, so tightening a ``Rule.pattern`` -- which is what
a real regression looks like, since ``DISCOVERED`` is derived state nobody edits
-- moved the oracle's eyes along with it. An oracle that calls the thing it
audits can only prove that thing self-consistent, and it can do that through a
parameter as easily as through a function call. So the inventory below is stated
as literals, the walk is ``os.listdir``, the verdict comes from the registry, and
the negative control narrows the **rule**.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fig02_bill_shape as fig02  # noqa: E402
import sources  # noqa: E402


#: The probe's own inventory, stated as literals.
#:
#: These deliberately duplicate `sources.DISCOVERY`'s roots, patterns and member
#: filenames instead of reading them off the rules. The first version of this
#: file did read them off the rules, and that was still the oracle calling the
#: engine it audits, one level up: narrowing a `Rule`'s pattern -- which is what
#: a real regression looks like, since `DISCOVERED` is derived and nobody edits
#: it by hand -- narrowed the probe's own inventory in the same motion, and the
#: probe reported nothing while both victims went back to being drawn dotted.
#:
#: Duplication is the point here and nowhere else in this directory. Two
#: independently written descriptions of the same tree can disagree, and the
#: disagreement is the finding; one description checked against itself cannot
#: disagree with anything.
THEORIA_ROOT = "theoria-arm/runs"

#: The filenames that can carry a theoria run's per-call cost record, stated as
#: literals for the same reason the roots are. On 2026-08-01 the arm's rename
#: from ``cost_curve.json`` to ``bill_shape.json`` hid seven billing legs from
#: the plate, and this probe **did** report them -- as "a manifest claims spend
#: and no cost curve stands beside it", which is a true sentence that names the
#: wrong cause. Had this tuple been read off ``sources.DISCOVERY`` it would have
#: been narrowed by the same rename, and the probe would have gone silent
#: instead: the run directories would have carried "no members at all" and been
#: skipped by the oracle exactly as they were by the rule. That is the third
#: time this file's inventory has had to be pulled back out of the thing it
#: audits, and this is the shape the pull-back takes for an alternation.
THEORIA_CURVE_NAMES = ("cost_curve.json", "bill_shape.json")
THEORIA_MEMBERS = ("MANIFEST.json",)
ROLLUP_ROOT = "baseline-arms/out"
ROLLUP_PATTERN = "pilot_*.json"


def _abs(rel: str) -> str:
    return os.path.join(sources.REPO_ROOT, *rel.split("/"))


def _walk(rel_dir: str) -> list[str]:
    """Sorted entry names under a repo-relative directory. The oracle's eyes."""
    try:
        return sorted(os.listdir(_abs(rel_dir)))
    except OSError:
        return []


def _curve_names_present(entry: str) -> list[str]:
    """Which of the accepted cost-record spellings this directory carries."""
    return [
        n
        for n in THEORIA_CURVE_NAMES
        if os.path.isfile(_abs(f"{THEORIA_ROOT}/{entry}/{n}"))
    ]


def _curve_calls(entry: str) -> list | None:
    """The per-call records under whichever spelling is present, or ``None``.

    Both dialects are read, because the oracle must be able to see a run under
    either name whatever the rule currently accepts. ``bill_shape.json`` wraps
    the list in a document; ``cost_curve.json`` is the bare list. An unreadable
    or unrecognised file counts as **present with unknown contents**, reported
    as an empty call list beside a manifest that may claim spend -- which is a
    failure downstream, not a silent skip.
    """
    present = _curve_names_present(entry)
    if not present:
        return None
    try:
        with open(_abs(f"{THEORIA_ROOT}/{entry}/{present[0]}"), encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("calls"), list):
        return payload["calls"]
    return []


def _theoria_dirs_with_cost() -> list[tuple[str, list, dict]]:
    """``(dir, cost_rows, manifest)`` for every run directory on disk that billed.

    Walked, not read out of the registry. The registry's opinion of which runs
    exist is precisely what is being audited.
    """
    out: list[tuple[str, list, dict]] = []
    for entry in _walk(THEORIA_ROOT):
        rows = _curve_calls(entry)
        if rows is None:
            continue
        manifest_path = _abs(f"{THEORIA_ROOT}/{entry}/MANIFEST.json")
        if not os.path.isfile(manifest_path):
            # A curve with no manifest is not a run this question can ask about
            # -- there is no slug to look for on the plate and no outcome to
            # carry. It is a half-written directory, and it is named as one by
            # _partial_theoria_dirs. Reporting it here as well would be the same
            # directory failing twice under two descriptions, and the second
            # description ("neither drawn nor named") would be false: it is
            # named, one section up.
            continue
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        out.append((entry, rows, manifest))
    return out


def _manifest_claims_spend(entry: str) -> bool | None:
    """Did this run directory's own manifest say it billed anything?

    ``True`` it claims spend, ``False`` it claims none, ``None`` it makes no
    claim either way (no ``cost`` block at all -- an ordinary work-run
    directory, not a campaign leg). Unreadable counts as a claim: a manifest
    nobody can parse is not evidence of innocence.
    """
    path = _abs(f"{THEORIA_ROOT}/{entry}/MANIFEST.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError):
        return True
    cost = manifest.get("cost")
    if not isinstance(cost, dict):
        return None
    usd = cost.get("cli_reported_usd")
    calls = cost.get("model_calls")
    return bool(usd) or bool(calls)


def _partial_theoria_dirs() -> tuple[list[str], list[str]]:
    """``(failures, named)`` over run directories carrying some members, not all.

    The rule skips these, correctly -- half a run is not a run. The oracle must
    not skip them on the same predicate, or a run that landed with a cost curve
    and a manifest still being written would be invisible to the rule and to its
    auditor at once, with the floor still satisfied.

    **But "some members, not all" is the wrong predicate for the failure**, and
    on 2026-07-29 it was wrong twelve times out of twelve. Every directory it
    flagged had a manifest and no cost curve for the same reason: there was
    nothing to write. Seven carry no ``cost`` block at all -- they are ordinary
    work-run directories (`a3-desk-gate`, `A11`, `E14-crash-is-not-a-finding`
    and so on), not campaign legs. The other five are salvage and preflight
    directories whose manifests state ``cli_reported_usd: 0.0`` and
    ``model_calls: 0``. A probe with twelve false alarms and no true one does
    not get read, and the case it exists for -- a *billing* run whose write was
    interrupted -- was the case it could no longer distinguish.

    So the failure now needs evidence, and the evidence is the run's own claim:
    a directory fails when its manifest says money moved and no cost curve
    stands beside it. The rest are still **named** -- which was always the
    demand ("a half-written run must be named, not silently dropped by both") --
    but naming and failing are separated, because they were never the same act.
    """
    failures: list[str] = []
    named: list[str] = []
    for entry in _walk(THEORIA_ROOT):
        curve_names = _curve_names_present(entry)
        present = [
            m for m in THEORIA_MEMBERS if os.path.isfile(_abs(f"{THEORIA_ROOT}/{entry}/{m}"))
        ] + curve_names
        # The curve role is one role under two spellings, so "all members" means
        # every plain member plus *at least one* curve name -- not both of them.
        # Counting the alternation as two members would have reported every run
        # in the repository as half-written, which is the same failure as
        # reporting none of them: a probe nobody can read.
        required = len(THEORIA_MEMBERS) + 1
        if not present or len(present) >= required:
            continue
        missing = [m for m in THEORIA_MEMBERS if m not in present]
        if not curve_names:
            missing = missing + [" or ".join(THEORIA_CURVE_NAMES)]
        shape = f"{entry} (has {', '.join(present)}; missing {', '.join(missing)})"
        claims = _manifest_claims_spend(entry)
        if claims:
            failures.append(
                f"theoria run directory {shape}: its own MANIFEST reports spend, and "
                "the cost curve that spend would be recorded in is absent. The "
                "discovery rule requires every member and so skips it, which means "
                "neither the rule nor this probe would otherwise notice that a "
                "billing run went missing from the plate."
            )
        else:
            named.append(
                f"{shape} -- {'no cost block; not a campaign leg' if claims is None else 'manifest states 0 model calls and $0.00'}"
            )
    return failures, named


def _rollups_on_disk() -> dict[str, str]:
    """``{run_id: file}`` over every roll-up on disk, registry not consulted."""
    found: dict[str, str] = {}
    for entry in _walk(ROLLUP_ROOT):
        # fnmatchcase, not fnmatch: fnmatch normcases on win32, so the same tree
        # would be inventoried differently on Windows and on Linux.
        if not fnmatch.fnmatchcase(entry, ROLLUP_PATTERN):
            continue
        path = _abs(f"{ROLLUP_ROOT}/{entry}")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, list):
            continue
        for row in payload:
            if isinstance(row, dict) and row.get("run_id"):
                found[row["run_id"]] = f"{ROLLUP_ROOT}/{entry}"
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
    partial_failures, _named = _partial_theoria_dirs()
    failures.extend(partial_failures)
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


#: A pattern matching exactly the four roll-ups the pre-P8 ``ROLLUP_KEYS`` tuple
#: named -- ``pilot_<game>-<hash>.json`` and not ``pilot_<game>_sonnet_rerun``.
#: The control narrows the **rule**, not the list the rule produced: a real
#: regression is somebody tightening a pattern or moving a root, and
#: ``DISCOVERED`` is derived state that nobody edits by hand. Narrowing derived
#: state exercised the one narrowing this probe already survived.
_PRE_P8_PATTERN = "pilot_????-*.json"

#: The two runs that drift D-1 left drawn as outcome-unknown.
_PRE_P8_VICTIMS = ("bare_cc-g50t-claude-sonnet-5-ddabe772", "bare_cc-sk48-claude-sonnet-5-9022a076")

#: The billing legs that the ``cost_curve.json`` -> ``bill_shape.json`` rename
#: hid from the plate between 2026-07-31 and 2026-08-01. Named, because a
#: control that says "some run fires" is satisfied by any accident.
_RENAME_VICTIMS = (
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
    "20260731T231654Z-R1-g50t-a",
    "20260731T231654Z-R1-sk48-b",
    "20260801T001851Z-R1b-g50t-a",
    "20260801T001851Z-R1b-sk48-b",
)


def _rename_control() -> list[str]:
    """Drop the ``bill_shape.json`` alternate and require the probe to fire.

    The defect of 2026-08-01, reconstructed. ``theoria-arm`` renamed its
    per-call cost record and ``sources.DISCOVERY``'s theoria rule named the old
    file, so seven billing legs -- tracked, committed, USD 85.60 between them --
    were read by nothing. The alternation in ``Rule.alternates`` is the fix, and
    this control is the reason to believe it is load-bearing rather than
    decorative: with the alternate removed, every one of the seven must be
    reported **by name**.

    It is a distinct control from the pre-P8 one above and not a variation of
    it. That one narrows a *pattern* and asks whether an outcome reaches the
    plate; this one narrows an *alternation* and asks whether a run reaches the
    plate at all. The first stayed green through this defect, which is the
    whole argument for writing the second: a control that passed over a live
    failure has been shown not to cover it.
    """
    problems: list[str] = []
    original_rules = sources.DISCOVERY
    original_found = dict(sources.DISCOVERED)
    try:
        sources.DISCOVERY = tuple(
            dataclasses.replace(r, alternates=(), floor=7)
            if r.name == fig02.THEORIA_RULE
            else r
            for r in original_rules
        )
        sources.DISCOVERED = {r.name: sources._discover(r) for r in sources.DISCOVERY}
        narrowed = len(sources.discovered_groups(fig02.THEORIA_RULE))
        if narrowed != 7:
            problems.append(
                "the rename control could not reconstruct the 2026-07-31 tree: expected "
                f"the un-alternated rule to find 7 theoria runs, it found {narrowed}"
            )
            return problems
        fired = check()
        for victim in _RENAME_VICTIMS:
            if not any(victim in f for f in fired):
                problems.append(
                    f"NEGATIVE CONTROL FAILED: with bill_shape.json removed from the "
                    f"theoria rule's alternation, {victim} bills real money and reaches "
                    "no figure, and the probe did not say so by name."
                )
    finally:
        sources.DISCOVERY = original_rules
        sources.DISCOVERED = original_found
    return problems


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

    # --- the spend-claim predicate, planted in memory ---------------------
    # The partial-directory check no longer fires on shape, it fires on the
    # run's own claim of spend. So the control for it plants that claim rather
    # than a file: every partial directory on disk currently claims none, and
    # one that claims some must fail. Done by substitution, not by writing into
    # `theoria-arm/runs/` -- another track's tree is not a scratch pad, and a
    # control that leaves debris is a control nobody runs twice.
    real_claims = _manifest_claims_spend
    partial_now, named_now = _partial_theoria_dirs()
    if partial_now:
        problems.append(
            "the spend-claim control cannot be read: a partial theoria directory "
            "is already failing, so a planted one proves nothing. Fix the real "
            "one first."
        )
    elif not named_now:
        problems.append(
            "no partial theoria run directory exists to plant a spend claim on. "
            "The control is unreachable; re-target it rather than deleting it."
        )
    else:
        victim = named_now[0].split(" (")[0]
        try:
            globals()["_manifest_claims_spend"] = (
                lambda entry: True if entry == victim else real_claims(entry))
            planted, _ = _partial_theoria_dirs()
            if not any(victim in line for line in planted):
                problems.append(
                    f"planted a spend claim on the partial directory {victim} and "
                    "the coverage probe stayed silent: a billing run whose cost "
                    "curve never landed would not be reported."
                )
        finally:
            globals()["_manifest_claims_spend"] = real_claims

    rule_name = fig02.ROLLUP_RULE
    original_rules = sources.DISCOVERY
    original_found = dict(sources.DISCOVERED)
    try:
        # Narrow the rule, then re-run discovery through the registry's own
        # machinery, exactly as a tightened pattern on master would behave.
        # Its floor is lowered too -- otherwise gate 0 catches the regression
        # first and the probe is never asked the question.
        sources.DISCOVERY = tuple(
            dataclasses.replace(r, pattern=_PRE_P8_PATTERN, floor=4)
            if r.name == rule_name
            else r
            for r in original_rules
        )
        sources.DISCOVERED = {
            r.name: sources._discover(r) for r in sources.DISCOVERY
        }
        narrowed = len(sources.DISCOVERED[rule_name])
        if narrowed != 4:
            problems.append(
                "self-test could not reconstruct the pre-P8 tree: expected the narrowed "
                f"rule to find 4 roll-ups, it found {narrowed}"
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
        sources.DISCOVERY = original_rules
        sources.DISCOVERED = original_found
    problems.extend(_rename_control())
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
            f"reports both runs it was written to catch ({', '.join(_PRE_P8_VICTIMS)}); "
            "with bill_shape.json dropped from the theoria rule's alternation, it "
            f"reports all {len(_RENAME_VICTIMS)} legs the 2026-08-01 rename hid."
        )
        return 0

    failures = check()
    n_theoria = len(_theoria_dirs_with_cost())
    n_rollups = len(_rollups_on_disk())
    if failures:
        for f in failures:
            print(f"COVERAGE: {f}")
        return 1
    _, named = _partial_theoria_dirs()
    for entry in named:
        print(f"COVERAGE-NAMED: partial theoria run directory, not a failure: {entry}")
    print(
        f"coverage ok: {n_theoria} billing theoria run(s), {len(named)} non-billing partial "
        f"directory(ies) named above, and {n_rollups} roll-up run_id(s) "
        "found by walking the tree; every cost-bearing run drawn or explained, every "
        "outcome on disk on the plate, every shape absence carrying its reason."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
