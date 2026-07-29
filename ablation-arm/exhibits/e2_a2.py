"""E2 — a false impossibility, believed; and the charity control beside it.

The exhibit the A4 ticket is about (`DESIGN.md` §E2).  The holed manual is
missing the teleport rule.  On its own evidence — `history_trace.jsonl`, the
record that stops at the portal transition — it replays **184/184 green**, so
nothing the cheap layer can see is wrong with it.  The planner returns UNSAT.
The world is solvable in 18 moves.

    ⇒ this arm settles the UNSAT bare, the bus stays empty, the loop does not
      turn, and "this level is unsolvable" is archived.

`Theoria.md:259`'s class (iii) failure in its worst form: a framework that says
"unsolvable" where it should have shut up.

## The charity control, and why it is in this module

A reviewer's first punch at E2 is: *你没给它反例,当然它修不好* — you never
handed it a counterexample, so of course it did not repair.  The mother-tree
recon answered that before the design was written, and the answer went **against**
the prior argument: `a2pipeline/locate.py` survives the ablation byte for byte,
because it needs only a compiled manual and one real solution path.  It reads no
`.lean`.

So this module runs it.  Handed the world's solved episode for free, the ablated
arm's holed manual is localised correctly:

    culprits = ['mispredicted_step'],  exactly 1 step disagrees

**The ablated arm can localise.**  That is recorded here, in the exhibit it
threatens, rather than in a footnote somewhere else — because it sharpens E2
instead of weakening it. The ablation's effect is not *it cannot repair*. It is
that **nothing ever schedules the experiment that would produce the
counterexample**: the certificate obligation is cut, so there is no theorem, no
`depends:` clause, and no directed probe. The repair machinery is intact and
idle, and it is idle for a reason derived from the incision.

## The sweep, and why it stays off the bus

`raw_trace.jsonl` — the fuller record — catches the hole immediately: 44
anomalies, first at t=184, cell (6,4).  This arm never had that record, and a
surprise it could not have had is not a surprise.  Reported here as the size of
the gap between the two readings, never put on the bus, because putting it there
would turn the loop on the referee's knowledge and destroy the exhibit.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any, Dict, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import _bootstrap                                                  # noqa: F401,E402

from ablcore import compile_abl, pin                               # noqa: E402

EXHIBIT = "E2"
WORLD = "a2-holed"
SOLVED_EPISODE = "cold-start-a2/artifacts/solved_episode.jsonl"
#: The world really is solvable, and this is the length upstream records.
WITNESS_LENGTH = 18


def _load_run() -> Dict[str, Any]:
    path = os.path.join(HERE, "artifacts", WORLD, "run_report.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "%s is missing; run `python ablation-arm/run_arm.py` first." % path)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def charity_control() -> Dict[str, Any]:
    """Hand the holed manual the world's solution path and ask locate to work.

    `locate()` reads a compiled manual and an episode and writes nothing; the
    upstream tree is hashed either side of the call rather than trusted to stay
    put, because "it only reads" is the kind of claim that is cheap to check.
    """
    from a2pipeline.locate import locate                           # noqa: E402

    before = pin.hash_tree()
    out = tempfile.mkdtemp(prefix="e2-charity-")
    compile_abl.compile_ablated(
        os.path.join(HERE, "theory", "a2_holed.dsl"),
        os.path.join(REPO, "cold-start-a2/artifacts/history_trace.jsonl"),
        "e2-charity", out, addressable=True)
    report = locate(os.path.join(out, "theory.py"),
                    os.path.join(REPO, SOLVED_EPISODE))
    moved = pin.changed(before, pin.hash_tree())
    return {
        "given": "the world's solved episode, free: %s" % SOLVED_EPISODE,
        "culprits": report["culprits"],
        "checks": report["checks"],
        "n_step_diffs": report["n_step_diffs"],
        "path_length": report["path_length"],
        "localised": bool(report["culprits"]),
        "upstream_unchanged": not moved,
        "upstream_files_changed": moved,
        "reading": (
            "handed the counterexample, the ablated arm localises correctly. "
            "So the ablation did not remove the ability to repair -- it removed "
            "the thing that would have *produced* the counterexample. The "
            "repair machinery is intact and idle, and it is idle because the "
            "certificate obligation that schedules the probe was cut."),
    }


def run(with_charity: bool = True) -> Dict[str, Any]:
    ours = _load_run()
    plan = ours["beats"]["plan"]
    certify = ours["beats"]["certify"]
    gate = ours["beats"]["loop_gate"]
    sweep = certify.get("sweep")

    believed = (ours["verdict"] == "unsolvable" and plan.get("settled") is True)
    silent = (gate["bus"]["count"] == 0 and gate["turns_the_loop"] is False)
    green_on_own_evidence = certify["report"].get("green") is True

    report: Dict[str, Any] = {
        "exhibit": EXHIBIT,
        "world": WORLD,
        "class": "(iii) the specificity failure -- `unsolvable` on a solvable level",
        "manual": "a2_holed.dsl -- the teleport rule is missing",
        "evidence": ours["trace"],
        "on_its_own_evidence": {
            "cheap_layer_green": green_on_own_evidence,
            "frames": certify["report"].get("frames"),
            "pixels_checked": certify["report"].get("pixels_checked"),
            "anomaly_kinds": certify["report"].get("anomaly_kinds"),
        },
        "verdict": {
            "ablated_arm": ours["verdict"],
            "settled": plan.get("settled"),
            "settled_by": plan.get("settled_by"),
            "certificate_owed": plan.get("certificate_owed"),
            "directed_probes_scheduled": plan.get("directed_probes_scheduled"),
        },
        "the_world": {
            "really_solvable": True,
            "witness_length": WITNESS_LENGTH,
            "so_the_verdict_is": "FALSE",
        },
        "the_loop": {
            "surprises": gate["bus"]["count"],
            "turns": gate["turns_the_loop"],
            "why": ours["beats"]["theorize"].get("why_not_owed"),
        },
        "the_sweep": None if not sweep else {
            "trace": sweep["trace"],
            "green": sweep["report"].get("green"),
            "anomalies": len(sweep["report"].get("anomalies", [])),
            "reaches_the_bus": sweep["reaches_the_bus"],
            "why_not": sweep["why_not"],
        },
    }
    if with_charity:
        report["charity_control"] = charity_control()

    report["holds"] = bool(believed and silent and green_on_own_evidence)
    report["testimony"] = (
        "照信不误. The manual is green on every frame of its own evidence, the "
        "planner says UNSAT, this arm settles it bare, and a solvable level is "
        "archived as impossible. Nothing is broken and nothing complains -- "
        "which is the finding. The repair machinery still works when it is "
        "handed a counterexample (see `charity_control`); what was cut is the "
        "obligation that would have gone and got one.")
    return report


def main() -> int:
    report = run()
    print("%s -- %s" % (EXHIBIT, report["class"]))
    own = report["on_its_own_evidence"]
    print("  on its own evidence : green=%s over %s frames, %s pixels"
          % (own["cheap_layer_green"], own["frames"], own["pixels_checked"]))
    print("  verdict             : %s (settled_by %s, certificate_owed %s)"
          % (report["verdict"]["ablated_arm"], report["verdict"]["settled_by"],
             report["verdict"]["certificate_owed"]))
    print("  the world           : solvable in %d -- so the verdict is %s"
          % (report["the_world"]["witness_length"],
             report["the_world"]["so_the_verdict_is"]))
    print("  the loop            : %d surprise(s), turns=%s"
          % (report["the_loop"]["surprises"], report["the_loop"]["turns"]))
    if report["the_sweep"]:
        print("  the sweep (off bus) : green=%s, %d anomalies"
              % (report["the_sweep"]["green"], report["the_sweep"]["anomalies"]))
    charity = report.get("charity_control")
    if charity:
        print("  charity control     : given the solution path, culprits=%s "
              "(%d step diff), upstream_unchanged=%s"
              % (charity["culprits"], charity["n_step_diffs"],
                 charity["upstream_unchanged"]))
    print("  holds               : %s" % report["holds"])
    return 0 if report["holds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
