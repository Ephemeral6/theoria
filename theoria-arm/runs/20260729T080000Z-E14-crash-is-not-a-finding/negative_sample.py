"""E14 item 3: the negative sample, and the proof that it is not vacuous.

Three columns for each of the three sites, dumped as artifacts rather than as
"a test passed":

    control        -- no injected crash. Must be green, or nothing below means
                      anything.
    poisoned       -- a `step` / a `synthesize` constructed to raise. Must go
                      RED: the exhaustiveness field must be false and the crash
                      count must be non-zero.
    counting off   -- the identical injected crash with the counting logic
                      removed and nothing else changed. This reproduces the
                      pre-E14 behaviour, and it must come back CLEAN. If it did
                      not, the poisoned column would be passing for some other
                      reason and the whole gate could be decoration.

Offline. No API, no network, no model call.

    python runs/20260729T080000Z-E14-crash-is-not-a-finding/negative_sample.py
"""

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ARM)
RAW = os.path.join(HERE, "raw")

sys.path.insert(0, ARM)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))
sys.path.insert(0, REPO)

import _bootstrap                                     # noqa: E402,F401

from inner import certify, commit, plan as plan_beat  # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402
from world.frames import FrameStore, Step             # noqa: E402


class Boom(RuntimeError):
    """Neither site declares this type, so it can only land in the bare
    `except Exception` handlers this ticket is about."""


class CrashingStep:
    def __init__(self, inner):
        self.inner = inner
        self.raised = 0

    def __call__(self, state, action):
        self.raised += 1
        raise Boom("injected: the compiled manual fell over on %r" % (action,))


def _namespace(slug, goal):
    workdir = os.path.join(RAW, "negative-" + slug)
    if os.path.isdir(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    books = Books(workdir)
    books.write(theory=WORKED_EXAMPLE.replace("goal count(Cart) = 1", goal),
                playbook="# none\n")
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    books.compile_all()
    namespace, error = books.load_predictor()
    if namespace is None:
        raise RuntimeError(error)
    return namespace


def _no_counting(cls):
    """Remove the counting logic and nothing else."""
    original = cls.record
    cls.record = lambda self, exc, **kw: None
    return original


def plan_site():
    out = {}
    ns = _namespace("plan", "goal Cart.pos = (2, 2)")
    out["control"] = plan_beat._tier_bfs(ns, node_cap=plan_beat.BFS_NODE_CAP)

    crashing = CrashingStep(ns["step"])
    out["poisoned"] = plan_beat._tier_bfs(dict(ns, step=crashing),
                                          node_cap=plan_beat.BFS_NODE_CAP)
    out["poisoned_raises"] = crashing.raised

    original = _no_counting(plan_beat.StepCrashLog)
    try:
        crashing2 = CrashingStep(ns["step"])
        out["counting_removed"] = plan_beat._tier_bfs(
            dict(ns, step=crashing2), node_cap=plan_beat.BFS_NODE_CAP)
        out["counting_removed_raises"] = crashing2.raised
    finally:
        plan_beat.StepCrashLog.record = original
    return out


def certify_site():
    out = {}
    ns = _namespace("certify", "goal count(Cart) = 1")
    store = FrameStore()
    store.add(Step(0, "RESET", [[[0, 0, 0], [0, 0, 0], [0, 6, 0]]]))
    out["control"] = certify._ambiguity(ns, store, commit.action_to_manual)

    crashing = CrashingStep(ns["step"])
    out["poisoned"] = certify._ambiguity(dict(ns, step=crashing), store,
                                         commit.action_to_manual)
    out["poisoned_raises"] = crashing.raised

    original = _no_counting(certify.StepCrashLog)
    try:
        crashing2 = CrashingStep(ns["step"])
        out["counting_removed"] = certify._ambiguity(
            dict(ns, step=crashing2), store, commit.action_to_manual)
        out["counting_removed_raises"] = crashing2.raised
    finally:
        certify.StepCrashLog.record = original
    return out


A0_DRIVER = r'''
import json, os, sys
here = os.path.abspath(sys.argv[1])
sys.path.insert(0, here)
sys.path.insert(0, os.path.join(os.path.dirname(here), "engine-rig"))
from pipeline import explore, stages
from world import levels

class Boom(RuntimeError):
    pass

def exploding(positives, universe, masks):
    exploding.n += 1
    raise Boom("injected: synthesis fell over")
exploding.n = 0

transitions = stages.transitions_from_episodes(
    explore.evidence_set(levels.MATCH, per_class=4)["episodes"])
out = {}

rules, account = stages.mine_with_account(transitions)
out["control"] = {"account": account.as_json(),
                  "n_rules": len(rules),
                  "n_unsound": sum(1 for r in rules if r.unsound_after_crash)}

real = stages.synthesize
stages.synthesize = exploding
try:
    rules, account = stages.mine_with_account(transitions)
    out["poisoned"] = {"account": account.as_json(),
                       "n_rules": len(rules),
                       "n_unsound": sum(1 for r in rules if r.unsound_after_crash),
                       "sample_rule": sorted(rules, key=lambda r: r.name)[0].as_json()}
    out["poisoned_raises"] = exploding.n

    original = stages.MiningAccount.record_crash
    stages.MiningAccount.record_crash = lambda self, exc, **kw: None
    try:
        exploding.n = 0
        rules, account = stages.mine_with_account(transitions)
        out["counting_removed"] = {
            "account": account.as_json(),
            "n_rules": len(rules),
            "n_unsound": sum(1 for r in rules if r.unsound_after_crash),
            "sample_rule": sorted(rules, key=lambda r: r.name)[0].as_json()}
        out["counting_removed_raises"] = exploding.n
    finally:
        stages.MiningAccount.record_crash = original
finally:
    stages.synthesize = real

json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1,
          sort_keys=True, default=str, ensure_ascii=False)
'''


def a0_site():
    driver = os.path.join(RAW, "_a0_negative_driver.py")
    out_path = os.path.join(RAW, "_a0_negative.json")
    with open(driver, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(A0_DRIVER)
    done = subprocess.run(
        [sys.executable, driver, os.path.join(REPO, "a0-spike"), out_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=os.path.join(REPO, "a0-spike"))
    if done.returncode != 0:
        raise RuntimeError("the A0 negative sample did not complete (exit %d):"
                           "\n%s" % (done.returncode, done.stderr[-2000:]))
    with open(out_path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    os.makedirs(RAW, exist_ok=True)
    result = {"plan": plan_site(), "certify": certify_site(), "a0_mine": a0_site()}

    verdicts = []

    p = result["plan"]
    verdicts.append({
        "site": "theoria-arm/inner/plan.py  _tier_bfs",
        "claim_field": "status / exhaustive",
        "control": "%s exhaustive=%s crashes=%s states=%s"
                   % (p["control"]["status"], p["control"]["exhaustive"],
                      p["control"]["step_crashes"]["count"],
                      p["control"]["reachable_states"]),
        "poisoned": "%s exhaustive=%s crashes=%s states=%s"
                    % (p["poisoned"]["status"], p["poisoned"]["exhaustive"],
                       p["poisoned"]["step_crashes"]["count"],
                       p["poisoned"]["reachable_states"]),
        "counting_removed": "%s exhaustive=%s crashes=%s states=%s"
                            % (p["counting_removed"]["status"],
                               p["counting_removed"]["exhaustive"],
                               p["counting_removed"]["step_crashes"]["count"],
                               p["counting_removed"]["reachable_states"]),
        "red_when_poisoned": p["poisoned"]["status"] == "unsat_unsound"
                             and p["poisoned"]["exhaustive"] is False,
        "waved_through_without_counting":
            p["counting_removed"]["status"] == "unsat"
            and p["counting_removed"]["exhaustive"] is True
            and p["counting_removed_raises"] > 0,
    })

    c = result["certify"]
    verdicts.append({
        "site": "theoria-arm/inner/certify.py  _ambiguity",
        "claim_field": "ok (constraint 9)",
        "control": "ok=%s crashes=%s %s/%s pairs"
                   % (c["control"]["ok"], c["control"]["step_crashes"]["count"],
                      c["control"]["pairs_checked"], c["control"]["pairs_nominal"]),
        "poisoned": "ok=%s crashes=%s %s/%s pairs"
                    % (c["poisoned"]["ok"], c["poisoned"]["step_crashes"]["count"],
                       c["poisoned"]["pairs_checked"],
                       c["poisoned"]["pairs_nominal"]),
        "counting_removed": "ok=%s crashes=%s %s/%s pairs"
                            % (c["counting_removed"]["ok"],
                               c["counting_removed"]["step_crashes"]["count"],
                               c["counting_removed"]["pairs_checked"],
                               c["counting_removed"]["pairs_nominal"]),
        "red_when_poisoned": c["poisoned"]["ok"] is False,
        "waved_through_without_counting":
            c["counting_removed"]["ok"] is True
            and c["counting_removed_raises"] > 0,
        "caveat": (
            "Same caveat as the a0 row, which the first pass gave only to a0 "
            "and an adversarial review demanded here too. Removing "
            "`StepCrashLog.record` removes the gate and hands `ok: true` back "
            "to a sweep that crashed. It does NOT remove the second mechanism "
            "the same change added: `pairs_checked` increments only on a "
            "non-raise, so `pairs_checked (%s) < pairs_nominal (%s)` still "
            "betrays the crash in the counting-removed column. Pre-E14 "
            "`_ambiguity` had neither field, so this column is an ablation of "
            "the gate, not a byte-faithful reproduction of the old code. Note "
            "also that the surviving `detail` sentence says \"all %s pairs were "
            "adjudicated\" while `pairs_checked` is %s -- it is built from the "
            "nominal product, which is the original defect, visible here "
            "because the gate that normally suppresses that sentence is off."
            % (c["counting_removed"]["pairs_checked"],
               c["counting_removed"]["pairs_nominal"],
               c["counting_removed"]["pairs_nominal"],
               c["counting_removed"]["pairs_checked"])),
    })

    a = result["a0_mine"]
    verdicts.append({
        "site": "a0-spike/pipeline/stages.py  mine",
        "claim_field": "all_guards_searched / disjunction_is_a_finding",
        "control": "searched=%s crashes=%s no_sep_guard=%s unsound_rules=%s"
                   % (a["control"]["account"]["all_guards_searched"],
                      a["control"]["account"]["synthesis_crashes"],
                      a["control"]["account"]["classes_no_separating_guard"],
                      a["control"]["n_unsound"]),
        "poisoned": "searched=%s crashes=%s no_sep_guard=%s unsound_rules=%s"
                    % (a["poisoned"]["account"]["all_guards_searched"],
                       a["poisoned"]["account"]["synthesis_crashes"],
                       a["poisoned"]["account"]["classes_no_separating_guard"],
                       a["poisoned"]["n_unsound"]),
        "counting_removed": "searched=%s crashes=%s no_sep_guard=%s unsound_rules=%s"
                            % (a["counting_removed"]["account"]["all_guards_searched"],
                               a["counting_removed"]["account"]["synthesis_crashes"],
                               a["counting_removed"]["account"]["classes_no_separating_guard"],
                               a["counting_removed"]["n_unsound"]),
        "red_when_poisoned":
            a["poisoned"]["account"]["all_guards_searched"] is False
            and a["poisoned"]["n_unsound"] == a["poisoned"]["n_rules"],
        "waved_through_without_counting":
            a["counting_removed"]["account"]["all_guards_searched"] is True
            and a["counting_removed_raises"] > 0,
        "caveat": (
            "The ablation removes `MiningAccount.record_crash` -- the counting "
            "-- and that is enough to hand `all_guards_searched: true` back to "
            "a run whose synthesis crashed %d times. It does NOT remove the "
            "second mechanism added by the same change: the per-rule "
            "`disjunctive_because: synthesis_crashed` stamp is set on the "
            "exception branch itself, so `unsound_rules` stays %d in the "
            "counting-removed column. So this column is a faithful ablation of "
            "the *gate*, not a byte-faithful reproduction of the pre-E14 code, "
            "which had neither. Reported this way round because the opposite "
            "reading -- 'the crash was caught anyway, so the gate is optional' "
            "-- is the error this ticket is about."
            % (a["poisoned"]["account"]["synthesis_crashes"],
               a["counting_removed"]["n_unsound"])),
    })

    result["verdicts"] = verdicts
    result["all_sites_go_red_when_poisoned"] = all(
        v["red_when_poisoned"] for v in verdicts)
    result["all_sites_wave_it_through_without_counting"] = all(
        v["waved_through_without_counting"] for v in verdicts)

    path = os.path.join(RAW, "negative_sample.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")

    for v in verdicts:
        print("\n%s   [%s]" % (v["site"], v["claim_field"]))
        print("    control          %s" % v["control"])
        print("    POISONED         %s   -> red? %s"
              % (v["poisoned"], v["red_when_poisoned"]))
        print("    counting removed %s   -> waved through? %s"
              % (v["counting_removed"], v["waved_through_without_counting"]))
    print("\nall sites go red when poisoned:            %s"
          % result["all_sites_go_red_when_poisoned"])
    print("all sites wave it through without counting: %s"
          % result["all_sites_wave_it_through_without_counting"])
    return 0 if (result["all_sites_go_red_when_poisoned"]
                 and result["all_sites_wave_it_through_without_counting"]) else 1


if __name__ == "__main__":
    sys.exit(main())
