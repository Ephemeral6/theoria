"""The per-level curve pipeline, and the gap it refuses to write.

`armtools/curves.py` reduces one leg's `turn_series` to the three curves figure
2 is made of -- theorize rounds, the seven surprise counts, cumulative cost --
cut at the level boundaries `inner/levels.py` recorded.

Two things are worth testing and they are not the same thing:

* **the cut.** No run in this archive has ever crossed a level boundary, so
  segmentation has no real data to be right about. The fixtures here are
  synthetic on purpose and they are built to be *asymmetric* -- level 1
  expensive and theorizing, level 2 cheap and quiet -- because a segmentation
  that is off by one turn, or that silently puts every row in level 1, would
  still produce a plausible-looking file from symmetric input.

* **the refusal.** The self-check is three strict equalities against the
  ledger -- environment commands, billed model calls, and dollars -- and each
  raises. A test that only ever feeds it consistent input proves nothing about
  it, so the mismatches are constructed here in both directions: a dropped
  turn, an extra ledger command, a billed call no turn row claims, and a call
  the curve prices differently from the ledger.

  The second and third of those equalities exist because the first was not
  enough, and the shortfall was measured rather than imagined. Two live legs
  ended on a tripped spend gate; each one's final desk call was billed by the
  pool and landed in no turn row, because `inner/loop.py` appends a turn's
  record only after that turn's last ARC command and the gate killed the turn
  before it sent one. The vanished turn had therefore issued no command, so
  the command equality balanced exactly -- 99 = 99 and 234 = 234 -- while the
  curves understated the legs by 17% and 12.5%.

The pipeline is also exercised against the **real** archive, which is the only
place the join's own quirks live (146 environment commands over 3 turns on one
run; 92 over 1 on another). A pipeline that only ever met its own fixtures
would be testing its author's idea of a ledger.
"""

from __future__ import annotations

import json
import os

import pytest

from armtools import archive, curves


def _turn(turn, *, step_idx=0, http=1, usd=0.0, theorize=0, surprises=None,
          actions=1, calls=0):
    counts = {kind: 0 for kind in archive.KINDS}
    for kind in (surprises or ()):
        counts[kind] += 1
    return {"turn": turn, "step_idx": step_idx, "http_commands": http,
            "actions_taken": actions, "theorize_rounds": theorize,
            "model_calls": calls, "usd": usd, "usd_cumulative": 0.0,
            "surprise_counts": counts, "surprise_total": sum(counts.values())}


def _leg(tmp_path, rows, *, boundaries=(), env_steps=None, slug="leg-fixture"):
    """A run directory carrying only what `curves()` reads.

    Deliberately not a whole run: `curves()` consumes `turn_series.json` and
    the `levels` block, and building a full ledger here would test the
    fixture-builder. The one raw file it does write is `ledger.jsonl`, because
    the self-check counts records in it and a fake count would defeat the only
    check this module has.
    """
    run_dir = tmp_path / slug
    run_dir.mkdir()

    # Money in a curve means a billed call in the ledger. The self-check is a
    # three-way equality now -- commands, billed calls, and dollars -- and a
    # fixture carrying cost with no `model_call` record would describe a run
    # that cannot exist, then fail the check for being impossible rather than
    # for being wrong. A row with cost and no declared call count gets one.
    for row in rows:
        if float(row.get("usd") or 0.0) and not row.get("model_calls"):
            row["model_calls"] = 1

    doc = {"schema": "theoria-arm/turn_series v1", "run_id": "fixture-run",
           "game_id": "g50t-5849a774", "slug": slug,
           "join": {"join_confidence": "exact"}, "rows": rows}
    (run_dir / "turn_series.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")

    events = [{"event": "level_boundary", "from_level": i + 1,
               "to_level": i + 2, "turn": turn, "step_idx": turn}
              for i, turn in enumerate(boundaries)]
    (run_dir / "run.json").write_text(json.dumps(
        {"levels": {"boundaries": len(events), "events": events,
                    "levels_completed": len(events)}}), encoding="utf-8")

    total = (env_steps if env_steps is not None
             else sum(r["http_commands"] for r in rows))
    # `v` comes from the frozen writer's own constant, never a literal: the
    # reader rejects any version it does not know (LEDGER_FORMAT.md §8), and a
    # fixture that hard-codes "1.0" would go red on a format bump for a reason
    # that has nothing to do with curves.
    from proxy.ledger import LEDGER_VERSION             # noqa: PLC0415

    with open(run_dir / "ledger.jsonl", "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(json.dumps({"v": LEDGER_VERSION, "event": "run_start",
                             "run_id": "fixture-run"}) + "\n")
        for i in range(total):
            fh.write(json.dumps({"v": LEDGER_VERSION, "event": "env_step",
                                 "step_idx": i}) + "\n")
        idx = 0
        for row in rows:
            n = int(row.get("model_calls") or 0)
            usd = float(row.get("usd") or 0.0)
            for k in range(n):
                # The last call of a turn carries the remainder, so the ledger
                # sums to the row's own figure exactly rather than to within a
                # float's worth of it.
                share = (usd - (usd / n) * (n - 1) if k == n - 1
                         else usd / n)
                fh.write(json.dumps(
                    {"v": LEDGER_VERSION, "event": "model_call",
                     "run_id": "fixture-run", "call_idx": idx,
                     "response": {"total_cost_usd": share}}) + "\n")
                idx += 1
    return str(run_dir)


def _freeze_turn_series(monkeypatch):
    """Stop `run_leg`'s archive step from re-deriving the fixture's series.

    `run_leg` calls `write_turn_series` and then `write_curves`. Left alone,
    the first would overwrite the `turn_series.json` these fixtures wrote with
    one derived from the fixture's deliberately minimal ledger -- and the test
    would then be about that derivation rather than about the wire. The join
    itself has its own tests; what is under test here is whether `run_leg`
    calls the reduction and records what it said.
    """
    def read_back(run_dir, **kwargs):
        with open(os.path.join(run_dir, "turn_series.json"),
                  encoding="utf-8") as fh:
            return json.load(fh)

    monkeypatch.setattr(archive, "write_turn_series", read_back)


# -- the cut ----------------------------------------------------------------

def test_the_boundary_turn_opens_the_new_level_rather_than_closing_the_old(
        tmp_path):
    """Off by one here is the most expensive mistake this file can make.

    `inner/levels.py:observe` records the boundary *at* the step whose envelope
    carries the new count, so the turn holding the event is the new level's
    **first**. Attributing it to the previous level instead would move the
    single most expensive turn of every level -- the one that theorizes against
    a board it has never seen -- onto the wrong side of the cut, and on a
    front-loaded curve that is the whole measurement.
    """
    rows = [_turn(0, usd=1.0, theorize=2),
            _turn(1, usd=0.5, theorize=1),
            _turn(2, usd=3.0, theorize=4),      # the boundary lands here
            _turn(3, usd=0.1, theorize=0)]
    out = curves.curves(_leg(tmp_path, rows, boundaries=[2]))

    assert [r["level"] for r in out["rows"]] == [1, 1, 2, 2]
    level1, level2 = out["levels"]
    assert level1["turns"] == [0, 1]
    assert level2["turns"] == [2, 3]
    assert level2["theorize_rounds"] == [4, 0]
    assert level2["totals"]["usd"] == pytest.approx(3.1)


def test_cost_accumulates_within_a_level_and_across_the_leg(tmp_path):
    """Two cumulative columns, because they answer two different questions.

    "Did the second level cost less than the first" needs a counter that
    restarts at the boundary; "what did this leg cost by turn 9" needs one that
    does not. Emitting only the leg-wide one would make every level after the
    first look expensive purely because it comes later.
    """
    rows = [_turn(0, usd=2.0), _turn(1, usd=1.0),
            _turn(2, usd=0.5), _turn(3, usd=0.25)]
    out = curves.curves(_leg(tmp_path, rows, boundaries=[2]))

    assert [r["usd_cumulative_in_leg"] for r in out["rows"]] == [2.0, 3.0,
                                                                 3.5, 3.75]
    assert [r["usd_cumulative_in_level"] for r in out["rows"]] == [2.0, 3.0,
                                                                   0.5, 0.75]
    assert out["levels"][1]["usd_cumulative"] == [0.5, 0.75]


def test_all_seven_surprise_kinds_are_series_even_when_they_are_all_zero(
        tmp_path):
    """A kind that never fired is a zero, never an absent key.

    The seven counts are a record of what the world did. A curve that omits the
    kinds with no occurrences would make two runs incomparable and would make
    "this kind stopped happening after level 1" -- the interesting claim --
    indistinguishable from "this kind was never plotted".
    """
    rows = [_turn(0, surprises=["replay_mismatch", "proof_failure"]),
            _turn(1, surprises=["replay_mismatch"]),
            _turn(2)]
    out = curves.curves(_leg(tmp_path, rows, boundaries=[2]))

    for block in out["levels"]:
        assert set(block["surprises"]) == set(archive.KINDS)
        for kind in archive.KINDS:
            assert len(block["surprises"][kind]) == block["totals"]["turns"]

    assert out["levels"][0]["surprises"]["replay_mismatch"] == [1, 1]
    assert out["levels"][0]["surprises"]["search_timeout"] == [0, 0]
    assert out["levels"][1]["totals"]["surprises"]["replay_mismatch"] == 0
    # And the flat rows carry the same seven, under the CSV column names.
    assert all("surprise_%s" % k in out["rows"][0] for k in archive.KINDS)


def test_a_leg_with_no_boundary_is_one_level(tmp_path):
    """The common case, and it must not be a special case in the output shape:
    a consumer that iterates `levels` has to work on a single-level leg too."""
    out = curves.curves(_leg(tmp_path, [_turn(0), _turn(1)]))
    assert out["totals"]["levels"] == 1
    assert out["levels"][0]["level"] == 1
    assert out["level_boundaries_at_turn"] == []


def test_a_boundary_with_no_turn_recorded_is_skipped_not_guessed(tmp_path):
    """`LevelLog.observe` takes `turn` as optional, and a leg reconstructed
    without `turns.json` may not have one. A cut placed by guesswork is worse
    than an uncut curve, because it looks exactly as authoritative."""
    run_dir = _leg(tmp_path, [_turn(0), _turn(1), _turn(2)])
    with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as fh:
        json.dump({"levels": {"boundaries": 1, "events": [
            {"event": "level_boundary", "to_level": 2, "turn": None}]}}, fh)
    out = curves.curves(run_dir)
    assert out["level_boundaries_at_turn"] == []
    assert out["totals"]["levels"] == 1


# -- the refusal ------------------------------------------------------------

def test_a_dropped_turn_raises_rather_than_writing_a_short_curve(tmp_path):
    """The failure the self-check exists for.

    A segmentation that loses a turn produces a curve that is simply shorter,
    and nothing about a shorter curve looks wrong -- least of all in a plot.
    The money it represents was still spent.
    """
    rows = [_turn(0, http=5), _turn(1, http=7)]
    # The ledger says 20 commands; the curves account for 12.
    run_dir = _leg(tmp_path, rows, env_steps=20)
    with pytest.raises(curves.CurveGap) as caught:
        curves.curves(run_dir)
    assert "12" in str(caught.value) and "20" in str(caught.value)


def test_an_over_counted_curve_raises_too(tmp_path):
    """Strict equality, not a floor. A curve that accounts for *more* commands
    than the ledger holds is just as broken -- it means a turn was counted
    twice -- and a one-sided check would let the double-counting through."""
    rows = [_turn(0, http=5), _turn(1, http=7)]
    with pytest.raises(curves.CurveGap):
        curves.curves(_leg(tmp_path, rows, env_steps=3))


def test_nothing_is_written_when_the_accounting_has_a_hole(tmp_path):
    """A missing file is a question somebody asks. A plausible short curve is
    not."""
    run_dir = _leg(tmp_path, [_turn(0, http=5)], env_steps=9)
    with pytest.raises(curves.CurveGap):
        curves.write_curves(run_dir)
    assert not os.path.exists(os.path.join(run_dir, "curves.json"))
    assert not os.path.exists(os.path.join(run_dir, "curves"))


def test_an_empty_leg_is_refused_rather_than_written_as_zeros(tmp_path):
    """`0 == 0` passes the equality, and that is the trap.

    A leg that never took a turn would otherwise produce a syntactically
    perfect `curves.json` whose every series is empty and whose every total is
    zero -- and zero in a cost curve reads as "this leg was cheap", not as
    "this leg did not happen". `theoria-arm/verify.py` opens with this exact
    rule, citing `figures/verify.sh` printing "ok" when both of its builds
    produced nothing at all.
    """
    run_dir = _leg(tmp_path, [], env_steps=0)
    with pytest.raises(curves.CurveGap) as caught:
        curves.curves(run_dir)
    assert "never played" in str(caught.value)
    with pytest.raises(curves.CurveGap):
        curves.write_curves(run_dir)
    assert not os.path.exists(os.path.join(run_dir, "curves.json"))


def test_a_join_that_lost_every_row_is_refused_by_the_same_floor(tmp_path):
    """The other cause of zero rows, and the dangerous one: the ledger has
    commands and the series has none. Same refusal, and the message names both
    numbers so the reader can tell which case they are in."""
    run_dir = _leg(tmp_path, [], env_steps=17)
    with pytest.raises(curves.CurveGap) as caught:
        curves.curves(run_dir)
    assert "17" in str(caught.value)


def test_the_self_check_is_reported_as_well_as_enforced(tmp_path):
    """The reader of a good file should be able to see the check ran, not
    infer it from the absence of an exception."""
    out = curves.curves(_leg(tmp_path, [_turn(0, http=4), _turn(1, http=6)]))
    check = out["self_check"]
    assert check["http_commands_over_the_curves"] == 10
    assert check["env_step_records_in_the_ledger"] == 10
    assert check["accounts_for_every_env_step"] is True


# -- on disk ----------------------------------------------------------------

def test_the_files_land_where_a_per_level_consumer_can_find_them(tmp_path):
    rows = [_turn(0, usd=1.0), _turn(1, usd=0.1), _turn(2, usd=0.05)]
    run_dir = _leg(tmp_path, rows, boundaries=[1, 2])
    curves.write_curves(run_dir)

    assert os.path.exists(os.path.join(run_dir, "curves.json"))
    for level in (1, 2, 3):
        path = os.path.join(run_dir, "curves", "level-%02d.json" % level)
        assert os.path.exists(path), path
        with open(path, encoding="utf-8") as fh:
            block = json.load(fh)
        assert block["level"] == level
        assert block["schema"] == curves.SCHEMA
        assert set(block["surprises"]) == set(archive.KINDS)


def test_the_written_file_is_byte_stable(tmp_path):
    """Determinism is a requirement here, not a nicety (CLAUDE.md): a figure
    whose input moves between two runs over the same ledger cannot be audited
    by diffing anything."""
    rows = [_turn(0, usd=1.0), _turn(1, usd=0.5)]
    run_dir = _leg(tmp_path, rows, boundaries=[1])
    curves.write_curves(run_dir)
    with open(os.path.join(run_dir, "curves.json"), "rb") as fh:
        first = fh.read()
    curves.write_curves(run_dir)
    with open(os.path.join(run_dir, "curves.json"), "rb") as fh:
        assert fh.read() == first
    assert b"\r\n" not in first


def test_the_columns_are_declared_and_match_the_rows(tmp_path):
    """`figures/` audits every plate through a CSV. A column order inferred
    from a dict would be alphabetical, which puts `usd_cumulative_in_leg`
    before `theorize_rounds` and makes the audit table read backwards."""
    out = curves.curves(_leg(tmp_path, [_turn(0), _turn(1)]))
    assert out["columns"][:3] == ["level", "turn", "campaign_turn_in_leg"]
    for row in out["rows"]:
        assert set(row) == set(out["columns"])


# -- against the real archive ----------------------------------------------

@pytest.mark.parametrize("slug,turns,commands", [
    ("20260729T004020Z-leg01", 52, 104),
    ("20260728T025503Z-g50t-e08-fixed", 3, 146),
])
def test_the_real_archive_reduces_and_balances(slug, turns, commands):
    """Real ledgers, with the ratios that make the invariant worth stating.

    146 environment commands over 3 turns is not a rounding difference -- it is
    what a turn actually looks like once RESETs, retries and refused actions
    are counted. Anyone tempted to write the self-check as "one turn per step"
    meets this run.
    """
    import _bootstrap                                   # noqa: PLC0415

    run_dir = _bootstrap.path("runs", slug)
    if not os.path.exists(os.path.join(run_dir, "ledger.jsonl")):
        pytest.skip("%s is not in this checkout" % slug)
    out = curves.curves(run_dir)
    assert out["totals"]["turns"] == turns
    assert out["self_check"]["env_step_records_in_the_ledger"] == commands
    assert out["self_check"]["accounts_for_every_env_step"] is True
    assert out["totals"]["levels"] == 1


def test_a_finished_leg_writes_its_curves(tmp_path, monkeypatch):
    """The wire, not the pipeline: does `run_leg` actually call this?

    Every test in `tests/test_campaign.py` replaces `run_leg` wholesale, which
    is why the archive step inside it has historically been the one part of the
    campaign with no coverage -- and `_leg_cost` shipped a bug for exactly that
    reason (it read a key `ModelDesk.summary()` has never emitted, so the $60
    and $200 ceilings could not trip). So this drives the **real** `run_leg`
    with only `play` replaced, and requires `curves.json` on disk afterwards.
    """
    from harness import campaign as camp                # noqa: PLC0415
    from harness import run as run_mod                  # noqa: PLC0415
    from harness import spend as spend_mod              # noqa: PLC0415

    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    monkeypatch.setattr(camp, "ARM", str(tmp_path))

    captured = {}
    _freeze_turn_series(monkeypatch)

    def fake_play(game_id, slug, factory, **kwargs):
        # `play` owns the run directory; stand in for it, then hand back a
        # summary of the shape `run_leg` reads.
        leg = _leg(runs_root, [_turn(0, usd=1.0, theorize=2, http=3),
                               _turn(1, usd=0.25, theorize=0, http=2)],
                   boundaries=[1], slug=slug)
        captured["run_dir"] = leg
        return {"levels": {"boundaries": 1, "events": [
                    {"event": "level_boundary", "to_level": 2, "turn": 1}]},
                "surprises": {"by_kind": {}, "total": 0},
                "outcome": "budget_exhausted", "theorize_rounds": 2,
                "budget": {"actions_ok": 2},
                "desk": {"cli_cost_usd": 1.25,
                         "spend_gate": {"usd_charged": 1.25}}}

    monkeypatch.setattr(camp, "play", fake_play)
    gate = spend_mod.SpendGate(
        run_mod._scratch_policy(str(tmp_path / "pool.jsonl")))
    campaign = camp.Campaign(prompt_id="A8-wire", out_dir=str(tmp_path / "out"),
                             games=["g50t-5849a774"], offline=True,
                             spend_gate=gate)
    leg = campaign.run_leg("g50t-5849a774", 1, None)

    assert leg["curves_error"] is None, leg["curves_error"]
    assert os.path.exists(leg["curves_path"]), leg["curves_path"]
    with open(leg["curves_path"], encoding="utf-8") as fh:
        doc = json.load(fh)
    assert doc["schema"] == curves.SCHEMA
    assert doc["totals"]["levels"] == 2
    assert doc["self_check"]["accounts_for_every_env_step"] is True
    assert os.path.exists(os.path.join(captured["run_dir"], "curves",
                                       "level-02.json"))


def test_a_curve_gap_is_recorded_on_the_leg_and_does_not_lose_it(
        tmp_path, monkeypatch):
    """The negative control for the wire above.

    A leg that played and was paid for must survive a failed reduction -- the
    money is spent either way and the leg is the record of it. But the failure
    has to reach the leg's own entry, or a campaign report would show a leg
    with no curves and no reason.
    """
    from harness import campaign as camp                # noqa: PLC0415
    from harness import run as run_mod                  # noqa: PLC0415
    from harness import spend as spend_mod              # noqa: PLC0415

    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    monkeypatch.setattr(camp, "ARM", str(tmp_path))
    _freeze_turn_series(monkeypatch)

    def fake_play(game_id, slug, factory, **kwargs):
        # A ledger claiming more commands than the turns account for.
        _leg(runs_root, [_turn(0, http=2)], env_steps=9, slug=slug)
        return {"levels": {"boundaries": 0, "events": []},
                "surprises": {"by_kind": {}, "total": 0},
                "outcome": "budget_exhausted", "budget": {"actions_ok": 1},
                "desk": {"cli_cost_usd": 0.5,
                         "spend_gate": {"usd_charged": 0.5}}}

    monkeypatch.setattr(camp, "play", fake_play)
    gate = spend_mod.SpendGate(
        run_mod._scratch_policy(str(tmp_path / "pool.jsonl")))
    campaign = camp.Campaign(prompt_id="A8-wire-negative",
                             out_dir=str(tmp_path / "out"),
                             games=["g50t-5849a774"], offline=True,
                             spend_gate=gate)
    leg = campaign.run_leg("g50t-5849a774", 1, None)

    assert leg["usd"] == 0.5, "the leg still has to be booked"
    assert leg["curves_error"] and "CurveGap" in leg["curves_error"]
    assert not os.path.exists(leg["curves_path"])


def test_the_pipeline_does_not_re_derive_the_join(tmp_path, monkeypatch):
    """`curves()` must consume `turn_series`, never recompute it.

    A second implementation of the join would be a second answer to the same
    question, and E2's input would then have two definitions. Enforced by
    breaking `archive.turn_series` and requiring the reduction to succeed
    anyway from the document already on disk.
    """
    def boom(*args, **kwargs):
        raise AssertionError("curves() re-derived the join")

    run_dir = _leg(tmp_path, [_turn(0), _turn(1)])
    monkeypatch.setattr(archive, "turn_series", boom)
    out = curves.curves(run_dir)
    assert out["totals"]["turns"] == 2


# -- the two equalities the command count could not see ---------------------

def _extra_call(run_dir, usd):
    """One more `model_call` in the ledger than the curves account for."""
    from proxy.ledger import LEDGER_VERSION             # noqa: PLC0415

    with open(os.path.join(run_dir, "ledger.jsonl"), "a", encoding="utf-8",
              newline="\n") as fh:
        fh.write(json.dumps({"v": LEDGER_VERSION, "event": "model_call",
                             "run_id": "fixture-run", "call_idx": 99,
                             "response": {"total_cost_usd": usd}}) + "\n")


def test_a_billed_call_the_curves_do_not_account_for_raises(tmp_path):
    """The defect the command equality was blind to.

    A leg killed inside a turn spends its last desk call and issues no
    environment command afterwards -- so `http_commands` balances exactly while
    the money does not. Two live legs shipped that way (r2 lost $1.63 of $9.56,
    r3 lost $1.68 of $13.44) and every check on the archive was green.
    """
    run_dir = _leg(tmp_path, [_turn(0, http=4, usd=1.0, calls=1)])
    _extra_call(run_dir, 9.0)

    with pytest.raises(curves.CurveGap) as caught:
        curves.curves(run_dir)
    message = str(caught.value)
    assert "1 billed model call" in message and "2 model_call" in message
    assert "spend gate" in message


def test_a_dollar_the_curves_do_not_account_for_raises_too(tmp_path):
    """Counting calls is not counting money.

    A curve can hold the right *number* of calls and the wrong total -- a
    misattributed retry, a response read from the wrong field -- and a bill
    shape drawn from it is the shape of a bill nobody was sent.
    """
    run_dir = _leg(tmp_path, [_turn(0, http=4, usd=1.0, calls=1)])
    path = os.path.join(run_dir, "ledger.jsonl")
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    lines[-1] = lines[-1].replace('"total_cost_usd": 1.0',
                                  '"total_cost_usd": 4.5')
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(lines)

    with pytest.raises(curves.CurveGap) as caught:
        curves.curves(run_dir)
    assert "$1.000000" in str(caught.value) and "$4.500000" in str(caught.value)


def test_nothing_is_written_when_a_call_is_missing_from_the_curve(tmp_path):
    """Same refusal as the command gap: a missing file is a question somebody
    asks, an understated cost curve is not."""
    run_dir = _leg(tmp_path, [_turn(0, http=4, usd=1.0, calls=1)])
    _extra_call(run_dir, 9.0)

    with pytest.raises(curves.CurveGap):
        curves.write_curves(run_dir)
    assert not os.path.exists(os.path.join(run_dir, "curves.json"))


def test_the_money_self_check_is_reported_as_well_as_enforced(tmp_path):
    """A reader of a good file should see all three equalities ran."""
    out = curves.curves(_leg(tmp_path, [_turn(0, http=4, usd=2.0, calls=1),
                                        _turn(1, http=6, usd=0.5, calls=2)]))
    check = out["self_check"]

    assert check["billed_calls_over_the_curves"] == 3
    assert check["model_call_records_in_the_ledger"] == 3
    assert check["accounts_for_every_billed_call"] is True
    assert check["usd_over_the_curves"] == pytest.approx(2.5)
    assert check["usd_in_the_ledger"] == pytest.approx(2.5)
    assert check["accounts_for_every_dollar"] is True
    assert check["turns_with_no_record_of_their_own"] == []


def test_turn_record_missing_is_a_column_on_every_row(tmp_path):
    """False on an ordinary turn, never an absent key.

    The same rule the seven surprise counts follow: a flag that appears only
    when something went wrong makes "this turn was recorded" and "this arm did
    not measure whether it was" the same bytes.
    """
    out = curves.curves(_leg(tmp_path, [_turn(0), _turn(1)]))
    assert "turn_record_missing" in out["columns"]
    assert [r["turn_record_missing"] for r in out["rows"]] == [False, False]


@pytest.mark.parametrize("slug,rows,calls,usd", [
    ("20260731T1310Z-A3-level2-carried-r2", 11, 5, 9.556852),
    ("20260731T1430Z-A3-level2-carried-r3", 31, 8, 13.439862),
])
def test_the_gate_tripped_legs_carry_their_last_call(slug, rows, calls, usd):
    """End to end on the material the defect was found in.

    Before the fix r2 reduced to 10 rows / 4 calls / $7.926367 and r3 to 30 /
    7 / $11.761053, and both self-checks were green because the missing turn
    had issued no environment command.
    """
    import _bootstrap                                   # noqa: PLC0415

    run_dir = _bootstrap.path("runs", slug)
    if not os.path.exists(os.path.join(run_dir, "ledger.jsonl")):
        pytest.skip("%s is not in this checkout" % slug)
    out = curves.curves(run_dir)

    assert out["totals"]["turns"] == rows
    assert out["totals"]["usd"] == pytest.approx(usd)
    assert out["self_check"]["accounts_for_every_billed_call"] is True
    assert out["self_check"]["accounts_for_every_dollar"] is True
    assert out["self_check"]["billed_calls_over_the_curves"] == calls

    orphan = [r for r in out["rows"] if r["turn_record_missing"]]
    assert len(orphan) == 1
    assert orphan[0]["model_calls"] == 1
    assert orphan[0]["http_commands"] == 0
    # The lost turn is on the level it died in, not banished to level 1.
    assert orphan[0]["level"] == out["rows"][-2]["level"]
