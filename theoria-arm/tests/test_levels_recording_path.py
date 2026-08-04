"""The recording path, end to end, on a leg that actually completes a level.

**Why this file exists (A34, following A31).** Twenty-two `runs/*/levels.jsonl`
were zero bytes -- every one on disk, including the mock legs -- and
`inner/levels.py` existed in full. Nothing could distinguish "the detector never
fired" from "the detector fired and the write is broken", and `tests/test_
levels.py` could not settle it either: every test there drives `TheoriaArm.
_record` directly with a hand-built envelope. That proves the unit works. It
does not prove the *shell* works, and the shell is what wrote the twenty-two
empty files.

So the tests here run `harness.run.play` -- the real shell, the real env proxy,
the real `proxy/mock` world -- and the leg genuinely reaches the mock's goal.

**What the measurement found.** Three things, in order:

1. The detector is called on every recorded step and has never fired, because no
   world has ever incremented the counter in front of it. On the live side that
   is A34's arithmetic (g50t level 1 costs a reference solver 78 actions; the
   longest leg walked 33). On the mock side it is stronger and stranger than
   that: the offline exploration policy is `min(legal, key=(times_tried, id))`,
   which on the mock's level 1 oscillates between exactly two cells **forever**.
   A mock leg on the default policy cannot reach the goal at any budget. That is
   `test_the_default_offline_policy_cannot_reach_the_mocks_goal`, and it is why
   the mock legs' zero bytes were never evidence of anything.

2. Given a leg that does reach the goal, the whole path works and writes.
   `test_a_mock_leg_that_completes_a_level_writes_the_boundary_to_disk`.

3. And the one case where it did **not** work is the case that matters most:
   the winning increment. `inner/levels.py` suppressed the event on the final
   level -- correctly, for the destructive half of the handling -- and thereby
   also suppressed the *record* of it. A seven-level g50t win would have written
   six rows to `levels.jsonl`, while `inner/scoreboard.ScoreWatch` recorded
   seven events and a verdict of `observed`. Two instruments, one event, silent
   disagreement, on the single run this project exists to produce.
   `test_the_two_instruments_agree_about_the_winning_increment`.

**The negative control is the last test and it is the point.** A leg that
genuinely completed a level, with `levels.jsonl` truncated to zero bytes, must
read as *completion information missing* and never as zero completions. While
those two produce the same integer, "no arm has ever completed a level" is a
sentence no measurement can refute.
"""

import json
import os
import shutil
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import level_evidence                   # noqa: E402
from inner.loop import TheoriaArm                     # noqa: E402

#: The mock opens every leg with a sweep of ACTION1..5 before the main loop's
#: first exploration, so a scripted walk starts from where that sweep left the
#: agent, not from the RESET position. Derived by breadth-first search over
#: `proxy.mock.arc_mock.Session` itself (never hand-copied), and re-derived at
#: test time by `_walk_to_the_first_boundary` so a change to the mock's maze is
#: a failing search rather than a wrong constant.
OPENING_SWEEP = [1, 2, 3, 4, 5]

GAME = "g50t-5849a774"


def _walk_to_the_first_boundary(prefix=OPENING_SWEEP, limit=30):
    """The shortest action sequence after `prefix` that increments the counter.

    Searched against the mock's own `Session`, so it is a fact about the world
    under test rather than a constant that can rot.
    """
    import collections                                # noqa: PLC0415

    from proxy.mock.arc_mock import Session           # noqa: PLC0415

    def replay(path):
        session = Session("guid-test", GAME, None)
        for action in list(prefix) + list(path):
            session.step(action)
        return session

    queue = collections.deque([[]])
    seen = {(0, (1, 1), "NOT_FINISHED")}
    while queue:
        path = queue.popleft()
        if len(path) > limit:
            break
        for action in (1, 2, 3, 4):
            session = replay(path + [action])
            key = (session.levels_completed, session.pos, session.state)
            if key in seen:
                continue
            seen.add(key)
            if session.levels_completed >= 1:
                return path + [action]
            queue.append(path + [action])
    raise AssertionError(
        "no action sequence within %d steps completes a level of the mock; "
        "either the maze changed or the transition rule did" % limit)


class _ScriptedArm(TheoriaArm):
    """The real arm, with the *choice* of action scripted and nothing else.

    Only `_probe_or_explore`'s pick is replaced. `_send`, `_record`,
    `LevelLog.observe`, `_on_level_boundary`, `_witness_the_win`, `_save_all`
    and every artefact writer are the shipped ones -- which is the whole point:
    the defect class this file guards against is one that lives between the
    detector and the disk, and a test that stubs any of them cannot see it.

    Scripting the action is not cheating. What is under test is what the arm
    records when the world moves, not whether this arm's explorer can solve a
    maze -- and `test_the_default_offline_policy_cannot_reach_the_mocks_goal`
    below states, as a measurement, that it cannot.
    """

    def __init__(self, *args, script=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.script = list(script)

    def _probe_or_explore(self, namespace, record):
        if not self.script:
            return super()._probe_or_explore(namespace, record)
        chosen = self.script.pop(0)
        record["probe"] = {"kind": "scripted", "action": chosen,
                           "why": "a scripted walk to the mock's goal; see "
                                  "tests/test_levels_recording_path.py"}
        self._send(chosen, note="scripted")


def _own_pool(tmp_path):
    """A spend pool this test owns. Same reason as `tests/test_arm.py`'s copy:
    `play()` defaults to the fleet's shared pool and tests have billed it."""
    from harness import run as run_mod                 # noqa: PLC0415
    from proxy.spend_gate import SpendGate             # noqa: PLC0415

    policy = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    return SpendGate(policy), {"pool": policy.pool,
                               "ledger_abspath": os.path.abspath(
                                   policy.ledger_path)}


def _play_scripted(tmp_path, script, budget):
    """One whole leg through the shipped shell, returned with its run dir."""
    from harness.run import FIXTURE_RUNS_DIR, play     # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    slug = "pytest-a34-" + os.path.basename(str(tmp_path))
    run_dir = os.path.join(FIXTURE_RUNS_DIR, slug)
    if os.path.isdir(run_dir):
        shutil.rmtree(run_dir)

    def factory(env_base, run):
        return _ScriptedArm(env_base=env_base, run=run, game_id=GAME,
                            budget_actions=budget, offline=True,
                            script=script)

    with MockArc(api_key=DEFAULT_KEY, games=[GAME]) as mock:
        gate, expect = _own_pool(tmp_path)
        summary = play(GAME, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False,
                       spend_gate=gate, expect_pool=expect,
                       runs_root=FIXTURE_RUNS_DIR,
                       ledger_path=str(tmp_path / "ledger.jsonl"))
    return summary, run_dir


def _rows(run_dir):
    path = os.path.join(run_dir, "levels.jsonl")
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ===================================================== 1. the mechanism
def test_the_default_offline_policy_cannot_reach_the_mocks_goal():
    """Why every mock leg's `levels.jsonl` is zero bytes, as a measurement.

    `inner/loop._probe_or_explore` explores by taking the least-tried legal
    action, ties broken by the lowest id. With no manual -- which is every
    offline leg, since `offline=True` makes no model call -- that is the only
    branch reachable, so the action sequence is 1,2,3,4,5,1,2,3,4,5,...

    Against the mock's level 1 that sequence visits **two** cells. Not few: two.
    The agent steps down and back up forever, and no budget changes it. So the
    zero bytes in `runs/a3-gate-mock/levels.jsonl` and
    `runs/audit-smoke/levels.jsonl` were never evidence that the recording path
    was broken, and never evidence that it worked either. They were a fact about
    the explorer.
    """
    from proxy.mock.arc_mock import Session           # noqa: PLC0415

    session = Session("guid-test", GAME, None)
    visited = set()
    for i in range(200):
        session.step((i % 5) + 1)
        visited.add(session.pos)
    assert session.levels_completed == 0
    assert len(visited) == 2, (
        "the round-robin explorer is expected to oscillate between exactly two "
        "cells of the mock's level 1; it visited %d" % len(visited))


# ===================================================== 2. the positive
def test_a_mock_leg_that_completes_a_level_writes_the_boundary_to_disk(tmp_path):
    """The positive control A34 asked for, and the one that was missing.

    Everything before this test asserted that nothing crashed. This asserts
    that when a boundary genuinely happens, in a real leg, through the real
    shell, it is on disk afterwards -- in `levels.jsonl`, in `RUN_STATE.json`,
    in the turn series, and in `witnessed_wins.json`.
    """
    script = _walk_to_the_first_boundary()
    summary, run_dir = _play_scripted(tmp_path, script,
                                      budget=len(OPENING_SWEEP) + len(script) + 3)

    levels = summary["levels"]
    assert levels["levels_completed"] == 1, summary["stopped_because"]
    assert levels["boundaries"] == 1
    assert len(levels["starts"]) == 2, "the trajectory must be cut at the boundary"

    path = os.path.join(run_dir, "levels.jsonl")
    assert os.path.getsize(path) > 0, (
        "a leg that completed a level wrote a zero-byte levels.jsonl -- this is "
        "the twenty-two-file defect, reproduced")
    rows = _rows(run_dir)
    assert len(rows) == 1
    row = rows[0]
    assert row["event"] == "level_boundary"
    assert row["signal"] == "levels_completed"
    assert (row["from_level"], row["to_level"]) == (1, 2)
    assert row["levels_completed"] == 1 and row["levels_completed_before"] == 0
    assert isinstance(row["step_idx"], int)
    assert row["witnessed"] is True

    # The step the row points at is the step whose envelope carried the
    # increment. Checked against the trace rather than assumed, because an
    # off-by-one here silently mis-attributes the winning frame.
    with open(os.path.join(run_dir, "trace.jsonl"), encoding="utf-8") as fh:
        trace = [json.loads(line) for line in fh if line.strip()]
    assert trace[row["step_idx"]]["levels_completed"] == 1
    assert trace[row["step_idx"] - 1]["levels_completed"] == 0

    state = json.load(open(os.path.join(run_dir, "RUN_STATE.json"),
                           encoding="utf-8"))
    assert state["levels"]["starts"] == [0, row["step_idx"]]

    turns = json.load(open(os.path.join(run_dir, "turns.json"), encoding="utf-8"))
    boundary_turns = [t for t in turns if t.get("beat") == "level"]
    assert len(boundary_turns) == 1
    assert boundary_turns[0]["detail"] == "level 1 complete"

    wins = json.load(open(os.path.join(run_dir, "witnessed_wins.json"),
                          encoding="utf-8"))
    assert len(wins) == 1
    assert wins[0]["witness"] == "level_cleared"
    assert wins[0]["game_won"] is False
    assert wins[0]["final_grid"], (
        "the frame the world treated as won is the evidence inner/goal.py "
        "records the desk waiting for; a witness without it is a header")


# ============================== 3. the two instruments, on the winning increment
def _feed(arm, levels_completed, *, win_levels, state="NOT_FINISHED"):
    envelope = {"frame": [[[1, 1], [1, 1]]], "state": state,
                "available_actions": [1, 2, 3, 4, 5],
                "levels_completed": levels_completed,
                "win_levels": win_levels}
    return arm._record("ACTION1", 200, envelope)


def _bare_arm(tmp_path):
    run_dir = str(tmp_path)
    os.makedirs(run_dir, exist_ok=True)
    run = types.SimpleNamespace(dir=run_dir, run=None, run_id="r-pytest")
    return TheoriaArm(env_base="http://127.0.0.1:1", run=run, game_id=GAME,
                      offline=True, budget_actions=50, cost_ceiling_usd=None)


def test_the_two_instruments_agree_about_the_winning_increment(tmp_path):
    """A27 landed a second witness. Two witnesses that can disagree in silence
    are worse than one, and on the most important event they did.

    Before A34: on a three-level game won in three increments, `LevelLog`
    recorded two events and `levels.jsonl` two rows, while `ScoreWatch` recorded
    three `level_boundary` events and reported `observed`. The suppressed one
    was the win. The suppression itself is right -- the boundary handler drops
    `problem.json` and `generated/`, which on a winning run deletes the
    artefacts that say how it was won -- but it was suppressing the *record*
    along with the handling, and only the handling had an argument behind it.

    So the test is not "the counts are equal by luck": it is that every
    completion the free rung saw has a row on disk, and that the win is
    identifiable as a win rather than filed as a boundary into a level that does
    not exist.
    """
    arm = _bare_arm(tmp_path)
    arm.arc.win_levels = 3
    arm.current_turn = 1
    arm.books.write(theory="semantics:\n  frame persist\n")
    arm.books.write_problem({"board": []})

    for completed in (0, 1, 2):
        _feed(arm, completed, win_levels=3)
    arm.books.write_problem({"board": []})
    _feed(arm, 3, win_levels=3, state="WIN")

    watch_boundaries = [e for e in arm.scoreboard.events
                        if e["event"] == "level_boundary"]
    assert len(watch_boundaries) == 3, "the free rung sees all three increments"
    assert arm.scoreboard.boundary_verdict()["verdict"] == "observed"

    # `events` stays the segmenting list, paired with `starts`. Two boundaries,
    # three starts: the win opened no level.
    assert len(arm.levels.events) == 2
    # Steps 0..3; the counter reads 1 at step 1 and 2 at step 2, so those two
    # steps open levels 2 and 3. Step 3 is the win and opens nothing.
    assert arm.levels.starts == [0, 1, 2]
    assert arm.levels.finished is True
    assert arm.levels.completed == 3

    arm._save_all()
    rows = _rows(arm.dir)
    assert len(rows) == 3, (
        "three increments were observed and %d row(s) reached disk; the missing "
        "one is the win" % len(rows))
    assert [r["event"] for r in rows] == [
        "level_boundary", "level_boundary", "game_won"]
    win = rows[-1]
    assert win["levels_completed"] == 3 and win["final_level"] == 3
    assert win["to_level"] is None, "no level follows a win"
    assert win["from_level"] == 3

    # The two instruments now agree about how many completions happened, and
    # the summary keeps the two kinds apart rather than adding them up.
    summary = arm.levels.summary()
    assert summary["boundaries"] == 2 and summary["game_won"] == 1
    assert summary["boundaries"] + summary["game_won"] == len(watch_boundaries)

    # And the destructive half is still refused: this is the guarantee
    # `test_winning_the_last_level_does_not_open_an_eighth` bought, and
    # recording the event must not have cost it.
    assert os.path.exists(arm.books.problem_path), (
        "a won game keeps the problem that describes the level it won on")
    assert arm.levels.level == 3, "no level 4 of a 3-level game"

    # The winning frame is kept. It is the only state in this project's history
    # the world would ever have been observed to treat as a whole-game win.
    wins = json.load(open(os.path.join(arm.dir, "witnessed_wins.json"),
                          encoding="utf-8"))
    assert len(wins) == 3
    assert wins[-1]["game_won"] is True
    assert wins[-1]["final_step_idx"] == win["step_idx"], (
        "at a boundary the increment's step is the first frame of the NEXT "
        "level; at a win it is the final frame itself")


# ===================================================== 4. the negative control
def test_a_completed_level_with_a_truncated_record_reads_as_missing_not_zero(
        tmp_path):
    """A34's negative control, and the reason this whole item was raised.

    Build a leg that **did** complete a level, then truncate its `levels.jsonl`
    to zero bytes -- the exact byte state of all twenty-two archived files. Every
    instrument must report *completion information missing*. Reporting zero
    completions is the defect: while a lost record and a lost game produce the
    same integer, "nothing has ever completed a level" cannot be refuted by any
    measurement, because winning and failing to record look identical on disk.
    """
    script = _walk_to_the_first_boundary()
    _, run_dir = _play_scripted(tmp_path, script,
                                budget=len(OPENING_SWEEP) + len(script) + 3)

    honest = level_evidence.read_leg(run_dir)
    assert honest["verdict"] == "observed"
    assert honest["levels_completed"] == 1

    # -- the truncation, byte for byte the state of the twenty-two ------------
    path = os.path.join(run_dir, "levels.jsonl")
    open(path, "w", encoding="utf-8").close()
    assert os.path.getsize(path) == 0

    damaged = level_evidence.read_leg(run_dir)
    assert damaged["verdict"] == "evidence_missing", damaged["detail"]
    assert damaged["levels_completed"] is None, (
        "a completion whose event record is gone must not be published as a "
        "number, and must not be published as 0")
    assert damaged["counter_max_in_trace"] == 1, (
        "the trace still says the counter moved -- which is what makes this a "
        "missing record rather than a missing level")
    assert "missing" in damaged["detail"]

    # -- and it must survive aggregation ------------------------------------
    #
    # `armtools/round.py` used to add `l.get("levels_completed") or 0` across a
    # round's legs. Under that rule the row below contributes 0 and the round
    # reads "one leg, zero levels", which is a claim about the world made from a
    # claim about a file.
    real_zero = {"slug": "a-leg-that-genuinely-completed-nothing",
                 "verdict": "measured_absent", "levels_completed": 0}
    never_looked = {"slug": "a-leg-whose-envelopes-never-carried-the-counter",
                    "verdict": "unmeasured", "levels_completed": None}
    total = level_evidence.total(
        [dict(damaged, slug="the-truncated-leg"), real_zero, never_looked])

    assert total["legs"] == 3
    assert total["legs_counted"] == 1, (
        "only the measured-absent leg may be counted; the other two are "
        "unknowns wearing a zero")
    assert total["levels_completed"] == 0
    assert total["legs_not_counted"] == 2
    assert total["not_counted_slugs"] == [
        "a-leg-whose-envelopes-never-carried-the-counter", "the-truncated-leg"]
    assert total["by_verdict"] == {"evidence_missing": 1, "measured_absent": 1,
                                   "unmeasured": 1}
    # The three are three different sentences and the reading says so.
    assert "evidence_missing=1" in total["reading"]
    assert "unmeasured=1" in total["reading"]


def test_absence_and_measured_absence_are_different_verdicts(tmp_path):
    """The other half of the same rule, on legs that completed nothing.

    `runs/audit-smoke` looked at four envelopes and the counter never rose:
    that is a measured absence and a legitimate zero. `runs/a3-gate-mock` has no
    `trace.jsonl` at all: nothing was looked at, and a zero there is invented.
    Both were reported as `levels_completed: 0` before this module existed.
    """
    looked = tmp_path / "looked"
    looked.mkdir()
    with open(looked / "trace.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for i in range(4):
            fh.write(json.dumps({"step_idx": i, "levels_completed": 0}) + "\n")
    open(looked / "levels.jsonl", "w", encoding="utf-8").close()

    verdict = level_evidence.read_leg(str(looked))
    assert verdict["verdict"] == "measured_absent"
    assert verdict["levels_completed"] == 0
    assert verdict["envelopes_carrying_counter"] == 4

    blind = tmp_path / "blind"
    blind.mkdir()
    with open(blind / "trace.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"step_idx": 0, "action": "RESET",
                             "status": 500}) + "\n")
    open(blind / "levels.jsonl", "w", encoding="utf-8").close()

    verdict = level_evidence.read_leg(str(blind))
    assert verdict["verdict"] == "unmeasured"
    assert verdict["levels_completed"] is None
    assert "absence of a measurement" in verdict["detail"]
