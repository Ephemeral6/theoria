"""The replay spot check, and the refusal-compaction rule added for game 2.

`replay_spotcheck.py` shipped with P-9 and carried no tests: it was run once
by hand, its output archived, and the archive treated as the evidence. That
held until a third harness turned up. `theoria-arm`'s live legs of 2026-07-31
are canonical v1.0 ledgers, and the tool read *zero* sessions out of them --
`INSUFFICIENT`, silently, with exit 1 and an empty session list, which is
indistinguishable from "these ledgers contain nothing".

The cause is the arm's retry shape: a refused command gets its own `env_step`
at its own `step_idx`, so a leg with 34 usable frames burns 234 indices, and
index 0 is a refusal in every leg. "Truncate at the first failed step" then
truncates at the first step.

These tests pin both halves of the fix and, more importantly, the three
things that must NOT move:

* the strict path is byte-identical to what the archived reports contain, so
  P-9's ar25 check and the closeout g50t check still reproduce;
* the compactable set is a closed whitelist -- an unrecognised failure still
  truncates, and no amount of it being obviously-probably-harmless changes
  that;
* compaction cannot manufacture agreement. It re-indexes positions, and every
  position still requires the same command in every session and the same
  frame hash from every session.

    cd proxy && python -m pytest tests/test_replay_spotcheck.py
"""

import json
import os

import pytest

from proxy.tools import replay_spotcheck as rs

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# -- helpers ----------------------------------------------------------------

def step(idx, action, frame_hash, ok=True, refusal=None):
    return {"step_idx": idx, "action": action, "frame_hash": frame_hash,
            "ok": ok, "refusal": refusal}


def refusal(idx, action, shape="game-not-found"):
    return step(idx, action, None, ok=False, refusal=shape)


def canon_row(run_id, idx, name, status=200, frames=("f",), n_frames=1,
              response=None, game="g50t-5849a774"):
    return {
        "v": "1.0", "event": "env_step", "run_id": run_id, "game_id": game,
        "step_idx": idx, "action": {"name": name, "id": None, "data": None},
        "http": {"status": status}, "frames": list(frames) if frames else None,
        "n_frames": n_frames, "frame_hash": None if frames is None else
        "sha256:%s-%d" % (name, idx), "response": response,
    }


def write_ledger(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return str(path)


# -- the whitelist is closed ------------------------------------------------

NOT_FOUND = {"error": "SERVER_ERROR", "message": "game g50t-5849a774 not found"}


def test_the_one_recognised_refusal_shape():
    record = canon_row("r", 0, "RESET", status=400, frames=None, n_frames=0,
                       response=NOT_FOUND)
    assert rs.non_executing_refusal(record) == "game-not-found"


@pytest.mark.parametrize("mutation, why", [
    ({"http": {"status": 500}}, "a 500 is not a 400"),
    ({"frames": ["f"]}, "a refusal that returned a frame is not a refusal"),
    ({"n_frames": 1}, "n_frames must corroborate the empty frame list"),
    ({"response": {"error": "RATE_LIMIT", "message": "slow down"}},
     "another error class says nothing about whether the action ran"),
    ({"response": {"error": "SERVER_ERROR", "message": "internal error"}},
     "a SERVER_ERROR with a different message is a different failure"),
    ({"response": None}, "no response body means no evidence"),
    ({"response": "game g50t-5849a774 not found"},
     "a bare string is not the documented shape"),
])
def test_everything_else_is_not_compactable(mutation, why):
    record = canon_row("r", 0, "RESET", status=400, frames=None, n_frames=0,
                       response=NOT_FOUND)
    record.update(mutation)
    assert rs.non_executing_refusal(record) is None, why


def test_a_near_miss_message_is_not_matched():
    """`^game \\S+ not found$` is anchored on both ends deliberately: a
    message that merely *contains* the phrase is a message we did not write
    the whitelist for."""
    record = canon_row("r", 0, "RESET", status=400, frames=None, n_frames=0,
                       response={"error": "SERVER_ERROR",
                                 "message": "game g50t not found in cache; "
                                            "the action was applied anyway"})
    assert rs.non_executing_refusal(record) is None


# -- clean_prefix: strict is unchanged, compaction re-indexes ---------------

def test_strict_truncates_at_the_first_refusal():
    steps = [refusal(0, "RESET"), step(1, "RESET", "h0"),
             step(2, "ACTION1", "h1")]
    prefix, compacted = rs.clean_prefix(steps)
    assert prefix == [] and compacted == {}


def test_compaction_drops_the_refusal_and_renumbers_positions():
    steps = [refusal(0, "RESET"), step(1, "RESET", "h0"),
             refusal(2, "ACTION1"), step(3, "ACTION1", "h1")]
    prefix, compacted = rs.clean_prefix(steps, compact_refusals=True)
    assert [s["action"] for s in prefix] == ["RESET", "ACTION1"]
    assert compacted == {"game-not-found": 2}


def test_compaction_still_stops_at_an_unrecognised_failure():
    steps = [refusal(0, "RESET"), step(1, "RESET", "h0"),
             step(2, "ACTION1", None, ok=False, refusal=None),
             step(3, "ACTION2", "h2")]
    prefix, _ = rs.clean_prefix(steps, compact_refusals=True)
    assert [s["action"] for s in prefix] == ["RESET"]


def test_contiguity_is_checked_over_the_raw_index_even_under_compaction():
    """A dropped row still has to be paid for by a refusal AT that index.

    Without this the compacting reader would happily accept 0,1,5,6 and put
    the step at index 5 in position 2 -- the g50t precheck's hole bug, back
    again with a new cause. `seen` counts raw indices, not retained ones.
    """
    steps = [refusal(0, "RESET"), step(1, "RESET", "h0"),
             step(5, "ACTION1", "h1")]
    prefix, _ = rs.clean_prefix(steps, compact_refusals=True)
    assert [s["action"] for s in prefix] == ["RESET"]


def test_a_session_that_is_all_refusals_yields_nothing_not_a_pass():
    prefix, compacted = rs.clean_prefix(
        [refusal(0, "RESET"), refusal(1, "RESET")], compact_refusals=True)
    assert prefix == []
    assert compacted == {"game-not-found": 2}


# -- spotcheck: compaction cannot manufacture agreement ---------------------

def test_compaction_does_not_hide_a_disagreement():
    sessions = {
        "a": [refusal(0, "RESET"), step(1, "RESET", "SAME"),
              step(2, "ACTION1", "LEFT")],
        "b": [step(0, "RESET", "SAME"), refusal(1, "ACTION1"),
              step(2, "ACTION1", "RIGHT")],
    }
    report = rs.spotcheck(sessions, "g50t-5849a774", compact_refusals=True)
    assert report["verdict"] == "FAIL"
    assert report["disagreements"][0]["position"] == 1
    assert report["disagreements"][0]["distinct_hashes"] == ["LEFT", "RIGHT"]


def test_the_report_says_how_much_it_compacted():
    sessions = {
        "a": [refusal(0, "RESET"), step(1, "RESET", "SAME")],
        "b": [step(0, "RESET", "SAME")],
    }
    report = rs.spotcheck(sessions, "g50t-5849a774", compact_refusals=True)
    assert report["verdict"] == "PASS"
    assert report["policy"]["refusals_compacted"] == {"a": {"game-not-found": 1}}
    assert report["policy"]["compactable_shapes"] == ["game-not-found"]


def test_the_strict_report_carries_no_policy_block():
    """The archived reports were hashed in their manifests before this flag
    existed; the strict path must still produce those bytes."""
    sessions = {"a": [step(0, "RESET", "SAME")], "b": [step(0, "RESET", "SAME")]}
    report = rs.spotcheck(sessions, "g50t-5849a774")
    assert "policy" not in report
    assert rs.spotcheck(sessions, "g50t-5849a774", True)["policy"]


def test_one_session_is_still_insufficient_under_compaction():
    sessions = {"a": [refusal(0, "RESET"), step(1, "RESET", "h")]}
    report = rs.spotcheck(sessions, "sk48-d8078629", compact_refusals=True)
    assert report["verdict"] == "INSUFFICIENT"
    assert report["policy"]["refusals"] == "compacted"


# -- end to end through a ledger file ---------------------------------------

def test_an_arm_shaped_ledger_is_unreadable_strict_and_readable_compacted(
        tmp_path):
    """The regression this whole flag exists for, in miniature.

    Two runs, each opening with a refused RESET that got its own step_idx,
    then the same three commands returning the same frames. Strict reading
    sees nothing at all; that silence -- not a wrong answer, an empty one --
    is what made the gap easy to miss.
    """
    rows = []
    for run_id in ("r-one", "r-two"):
        rows.append(canon_row(run_id, 0, "RESET", status=400, frames=None,
                              n_frames=0, response=NOT_FOUND))
        for idx, name in enumerate(("RESET", "ACTION1", "ACTION2"), start=1):
            rows.append(canon_row(run_id, idx, name))
    path = write_ledger(tmp_path / "ledger.jsonl", rows)

    sessions = rs.sessions_from_canon(path, "g50t-5849a774")
    assert sorted(sessions) == ["r-one", "r-two"]

    strict = rs.spotcheck(sessions, "g50t-5849a774")
    assert strict["verdict"] == "INSUFFICIENT"
    assert strict["sessions"] == []

    compacted = rs.spotcheck(sessions, "g50t-5849a774", compact_refusals=True)
    assert compacted["verdict"] == "PASS"
    assert compacted["steps_compared"] == 3
    assert compacted["pairwise_comparisons"] == 3
    assert compacted["disagreements"] == []


def test_main_wires_the_flag_and_records_the_source_of_each_session(tmp_path):
    rows = []
    for run_id in ("r-one", "r-two"):
        rows.append(canon_row(run_id, 0, "RESET", status=400, frames=None,
                              n_frames=0, response=NOT_FOUND))
        rows.append(canon_row(run_id, 1, "RESET"))
    path = write_ledger(tmp_path / "ledger.jsonl", rows)
    out = tmp_path / "report.json"

    assert rs.main(["--game", "g50t-5849a774", "--canon", path]) == 1
    assert rs.main(["--game", "g50t-5849a774", "--compact-refusals",
                    "--canon", path, "-o", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["verdict"] == "PASS"
    assert report["session_origin"] == {"r-one": path, "r-two": path}


ARCHIVED_REPORTS = [
    "runs/p9-shell-harden/replay_spotcheck_ar25.json",
    "runs/20260731T154336Z-P1-replay-spotcheck-2/replay_spotcheck_g50t.json",
    "runs/20260731T154336Z-P1-replay-spotcheck-2/"
    "replay_spotcheck_ar25_regression.json",
]

PROXY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("relative", ARCHIVED_REPORTS)
def test_the_archived_reports_still_match_the_shape_this_code_emits(relative):
    """The archived reports were produced by the pre-flag code and hashed in
    their manifests. Their inputs are not all in the repository (the lifted
    canonical ledgers are ~33 MB and were never archived), so the reports
    cannot simply be regenerated here -- which is exactly why the shape is
    worth pinning: a key silently added to the strict path would make every
    one of those manifests unreproducible, and nobody would find out until
    somebody tried."""
    path = os.path.join(PROXY, relative)
    if not os.path.exists(path):
        pytest.skip("%s not in this checkout" % relative)
    archived = json.loads(open(path, encoding="utf-8").read())

    sessions = {"a": [step(0, "RESET", "SAME")], "b": [step(0, "RESET", "SAME")]}
    emitted = rs.spotcheck(sessions, archived["game_id"])
    emitted["sources"] = {"canon": [], "recon": None}
    assert set(emitted) == set(archived), (
        "the strict report's key set moved; %s can no longer be reproduced"
        % relative)
    assert set(emitted["comparisons"][0]) <= set(archived["comparisons"][0])


# -- the live legs, read from the repository --------------------------------

ARM_LEGS = [
    "theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl",
    "theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl",
    "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl",
]

#: Position-by-position frame hashes from
#: `proxy/runs/20260731T154336Z-P1-replay-spotcheck-2/replay_spotcheck_g50t.json`
#: -- 26 baseline-arms sessions, a different harness, a different campaign.
#: The arm's live legs have to land on these exact values or one of the two
#: measurements is not measuring what it says.
BASELINE_G50T_PREFIX = [
    ("RESET", "sha256:801726dc499f3f52f79a7a69f2720fcd308dbe625cbf9eb760442f71c298fba7"),
    ("ACTION1", "sha256:801726dc499f3f52f79a7a69f2720fcd308dbe625cbf9eb760442f71c298fba7"),
    ("ACTION2", "sha256:e665977d6ad439ffb07bb1613e5bdae5caab80b8d4eb7e5eeccc57e2a4a97dc7"),
    ("ACTION3", "sha256:0752f8b0c82bd16302700744e621d0b692c3719dd0964adbcfe74f8e6fdc9cd4"),
    ("ACTION4", "sha256:5cc8add00a5dcfbcb2d4c171652b36cb9a572d7decadbccc533d06d378981257"),
    ("ACTION5", "sha256:dd5deaacbac46e31e5b548f587cab2a91f4b73da110aa1319cb5b7c17905a250"),
]


@pytest.mark.skipif(not all(os.path.exists(os.path.join(REPO, p))
                            for p in ARM_LEGS),
                    reason="theoria-arm live legs not present in this checkout")
def test_the_three_live_g50t_legs_agree_byte_for_byte():
    sessions = {}
    for leg in ARM_LEGS:
        sessions.update(rs.sessions_from_canon(os.path.join(REPO, leg),
                                               "g50t-5849a774"))
    assert len(sessions) == 3

    assert rs.spotcheck(sessions, "g50t-5849a774")["verdict"] == "INSUFFICIENT"

    report = rs.spotcheck(sessions, "g50t-5849a774", compact_refusals=True)
    assert report["verdict"] == "PASS"
    assert report["n_sessions"] == 3
    assert report["steps_compared"] == 10
    assert report["disagreements"] == []
    # 87% of the rows in these legs are refusals; the count is part of the
    # finding, not an implementation detail.
    assert sum(c["game-not-found"] for c in
               report["policy"]["refusals_compacted"].values()) == 339

    observed = [(c["action"], c["frame_hash"]) for c in report["comparisons"]]
    assert observed[:len(BASELINE_G50T_PREFIX)] == BASELINE_G50T_PREFIX, (
        "the live legs must reproduce the frame hashes the baseline-arms "
        "campaign recorded through a different harness")
