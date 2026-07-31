"""The live-arm extractor reads the archive right — and is seen to refuse.

Same shape as `test_live_tiers.py`: positives against the real committed leg
archives first (the adapter's numbers reconcile with the ledgers they came
from), then negative controls that break the arrangement one way each and
assert the refusal or the red rung by name.  A guard that has never been seen
refusing is a comment.
"""

import json
import os

import pytest

from battery import verify
from battery.adapters import theoria_live
from battery.audit import live_arm
from battery.guard import SealedPileError, load_piles

R1 = "20260731T1240Z-A3-level2-carried"
R2 = "20260731T1310Z-A3-level2-carried-r2"


@pytest.fixture(scope="module")
def piles():
    return load_piles()


@pytest.fixture(scope="module")
def runs(piles):
    return {r.run_id: r
            for r in theoria_live.load_theoria_live_runs(piles=piles)}


@pytest.fixture(scope="module")
def fresh():
    """One in-process recompute of the companion, shared across tests."""
    return live_arm.build()


# --- discovery is content-based -------------------------------------------

def test_discovery_finds_the_carried_legs(runs):
    assert R1 in runs and R2 in runs


def test_every_run_is_the_live_arm_on_the_dev_pile(runs):
    assert runs, "no live legs loaded from the committed archive"
    for run in runs.values():
        assert run.arm == "theoria"
        assert run.source == "theoria-arm-live"
        assert run.pile == "dev"
        assert run.intent == "solve"
        assert run.truth is None, "a live game has no ground truth"


def test_mock_upstream_legs_are_excluded_with_a_reason(piles):
    """`a3-gate-mock` wears the campaign label but played a local mock; it
    must be excluded, and the exclusion must say why rather than vanish."""
    loaded, excluded = theoria_live.collect(piles=piles)
    slugs = {r.run_id for r in loaded}
    assert "a3-gate-mock" not in slugs
    reasons = {e["slug"]: e["reason"] for e in excluded}
    assert "a3-gate-mock" in reasons
    assert "mock" in reasons["a3-gate-mock"]


def test_a_zero_step_leg_is_refused_not_scored(piles):
    """A8's floor, inherited: zero in a cost curve reads as `cheap`, not as
    `did not happen`.  The salvage stub is real and must stay excluded."""
    _, excluded = theoria_live.collect(piles=piles)
    reasons = {e["slug"]: e["reason"] for e in excluded}
    assert "20260729T004020Z-leg01-salvage" in reasons
    assert "0 env_step" in reasons["20260729T004020Z-leg01-salvage"]


# --- the numbers reconcile with the ledger --------------------------------

def _ledger_rows(slug):
    path = os.path.join(theoria_live.LIVE_ROOT, slug, "ledger.jsonl")
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_steps_account_for_every_env_step(runs):
    """Strict equality, both directions, like A8's own self-check: short is a
    lost step whose money was still spent, long is a step counted twice."""
    for slug in (R1, R2):
        ledger_steps = sum(1 for r in _ledger_rows(slug)
                           if r.get("event") == "env_step")
        assert len(runs[slug].steps) == ledger_steps


def test_calls_carry_the_ledger_money(runs):
    """r2 billed five CLI invocations; the Call rows must carry real dollars
    summed over every model the invocation used, not just the main line."""
    calls = runs[R2].calls
    ledger_calls = sum(1 for r in _ledger_rows(R2)
                       if r.get("event") == "model_call")
    assert len(calls) == ledger_calls
    assert sum(c.cost_usd or 0.0 for c in calls) > 1.0
    assert all(c.input_tokens + c.output_tokens + c.cache_read_tokens
               + c.cache_creation_tokens > 0 for c in calls)


def test_failed_steps_are_kept_not_dropped(runs):
    """r1's leg hit 400s all the way down; dropping those steps would flatter
    the economy family, so they stay in as failed with no state_key."""
    run = runs[R1]
    failed = [s for s in run.steps if s.failed]
    assert failed, "the r1 leg demonstrably had failing steps"
    assert all(s.state_key is None for s in failed)


def test_the_books_are_read_and_the_replay_is_certifys_last_word(runs):
    theory = runs[R2].theory
    assert theory is not None
    assert theory.clauses, "books/theory.dsl parsed to zero clauses"
    assert theory.concepts, "the word table's compress: accounts were lost"
    cert = json.load(open(os.path.join(theoria_live.LIVE_ROOT, R2,
                                       "certify.json"), encoding="utf-8"))
    replay = cert[-1]["cheap"]["checks"]["replay"]
    assert theory.replay_pairs == replay["transitions"]
    assert theory.replay_agree == replay["matched"]


def test_no_held_out_ratio_is_fabricated(runs):
    """A live leg has no held-out set; the fields must stay None and the
    frame must say so, or K2 gets compared across incomparable frames."""
    theory = runs[R2].theory
    assert theory.held_out_pairs is None and theory.held_out_agree is None
    assert "no held-out set" in (theory.held_out_frame or "").lower()


# --- the companion artefact -----------------------------------------------

def test_build_is_deterministic(fresh):
    assert live_arm.build() == fresh
    assert live_arm.serialise(live_arm.build()) == live_arm.serialise(fresh)


def test_no_timestamp_no_machine_path(fresh):
    text = live_arm.serialise(fresh)
    assert "Users" not in text and ":\\" not in text, "an absolute path got in"
    assert "utc" not in fresh


def test_committed_artifact_matches_the_recompute(fresh):
    with open(live_arm.DEFAULT_OUT, encoding="utf-8") as fh:
        committed = fh.read()
    assert committed == live_arm.serialise(fresh), (
        "battery/artifacts_live/live_arm_readings.json is stale; regenerate "
        "with `python -m battery.audit.live_arm` and commit it")


def test_the_two_families_carry_real_live_readings(fresh):
    """The sentence this material exists to support: 认识族 and 经济族 read
    real legs now, not only offline bundles and controls."""
    measured = fresh["measured_by_family"]
    assert "K1" in measured["epistemic"]
    assert measured["economy"], "no economy metric carries a live reading"
    assert fresh["n_measured_cells"] > 0


def test_the_constraint_is_stated_inside_the_artifact(fresh):
    """Measurement-only is a recorded decision, not an omission: the artefact
    itself must say the prereg is frozen and nothing here settles it."""
    assert "not confirmations" in fresh["constraint"]
    assert "PREDICTIONS.md" in fresh["what"]


# --- refusals --------------------------------------------------------------

def test_a_sealed_game_id_refuses_the_whole_load(tmp_path, piles):
    """The guard, seen refusing: a leg whose ledger names a sealed game must
    raise, not be skipped — an adapter that skips a sealed leg has learnt to
    ignore the one line it must never cross."""
    leg = tmp_path / "sealed-leg"
    leg.mkdir()
    sealed_id = sorted(piles.sealed_pile)[0]
    row = {"event": "run_start", "arm": "theoria", "game_id": sealed_id,
           "env_upstream": "https://three.arcprize.org",
           "spend_gate": {"campaign":
                          "theoria-arm:A3-campaign-devpile:x:sealed-leg"}}
    (leg / "ledger.jsonl").write_text(json.dumps(row) + "\n",
                                      encoding="utf-8", newline="\n")
    with pytest.raises(SealedPileError):
        theoria_live.collect(str(tmp_path), piles=piles)


def test_writing_into_the_frozen_directory_is_refused(tmp_path):
    frozen_dir = os.path.join(live_arm.BATTERY, "artifacts")
    with pytest.raises(ValueError, match="frozen baseline"):
        live_arm.write(os.path.join(frozen_dir, "live_arm_readings.json"))
    rc = live_arm.main(["--out", os.path.join(frozen_dir, "evil.json")])
    assert rc == 2
    assert not os.path.exists(os.path.join(frozen_dir, "evil.json"))


# --- the rung, green then red ---------------------------------------------

def test_rung_green_on_the_real_tree(capsys):
    problems = []
    verify.rung_live_arm(problems)
    assert problems == [], problems
    out = capsys.readouterr().out
    assert "live leg(s)" in out


def test_rung_red_on_a_tampered_companion(tmp_path):
    """Staleness is the failure class the rung exists for."""
    doc = json.load(open(live_arm.DEFAULT_OUT, encoding="utf-8"))
    doc["n_measured_cells"] = doc["n_measured_cells"] + 1
    bad = tmp_path / "live_arm_readings.json"
    bad.write_text(live_arm.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_arm(problems, live_path=str(bad))
    assert any("recompute" in p for p in problems), problems


def test_rung_red_on_a_non_dev_row(tmp_path):
    """The gate re-reads the committed rows rather than trusting the
    generator: a row claiming a non-dev pile must go red even if the
    recompute half were somehow satisfied."""
    doc = json.load(open(live_arm.DEFAULT_OUT, encoding="utf-8"))
    slug = sorted(doc["runs"])[0]
    doc["runs"][slug]["game_id"] = "nonexistent-game"
    bad = tmp_path / "live_arm_readings.json"
    bad.write_text(live_arm.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_arm(problems, live_path=str(bad))
    assert any("development-pile" in p for p in problems), problems


def test_rung_red_when_the_companion_is_absent(tmp_path):
    problems = []
    verify.rung_live_arm(problems, live_path=str(tmp_path / "nowhere.json"))
    assert any("absent" in p for p in problems), problems


def test_rung_red_on_unparseable_companion(tmp_path):
    bad = tmp_path / "live_arm_readings.json"
    bad.write_text("{not json", encoding="utf-8")
    problems = []
    verify.rung_live_arm(problems, live_path=str(bad))
    assert any("not JSON" in p for p in problems), problems
