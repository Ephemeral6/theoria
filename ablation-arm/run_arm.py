"""Step 3 — the driver: the beats composed into a loop that turns on its own.

```bash
python ablation-arm/run_arm.py                  # every world
python ablation-arm/run_arm.py --world a2-holed # one
python ablation-arm/run_arm.py --json           # the reports, as data
```

`ablcore/` has been a library with no caller since P-18 wrote it.  This is the
caller.  It is the piece `DESIGN.md` §12 lists only implicitly, which is most of
why the arm had never been run end to end.

## The one rule this file is not allowed to break

`DESIGN.md` §7.2, and it is the most important sentence in the design:

> **不能**把 `refute/locate/probe/repair` 从步骤表里删掉,然后报告"消融臂修不好"。
> 那是**手工拆掉回路再宣布回路不转**。

So this driver does **not** contain a step table with the repair beats missing.
It contains the scheduling rule both arms share — `Theoria.md:233`, 有意外才回
theorize — expressed once, as one line:

    if bus.turns_the_loop(): ...   # i.e. `not bus.empty()`

Whether the loop turns is then a *consequence of what the beats could put on the
bus*, and the incision is what decides that.  On a UNSAT plan the full arm owes a
certificate (constraint 6), generates invariants, proves them, reads the
theorem's `depends:` clauses, probes them (constraint 7), and the probe's
refutation is a surprise.  This arm owes nothing, so there is no theorem, no
`depends:`, no directed probe, and **nothing reaches the bus**.  The loop not
turning is derived here, not arranged.

## Where the trace comes from, and why it is not re-explored

`compile_ablated` needs a trace, and this is the first thing in the build that
upstream does not hand over already finished.  Two options: re-run the explorer,
or read the artefact the full arm read.

**It reads the artefact**, for the same reason steps 1 and 2 select rather than
reimplement.  P-1 and P-2 predict this arm's replay and held-out accuracy are
*byte-equal to the full arm's*.  Two arms that learned from different evidence
cannot settle that, however similar the two traces looked — a re-exploration is a
second difference, and `Theoria.md:280` says a second difference makes the first
unattributable.  The trace's sha256 goes in every report, so A4b can prove both
arms read the same bytes rather than assuming it.

The traces live in another track's `artifacts/`.  They are read and hashed;
`tests/test_readonly.py` is what makes "and never written" checkable.

## What this driver does not do

It does not theorize.  Theorize is the LLM's beat and this arm is offline by
construction (`ledger_abl.py:9`: zero API calls, zero network, zero dollars), so
when the bus does turn the loop the driver records **that a theorize turn is
owed, and what owes it**, and stops there.  Recording the debt is honest; making
up the turn would not be.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import _bootstrap                                                  # noqa: F401,E402

from ablcore import certify_abl, compile_abl, ledger_abl, pin, plan_abl  # noqa: E402
from ablcore.surprise import SurpriseBus                           # noqa: E402
from worlds import a0_abl, a2_abl                                  # noqa: E402

THEORY_DIR = os.path.join(HERE, "theory")
ARTIFACTS = os.path.join(HERE, "artifacts")

#: The beats, in the order the inner loop runs them.  `theorize` is on this list
#: and is reached exactly when the bus says so -- it is not omitted, which is the
#: distinction DESIGN.md §7.2 turns on.
BEATS = ("compile", "certify", "plan", "commit", "loop_gate", "theorize")


class WorldRun:
    """One world, one manual, one trace.  Everything the beats need."""

    def __init__(self, key: str, dsl: str, trace: str,
                 world: Callable[[], Any], *, addressable: bool = True,
                 exhibit: Optional[str] = None, note: str = "",
                 sweep_trace: Optional[str] = None,
                 expect_pixels: Optional[int] = None,
                 expect_frames: Optional[int] = None):
        self.key = key
        self.dsl = dsl
        #: The evidence this manual was theorized from. Not "a trace of this
        #: world" -- *the* record its theorizer had. See `WORLDS`.
        self.trace = trace
        self.world = world
        self.addressable = addressable
        self.exhibit = exhibit
        self.note = note
        #: A fuller record, read only as a referee-side second opinion. It never
        #: touches the bus: the arm did not have it.
        self.sweep_trace = sweep_trace
        #: DESIGN.md §8 P-1's pre-registered numbers, where it states them.
        self.expect_pixels = expect_pixels
        self.expect_frames = expect_frames


#: Every trace here is **the record its manual was theorized from**, taken from
#: the upstream artefact that names it, never guessed and never re-explored.
#:
#: That distinction cost this driver a wrong result on its first run and is
#: therefore written down rather than left to care. `a2-holed` was pointed at
#: `raw_trace.jsonl` because that is the A2 world's trace — and the cheap layer
#: promptly went red, the loop turned, and P-6 looked falsified. It was not:
#: `cold-start-a2/artifacts/exhibit_report.json` records the holed manual's
#: evidence as **`history_trace.jsonl`**, on which the cheap layer is green over
#: 184 frames, and separately records the fuller sweep going red at t=184 with
#: its own reading — *"the hole is invisible to the evidence its theorizer had,
#: which is exactly Theoria §1.3's claim and exactly its limit"*.
#:
#: `trace_summary.json` states the cut rule: `history_trace = raw_trace[0 ..
#: portal_transition]`, omitting **exactly one** state-action pair,
#: `cart=(6,4) pressed=1 act=DOWN` — the same single disagreement
#: `a2_abl.disagreement()` computed in step 1, arrived at from the other side.
#:
#: `expect_pixels` is P-1's pre-registered number where DESIGN.md §8 states it,
#: and it is what makes a repeat of that mistake loud instead of plausible.
WORLDS: Tuple[WorldRun, ...] = (
    WorldRun("a0-base", "a0_base.dsl",
             "cold-start-a0/artifacts/raw_trace.jsonl", a0_abl.base,
             expect_pixels=22356, expect_frames=276,
             note="the solvable A0 world. P-1/P-2 read accuracy off this run "
                  "and P-5 reads its verdict."),
    WorldRun("a0-no-button", "a0_no_button.dsl",
             "cold-start-a0/artifacts/raw_trace_no_button.jsonl",
             a0_abl.no_button, exhibit="E1",
             note="A0 with no Button: genuinely unsolvable, and the manual said "
                  "so truthfully until the cut deleted `unsolvable_no_button`. "
                  "The verdict should be right and the reason should be bare "
                  "search."),
    WorldRun("a2-base", "a2_base.dsl",
             "cold-start-a2/artifacts/raw_trace.jsonl", a2_abl.world,
             expect_pixels=20088, expect_frames=248,
             note="the A2 world with its teleport rule intact."),
    WorldRun("a2-holed", "a2_holed.dsl",
             "cold-start-a2/artifacts/history_trace.jsonl", a2_abl.world,
             sweep_trace="cold-start-a2/artifacts/raw_trace.jsonl",
             expect_pixels=14904, expect_frames=184,
             exhibit="E2",
             note="**the ticket's exhibit**: the manual is missing the teleport "
                  "rule, so it derives `unsolvable` for a world that is "
                  "solvable. Its evidence is `history_trace.jsonl`, the record "
                  "that stops at the portal transition -- on which the cheap "
                  "layer is green, so the hole is invisible to everything this "
                  "arm still has. The world passed to `commit` is the REAL one; "
                  "`a2_abl.manual_world()` is deliberately not used, because "
                  "the point is that the arm never finds out."),
)

WORLD_BY_KEY = {w.key: w for w in WORLDS}


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run_world(spec: WorldRun, out_root: Optional[str] = None) -> Dict[str, Any]:
    """One world, all the beats, one report."""
    out_root = out_root or ARTIFACTS
    out_dir = os.path.join(out_root, spec.key)
    os.makedirs(out_dir, exist_ok=True)

    dsl_path = os.path.join(THEORY_DIR, spec.dsl)
    trace_path = os.path.join(REPO, spec.trace)
    for path, what in ((dsl_path, "manual"), (trace_path, "trace")):
        if not os.path.exists(path):
            raise FileNotFoundError(
                "%s missing for %s: %s. Run build_theory.py first if it is the "
                "manual; a missing trace is a broken checkout."
                % (what, spec.key, path))

    bus = SurpriseBus(ablated=True)
    beats: Dict[str, Any] = {}
    report: Dict[str, Any] = {
        "world": spec.key,
        "exhibit": spec.exhibit,
        "note": spec.note,
        "manual": os.path.relpath(dsl_path, REPO).replace("\\", "/"),
        "manual_sha256": sha256_file(dsl_path),
        "trace": spec.trace,
        "trace_sha256": sha256_file(trace_path),
        "trace_source": ("read, never re-explored: a different trace would be a "
                         "second difference between the arms and P-1/P-2 could "
                         "not be settled (DESIGN.md §5)"),
        "beats": beats,
    }

    # -- 1. compile ----------------------------------------------------------
    beats["compile"] = compile_abl.compile_ablated(
        dsl_path, trace_path, spec.key, out_dir, addressable=spec.addressable)

    # -- 2. certify (cheap layer only; the expensive one is the cut) ----------
    theory_py = os.path.join(out_dir, "theory.py")
    cheap = certify_abl.cheap(theory_py, trace_path)
    certify_abl.report_surprises(bus, cheap, beat="certify")
    beats["certify"] = {
        "layers_run": ["cheap"],
        "layer_omitted": "expensive",
        "omitted_because": ("constraint 6 is the cut; `certify_abl.expensive` "
                            "raises ObligationCut and nothing calls it"),
        "report": cheap,
        "pre_registered": _check_preregistered(spec, cheap),
    }

    # -- 2b. the sweep: a referee-side second opinion that never reaches the bus
    if spec.sweep_trace:
        sweep_path = os.path.join(REPO, spec.sweep_trace)
        sweep = certify_abl.cheap(theory_py, sweep_path)
        beats["certify"]["sweep"] = {
            "trace": spec.sweep_trace,
            "trace_sha256": sha256_file(sweep_path),
            "report": sweep,
            "reaches_the_bus": False,
            "why_not": (
                "this arm never had this record. Its manual was theorized from "
                "`%s`, and a surprise the arm could not have had is not a "
                "surprise -- putting it on the bus would turn the loop on the "
                "referee's knowledge and destroy the exhibit. It is reported "
                "because the size of the gap between the two readings IS the "
                "measurement: green on the evidence, red on the sweep."
                % spec.trace),
        }

    # -- 3 + 4. plan, and commit against the world ---------------------------
    world = spec.world()
    plan_report = plan_abl.run_plan(
        out_dir, spec.key, world=world, bus=bus,
        out_path=os.path.join(out_dir, "plan.json"))
    beats["plan"] = plan_report
    beats["commit"] = {
        "committed": "world_reaches_goal" in plan_report,
        "world_reaches_goal": plan_report.get("world_reaches_goal"),
        "execution_mismatches": plan_report.get("execution_mismatches"),
        "why_not": (None if "world_reaches_goal" in plan_report else
                    "the plan came back UNSAT, so there is nothing to commit"),
    }

    # -- 5. the loop gate: the whole scheduling rule, shared by both arms -----
    turns = bus.turns_the_loop()
    beats["loop_gate"] = {
        "rule": "Theoria.md:233 -- 有意外才回 theorize. One line, both arms: "
                "`if bus.turns_the_loop()`",
        "bus": bus.as_json(),
        "turns_the_loop": turns,
        "derived_not_arranged": (
            "the repair beats are not deleted from a step table; they are "
            "reached iff the bus is non-empty, and what can reach the bus is "
            "what the incision decides (DESIGN.md §7.2, §7.3)"),
    }

    # -- 6. theorize, reached exactly when the bus says so --------------------
    if turns:
        beats["theorize"] = {
            "entered": False,
            "owed": True,
            "owed_by": bus.pending(),
            "why_not_run": ("theorize is the LLM's beat and this arm is offline "
                            "by construction (zero API calls, zero model calls). "
                            "The debt is recorded; inventing the turn would not "
                            "be a measurement."),
        }
    else:
        beats["theorize"] = {
            "entered": False,
            "owed": False,
            "why_not_owed": _why_the_bus_is_empty(plan_report),
        }

    report["surprises"] = bus.as_json()
    report["settled"] = plan_report.get("settled")
    report["verdict"] = plan_report.get("verdict", "solvable"
                                        if plan_report.get("status") == "SAT"
                                        else None)
    report["ledger"] = _write_ledger(spec, world, plan_report, out_dir)
    _write(os.path.join(out_dir, "run_report.json"), report)
    return report


def _check_preregistered(spec: WorldRun, cheap: Dict[str, Any]) -> Dict[str, Any]:
    """P-1's numbers, where DESIGN.md §8 states them, checked at run time.

    §8 does not write P-1 as "the replay accuracy is equal"; it writes the
    counts — *A0 base:22356 像素 0 异常; A2 holed:14904 像素 0 异常*. Those
    counts are a fingerprint of **which record was replayed**, so checking them
    catches the one mistake that produces a plausible run out of the wrong
    evidence. It caught exactly that on this driver's first run.

    A4b compares these to the full arm. A4a only has to produce them and refuse
    to produce them quietly wrong.
    """
    out: Dict[str, Any] = {
        "source": "DESIGN.md §8 P-1",
        "expected_pixels": spec.expect_pixels,
        "observed_pixels": cheap.get("pixels_checked"),
        "expected_frames": spec.expect_frames,
        "observed_frames": cheap.get("frames"),
        "anomaly_kinds": cheap.get("anomaly_kinds"),
        "green": cheap.get("green"),
    }
    failures: List[str] = []
    if spec.expect_pixels is not None and \
            cheap.get("pixels_checked") != spec.expect_pixels:
        failures.append(
            "%s: replayed %s pixels against a pre-registered %d. The count is a "
            "fingerprint of which record was replayed -- check the trace before "
            "changing this number."
            % (spec.key, cheap.get("pixels_checked"), spec.expect_pixels))
    if spec.expect_frames is not None and cheap.get("frames") != spec.expect_frames:
        failures.append("%s: %s frames against a pre-registered %d"
                        % (spec.key, cheap.get("frames"), spec.expect_frames))
    if spec.expect_pixels is not None and not cheap.get("green"):
        failures.append(
            "%s: the cheap layer is red on the manual's own evidence (%s). This "
            "arm did not touch the cheap layer, so a red here is a wrong trace "
            "or a broken manual, not the ablation."
            % (spec.key, cheap.get("anomaly_kinds")))
    out["failures"] = failures
    out["holds"] = not failures
    return out


def _why_the_bus_is_empty(plan_report: Dict[str, Any]) -> str:
    """The empty bus has two very different causes, and they must not blur.

    A silent run on a world the manual gets right is the framework working.  A
    silent run on a UNSAT the manual got *wrong* is the finding, and the two
    would look identical in a report that only said `turns_the_loop: false`.
    """
    if plan_report.get("status") == "UNSAT":
        return ("the plan came back UNSAT and this arm settles it bare "
                "(C-4). No certificate is owed (constraint 6, cut), so there "
                "is no theorem, no `depends:` clause, and no directed probe "
                "(constraint 7, shadow 1) -- nothing exists that could put a "
                "refutation on the bus. THIS IS THE FINDING, not a quiet "
                "success: the verdict is archived unexamined whether it is "
                "true or false, and the arm cannot tell which.")
    return ("the cheap layer found no anomaly and the committed plan matched "
            "prediction. A silent loop here is the framework working as "
            "designed -- 无意外时 plan/commit 静默运转,免费 (Theoria.md:233).")


def _write_ledger(spec: WorldRun, world: Any, plan_report: Dict[str, Any],
                  out_dir: str) -> Dict[str, Any]:
    """A proxy v1.0 ledger for the episode, or a stated reason there is none.

    The plan is executed once more here to collect the frames the ledger format
    needs.  `run_plan` also walks it, for a different purpose — it is checking
    the manual against the world — and the walk is deterministic, so the two
    agree by construction rather than by coincidence.
    """
    path = os.path.join(out_dir, "episode.jsonl")
    directions = plan_report.get("directions")
    if not directions:
        return {"written": None,
                "why": "no plan, so no episode: %s"
                       % plan_report.get("verdict", "UNSAT")}

    actions = [plan_abl.WORLD_ACTION[d] for d in directions]
    state = world.initial()
    frames = [world.render(state)]
    wins = [world.is_win(state)]
    for action in actions:
        state = world.step(state, action)
        frames.append(world.render(state))
        wins.append(world.is_win(state))

    ledger_abl.write_episode(
        path, run_id="a4a-%s" % spec.key, world_name=spec.key,
        actions=actions, frames=frames, wins=wins,
        outcome="WIN" if wins[-1] else "NOT_FINISHED",
        extra_start={"manual": spec.dsl, "trace": spec.trace},
        extra_end={"exhibit": spec.exhibit})
    return {"written": os.path.relpath(path, REPO).replace("\\", "/"),
            "steps": len(actions) + 1,
            "outcome": "WIN" if wins[-1] else "NOT_FINISHED"}


def _write(path: str, payload: Any) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    return path


def _ledger_lines_modulo_ts(path: str) -> List[str]:
    out: List[str] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            record.pop("ts", None)
            out.append(json.dumps(record, sort_keys=True, ensure_ascii=False))
    return out


def determinism(keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run everything twice into separate roots and compare the outputs.

    CLAUDE.md makes byte-reproducibility a requirement rather than a nicety, and
    every artefact here meets it **except the ledger**, which carries a wall
    clock because `proxy.ledger` writes `ts` on every record. That field is
    upstream's format and correct in it — a ledger is a record of an event and
    an event happened at a time — so the ledger is compared *modulo* `ts` and
    everything else byte for byte. Saying which fields are exempt, and checking
    that nothing else differs, is the difference between a documented exemption
    and an unexamined one.
    """
    roots = [os.path.join(ARTIFACTS, "_determinism", "run%d" % i) for i in (1, 2)]
    for root in roots:
        for spec in [WORLD_BY_KEY[k] for k in (keys or list(WORLD_BY_KEY))]:
            run_world(spec, out_root=root)

    def normalised(path: str, root: str) -> str:
        """The file's text with its own output root replaced by a placeholder.

        The two runs write to different directories, and a report that records
        where it wrote things faithfully says so.  The claim under test is *same
        inputs, same outputs*, and the output root is an input — so comparing
        the raw bytes would be comparing two runs that were given different
        inputs and calling the expected difference a defect.  Only the root is
        normalised, and only in the two spellings a JSON file can carry it.
        """
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        # Both spellings a report can carry: the absolute root, and the
        # repo-relative one -- `certify.replay` records the latter.
        for base in (root, os.path.relpath(root, REPO)):
            for spelling in (base, base.replace("\\", "\\\\"),
                             base.replace("\\", "/"),
                             base.replace("/", "\\").replace("\\", "\\\\")):
                text = text.replace(spelling, "<OUT_ROOT>")
        return text

    differences: List[str] = []
    exempt: List[str] = []
    names: List[str] = []
    skipped: List[str] = []
    for dirpath, dirs, files in os.walk(roots[0]):
        # `__pycache__` holds the interpreter's own bytecode for the generated
        # `theory.py`, which embeds a source mtime. It is a side effect of
        # importing the module, not an output of this arm.
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            first = os.path.join(dirpath, name)
            relative = os.path.relpath(first, roots[0])
            second = os.path.join(roots[1], relative)
            names.append(relative.replace("\\", "/"))
            if not os.path.exists(second):
                differences.append("%s: missing from the second run" % relative)
                continue
            if name.endswith(".jsonl"):
                if _ledger_lines_modulo_ts(first) != _ledger_lines_modulo_ts(second):
                    differences.append("%s: differs in a field other than `ts`"
                                       % relative)
                else:
                    exempt.append(relative.replace("\\", "/"))
                continue
            if normalised(first, roots[0]) != normalised(second, roots[1]):
                differences.append("%s: differs between two runs, and not only "
                                   "in the output root" % relative)
    for dirpath, _dirs, files in os.walk(roots[0]):
        if os.path.basename(dirpath) == "__pycache__":
            skipped.extend(os.path.join(os.path.basename(os.path.dirname(dirpath)),
                                        f).replace("\\", "/") for f in files)
    return {
        "files_compared": sorted(names),
        "n_files": len(names),
        "ledgers_compared_modulo_ts": sorted(exempt),
        "exempt_field": "ts",
        "exempt_because": ("proxy.ledger stamps every record with a wall clock. "
                           "A ledger is a record of an event, so the field is "
                           "right there; it is named here rather than silently "
                           "tolerated."),
        "normalised": "the output root, because the two runs are given "
                      "different ones and a report that records where it wrote "
                      "is right to differ",
        "not_compared": sorted(skipped),
        "not_compared_because": "__pycache__ is the interpreter's bytecode for "
                                "the generated theory.py and embeds a source "
                                "mtime; it is a side effect of importing, not "
                                "an output of this arm",
        "differences": differences,
        "deterministic": not differences,
    }


#: The fields that carry a decision.  If E1 and E2 agree on every one of them,
#: then nothing this arm records distinguishes a true impossibility from a false
#: one — which is P-6, as a table rather than as an argument.
DECISION_FIELDS: Tuple[Tuple[str, Callable[[Dict[str, Any]], Any]], ...] = (
    ("verdict", lambda r: r["verdict"]),
    ("settled", lambda r: r["settled"]),
    ("settled_by", lambda r: r["beats"]["plan"].get("settled_by")),
    ("certificate_owed", lambda r: r["beats"]["plan"].get("certificate_owed")),
    ("directed_probes_scheduled",
     lambda r: r["beats"]["plan"].get("directed_probes_scheduled")),
    ("distinguishes_proof_from_exhaustion",
     lambda r: r["beats"]["plan"].get("distinguishes_proof_from_exhaustion")),
    ("cheap_layer_green",
     lambda r: r["beats"]["certify"]["report"].get("green")),
    ("surprises_on_the_bus", lambda r: r["surprises"]["count"]),
    ("loop_turns", lambda r: r["beats"]["loop_gate"]["turns_the_loop"]),
    ("theorize_owed", lambda r: r["beats"]["theorize"]["owed"]),
)

#: What is actually true of each exhibit's world, held by the referee and never
#: by the arm.  This is the only place in this file that knows it.
GROUND_TRUTH = {
    "a0-no-button": {"really_solvable": False,
                     "so_the_verdict_unsolvable_is": "TRUE",
                     "why": "the Button is absent, so the Door never opens and "
                            "the goal cell is unreachable"},
    "a2-holed": {"really_solvable": True,
                 "so_the_verdict_unsolvable_is": "FALSE",
                 "why": "the world has the teleport rule and the goal is "
                        "reachable in 18 moves; the manual is missing it"},
}


def _exhibit_comparison(reports: Dict[str, Any]) -> Dict[str, Any]:
    """E1 beside E2, field by field.  The comparison A4's ticket asks for.

    The two runs are a true impossibility and a false one.  Every field below
    that comes out `SAME` is a field on which this arm's record of the two is
    identical, and the union of them is the answer to *does the arm believe an
    A2-type false theorem, and would anything notice?*
    """
    e1, e2 = reports.get("a0-no-button"), reports.get("a2-holed")
    if not (e1 and e2):
        return {"available": False,
                "why": "both a0-no-button and a2-holed must be in the run"}
    rows = {}
    identical = []
    for name, get in DECISION_FIELDS:
        left, right = get(e1), get(e2)
        rows[name] = {"E1_a0_no_button": left, "E2_a2_holed": right,
                      "same": left == right}
        if left == right:
            identical.append(name)
    return {
        "available": True,
        "fields": rows,
        "n_fields": len(rows),
        "n_identical": len(identical),
        "indistinguishable": len(identical) == len(rows),
        "ground_truth": GROUND_TRUTH,
        "reading": (
            "E1's world is really unsolvable and E2's is really solvable, so "
            "one of these two verdicts is true and the other is false. Every "
            "decision-carrying field this arm records is the same for both. "
            "Nothing here is a bug: the fields are identical because the cut "
            "removed the only machinery whose output would have differed -- the "
            "certificate obligation and the directed probes it schedules. That "
            "is P-6, and it is also the ticket's question answered: the arm "
            "believes the false theorem, and nothing in it notices."
            if len(identical) == len(rows) else
            "the two exhibits differ on %d field(s); P-6 as pre-registered "
            "expects them to be indistinguishable, so a difference here is "
            "either a finding or a defect in the driver and must be diagnosed "
            "before it is reported as either."
            % (len(rows) - len(identical))),
    }


def run_all(keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """Every world, with the upstream trees hashed on both sides of the run."""
    before = pin.hash_tree()
    reports = {}
    for key in (keys or [w.key for w in WORLDS]):
        reports[key] = run_world(WORLD_BY_KEY[key])
    after = pin.hash_tree()
    moved = pin.changed(before, after)

    exhibits = _exhibit_comparison(reports)
    pre_registered_failures = [
        line for report in reports.values()
        for line in report["beats"]["certify"]["pre_registered"]["failures"]]

    payload = {
        "what": "ablation-arm end-to-end run (A4a step 3)",
        "worlds": reports,
        "exhibits": exhibits,
        "pre_registered_failures": pre_registered_failures,
        "pre_registered_holds": not pre_registered_failures,
        "upstream_unchanged": not moved,
        "upstream_files_changed": moved,
        "upstream_trees_hashed": len(before),
        "loop_turned_on": sorted(k for k, r in reports.items()
                                 if r["beats"]["loop_gate"]["turns_the_loop"]),
        "surprise_kinds_in_taxonomy": 7,
        "surprise_kinds_available_to_this_arm": len(
            SurpriseBus(ablated=True).kinds_available()),
    }
    _write(os.path.join(ARTIFACTS, "run_all.json"), payload)
    return payload


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--world", action="append", choices=sorted(WORLD_BY_KEY),
                        help="run one world; repeatable. Default: all four.")
    parser.add_argument("--json", action="store_true", help="dump the reports")
    parser.add_argument("--twice", action="store_true",
                        help="run everything twice into separate roots and "
                             "compare; ledgers are compared modulo `ts`")
    args = parser.parse_args(argv)

    if args.twice:
        result = determinism(args.world)
        print("determinism: %d file(s) compared, %d ledger(s) modulo `ts`"
              % (result["n_files"], len(result["ledgers_compared_modulo_ts"])))
        for line in result["differences"]:
            print("  DIFF " + line)
        print("  deterministic: %s" % result["deterministic"])
        return 0 if result["deterministic"] else 1

    payload = run_all(args.world)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print("ablation arm -- %d world(s)" % len(payload["worlds"]))
    for key, report in payload["worlds"].items():
        gate = report["beats"]["loop_gate"]
        print("  %-14s %-6s verdict=%-11s surprises=%d  loop_turns=%s%s"
              % (key,
                 report["beats"]["plan"].get("status"),
                 report.get("verdict"),
                 gate["bus"]["count"], gate["turns_the_loop"],
                 "  [%s]" % report["exhibit"] if report["exhibit"] else ""))
        sweep = report["beats"]["certify"].get("sweep")
        if sweep:
            print("       sweep (%s, off the bus): green=%s anomalies=%d"
                  % (os.path.basename(sweep["trace"]),
                     sweep["report"].get("green"),
                     len(sweep["report"].get("anomalies", []))))
    exhibits = payload["exhibits"]
    if exhibits.get("available"):
        print("  E1 (true impossibility) vs E2 (false one): %d/%d "
              "decision fields identical -> indistinguishable=%s"
              % (exhibits["n_identical"], exhibits["n_fields"],
                 exhibits["indistinguishable"]))
    print("  surprise kinds: %d in the taxonomy, %d available to this arm"
          % (payload["surprise_kinds_in_taxonomy"],
             payload["surprise_kinds_available_to_this_arm"]))
    print("  P-1 pre-registered counts hold: %s" % payload["pre_registered_holds"])
    for line in payload["pre_registered_failures"]:
        print("    FAIL " + line)
    print("  upstream trees unchanged: %s (%d files hashed)"
          % (payload["upstream_unchanged"], payload["upstream_trees_hashed"]))
    return 0 if (payload["upstream_unchanged"]
                 and payload["pre_registered_holds"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
