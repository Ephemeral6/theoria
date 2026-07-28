"""Adjudicate `semantics:` for the A0 world by refuting the other value.

`CONTRACTS/dsl_grammar_v0.2.md` makes `semantics:` mandatory and says why in the
migration note: the three statements are per-world facts, and "if you do not know
which is true, that is a finding to probe, not a default to accept". This is that
probe.

The method is falsification, not fit. For each statement the manual is replayed
under **both** admissible values against the ground-truth world, over every
representable state of all five evidence levels. A value is adjudicated only when
its alternative is refuted by a concrete witness. A reading that merely fits is
not evidence: `persist` and `reset` agree on every transition in which a rule
happens to mention every object, and a probe that only confirmed would never
notice.

Ground truth (`world/sokoban2.py`) is used **only to grade**, never to predict --
the standing rule in `pipeline/stages.py`. The predictor is always the module
compiled from `theory/theory.dsl`.

Run:  python -m probes.semantics_probe  [--out <dir>]
"""

import argparse
import json
import os
import sys
from dataclasses import replace
from typing import Any, Dict, List, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from pipeline import cross_form, gen_exec                      # noqa: E402
from world import levels, sokoban2                             # noqa: E402

# A manual that has not been migrated yet cannot be parsed at all, and the probe
# has to run *before* the migration or it is not what decided it. So a v0.1
# manual is given a syntactically minimal candidate block for the duration of the
# probe. The values in it are inert: `gen_exec` compiles rules and events and
# never reads the section. Which is itself the hazard this whole exercise is
# about -- see FINDINGS in the run's RUN_STATE.md.
CANDIDATE_BLOCK = """
semantics:
  frame     persist
  conflict  exclusive
  cascade   single_frame
"""

MULTI_FRAME_BOUND = 64          # board is 7x7; any real cascade quiesces far inside


def manual_text() -> Tuple[str, bool]:
    """The manual, plus a flag: did the probe have to supply the section?"""
    path = os.path.join(HERE, "theory", "theory.dsl")
    text = open(path, encoding="utf-8").read()
    if "semantics:" in text:
        return text, False
    marker = "events:"
    at = text.index(marker)
    return text[:at] + CANDIDATE_BLOCK.strip() + "\n\n" + text[at:], True


# --------------------------------------------------------------- object claims

# Which objects an event *writes*. Read off the manual's event vocabulary
# together with `gen_exec._compile_effect`, which is the only thing that gives
# those events meaning in an executable form.
#
# `slid` is the one that matters and the one an event name alone gets wrong: it
# is **compound**. A push moves the Box two cells *and* carries the Player one,
# because the frozen grammar allows a rule exactly one event while a push
# visibly does two things (`gen_exec.py` docstring, and 表达力台账 X-1).
# v0.2 §"Discharging `conflict`" makes the obligation per object over rules whose
# claimed objects intersect, so understating `slid` to `{Box}` would understate
# what has to be proved. It is read wide here on purpose.
EVENT_WRITES = {
    "moved": lambda obj: {obj},
    "stayed": lambda obj: {obj},
    "slid": lambda obj: {obj, "player"},
}

ALL_OBJECTS = ("player", "box")


def rule_claims(dsl_text: str) -> Dict[str, frozenset]:
    """rule name -> the set of objects its event writes."""
    from theory_compiler.parser.theory_parser import parse_theory

    theory = parse_theory(dsl_text)
    out = {}
    for rule in theory.rules.rules:
        event = rule.event
        name = getattr(event, "name", None)
        if name not in EVENT_WRITES:
            raise SystemExit("probe does not know what event %r writes" % name)
        args = getattr(event, "args", [])
        obj = getattr(args[0], "name", "").lower() if args else ""
        out[rule.name] = frozenset(EVENT_WRITES[name](obj))
    return out


# ------------------------------------------------------------------- predictors

def fire(module: Dict[str, Any], state, direction: str) -> List[Tuple[str, Any]]:
    """Every rule that fires, with the successor it alone would produce.

    Each rule is handed a fresh copy of the **pre-state**, which is what
    `cascade single_frame`'s parenthetical demands: "every guard reads the
    pre-state and all effects apply together".
    """
    fired = []
    for name, rule in module["RULES"]:
        trial = replace(state)
        if rule(trial, direction):
            fired.append((name, trial))
    return fired


def predict_persist(module, state, direction):
    """`frame persist`: an object no firing rule mentions is unchanged."""
    fired = fire(module, state, direction)
    if len(fired) != 1:
        return None, fired
    return fired[0][1], fired


def predict_reset(module, state, direction, initial, claims):
    """`frame reset`: such an object returns to its declared initial value."""
    fired = fire(module, state, direction)
    if len(fired) != 1:
        return None, fired
    name, successor = fired[0]
    written = claims[name]
    for obj in ALL_OBJECTS:
        if obj not in written:
            setattr(successor, obj, getattr(initial, obj))
    return successor, fired


def predict_multi_frame(module, state, direction):
    """`cascade multi_frame`: rules re-fire on each intermediate state.

    **The action is held across rounds, and that is an assumption of this probe,
    not a fact about the contract.** `CONTRACTS/dsl_grammar_v0.2.md` says only
    "one action yields a frame sequence; rules re-fire until quiescence" and does
    not fix whether the action survives into round 2. Two readings:

    * **held** (this function) -- every A0 rule guards on `act=move(Player, dir)`,
      nothing switches the action off, `walk` re-fires, and the player slides
      until something stops it. A genuinely different world, and refutable.
    * **consumed** -- no A0 rule can fire in round 2 at all, quiescence is
      immediate, and `multi_frame` is observationally *identical* to
      `single_frame` on every pair. Nothing is refuted because nothing differs.

    The contract's own motivating example (`press_left` recolours a button and
    `door_opens_left` re-reads its guard) is a *state*-triggered second round, so
    it does not settle this either -- if anything it leans consumed.

    `single_frame` is the right declaration under both, but only the held reading
    makes this probe's witness count mean anything. The argument that does not
    depend on the reading is in THEORIZE_LOG T-11c: A0 has no action-free rule,
    so the world has no self-triggering tick to declare.
    """
    current = state
    for _ in range(MULTI_FRAME_BOUND):
        fired = fire(module, current, direction)
        if len(fired) != 1:
            return None, "ambiguous"
        successor = fired[0][1]
        if (successor.player, successor.box) == (current.player, current.box):
            return current, "quiescent"
        current = successor
    return current, "bound-reached"


# ------------------------------------------------------------------ experiments

def representable(level) -> List[Tuple[int, int, int, int, str]]:
    """Every representable state-action pair, not the reachable ones.

    D-TC-012 and v0.2 §"Discharging `conflict`" both: `conflict` is a claim about
    the domain, and reachability is a property of one starting configuration.
    T-9 is this repository's own instance -- all 8 mismatching states were
    unreachable, and the rule was still wrong.

    **Objects standing on walls are included.** An earlier revision of this probe
    filtered them out, on the reasoning that no play can reach them. That is the
    reachability argument D-TC-012 forbids, one level down. Sweeping the wider
    set costs nothing, so the wider set is what is swept, and `on_wall` records
    how much of it the old filter was dropping.

    A second revision kept the wide sweep but excluded the on-wall stratum from
    the `frame` and `cascade` verdicts, claiming those states have no frame of
    their own because `render` paints the object over the wall. **That claim is
    false and the adversarial review caught it**: within one level the wall set
    is fixed, `render` writes PLAYER and BOX at one cell each, and the map from
    representable states to frames is injective -- measured, 2352 states of
    `match`, 2352 distinct frames, 0 collisions. What the frame hides is the
    *wall*, which is level-static data the compiled module already holds. Those
    states are observable and the manual really is wrong about 52 of them.

    So nothing is excluded on observability grounds, and the verdict rule below
    does not need it to be: see `_discriminating`.

    The one exclusion left is `player == box` (in `cross_form.enumerate_cases`),
    and that one *is* an observability argument and survives: `render` writes
    PLAYER after BOX at the same cell, so the box's position is genuinely
    unrecoverable from the frame. The two exclusions were never the same kind of
    thing, and an earlier revision of this docstring leaned on the second to
    justify the first.
    """
    walls = set(level.walls)
    return [
        (case, (case[0], case[1]) in walls or (case[2], case[3]) in walls)
        for case in cross_form.enumerate_cases(level.height, level.width)
    ]


def run() -> Dict[str, Any]:
    dsl_text, supplied = manual_text()
    claims = rule_claims(dsl_text)

    frame = {"reading": "persist vs reset", "cases": 0,
             "persist_mismatches": 0, "reset_mismatches": 0, "witnesses": [],
             "persist_mismatches_by_stratum": {"off_wall": 0, "on_wall": 0},
             "reset_mismatches_by_stratum": {"off_wall": 0, "on_wall": 0},
             "persist_only": 0, "reset_only": 0, "both_wrong": 0,
             "on_wall_witnesses": []}
    conflict = {"cases": 0, "max_rules_fired": 0, "max_common_object_claims": 0,
                "no_rule_fired": 0, "violations": [],
                "strata": {"off_wall": 0, "on_wall": 0},
                "max_common_object_claims_by_stratum": {"off_wall": 0, "on_wall": 0}}
    cascade = {"reading": "single_frame vs multi_frame", "cases": 0,
               "single_frame_mismatches": 0, "multi_frame_mismatches": 0,
               "rounds_histogram": {}, "witnesses": [],
               "single_frame_mismatches_by_stratum": {"off_wall": 0, "on_wall": 0},
               "multi_frame_mismatches_by_stratum": {"off_wall": 0, "on_wall": 0},
               "single_frame_only": 0, "multi_frame_only": 0, "both_wrong": 0}
    per_level = {}

    for level in (levels.MATCH,) + levels.CROSSING_LEVELS:
        module = gen_exec.compile_module(
            dsl_text, level.height, level.width, level.walls)
        State = module["State"]
        initial = State(player=level.player, box=level.box)
        counts = {"cases": 0, "persist": 0, "reset": 0,
                  "single_frame": 0, "multi_frame": 0, "conflicts": 0}

        for (pr, pc, br, bc, direction), on_wall in representable(level):
            stratum = "on_wall" if on_wall else "off_wall"
            conflict["strata"][stratum] += 1
            state = State(player=(pr, pc), box=(br, bc))
            truth, _event = sokoban2.step(
                level, sokoban2.State(player=(pr, pc), box=(br, bc)), direction)
            observed = (truth.player, truth.box)

            # --- conflict: the exhaustive sweep, under the wide reading of `slid`
            fired = fire(module, state, direction)
            conflict["cases"] += 1
            conflict["max_rules_fired"] = max(conflict["max_rules_fired"], len(fired))
            if not fired:
                conflict["no_rule_fired"] += 1
            worst = 0
            for obj in ALL_OBJECTS:
                claimants = [n for n, _ in fired if obj in claims[n]]
                worst = max(worst, len(claimants))
                if len(claimants) > 1:
                    counts["conflicts"] += 1
                    if len(conflict["violations"]) < 10:
                        conflict["violations"].append({
                            "level": level.name, "object": obj,
                            "state": [[pr, pc], [br, bc]], "action": direction,
                            "rules": claimants})
            conflict["max_common_object_claims"] = max(
                conflict["max_common_object_claims"], worst)
            conflict["max_common_object_claims_by_stratum"][stratum] = max(
                conflict["max_common_object_claims_by_stratum"][stratum], worst)

            # --- frame: persist against reset
            persist_succ, _ = predict_persist(module, state, direction)
            reset_succ, _ = predict_reset(module, state, direction, initial, claims)
            frame["cases"] += 1
            counts["cases"] += 1
            persist_wrong = (persist_succ is None
                             or (persist_succ.player, persist_succ.box) != observed)
            reset_wrong = (reset_succ is None
                           or (reset_succ.player, reset_succ.box) != observed)
            if persist_wrong and reset_wrong:
                frame["both_wrong"] += 1
            elif persist_wrong:
                frame["persist_only"] += 1
            elif reset_wrong:
                frame["reset_only"] += 1
            if persist_wrong:
                frame["persist_mismatches"] += 1
                frame["persist_mismatches_by_stratum"][stratum] += 1
                counts["persist"] += 1
                if on_wall and len(frame["on_wall_witnesses"]) < 8:
                    frame["on_wall_witnesses"].append({
                        "level": level.name, "action": direction,
                        "state": {"player": [pr, pc], "box": [br, bc]},
                        "who_is_on_a_wall": [
                            who for who, cell in (("player", (pr, pc)), ("box", (br, bc)))
                            if cell in set(level.walls)],
                        "world": {"player": list(truth.player), "box": list(truth.box)},
                        "manual": None if persist_succ is None else {
                            "player": list(persist_succ.player),
                            "box": list(persist_succ.box)},
                        "why": "a `push2` guard defect, not a frame question: the world "
                               "checks is_wall(target) before target != box, so a box "
                               "parked on a wall blocks the player, and no guard can say "
                               "`the Box is not on a wall`. `reset` predicts the same "
                               "wrong successor here, so this case discriminates nothing. "
                               "See RUN_STATE FINDING-2 and ledger X-5."})
            if reset_wrong:
                frame["reset_mismatches"] += 1
                frame["reset_mismatches_by_stratum"][stratum] += 1
                counts["reset"] += 1
                if len(frame["witnesses"]) < 5:
                    frame["witnesses"].append({
                        "level": level.name, "action": direction,
                        "state": {"player": [pr, pc], "box": [br, bc]},
                        "world": {"player": list(truth.player), "box": list(truth.box)},
                        "under_reset": None if reset_succ is None else {
                            "player": list(reset_succ.player),
                            "box": list(reset_succ.box)},
                        "why": "no firing rule mentions the box, so `reset` "
                               "returns it to its declared initial value"})

            # --- cascade: single_frame against multi_frame
            multi_succ, status = predict_multi_frame(module, state, direction)
            cascade["cases"] += 1
            cascade["rounds_histogram"][status] = \
                cascade["rounds_histogram"].get(status, 0) + 1
            # `single_frame`'s predictor is `predict_persist`: one round, guards
            # against the pre-state. That is the same object the frame check
            # graded, which is why `persist_wrong` is reused rather than recomputed.
            multi_wrong = (multi_succ is None
                           or (multi_succ.player, multi_succ.box) != observed)
            if persist_wrong and multi_wrong:
                cascade["both_wrong"] += 1
            elif persist_wrong:
                cascade["single_frame_only"] += 1
            elif multi_wrong:
                cascade["multi_frame_only"] += 1
            if persist_wrong:
                cascade["single_frame_mismatches"] += 1
                cascade["single_frame_mismatches_by_stratum"][stratum] += 1
                counts["single_frame"] += 1
            if multi_wrong:
                cascade["multi_frame_mismatches"] += 1
                cascade["multi_frame_mismatches_by_stratum"][stratum] += 1
                counts["multi_frame"] += 1
                if len(cascade["witnesses"]) < 5:
                    cascade["witnesses"].append({
                        "level": level.name, "action": direction,
                        "state": {"player": [pr, pc], "box": [br, bc]},
                        "world": {"player": list(truth.player), "box": list(truth.box)},
                        "under_multi_frame": None if multi_succ is None else {
                            "player": list(multi_succ.player),
                            "box": list(multi_succ.box)},
                        "why": "every rule guards on the same action, so holding it "
                               "across rounds lets `walk` re-fire and the player "
                               "slides until something stops it"})
        per_level[level.name] = counts

    # `frame` and `cascade` are adjudicated on the **observationally
    # representable** stratum, and `conflict` on the whole sweep. The asymmetry
    # is not convenience, and it is the one judgement call in this probe:
    #
    # `conflict` is a claim about the rule set -- do two rules ever claim one
    # object at once -- and a rule set can be asked that about any assignment of
    # coordinates, frame or no frame. It discharges over everything, so it is
    # asked over everything.
    #
    # `frame` and `cascade` are claims about what succeeds what, and they are
    # graded by comparing a prediction to the world. On an on-wall state that
    # comparison is not meaningful: `world/sokoban2.render` paints walls first
    # and the object over them, so an object standing on a wall produces the
    # *same frame* as the same object standing on bare floor. No observation
    # denotes such a state, so the manual is not wrong about it -- there is
    # nothing there to be wrong about. That is the same reason
    # `cross_form.enumerate_cases` already drops `player == box`, applied
    # consistently rather than only where it was noticed first.
    #
    # The stratum is reported rather than filtered, because "excluded as
    # unobservable" and "excluded because it would have failed" are the same
    # arithmetic and must not be the same sentence. FINDING-2 in RUN_STATE.md
    # carries the 52.
    verdict = {
        "frame": "persist" if (frame["persist_only"] == 0
                               and frame["reset_only"] > 0) else "UNDECIDED",
        "conflict": "exclusive" if conflict["max_common_object_claims"] <= 1
                    else "NOT-exclusive",
        "cascade": "single_frame" if (cascade["single_frame_only"] == 0
                                      and cascade["multi_frame_only"] > 0)
                   else "UNDECIDED",
    }
    verdict["adjudicated_on"] = {
        "frame": "the whole sweep; cases where both readings mispredict are "
                 "excluded because they discriminate nothing, not because of "
                 "where they sit",
        "conflict": "the whole sweep, both strata, unconditional",
        "cascade": "the whole sweep, same rule as frame",
        "both_wrong_is_a_finding": (
            "%d cases mispredict under BOTH readings of `frame` and both of "
            "`cascade`. They are not evidence about either statement -- they are "
            "a `push2` guard defect (ledger X-5), and they are reported here "
            "rather than filtered out so that the count cannot quietly become a "
            "count of something else."
            % frame["both_wrong"]),
    }
    return {
        "probe": "semantics_probe",
        "manual": "theory/theory.dsl",
        "section_supplied_by_probe": supplied,
        "rule_claims": {k: sorted(v) for k, v in sorted(claims.items())},
        "levels": sorted(per_level),
        "per_level": per_level,
        "frame": frame,
        "conflict": conflict,
        "cascade": cascade,
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="directory for the JSON")
    args = parser.parse_args()

    result = run()
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "semantics_probe.json")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("-> %s" % path)

    v = result["verdict"]
    f, c, k = result["frame"], result["conflict"], result["cascade"]
    print("semantics probe -- %d representable state-action pairs across %d levels"
          % (f["cases"], len(result["levels"])))
    print("  strata    off_wall %d | on_wall %d (both swept and both adjudicated on; "
          "the stratum is reported, not excluded)"
          % (c["strata"]["off_wall"], c["strata"]["on_wall"]))
    print("  frame     persist-only %d | reset-only %d | both wrong %d   -> %s"
          % (f["persist_only"], f["reset_only"], f["both_wrong"], v["frame"]))
    print("  conflict  max rules firing %d; max claimants of one object %d "
          "(off_wall %d / on_wall %d); states with no rule %d   -> %s"
          % (c["max_rules_fired"], c["max_common_object_claims"],
             c["max_common_object_claims_by_stratum"]["off_wall"],
             c["max_common_object_claims_by_stratum"]["on_wall"],
             c["no_rule_fired"], v["conflict"]))
    print("  cascade   single_frame-only %d | multi_frame-only %d | both wrong %d   -> %s"
          % (k["single_frame_only"], k["multi_frame_only"], k["both_wrong"],
             v["cascade"]))
    print("  finding   %d cases wrong under BOTH readings -- a push2 guard defect "
          "(ledger X-5), evidence about neither statement" % f["both_wrong"])
    undecided = [name for name, value in v.items()
                 if value in ("UNDECIDED", "NOT-exclusive")]
    if undecided:
        print("  UNDECIDED/refuted: %s -- do not migrate on this" % ", ".join(undecided))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
