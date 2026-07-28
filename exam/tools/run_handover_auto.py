"""Drive the layered handover test end to end, without a human in the middle.

    python -m exam.tools.run_handover_auto build   --run <run_dir>
    python -m exam.tools.run_handover_auto score   --run <run_dir>

`build` writes the sheet, the two examinee prompts, and a pre-registration
record; `score` re-derives the answer key, checks it against the digest the
pre-registration froze, marks every answer file that has arrived, and reports
the tier difference with an interval around it.

**Why the answer key is not written at build time.**  The examinees are
subagents.  They run on the same machine, with the same filesystem, and an
instruction not to look around is an instruction, not a wall.  So the key is
never written to disk before the answers are in: `build()` is deterministic, so
`score` can re-derive it, and what `build` stores is the *digest* of the key it
would have written.  A key that matches a digest committed before the examinees
ran is pre-registered in the only sense that survives an adversary with a shell.

**Why the difference is reported with an interval and not as a number.**  A
delta smaller than the noise of the instrument that produced it is not a small
effect, it is not an effect.  Two intervals are computed and both must exclude
zero before the difference is quoted as one: a bootstrap over examinees (do
readers of the same tier agree?) and a bootstrap over items (would a different
sheet have said the same?).  The marker's own contribution is measured
separately and is expected to be exactly zero -- see `grader_noise`.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import guard, leakage                                     # noqa: E402
from exam.grading.mark import mark                                  # noqa: E402
from exam.grading.registry import digest, module_digests            # noqa: E402
from exam.model import (Paper, Submission, canonical, sha256,       # noqa: E402
                        sha256_text, read_json, write_json)
from exam.papers import handover_auto as HA                         # noqa: E402

#: How many bootstrap resamples.  Fixed, with a fixed seed: an interval that
#: moves between runs is not an interval, it is a mood.
BOOTSTRAP_N = 20000
BOOTSTRAP_SEED = 20260729


# ------------------------------------------------------------------- helpers

def _git(*args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", REPO, *args], capture_output=True,
                             text=True, check=True)
        return out.stdout.strip()
    except Exception:                                # pragma: no cover
        return "unknown"


def _sheet_and_key(paper: Paper) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rubric_digest = digest()
    module_digest = module_digests().get("exam.grading.rubrics_handover_auto")
    return (paper.sheet(rubric_digest, module_digest),
            paper.key(rubric_digest))


# --------------------------------------------------------------------- build

def build(run_dir: str) -> Dict[str, Any]:
    """Write the sheet, the prompts and the pre-registration.  No key on disk."""
    with guard.no_network():
        paper = HA.build()
        sheet, key_doc = _sheet_and_key(paper)
        leak = leakage.check_paper(paper, sheet, key_doc=key_doc,
                                   answer_of=HA.answer_labels(paper, key_doc))

    os.makedirs(run_dir, exist_ok=True)
    prompts_dir = os.path.join(run_dir, "prompts")
    os.makedirs(prompts_dir, exist_ok=True)

    sheet_path = write_json(os.path.join(run_dir, "sheet.json"), sheet)
    prompt_digests = {}
    for tier in HA.TIERS:
        text = HA.prompt_text(tier, sheet)
        path = os.path.join(prompts_dir, "%s.prompt.md" % tier)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        prompt_digests[tier] = {"path": path, "sha256": sha256_text(text),
                                "bytes": len(text.encode("utf-8"))}

    prereg = {
        "prompt_id": HA.PROMPT_ID,
        "paper_id": HA.PAPER_ID,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "HEAD"),
        "rubric_digest": digest(),
        "rubric_module_digests": module_digests(),
        "sheet_sha256": sha256(sheet),
        "key_sha256": sha256(key_doc),
        "key_written_to_disk": False,
        "key_note": ("the answer key is deliberately not written until the "
                     "examinees have answered. `score` re-derives it from the "
                     "deterministic builder and refuses to mark if the digest "
                     "does not match the value frozen here."),
        "n_items": len(paper.items),
        "total_points": sheet["total_points"],
        "prediction": HA.PREDICTION,
        "prompts": prompt_digests,
        "bundle_sha256": {t: sha256_text(HA.bundle_text(t)) for t in HA.TIERS},
        # Counts and hit totals only.  The full report carries
        # `positional.example_ids_by_answer` and `label_counts`, which together
        # are a literal answer-label -> item-id map: the adversarial review of
        # this run marked a submission built from nothing but that block and
        # scored 0.603 on a paper it had never seen, on a file sitting in the
        # examinees' own run directory. The build's job is to record that the
        # check ran and passed, not to publish what it found.
        "leakage": {k: v for k, v in leak.items()
                    if k not in ("positional", "positional_derived")},
        "leakage_note": ("the positional block is deliberately not persisted; "
                         "it is an answer key in a different spelling. Re-run "
                         "`leakage.check_paper` to see it."),
        "bootstrap": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
    }
    write_json(os.path.join(run_dir, "PREREGISTRATION.json"), prereg)
    os.makedirs(os.path.join(run_dir, "answers"), exist_ok=True)
    return {"sheet_path": sheet_path, "prereg": prereg}


# --------------------------------------------------------------------- score

def _load_answers(run_dir: str) -> List[Dict[str, Any]]:
    """Every answer file in the run, newest name order, as submissions."""
    adir = os.path.join(run_dir, "answers")
    out = []
    for name in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        if not name.endswith(".json"):
            continue
        doc = read_json(os.path.join(adir, name))
        out.append(doc)
    return out


def grader_noise(key_doc: Dict[str, Any],
                 submissions: Sequence[Submission]) -> Dict[str, Any]:
    """How much of the spread is the marker's own?

    Two probes.  *Repeat*: mark the same submission twice and compare the score
    -- a marker with any state or any ordering dependence shows up here.
    *Cosmetic*: mark a perturbed copy whose answers mean exactly what the
    originals meant (different case, extra spaces, reordered fields, reordered
    citations) and compare again.  Both differences are expected to be exactly
    zero, and the point of running them is that "expected" and "measured" are
    different words.

    A non-zero result here would put a floor under every delta this run reports,
    which is why it is computed before the delta and quoted beside it.
    """
    def _perturb(answer: Any) -> Any:
        if not isinstance(answer, str):
            return answer
        text = answer.strip()
        if text.lower() == "abstain":
            return "  ABSTAIN  "
        if "rests_on=" in text:
            body = text.split("=", 1)[1]
            parts = [p.strip() for p in body.split("+") if p.strip()]
            return "  rests_on = " + " + ".join(reversed(parts)) + "  "
        if ";" in text:
            parts = [p.strip() for p in text.split(";") if p.strip()]
            fields = []
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    fields.append("%s = %s" % (k.strip().upper(), v.strip()))
                else:
                    fields.append(part)
            return " ;  ".join(reversed(fields)) + " "
        return "  %s  " % text

    repeat_max = 0.0
    cosmetic_max = 0.0
    per_examinee = {}
    for sub in submissions:
        one = mark(key_doc, sub).awarded
        two = mark(key_doc, sub).awarded
        perturbed = Submission(examinee_id=sub.examinee_id,
                               paper_id=sub.paper_id,
                               answers={k: _perturb(v)
                                        for k, v in sub.answers.items()},
                               capabilities=sub.capabilities, meta=sub.meta)
        three = mark(key_doc, perturbed).awarded
        per_examinee[sub.examinee_id] = {
            "awarded": round(one, 6),
            "repeat_delta": round(two - one, 6),
            "cosmetic_delta": round(three - one, 6),
        }
        repeat_max = max(repeat_max, abs(two - one))
        cosmetic_max = max(cosmetic_max, abs(three - one))
    return {
        "repeat_max_abs_delta_points": round(repeat_max, 6),
        "cosmetic_max_abs_delta_points": round(cosmetic_max, 6),
        "per_examinee": per_examinee,
        "note": ("the marker's own inconsistency, in points. A tier difference "
                 "smaller than this is the marker talking, not the tiers."),
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pct(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = int(round(q * (len(sorted_values) - 1)))
    return sorted_values[max(0, min(len(sorted_values) - 1, index))]


def bootstrap_over_examinees(tier1: Sequence[float], tier2: Sequence[float],
                             *, n: int = BOOTSTRAP_N,
                             seed: int = BOOTSTRAP_SEED) -> Dict[str, Any]:
    """Resample readers with replacement.  Answers: would other readers agree?"""
    rng = random.Random(seed)
    if not tier1 or not tier2:
        return {"ci": None, "note": "a tier with no examinee has no interval"}
    draws = []
    for _ in range(n):
        a = _mean([rng.choice(tier1) for _ in tier1])
        b = _mean([rng.choice(tier2) for _ in tier2])
        draws.append(b - a)
    draws.sort()
    low, high = _pct(draws, 0.025), _pct(draws, 0.975)
    return {"point": round(_mean(tier2) - _mean(tier1), 6),
            "ci95": [round(low, 6), round(high, 6)],
            "excludes_zero": bool(low > 0 or high < 0),
            "n_tier1": len(tier1), "n_tier2": len(tier2), "resamples": n}


def bootstrap_over_items(per_item: Dict[str, Dict[str, List[float]]], *,
                         n: int = BOOTSTRAP_N,
                         seed: int = BOOTSTRAP_SEED) -> Dict[str, Any]:
    """Resample items with replacement.  Answers: would another sheet agree?

    Fractions are recomputed inside each resample from the resampled items'
    awarded and possible points, so an item worth three points counts for three
    points -- averaging per-item fractions would silently reweight the sheet.
    """
    rng = random.Random(seed + 1)
    item_ids = sorted(per_item)
    if not item_ids:
        return {"ci": None, "note": "no items"}

    def _frac(ids: Sequence[str], tier: str) -> float:
        got = sum(_mean(per_item[i][tier]) for i in ids)
        can = sum(per_item[i]["possible"][0] for i in ids)
        return got / can if can else 0.0

    one, two = HA.TIER1, HA.TIER2
    point = _frac(item_ids, two) - _frac(item_ids, one)
    draws = []
    for _ in range(n):
        sample = [rng.choice(item_ids) for _ in item_ids]
        draws.append(_frac(sample, two) - _frac(sample, one))
    draws.sort()
    low, high = _pct(draws, 0.025), _pct(draws, 0.975)
    return {"point": round(point, 6), "ci95": [round(low, 6), round(high, 6)],
            "excludes_zero": bool(low > 0 or high < 0),
            "n_items": len(item_ids), "resamples": n}


def score(run_dir: str) -> Dict[str, Any]:
    prereg = read_json(os.path.join(run_dir, "PREREGISTRATION.json"))
    with guard.no_network():
        paper = HA.build()
        sheet, key_doc = _sheet_and_key(paper)

    key_now = sha256(key_doc)
    if key_now != prereg["key_sha256"]:
        raise RuntimeError(
            "the answer key re-derived now (%s) is not the key frozen before "
            "the examinees ran (%s). Either the builder changed or the world "
            "did; in both cases these answers cannot be marked against this "
            "pre-registration." % (key_now[:12], prereg["key_sha256"][:12]))
    if sha256(sheet) != prereg["sheet_sha256"]:
        raise RuntimeError("the sheet re-derived now is not the sheet the "
                           "examinees sat")

    docs = _load_answers(run_dir)
    subs: List[Submission] = []
    for doc in docs:
        subs.append(HA.submission(doc["examinee_id"], doc["tier"],
                                  doc.get("answers", {}),
                                  meta=doc.get("meta", {})))

    # calibration first: an uncalibrated marker's output is not a result
    calib = {}
    for mode in HA.CALIBRATION_MODES:
        fake = HA.reference_answers(paper, key_doc, mode)
        report = mark(key_doc, Submission("calib-" + mode, HA.PAPER_ID, fake))
        calib[mode] = {"fraction": report.fraction, "awarded": report.awarded,
                       "possible": report.possible,
                       "counts": report.to_json()["counts"]}
    if abs(calib["oracle"]["fraction"] - 1.0) > 1e-9:
        raise RuntimeError("the oracle does not score 1.0 (%s): the rubric "
                           "rejects a correct answer, so every score below is "
                           "depressed by an unknown amount"
                           % calib["oracle"]["fraction"])
    if abs(calib["null"]["fraction"]) > 1e-9:
        raise RuntimeError("the null examinee scores above zero: the marker "
                           "pays for silence")

    reports = []
    tag_of = {e["item_id"]: tuple(e.get("tags", ())) for e in key_doc["items"]}
    for sub in subs:
        report = mark(key_doc, sub, axes_fn=None,
                      meta={"tier": sub.meta.get("tier")})
        reports.append((sub, report))

    by_tier: Dict[str, List[float]] = {t: [] for t in HA.TIERS}
    per_item: Dict[str, Dict[str, List[float]]] = {}
    per_examinee = []
    for sub, report in reports:
        tier = sub.meta["tier"]
        by_tier[tier].append(report.fraction)
        per_examinee.append({
            "examinee_id": sub.examinee_id, "tier": tier,
            "awarded": report.awarded, "possible": report.possible,
            "fraction": report.fraction,
            "counts": report.to_json()["counts"],
            "by_tag": report.axes.get("by_tag", {}),
            "report": report.to_json(),
        })
        for item_score in report.scores:
            slot = per_item.setdefault(
                item_score.item_id,
                {"tier1_manual": [], "tier2_manual_playbook": [],
                 "possible": [item_score.possible]})
            slot[tier].append(item_score.awarded)

    complete = [iid for iid, slot in per_item.items()
                if slot[HA.TIER1] and slot[HA.TIER2]]
    boot_items = bootstrap_over_items(
        {iid: per_item[iid] for iid in complete}) if complete else {
            "ci95": None, "note": "no item was answered in both tiers"}
    boot_readers = bootstrap_over_examinees(by_tier[HA.TIER1],
                                            by_tier[HA.TIER2])
    noise = grader_noise(key_doc, [s for s, _ in reports])

    families = {}
    for family in HA.FAMILIES:
        means = {}
        for tier in HA.TIERS:
            fracs = []
            for sub, report in reports:
                if sub.meta["tier"] != tier:
                    continue
                got = sum(s.awarded for s in report.scores
                          if family in tag_of.get(s.item_id, ()))
                can = sum(s.possible for s in report.scores
                          if family in tag_of.get(s.item_id, ()))
                if can:
                    fracs.append(got / can)
            means[tier] = round(_mean(fracs), 6) if fracs else None
        if means[HA.TIER1] is not None and means[HA.TIER2] is not None:
            families[family] = {**means,
                                "delta": round(means[HA.TIER2]
                                               - means[HA.TIER1], 6)}
        else:
            families[family] = means

    tier1_mean = round(_mean(by_tier[HA.TIER1]), 6)
    tier2_mean = round(_mean(by_tier[HA.TIER2]), 6)
    saturated = max(tier1_mean, tier2_mean) > 0.95
    conclusive = bool(boot_readers.get("excludes_zero")
                      and boot_items.get("excludes_zero")
                      and not saturated)

    result = {
        "prompt_id": HA.PROMPT_ID,
        "paper_id": HA.PAPER_ID,
        "rubric_digest": digest(),
        "key_sha256": key_now,
        "matches_preregistration": True,
        "calibration": calib,
        "n_examinees": {t: len(by_tier[t]) for t in HA.TIERS},
        "tier_means": {HA.TIER1: tier1_mean, HA.TIER2: tier2_mean},
        "delta": round(tier2_mean - tier1_mean, 6),
        "by_family": families,
        "bootstrap_over_examinees": boot_readers,
        "bootstrap_over_items": boot_items,
        "grader_noise": noise,
        "saturated": saturated,
        "saturation_rule": HA.PREDICTION["saturation_guard"],
        "conclusive": conclusive,
        "verdict": (
            "the tier difference is larger than the noise of the instruments "
            "that produced it" if conclusive else
            "no conclusion: the difference does not clear its own error bars, "
            "or the sheet saturated. Reporting the point estimate as a finding "
            "would be the mistake V17 made."),
        "examinees": per_examinee,
        "per_item": {iid: {k: v for k, v in slot.items()}
                     for iid, slot in sorted(per_item.items())},
    }
    write_json(os.path.join(run_dir, "RESULTS.json"), result)
    return result


# ---------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "score"))
    parser.add_argument("--run", required=True, help="the run directory")
    args = parser.parse_args(argv)

    if args.action == "build":
        out = build(args.run)
        prereg = out["prereg"]
        print("built %s: %d items, %.6g points"
              % (prereg["paper_id"], prereg["n_items"], prereg["total_points"]))
        print("  rubric digest %s" % prereg["rubric_digest"][:12])
        print("  sheet  sha256 %s" % prereg["sheet_sha256"][:12])
        print("  key    sha256 %s  (frozen, not written)"
              % prereg["key_sha256"][:12])
        for tier, info in sorted(prereg["prompts"].items()):
            print("  prompt %-24s %d bytes  %s"
                  % (tier, info["bytes"], info["sha256"][:12]))
        return 0

    result = score(args.run)
    print("tier means: %s" % json.dumps(result["tier_means"]))
    print("delta      : %s" % result["delta"])
    print("readers CI : %s" % result["bootstrap_over_examinees"].get("ci95"))
    print("items   CI : %s" % result["bootstrap_over_items"].get("ci95"))
    print("grader noise (points): repeat %s cosmetic %s"
          % (result["grader_noise"]["repeat_max_abs_delta_points"],
             result["grader_noise"]["cosmetic_max_abs_delta_points"]))
    print("conclusive : %s" % result["conclusive"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
