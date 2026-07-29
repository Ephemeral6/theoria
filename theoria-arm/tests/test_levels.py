"""The level boundary, offline: detection, the view, transfer, and the gate.

No key, no network, no model call. Every fixture here is hand-built or driven
through `TheoriaArm._record` with a fabricated envelope, because the one thing
that has to be checked -- what happens when `levels_completed` increments -- is
the one thing a run cannot be asked to reproduce on demand.

These tests are written against the specification in `inner/levels.py`'s module
docstring and `inner/loop.py:_on_level_boundary`, not against what the code
happens to do.
"""

import hashlib
import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import commit, surprise                    # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402
from inner.levels import LevelLog                     # noqa: E402
from inner.loop import MIN_NEW_FRAMES_BETWEEN_THEORIZE, TheoriaArm   # noqa: E402
from world.frames import FrameStore, Step, grid_hash  # noqa: E402


# ===================================================================== helpers
def _store(*steps):
    """(action, grid) pairs into a FrameStore, indices dense from 0."""
    store = FrameStore()
    for i, (action, grid) in enumerate(steps):
        store.add(Step(i, action, [grid]))
    return store


def _envelope(grid, levels_completed=0, state="NOT_FINISHED"):
    body = {"frame": [grid], "state": state,
            "available_actions": [1, 2, 3, 4, 5]}
    if levels_completed is not None:
        body["levels_completed"] = levels_completed
    return body


def _arm(tmp_path, **kwargs):
    """A `TheoriaArm` with no route to anything. `env_base` is never dialled:
    the tests below drive `_record` directly rather than `play()`."""
    run_dir = str(tmp_path)
    os.makedirs(run_dir, exist_ok=True)
    run = types.SimpleNamespace(dir=run_dir, run=None, run_id="r-pytest")
    kwargs.setdefault("offline", True)
    return TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                      game_id="g50t-5849a774", **kwargs)


def _feed(arm, grid, levels_completed=0, action="ACTION1"):
    return arm._record(action, 200, _envelope(grid, levels_completed))


G0 = [[0, 0], [0, 0]]
G1 = [[0, 6], [0, 0]]


def _sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# =========================================================== 1. the detection
def test_only_an_increase_in_levels_completed_is_a_boundary():
    """Equal is not a transition, and a decrease (which a full reset would
    produce) is not one either. A counter that is merely *present* must not be
    mistaken for a counter that moved."""
    log = LevelLog()
    assert log.observe(levels_completed=0, step_idx=0, action="RESET") is None
    assert log.observe(levels_completed=0, step_idx=1, action="ACTION1") is None
    event = log.observe(levels_completed=1, step_idx=2, action="ACTION2")
    assert event is not None and event["event"] == "level_boundary"
    assert log.observe(levels_completed=1, step_idx=3, action="ACTION1") is None
    assert log.observe(levels_completed=0, step_idx=4, action="ACTION1") is None
    assert log.completed == 1
    assert len(log.events) == 1


def test_an_absent_counter_is_not_a_zero_and_triggers_nothing():
    """`levels_completed` is absent on a failed command. Reading `None` as 0
    would report a boundary on the next successful command and cut the
    trajectory in half for no reason."""
    log = LevelLog()
    log.observe(levels_completed=1, step_idx=3, action="ACTION2")
    assert log.completed == 1 and log.starts == [0, 3]

    # A failed command carries no counter at all.
    assert log.observe(levels_completed=None, step_idx=4, action="ACTION1") is None
    assert log.completed == 1                          # not reset to 0
    assert log.starts == [0, 3]                        # no second boundary
    # And the next successful command, still on level 2, must not fire either.
    assert log.observe(levels_completed=1, step_idx=5, action="ACTION1") is None
    assert log.starts == [0, 3]


def test_the_new_levels_first_step_is_the_step_that_carried_the_count():
    """`starts` is an index into `FrameStore.steps`, and `level` is 1-based:
    level 1 begins at the first step of the run."""
    log = LevelLog()
    assert log.level == 1 and log.start == 0 and log.starts == [0]

    event = log.observe(levels_completed=1, step_idx=7, action="ACTION2",
                        turn=3, actions_spent=7)
    assert log.starts == [0, 7]
    assert log.start == 7
    assert log.level == 2
    assert event["from_level"] == 1 and event["to_level"] == 2
    assert event["step_idx"] == 7
    assert event["turn"] == 3 and event["actions_spent"] == 7
    assert "skipped" not in event

    log.observe(levels_completed=2, step_idx=19, action="ACTION4")
    assert log.starts == [0, 7, 19] and log.level == 3


def test_a_jump_of_more_than_one_level_says_so_instead_of_counting_one():
    """A level completed without a frame of its own is a fact about the run.
    Quietly counting it as one boundary would lose it."""
    log = LevelLog()
    event = log.observe(levels_completed=3, step_idx=5, action="ACTION2")
    assert event["skipped"] == 2
    assert event["levels_completed"] == 3
    assert event["levels_completed_before"] == 0
    assert log.completed == 3
    assert len(log.events) == 1                        # one event, not three


def test_the_summary_carries_the_starts_and_every_event():
    log = LevelLog()
    log.observe(levels_completed=1, step_idx=4, action="ACTION2")
    log.observe(levels_completed=2, step_idx=9, action="ACTION3")
    summary = log.summary()
    assert summary["levels_completed"] == 2
    assert summary["boundaries"] == 2
    assert summary["starts"] == [0, 4, 9]
    assert [e["step_idx"] for e in summary["events"]] == [4, 9]
    # `summary()` hands out copies: a caller mutating them must not be able to
    # rewrite the run's own record of its boundaries.
    summary["starts"].append(999)
    assert log.starts == [0, 4, 9]


# ============================================================== 2. the view
def _two_level_store():
    """Three steps of a 1-coloured level, then two of a 3-coloured one."""
    return _store(("RESET", [[1, 1], [1, 1]]),
                  ("ACTION1", [[1, 2], [1, 1]]),
                  ("ACTION1", [[1, 1], [1, 1]]),
                  ("ACTION2", [[3, 3], [3, 3]]),       # the new level's board
                  ("ACTION1", [[3, 3], [3, 4]]))


def test_the_level_view_shares_step_objects_rather_than_copying_them():
    """A step's identity has to be the same in both views, or `trace.jsonl`
    and the level's arithmetic would be talking about different objects."""
    store = _two_level_store()
    before = [s.before_hash for s in store.steps]
    view = store.since(3)

    assert len(view) == 2
    assert view.steps[0] is store.steps[3]
    assert view.steps[1] is store.steps[4]
    # Not renumbered, not rehashed: the index and the predecessor hash stay as
    # they were recorded.
    assert [s.step_idx for s in view.steps] == [3, 4]
    assert [s.before_hash for s in view.steps] == before[3:]
    assert view.steps[0].before_hash == grid_hash([[1, 1], [1, 1]])


def test_the_view_derives_only_from_the_tail():
    """`grids`, `actions`, `constant_cells`, `background` and `summary` are all
    statements about one continuous trajectory. Pooled across a boundary they
    are statements about neither level."""
    store = _two_level_store()
    view = store.since(3)

    assert view.grids == [[[3, 3], [3, 3]], [[3, 3], [3, 4]]]
    # `actions[t]` is the action taken *at* grid t, and the list ends in None.
    assert view.actions == ["ACTION1", None]
    assert view.background() == 3                      # the whole run's is 1
    assert store.background() == 1
    assert sorted(view.constant_cells()) == [(0, 0), (0, 1), (1, 0)]
    assert sorted(view.dynamic_cells()) == [(1, 1)]
    # Pooled, "never varied" is the intersection of two unrelated boards --
    # which describes neither.
    assert store.constant_cells() == []
    assert len(store.dynamic_cells()) == 4

    summary = view.summary()
    assert summary["steps"] == 2 and summary["states"] == 2
    assert summary["background"] == 3
    assert summary["colours_seen"] == [3, 4]
    assert summary["actions_used"] == ["ACTION1", "ACTION2"]
    assert store.summary()["steps"] == 5


def test_an_append_to_the_store_does_not_reach_a_view_already_taken():
    """`commit.execute` reads `store.actions` once, before it sends anything,
    and then sends -- which appends to the store it was handed a view of. If
    the view tracked the parent the roll-forward would be reading actions the
    script itself had just produced."""
    store = _two_level_store()
    view = store.since(3)
    assert len(view) == 2

    store.add(Step(5, "ACTION1", [[[3, 4], [3, 4]]]))
    assert len(store) == 6
    assert len(view) == 2
    assert view.actions == ["ACTION1", None]


def test_commit_rolls_forward_over_this_levels_actions_only():
    """The same property, through the caller that relies on it. Level 1 was
    played with ACTION2 and level 2 with ACTION1; a roll-forward that saw
    `("key", 2)` would be replaying a trajectory that no longer exists."""
    store = _store(("RESET", [[0]]),
                   ("ACTION2", [[0]]),
                   ("ACTION2", [[0]]),
                   ("ACTION2", [[0]]),                 # finished level 1
                   ("ACTION1", [[0]]))
    view = store.since(3)

    stepped = []

    def step(state, action):
        stepped.append(tuple(action))
        return state + 1

    namespace = {"initial_state": lambda: 0, "step": step,
                 "render": lambda s: [[s]]}

    def send(arc_action):
        store.add(Step(len(store.steps), "ACTION%d" % arc_action, [[[9]]]))
        return 200, {}, [[[9]]]

    commit.execute(namespace, [["key", 1]], send=send, store=view,
                   action_to_arc=commit.action_to_arc)

    # One roll-forward action (level 2's single recorded transition), then the
    # plan's own step. Never level 1's ACTION2s.
    assert stepped == [("key", 1), ("key", 1)]
    assert ("key", 2) not in stepped
    # And the send that happened inside did not grow the view under it.
    assert len(view) == 2
    assert len(store) == 6


# ======================================================= 3. what travels
def test_the_domain_travels_and_the_sha256_proves_it(tmp_path):
    """`cold-start-a3/a3pipeline/transfer.py`'s discipline: byte-identity is
    asserted by hash, not by inspection, so "the manual that played level 2 is
    the manual level 1 wrote" is a checkable claim about the artefacts."""
    first = Books(str(tmp_path / "level1"))
    first.write(theory=WORKED_EXAMPLE, playbook="# playbook\nprefer key(1)\n")

    second = Books(str(tmp_path / "level2"), seed_from=first.root)

    assert _sha256_file(second.theory_path) == _sha256_file(first.theory_path)
    assert _sha256_file(second.playbook_path) == _sha256_file(first.playbook_path)
    assert second.theory == WORKED_EXAMPLE

    carried = json.load(open(os.path.join(second.root, "CARRIED.json"),
                             encoding="utf-8"))
    assert carried["seed_from"] == first.root
    assert carried["empty"] is False
    assert carried["skipped"] == []
    assert set(carried["carried"]) == {"theory.dsl", "playbook.dsl"}
    # The recorded hash is the hash of the file that is now on disk.
    assert (carried["carried"]["theory.dsl"]["sha256"]
            == _sha256_file(second.theory_path))
    assert (carried["carried"]["playbook.dsl"]["sha256"]
            == _sha256_file(second.playbook_path))
    assert second.carried == carried


def test_the_carried_hash_describes_the_file_it_sits_next_to(tmp_path):
    """`CARRIED.json` is the evidence, so its hash has to be a hash of an
    artefact. `_write` normalises -- LF, and a trailing newline if the source
    lacked one -- so a seed that is not already normalised is *not* copied
    byte-for-byte, and a digest taken over the string in hand would name a file
    that exists nowhere. What must hold is that the recorded hash is the hash
    of the book this run will actually play."""
    seed = str(tmp_path / "seed")
    os.makedirs(seed)
    with open(os.path.join(seed, "theory.dsl"), "wb") as fh:
        fh.write(b"semantics:\r\n  frame persist")     # CRLF, no final newline
    with open(os.path.join(seed, "playbook.dsl"), "wb") as fh:
        fh.write(b"# none\n")

    books = Books(str(tmp_path / "level2"), seed_from=seed)
    carried = json.load(open(os.path.join(books.root, "CARRIED.json"),
                             encoding="utf-8"))
    assert (carried["carried"]["theory.dsl"]["sha256"]
            == _sha256_file(books.theory_path))
    assert (carried["carried"]["playbook.dsl"]["sha256"]
            == _sha256_file(books.playbook_path))
    # A seed that was itself written by `Books.write` -- which is the only way
    # the campaign produces one -- is already normalised, so for it the copy is
    # byte-identical and the hash is the source's too.
    assert (carried["carried"]["playbook.dsl"]["sha256"]
            == _sha256_file(os.path.join(seed, "playbook.dsl")))


def test_the_problem_and_the_derived_forms_do_not_travel(tmp_path):
    """The problem instance is computed from the level being played, so
    carrying it would be carrying an answer to a question this level has not
    asked. The four forms are re-derived, which is what co-derivation means."""
    first = Books(str(tmp_path / "level1"))
    first.write(theory=WORKED_EXAMPLE, playbook="# none\n")
    first.write_problem({"name": "level-1", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    first.compile_all()
    first.snapshot("end-of-level-1")
    assert os.path.exists(first.problem_path)
    assert os.listdir(first.generated)
    assert os.listdir(first.snapshots)

    second = Books(str(tmp_path / "level2"), seed_from=first.root)

    assert not os.path.exists(second.problem_path)
    assert os.listdir(second.generated) == []
    assert os.listdir(second.snapshots) == []
    assert sorted(os.listdir(second.root)) == [
        "CARRIED.json", "generated", "playbook.dsl", "snapshots", "theory.dsl"]


def test_having_nothing_to_carry_is_recorded_rather_than_raised(tmp_path):
    """The first level of the first game has nothing to carry, and "carried
    nothing" and "carried something" produce very different bills."""
    # (a) the source directory does not exist at all.
    missing = Books(str(tmp_path / "a"), seed_from=str(tmp_path / "nowhere"))
    assert missing.carried["empty"] is True
    assert [s["why"] for s in missing.carried["skipped"]] == \
        ["not present", "not present"]
    assert os.path.exists(os.path.join(missing.root, "CARRIED.json"))

    # (b) the directory exists but holds neither book.
    bare = str(tmp_path / "bare")
    os.makedirs(bare)
    partial = Books(str(tmp_path / "b"), seed_from=bare)
    assert partial.carried["empty"] is True
    assert partial.carried["carried"] == {}

    # (c) the books exist but are blank -- a level that never theorized.
    blank = Books(str(tmp_path / "blank"))
    blank.write(theory="   \n", playbook="\n")
    third = Books(str(tmp_path / "c"), seed_from=blank.root)
    assert third.carried["empty"] is True
    assert [s["why"] for s in third.carried["skipped"]] == ["empty", "empty"]
    assert third.theory == ""                          # nothing was written

    # (d) one book only: recorded as a partial carry, not as nothing.
    half = Books(str(tmp_path / "half"))
    half.write(theory=WORKED_EXAMPLE)
    fourth = Books(str(tmp_path / "d"), seed_from=half.root)
    assert fourth.carried["empty"] is False
    assert list(fourth.carried["carried"]) == ["theory.dsl"]
    assert fourth.carried["skipped"] == [{"file": "playbook.dsl",
                                          "why": "not present"}]


def test_the_arm_reports_what_it_carried_in(tmp_path):
    seed = Books(str(tmp_path / "seed"))
    seed.write(theory=WORKED_EXAMPLE, playbook="# none\n")
    arm = _arm(tmp_path / "run", seed_books=seed.root)
    assert arm.books.theory == WORKED_EXAMPLE
    assert arm.summary()["carried_books"]["empty"] is False
    assert set(arm.summary()["carried_books"]["carried"]) == {
        "theory.dsl", "playbook.dsl"}

    plain = _arm(tmp_path / "run2")
    assert plain.summary()["carried_books"] is None


# ================================================ 4. the boundary in the loop
def _armed_at_a_boundary(tmp_path):
    """An arm with a manual, a problem, pending surprises and a theorize behind
    it -- driven up to and over one level boundary."""
    arm = _arm(tmp_path)
    arm.books.write(theory=WORKED_EXAMPLE, playbook="# none\n")
    arm.books.write_problem({"name": "level-1", "grid": [2, 2],
                             "background": 0, "board": [[0, 0], [0, 0]],
                             "objects": []})
    arm.current_turn = 4
    for i in range(3):
        _feed(arm, G0 if i % 2 else G1, levels_completed=0)
    arm._frames_at_last_theorize = arm._frames_this_level()
    arm.register.fire("replay_mismatch", "the manual disagreed at t=2",
                      step_idx=2)
    arm.register.fire("render_mismatch", "a pixel nobody claims", step_idx=2)
    assert len(arm.register.pending) == 2
    step = _feed(arm, [[3, 3], [3, 3]], levels_completed=1, action="ACTION2")
    return arm, step


def test_the_boundary_snapshots_the_pair_and_drops_the_problem(tmp_path):
    arm, step = _armed_at_a_boundary(tmp_path)

    assert arm.levels.starts == [0, step.step_idx]
    assert arm.levels.level == 2

    snaps = sorted(os.listdir(arm.books.snapshots))
    assert snaps == ["rev01-level1-complete"]
    kept = os.path.join(arm.books.snapshots, "rev01-level1-complete")
    assert sorted(os.listdir(kept)) == ["playbook.dsl", "problem.json",
                                        "theory.dsl"]
    # The snapshot is taken before the problem is dropped, so the timeline
    # keeps what level 1 was actually played against.
    assert open(os.path.join(kept, "theory.dsl"), encoding="utf-8").read() \
        == WORKED_EXAMPLE

    # level N's board is not handed to the planner as level N+1's.
    assert not os.path.exists(arm.books.problem_path)
    # The domain stays exactly where it was: transfer is a claim about these
    # two files being unchanged across the boundary.
    assert arm.books.theory == WORKED_EXAMPLE
    assert arm.books.playbook == "# none\n"


def test_pending_surprises_are_retired_at_the_boundary_with_a_reason(tmp_path):
    """A surprise is the only thing that calls the desk. One fired against a
    trajectory that no longer exists would buy an adjudication of evidence the
    arm cannot show."""
    arm, _ = _armed_at_a_boundary(tmp_path)

    assert arm.register.pending == []
    retired = arm.turns[-1]["level_boundary"]["retired_surprises"]
    assert retired["retired"] == 2
    assert retired["kinds"] == ["render_mismatch", "replay_mismatch"]
    assert "level boundary: level 1 -> 2" in retired["reason"]
    for item in arm.register.items:
        assert item.handled_by.startswith("retired: level boundary")
    # Retired, not deleted.
    assert arm.register.summary()["total"] == 2


def test_the_boundary_appends_a_turn_and_names_the_beat(tmp_path):
    arm, step = _armed_at_a_boundary(tmp_path)
    entry = arm.turns[-1]
    assert entry["beat"] == "level"
    assert entry["turn"] == 4
    assert entry["detail"] == "level 1 complete"
    assert entry["level_boundary"]["from_level"] == 1
    assert entry["level_boundary"]["step_idx"] == step.step_idx
    assert "actions_spent" in entry

    # And the event reaches disk in its own file.
    arm._save_all()
    rows = [json.loads(line) for line
            in open(os.path.join(arm.dir, "levels.jsonl"), encoding="utf-8")
            if line.strip()]
    assert len(rows) == 1 and rows[0]["event"] == "level_boundary"
    state = json.load(open(os.path.join(arm.dir, "RUN_STATE.json"),
                           encoding="utf-8"))
    assert state["levels"]["starts"] == [0, step.step_idx]


def test_a_new_level_starts_the_evidence_gate_where_a_new_run_starts_it(tmp_path):
    """The gate is re-armed at the boundary. Level 2 must be in exactly the
    state a fresh run is in one step after RESET -- otherwise the desk is
    either called with almost no evidence or starved for a whole level."""
    def gate(arm):
        return arm._frames_this_level() - arm._frames_at_last_theorize

    arm, _ = _armed_at_a_boundary(tmp_path)
    assert arm._frames_at_last_theorize == -1          # the never-called value
    assert gate(arm) < MIN_NEW_FRAMES_BETWEEN_THEORIZE   # closed at the boundary

    fresh = _arm(tmp_path / "fresh")
    _feed(fresh, G0, levels_completed=0, action="RESET")
    assert fresh._frames_at_last_theorize == -1
    assert gate(fresh) == gate(arm)

    def steps_until_open(a, colour):
        n = 0
        while gate(a) < MIN_NEW_FRAMES_BETWEEN_THEORIZE:
            _feed(a, [[colour, colour], [colour, colour]], levels_completed=None)
            n += 1
        return n

    assert steps_until_open(arm, 3) == steps_until_open(fresh, 0)


def test_the_evidence_gate_counts_this_levels_frames_not_the_runs(tmp_path):
    """Spec: after a boundary at step 30, a run with 32 total steps has seen 2
    frames of the level it is playing. Counting all 32 would open the gate
    instantly and call the desk on a level it has barely looked at."""
    arm = _arm(tmp_path)
    for i in range(30):                                # steps 0..29
        _feed(arm, G0 if i % 2 else G1, levels_completed=0)
    assert arm._frames_this_level() == 30

    boundary = _feed(arm, [[3, 3], [3, 3]], levels_completed=1)
    assert boundary.step_idx == 30
    assert arm.levels.start == 30
    _feed(arm, [[3, 4], [3, 3]], levels_completed=1)

    assert len(arm.store.steps) == 32
    assert arm._frames_this_level() == 2
    assert len(arm._level_store()) == 2
    assert arm._level_store().steps[0] is arm.store.steps[30]
    # The whole run is still what gets written to trace.jsonl.
    assert arm.summary()["steps"] == 32
    assert arm.summary()["levels"]["starts"] == [0, 30]


def test_a_failed_command_at_a_boundary_does_not_fire_one(tmp_path):
    """A non-200 carries no `levels_completed`, and `_record` must not read the
    absence as a zero -- nor as a level advance."""
    arm = _arm(tmp_path)
    _feed(arm, G0, levels_completed=0)
    _feed(arm, [[3, 3], [3, 3]], levels_completed=1)
    assert arm.levels.level == 2

    arm._record("ACTION1", 500, {"message": "SERVER_ERROR"})
    assert arm.levels.level == 2
    assert arm.levels.completed == 1
    assert len(arm.levels.events) == 1


def test_the_probe_is_told_where_the_world_is_in_this_level(tmp_path):
    """`_roll_forward` replays the manual over the recorded actions to tell
    probe where the world is now. Across a boundary that replays level 1's
    trajectory into level 2's opening board -- the third of the three errors
    `inner/levels.py` names."""
    import inner.loop as loop_mod                      # noqa: PLC0415

    arm = _arm(tmp_path)
    arm.books.write(theory=WORKED_EXAMPLE, playbook="# none\n")
    arm.books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                             "board": [[0] * 3 for _ in range(3)],
                             "objects": [{"name": "Cart", "type": "Cart",
                                          "pos": [2, 1], "color": 6}]})
    assert arm.books.compile_all()["ok"]
    namespace, error = arm.books.load_predictor()
    assert namespace is not None, error

    for _ in range(3):
        _feed(arm, G0, levels_completed=0, action="ACTION2")
    _feed(arm, [[3, 3], [3, 3]], levels_completed=1, action="ACTION2")
    _feed(arm, [[3, 4], [3, 3]], levels_completed=1, action="ACTION1")

    seen = {}
    real_roll_forward = loop_mod._roll_forward

    def capture(ns, store):
        seen["store"] = store
        return real_roll_forward(ns, store)

    loop_mod._roll_forward = capture
    arm.arc.available_actions = [1]
    arm._send = lambda action_id, probe=False, note="": (200, {}, [[[0]]])
    try:
        arm._probe_or_explore(namespace, {})
    finally:
        loop_mod._roll_forward = real_roll_forward

    handed = seen["store"]
    assert list(handed.steps) == list(arm.store.steps[arm.levels.start:])
    assert len(handed) == 2
    assert handed.actions == ["ACTION1", None]


def test_theorize_and_certify_are_shown_this_level_and_not_the_run(tmp_path):
    """`certify.cheap` replays the manual's `step` over every recorded action
    and compares grids; `theorize` computes the problem instance from the cells
    that never varied. Pooled across a boundary the first manufactures a
    `replay_mismatch` -- the only thing that calls the desk -- and the second
    describes neither level."""
    import inner.loop as loop_mod                      # noqa: PLC0415

    arm = _arm(tmp_path, offline=False)
    arm.books.write(theory=WORKED_EXAMPLE, playbook="# none\n")
    for _ in range(4):
        _feed(arm, G0, levels_completed=0, action="ACTION2")
    _feed(arm, [[3, 3], [3, 3]], levels_completed=1, action="ACTION2")
    for _ in range(3):
        _feed(arm, [[3, 4], [3, 3]], levels_completed=1, action="ACTION1")
    arm.register.fire("replay_mismatch", "the manual disagreed", step_idx=6)

    seen = {}

    def fake_theorize(desk, books, store, candidates_path, **kwargs):
        seen["theorize"] = store
        return {"ok": True, "calls": 1}

    def fake_certify(books, store, action_of, compiled):
        seen["certify"] = store
        return {"cheap": {"checks": {}}, "expensive": {"available": False},
                "cheap_green": True}

    real = (loop_mod.theorize.run, loop_mod.certify.run)
    loop_mod.theorize.run, loop_mod.certify.run = fake_theorize, fake_certify
    try:
        arm._theorize_and_certify({})
    finally:
        loop_mod.theorize.run, loop_mod.certify.run = real

    level_steps = list(arm.store.steps[arm.levels.start:])
    assert len(level_steps) == 4
    for beat in ("theorize", "certify"):
        assert list(seen[beat].steps) == level_steps, beat
        assert seen[beat].actions == ["ACTION1", "ACTION1", "ACTION1", None]
        assert seen[beat].background() == 3


# ================================================= 5. retiring keeps the count
def test_retiring_changes_handled_by_and_nothing_else():
    """Constraint 8 audits surprise counts against the ledger. A retire that
    deleted items would break the audit."""
    register = surprise.Register()
    register.fire("replay_mismatch", "a")
    register.fire("replay_mismatch", "b")
    register.fire("search_timeout", "c")
    register.handled("theorize")
    register.fire("probe_refutation", "d")

    before_counts = register.counts()
    before_summary = register.summary()
    assert before_summary["unhandled"] == 1

    out = register.retire_pending("level boundary: level 1 -> 2")
    assert out["retired"] == 1
    assert out["kinds"] == ["probe_refutation"]

    after = register.summary()
    assert register.counts() == before_counts
    assert len(register.counts()) == 7                 # all seven, zeros included
    assert register.counts()["heuristic_miss"] == 0
    assert after["total"] == before_summary["total"] == 4
    assert after["by_kind"] == before_summary["by_kind"]
    assert after["by_family"] == before_summary["by_family"]
    assert after["unhandled"] == 0                     # the only thing that moved
    assert register.items[3].handled_by == \
        "retired: level boundary: level 1 -> 2"
    assert register.items[0].handled_by == "theorize"   # untouched


def test_retiring_nothing_is_a_no_op_that_still_says_so():
    register = surprise.Register()
    register.fire("replay_mismatch", "a")
    register.handled("theorize")
    out = register.retire_pending("level boundary: level 1 -> 2")
    assert out == {"retired": 0, "kinds": [],
                   "reason": "level boundary: level 1 -> 2"}
    assert register.summary()["total"] == 1


def test_constraint_8_still_holds_over_a_run_that_retired(tmp_path):
    """Both implementations: `Register.audit` in-process, and
    `armtools/archive.constraint_8` re-reading `surprises.jsonl` from disk."""
    from armtools.archive import constraint_8          # noqa: PLC0415

    register = surprise.Register()
    register.fire("replay_mismatch", "a", step_idx=1)
    register.handled("theorize")                       # the bootstrap call
    register.fire("replay_mismatch", "b", step_idx=4)
    register.fire("render_mismatch", "c", step_idx=4)
    register.retire_pending("level boundary: level 1 -> 2")

    ledger = [{"event": "model_call", "run_id": "r", "beat": "theorize"}]
    audit = register.audit(ledger, "r")
    assert audit["surprises"] == 3                     # retired items still count
    assert audit["constraint_8_holds"] is True

    run_dir = str(tmp_path)
    register.to_jsonl(os.path.join(run_dir, "surprises.jsonl"))
    rows = [json.loads(line) for line
            in open(os.path.join(run_dir, "surprises.jsonl"), encoding="utf-8")
            if line.strip()]
    assert len(rows) == 3
    assert sum(1 for r in rows
               if (r["handled_by"] or "").startswith("retired:")) == 2

    report = constraint_8(ledger, run_dir)
    assert report["surprises"] == 3
    assert report["calls_not_covered_by_a_surprise"] == 0
    assert report["holds"] is True
    assert report["surprises_by_kind"]["replay_mismatch"] == 2


def test_a_boundary_run_keeps_its_surprise_account_on_disk(tmp_path):
    """The same audit, over an arm that actually crossed a boundary."""
    from armtools.archive import constraint_8          # noqa: PLC0415

    arm, _ = _armed_at_a_boundary(tmp_path)
    arm._save_all()

    ledger = [{"event": "model_call", "run_id": "r", "beat": "theorize"}]
    report = constraint_8(ledger, arm.dir)
    assert report["surprises"] == 2
    assert report["holds"] is True
    assert arm.summary()["surprises"]["total"] == 2
    assert arm.summary()["surprises"]["unhandled"] == 0
