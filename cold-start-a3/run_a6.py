"""A6 acceptance — every arm and every control, in order, from one command.

`run_all.py` is A3's and is left alone: it is P-17's deliverable, its stage order
is load-bearing, and its numbers are quoted in `A3_REPORT.md`.  This is A6's, and
what it runs is the acceptance the board item names:

> 验收：拿 worldgen 产的两个同机制异布局世界端到端验证，且 A3 的两个负对照在新
> 形态下同样被抓住。

Five arms and four controls.  The arms are the claim; the controls are the
reasons to believe it, and two of them exist because the claim is weaker than it
looks:

| | what it establishes |
|---|---|
| `source_open` | the push manual wins the world it was theorized from |
| `transfer_corridor` | it wins a world it has never seen, at zero relearning |
| `a3_l2_positive` | the new protocol does not break A3's own result |
| `a3_l2_oneway` | A3's negative control 1 is still caught, through this protocol |
| `a3_l2_rewired` | A3's negative control 2 is still caught |
| `wrong_world_switch_latch` | a wrong-mechanism world stops the run before an action is spent |
| `wrong_world_cycler_gate` | **a green carry is not evidence the manual is right** |
| `tampered_books` | the pack's own hashes have a reader |
| `drifted_fingerprint` | the dependency fingerprint has a reader |

The two `wrong_world_*` controls are the honest half.  A protocol that only ever
reported `win` on worlds it was aimed at would be reporting the aim.

## The control that matters most

`wrong_world_cycler_gate` carries the **push** pack onto `t1-cycler-gate`, whose
mechanism the manual does not model at all — colour 2 there is a cycler that
recolours when bumped, not a block that slides.  The run comes back
`outcome=win`, `replay green`, **zero unexplained pixels**.  It is not a fluke
and it is not a bug: the planner found a route that never touches the cycler, so
every transition the manual was asked about was one it happens to get right.
Sending the same pack at the same world along `RIGHT RIGHT RIGHT` produces eight
anomalies at t=2 — the manual predicts the shove it knows, the world recolours
instead.

So a green end-to-end carry certifies **the path, not the world**, and this
runner asserts that in both directions rather than leaving it as a caveat in
prose.  `a6carry/score.py` is the answer to it: exhaustive scoring over every
reachable transition, which is what "the manual is right about this world" would
actually require.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _bootstrap  # noqa: F401,E402

from a3pipeline import certify_a3, compile_a3  # noqa: E402

from a6carry import pack as packlib  # noqa: E402
from a6carry import protocol  # noqa: E402
from a6carry.executor_api import write_execution  # noqa: E402
from a6carry.executors import A3Executor, WorldgenExecutor  # noqa: E402
from a6carry.pack import Pack  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join("runs", "20260728T1800Z-A6-transfer-protocol")
PACKS = os.path.join(RUN, "packs")
GENERATED = os.path.join(RUN, "generated")
ARTEFACTS = os.path.join(RUN, "artifacts")

#: The two worlds the item names, and the direction of carry.  `worldgen`'s own
#: `INDEX.json` declares exactly one "same mechanism, different layout" pair and
#: its `variant_delta` says so in those words.  Open room -> corridor is the
#: honest direction: the corridor is the world `worldgen/README.md` names as the
#: A0 failure mode, where `push` has a single witness and no way to obtain a
#: second, so books written *there* would be books written on one witness.
SOURCE_WORLD = "t1-push-open"
TRANSFER_WORLD = "t1-push-corridor"

#: `t1-push-open` renders the mover at 6 and the block at 2 (`spec.json`'s
#: legend, `colors: {"block": 2}`).  Declared rather than derived because A0's
#: word table gives an object a `color: Int` field and never a value; `pack.build`
#: checks the declaration against every `recolored` literal in the manual.
PUSH_COLOURS = {"Cart": [6], "Block": [2]}
A3_COLOURS = {"Door": [5], "Cart": [6], "Switch": [7, 8]}


def rule(title):
    print("\n" + "-" * 72)
    print(title)
    print("-" * 72)


def build_packs():
    """Both packs, rebuilt from the books every run.

    Rebuilding rather than reusing is deliberate: a pack that survives across
    runs is a pack whose `fingerprint` was taken against a tree nobody checked
    this time, and the whole argument for the fingerprint is that a stale one is
    worse than none.
    """
    push = packlib.build(
        pack_dir=os.path.join(PACKS, "push-v1"),
        domain_path=os.path.join("theory", "push", "domain.dsl"),
        playbook_path=os.path.join("theory", "push", "playbook.dsl"),
        pack_id="push-v1",
        origin={"world": SOURCE_WORLD, "evidence": "raw_trace.jsonl",
                "frames": 41, "actions": 40,
                "note": "adjudicated from one world's trace; eight of twelve "
                        "clauses rest on symmetry and say so"},
        object_colours=PUSH_COLOURS,
        colour_roles={6: "agent", 2: "block"})
    a3 = packlib.build(
        pack_dir=os.path.join(PACKS, "a3-v1"),
        domain_path=os.path.join("theory", "domain.dsl"),
        playbook_path=os.path.join("theory", "playbook.dsl"),
        pack_id="a3-v1",
        origin={"arm": "A3 level 1", "note": "A3's own books, so the negative "
                                             "controls run the same path"},
        object_colours=A3_COLOURS,
        colour_roles={5: "door", 6: "cart", 7: "switch-up", 8: "switch-down"})
    return push, a3


def row(report):
    """One arm, flattened to the numbers the claim is about."""
    counts = report.get("bill", {}).get("counts", {})
    first = report.get("first_mismatch")
    return {
        "arm": report.get("arm"),
        "level": report.get("level"),
        "pack": report.get("pack"),
        "outcome": report.get("outcome"),
        "static_certify_green": (report.get("certify_static") or {}).get("green"),
        "plan_status": (report.get("plan") or {}).get("status"),
        "replay_certify_green": (report.get("certify_replay") or {}).get("green"),
        "theorize_triggered": report.get("theorize_triggered"),
        "world_frames": counts.get("world_frames"),
        "world_actions": counts.get("world_actions"),
        "theorize_rounds": counts.get("theorize_rounds"),
        "dsl_clauses_written": counts.get("dsl_clauses_written"),
        "candidates_adjudicated": counts.get("candidates_adjudicated"),
        "engine_stages": counts.get("engine_stages"),
        "cost_to_first_plan": report.get("bill", {}).get("cost_to_first_plan"),
        "first_mismatch_kind": first.get("kind") if isinstance(first, dict) else None,
        "lean": (report.get("certify_lean") or {}).get("green"),
        "lean_withheld_reason": (report.get("certify_lean") or {}).get("reason"),
    }


def carry(pack, executor, arm, **kwargs):
    report = protocol.carry(pack, executor,
                            out_dir=os.path.join(GENERATED, arm),
                            artefacts=ARTEFACTS, arm=arm, **kwargs)
    print("   " + protocol.brief(report))
    return report


# ------------------------------------------------------------------- controls

def control_tampered_books(pack_dir):
    """Edit a carried book by one byte; the pack must notice before step 1.

    `PACK.json` records a sha256 per book and `protocol.carry` compares them at
    step 0.  Without this control that comparison is another fingerprint with no
    reader — the exact defect `monitor/inbox/20260728T082700Z-W-1521` reports
    against `upstream_pin()`, and the reason step 0 exists at all.
    """
    path = os.path.join(pack_dir, "domain.dsl")
    with open(path, "r", encoding="utf-8") as handle:
        original = handle.read()
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original + "\n# one byte a receiver did not write\n")
        report = carry(Pack(pack_dir), WorldgenExecutor(TRANSFER_WORLD),
                       "tampered_books")
    finally:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original)
    return report


def control_drifted_fingerprint(pack_dir):
    """Claim the pack was validated against a toolchain that is not this one.

    Rewrites one recorded hash in `PACK.json` rather than editing an upstream
    file — the upstream files belong to other tracks and this control may not
    touch them, and the check under test is the comparison, not the hashing.
    """
    manifest_path = os.path.join(pack_dir, "PACK.json")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        original = handle.read()
    manifest = json.loads(original)
    victim = sorted(manifest["fingerprint"]["files"])[0]
    manifest["fingerprint"]["files"][victim] = "0" * 64
    try:
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, indent=2, sort_keys=True,
                                    ensure_ascii=False) + "\n")
        try:
            report = carry(Pack(pack_dir), WorldgenExecutor(TRANSFER_WORLD),
                           "drifted_fingerprint")
            refused = False
        except protocol.DependencyDrift as drift:
            refused = True
            report = {"arm": "drifted_fingerprint", "level": TRANSFER_WORLD,
                      "outcome": "dependency_drift", "drifted": drift.verdict["drifted"]}
            print("   %-26s %-18s refused before frame 1; drifted: %s"
                  % (TRANSFER_WORLD, "dependency_drift",
                     ", ".join(drift.verdict["drifted"])))
    finally:
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(original)
    return report, refused, victim


def control_green_is_about_the_path(pack, world, off_route):
    """The same pack, the same world, two routes — one green, one red.

    This is the control the whole report turns on.  `carry` reports `win` and a
    green replay on `t1-cycler-gate`, a world whose mechanism the push manual
    does not model, because the planner routed around the part it is wrong
    about.  Driving the same manual down `off_route` finds the disagreement
    immediately.  Both halves are recorded; reporting only the first would be
    reporting the aim.
    """
    executor = WorldgenExecutor(world)
    record = executor.execute(off_route)
    trace = os.path.join(ARTEFACTS, "offroute_%s.jsonl" % world)
    write_execution(trace, record)
    theory_py = os.path.join(GENERATED, "wrong_world_%s" % world.replace("-", "_"),
                             "theory.py")
    verdict = certify_a3.cheap(theory_py, trace)
    anomalies = verdict.get("anomalies") or []
    print("   off-route %-14s green=%-5s anomalies=%d %s"
          % (" ".join(off_route), verdict["green"], len(anomalies),
             sorted({a["kind"] for a in anomalies})))
    return {
        "world": world,
        "off_route": list(off_route),
        "green": verdict["green"],
        "anomaly_count": len(anomalies),
        "anomaly_kinds": sorted({a["kind"] for a in anomalies}),
        "first_anomaly": anomalies[0] if anomalies else None,
        "pixels_unexplained": verdict["pixels_unexplained"],
    }


# ----------------------------------------------------------------------- main

def main():
    os.chdir(ROOT)
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    os.makedirs(ARTEFACTS, exist_ok=True)

    rule("0. the two packs — books in, PACK.json out")
    push_manifest, a3_manifest = build_packs()
    for name, manifest in (("push-v1", push_manifest), ("a3-v1", a3_manifest)):
        book = manifest["books"]
        print("   %-8s rules=%-3s laws=%-3s theorems=%-2s playbook=%s "
              "carried=%s left_behind=%s"
              % (name, book["domain"]["rules"], book["domain"]["laws"],
                 len(manifest["theorems"]), book["playbook"]["parsed"],
                 book["playbook"]["entries_carried"],
                 book["playbook"]["entries_left_behind"]))
    push = Pack(os.path.join(PACKS, "push-v1"))
    a3 = Pack(os.path.join(PACKS, "a3-v1"))

    rows = []

    rule("1. the source world — the manual wins what it was theorized from")
    rows.append(row(carry(push, WorldgenExecutor(SOURCE_WORLD), "source_open")))

    rule("2. the transfer — a world it has never seen, nothing relearned")
    rows.append(row(carry(push, WorldgenExecutor(TRANSFER_WORLD),
                          "transfer_corridor")))

    rule("3. A3's positive control — the new protocol does not break A3")
    rows.append(row(carry(a3, A3Executor("a3-l2"), "a3_l2_positive",
                          invariant_builder=compile_a3.switch_latch_invariant)))

    rule("4. A3's two negative controls, through the new protocol")
    for level, arm in (("a3-l2-oneway", "a3_l2_oneway"),
                       ("a3-l2-rewired", "a3_l2_rewired")):
        rows.append(row(carry(a3, A3Executor(level), arm,
                              invariant_builder=compile_a3.switch_latch_invariant)))

    rule("5. wrong-mechanism worlds — what the protocol does when aimed badly")
    for world in ("t1-switch-latch", "t1-cycler-gate"):
        rows.append(row(carry(push, WorldgenExecutor(world),
                              "wrong_world_%s" % world.replace("-", "_"))))

    rule("6. green is about the path, not the world")
    off_route = control_green_is_about_the_path(
        push, "t1-cycler-gate", ["RIGHT", "RIGHT", "RIGHT"])

    rule("7. the pack's own checks have readers")
    tampered = row(control_tampered_books(os.path.join(PACKS, "push-v1")))
    rows.append(tampered)
    drift_report, drift_refused, drift_victim = control_drifted_fingerprint(
        os.path.join(PACKS, "push-v1"))

    # ------------------------------------------------------------- the verdict
    by_arm = {r["arm"]: r for r in rows}
    carried = [by_arm["source_open"], by_arm["transfer_corridor"]]
    negatives = [by_arm["a3_l2_oneway"], by_arm["a3_l2_rewired"]]

    acceptance = {
        "two_worldgen_worlds_end_to_end": all(
            r["outcome"] == "win" and r["replay_certify_green"] is True
            for r in carried),
        "transfer_relearned_nothing": all(
            by_arm["transfer_corridor"][k] == 0 for k in
            ("theorize_rounds", "dsl_clauses_written",
             "candidates_adjudicated", "engine_stages")),
        "transfer_planned_before_acting":
            by_arm["transfer_corridor"]["cost_to_first_plan"]["world_actions"] == 0,
        "a3_negative_controls_still_caught": all(
            r["outcome"] != "win" and r["theorize_triggered"] is True
            for r in negatives),
        "none_claimed_a_win": all(
            not (r["outcome"] == "win" and r["replay_certify_green"] is True)
            for r in negatives),
        "a3_positive_control_still_wins":
            by_arm["a3_l2_positive"]["outcome"] == "win",
        "tampered_books_refused":
            by_arm["tampered_books"]["outcome"] == "pack_tampered"
            and by_arm["tampered_books"]["world_actions"] == 0,
        "drifted_fingerprint_refused": drift_refused,
        "wrong_mechanism_world_spent_no_actions":
            by_arm["wrong_world_t1_switch_latch"]["world_actions"] == 0,
        # Deliberately named as a limit, not a pass.  It records that the
        # protocol *did* return a green win on a world the manual is wrong
        # about, and that the same manual on the same world goes red off-route.
        "green_carry_can_be_earned_on_a_wrong_world":
            by_arm["wrong_world_t1_cycler_gate"]["outcome"] == "win"
            and by_arm["wrong_world_t1_cycler_gate"]["replay_certify_green"] is True
            and off_route["green"] is False,
    }

    verdict = {
        "protocol": "a6carry/1",
        "item": "A6-transfer-protocol",
        "source_world": SOURCE_WORLD,
        "transfer_world": TRANSFER_WORLD,
        "packs": {
            "push-v1": {"books": push_manifest["books"],
                        "requires": push_manifest["requires"],
                        "theorems": [t.get("name") for t in push_manifest["theorems"]]},
            "a3-v1": {"books": a3_manifest["books"],
                      "requires": a3_manifest["requires"],
                      "theorems": [t.get("name") for t in a3_manifest["theorems"]]},
        },
        "arms": sorted(rows, key=lambda r: r["arm"]),
        "off_route_control": off_route,
        "fingerprint_control": {"refused": drift_refused,
                                "file_drifted": drift_victim},
        "acceptance": acceptance,
        "all_green": all(acceptance.values()),
    }

    out = os.path.join(RUN, "a6_acceptance.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(verdict, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")

    rule("acceptance")
    for key in sorted(acceptance):
        print("   %-46s %s" % (key, acceptance[key]))
    print("\n   wrote %s" % out.replace(os.sep, "/"))
    return 0 if verdict["all_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
