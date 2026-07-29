"""Properties of the sealed drill.

The drill's own gates check that a run came out right.  These check the things a
green run cannot: that the guard would refuse if it were fed something it must
refuse, that a *wrong* certificate is rejected, that the checker declines worlds
its premises do not cover, and that the marking ladder has not drifted away from
the frozen one it claims to mirror.

A rehearsal whose only negative control is "it passed" has no negative control.
"""

import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import drill_certificates as certs
from exam import guard
from exam.drill_wrapper import WorldSession, replay, solve
from exam.tools import sealed_drill as drill
from proxy.variants import Variant
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("drill")
    return drill.run(str(out)), str(out)


# -- the guardrail ---------------------------------------------------------

def test_the_guard_fires_on_every_sealed_id_not_one(run):
    """The sweep must be total, not a sample.

    An earlier version probed one sealed id of twenty-one. The adversarial pass
    built a guard that refused exactly that one and accepted the other twenty
    plus all four dev games, and this report still said `fired: True`.
    """
    payload, _ = run
    checks = {c["check"]: c for c in payload["guard"]["checks"]}
    counts = payload["guard"]["counts"]
    n_sealed = payload["guard"]["n_sealed"]
    assert n_sealed == 21
    for label in ("sealed_full_ids", "sealed_short_ids"):
        assert checks[label]["passed"], checks[label]
        assert counts[label]["probed"] == n_sealed, counts[label]
    assert checks["dev_pile_ids"]["passed"], checks["dev_pile_ids"]
    assert counts["dev_pile_ids"]["probed"] == 4
    assert counts["synthetic_control"]["probed"] >= 20


def test_the_guard_still_accepts_a_synthetic_world(run):
    """A guard that refuses everything passes every refusal test and is useless."""
    payload, _ = run
    checks = {c["check"]: c for c in payload["guard"]["checks"]}
    assert checks["synthetic_control"]["passed"], checks["synthetic_control"]


def test_no_sealed_id_is_written_into_the_run(run):
    """The drill reads a sealed id at run time; it must not leave one behind.

    An artefact that names a sealed game is the leak the guard exists to
    prevent, arriving by the door marked "test".
    """
    payload, out = run
    sealed = set(guard.load_piles().sealed_pile)
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    for name in sorted(sealed):
        assert name not in blob, "%s reaches the run record" % name
    # Short stems are checked as whole tokens. Several of them (`dc22`, `ka59`,
    # `re86`, ...) are valid hex, so a plain substring search hits inside every
    # sha256 in the file and the test would fail on noise for ever.
    tokens = set(re.findall(r"[0-9a-z][0-9a-z-]*", blob.lower()))
    for stem in sorted(s.split("-", 1)[0] for s in sealed):
        assert stem not in tokens, "%s reaches the run record" % stem


# -- the certificates ------------------------------------------------------

def test_every_offered_certificate_checks_out(run):
    payload, _ = run
    for finding in payload["findings"]:
        if finding["certificate_offered"]:
            assert finding["certificate_check"]["ok"], finding


def test_construction_agrees_with_the_exhaustive_oracle(run):
    """The one thing Phase 4 will never be able to do, done here."""
    payload, _ = run
    disagreements = [f for f in payload["findings"]
                     if not f["construction_agrees_with_oracle"]]
    assert not disagreements, disagreements


def test_an_invariant_that_is_not_invariant_is_refused():
    """Forbidding UP leaves DOWN available, so the row is not monotone."""
    spec = BY_ID["t1-walk-maze"]
    out = certs.check(spec, [{"op": "forbid_action", "action": "UP"}],
                      {"kind": "invariant", "invariant": "agent_row",
                       "initial_value": 1, "goal_value": 5})
    assert not out["ok"]
    assert "not monotone" in out["why"]


def test_a_cut_that_does_not_cut_is_refused():
    """(4,1) alone leaves the crossing at (4,7) open."""
    spec = BY_ID["t1-walk-maze"]
    out = certs.check(spec, [{"op": "observation_loss", "cells": [[4, 1]],
                              "value": 6}],
                      {"kind": "cut_set", "cells": [[4, 1]]})
    assert not out["ok"]
    assert "not a cut" in out["why"]


def test_a_budget_that_does_not_bite_is_refused():
    spec = BY_ID["t1-walk-maze"]
    out = certs.check(spec, [{"op": "step_limit", "limit": 10}],
                      {"kind": "counting", "bound": 10, "limit": 10})
    assert not out["ok"]
    assert "proves nothing" in out["why"]


def test_a_wrong_manhattan_bound_is_refused():
    spec = BY_ID["t1-walk-maze"]
    out = certs.check(spec, [{"op": "step_limit", "limit": 9}],
                      {"kind": "counting", "bound": 99, "limit": 9})
    assert not out["ok"]
    assert "Manhattan distance" in out["why"]


def test_the_grammar_is_closed():
    spec = BY_ID["t1-walk-maze"]
    ops = [{"op": "forbid_action", "action": "DOWN"}]
    extra = certs.check(spec, ops, {"kind": "invariant", "invariant": "agent_row",
                                    "initial_value": 1, "goal_value": 5,
                                    "confidence": "high"})
    assert not extra["ok"] and "unexpected" in extra["why"]
    missing = certs.check(spec, ops, {"kind": "invariant", "invariant": "agent_row",
                                      "initial_value": 1})
    assert not missing["ok"] and "missing" in missing["why"]
    unknown = certs.check(spec, ops, {"kind": "vibes"})
    assert not unknown["ok"] and "unknown certificate kind" in unknown["why"]


def test_a_teleporting_world_is_refused_not_assumed():
    """The premises are checked against the world, not hoped for.

    `t2-portal-paired` carries portals, so "one cell per command" is false and
    both the axis invariant and the Manhattan bound are unsound on it. The
    checker must decline rather than return a confident wrong answer.
    """
    spec = BY_ID["t2-portal-paired"]
    out = certs.check(spec, [{"op": "forbid_action", "action": "DOWN"}],
                      {"kind": "invariant", "invariant": "agent_row",
                       "initial_value": 1, "goal_value": 5})
    assert not out["ok"]
    assert "portal" in out["why"] and "Refused rather than assumed" in out["why"]

    cut = certs.check(spec, [], {"kind": "cut_set", "cells": [[3, 1]]})
    assert not cut["ok"] and "walks the board" in cut["why"]


# -- the frozen operator order --------------------------------------------

def test_forbid_is_consulted_before_remap():
    """`proxy/variants.py:before` forbids first, so a forbidden command is never
    remapped and a command remapped *onto* a forbidden action still forwards.

    Getting this backwards silently changes which invariants hold, so it is
    pinned rather than trusted.
    """
    alphabet = certs.effective_actions([
        {"op": "forbid_action", "action": "DOWN"},
        {"op": "remap_action", "from": "DOWN", "to": "RIGHT"},
        {"op": "remap_action", "from": "LEFT", "to": "DOWN"},
    ])
    assert alphabet["DOWN"] is None, "a forbidden command was remapped instead"
    assert alphabet["LEFT"] == "DOWN", "a remap onto a forbidden action was refused"


# -- the oracle, against an artefact it did not produce --------------------

@pytest.mark.parametrize("world_id", sorted(
    w["world_id"] for w in json.load(
        open(os.path.join(REPO, "worldgen", "out", "worlds", "INDEX.json"),
             encoding="utf-8"))["worlds"]))
def test_the_oracle_reproduces_worldgens_own_ground_truth(world_id):
    """Cross-check: the drill's composed search, with no variant, must agree
    with `worldgen/out/worlds/INDEX.json` on solvability and optimal length.

    The index was produced by a different searcher in a different package. Two
    independent implementations agreeing on twenty worlds is worth more than
    either one's self-report.
    """
    index = json.load(open(os.path.join(REPO, "worldgen", "out", "worlds",
                                        "INDEX.json"), encoding="utf-8"))
    row = next(w for w in index["worlds"] if w["world_id"] == world_id)
    result = solve(GridWorld(BY_ID[world_id]), None)
    assert result["solvable"] == row["solvable"], world_id
    if row["solvable"]:
        assert len(result["witness"]) == row["optimal_length"], world_id


def test_reset_is_not_in_the_alphabet():
    """RESET zeroes the counters, so admitting it would defeat every step_limit.

    Stated in the module docstring; pinned here because a future "let the arm
    reset" change would make every budget variant silently solvable.
    """
    world = GridWorld(BY_ID["t1-walk-maze"])
    variant = Variant({"variant_id": "t", "base_game": "t1-walk-maze",
                       "claim": "unsolvable",
                       "justification": "x" * 60,
                       "operators": [{"op": "step_limit", "limit": 3}]})
    assert solve(world, variant)["solvable"] is False
    # RESET does refill the budget -- but it also puts the agent back on the
    # start, so a goal ten cells away is no closer after three commands than it
    # was after none. The budget is escapable; the world is not.
    escaped = replay(world, variant,
                     ["DOWN", "DOWN", "DOWN", "RESET",
                      "DOWN", "DOWN", "DOWN", "RESET",
                      "DOWN", "DOWN", "DOWN"])
    assert escaped["win"] is False
    session = WorldSession(world)
    session.command("DOWN")
    assert session.command("RESET")["state"] == "NOT_FINISHED"
    assert session.state == world.initial()


# -- the marking ladder, pinned to the frozen one --------------------------

def test_the_reason_vocabulary_matches_the_frozen_rubric():
    """Every reason this drill pays must exist in `rubrics_verdict.py`.

    The drill deliberately reimplements the ladder rather than registering a
    rubric (see the module docstring). That is only safe if the two cannot
    drift apart unnoticed, so the vocabulary is compared against the frozen
    source directly.
    """
    frozen = open(os.path.join(REPO, "exam", "grading", "rubrics_verdict.py"),
                  encoding="utf-8").read()
    for reason in ("certificate", "invalid_certificate", "none", "witness",
                   "invalid_witness"):
        assert '"%s"' % reason in frozen, reason
    ours = open(os.path.join(REPO, "exam", "tools", "sealed_drill.py"),
                encoding="utf-8").read()
    assert "search_exhaustion" not in ours, (
        "the drill offers no search-credit path on purpose -- every item here "
        "is small enough that exhaustion is cheap, so paying for it would "
        "measure nothing. If that changes, change this test deliberately.")


def test_an_arm_with_every_claim_right_and_no_reason_scores_exactly_half(run):
    payload, _ = run
    assert payload["calibration"]["claim_only"]["fraction"] == pytest.approx(0.5)


def test_the_two_rates_are_separate_numbers(run):
    """The bluffer and the contrarian sit at opposite corners.

    One accuracy figure cannot distinguish them; two can. This is the same
    property `exam/grading/selftest.py:453` injects a fault against on the real
    marker.
    """
    payload, _ = run
    bluffer = payload["calibration"]["bluffer"]["confusion"]["overall"]
    contrarian = payload["calibration"]["contrarian"]["confusion"]["overall"]
    assert (bluffer["sensitivity"], bluffer["specificity"]) == (1.0, 0.0)
    assert (contrarian["sensitivity"], contrarian["specificity"]) == (0.0, 1.0)


def test_sensitivity_and_specificity_are_reported_per_class(run):
    payload, _ = run
    by_class = payload["calibration"]["oracle"]["confusion"]["by_class"]
    assert set(by_class) == {"small_unsolvable", "solvable_hard"}
    for cell in by_class.values():
        assert "sensitivity" in cell and "specificity" in cell
        assert "coverage_positive" in cell


def test_an_empty_denominator_is_none_and_never_zero(run):
    """`solvable_hard` holds no positives, so sensitivity is undefined there."""
    payload, _ = run
    cell = payload["calibration"]["oracle"]["confusion"]["by_class"]["solvable_hard"]
    assert cell["sensitivity"] is None
    assert "sensitivity_undefined_because" in cell


# -- truth isolation -------------------------------------------------------

def test_the_sheet_carries_no_answer(run):
    payload, out = run
    assert payload["leakage"]["failures"] == []
    sheet = json.load(open(os.path.join(out, "sheet.json"), encoding="utf-8"))
    blob = json.dumps(sheet, sort_keys=True, ensure_ascii=False)
    # The words `certificate` and `witness` appear in the question by
    # necessity -- the examinee is asked for one. What must not appear is any
    # answer *content*, which is what `leak_probes` carries and what the
    # assertion above already covers. These two keys are structural: they are
    # truth-side field names and their presence would mean the key doc leaked.
    for word in ("oracle_solvable", "\"truth\""):
        assert word not in blob, word


def test_the_key_and_the_sheet_are_different_files(run):
    payload, out = run
    assert os.path.exists(os.path.join(out, "sheet.json"))
    assert os.path.exists(os.path.join(out, "truth.json"))
    key = json.load(open(os.path.join(out, "truth.json"), encoding="utf-8"))
    assert all("truth" in item for item in key["items"])


# -- provenance ------------------------------------------------------------

def test_every_written_artefact_is_lf(run):
    """`exam/.gitattributes` pins LF. A CRLF artefact hashes differently on the
    machine that clones it, which is the only machine the digest is for."""
    _, out = run
    for root, _dirs, files in os.walk(out):
        for name in files:
            data = open(os.path.join(root, name), "rb").read()
            assert b"\r\n" not in data, os.path.join(root, name)


def test_the_run_is_byte_reproducible(tmp_path):
    """Two runs, fresh interpreters, different hash seeds, identical bytes."""
    digests = []
    for salt in ("7", "99"):
        out = tmp_path / ("run" + salt)
        env = dict(os.environ, PYTHONHASHSEED=salt)
        code = subprocess.run(
            [sys.executable, "-m", "exam.tools.sealed_drill", "--out", str(out)],
            cwd=REPO, env=env, capture_output=True, text=True)
        assert code.returncode == 0, code.stdout + code.stderr
        blob = {}
        for root, _dirs, files in os.walk(out):
            for name in sorted(files):
                path = os.path.join(root, name)
                blob[os.path.relpath(path, out)] = open(path, "rb").read()
        digests.append(blob)
    assert digests[0].keys() == digests[1].keys()
    differing = [k for k in digests[0] if digests[0][k] != digests[1][k]]
    assert not differing, differing


def test_the_drill_declares_the_class_it_cannot_rehearse(run):
    """Class (ii) of Theoria.md:259 is absent, and must be said so out loud.

    worldgen's largest world has 2654 reachable states, so nothing in the
    catalogue can stand in for a space exhaustive search cannot reach. A
    rehearsal that quietly omitted it would read as covering all three.
    """
    payload, _ = run
    assert payload["coverage"]["classes_absent"] == ["large_unsolvable"]
    assert payload["coverage"]["classes_absent_because"]


def test_all_five_frozen_operators_are_exercised(run):
    """`exam/tests/test_verdict.py:289` makes the same demand of the a2 paper,
    and for the same reason: an operator never exercised in the rehearsal is one
    whose first use is on a sealed game."""
    from proxy.variants import LEGAL_OPERATORS
    payload, _ = run
    used = set(payload["coverage"]["operators_exercised"])
    assert used == set(LEGAL_OPERATORS), sorted(set(LEGAL_OPERATORS) - used)


# -- the gate itself, falsified in both directions -------------------------

def test_a_permissive_guard_makes_the_drill_red(monkeypatch):
    """A guard that accepts a sealed id must fail the drill's own gate.

    Watching a gate pass tells you nothing about whether it can fail. This is
    the lesson from V7: a guard was added, and the negative control found it
    was being skipped rather than passed.
    """
    monkeypatch.setattr(guard, "assert_synthetic_world", lambda wid, **kw: wid)
    evidence = drill.fire_the_guard()
    assert evidence["fired"] is False
    failed = {c["check"] for c in evidence["checks"] if not c["passed"]}
    assert failed == {"sealed_full_ids", "sealed_short_ids", "dev_pile_ids"}


def test_a_paranoid_guard_makes_the_drill_red_too(monkeypatch):
    """And a guard that refuses *everything* must fail it as well.

    This is the direction a refusal-only test cannot see: refusing the sealed
    id is necessary and nowhere near sufficient.
    """
    def refuse(wid, **kw):
        raise guard.SealedPileError("no")
    monkeypatch.setattr(guard, "assert_synthetic_world", refuse)
    evidence = drill.fire_the_guard()
    assert evidence["fired"] is False
    failed = {c["check"] for c in evidence["checks"] if not c["passed"]}
    # dev ids are expected to raise UnknownGameError specifically, so a guard
    # that raises SealedPileError at everything fails that sweep too.
    assert "synthetic_control" in failed


def test_a_cut_set_is_refused_on_a_cascading_world():
    """Gravity is refused for `cut_set`, and not for the obvious reason.

    An `observation_loss` fires on a rendered frame, and only the last one
    (`proxy/variants.py:_cells_hit`). `GridWorld.step` settles to a fixpoint
    before rendering. So an agent that gravity carries *through* a lethal cell
    is never observed on it, the loss never fires, and a cut on the board is not
    a cut in the state space. The checker must decline.
    """
    spec = BY_ID["t2-gravity-push"]
    assert "gravity" in spec.families
    out = certs.check(spec, [{"op": "observation_loss", "cells": [[1, 1]],
                              "value": 6}],
                      {"kind": "cut_set", "cells": [[1, 1]]})
    assert not out["ok"]
    assert "observed" in out["why"] and "gravity" in out["why"]


def test_an_undeclared_portal_does_not_evade_the_side_condition():
    """`families` is a declaration; the bound mechanisms are the fact.

    A spec can carry portal entities without naming `portal` in `families`. The
    shipped catalogue never does -- but a side condition that can be evaded by
    omitting a word is not a side condition, so the checker reads the mechanisms
    the world actually binds.
    """
    import dataclasses
    from worldgen.core.world import GridWorld
    base = BY_ID["t2-portal-paired"]
    liar = dataclasses.replace(base, families=())          # entities kept, family dropped
    assert "portal" not in liar.families
    assert "portal" in certs.effective_families(liar)
    assert "portal" in {m.name for m in GridWorld(liar, check=False).mechanisms}
    out = certs.check(liar, [{"op": "forbid_action", "action": "DOWN"}],
                      {"kind": "invariant", "invariant": "agent_row",
                       "initial_value": 1, "goal_value": 5})
    assert not out["ok"] and "portal" in out["why"]
    cut = certs.check(liar, [], {"kind": "cut_set", "cells": [[3, 1]]})
    assert not cut["ok"] and "portal" in cut["why"]


def test_a_guard_broken_for_all_but_one_sealed_id_is_caught(monkeypatch):
    """The exact attack that defeated the n=1 version.

    A guard that refuses only the first sealed id -- the one the old code
    happened to probe -- and waves through the other twenty and all four dev
    games. It must not be able to report `fired: True`.
    """
    piles = guard.load_piles()
    only = piles.sealed_pile[0]

    def leaky(world_id, **kw):
        if world_id in (only, only.split("-", 1)[0]):
            raise guard.SealedPileError("no")
        return world_id

    monkeypatch.setattr(guard, "assert_synthetic_world", leaky)
    evidence = drill.fire_the_guard()
    assert evidence["fired"] is False
    failed = {c["check"] for c in evidence["checks"] if not c["passed"]}
    assert {"sealed_full_ids", "sealed_short_ids", "dev_pile_ids"} <= failed


def test_a_doctored_cut_is_a_red_report_not_a_traceback(monkeypatch):
    """`load_piles` verifies its own digest. When it refuses, the drill must
    still produce a verdict rather than dying before it writes one."""
    def refuse(*a, **kw):
        raise guard.CutIntegrityError("piles.json does not hash to its own field")
    monkeypatch.setattr(guard, "load_piles", refuse)
    evidence = drill.fire_the_guard()
    assert evidence["fired"] is False
    assert evidence["checks"][0]["check"] == "cut_integrity"
    assert not evidence["checks"][0]["passed"]


def test_a_hostile_submission_is_scored_not_raised(run):
    """One malformed answer must not abort everybody else's marking."""
    payload, out = run
    import exam.tools.sealed_drill as sd
    items, _ = sd.build_items(os.path.join(out, "hostile_specs"), out)
    hostile = [{"claim": "unsolvable", "certificate": "just trust me"},
               {"claim": "unsolvable", "certificate": ["nope"]},
               {"claim": "solvable", "witness": "DOWN"},
               {"claim": "solvable", "witness": ["BANANA"]},
               {"claim": "solvable", "witness": ["DOWN"] * 200000}]
    for item in items:
        for answer in hostile:
            score = sd.grade(answer, item, out)          # must not raise
            assert score.awarded <= item.points


def test_a_bogus_cut_set_cannot_buy_the_reason_half(run):
    """The blocking finding, pinned.

    A `cut_set` naming cells the variant never made lethal is a claim about a
    different world. Before the fix it was accepted, and it bought full marks on
    an item whose reason half the drill declares unpayable.
    """
    payload, out = run
    import exam.tools.sealed_drill as sd
    items, _ = sd.build_items(os.path.join(out, "bogus_specs"), out)
    target = next(i for i in items
                  if i.truth["spec"]["variant_id"].endswith("win-tighten-scoreless"))
    score = sd.grade({"claim": "unsolvable",
                      "certificate": {"kind": "cut_set", "cells": [[4, 1], [4, 7]]}},
                     target, out)
    assert score.detail["reason"] == "invalid_certificate"
    assert score.awarded == target.points * 0.5
