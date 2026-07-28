"""M6 — score a manual against the referee's transition function.

The transfer arm's replay is green over the 11 frames it actually executed.
That is the right check to *run* — it is what an agent can verify in the field
— but it is a weak measurement, because 10 transitions out of a level's few
hundred could be green by luck.

This module asks the stronger question, and it can only be asked from the
referee's side: **for every reachable (state, action) pair of the level, does
the manual predict what the world does?**  For the transfer arm the level in
question is one the manual was never induced from and never explored, so the
answer is the real accuracy of the carried domain.

A0 scored 233/236 this way and found three errors that full-history replay
could not see.  The same instrument is pointed at A3's carried manual here, for
the same reason: replay against a trajectory answers "is the manual consistent
with what I saw", and only this answers "is the manual right".

**This lives in `a3world/` and not in `a3pipeline/`, and the placement is the
discipline.**  Scoring requires the transition function, so it is the referee's
job; no arm imports it, no arm's result depends on it, and it runs after the
arms are finished.  `tests/test_sealing.py` enforces that `a3pipeline` never
imports a world module, and this file is exactly what that rule exists to keep
out of the arms' reach.

The manual is loaded as its **generated Python form** — the same artefact the
cheap layer replays — so what is scored is the compiled manual and not a second
reading of the DSL.
"""

import importlib.util
import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3world.a3_world import ACTIONS, LEVELS, A3World  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")

DIRECTION = {"UP": "up", "DOWN": "down", "LEFT": "left", "RIGHT": "right"}


def _load(theory_py: str):
    spec = importlib.util.spec_from_file_location("a3_scored_theory", theory_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score(level: str, theory_py: str) -> Dict[str, object]:
    """Every reachable (state, action) pair, manual against world.

    The manual's state is reconstructed from the world's by placing the Cart,
    the Switch's colour and the Door's presence — the three observables the
    word table declares — and the comparison is on the **rendered frame**, so a
    manual that gets the right cell for the wrong reason still has to draw the
    right picture.
    """
    world = A3World(LEVELS[level])
    module = _load(theory_py)

    # The reused stack keys on object *names* in four places (D-A3-008), so a
    # manual whose mover is not called `Cart` cannot be scored, replayed or
    # Lean-checked.  Fail with the reason rather than with an AttributeError
    # forty lines down.
    probe = module.initial_state()
    for field in ("Cart_pos", "Switch_colour", "Door_present"):
        if not hasattr(probe, field):
            raise AttributeError(
                "%s has no %s: this manual names its objects differently, and "
                "certify.replay, gen_python_a0, the Lean invariant helpers and "
                "the goal binder all assume Cart/Door. See DECISIONS D-A3-008."
                % (os.path.basename(os.path.dirname(theory_py)), field))

    mismatches: List[Dict[str, object]] = []
    checked = 0

    for state in world.reachable():
        for action in ACTIONS:
            checked += 1
            truth = world.step(state, action)

            predicted = module.initial_state()
            predicted.Cart_pos = state.cart
            predicted.Switch_colour = 8 if state.pressed else 7
            predicted.Door_present = not state.pressed
            try:
                after = module.step(predicted, ("push", "Cart",
                                                DIRECTION[action]))
            except Exception as exc:                      # noqa: BLE001
                mismatches.append({
                    "state": list(state.key()), "action": action,
                    "error": "%s: %s" % (type(exc).__name__, exc)})
                continue

            want = world.render(truth)
            got = module.render(after)
            if want != got:
                if len(mismatches) < 40:
                    mismatches.append({
                        "state": list(state.key()),
                        "action": action,
                        "world_cart": list(truth.cart),
                        "manual_cart": list(after.Cart_pos),
                        "world_pressed": truth.pressed,
                        "manual_switch": after.Switch_colour,
                    })
                else:
                    mismatches.append({"truncated": True})

    correct = checked - len([m for m in mismatches if "truncated" not in m])
    return {
        "level": level,
        "theory": os.path.relpath(theory_py, ROOT).replace("\\", "/"),
        "pairs_checked": checked,
        "pairs_correct": correct,
        "accuracy": round(correct / checked, 6) if checked else 0.0,
        "mismatches": mismatches[:40],
        "perfect": not mismatches,
    }


TARGETS = (
    ("a3-l1", "generated_l1",
     "the manual on the level it was induced from"),
    ("a3-l2", "generated_l2",
     "THE CARRIED MANUAL on a level it never explored"),
    ("a3-l2", "generated_l2_scratch",
     "the control arm's manual, induced from level 2's own sweep"),
)


def run_all() -> Dict[str, object]:
    results = []
    for level, out_name, note in TARGETS:
        theory_py = os.path.join(THEORY, out_name, "theory.py")
        if not os.path.exists(theory_py):
            continue
        try:
            row = score(level, theory_py)
        except AttributeError as exc:
            # D-A3-008: a manual whose objects are not called Cart/Door cannot
            # be scored.  Recorded as a result, because "this manual could not
            # be measured, and here is why" is a finding and not a gap.
            row = {"level": level, "unscoreable": str(exc),
                   "theory": os.path.relpath(theory_py, ROOT).replace("\\", "/")}
        row["note"] = note
        results.append(row)

    payload = {
        "results": results,
        "reading": (
            "Replay against a trajectory answers 'is the manual consistent "
            "with what I saw'. This answers 'is the manual right'. For the "
            "carried manual the level was never explored, so this is the "
            "accuracy of transfer rather than of induction."
        ),
    }
    out = os.path.join(ARTIFACTS, "score_vs_truth.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def main() -> int:
    payload = run_all()
    for row in payload["results"]:
        if "unscoreable" in row:
            print("%-22s %-8s UNSCOREABLE — %s"
                  % (row["theory"].split("/")[1], row["level"],
                     row["unscoreable"][:90]))
            continue
        print("%-22s %-8s %4d/%-4d = %.4f  %s"
              % (row["theory"].split("/")[1], row["level"],
                 row["pairs_correct"], row["pairs_checked"],
                 row["accuracy"], row["note"]))
        for bad in row["mismatches"][:3]:
            print("      mismatch %s" % bad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
