"""The offline replay of S47's body predicate over the archived legs.

`refusal_replay.py` makes one arithmetic claim -- the wave stops buying an
`env_step` row per attempt -- and two conservation claims: the outbound request
count does not move, and `actions_agree` still holds. The arithmetic is the
easy part. What these tests are actually for is the two ways the tool could
produce an impressive number while being wrong:

* **collapsing more than `forward()` would.** The loop is bounded by
  `max_attempts`, so a long run of refusals becomes several rows, not one. A
  simulator that ignores the bound reports a saving nobody will ever get.
* **collapsing something that is not the wave.** The predicate is three
  conjuncts and the ledgers contain the near-misses that make each one
  load-bearing: a `400` with another `error`, the scorecard `404`
  (`VALIDATION_ERROR`, `scorecard <uuid> not found`) which is a real failure,
  and the hypothetical message naming a game the row did not ask for. Each is
  pinned here as a row that must survive.

The synthetic cases carry their own scorecard, so `actions_agree` is recomputed
before and after in every one of them rather than being checked once on the
archive. The archive-driven case is last and skips when the four legs are not
on this machine.

    cd proxy && python -m pytest tests/test_refusal_replay.py
"""

import os

import pytest

from proxy.tools import refusal_replay as rr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GAME = "g50t-5849a774"

#: The four live legs, and the pooled numbers `armtools/refusal.py` publishes
#: for them. Tracked artefacts, but a checkout is not a guarantee.
LEGS = ("20260731T1240Z-A3-level2-carried",
        "20260731T1310Z-A3-level2-carried-r2",
        "20260731T1430Z-A3-level2-carried-r3",
        "20260731T1500Z-A3-sk48-carried-l1")


# -- synthetic rows ---------------------------------------------------------

def step(seq, name="ACTION1", status=400, response=None, game=GAME,
         forwarded=True, attempts=1):
    """One `env_step` row in the shape `proxy/env_proxy.py:_command` writes."""
    return {
        "v": "1.0", "event": "env_step", "seq": seq, "game_id": game,
        "action": {"name": name, "id": None, "data": None},
        "frames": None, "n_frames": 0,
        "response": response,
        "http": {"method": "POST", "path": "/api/cmd/" + name, "status": status,
                 "forwarded": forwarded, "attempts": attempts},
    }


def wave(seq, name="ACTION1", game=GAME):
    """The refusal the predicate exists for."""
    return step(seq, name, 400, {"error": "SERVER_ERROR",
                                 "message": "game %s not found" % game},
                game=game)


def ok(seq, name="ACTION1"):
    row = step(seq, name, 200, {"state": "NOT_FINISHED", "score": 0})
    row["n_frames"] = 1
    row["frames"] = [[[0]]]
    return row


def card(total_actions):
    """The closing scorecard row, found the way `refusal.py:_scorecard` finds
    it: an `env_meta` whose response carries `environments`."""
    return {"v": "1.0", "event": "env_meta", "seq": 10_000,
            "response": {"environments": {GAME: {}},
                         "total_actions": total_actions}}


def report(rows, max_attempts=5, total_actions=None):
    """A full leg report over synthetic rows.

    `total_actions` defaults to the truth -- the number of 200 non-RESET rows --
    so that `actions_agree_before` is true by construction and the test is
    asking whether the *collapse* preserved it.
    """
    if total_actions is None:
        total_actions = len([r for r in rows
                             if r["http"]["status"] == 200
                             and r["action"]["name"] != "RESET"])
    return rr.replay_records(list(rows) + [card(total_actions)], max_attempts)


def assert_agrees(rep):
    assert rep["actions_agree_before"] is True
    assert rep["actions_agree_after"] is True
    assert rep["successful_actions"] == rep["successful_actions_before"]


# -- the loop ---------------------------------------------------------------

def test_three_refusals_then_success_is_one_row():
    rows = [wave(1), wave(2), wave(3), ok(4)]
    rep = report(rows)
    assert rep["env_steps_before"] == 4
    assert rep["env_steps_after"] == 1
    assert rep["wave_attempts"] == 3
    # One row, and it cost the four sockets it really cost.
    assert rep["outbound_attempts_after"] == 4
    assert rep["longest_collapse"] == 4
    assert rep["rows_out_of_budget"] == 0
    assert_agrees(rep)


def test_a_run_longer_than_the_budget_becomes_several_rows():
    """Twelve refusals then a success, budget 5: 5 + 5 + 3, not 1.

    This is the case that separates a simulation of `forward()` from a wish
    about it. The proxy gives up at `max_attempts`, the arm retries what it was
    handed, and that retry is a second proxy request and so a second row.
    """
    rows = [wave(i) for i in range(1, 13)] + [ok(13)]
    rep = report(rows, max_attempts=5)
    assert rep["env_steps_before"] == 13
    assert rep["env_steps_after"] == 3
    assert rep["rows_out_of_budget"] == 2
    assert rep["outbound_attempts_before"] == 13
    assert rep["outbound_attempts_after"] == 13
    assert rep["sockets_unchanged"] is True
    assert rep["rows_consumed"] == 13
    assert_agrees(rep)


def test_the_collapse_tracks_max_attempts():
    """Same twelve refusals, other budgets. 1 means no collapse at all."""
    rows = [wave(i) for i in range(1, 13)] + [ok(13)]
    sweep = report(rows)["env_steps_after_by_max_attempts"]
    assert sweep["1"] == 13                    # every attempt keeps its row
    assert sweep["2"] == 7                     # 2+2+2+2+2+2+1
    assert sweep["5"] == 3
    assert sweep["16"] == 1


# -- what must NOT collapse -------------------------------------------------

def test_a_400_with_another_error_does_not_collapse():
    rows = [step(1, response={"error": "VALIDATION_ERROR",
                              "message": "game %s not found" % GAME}),
            step(2, response={"error": "VALIDATION_ERROR",
                              "message": "game %s not found" % GAME}),
            ok(3)]
    rep = report(rows)
    assert rep["wave_attempts"] == 0
    assert rep["env_steps_after"] == 3
    assert_agrees(rep)


def test_the_scorecard_404_does_not_collapse():
    """The negative sample living in the same four legs.

    `404` / `VALIDATION_ERROR` / `scorecard <uuid> not found` is a card the
    server auto-closed -- a real, consequential failure that merely shares the
    substring `not found`. Two of them in a row must stay two rows.
    """
    body = {"error": "VALIDATION_ERROR",
            "message": "scorecard 6f1d0f6a-0d2c-4e6f-9d29-2a1b3c4d5e6f not found"}
    rows = [step(1, status=404, response=body),
            step(2, status=404, response=body),
            ok(3)]
    rep = report(rows)
    assert rep["wave_attempts"] == 0
    assert rep["env_steps_after"] == 3
    assert_agrees(rep)


def test_a_wave_message_naming_another_game_does_not_collapse():
    """No such row exists today. If one appears it is a client defect -- the id
    really was wrong -- and retrying it would turn a defect into a quota bill,
    so it must stay one row per attempt."""
    other = {"error": "SERVER_ERROR", "message": "game sk48-d8078629 not found"}
    rows = [step(1, response=other, game=GAME),
            step(2, response=other, game=GAME),
            ok(3)]
    rep = report(rows)
    assert rep["wave_attempts"] == 0
    assert rep["env_steps_after"] == 3
    assert_agrees(rep)


def test_a_row_with_no_body_does_not_collapse():
    """Three of this arm's legs predate the proxy keeping response bodies.
    `response: null` is unanswerable, not retryable."""
    rows = [step(1, response=None), step(2, response=None), ok(3)]
    rep = report(rows)
    assert rep["wave_attempts"] == 0
    assert rep["env_steps_after"] == 3


def test_an_unforwarded_row_never_joins_a_chain():
    """A guard refusal is this proxy saying no. Nothing left the process, there
    was no upstream answer to retry, and it costs the pool nothing."""
    denied = step(2, status=403, forwarded=False,
                  response={"error": "refused by the sealed-pile guard"})
    rows = [wave(1), denied, wave(3), ok(4)]
    rep = report(rows)
    assert rep["env_steps_after"] == 3         # wave | denied | wave+ok
    assert rep["outbound_attempts_before"] == 3
    assert rep["sockets_unchanged"] is True
    assert rep["rows_consumed"] == 4


def test_a_reset_wave_collapses_and_the_reset_stays_a_reset():
    """RESET is refused by the wave too -- `step_idx 0` is a refusal in all four
    legs -- and a collapsed RESET must not start counting as a landed action."""
    rows = [wave(1, "RESET"), wave(2, "RESET"), ok(3, "RESET"), ok(4, "ACTION2")]
    rep = report(rows)
    assert rep["env_steps_after"] == 2
    assert rep["scorecard_total_actions"] == 1
    assert_agrees(rep)


# -- conservation -----------------------------------------------------------

def test_sockets_are_conserved_for_every_budget():
    rows = [wave(1), wave(2), ok(3), wave(4), wave(5), wave(6), wave(7), ok(8)]
    for budget in (1, 2, 3, 5, 10):
        rep = report(rows, max_attempts=budget)
        assert rep["outbound_attempts_after"] == rep["outbound_attempts_before"]
        assert rep["rows_consumed"] == rep["env_steps_before"]
        assert_agrees(rep)


def test_a_broken_scorecard_is_reported_not_hidden():
    """`actions_agree_before` false must survive into the report as false. A
    tool that only ever prints true is a tool that is not measuring."""
    rep = report([ok(1), ok(2)], total_actions=99)
    assert rep["actions_agree_before"] is False
    assert rep["actions_agree_after"] is False
    problems = rr.failures([rep], rr._pool([rep], 5), verify=False)
    assert any("actions_agree_before" in p for p in problems)


def test_max_attempts_below_one_is_refused():
    with pytest.raises(ValueError):
        rr.simulate([wave(1)], 0)


# -- the archive ------------------------------------------------------------

def test_the_four_live_legs():
    """The real thing, skipped where the archive is not checked out.

    The expected numbers are asserted, not printed: 570 rows and 494 wave
    attempts are published in `armtools/refusal.py`, and 149 is what this
    simulation measures at the shipped `max_attempts` of 5. If the archive
    moves, this fails loudly rather than reporting a different answer to the
    same question.
    """
    paths = [os.path.join(REPO, "theoria-arm", "runs", leg, "ledger.jsonl")
             for leg in LEGS]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        pytest.skip("archived legs not present: %s" % ", ".join(missing))

    legs = [rr.replay_leg(path, 5) for path in paths]
    pooled = rr._pool(legs, 5)

    assert pooled["env_steps_before"] == 570
    assert pooled["wave_attempts"] == 494
    assert pooled["scorecard_total_actions"] == 72
    assert pooled["successful_actions"] == 72
    assert pooled["env_steps_after"] == 149
    assert [leg["env_steps_after"] for leg in legs] == [15, 27, 63, 44]
    assert pooled["outbound_attempts_before"] == 570
    assert pooled["outbound_attempts_after"] == 570
    assert pooled["sockets_unchanged"] is True
    assert pooled["actions_agree_before"] is True
    assert pooled["actions_agree_after"] is True
    assert rr.failures(legs, pooled, verify=True) == []


def test_the_cli_runs_the_four_legs(tmp_path, capsys):
    paths = [os.path.join(REPO, "theoria-arm", "runs", leg, "ledger.jsonl")
             for leg in LEGS]
    if any(not os.path.exists(p) for p in paths):
        pytest.skip("archived legs not present")

    out = str(tmp_path / "report.json")
    argv = []
    for path in paths:
        argv += ["--leg", path]
    assert rr.main(argv + ["--verify", "-o", out]) == 0
    capsys.readouterr()
    assert os.path.exists(out)
