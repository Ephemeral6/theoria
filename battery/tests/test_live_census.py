"""The archive census is true, reproducible -- and seen to catch its own gap.

Same shape as `test_live_tiers.py` and `test_theoria_live.py`: positive checks
first (the committed artefact matches an in-process recompute, byte for byte,
twice; the counts add up; the shape floor is read from the metric module and
not restated), then negative controls that break the arrangement in one
specific way each and require `verify.rung_live_census` to name it.

The controls that matter most here are the two the census exists for:

* a leg archive whose ledger declares this arm but carries no A3 campaign
  label is `invisible` -- present in the census with a reason, and absent
  from `theoria_live.collect`'s *both* lists.  That asymmetry is the finding
  the census encodes, so a test asserts it directly rather than trusting the
  prose;
* the pile guard reaches such a leg.  `discover` never hands it to
  `load_leg`, so before this module the sealed-pile line was checked only
  over the adapter's filtered view of the archive.  The control builds an
  unlabelled leg naming a sealed game and requires the census to raise.

No sealed game id is written into this file.  The control reads one out of
`arc-recon/data/piles.json` at run time, which is where the cut lives and the
only place it may be read from.
"""

import json
import os
import re

import pytest

from battery import verify
from battery.adapters import theoria_live
from battery.audit import live_census
from battery.guard import SealedPileError, load_piles
from battery.metrics.economy import MIN_TURNS_FOR_SHAPE


@pytest.fixture(scope="module")
def fresh():
    return live_census.build()


def _ledger(path, *, arm="theoria", campaign=None, game=None, steps=1,
            upstream="https://three.arcprize.org"):
    """A minimal but honest leg archive: run_start, env_steps, run_end."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = {"event": "run_start", "arm": arm, "game_id": game,
             "env_upstream": upstream, "run_id": "t"}
    if campaign is not None:
        start["spend_gate"] = {"campaign": campaign}
    rows = [start]
    for i in range(steps):
        rows.append({"event": "env_step", "idx": i, "ok": True})
    rows.append({"event": "run_end", "outcome": "test"})
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _dev_game():
    return load_piles().dev_pile[0]


def _sealed_game():
    """A sealed id, read from the cut at run time -- never written down here."""
    return load_piles().sealed_pile[0]


# --- the artefact itself --------------------------------------------------

def test_build_is_deterministic(fresh):
    assert live_census.build() == fresh
    assert live_census.serialise(live_census.build()) \
        == live_census.serialise(fresh)


def test_no_timestamp_no_machine_path(fresh):
    text = live_census.serialise(fresh)
    assert not re.search(r"20\d\d-\d\d-\d\dT\d", text), "a timestamp got in"
    assert "utc" not in fresh
    assert "Users" not in text and ":\\" not in text, "an absolute path got in"


def test_committed_artifact_matches_the_recompute(fresh):
    with open(live_census.DEFAULT_OUT, encoding="utf-8") as fh:
        committed = fh.read()
    assert committed == live_census.serialise(fresh), (
        "battery/artifacts_live/live_census.json is stale; regenerate with "
        "`python -m battery.audit.live_census` and commit it")


def test_every_ledger_gets_exactly_one_disposition(fresh):
    counts = fresh["counts"]
    assert sum(counts.values()) == fresh["n_with_ledger"]
    assert set(fresh["dispositions"]) == set(
        s for s in fresh["dispositions"])   # keys are the slugs, no dupes
    for slug, row in fresh["dispositions"].items():
        assert row["disposition"] in (
            "scored", "excluded", "invisible", "foreign", "unreadable"), slug


def test_scored_and_excluded_match_the_adapter(fresh):
    """The census must not hold a second opinion about what the adapter did."""
    runs, excluded = theoria_live.collect()
    assert fresh["counts"]["scored"] == len(runs)
    assert fresh["counts"]["excluded"] == len(excluded)


def test_the_invisible_legs_are_in_neither_adapter_list(fresh):
    """The finding, asserted rather than narrated: these legs are not refused,
    they are never seen -- so no recompute of either companion can move over
    them."""
    runs, excluded = theoria_live.collect()
    known = {r.run_id for r in runs} | {row["slug"] for row in excluded}
    invisible = fresh["invisible"]["slugs"]
    assert invisible, ("this tree is expected to carry pre-campaign legs; if "
                       "the arm has since labelled them, delete this "
                       "expectation deliberately, do not weaken it")
    for slug in invisible:
        assert slug not in known, slug
        row = fresh["dispositions"][slug]
        assert row["arm"] == theoria_live.ARM
        assert not (row["campaign"] or "").startswith(
            theoria_live.CAMPAIGN_PREFIX)


def test_absence_is_not_zero_in_the_money_column(fresh):
    for slug, row in fresh["dispositions"].items():
        if row["disposition"] in ("unreadable", "foreign"):
            continue
        if row["model_calls"] == 0:
            assert row["billed_usd"] is None, (
                "%s has no billed call and still carries a number" % slug)


def test_the_shape_floor_is_read_not_restated(fresh):
    floor = fresh["shape_floor"]
    assert floor["min_turns_for_shape"] == MIN_TURNS_FOR_SHAPE
    assert floor["n_scored"] == fresh["counts"]["scored"]
    for slug, row in floor["per_leg"].items():
        turns = row["decision_turns"]
        assert row["clears_floor"] == bool(
            turns is not None and turns >= MIN_TURNS_FOR_SHAPE), slug
    assert floor["n_clearing"] == len(floor["clearing"])


# --- the walk, on a synthetic archive ------------------------------------

def test_an_unlabelled_leg_is_invisible_not_dropped(tmp_path):
    root = tmp_path / "runs"
    _ledger(str(root / "no-campaign" / "ledger.jsonl"), game=_dev_game())
    doc = live_census.build(str(root))
    assert doc["counts"] == {"scored": 0, "excluded": 0, "invisible": 1,
                             "foreign": 0, "unreadable": 0}
    row = doc["dispositions"]["no-campaign"]
    assert row["disposition"] == "invisible"
    assert "never seen" in row["reason"]
    # and the adapter itself does not mention it at all -- the gap, in one line
    runs, excluded = theoria_live.collect(str(root))
    assert runs == [] and excluded == []


def test_a_foreign_arm_is_named_not_guessed(tmp_path):
    root = tmp_path / "runs"
    _ledger(str(root / "other" / "ledger.jsonl"), arm="baseline",
            game=_dev_game())
    doc = live_census.build(str(root))
    assert doc["counts"]["foreign"] == 1
    assert doc["dispositions"]["other"]["pile"] is None


def test_a_ledger_without_a_run_start_is_unreadable(tmp_path):
    root = tmp_path / "runs"
    path = root / "junk" / "ledger.jsonl"
    os.makedirs(str(path.parent))
    path.write_text('{"event": "env_step"}\n', encoding="utf-8", newline="\n")
    doc = live_census.build(str(root))
    assert doc["counts"]["unreadable"] == 1
    assert "run_start" in doc["dispositions"]["junk"]["reason"]


def test_a_directory_without_a_ledger_is_not_counted(tmp_path):
    root = tmp_path / "runs"
    os.makedirs(str(root / "analysis-only"))
    doc = live_census.build(str(root))
    assert doc["n_dirs"] == 1 and doc["n_with_ledger"] == 0


def test_the_guard_reaches_an_unlabelled_leg(tmp_path):
    """The sharp edge: `discover` never hands this leg to `load_leg`, so the
    pile guard never ran on it before this module existed."""
    root = tmp_path / "runs"
    _ledger(str(root / "unlabelled-sealed" / "ledger.jsonl"),
            game=_sealed_game())
    # the adapter is silent about it ...
    assert theoria_live.collect(str(root)) == ([], [])
    # ... and the census refuses, default deny.
    with pytest.raises(SealedPileError):
        live_census.build(str(root))


# --- the refusal ----------------------------------------------------------

def test_writing_into_the_frozen_directory_is_refused(tmp_path):
    from battery.audit.live_tiers import refuse_frozen_destination
    frozen_dir = os.path.join(verify.HERE, "artifacts")
    with pytest.raises(ValueError, match="frozen baseline"):
        refuse_frozen_destination(os.path.join(frozen_dir, "live_census.json"))
    assert refuse_frozen_destination(str(tmp_path / "ok.json"))


def test_the_cli_refuses_with_exit_2(capsys):
    target = os.path.join(verify.HERE, "artifacts", "evil_census.json")
    rc = live_census.main(["--out", target])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().out
    assert not os.path.exists(target)


# --- the rung, green ------------------------------------------------------

def test_rung_green_on_the_real_tree(capsys):
    problems = []
    verify.rung_live_census(problems)
    assert problems == [], problems
    out = capsys.readouterr().out
    assert "invisible to rungs 7 and 8" in out    # reported, exit-neutral
    assert "bill-shape floor" in out


# --- the rung, red: negative controls ------------------------------------

def test_rung_red_on_a_stale_census(tmp_path):
    doc = json.load(open(live_census.DEFAULT_OUT, encoding="utf-8"))
    doc["invisible"]["slugs"] = []               # quietly hide the gap
    doc["counts"]["invisible"] = 0
    bad = tmp_path / "live_census.json"
    bad.write_text(live_census.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_census(problems, census_path=str(bad))
    assert any("recompute" in p for p in problems), problems


def test_rung_red_when_a_row_leaves_the_development_pile(tmp_path):
    doc = json.load(open(live_census.DEFAULT_OUT, encoding="utf-8"))
    slug = sorted(doc["dispositions"])[0]
    doc["dispositions"][slug]["pile"] = "sealed"
    bad = tmp_path / "live_census.json"
    bad.write_text(live_census.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_census(problems, census_path=str(bad))
    assert any("development-pile" in p for p in problems), problems


def test_rung_red_when_the_census_and_the_readings_disagree(tmp_path):
    """Two files describing one archive may not disagree about how much of it
    was read -- the control points the census at an archive of one leg."""
    root = tmp_path / "runs"
    _ledger(str(root / "leg" / "ledger.jsonl"),
            campaign=theoria_live.CAMPAIGN_PREFIX + "-devpile",
            game=_dev_game())
    census = tmp_path / "live_census.json"
    census.write_text(live_census.serialise(live_census.build(str(root))),
                      encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_census(problems, census_path=str(census),
                            runs_root=str(root))
    assert any("disagree" in p for p in problems), problems


def test_rung_red_when_the_census_is_absent(tmp_path):
    problems = []
    verify.rung_live_census(problems,
                            census_path=str(tmp_path / "nowhere.json"))
    assert any("absent" in p for p in problems), problems


def test_rung_red_on_unparseable_census(tmp_path):
    bad = tmp_path / "live_census.json"
    bad.write_text("{not json", encoding="utf-8")
    problems = []
    verify.rung_live_census(problems, census_path=str(bad))
    assert any("not JSON" in p for p in problems), problems
