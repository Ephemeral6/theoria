"""M6 scoring: the induced manual against the referee's copy of the truth.

**This is the only file allowed to read `world/GROUND_TRUTH.md` /
`artifacts/ground_truth.json`, and it runs after M4 is green.** Nothing here
feeds back into `theory.dsl`; its output goes to `A0_REPORT.md`.

Two measurements, because they answer different questions:

* **behavioural** — exhaustive comparison of the manual's `step` against the
  world's `step`, over *every* (reachable state × action) pair. This is the
  held-out test the trajectory could not be: it includes the state-action pairs
  the explorer could never cover (D-A0-003), which is exactly where a missing
  rule hides.
* **structural** — clause by clause, does the manual say what the world does?
  Scored by hand-written correspondence, since "the same rule" is not a
  machine-checkable relation.
"""

import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from certify.replay import ACTION_NAMES, load_theory  # noqa: E402
from world import a0_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# theory.dsl clause  ->  ground-truth rule it corresponds to, or None if the
# manual has no clause for it.  Filled in by reading both, by hand.
STRUCTURAL = [
    ("push_up",          "push",      "exact"),
    ("push_down",        "push",      "exact"),
    ("push_left",        "push",      "exact"),
    ("push_right",       "push",      "exact"),
    ("teleport_down",    "teleport",  "exact"),
    ("press_left",       "press",     "partial: only the leftward push"),
    ("door_opens_left",  "door_open", "partial: only the leftward push"),
    (None,               "blocked",   "entailed by the frame axiom, not a clause"),
    ("<missing>",        "press (up/down/right)",
     "MISSING — rejected at THEORIZE_LOG R-05 for want of evidence"),
]


def behavioural(theory_py: str, spec) -> Dict[str, object]:
    theory = load_theory(theory_py)
    world = a0_world.A0World(spec)

    def to_manual(state):
        manual = theory.initial_state()
        manual.Cart_pos = state.cart
        if hasattr(manual, "Button_colour"):
            manual.Button_colour = 8 if state.pressed else 7
        if hasattr(manual, "Door_present"):
            manual.Door_present = not state.pressed
        return manual

    reachable = world.reachable()
    agree = 0
    disagree: List[Dict[str, object]] = []
    for state in reachable:
        for action in a0_world.ACTIONS:
            world_next = world.step(state, action)
            manual_next = theory.step(to_manual(state), ACTION_NAMES[action])
            if world.render(world_next) == theory.render(manual_next):
                agree += 1
            else:
                disagree.append({
                    "cart": list(state.cart),
                    "pressed": state.pressed,
                    "action": action,
                    "world_cart": list(world_next.cart),
                    "world_pressed": world_next.pressed,
                    "manual_cart": list(manual_next.Cart_pos),
                })
    total = len(reachable) * len(a0_world.ACTIONS)
    return {
        "reachable_states": len(reachable),
        "pairs": total,
        "agree": agree,
        "disagree": len(disagree),
        "accuracy": round(agree / total, 6),
        "examples": disagree[:12],
    }


def held_out(theory_py: str, spec, trace_path: str) -> Dict[str, object]:
    """The same comparison, restricted to pairs the trajectory never contained.

    Replay grades the manual on what it has already seen. This grades it on what
    it has not — which is where a rule that is *missing* rather than *wrong* can
    finally show up (Theoria 1.3).
    """
    from world.explorer import coverage_report, explore

    states, actions = explore(spec)
    seen = {(states[i].key(), actions[i])
            for i in range(len(actions)) if actions[i] is not None}

    theory = load_theory(theory_py)
    world = a0_world.A0World(spec)
    unseen, agree, disagree = 0, 0, []
    for state in world.reachable():
        for action in a0_world.ACTIONS:
            if (state.key(), action) in seen:
                continue
            unseen += 1
            manual = theory.initial_state()
            manual.Cart_pos = state.cart
            if hasattr(manual, "Button_colour"):
                manual.Button_colour = 8 if state.pressed else 7
            if hasattr(manual, "Door_present"):
                manual.Door_present = not state.pressed
            world_next = world.step(state, action)
            manual_next = theory.step(manual, ACTION_NAMES[action])
            if world.render(world_next) == theory.render(manual_next):
                agree += 1
            else:
                disagree.append({
                    "cart": list(state.cart), "pressed": state.pressed,
                    "action": action,
                    "world_cart": list(world_next.cart),
                    "world_pressed": world_next.pressed,
                    "manual_cart": list(manual_next.Cart_pos),
                })
    _ = coverage_report
    return {
        "held_out_pairs": unseen,
        "agree": agree,
        "disagree": len(disagree),
        "accuracy": round(agree / unseen, 6) if unseen else None,
        "examples": disagree[:12],
    }


def main() -> int:
    generated = os.path.join(ROOT, "theory", "generated", "theory.py")
    generated_nb = os.path.join(ROOT, "theory", "generated_no_button", "theory.py")

    report = {
        "seal": "ground truth first read at M6, after M4 and M5 were green",
        "base": {
            "behavioural": behavioural(generated, a0_world.BASE),
            "held_out": held_out(generated, a0_world.BASE,
                                 os.path.join(ROOT, "artifacts", "raw_trace.jsonl")),
        },
        "variant": {
            "behavioural": behavioural(generated_nb, a0_world.NO_BUTTON),
        },
        "structural": [
            {"manual_clause": a, "ground_rule": b, "verdict": c}
            for a, b, c in STRUCTURAL
        ],
    }
    out = os.path.join(ROOT, "artifacts", "score_vs_truth.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    for name in ("base", "variant"):
        for kind, data in report[name].items():
            print("%-8s %-11s %s" % (name, kind, json.dumps(
                {k: v for k, v in data.items() if k != "examples"}, sort_keys=True)))
    for example in report["base"]["held_out"]["examples"]:
        print("   miss:", json.dumps(example, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
