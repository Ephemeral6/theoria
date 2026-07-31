"""Change B's offline evidence: the same campaign, before and after.

Two parts, and the second exists because the first cannot show the interesting
state.

**Part 1 -- the loop, end to end against `proxy/mock`.** The same game, the same
budget, the same seed, played twice: once at the `off` rung and once at
`record`. No key, no network, no model call, no ARC quota. What it establishes
is the switch: `off` must leave every artefact free of the new key, and
`record` must carry the block on every turn and in the summary. It CANNOT show
`exploring_no_goal`, because an offline run makes no model call, so it never
gets a compiled manual, so its honest mode is `no_manual` throughout -- and
that the state machine says `no_manual` there rather than "exploring without a
goal" is itself worth recording.

**Part 2 -- the scoreboard, from real plan reports.** Two legs' worth of turn
records, built by feeding `GoalState` the output of the actual planner on
actual compiled books: one manual with a reachable goal, one identical manual
with the goal clause deleted. Those go through `armtools.archive.turn_series`
and `harness.campaign.Campaign.campaign_series` unmodified, and the scoreboard
columns are printed before and after. This is the comparison change B is for:
two campaigns that complete zero levels and are told apart anyway.

    python runs/20260731T1740Z-A3-change-b-goal-state/evidence.py

Writes `evidence.json` beside itself. Deterministic: no clock, no randomness,
no network.
"""

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import archive                          # noqa: E402
from harness import campaign as campaign_mod          # noqa: E402
from inner import plan as plan_beat                   # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.goal import GoalState                      # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402

GAME = "g50t-5849a774"                                # development pile
BUDGET_ACTIONS = 6


# ------------------------------------------------------------------ part 1
def _scratch_gate(root, name):
    """A spend gate over a throwaway pool. A rehearsal's fictional reservations
    must never land in `proxy/var/spend_gate.jsonl`, which the fleet shares --
    tests that forgot this once wrote 2,817 of its 4,775 actions."""
    from harness.run import _scratch_policy            # noqa: PLC0415
    from proxy.spend_gate import SpendGate             # noqa: PLC0415

    policy = _scratch_policy(os.path.join(root, "%s-pool.jsonl" % name))
    gate = SpendGate(policy)
    return gate, {"pool": policy.pool,
                  "ledger_abspath": os.path.abspath(policy.ledger_path)}


def _play(protocol, root):
    from harness.run import FIXTURE_RUNS_DIR, play     # noqa: PLC0415
    from inner.loop import TheoriaArm                  # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    slug = "evidence-goal-%s" % protocol

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=GAME,
                          budget_actions=BUDGET_ACTIONS, offline=True,
                          goal_protocol=protocol)

    with MockArc(api_key=DEFAULT_KEY, games=[GAME]) as mock:
        gate, expect = _scratch_gate(root, protocol)
        summary = play(GAME, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False,
                       spend_gate=gate, expect_pool=expect,
                       runs_root=FIXTURE_RUNS_DIR,
                       ledger_path=os.path.join(root, "%s.jsonl" % protocol))

    run_dir = os.path.join(FIXTURE_RUNS_DIR, slug)
    with open(os.path.join(run_dir, "turns.json"), encoding="utf-8") as fh:
        turns = json.load(fh)
    with open(os.path.join(run_dir, "RUN_STATE.json"), encoding="utf-8") as fh:
        run_state = json.load(fh)
    return {
        "protocol": protocol,
        "actions_ok": summary["budget"]["actions_ok"],
        "model_calls": summary["model_calls"],
        "levels_completed": (summary.get("levels") or {}).get(
            "levels_completed"),
        "turns": len(turns),
        "turn_record_keys": sorted({k for t in turns for k in t}),
        "turns_carrying_a_goal_block": sum(1 for t in turns if "goal" in t),
        "goal_modes": [(t.get("goal") or {}).get("mode") for t in turns],
        "summary_has_goal_key": "goal" in summary,
        "run_state_has_goal_key": "goal" in run_state,
        "goal_summary": summary.get("goal"),
    }


def part_one():
    root = tempfile.mkdtemp(prefix="change-b-evidence-")
    try:
        return {"off": _play("off", root), "record": _play("record", root)}
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ------------------------------------------------------------------ part 2
def _books(root, name, goal_clause):
    """The worked example, compiled, with or without a goal clause."""
    theory = WORKED_EXAMPLE.replace("goal count(Cart) = 1", "goal Cart.pos = (0, 1)")
    if goal_clause is None:
        theory = theory.replace("goal:\n  goal Cart.pos = (0, 1)\n", "")
    path = os.path.join(root, name)
    books = Books(path)
    books.write(theory=theory, playbook="# none\n")
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    compiled = books.compile_all()
    namespace, error = books.load_predictor()
    assert namespace is not None, error
    return books, namespace, compiled


def _leg_turns(root, name, goal_clause, protocol, turns=6):
    """One leg's `turns.json`, with the goal block produced by a real
    `GoalState` fed by a real `plan()` report."""
    books, namespace, compiled = _books(root, name, goal_clause)
    report = plan_beat.plan(books, namespace, compiled)
    state = GoalState(protocol)

    rows = []
    for turn in range(1, turns + 1):
        record = {"turn": turn, "actions_before": turn - 1,
                  "theorize_rounds": 0, "elapsed_s": float(turn)}
        if state.enabled:
            record["goal"] = state.observe(
                turn=turn, theory_text=books.theory, plan_report=report,
                distinct_states=turn + 2, actions_spent=turn,
                has_predictor=True)
        rows.append(record)
    return report, rows, state


def _series(root, slug, rows):
    run_dir = os.path.join(root, slug)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "turns.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh)
    doc = archive.turn_series(run_dir, records=[])
    doc["rows"] = doc["rows"]
    return doc


class _FakeCampaign(campaign_mod.Campaign):
    """`campaign_series()` over legs whose turn series are already on disk.

    Subclassed rather than reimplemented: the whole point is that the
    scoreboard columns come out of the real assembler, not out of this file.
    """

    def __init__(self, root, legs):
        self.prompt_id = "A3-change-b"
        self.games = [GAME]
        self.legs = legs
        self._root = root

    def _series_path(self, slug):
        return os.path.join(self._root, slug, "turn_series.json")


def _campaign_totals(root, legs):
    """`Campaign.campaign_series()` totals, with `ARM/runs/<slug>` redirected
    to this evidence run's scratch directory."""
    original = campaign_mod.ARM
    campaign_mod.ARM = root
    try:
        return _FakeCampaign(root, legs).campaign_series()
    finally:
        campaign_mod.ARM = original


def part_two():
    root = tempfile.mkdtemp(prefix="change-b-scoreboard-")
    try:
        out = {}
        for protocol in ("off", "record"):
            legs = []
            per_leg = []
            for idx, (name, clause) in enumerate(
                    (("leg-with-goal", "goal"), ("leg-no-goal", None)), start=1):
                slug = "%s-%s" % (protocol, name)
                report, rows, state = _leg_turns(root, slug, clause, protocol)
                doc = _series(root, slug, rows)
                os.makedirs(os.path.join(root, "runs", slug), exist_ok=True)
                with open(os.path.join(root, "runs", slug, "turn_series.json"),
                          "w", encoding="utf-8") as fh:
                    json.dump(doc, fh)
                legs.append({"slug": slug, "index": idx, "game_id": GAME,
                             "outcome": "budget_exhausted", "usd": 0.0,
                             "levels": {"events": []}})
                per_leg.append({
                    "leg": name,
                    "plan_status": report["status"],
                    "plan_produced": report.get("plan") is not None,
                    "goal_modes": [r["goal_mode"] for r in doc["rows"]],
                    "goal_summary": (state.summary() if state.enabled
                                     else None),
                })
            series = _campaign_totals(root, legs)
            out[protocol] = {"legs": per_leg,
                             "campaign_totals": series["totals"]}
        return out
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    doc = {
        "prompt_id": "A3-change-b",
        "what": "offline before/after for change B (goal-absence as a state)",
        "part_1_loop_end_to_end_against_mock": part_one(),
        "part_2_scoreboard_columns": part_two(),
    }
    path = os.path.join(HERE, "evidence.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    print(json.dumps(doc, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
