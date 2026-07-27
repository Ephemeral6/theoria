"""probe: design an experiment, predict, execute, adjudicate.

This is the beat A0 never got to run. `A0_REPORT.md` §6.2: A0 emitted **zero**
executable probes, because its ambiguities were either extensionally identical
predicates or needed configurations an irreversible latch had already ruled out.
A0′ is reversible, so the divergent states are reachable and the experiment is
real.

The loop, per Theoria 1.10d — *"对证据最薄的子句、假设前沿分歧最大的动作设计判别
实验（预测先写），经唯一通道以脚本执行,结果入 probes.jsonl；打脸 → theorize"*:

1. `probe_frontier` picks the (state, action) that splits the surviving guards
   furthest, out of the states the trajectory actually visited;
2. **the prediction is written first** — one outcome per surviving hypothesis,
   recorded before anything is executed;
3. getting there is a planning problem and it is solved **with the manual**, not
   with the world: BFS over `theory.py`'s state space to a state whose rendering
   equals the target frame. Then the path is executed in the world, frame by
   frame. A mismatch during navigation is an execution anomaly in its own right,
   and it is recorded rather than silently retried;
4. the probe action is taken, the outcome is read **off the frames** — never off
   the world's internal state — and every hypothesis that predicted otherwise is
   refuted;
5. the frames are appended to the trace, so the next `certify` covers the probe
   too, and the whole record goes to `probes.jsonl`.
"""

import importlib.util
import json
import os
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from engines import probe_frontier as pf  # noqa: E402

from pipeline import atoms_a0  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from prime.world import a0p_world as W  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTION_NAMES = {"UP": ("push", "Cart", "up"), "DOWN": ("push", "Cart", "down"),
                "LEFT": ("push", "Cart", "left"), "RIGHT": ("push", "Cart", "right")}
WORLD_ACTION = {v: k for k, v in ACTION_NAMES.items()}


def load_theory(path: str):
    spec = importlib.util.spec_from_file_location("a0p_theory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ observing

def locate(frame, colour) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == colour:
                return (r, c)
    return None


def observed_outcome(before, after, rule_payload, track_colour) -> str:
    """Did the rule's effect happen?  Read off the frames, nothing else."""
    effect = rule_payload["effect"]
    kind = effect["type"]
    if kind == "move":
        a, b = locate(before, track_colour), locate(after, track_colour)
        if a is None or b is None:
            return "silent"
        return "fires" if (b[0] - a[0], b[1] - a[1]) == (effect["dy"], effect["dx"]) \
            else "silent"
    if kind == "recolor":
        return "fires" if locate(after, effect["to"]) is not None \
            and locate(before, effect["to"]) is None else "silent"
    if kind == "vanish":
        return "fires" if locate(before, track_colour) is not None \
            and locate(after, track_colour) is None else "silent"
    if kind == "appear":
        return "fires" if locate(before, track_colour) is None \
            and locate(after, track_colour) is not None else "silent"
    if kind == "none":
        return "fires" if before == after else "silent"
    raise ValueError("unknown effect %r" % (effect,))


def obs_from_frame(frame, board, background, mover_colour, track_colours):
    anchors, colours = {}, {}
    for tid, colour_set in track_colours.items():
        found = None
        for colour in colour_set:
            cell = locate(frame, colour)
            if cell is not None:
                found = (cell, colour)
                break
        anchors[tid] = found[0] if found else None
        colours[tid] = found[1] if found else None
    return atoms_a0.Obs(
        frame=tuple(tuple(row) for row in frame),
        mover_anchor=locate(frame, mover_colour),
        mover_shape=(1, 1),
        anchors=anchors,
        colors=colours,
        background=background,
    )


# ------------------------------------------------------------------ navigation

def navigate(theory, start_state, target_frame, limit: int = 400):
    """Shortest action sequence, **in the manual**, to a state that renders
    `target_frame`.  Returns None when the manual says it cannot get there."""
    if theory.render(start_state) == target_frame:
        return []
    seen = {start_state.key()}
    queue = deque([(start_state, [])])
    expansions = 0
    while queue:
        state, path = queue.popleft()
        expansions += 1
        if expansions > limit * 10:
            return None
        for action in theory.ACTIONS:
            nxt = theory.step(state, action)
            if nxt.key() in seen:
                continue
            seen.add(nxt.key())
            extended = path + [action]
            if theory.render(nxt) == target_frame:
                return extended
            if len(extended) < limit:
                queue.append((nxt, extended))
    return None


# ----------------------------------------------------------------------- run

def run_probes(theory_py: str, trace_path: str, engines_report: str,
               probes_path: str, out_trace: str,
               spec: W.WorldSpec = W.BASE,
               max_probes: int = 8) -> Dict[str, object]:
    theory = load_theory(theory_py)
    frames, actions, wins = read_trace(trace_path)
    report = json.load(open(engines_report, encoding="utf-8"))
    board = extract_board(frames)
    background = background_color(board, frames)

    candidates = [json.loads(line) for line
                  in open(os.path.join(ROOT, "prime", "artifacts",
                                       "candidates.jsonl"), encoding="utf-8")
                  if line.strip()]
    by_name = {c["payload"]["name"]: c["payload"] for c in candidates
               if c["kind"] == "rule_hypothesis"}
    track_colour = {t["id"]: t["color"] for t in report["segmentation"]["tracks"]}
    track_colours = {t["id"]: sorted({t["color"], 7, 8} if t["color"] in (7, 8)
                                     else {t["color"]})
                     for t in report["segmentation"]["tracks"]}
    mover = report["segmentation"]["mover"]

    executable = [p for p in report["probes"] if p.get("tier") == "executable"]
    executable.sort(key=lambda p: (-p["entropy_bits"], p["rule"]))
    executable = executable[:max_probes]

    world = W.A0PWorld(spec)
    wstate = world.initial()
    mstate = theory.initial_state()
    for action in actions:
        if action is None:
            break
        wstate = world.step(wstate, action)
        mstate = theory.step(mstate, ACTION_NAMES[action])

    trace_rows = [json.loads(line) for line in open(trace_path, encoding="utf-8")
                  if line.strip()]
    rows: List[Dict[str, object]] = []
    appended = 0

    for probe in executable:
        payload = by_name.get(probe["rule"])
        if payload is None:
            continue
        target_frame = frames[probe["at_transition"]]

        hypotheses = pf.hypotheses_from_guards(
            [[_atom(name) for name in guard] for guard in probe["frontier"]],
            atoms_a0.evaluate, label=probe["rule"],
        )
        obs = obs_from_frame(target_frame, board, background,
                             track_colour[mover], track_colours)
        # --- prediction first ------------------------------------------
        predictions = {h.id: h.predict(obs, probe["action"]) for h in hypotheses}

        path = navigate(theory, mstate, target_frame)
        if path is None:
            rows.append({"rule": probe["rule"], "action": probe["action"],
                         "status": "unreachable",
                         "note": "the manual cannot navigate to the divergent "
                                 "state; probe not run"})
            continue

        # --- execute through the single channel ------------------------
        episode_states, episode_actions = [], []
        mismatch = None
        for action in path:
            wstate = world.step(wstate, WORLD_ACTION[("push", "Cart", action[2])]
                                if isinstance(action, tuple) else action)
            mstate = theory.step(mstate, ACTION_NAMES[
                WORLD_ACTION[action] if isinstance(action, tuple) else action])
            episode_actions.append(
                WORLD_ACTION[action] if isinstance(action, tuple) else action)
            episode_states.append(world.render(wstate))
            if world.render(wstate) != theory.render(mstate):
                mismatch = len(episode_actions)
                break
        if mismatch is not None:
            rows.append({"rule": probe["rule"], "action": probe["action"],
                         "status": "execution_mismatch", "step": mismatch,
                         "note": "the world diverged from the manual while "
                                 "navigating — an anomaly in its own right"})
            break

        before = world.render(wstate)
        wstate = world.step(wstate, probe["action"])
        after = world.render(wstate)
        mstate = theory.step(mstate, ACTION_NAMES[probe["action"]])
        episode_actions.append(probe["action"])
        episode_states.append(after)

        outcome = observed_outcome(before, after, payload,
                                   track_colour[payload["track"]])
        surviving = [h.id for h in hypotheses if predictions[h.id] == outcome]
        refuted = [h.id for h in hypotheses if predictions[h.id] != outcome]

        rows.append({
            "rule": probe["rule"],
            "coverage_before": probe["coverage"],
            "action": probe["action"],
            "entropy_bits": probe["entropy_bits"],
            "navigation_steps": len(path),
            "frontier": probe["frontier"],
            "predictions": predictions,
            "observation": outcome,
            "surviving": surviving,
            "refuted": refuted,
            "refuted_guards": [probe["frontier"][int(r.rsplit("_", 1)[1])]
                               for r in refuted],
            "surviving_guards": [probe["frontier"][int(s.rsplit("_", 1)[1])]
                                 for s in surviving],
            "status": "refuted" if refuted else "confirmed",
            "manual_agreed": theory.render(mstate) == after,
        })
        for i, frame in enumerate(episode_states):
            trace_rows.append({
                "t": len(trace_rows), "frame": frame,
                "action": episode_actions[i + 1] if i + 1 < len(episode_actions) else None,
                "win": frame == world.render(W.State(spec.goal_cell, wstate.switch_on)),
                "probe": probe["rule"],
            })
            appended += 1

    # the last appended frame ends the trace
    if trace_rows:
        trace_rows[-1]["action"] = None
    with open(out_trace, "w", encoding="utf-8", newline="\n") as handle:
        for row in trace_rows:
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    with open(probes_path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    return {
        "probes_designed": len(executable),
        "probes_run": len([r for r in rows if r.get("status") in
                           ("refuted", "confirmed")]),
        "refuted": len([r for r in rows if r.get("status") == "refuted"]),
        "confirmed": len([r for r in rows if r.get("status") == "confirmed"]),
        "unreachable": len([r for r in rows if r.get("status") == "unreachable"]),
        "execution_mismatch": len([r for r in rows
                                   if r.get("status") == "execution_mismatch"]),
        "manual_disagreed": [r["rule"] for r in rows
                             if r.get("manual_agreed") is False],
        "frames_appended": appended,
        "rows": rows,
    }


def _atom(name: str):
    """Rebuild an atom from its printed name (the frontier is stored as text)."""
    negated = name.startswith("!")
    body = name[1:] if negated else name
    if body.startswith("act=="):
        return atoms_a0.Atom("act", body[5:], negated)
    if body.startswith("at("):
        r, c = body[3:-1].split(",")
        return atoms_a0.Atom("at", (int(r), int(c)), negated)
    if body.startswith("tcolor("):
        head, value = body.split("==")
        return atoms_a0.Atom("tcolor", (head[len("tcolor("):-1], int(value)), negated)
    if body.startswith("color("):
        head, value = body.split("==")
        return atoms_a0.Atom("color", (head[len("color("):-1], int(value)), negated)
    if body.startswith("present("):
        return atoms_a0.Atom("present", body[len("present("):-1], negated)
    kind, rest = body.split("(strip(")
    return atoms_a0.Atom(kind, rest[:-2], negated)
