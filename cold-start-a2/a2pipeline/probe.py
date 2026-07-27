"""M8 — 戳探.  Design the experiment, write the prediction first, then execute.

Theoria §1.10d: *"对证据最薄的子句、假设前沿分歧最大的动作设计判别实验（预测先
写），经唯一通道以脚本执行，结果入 probes.jsonl；打脸 → theorize"*.  Four
commitments, and this module keeps all four:

1. **the prediction is written before anything runs** — one outcome per
   surviving hypothesis, recorded, then the action is taken;
2. **navigation is planned with the manual, not with the world** — BFS over
   `theory.py`'s state space to a state whose *rendering* equals the target
   frame.  A divergence while navigating is an execution anomaly in its own
   right and is recorded rather than retried;
3. **the outcome is read off the frames** — never off the world's state;
4. **the frames are appended to the trace**, so the next `certify` covers the
   probes too.  `probed_trace.jsonl` is what the repaired manual is certified
   against.

## The three probes, and why these three

M7 handed over one target: at (6,4), `DOWN`, the manual predicts nothing and the
world jumps three cells.  That yields **P-01**, and it is executable.

`engines_report.json` records that the miner's frontier for the jump never
closed: `tcolor(DOWN)==3` and `at(6,4)` both fit the single witness, and
`probe_frontier` classified the separating experiment as *hypothetical* — this
world has exactly one Portal, so no reachable configuration tells the two apart.
**P-03** records that as a result rather than hiding it, and the ambiguity is
carried into the repaired manual as an openly pending theorem.  A probe that
cannot be run is a finding; a probe that is quietly dropped is a lie.

**P-02** probes the *next* theorem before it is proved rather than after.  The
repaired manual is going to claim the sealed pocket (7,1) is unreachable, and
that claim rests on a ring of wall cells.  The ring can be touched from exactly
three reachable (cell, action) pairs, and all three are executed here.

## One ordering constraint, and it is the world's, not ours

The Portal is one-way: after P-01 the Cart is in the right room and cannot come
back, so every left-room probe has to run first.  That is a real constraint on
experiment design in an irreversible world, and it is worth writing down —
A0's report noted the mirror-image problem, that an irreversible latch had ruled
its divergent states out entirely.
"""

import json
import os
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from common.candidates import emit, make_candidate  # noqa: E402

from certify.replay import ACTION_NAMES, load_theory  # noqa: E402

from a2world import a2_world  # noqa: E402
from a2world.ground_truth import read_trace  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
HOLED = os.path.join(ROOT, "theory", "generated_holed", "theory.py")
HISTORY = os.path.join(ARTIFACTS, "history_trace.jsonl")

MOVER_COLOUR = 6
WORLD_ACTION = {v: k for k, v in ACTION_NAMES.items()}

POCKET = (7, 1)


def _cell_of(frame, colour: int) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == colour:
                return (r, c)
    return None


def navigate(theory, start_state, target_cell, limit: int = 600):
    """Shortest action sequence the MANUAL believes reaches `target_cell`."""
    start = start_state.copy()
    seen = {start.key()}
    queue = deque([(start, [])])
    while queue:
        state, path = queue.popleft()
        if tuple(state.Cart_pos) == tuple(target_cell):
            return path
        if len(path) >= limit:
            continue
        for name, action in sorted(ACTION_NAMES.items()):
            nxt = theory.step(state, action)
            if nxt.key() in seen:
                continue
            seen.add(nxt.key())
            queue.append((nxt, path + [name]))
    return None


class Environment:
    """The only channel to the world: actions in, frames out.

    Deliberately thin and deliberately the only thing in this module that
    touches `a2world`.  Probes read `env.frame()`; nothing reads `env._state`.
    """

    def __init__(self, spec=a2_world.BASE):
        self._world = a2_world.A2World(spec)
        self._state = self._world.initial()
        self.log: List[Dict[str, object]] = []

    def frame(self):
        return self._world.render(self._state)

    def win(self) -> bool:
        return bool(self._world.is_win(self._state))

    def act(self, action: str):
        self._state = self._world.step(self._state, action)
        return self.frame()


def _probe_row(pid: str, question: str, at_cell, action: str,
               predictions: Dict[str, str], observed: str,
               navigation: int, note: str, tier: str = "executable",
               extra: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    surviving = sorted(h for h, p in predictions.items() if p == observed)
    refuted = sorted(h for h, p in predictions.items() if p != observed)
    row = {
        "id": pid,
        "tier": tier,
        "question": question,
        "mover_cell": list(at_cell) if at_cell else None,
        "action": action,
        "predictions": predictions,
        "observation": observed,
        "surviving": surviving,
        "refuted": refuted,
        "navigation_steps": navigation,
        "status": "refuted" if refuted else "confirmed",
        "note": note,
    }
    if extra:
        row.update(extra)
    return row


def run(theory_py: str = HOLED) -> Dict[str, object]:
    theory = load_theory(theory_py)
    env = Environment()

    # Replay the play record so the probes start where the theorizer stopped.
    frames, actions, wins = read_trace(HISTORY)
    rows_out: List[Dict[str, object]] = [json.loads(line) for line
                                         in open(HISTORY, encoding="utf-8")
                                         if line.strip()]
    mstate = theory.initial_state()
    for action in actions:
        if action is None:
            break
        env.act(action)
        mstate = theory.step(mstate, ACTION_NAMES[action])
    if env.frame() != theory.render(mstate):
        raise AssertionError("the manual and the world already disagree at the "
                             "end of the play record — nothing below is meaningful")

    probes: List[Dict[str, object]] = []
    appended: List[Dict[str, object]] = []

    def run_one(target_cell, action_name: str, pid: str, question: str,
                predictions: Dict[str, str], note: str,
                classify) -> Optional[Dict[str, object]]:
        nonlocal mstate
        path = navigate(theory, mstate, target_cell)
        if path is None:
            probes.append({
                "id": pid, "tier": "executable", "question": question,
                "status": "unreachable",
                "note": "the manual cannot navigate to the probe state; not run",
            })
            return None
        for step_action in path:
            before = env.frame()
            after = env.act(step_action)
            mstate = theory.step(mstate, ACTION_NAMES[step_action])
            appended.append({"frame": after, "action": step_action,
                             "probe": pid, "phase": "navigate"})
            if after != theory.render(mstate):
                probes.append({
                    "id": pid, "tier": "executable", "question": question,
                    "status": "execution_mismatch",
                    "at_step": len(appended),
                    "note": "the world diverged from the manual while navigating "
                            "— an anomaly in its own right, recorded not retried",
                })
                return None
            del before

        before = env.frame()
        after = env.act(action_name)
        mstate_pred = theory.step(mstate, ACTION_NAMES[action_name])
        appended.append({"frame": after, "action": action_name,
                         "probe": pid, "phase": "probe"})
        observed = classify(before, after)
        row = _probe_row(
            pid, question, _cell_of(before, MOVER_COLOUR), action_name,
            predictions, observed, len(path), note,
            extra={
                "mover_after": list(_cell_of(after, MOVER_COLOUR) or ()),
                "manual_predicted_mover": list(
                    tuple(mstate_pred.Cart_pos)),
                "manual_agreed": after == theory.render(mstate_pred),
            })
        probes.append(row)
        # The manual's own successor is not the world's; re-seat on the frame.
        mstate = mstate_pred
        cell = _cell_of(after, MOVER_COLOUR)
        if cell is not None:
            mstate.Cart_pos = cell
        return row

    def mover_outcome(before, after) -> str:
        a = _cell_of(before, MOVER_COLOUR)
        b = _cell_of(after, MOVER_COLOUR)
        if a == b:
            return "stays"
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1:
            return "steps to (%d,%d)" % b
        return "jumps to (%d,%d)" % b

    # ---- P-02 first: the Portal is one-way, so left-room probes go first ---
    ring = [((5, 1), "DOWN", "(6,1)"), ((6, 2), "LEFT", "(6,1)"),
            ((6, 2), "DOWN", "(7,2)")]
    for i, (cell, action, wall) in enumerate(ring, start=1):
        run_one(
            cell, action, "P-02.%d" % i,
            "is the wall ring around the sealed pocket %s really solid at %s?"
            % (str(POCKET), wall),
            {"ring_is_solid": "stays",
             "ring_has_a_gap": "steps to %s" % wall},
            "the repaired manual is about to claim (7,1) is unreachable; the "
            "claim rests on this ring, so the ring is probed before the theorem "
            "is proved rather than after",
            mover_outcome,
        )

    # ---- P-01 last: it is irreversible ------------------------------------
    run_one(
        (6, 4), "DOWN", "P-01",
        "M7 located the divergence here: at (6,4), DOWN.  What does the world "
        "actually do?",
        {"holed_manual__nothing_happens": "stays",
         "missing_rule__one_step_down": "steps to (7,4)",
         "missing_rule__teleport_to_7_6": "jumps to (7,6)"},
        "this is the probe the localisation asked for; the holed manual's "
        "prediction is one of the three hypotheses and it is on the record "
        "before the action is taken",
        mover_outcome,
    )

    # ---- P-03: designed, and NOT runnable.  Recorded as such. --------------
    probes.append({
        "id": "P-03",
        "tier": "hypothetical",
        "question": "is the jump triggered by the colour below the Cart "
                    "(tcolor(DOWN)==3) or by the Cart's being on (6,4)?",
        "frontier": [["act==DOWN", "tcolor(DOWN)==3"], ["act==DOWN", "at(6,4)"]],
        "status": "not_separable_in_this_world",
        "note": "`probe_frontier` ranks a separating experiment at 1.0 bits but "
                "classifies it hypothetical: it needs either a second colour-3 "
                "cell or a Cart on (6,4) with something else below, and this "
                "level has exactly one Portal, so neither configuration is "
                "reachable.  The two guards are extensionally identical here.  "
                "Decided on description length and carried into "
                "theory_repaired.dsl as an openly pending theorem — see "
                "THEORIZE_LOG R-05.",
        "source": "artifacts/engines_report.json probes[0]",
    })

    # ---- write the grown trace --------------------------------------------
    trace_rows = list(rows_out)
    if trace_rows:
        trace_rows[-1]["action"] = appended[0]["action"] if appended else None
    for i, row in enumerate(appended):
        trace_rows.append({
            "t": len(trace_rows),
            "frame": row["frame"],
            "action": appended[i + 1]["action"] if i + 1 < len(appended) else None,
            "win": row["frame"] == env.frame() and env.win(),
            "probe": row["probe"],
        })
    for i, row in enumerate(trace_rows):
        row["t"] = i
    trace_rows[-1]["action"] = None
    out_trace = os.path.join(ARTIFACTS, "probed_trace.jsonl")
    with open(out_trace, "w", encoding="utf-8", newline="\n") as handle:
        for row in trace_rows:
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")

    with open(os.path.join(ARTIFACTS, "probes.jsonl"), "w",
              encoding="utf-8", newline="\n") as handle:
        for row in probes:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    # the probe that found a new rule is a proposal, and proposals go through
    # the frozen contract like every other proposal
    candidates_path = os.path.join(ARTIFACTS, "candidates_probe.jsonl")
    if os.path.exists(candidates_path):
        os.remove(candidates_path)
    teleport = next((p for p in probes if p["id"] == "P-01"
                     and p.get("status") in ("refuted", "confirmed")), None)
    if teleport and teleport["surviving"]:
        emit(candidates_path, [make_candidate(
            engine="probe_frontier",
            kind="probe_design",
            payload={
                "probe": "P-01",
                "at": teleport["mover_cell"],
                "action": teleport["action"],
                "predictions": teleport["predictions"],
                "observation": teleport["observation"],
                "surviving": teleport["surviving"],
                "refuted": teleport["refuted"],
            },
            transitions=[len(rows_out) - 1],
            coverage="1/1",
        )])

    summary = {
        "probes_designed": len(probes),
        "executable": len([p for p in probes if p.get("tier") == "executable"]),
        "run": len([p for p in probes if p.get("status") in ("refuted", "confirmed")]),
        "refuted": len([p for p in probes if p.get("status") == "refuted"]),
        "confirmed": len([p for p in probes if p.get("status") == "confirmed"]),
        "not_separable": len([p for p in probes
                              if p.get("status") == "not_separable_in_this_world"]),
        "trace_frames_before": len(rows_out),
        "trace_frames_after": len(trace_rows),
        "probed_trace": os.path.relpath(out_trace, ROOT),
        "ordering_constraint": "the Portal is one-way, so every left-room probe "
                               "had to run before P-01; an irreversible world "
                               "constrains experiment order, not just experiment "
                               "design",
        "probes": probes,
    }
    return summary


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    summary = run()
    with open(os.path.join(ARTIFACTS, "probe_report.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    for probe in summary["probes"]:
        print("%-7s %-14s %s" % (probe["id"], probe["status"],
                                 probe.get("observation")
                                 or probe["question"][:70]))
    print("trace: %d -> %d frames" % (summary["trace_frames_before"],
                                      summary["trace_frames_after"]))
    return 0 if summary["run"] >= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
