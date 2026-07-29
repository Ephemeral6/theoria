"""判卷器自检 -- who marks the marker.

`calibration.py` answers half of that question and says so: four fakes, and
`oracle == 1.0` / `null == 0.0` exact on every paper.  Those two numbers pin the
marker at its two **endpoints**.  A marker that is exact at both ends and
arbitrary in between passes every check that existed before this module.

So this module attacks the middle of the range, from two directions.

**Submission side -- mutants with a score predicted before the run.**  Take the
ground-truth submission, perturb it by a known amount, and require the score to
move by exactly the amount arithmetic says it must.  Six mutants, each pinning a
different way a marker can be wrong while still scoring 1.0 on truth and 0.0 on
silence:

    drop_exact      dropping a set S costs exactly what S was worth
    independence    dropping item i changes item i and nothing else
    key_order       reversing the key's item order changes no item's mark
    transplant      an answer correct for a *different* truth is not full marks
    monotone        more dropped, never more awarded
    garbage         structured nonsense pays nothing

**Marker side -- faults injected on purpose.**  Break the marker in a named way,
run every check, and record which checks notice.  The output is a matrix, and
**the zeros in it are the finding**: a fault that no check catches is a hole in
the calibration, reported as a hole rather than left for a later run to hit for
real.  A fault-injection suite that catches everything on the first try is
usually a suite that only injects faults it already knows how to catch, so the
faults here were chosen from how markers actually fail -- pay for silence,
reject truth, mark on something other than the answer, blend a pair that must
stay split, inflate or truncate partial credit -- and the misses are published.

Nothing here touches the network, a game, or a pile.  It is arithmetic over
papers this repository builds for itself.
"""

from __future__ import annotations

import contextlib
import importlib
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

from ..model import ExamError, Item, ItemScore, Paper, Submission, canonical
from ..papers import BUILDERS, module_for
from . import mark as mark_mod
from .mark import mark
from .registry import digest, rubric

#: What a mutant submits when it is asked to submit nonsense.  A string where
#: every rubric expects a mapping: the shape is wrong in the way a real arm's
#: output is wrong when its serialiser breaks, not in a way tailored to pass.
GARBAGE = "__V4_GARBAGE__"

#: Pre-registered, in the sense `calibration.py` uses the word: written down
#: before the first run, and if one fails it is reported as a failure rather
#: than widened.  Each is exact -- these are arithmetic identities about the
#: marker, not properties of item mix, so there is no band to draw.
PRE_REGISTERED: Dict[str, str] = {
    "drop_exact": "dropping a set of answers costs exactly the sum of what "
                  "those items were awarded, to the last decimal",
    "independence": "dropping one answer changes that item's mark and no "
                    "other item's mark. A marker that leaks state between "
                    "items is scoring the submission, not the answer.",
    "key_order": "reversing the order of items in the answer key changes no "
                 "item's mark. The order is an artefact of the builder; a mark "
                 "that depends on it is not a property of the answer.",
    "transplant": "an answer that is ground truth for an item with a different "
                  "truth does not earn full marks here. Full marks for a "
                  "transplanted answer means the rubric is checking shape and "
                  "calling it correctness.",
    "monotone": "dropping more answers never awards more points",
    "garbage": "a submission of structured nonsense scores exactly zero. If "
               "nonsense reads as an abstention and abstention pays, then a "
               "broken serialiser is indistinguishable from an honest refusal "
               "to answer, and both are being paid.",
    "partial_credit_survives":
        "an answer missing one component of a composite scores strictly "
        "between zero and full on a paper whose rubrics award partial credit. "
        "Added after the first fault-matrix run, which is the honest place to "
        "say why: every band in `calibration.EXPECTED` for the informative "
        "fakes is `Band(0.0, x)`, bounded above and open below, so a marker "
        "that silently *depresses* scores satisfies every one of them. "
        "`truncates_partial` was injected and no check anywhere noticed. This "
        "is the check that notices, and it is structural rather than a "
        "number fitted to what the first run happened to produce.",
}


# ---------------------------------------------------------------- small helpers

def _oracle_setup(question_type: str):
    module = module_for(question_type)
    paper = module.build()
    key_doc = paper.key(digest())
    answers = module.reference_answers(paper, key_doc, "oracle")
    return module, paper, key_doc, dict(answers)


def _submit(paper_id: str, answers: Dict[str, Any], tag: str) -> Submission:
    return Submission(examinee_id="mutant-%s" % tag, paper_id=paper_id,
                      answers=answers, capabilities=("answers",),
                      meta={"mutant": tag,
                            "note": "a marker self-test examinee, not a real arm"})


def _mark(key_doc: Dict[str, Any], answers: Dict[str, Any], tag: str,
          axes_fn: Optional[Callable] = None):
    return mark(key_doc, _submit(key_doc["paper_id"], answers, tag),
                axes_fn=axes_fn)


def _awarded_of(report) -> Dict[str, float]:
    return {s.item_id: round(s.awarded, 9) for s in report.scores}


def _verdict_of(report) -> Dict[str, str]:
    return {s.item_id: s.verdict for s in report.scores}


def _sample(ids: Sequence[str], cap: int) -> List[str]:
    """A deterministic spread over the paper, never the first `cap` items.

    Taking a prefix would sample one family of a paper whose items are grouped
    by family, which most of them are.
    """
    ids = list(ids)
    if len(ids) <= cap:
        return ids
    step = len(ids) / float(cap)
    return [ids[int(i * step)] for i in range(cap)]


def _drop_one_component(answer: Any) -> Optional[Any]:
    """The same answer with one component of a composite removed, or None.

    Deterministic and shape-driven: the first nested mapping with at least two
    entries loses its last key in sorted order.  Nothing here knows what any
    paper's answers mean -- an answer that is a flat value has no component to
    drop and returns None, which is why the check that uses this declares
    itself inapplicable rather than passing on those papers.
    """
    if not isinstance(answer, dict):
        return None
    for key in sorted(answer):
        value = answer[key]
        if isinstance(value, dict) and len(value) >= 2:
            out = dict(answer)
            out[key] = {k: v for k, v in value.items() if k != sorted(value)[-1]}
            return out
    return None


def _reordered_key(key_doc: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(key_doc)
    out["items"] = list(reversed(key_doc["items"]))
    return out


# ------------------------------------------------------------ the six mutants

def mutant_battery(question_type: str, *, cap: int = 8) -> Dict[str, Any]:
    """Run the six mutants on one paper.  Every expectation is exact."""
    module, paper, key_doc, oracle = _oracle_setup(question_type)
    axes_fn = getattr(module, "axes", None)
    base = _mark(key_doc, oracle, "oracle", axes_fn)
    base_awarded = _awarded_of(base)
    points_of = {e["item_id"]: float(e["points"]) for e in key_doc["items"]}
    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    rubric_of = {e["item_id"]: e["rubric_id"] for e in key_doc["items"]}
    ids = [e["item_id"] for e in key_doc["items"]]

    checks: Dict[str, Any] = {}
    failures: List[str] = []

    def record(name: str, ok: bool, detail: Dict[str, Any],
               message: Optional[str] = None) -> None:
        checks[name] = dict(detail, passed=bool(ok),
                            pre_registered=PRE_REGISTERED[name])
        if not ok:
            failures.append("%s/%s: %s" % (question_type, name,
                                           message or "expectation failed"))

    # -- 1. drop_exact --------------------------------------------------------
    dropped = _sample(ids, max(2, len(ids) // 3))
    thinned = {k: v for k, v in oracle.items() if k not in set(dropped)}
    got = _mark(key_doc, thinned, "drop_exact", axes_fn)
    predicted = round(base.awarded - sum(base_awarded[i] for i in dropped), 6)
    all_unanswered = all(v == "unanswered"
                         for i, v in _verdict_of(got).items() if i in set(dropped))
    ok = abs(got.awarded - predicted) < 1e-9 and all_unanswered
    record("drop_exact", ok,
           {"n_dropped": len(dropped), "predicted_awarded": predicted,
            "observed_awarded": got.awarded,
            "dropped_all_unanswered": all_unanswered},
           "predicted %.6f, observed %.6f (dropped items all unanswered: %s)"
           % (predicted, got.awarded, all_unanswered))

    # -- 2. independence ------------------------------------------------------
    bleed: List[Dict[str, Any]] = []
    for target in _sample(ids, cap):
        one_out = {k: v for k, v in oracle.items() if k != target}
        got = _mark(key_doc, one_out, "independence", axes_fn)
        after = _awarded_of(got)
        moved = [i for i in ids
                 if i != target and abs(after[i] - base_awarded[i]) > 1e-9]
        if moved:
            bleed.append({"dropped": target, "also_moved": sorted(moved)[:10],
                          "n_moved": len(moved)})
    record("independence", not bleed,
           {"n_probed": len(_sample(ids, cap)), "bleed": bleed},
           "dropping one answer moved other items' marks on %d of %d probes"
           % (len(bleed), len(_sample(ids, cap))))

    # -- 3. key_order ---------------------------------------------------------
    got = _mark(_reordered_key(key_doc), oracle, "key_order", axes_fn)
    after = _awarded_of(got)
    moved = [i for i in ids if abs(after.get(i, -1.0) - base_awarded[i]) > 1e-9]
    record("key_order", not moved,
           {"n_moved": len(moved), "moved": sorted(moved)[:10],
            "total_before": base.awarded, "total_after": got.awarded},
           "%d item(s) scored differently when the key was reversed" % len(moved))

    # -- 4. transplant --------------------------------------------------------
    # Only donor/host pairs where the *truths* differ: an answer that is right
    # for a different truth must not be full marks here.  Where two items share
    # a truth, an identical answer is legitimately correct and proves nothing.
    accepted: List[Dict[str, Any]] = []
    attempted = 0
    hosts = _sample(ids, cap)
    for host in hosts:
        donor = None
        for cand in ids:
            if cand == host or rubric_of[cand] != rubric_of[host]:
                continue
            if canonical(truth_of[cand]) == canonical(truth_of[host]):
                continue
            if cand not in oracle or host not in oracle:
                continue
            if canonical(oracle[cand]) == canonical(oracle[host]):
                continue
            donor = cand
            break
        if donor is None:
            continue
        attempted += 1
        swapped = dict(oracle)
        swapped[host] = oracle[donor]
        got = _mark(key_doc, swapped, "transplant", axes_fn)
        awarded_host = _awarded_of(got)[host]
        if awarded_host >= points_of[host] - 1e-9:
            accepted.append({"host": host, "donor": donor,
                             "awarded": awarded_host,
                             "possible": points_of[host]})
    record("transplant", not accepted,
           {"n_attempted": attempted, "n_accepted": len(accepted),
            "accepted": accepted[:10]},
           "%d of %d transplanted answers earned full marks" % (len(accepted),
                                                                attempted))

    # -- 5. monotone ----------------------------------------------------------
    ladder: List[Dict[str, Any]] = []
    violations: List[str] = []
    previous = None
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        n = int(round(frac * len(ids)))
        drop = set(ids[:n])
        got = _mark(key_doc, {k: v for k, v in oracle.items() if k not in drop},
                    "monotone", axes_fn)
        ladder.append({"dropped_fraction": frac, "n_dropped": n,
                       "awarded": got.awarded})
        if previous is not None and got.awarded > previous + 1e-9:
            violations.append("dropping %d answers awarded %.6f, more than the "
                              "%.6f awarded when fewer were dropped"
                              % (n, got.awarded, previous))
        previous = got.awarded
    record("monotone", not violations, {"ladder": ladder,
                                        "violations": violations},
           "; ".join(violations))

    # -- 6. garbage -----------------------------------------------------------
    garbage_answers = {i: GARBAGE for i in ids}
    raised: Optional[str] = None
    garbage_awarded: Optional[float] = None
    try:
        got = _mark(key_doc, garbage_answers, "garbage", axes_fn)
        garbage_awarded = got.awarded
        garbage_counts = {v: sum(1 for s in got.scores if s.verdict == v)
                          for v in ("correct", "wrong", "abstained", "unanswered")}
    except Exception as exc:                        # noqa: BLE001 -- reported
        raised = "%s: %s" % (type(exc).__name__, exc)
        garbage_counts = {}
    ok = raised is None and garbage_awarded is not None and garbage_awarded == 0.0
    record("garbage", ok,
           {"raised": raised, "awarded": garbage_awarded,
            "possible": base.possible, "counts": garbage_counts,
            "fraction": (round(garbage_awarded / base.possible, 6)
                         if garbage_awarded is not None and base.possible else None)},
           ("the marker raised %s" % raised) if raised else
           "structured nonsense was awarded %.6f of %.6f"
           % (garbage_awarded or 0.0, base.possible))

    # -- 7. partial_credit_survives ------------------------------------------
    degraded: Dict[str, Any] = {}
    n_degraded = 0
    for iid, answer in oracle.items():
        weaker = _drop_one_component(answer)
        if weaker is None:
            degraded[iid] = answer
        else:
            degraded[iid] = weaker
            n_degraded += 1
    if n_degraded:
        got = _mark(key_doc, degraded, "partial", axes_fn)
        strictly_partial = [s.item_id for s in got.scores
                            if 1e-9 < s.awarded < points_of[s.item_id] - 1e-9]
        record("partial_credit_survives", bool(strictly_partial),
               {"applicable": True, "n_degraded": n_degraded,
                "n_strictly_partial": len(strictly_partial),
                "examples": sorted(strictly_partial)[:5],
                "awarded": got.awarded, "possible": got.possible},
               "%d answers were degraded and not one scored strictly between "
               "zero and full: the marker has collapsed the middle of its own "
               "range" % n_degraded)
    else:
        # No composite answers to degrade. Vacuous here, and said out loud
        # rather than reported as a pass -- a check that cannot run is not a
        # check that passed (DECISIONS.md D-EX-011 is the same lesson).
        record("partial_credit_survives", True,
               {"applicable": False, "n_degraded": 0,
                "why": "no answer on this paper is a composite with a "
                       "removable component, so there is nothing to degrade"})

    return {
        "question_type": question_type,
        "paper_id": paper.paper_id,
        "n_items": len(ids),
        "oracle_fraction": base.fraction,
        "checks": checks,
        "failures": failures,
        "passed": not failures,
    }


def mutant_battery_all(question_types: Optional[Sequence[str]] = None,
                       *, cap: int = 8) -> Dict[str, Any]:
    types = list(question_types or BUILDERS)
    per_type = {qt: mutant_battery(qt, cap=cap) for qt in types}
    failures = [f for r in per_type.values() for f in r["failures"]]
    return {"pre_registered": dict(PRE_REGISTERED), "per_type": per_type,
            "failures": failures, "passed": not failures}


# ------------------------------------------------------- injected marker faults

@contextlib.contextmanager
def _patched(target: Any, name: str, value: Any) -> Iterator[None]:
    original = getattr(target, name)
    setattr(target, name, value)
    try:
        yield
    finally:
        setattr(target, name, original)


def _wrap_rubric(transform: Callable[[ItemScore, Any, Item], ItemScore]):
    """Replace `mark`'s rubric lookup with one whose grade is transformed.

    This is the seam every score-side fault goes through: `mark()` calls
    `rubric(item.rubric_id).grade(...)` and nothing else, so a fault injected
    here is a fault in marking and cannot be anything else.
    """
    from ..model import Rubric

    def looked_up(rubric_id: str) -> Rubric:
        real = rubric(rubric_id)

        def graded(answer, truth, item):
            return transform(real.grade(answer, truth, item), answer, item)

        return Rubric(rubric_id=real.rubric_id, description=real.description,
                      grade=graded)

    return looked_up


def _full(item: Item, why: str) -> ItemScore:
    return ItemScore(item.item_id, item.rubric_id, item.points, item.points,
                     "correct", {"injected_fault": why})


def _zero(score: ItemScore, why: str) -> ItemScore:
    return ItemScore(score.item_id, score.rubric_id, 0.0, score.possible,
                     "wrong", dict(score.detail, injected_fault=why))


def _fault_pays_for_silence():
    def fake_unanswered(item, why="no answer submitted"):
        return _full(item, "unanswered items are paid in full")
    return [(mark_mod, "unanswered", fake_unanswered)]


def _fault_rejects_truth():
    def transform(score, answer, item):
        if score.verdict == "correct":
            return _zero(score, "correct answers are marked wrong")
        return score
    return [(mark_mod, "rubric", _wrap_rubric(transform))]


def _fault_marks_by_item_name():
    def transform(score, answer, item):
        if sum(ord(c) for c in score.item_id) % 2 == 0:
            return _full(item, "marked on the item's name, not the answer")
        return _zero(score, "marked on the item's name, not the answer")
    return [(mark_mod, "rubric", _wrap_rubric(transform))]


def _fault_accepts_anything():
    def transform(score, answer, item):
        return _full(item, "any answer that is present is accepted")
    return [(mark_mod, "rubric", _wrap_rubric(transform))]


def _fault_order_dependent():
    state = {"n": 0}

    def transform(score, answer, item):
        state["n"] += 1
        if state["n"] % 2 == 0:
            return _zero(score, "every second item marked is zeroed")
        return score
    return [(mark_mod, "rubric", _wrap_rubric(transform))]


def _fault_inflates_partial():
    def transform(score, answer, item):
        if 1e-9 < score.awarded < score.possible - 1e-9:
            return ItemScore(score.item_id, score.rubric_id, score.possible,
                             score.possible, "correct",
                             dict(score.detail, injected_fault="partial rounded up"))
        return score
    return [(mark_mod, "rubric", _wrap_rubric(transform))]


def _fault_truncates_partial():
    def transform(score, answer, item):
        if 1e-9 < score.awarded < score.possible - 1e-9:
            return _zero(score, "partial credit truncated to zero")
        return score
    return [(mark_mod, "rubric", _wrap_rubric(transform))]


def _fault_blends_the_pair():
    """The one fault that is not about points: report one accuracy twice.

    Theoria.md 1.11 requires sensitivity and specificity as a pair.  A marker
    that computes both and then reports their blend is right about every
    individual answer and wrong about the only thing the verdict paper exists
    to measure -- so nothing on the score side can catch it.
    """
    real = mark_mod.confusion

    def blended(report, key_doc, *, positive):
        out = dict(real(report, key_doc, positive=positive))
        n_right = sum(1 for s in report.scores if s.verdict == "correct")
        accuracy = round(n_right / len(report.scores), 6) if report.scores else 0.0
        out["sensitivity"] = accuracy
        out["specificity"] = accuracy
        out["injected_fault"] = "the pair was replaced by one accuracy"
        return out

    targets = [(mark_mod, "confusion", blended)]
    for qt in BUILDERS:
        module = module_for(qt)
        if hasattr(module, "confusion"):
            targets.append((module, "confusion", blended))
    return targets


#: Fault name -> builder of (module, attribute, replacement) patches.  Chosen
#: from how markers actually fail, not from what these checks already catch.
FAULTS: Dict[str, Callable[[], List[Tuple[Any, str, Any]]]] = {
    "pays_for_silence": _fault_pays_for_silence,
    "rejects_truth": _fault_rejects_truth,
    "marks_by_item_name": _fault_marks_by_item_name,
    "accepts_anything": _fault_accepts_anything,
    "order_dependent": _fault_order_dependent,
    "inflates_partial": _fault_inflates_partial,
    "truncates_partial": _fault_truncates_partial,
    "blends_the_pair": _fault_blends_the_pair,
}

FAULT_NOTES: Dict[str, str] = {
    "pays_for_silence": "an unanswered item is awarded full marks -- every "
                        "real score is inflated by the amount the examinee "
                        "left blank",
    "rejects_truth": "a correct answer is marked wrong -- every real score is "
                     "depressed by an unknown amount",
    "marks_by_item_name": "the mark is a function of the item id and ignores "
                          "the answer entirely",
    "accepts_anything": "any answer that is present earns full marks; content "
                        "is never read",
    "order_dependent": "the mark depends on how many items were marked before "
                       "it, so the same answer scores differently in a "
                       "different key",
    "inflates_partial": "partial credit is rounded up to full",
    "truncates_partial": "partial credit is truncated to zero",
    "blends_the_pair": "sensitivity and specificity are both replaced by one "
                       "blended accuracy",
}


def _run_all_checks(question_types: Sequence[str], *, cap: int) -> Dict[str, List[str]]:
    """Every check this repository has, as {check_family: [failure lines]}."""
    from .calibration import calibrate_all

    out: Dict[str, List[str]] = {}
    try:
        calib = calibrate_all(question_types)
        out["calibration"] = list(calib["failures"])
    except Exception as exc:                        # noqa: BLE001 -- reported
        out["calibration"] = ["raised %s: %s" % (type(exc).__name__, exc)]
    try:
        mutants = mutant_battery_all(question_types, cap=cap)
        for qt, res in mutants["per_type"].items():
            for name, entry in res["checks"].items():
                out.setdefault("mutant:%s" % name, [])
                if not entry["passed"]:
                    out["mutant:%s" % name].append("%s: failed" % qt)
    except Exception as exc:                        # noqa: BLE001 -- reported
        out["mutant:raised"] = ["raised %s: %s" % (type(exc).__name__, exc)]
    return out


def fault_matrix(question_types: Optional[Sequence[str]] = None,
                 *, cap: int = 4) -> Dict[str, Any]:
    """Inject each fault, run every check, record which checks noticed.

    `cap` is smaller here than in a standalone battery run: the batteries run
    once per fault, and the mutants that matter for detection are the ones that
    fire at all rather than the ones that fire the most times.
    """
    types = list(question_types or BUILDERS)

    baseline = _run_all_checks(types, cap=cap)
    baseline_noise = {k: v for k, v in baseline.items() if v}

    rows: Dict[str, Any] = {}
    uncaught: List[str] = []
    for name, build_patches in sorted(FAULTS.items()):
        patches = build_patches()
        with contextlib.ExitStack() as stack:
            for target, attr, value in patches:
                stack.enter_context(_patched(target, attr, value))
            observed = _run_all_checks(types, cap=cap)
        caught_by = sorted(k for k, v in observed.items() if v and not baseline.get(k))
        rows[name] = {
            "what_it_does": FAULT_NOTES[name],
            "caught_by": caught_by,
            "n_catchers": len(caught_by),
            "caught": bool(caught_by),
            "detail": {k: v[:4] for k, v in observed.items() if v},
        }
        if not caught_by:
            uncaught.append(name)

    return {
        "checks_available": sorted(baseline),
        "baseline_clean": not baseline_noise,
        "baseline_noise": baseline_noise,
        "faults": rows,
        "uncaught": uncaught,
        "n_faults": len(rows),
        "n_uncaught": len(uncaught),
    }


def selftest(question_types: Optional[Sequence[str]] = None, *,
             cap: int = 8, faults: bool = True,
             fault_cap: int = 4) -> Dict[str, Any]:
    types = list(question_types or BUILDERS)
    battery = mutant_battery_all(types, cap=cap)
    out: Dict[str, Any] = {
        "protocol_digest": protocol_digest(),
        "rubric_digest": digest(),
        "mutants": battery,
        "passed": battery["passed"],
    }
    if faults:
        matrix = fault_matrix(types, cap=fault_cap)
        out["fault_matrix"] = matrix
        # An uncaught fault is a hole to report, not a failed run: the run that
        # reports it is doing its job. A *dirty baseline* is a failed run --
        # it means a check was already firing before anything was injected.
        out["passed"] = out["passed"] and matrix["baseline_clean"]
    return out


# ------------------------------------------------------------ protocol digest

#: The files that decide what a mark means, hashed together.  `registry.digest`
#: covers the rubrics and travels onto every sheet; it deliberately does **not**
#: cover the marker or the calibration bands, and `calibration.py` says so in a
#: comment above `EXPECTED` ("a quiet widening here would not show up as a
#: digest mismatch").  This is that hole closed from the outside: the value is
#: pinned by a test, so widening a band or loosening the marker forces a
#: deliberate edit to the pin and a line in DECISIONS.md.
#:
#: It is a separate hash rather than an extension of `registry.digest` on
#: purpose -- extending that one would change every sheet's seal and every
#: stored artefact, which is a large blast radius for a check that does not
#: need to travel on the sheet.
PROTOCOL_MODULES: Tuple[str, ...] = (
    "exam.grading.mark",
    "exam.grading.calibration",
    "exam.grading.selftest",
)


def protocol_digest() -> str:
    """sha256 over the source of the marker, the bands, and this self-test."""
    import hashlib
    import inspect

    hasher = hashlib.sha256()
    for name in PROTOCOL_MODULES:
        source = inspect.getsource(importlib.import_module(name))
        one = hashlib.sha256(source.encode("utf-8")).hexdigest()
        hasher.update(("%s:%s\n" % (name, one)).encode("utf-8"))
    return hasher.hexdigest()


def protocol_module_digests() -> Dict[str, str]:
    import hashlib
    import inspect

    out = {}
    for name in PROTOCOL_MODULES:
        source = inspect.getsource(importlib.import_module(name))
        out[name] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return out
