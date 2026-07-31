"""Mock campaign for framework change A -- probe economics. Offline, no spend.

Two legs of the same scripted world, identical seed, identical everything except
the one flag. The world is deterministic and its true dynamics are deliberately
*not* what the manual says, because that is the condition the four live legs of
2026-07-31 were actually in: 47 of 52 completed probes landed off the frontier.
A mock in which the manual is right would measure nothing, since the rule that
matters -- retire the probe class after N off-frontier results -- would never be
reached.

What is real here: `inner.probe.design`, `inner.probe.ProbeEconomy`,
`inner.probe.ProbeLog`, `inner.surprise.Register`, and `engines.probe_frontier`.
What is scripted: the world, the legal actions, and a `theorize` that grows the
manual by one rule when the register says the manual is wrong. Nothing calls a
model and nothing touches the network.

    python mock_campaign.py            # writes campaign_off.json / campaign_on.json / COMPARISON.json
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import probe as probe_beat                 # noqa: E402
from inner.probe import ProbeEconomy, ProbeEconomyConfig   # noqa: E402
from inner.surprise import KINDS, Register            # noqa: E402

ACTIONS = [1, 2, 3, 4, 5]
BUDGET_ACTIONS = 40
SEED = 20260801

#: How many theorize rounds it takes to add a rule *schema* to the manual.
#:
#: Not 1, and this is the number the mock most has to get right. Theorize fires
#: on every refutation, but it usually rewrites a rule body and leaves the
#: schema set alone -- r3 measured 28 probe refutations against only 3 distinct
#: hypothesis-id sets, and r2 measured 8 against 2. A mock that grew the manual
#: on every refutation would open a new generation every turn, reset every
#: counter every turn, and show change A doing nothing at all. It would also be
#: a lie about the live legs. 8 is r3's ratio, rounded to the pessimistic side.
RULES_GROW_EVERY = 8


# ---------------------------------------------------------------- the world
#: The world starts latched. The manual has no concept of a latch, so its
#: predictions are wrong from the first action -- which is the condition the
#: live legs were in, and the only condition under which probe economics is
#: worth measuring at all.
WORLD_START = (0, 1, 0)
MANUAL_START = (0, 1, 0)


def true_step(state, key):
    """The world. Deterministic, and the manual does not know all of it.

    Key 1 and 2 move the cursor; key 3 toggles a latch that keys 1 and 2 then
    read -- a coupling no single-rule *ablation* of the manual can express,
    since every ablation only ever removes a rule. That is exactly why probes
    against this world land off the frontier: the truth is not in the frontier,
    so no partition of the frontier contains it.
    """
    cursor, latch, burn = state
    if key == 3:
        return (cursor, 1 - latch, burn)
    if key in (1, 2):
        delta = 1 if key == 1 else -1
        if latch:
            delta *= 3
        return ((cursor + delta) % 7, latch, burn + 1)
    if key == 4:
        return (cursor, latch, (burn + 2) % 5)
    return (cursor, latch, burn)


def true_render(state):
    return [[state[0], state[1], state[2]]]


# ------------------------------------------------------------- the manual
def make_namespace(n_rules):
    """The manual as the arm currently believes it, with `n_rules` schemas.

    Growing `n_rules` is what `theorize` does here: each new rule adds one
    ablation hypothesis, which is what opens a new generation.
    """
    def initial_state():
        return MANUAL_START

    def step(state, action):
        _kind, key = action
        cursor, latch, burn = state
        # The manual's error, held fixed: it never learns the latch coupling.
        if key in (1, 2) and n_rules >= 1:
            return ((cursor + (1 if key == 1 else -1)) % 7, latch, burn + 1)
        if key == 3 and n_rules >= 2:
            return (cursor, 1 - latch, burn)
        if key == 4 and n_rules >= 3:
            return (cursor, latch, (burn + 2) % 5)
        return state

    def render(state):
        return [[state[0], state[1], state[2]]]

    def fired(state, action):
        _kind, key = action
        out = []
        if key in (1, 2) and n_rules >= 1:
            out.append("move__k%d" % key)
        if key == 3 and n_rules >= 2:
            out.append("latch__k3")
        if key == 4 and n_rules >= 3:
            out.append("burn__k4")
        if n_rules >= 4:
            out.append("spare%d__k9" % n_rules)
        return out

    rules = []
    if n_rules >= 1:
        rules += [("move__k1", None, None, None), ("move__k2", None, None, None)]
    if n_rules >= 2:
        rules += [("latch__k3", None, None, None)]
    if n_rules >= 3:
        rules += [("burn__k4", None, None, None)]
    for extra in range(4, n_rules + 1):
        rules += [("spare%d__k9" % extra, None, None, None)]

    return {"initial_state": initial_state, "step": step, "render": render,
            "fired": fired, "RULES": rules}


def _hash(grid):
    from world.frames import grid_hash                # noqa: PLC0415
    return grid_hash(grid) or "none"


# ------------------------------------------------------------------ the leg
def run_leg(enabled, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    probes_path = os.path.join(out_dir, "probes.jsonl")
    if os.path.exists(probes_path):
        os.remove(probes_path)

    econ = ProbeEconomy(config=ProbeEconomyConfig(enabled=enabled))
    log = probe_beat.ProbeLog(probes_path)
    register = Register()

    n_rules = 1
    theorize_rounds = 0
    actions_spent = 0
    world = WORLD_START
    manual_state = MANUAL_START
    explorations = 0
    turns = []

    while actions_spent < BUDGET_ACTIONS:
        namespace = make_namespace(n_rules)
        manual_actions = [("key", a) for a in ACTIONS]
        design = probe_beat.design(namespace, manual_state, manual_actions,
                                   economy=econ)
        best = design.get("best")

        if not best or best.get("entropy_bits", 0) <= 0:
            log.record_unrunnable(reason=design.get("verdict") or "no split",
                                  design_report=design, step_idx=actions_spent)
            chosen = ACTIONS[actions_spent % len(ACTIONS)]
            world = true_step(world, chosen)
            manual_state = namespace["step"](manual_state, ("key", chosen))
            actions_spent += 1
            explorations += 1
            turns.append({"kind": "exploration", "action": chosen,
                          "why": "no_split"})
            continue

        allowed, why = econ.gate(design,
                                 n_frontier=int(design.get("n_hypotheses") or 0))
        econ.note_decision(allowed=allowed, reason=why, step_idx=actions_spent,
                           action=best["action"], bits=best.get("entropy_bits"))
        if not allowed:
            log.record_unrunnable(reason=why, design_report=design,
                                  step_idx=actions_spent)
            # The refusal's whole point: the action is not spent. The loop
            # explores instead, which is cheaper in information but is at least
            # a question that has not already been answered.
            chosen = ACTIONS[actions_spent % len(ACTIONS)]
            world = true_step(world, chosen)
            manual_state = namespace["step"](manual_state, ("key", chosen))
            actions_spent += 1
            explorations += 1
            turns.append({"kind": "exploration", "action": chosen,
                          "why": "gate_refusal",
                          "refused_because": why[:70]})
            # An honest exploration is still a turn in which the manual can be
            # caught out; that is where replay_mismatch comes from below.
            if _hash(true_render(world)) != _hash(namespace["render"](manual_state)):
                register.fire("replay_mismatch",
                              "the manual's replay diverged from the world",
                              step_idx=actions_spent - 1)
                theorize_rounds += 1
                if theorize_rounds % RULES_GROW_EVERY == 0:
                    n_rules += 1
                manual_state = world
            continue

        chosen = int(best["action"][1])
        predictions = {}
        for hypothesis in econ.filter_hypotheses(
                probe_beat.build_hypotheses(namespace)):
            try:
                predictions[hypothesis.id] = hypothesis.predict(
                    manual_state, ("key", chosen))
            except Exception:                          # noqa: BLE001
                predictions[hypothesis.id] = "error"

        probe_id = log.record_design(action=chosen, design_report=design,
                                     predictions=predictions,
                                     step_idx=actions_spent,
                                     rationale="mock campaign")
        econ.record_fired(design)
        world = true_step(world, chosen)
        actions_spent += 1
        observed = _hash(true_render(world))
        result = log.record_result(probe_id, observed=observed, status=200,
                                   n_frames=1)
        learnt = econ.observe(result)
        manual_state = namespace["step"](manual_state, ("key", chosen))
        turns.append({"kind": "probe", "action": chosen,
                      "manual_survived": result["manual_survived"],
                      "off_frontier": learnt["off_frontier"]})

        if not result["manual_survived"]:
            register.fire("probe_refutation", result["verdict"],
                          step_idx=actions_spent - 1,
                          payload={"probe_id": probe_id})
            theorize_rounds += 1
            if theorize_rounds % RULES_GROW_EVERY == 0:
                n_rules += 1
            manual_state = world      # theorize re-anchors on what was seen

    counts = register.counts() if hasattr(register, "counts") else {}
    if not counts:
        counts = {k: 0 for k in KINDS}
        for item in register.items:
            counts[item.kind] += 1

    return {
        "probe_economy_enabled": enabled,
        "actions_spent": actions_spent,
        "theorize_rounds": theorize_rounds,
        "probes_fired": sum(1 for t in turns if t["kind"] == "probe"),
        "probes_refused": sum(1 for d in econ.decisions if not d.get("allowed")),
        "explorations": explorations,
        "explorations_after_gate_refusal": sum(
            1 for t in turns if t.get("why") == "gate_refusal"),
        "explorations_after_no_split": sum(
            1 for t in turns if t.get("why") == "no_split"),
        "off_frontier_probes": sum(1 for t in turns
                                   if t["kind"] == "probe" and t["off_frontier"]),
        "surprises_by_kind": {k: counts.get(k, 0) for k in KINDS},
        "surprises_total": sum(counts.get(k, 0) for k in KINDS),
        "final_rule_count": n_rules,
        "economy": econ.as_json(),
    }


def main():
    off = run_leg(False, os.path.join(HERE, "leg_off"))
    on = run_leg(True, os.path.join(HERE, "leg_on"))
    for name, blob in (("campaign_off.json", off), ("campaign_on.json", on)):
        with open(os.path.join(HERE, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            json.dump(blob, fh, indent=2, sort_keys=True)
            fh.write("\n")

    comparison = {
        "seed": SEED,
        "budget_actions": BUDGET_ACTIONS,
        "note": ("Same world, same seed, same budget. The only difference is "
                 "ProbeEconomyConfig.enabled."),
        "off": off,
        "on": on,
        "deltas": {
            "probes_fired": on["probes_fired"] - off["probes_fired"],
            "probes_refused": on["probes_refused"] - off["probes_refused"],
            "off_frontier_probes": (on["off_frontier_probes"]
                                    - off["off_frontier_probes"]),
            "theorize_rounds": on["theorize_rounds"] - off["theorize_rounds"],
            "surprises_total": on["surprises_total"] - off["surprises_total"],
        },
    }
    with open(os.path.join(HERE, "COMPARISON.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(comparison, fh, indent=2, sort_keys=True)
        fh.write("\n")

    width = max(len(k) for k in KINDS) + 2
    print("%-28s %10s %10s" % ("", "OFF", "ON"))
    for field in ("actions_spent", "theorize_rounds", "probes_fired",
                  "probes_refused", "explorations",
                  "explorations_after_gate_refusal",
                  "explorations_after_no_split", "off_frontier_probes",
                  "surprises_total", "final_rule_count"):
        print("%-28s %10s %10s" % (field, off[field], on[field]))
    print()
    print("the seven surprise counts")
    for kind in KINDS:
        print("  %-*s %10d %10d" % (width, kind,
                                    off["surprises_by_kind"][kind],
                                    on["surprises_by_kind"][kind]))


if __name__ == "__main__":
    main()
