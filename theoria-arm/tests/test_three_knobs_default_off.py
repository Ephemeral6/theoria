"""The three switchable changes, all present at once, all at their defaults.

Three independent changes landed within a day of each other and each shipped
its own proof that its own default moves nothing:

* `goal_protocol` -- `test_goal_state.py::test_off_is_disabled_and_the_other_two_are_not`
* `probe_economy` -- `test_probe_economy.py::test_the_default_is_the_old_behaviour`
* `desk_diet`     -- `test_desk_diet.py::test_full_mode_is_byte_identical_to_today`

Three separate claims are not the claim that matters once they are merged. The
knobs are independent in intent but they are not independent in code: they meet
in one prompt builder and one beat. `theorize.build_prompt` now takes
`goal_rider`, `diet` and `allow_patch` together, and `theorize.run` threads all
of them through a single call site that each change rewrote separately -- the
`goal_protocol` side added the rider to a prompt built once before the repair
loop, and the `desk_diet` side moved prompt construction *into* the loop so the
patch contract could be withdrawn per attempt. Whichever way that conflict is
resolved, "each is off by itself" does not entail "all three off together is
the arm master had", and the way it fails is silent: a dropped `goal_rider=`
keyword still compiles, still passes every test above, and quietly voids any
leg that turns the protocol on.

So this file asserts the conjunction, and it asserts it by comparison rather
than against a golden string -- a frozen expected prompt would only prove that
two copies of the same mistake agree.

Offline: no key, no network, no model call, no quota. The desk is a scripted
double that returns text from a list.
"""

import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import deskdiet, goal as goal_beat, theorize   # noqa: E402
from inner.books import Books                             # noqa: E402
from inner.goal import GoalState                          # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE             # noqa: E402
from inner.loop import DEFAULT_GOAL_PROTOCOL, TheoriaArm  # noqa: E402
from world.frames import FrameStore, Step                 # noqa: E402

#: The exact dict `theorize.run` builds when a reply carries no THEORY block.
#: Repeated here so the repair-prompt comparison below is against what the beat
#: is *supposed* to send, not against whatever it happens to send.
NO_THEORY_ERRORS = {"reply": "the reply carried no === THEORY === "
                             "block; emit all three blocks"}


# ---------------------------------------------------------------- fixtures
def _grid(n, fill=0, mark=None):
    g = [[fill] * n for _ in range(n)]
    if mark:
        r, c = mark
        g[r][c] = 6
    return g


def _store(n_steps=8, size=6):
    store = FrameStore()
    store.add(Step(0, "RESET", [_grid(size, mark=(0, 0))], state="NOT_FINISHED"))
    for i in range(1, n_steps):
        store.add(Step(i, "ACTION%d" % (1 + i % 4),
                       [_grid(size, mark=(i % size, (i * 2) % size))],
                       state="NOT_FINISHED"))
    return store


def _engines():
    return {"window": {"box": [0, 5, 0, 5]},
            "mdl_segmenter": {"objects": [{"id": "obj0", "color": 6,
                                           "cells": [[0, 0]]}]},
            "cegis_miner": {"rules": [{"id": "r0", "guard": "free"}]},
            "zero_space": {"invariants": ["count(obj0) = 1"]}}


def _books(tmp_path, theory=None):
    books = Books(str(tmp_path))
    books.write(theory=theory if theory is not None else "",
                playbook="# nothing defensible yet\n")
    return books


def _candidates(tmp_path):
    path = os.path.join(str(tmp_path), "candidates.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"kind": "object", "status": "candidate"}\n' * 3)
    return path


def _reply(theory, playbook="# none\n", log="[]"):
    return ("=== THEORY ===\n```\n%s\n```\n\n=== PLAYBOOK ===\n```\n%s\n```\n\n"
            "=== LOG ===\n```json\n%s\n```\n" % (theory, playbook, log))


class ScriptedDesk:
    """Returns canned replies and records the prompts it was sent.

    Refuses to be called more often than it was scripted for: a desk that
    returns its last reply forever cannot tell "the loop repaired once" from
    "the loop spun until the budget ran out".
    """

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def call(self, prompt, *, beat, step_idx=None, label=None):
        assert beat == "theorize"
        assert self.replies, "the desk was called more times than it was scripted"
        self.prompts.append(prompt)
        return self.replies.pop(0)


def _rider():
    """A real rider, not a marker string -- the thing the loop actually parks."""
    state = GoalState("propose")
    state.turns_without_goal = 7
    state.actions_without_goal = 21
    return goal_beat.prompt_rider(state, {"reason": "no goal"}, 12)


# ================================================== 1. the joint default
def test_all_three_defaults_are_the_prompt_master_sent(tmp_path):
    """Every spelling of "all three off" must give one string.

    The reference is `build_prompt` called with no optional keyword at all,
    which is exactly how `inner/loop.py` called it before any of the three
    changes existed. Compared across the option matrix, because an equality
    that only covered the cold-start prompt would miss a divergence in the
    manual, surprise or compiler-refusal branches -- and the patch contract in
    particular is only ever appended when a manual already exists.
    """
    store, engines = _store(), _engines()
    cands = _candidates(tmp_path)

    class _S:
        kind, family, book = "replay_mismatch", "mechanism", "theory"
        detail, payload = "t4 diverged", {"t": 4}

    for theory in ("", WORKED_EXAMPLE):
        books = _books(tmp_path, theory)
        for surprises in ([], [_S()]):
            for errors in (None, {"clause": "rules: line 3"}):
                today = theorize.build_prompt(store, engines, books, cands,
                                              surprises, errors, {"cheap": {}})
                for spelling in (
                        # each knob named at its default, one at a time ...
                        dict(goal_rider=None),
                        dict(diet=deskdiet.DeskDiet()),
                        dict(diet=deskdiet.full()),
                        dict(allow_patch=True),
                        # ... and all of them together, which is the claim
                        dict(goal_rider=None, diet=deskdiet.full(),
                             allow_patch=True),
                        dict(goal_rider=None,
                             diet=deskdiet.DeskDiet.parse(None),
                             allow_patch=True)):
                    assert today == theorize.build_prompt(
                        store, engines, books, cands, surprises, errors,
                        {"cheap": {}}, **spelling), spelling
                assert "THEORY-PATCH" not in today
                assert "The manual has no goal section" not in today


def test_the_beat_at_its_defaults_sends_exactly_that_prompt(tmp_path):
    """The beat, not just the builder.

    `theorize.run` is where the three changes actually collide: the rider is
    taken once per beat, the diet decides per attempt whether the patch
    contract rides along, and both feed one `build_prompt` call. With no knobs
    passed, the string that reaches the desk must be the one the builder
    produces with no knobs at all.
    """
    store, engines, cands = _store(), _engines(), _candidates(tmp_path)
    books = _books(tmp_path, WORKED_EXAMPLE)
    # Computed BEFORE the beat runs: the beat rewrites the manual, and a
    # reference built afterwards would be quoting the reply back at itself.
    expected = theorize.build_prompt(store, engines, books, cands, [], None,
                                     None)

    desk = ScriptedDesk([_reply(WORKED_EXAMPLE)])
    result = theorize.run(desk, books, store, cands, engines=engines)

    assert desk.prompts == [expected]
    assert result["calls"] == 1
    assert result["goal_rider"] is False
    assert result["diet"] == {"mode": "full", "evidence_delta": False,
                              "theory_patch": False}


def test_the_repair_attempt_at_its_defaults_is_todays_repair_prompt(tmp_path):
    """The second call, which is where the merge could quietly lose a knob.

    Both changes rewrote the repair path: one added `goal_rider=` to the
    rebuild after a bad reply, the other deleted that rebuild and moved prompt
    construction to the top of the loop. A resolution that keeps the deletion
    and forgets the keyword sends attempt 1 with the rider and attempt 2
    without it, and nothing else in the suite notices.
    """
    store, engines, cands = _store(), _engines(), _candidates(tmp_path)
    books = _books(tmp_path, WORKED_EXAMPLE)
    first = theorize.build_prompt(store, engines, books, cands, [], None, None)
    repair = theorize.build_prompt(store, engines, books, cands, [],
                                   NO_THEORY_ERRORS, None)
    assert first != repair                     # the fixture proves the point

    desk = ScriptedDesk(["=== LOG ===\n```json\n[]\n```\n",
                         _reply(WORKED_EXAMPLE)])
    result = theorize.run(desk, books, store, cands, engines=engines)

    assert result["calls"] == 2
    assert desk.prompts == [first, repair]
    assert "THEORY-PATCH" not in repair


# ============================================ 2. still independent, still wired
def test_a_rider_survives_the_diets_call_site(tmp_path):
    """Turning the diet on must not drop the goal ask, and vice versa.

    This is the union the merge had to make: the diet's `build_prompt` call is
    the only one left, so it is the only place the rider can be threaded
    through. On the branch that call had no `goal_rider` argument at all.
    """
    store, engines, cands = _store(), _engines(), _candidates(tmp_path)
    rider = _rider()

    for diet, wants_patch in ((deskdiet.full(), False),
                              (deskdiet.DeskDiet.parse("patch"), True),
                              (deskdiet.DeskDiet.parse("diet"), True)):
        books = _books(tmp_path, WORKED_EXAMPLE)
        desk = ScriptedDesk([_reply(WORKED_EXAMPLE)])
        result = theorize.run(desk, books, store, cands, engines=engines,
                              goal_rider=rider, diet=diet)
        sent = desk.prompts[0]
        assert rider in sent, diet.name
        assert ("THEORY-PATCH" in sent) is wants_patch, diet.name
        assert result["goal_rider"] is True
        assert result["diet"]["mode"] == diet.name


def test_each_knob_adds_only_its_own_section(tmp_path):
    """Off-by-default, measured as a difference rather than asserted.

    The rider and the patch contract are additive and disjoint: the prompt with
    both on is the prompt with neither on plus exactly those two blocks, so no
    knob can be silently rewriting a section that belongs to another.
    """
    store, engines, cands = _store(), _engines(), _candidates(tmp_path)
    books = _books(tmp_path, WORKED_EXAMPLE)
    rider = _rider()
    patch = deskdiet.DeskDiet.parse("patch")

    plain = theorize.build_prompt(store, engines, books, cands, [], None, None)
    with_rider = theorize.build_prompt(store, engines, books, cands, [], None,
                                       None, goal_rider=rider)
    with_patch = theorize.build_prompt(store, engines, books, cands, [], None,
                                       None, diet=patch)
    with_both = theorize.build_prompt(store, engines, books, cands, [], None,
                                      None, goal_rider=rider, diet=patch)

    assert len(with_rider) == len(plain) + len(rider) + 2      # "\n" + rider
    assert len(with_patch) == len(plain) + len(deskdiet.PATCH_CONTRACT) + 2
    assert (len(with_both) == len(plain) + len(rider)
            + len(deskdiet.PATCH_CONTRACT) + 4)
    # and the rider still lands before the output contract, not after the
    # patch contract that was appended later.
    assert with_both.index(rider) < with_both.index(deskdiet.PATCH_CONTRACT.strip())


def test_the_final_repair_attempt_withdraws_the_patch_but_keeps_the_rider(tmp_path):
    """The beat's own veto, checked against the other knob.

    `allow_patch` is turned off on the last attempt so a desk that cannot
    produce a usable patch is asked for the whole book. That veto belongs to
    the diet alone; the goal ask is unanswered either way and must still be
    carried.
    """
    store, engines, cands = _store(), _engines(), _candidates(tmp_path)
    books = _books(tmp_path, WORKED_EXAMPLE)
    rider = _rider()
    desk = ScriptedDesk([
        # a patch the applier must refuse -- the anchor is not in the manual
        '=== THEORY-PATCH ===\n```json\n[{"op": "replace", "find": "nowhere", '
        '"with": "x"}]\n```\n\n=== LOG ===\n```json\n[]\n```\n',
        '=== THEORY-PATCH ===\n```json\n[{"op": "replace", "find": "nowhere", '
        '"with": "x"}]\n```\n\n=== LOG ===\n```json\n[]\n```\n',
        _reply(WORKED_EXAMPLE)])

    result = theorize.run(desk, books, store, cands, engines=engines,
                          goal_rider=rider,
                          diet=deskdiet.DeskDiet.parse("patch"))

    assert result["calls"] == 3
    assert [("THEORY-PATCH" in p) for p in desk.prompts] == [True, True, False]
    assert all(rider in p for p in desk.prompts)
    assert [e["patch_contract"] for e in result["prompt_census"]] == [
        True, True, False]


def test_the_census_bills_the_rider_to_the_rider(tmp_path):
    """The instrument has to be able to see the other change's section.

    `armtools/prompt_census.py` is the measurement `desk_diet` is judged by,
    and it cuts a prompt at anchors, giving every unclaimed byte to the section
    that opened last. It shipped knowing nothing about the goal rider, because
    on its own branch the rider did not exist -- so a merged arm running
    `goal_protocol=propose` would have billed ~2 kB of ask to
    `engine_proposals` and read it as evidence growth that never happened.
    Silent, and in exactly the direction that would flatter the diet.
    """
    store, engines, cands = _store(), _engines(), _candidates(tmp_path)
    rider = _rider()

    def _sections(**kwargs):
        books = _books(tmp_path, WORKED_EXAMPLE)
        desk = ScriptedDesk([_reply(WORKED_EXAMPLE)])
        result = theorize.run(desk, books, store, cands, engines=engines,
                              **kwargs)
        entry = result["prompt_census"][0]
        assert "census_error" not in entry, entry.get("census_error")
        assert sum(entry["sections"].values()) == entry["chars"]
        return entry

    without = _sections()
    with_rider = _sections(goal_rider=rider)

    assert "goal_rider" not in without["sections"]
    assert with_rider["chars"] - without["chars"] == len(rider) + 2
    # Nearly all of that lands on the rider's own row. Not exactly all: the
    # anchors carry a leading newline and the blank lines between blocks are
    # claimed by whichever section opened last, so the boundaries either side
    # move by a character or two. A handful of characters is a boundary; two
    # kilobytes would be the misattribution this row exists to prevent.
    assert len(rider) <= with_rider["sections"]["goal_rider"] <= len(rider) + 4

    # The direction that matters. `evidence` is the bucket the diet is trying
    # to shrink, so a rider billed to it would read as the diet failing -- or,
    # on a full leg, as the world growing. It must not move at all.
    assert with_rider["by_kind"]["evidence"] == without["by_kind"]["evidence"]
    assert with_rider["by_kind"]["boilerplate"] == without["by_kind"]["boilerplate"]
    assert (with_rider["by_kind"]["feedback"]
            - without["by_kind"].get("feedback", 0)) >= len(rider)


# ======================================================== 3. the constructor
def test_an_arm_built_with_no_knobs_has_all_three_off(tmp_path, monkeypatch):
    """One arm, three switches, every one of them at the pre-merge setting.

    Constructed exactly as `harness/run.py` constructed it before any of the
    three existed -- no knob keyword at all -- because the defect this guards
    against is a default that moved, and a test that passes the defaults in
    explicitly cannot see that.
    """
    monkeypatch.delenv("THEORIA_PROBE_ECONOMY", raising=False)
    monkeypatch.delenv("THEORIA_FRONTIER", raising=False)
    run = types.SimpleNamespace(dir=str(tmp_path), run=None, run_id="r-pytest")
    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                     game_id="g50t-5849a774", offline=True)

    # A fourth knob landed after this file was named (R2's `--frontier`), and
    # the conjunction this file exists to assert is over however many there
    # are, not over three. Its own default-off proof is
    # `test_frontier_generation.py`; this line is the one that fails if a
    # future merge makes it the default while every single-knob test stays
    # green.
    assert arm.frontier.mode == "ablation"

    assert DEFAULT_GOAL_PROTOCOL == "off"
    assert arm.goal.protocol == "off"
    assert arm.goal.enabled is False

    assert arm.probe_economy.enabled is False

    assert arm.desk_diet.name == "full"
    assert arm.desk_diet.evidence_delta is False
    assert arm.desk_diet.theory_patch is False
    assert arm.desk_diet.state_is_fresh()


def test_the_three_knobs_can_be_set_independently(tmp_path, monkeypatch):
    """Independently switchable, which is what "union" was supposed to mean.

    Each knob is turned on alone and the other two are asserted still off, so
    a resolution that accidentally coupled two of them -- one flag reading
    another's config, or one constructor argument shadowing another -- fails
    here rather than in a live leg that measured the wrong arm.
    """
    monkeypatch.delenv("THEORIA_PROBE_ECONOMY", raising=False)
    from inner.probe import ProbeEconomyConfig              # noqa: PLC0415

    def _arm(**kwargs):
        run = types.SimpleNamespace(dir=str(tmp_path), run=None,
                                    run_id="r-pytest")
        return TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                          game_id="g50t-5849a774", offline=True, **kwargs)

    only_goal = _arm(goal_protocol="propose")
    assert only_goal.goal.protocol == "propose"
    assert only_goal.probe_economy.enabled is False
    assert only_goal.desk_diet.name == "full"

    only_probe = _arm(probe_economy=ProbeEconomyConfig(enabled=True))
    assert only_probe.goal.protocol == "off"
    assert only_probe.probe_economy.enabled is True
    assert only_probe.desk_diet.name == "full"

    only_diet = _arm(desk_diet="diet")
    assert only_diet.goal.protocol == "off"
    assert only_diet.probe_economy.enabled is False
    assert only_diet.desk_diet.name == "diet"

    all_three = _arm(goal_protocol="record",
                     probe_economy=ProbeEconomyConfig(enabled=True),
                     desk_diet="patch")
    assert all_three.goal.protocol == "record"
    assert all_three.probe_economy.enabled is True
    assert all_three.desk_diet.name == "patch"
