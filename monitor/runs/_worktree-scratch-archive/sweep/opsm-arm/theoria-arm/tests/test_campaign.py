"""The campaign's accounts and its stop conditions, without spending anything.

Every test here drives `harness/campaign.py` with `run_leg` replaced, because
the thing under test is the loop *above* a run: the money arithmetic, the
carry-over rule, the four stop conditions and the checkpoint. Whether a leg
plays well is `tests/test_arm.py`'s question; whether a campaign stops when it
should is this file's, and it is the one that is answered in dollars.

The dev-pile guard is tested against the real `piles.json`, not a fixture. A
fixture would prove the code reads a file; the point is that it reads *that*
file, because the sealed pile's guarantee is the one claim in this repo that
cannot be repaired after it is broken.
"""

from __future__ import annotations

import json
import os

import pytest

from harness import campaign as camp


def _summary(*, boundaries=0, kinds=(), usd=0.0, outcome="budget_exhausted"):
    by_kind = {k: 0 for k in (
        "replay_mismatch", "render_mismatch", "proof_failure",
        "probe_refutation", "execution_mismatch", "search_timeout",
        "heuristic_miss")}
    for kind in kinds:
        by_kind[kind] += 1
    return {"levels": {"boundaries": boundaries, "levels_completed": boundaries},
            "surprises": {"by_kind": by_kind, "total": sum(by_kind.values())},
            "usd": usd, "outcome": outcome}


class _Fake(camp.Campaign):
    """A campaign whose legs are scripted instead of played."""

    def __init__(self, script, **kwargs):
        kwargs.setdefault("prompt_id", "A3-campaign-devpile")
        super().__init__(**kwargs)
        self.script = list(script)
        self.calls = []

    def run_leg(self, game_id, index, seed_books):
        self._check_budget(game_id)
        self.calls.append({"game_id": game_id, "index": index,
                           "seed_books": seed_books})
        spec = self.script.pop(0) if self.script else _summary()
        usd = float(spec.get("usd", 0.0))
        self.spent_usd += usd
        self.by_game[game_id] = self.by_game.get(game_id, 0.0) + usd
        slug = "%s-leg%02d" % (game_id.split("-")[0], index)
        return {"index": index, "game_id": game_id, "slug": slug,
                "usd": usd, "levels": spec["levels"],
                "surprises": spec["surprises"],
                "outcome": spec.get("outcome", "budget_exhausted"),
                "books_dir": "/runs/%s/books" % slug,
                "carried": None, "stopped_because": ""}


# -- the pile guard ---------------------------------------------------------

def test_a_sealed_game_is_refused_by_name():
    """The one failure this repo cannot repair after the fact."""
    piles = json.load(open(
        os.path.join(camp.REPO, "arc-recon", "data", "piles.json"), encoding="utf-8"))
    sealed = piles["sealed_pile"][0]
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_dev_pile([sealed])
    assert "sealed" in str(caught.value)
    assert sealed in str(caught.value)


def test_a_game_in_neither_pile_is_refused():
    with pytest.raises(camp.CampaignStopped):
        camp.assert_dev_pile(["not-a-real-game"])


def test_the_default_roster_is_exactly_the_development_pile():
    """`DEV_PILE` is a convenience; `piles.json` is the authority. If they ever
    disagree, this test says so before a run does."""
    piles = json.load(open(
        os.path.join(camp.REPO, "arc-recon", "data", "piles.json"), encoding="utf-8"))
    assert set(camp.DEV_PILE) == set(piles["dev_pile"])
    camp.assert_dev_pile(camp.DEV_PILE)          # must not raise


# -- the money --------------------------------------------------------------

def test_the_leg_reservation_cannot_exceed_the_authorised_cap():
    """$25 per reservation, and `plan_caps` adds a model-call ceiling on top of
    the cost ceiling -- so the cost ceiling has to be the smaller number."""
    from harness import spend as spend_mod
    assert (camp.LEG_COST_CEILING_USD + spend_mod.MODEL_CALL_CEILING_USD
            <= camp.LEG_USD_CAP)


def test_a_game_stops_at_its_own_ceiling_without_ending_the_campaign(tmp_path):
    camp_run = _Fake([_summary(usd=30.0, kinds=["replay_mismatch"]),
                      _summary(usd=31.0, kinds=["render_mismatch"]),
                      _summary(usd=5.0, kinds=["proof_failure"])],
                     out_dir=str(tmp_path), games=["g50t-5849a774",
                                                   "sk48-d8078629"],
                     offline=True)
    report = camp_run.run(max_legs_per_game=5)
    played = [c["game_id"] for c in camp_run.calls]
    assert played.count("g50t-5849a774") == 2, played
    # The game ran out of money; the campaign moved to the next game rather
    # than ending.
    assert "sk48-d8078629" in played
    assert report["by_game"]["g50t-5849a774"] == pytest.approx(61.0)


def test_the_campaign_ceiling_ends_everything(tmp_path):
    camp_run = _Fake([_summary(usd=59.0, kinds=["replay_mismatch"]),
                      _summary(usd=59.0, kinds=["render_mismatch"]),
                      _summary(usd=59.0, kinds=["proof_failure"]),
                      _summary(usd=59.0, kinds=["probe_refutation"])],
                     out_dir=str(tmp_path), games=list(camp.DEV_PILE),
                     offline=True)
    report = camp_run.run(max_legs_per_game=1)
    assert report["spent_usd"] <= camp.CAMPAIGN_USD + 59.0
    assert report["stopped"] is not None
    assert "campaign budget" in report["stopped"]["reason"]


# -- progress ---------------------------------------------------------------

def test_three_dead_legs_end_the_campaign(tmp_path):
    """No level, no new kind of surprise, three times."""
    dead = _summary(usd=1.0, kinds=["replay_mismatch"])
    camp_run = _Fake([_summary(usd=1.0, kinds=["replay_mismatch"]),
                      dead, dead, dead, dead],
                     out_dir=str(tmp_path), games=["g50t-5849a774"],
                     offline=True)
    report = camp_run.run(max_legs_per_game=9)
    assert report["stopped"] is not None
    assert "no new kind of surprise" in report["stopped"]["reason"]
    # First leg was progress (the kind was fresh), then three dead ones.
    assert len(camp_run.calls) == 4, camp_run.calls


def test_a_new_kind_of_surprise_counts_as_progress(tmp_path):
    """On a game nobody has ever cleared a level of, insisting on level
    completions would end the campaign before it measured anything."""
    camp_run = _Fake([_summary(usd=1.0, kinds=["replay_mismatch"]),
                      _summary(usd=1.0, kinds=["render_mismatch"]),
                      _summary(usd=1.0, kinds=["proof_failure"]),
                      _summary(usd=1.0, kinds=["search_timeout"])],
                     out_dir=str(tmp_path), games=["g50t-5849a774"],
                     offline=True)
    report = camp_run.run(max_legs_per_game=4)
    assert report["stopped"] is None, report["stopped"]
    assert report["zero_progress_streak"] == 0


def test_a_completed_level_counts_as_progress_even_with_no_new_surprise(tmp_path):
    repeat = ["replay_mismatch"]
    camp_run = _Fake([_summary(usd=1.0, kinds=repeat),
                      _summary(usd=1.0, kinds=repeat, boundaries=1),
                      _summary(usd=1.0, kinds=repeat, boundaries=1)],
                     out_dir=str(tmp_path), games=["g50t-5849a774"],
                     offline=True)
    report = camp_run.run(max_legs_per_game=3)
    assert report["stopped"] is None
    assert report["levels_completed"] == 2


# -- what travels -----------------------------------------------------------

def test_books_travel_between_legs_of_one_game_and_not_between_games(tmp_path):
    """C3's claim is level-to-level. Two ARC games are two different worlds."""
    camp_run = _Fake([_summary(usd=1.0, kinds=["replay_mismatch"]),
                      _summary(usd=1.0, kinds=["render_mismatch"]),
                      _summary(usd=1.0, kinds=["proof_failure"]),
                      _summary(usd=1.0, kinds=["search_timeout"])],
                     out_dir=str(tmp_path),
                     games=["g50t-5849a774", "sk48-d8078629"],
                     offline=True)
    camp_run.run(max_legs_per_game=2)
    calls = camp_run.calls
    assert calls[0]["seed_books"] is None, "first leg has nothing to carry"
    assert calls[1]["seed_books"] == "/runs/g50t-leg01/books"
    # New game: the chain restarts.
    assert calls[2]["game_id"] == "sk48-d8078629"
    assert calls[2]["seed_books"] is None, "books must not cross games"
    assert calls[3]["seed_books"] == "/runs/sk48-leg01/books"


def test_a_leg_that_died_before_writing_does_not_seed_the_next(tmp_path):
    """Seeding from a half-written manual would launder a broken book into a
    transfer claim."""
    broken = _summary(usd=1.0, kinds=["replay_mismatch"], outcome="reset_failed")
    camp_run = _Fake([broken,
                      _summary(usd=1.0, kinds=["render_mismatch"])],
                     out_dir=str(tmp_path), games=["g50t-5849a774"],
                     offline=True)
    camp_run.run(max_legs_per_game=2)
    assert camp_run.calls[1]["seed_books"] is None


# -- the checkpoint ---------------------------------------------------------

def test_every_leg_is_on_disk_before_the_next_one_starts(tmp_path):
    """A campaign is hours long and the session running it will be
    interrupted. Only what is on disk exists."""
    seen = []

    class Watching(_Fake):
        def run_leg(self, game_id, index, seed_books):
            if os.path.exists(self.state_path):
                with open(self.state_path, encoding="utf-8") as fh:
                    seen.append(len(json.load(fh)["legs"]))
            else:
                seen.append(0)
            return super().run_leg(game_id, index, seed_books)

    run = Watching([_summary(usd=1.0, kinds=["replay_mismatch"]),
                    _summary(usd=1.0, kinds=["render_mismatch"]),
                    _summary(usd=1.0, kinds=["proof_failure"])],
                   out_dir=str(tmp_path), games=["g50t-5849a774"],
                   offline=True)
    run.run(max_legs_per_game=3)
    assert seen == [0, 1, 2], seen
    on_disk = json.load(open(run.state_path, encoding="utf-8"))
    assert len(on_disk["legs"]) == 3
    assert on_disk["prompt_id"] == "A3-campaign-devpile"


def test_the_checkpoint_is_replaced_atomically(tmp_path):
    run = _Fake([_summary(usd=1.0, kinds=["replay_mismatch"])],
                out_dir=str(tmp_path), games=["g50t-5849a774"], offline=True)
    run.run(max_legs_per_game=1)
    assert not os.path.exists(run.state_path + ".tmp"), (
        "a leftover .tmp means the replace did not happen and a reader could "
        "see a half-written campaign")


def test_the_report_carries_the_authorised_package(tmp_path):
    """The run and its authorisation must not be able to drift apart."""
    run = _Fake([], out_dir=str(tmp_path), games=["g50t-5849a774"],
                offline=True)
    report = run.run(max_legs_per_game=0)
    assert report["budget"] == {"campaign_usd": 200.0, "game_usd": 60.0,
                                "leg_usd_cap": 25.0, "actions_per_level": 40}


# ------------------------------------------------- the leg's dollar accounting
#
# The bug these exist for: `run_leg` read `summary["desk"]["cost_usd"]`, a key
# `ModelDesk.summary()` has never emitted. It evaluated to None on every leg, so
# `usd` was always 0.0, `spent_usd` and `by_game` never moved, and the $60/game
# and $200/campaign ceilings could not trip. It survived because every test
# above replaces `run_leg` wholesale -- the accounting was the one part of the
# campaign nothing exercised.

def test_the_leg_cost_reads_a_key_the_desk_actually_emits():
    """The regression, stated as the shape of a real `ModelDesk.summary()`."""
    usd, acct = camp._leg_cost({"desk": {
        "model": "claude-opus-5", "calls": 3, "cli_cost_usd": 4.25,
        "spend_gate": {"usd_charged": 4.25}}})
    assert usd == 4.25
    assert acct["cli_cost_usd"] == 4.25
    assert acct["gate_usd_charged"] == 4.25


def test_the_old_key_is_gone_from_the_desks_vocabulary():
    """Pins the cause rather than the symptom.

    If `ModelDesk.summary()` ever grows a `cost_usd`, the fix above becomes
    ambiguous and this test says so before a campaign banks on it.
    """
    from harness.modelcall import ModelDesk             # noqa: PLC0415

    class _Run:
        run_id = "r"
    keys = set(ModelDesk(_Run(), cost_ceiling_usd=1.0).summary())
    assert "cli_cost_usd" in keys
    assert "cost_usd" not in keys


def test_the_ceiling_governs_on_the_larger_of_two_disagreeing_figures():
    """INC-TA-003: `proxy/cost.py` under-bills 1h cache writes by 6.8%, and the
    gate charges a ceiling for a call it cannot price. The two figures disagree
    by construction, and a ceiling that believes the smaller one is a ceiling
    that can be walked past."""
    usd, acct = camp._leg_cost({"desk": {
        "cli_cost_usd": 5.0, "spend_gate": {"usd_charged": 9.0}}})
    assert usd == 9.0 and acct["governing_source"] == "gate"

    usd, acct = camp._leg_cost({"desk": {
        "cli_cost_usd": 9.0, "spend_gate": {"usd_charged": 5.0}}})
    assert usd == 9.0 and acct["governing_source"] == "cli"


def test_a_leg_that_reports_no_cost_at_all_is_recorded_as_such():
    """Zero and unknown are different facts. An offline leg genuinely costs
    nothing; a leg whose desk reported nothing is a hole in the accounts, and
    booking both as 0.0 is how the original bug stayed invisible."""
    usd, acct = camp._leg_cost({"desk": {}})
    assert usd == 0.0
    assert acct["governing_source"] == "no-cost-reported"
    assert acct["gate_absent"] is True


def test_a_game_ceiling_now_actually_trips(tmp_path):
    """End to end through the real accounting.

    Three legs at $25 take g50t to $75. The ceiling is checked *before* a leg,
    not after, so the overrun to $75 is expected -- a leg is sized by
    `_game_headroom` and then allowed to finish. What must happen is that the
    *fourth* leg is refused and the campaign moves to the next game instead of
    ending. With the old `cost_usd` key every leg booked $0.00, `by_game` never
    moved, and neither the refusal nor the move ever happened.
    """
    run = _Fake([_summary(usd=25.0, kinds=["replay_mismatch"]),
                 _summary(usd=25.0, kinds=["render_mismatch"]),
                 _summary(usd=25.0, kinds=["proof_failure"])],
                out_dir=str(tmp_path),
                games=["g50t-5849a774", "sk48-d8078629"])
    # `_Fake.run_leg` books through the same fields `run_leg` does.
    report = run.run(max_legs_per_game=4)
    assert report["by_game"]["g50t-5849a774"] >= 60.0
    assert any(leg.get("event") == "game_end" for leg in report["legs"])


# ------------------------------------------------ figure 2's raw material
#
# The A3 order names three columns -- theorize rounds, the seven surprise
# counts, per-turn cost -- and calls them figure 2's entire raw material.
# `armtools.archive.write_turn_series` produces all three per leg. What only a
# campaign knows is play order across legs and where the level boundaries fell.

@pytest.fixture
def arm_runs(tmp_path, monkeypatch):
    """Point `campaign_series` at a runs/ tree the test owns.

    Without this the helper below writes into the real `theoria-arm/runs/`,
    which is the same non-hermetic shape that let `test_arm.py` poison a shared
    ledger and go permanently red. A test that leaves artefacts in the tree it
    is testing will eventually be testing its own leftovers.
    """
    monkeypatch.setattr(camp, "ARM", str(tmp_path / "arm"))
    return tmp_path


def _leg_with_series(tmp_path, slug, game, turns, *, seeded=False,
                     boundary_turn=None):
    """Write a leg's turn_series.json where `campaign_series` will look."""
    run_dir = os.path.join(camp.ARM, "runs", slug)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "turn_series.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": [{"turn": t, "usd": 1.0 + t, "theorize_rounds": 1}
                            for t in range(turns)]}, fh)
    levels = ({"events": [{"turn": boundary_turn}]}
              if boundary_turn is not None else {})
    return {"index": 1, "game_id": game, "slug": slug, "levels": levels,
            "seed_books": "/books" if seeded else None,
            "usd": sum(1.0 + t for t in range(turns)), "outcome": "ok"}


def test_the_campaign_turn_is_dense_while_the_legs_own_turn_restarts(arm_runs, tmp_path):
    """The axis C2's front-heavy claim is about.

    A leg's `turn` restarts every time a leg dies and a new one begins. A bill
    shape read off that axis would show the campaign restarting its own clock
    at every interruption, which is precisely the artefact that would fake the
    predicted shape.
    """
    c = camp.Campaign(prompt_id="A3", out_dir=str(tmp_path),
                      games=["g50t-5849a774"])
    c.legs = [_leg_with_series(tmp_path, "t-a3-x1", "g50t-5849a774", 3),
              _leg_with_series(tmp_path, "t-a3-x2", "g50t-5849a774", 2)]
    doc = c.campaign_series()

    assert [r["campaign_turn"] for r in doc["rows"]] == [1, 2, 3, 4, 5]
    assert [r["turn"] for r in doc["rows"]] == [0, 1, 2, 0, 1]
    assert doc["totals"]["turns"] == 5
    assert doc["totals"]["legs_with_rows"] == 2


def test_a_leg_that_produced_no_series_is_kept_not_dropped(arm_runs, tmp_path):
    """A campaign that spent money on a leg which produced nothing is not the
    same as a campaign with fewer legs, and concatenation is exactly where that
    difference gets quietly destroyed."""
    c = camp.Campaign(prompt_id="A3", out_dir=str(tmp_path),
                      games=["g50t-5849a774"])
    c.legs = [_leg_with_series(tmp_path, "t-a3-y1", "g50t-5849a774", 2),
              {"index": 2, "game_id": "g50t-5849a774", "slug": "t-a3-missing",
               "usd": 12.0, "turn_series_error": "ArcError: boom"},
              {"game_id": "g50t-5849a774", "event": "leg_failed",
               "error": "ArcError: boom"}]
    doc = c.campaign_series()

    assert doc["totals"]["legs_recorded"] == 3
    assert doc["totals"]["legs_with_rows"] == 1
    missing = [e for e in doc["legs"] if e.get("slug") == "t-a3-missing"][0]
    assert missing["rows"] == 0 and "boom" in missing["error"]
    assert any(e.get("event") == "leg_failed" for e in doc["legs"])


def test_a_level_boundary_and_a_carried_seed_are_marked_on_the_row(arm_runs, tmp_path):
    """C3's transfer claim is about rows on the far side of these two flags. A
    series that does not mark them cannot be read for transfer at all."""
    c = camp.Campaign(prompt_id="A3", out_dir=str(tmp_path),
                      games=["g50t-5849a774"])
    c.legs = [_leg_with_series(tmp_path, "t-a3-z1", "g50t-5849a774", 3,
                               seeded=True, boundary_turn=1)]
    rows = c.campaign_series()["rows"]

    assert [r["level_boundary"] for r in rows] == [False, True, False]
    assert all(r["seeded_from_previous_leg"] for r in rows)
    assert c.campaign_series()["totals"]["level_boundaries"] == 1


def test_a_leg_that_raises_is_charged_its_ceiling_not_zero(tmp_path):
    """A leg that spends and then raises must not be booked at $0.00.

    The desk settles each call against the shared pool as it goes, and `play()`
    re-raises after releasing the reservation, so the campaign never sees a
    summary. Booking 0.0 asserts the leg cost nothing, which lets the $60 and
    $200 ceilings under-count by the full cost of every failure. Charged at the
    leg's ceiling instead -- an upper bound, erring towards stopping early --
    and labelled so it is not mistaken for a measurement.
    """
    class _Boom(camp.Campaign):
        def run_leg(self, game_id, index, seed_books):
            raise RuntimeError("transport died mid-leg")

    c = _Boom(prompt_id="A3", out_dir=str(tmp_path), games=["g50t-5849a774"])
    report = c.run(max_legs_per_game=1)

    failed = [leg for leg in report["legs"] if leg.get("event") == "leg_failed"]
    assert failed, "the failure was not recorded at all"
    assert failed[0]["usd"] > 0.0
    assert failed[0]["cost_accounting"]["governing_source"] == \
        "leg-ceiling-upper-bound"
    assert report["spent_usd"] > 0.0
    assert report["by_game"]["g50t-5849a774"] > 0.0


def test_a_leg_that_died_before_spending_is_not_charged_a_ceiling(tmp_path):
    """The case that actually happened, on the first live attempt.

    The leg raised on a missing credential having made zero model calls, and
    the first version of this accounting booked it at the full $14 leg ceiling.
    An upper bound errs safely for a leg that died halfway; for one that never
    started it is simply a fabricated number, and it would have eaten a quarter
    of the campaign's budget on a run that did nothing.

    The shared pool settles per call and is keyed by the leg's campaign name,
    so it knows the true figure. Absent from the pool means never billed.
    """
    class _Boom(camp.Campaign):
        def run_leg(self, game_id, index, seed_books):
            # As the real one does: name the campaign, then fail.
            self._in_flight = {"campaign": "theoria-arm:test:never-billed",
                               "slug": "s", "ceiling": 14.0}
            raise RuntimeError("ARC_API_KEY is not set")

    c = _Boom(prompt_id="A3", out_dir=str(tmp_path), games=["g50t-5849a774"])
    report = c.run(max_legs_per_game=1)

    failed = [l for l in report["legs"] if l.get("event") == "leg_failed"][0]
    assert failed["usd"] == 0.0
    assert failed["cost_accounting"]["governing_source"] == \
        "gate-settled-never-spent"
    assert report["spent_usd"] == 0.0


def test_a_failed_git_lookup_says_why_instead_of_writing_a_bare_null(
        tmp_path, monkeypatch):
    """`branch` and `base_commit` are required fields, so a null in either is a
    hole in the provenance -- and the 2026-07-29 g50t campaign wrote both as
    null with nothing on disk explaining it.

    The old `_git` collapsed every failure into `None`: a thrown exception and
    a non-zero exit with empty stdout were indistinguishable from each other
    and, after `out.stdout.strip() or None`, from a repository that simply had
    no answer. Re-running the same command by hand afterwards succeeded, which
    is what makes this worth a test -- a transient failure that erases its own
    reason cannot be chased later.
    """
    camp._GIT_FAILURES.clear()
    c = _Fake([], prompt_id="A3", out_dir=str(tmp_path),
              games=["g50t-5849a774"])
    # After construction: the constructor reads the real `piles.json` under
    # REPO, and that guard is not the thing under test here.
    monkeypatch.setattr(camp, "REPO", str(tmp_path / "not-a-repo"))
    manifest = c.manifest()

    assert manifest["branch"] is None and manifest["base_commit"] is None
    gap = manifest["provenance_gap"]
    assert gap["missing_required"] == ["branch", "base_commit"]
    # The point of the whole change: a reason, not an absence.
    assert gap["why"] and gap["why"] != "no reason was recorded"
    assert any("rev-parse" in cmd for cmd in gap["why"])


def test_a_complete_manifest_carries_no_provenance_gap(tmp_path):
    """The negative control. `provenance_gap` must appear only when a required
    field is genuinely missing, or it degrades into noise that gets skimmed
    past -- which is how the null got shipped in the first place.
    """
    camp._GIT_FAILURES.clear()
    c = _Fake([], prompt_id="A3", out_dir=str(tmp_path),
              games=["g50t-5849a774"])
    manifest = c.manifest()

    assert manifest["branch"] and manifest["base_commit"]
    assert "provenance_gap" not in manifest
