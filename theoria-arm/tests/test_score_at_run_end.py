"""A18 -- the run scores itself when it ends, and says so out loud.

`Theoria.md:371` asks for 跑完一局即打分 and Phase 1 (5) for 逐局跑完即打分入库、
与 scorecard 对账. The frozen scorer has existed and been correct for a while
(37 archived runs replayed through it, this arm's four live legs all PASS), and
**no arm had ever called it from a run**. A sweep afterwards is the thing those
lines forbid: Phase 3 audits the order results arrive in, and a batch scored
later is a batch somebody could have scored after seeing it.

So the assertions here are about *the harness*, not about the scorer:

  * a mock game, played end to end, lands a verdict in its own run directory
    and in `run.json` -- without anyone asking for one afterwards;
  * a **coherent forgery** -- a scorecard whose own arithmetic adds up, and
    which only the ledger contradicts -- comes back red and leaves an
    `incident` behind. This is the negative control: without it, "the verdict
    was PASS" would only be evidence that nothing was checked;
  * the two ways an honest run has no answer -- no scorecard, and a scorer that
    could not run at all -- come back `UNDETERMINED`, never `PASS`, and never
    as a traceback out of the harness. `baseline-arms` lost 22 of 23 scorecards
    silently; a harness that swallowed the loss would reproduce exactly that;
  * `main()` forwards `ledger_path`, which is the whole of the config-only gap
    in `proxy/DELIVERY_RULING.md` §4 axis 1.

Everything runs against `proxy/mock`: no key, no network, no model call, and
the spend claim is on a pool each test owns.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401

from harness import run as run_mod                      # noqa: E402

GAME = "g50t-5849a774"                                  # development pile


def _own_pool(tmp_path):
    """A spend pool this test owns, so the fleet's does not get billed.

    `play()` defaults `spend_gate=None`, which resolves to the pool every
    session shares -- the one whose action ceiling decides whether the sealed
    confirmation run can still afford to happen. Tests that forgot this wrote
    2 817 of its 4 775 actions.
    """
    from proxy.spend_gate import SpendGate               # noqa: PLC0415

    policy = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    return SpendGate(policy), {
        "pool": policy.pool,
        "ledger_abspath": os.path.abspath(policy.ledger_path)}


class _Wrapped:
    """The real arm, with one thing done to its closing summary.

    Only `play()` and `summary()` are reached from `harness.run.play`, so a
    wrapper is enough and the arm itself stays untouched -- the run really is
    played, the ledger really is the writer's, and the only planted thing is
    the number the forgery is about.

    Both are doctored, because `play()` merges the two and its own return wins:
    a first draft that patched only `summary()` planted a forgery that never
    reached the ledger, and the negative control passed by scoring a clean run.
    """

    def __init__(self, inner, doctor):
        self.inner = inner
        self.doctor = doctor

    def play(self):
        return self.doctor(dict(self.inner.play()))

    def summary(self):
        return self.doctor(dict(self.inner.summary()))


def _forge_actions(summary, by=3):
    """Add `by` actions to the scorecard, coherently.

    Every number on the card that has to agree with another number on the card
    is moved together: the run's, its environment's, and the card total. So
    S-10 ("the card's totals agree with its own environments") still passes and
    the card is internally perfect. The only witness left is the ledger, which
    is the point -- a forgery a scorecard can catch by itself needs no
    reconciliation, and reconciliation is what this ticket wires in.
    """
    if not summary.get("scorecard"):
        return summary
    card = json.loads(json.dumps(summary["scorecard"]))
    card["total_actions"] = (card.get("total_actions") or 0) + by
    for env in card.get("environments") or []:
        env["actions"] = (env.get("actions") or 0) + by
        for run in env.get("runs") or []:
            run["actions"] = (run.get("actions") or 0) + by
    summary["scorecard"] = card
    return summary


def _drop_card(summary):
    summary.pop("scorecard", None)
    return summary


def _play(tmp_path, *, doctor=None, actions=6, **kwargs):
    """One mock game, end to end, through the real `play()`."""
    from inner.loop import TheoriaArm                    # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc  # noqa: PLC0415

    slug = "pytest-a18-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        arm = TheoriaArm(env_base=env_base, run=run, game_id=GAME,
                         budget_actions=actions, offline=True)
        return arm if doctor is None else _Wrapped(arm, doctor)

    gate, expect = _own_pool(tmp_path)
    with MockArc(api_key=DEFAULT_KEY, games=[GAME]) as mock:
        summary = run_mod.play(
            GAME, slug, factory, env_upstream=mock.base_url,
            env_key=DEFAULT_KEY, require_key=False,
            spend_gate=gate, expect_pool=expect,
            # Not `runs/`: that is the archive, and a fixture landing in it is
            # indistinguishable by directory listing from a game that cost
            # money. Not `proxy/var/scores/` either, for the same reason one
            # directory over.
            runs_root=run_mod.FIXTURE_RUNS_DIR,
            scores_dir=str(tmp_path / "scores"),
            ledger_path=str(tmp_path / "ledger.jsonl"), **kwargs)
    return summary, os.path.join(run_mod.FIXTURE_RUNS_DIR, slug)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _records(tmp_path, run_id):
    from proxy.ledger import read_ledger                 # noqa: PLC0415

    return [r for r in read_ledger(str(tmp_path / "ledger.jsonl"))
            if r["run_id"] == run_id]


# --------------------------------------------------------------- the positive
def test_a_finished_mock_game_scores_itself_and_files_the_verdict(tmp_path):
    """The whole ticket in one run: nobody scores this afterwards."""
    summary, run_dir = _play(tmp_path)

    report = _read(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))
    assert report["verdict"] == "PASS", report.get("failed_checks")
    assert report["run_id"] == summary["run_id"]
    assert summary["score_verdict"] == "PASS"

    # The number is traceable to the rule that produced it (SCORING.md §1):
    # which scorer, which version, which bytes -- and the freeze verified, or
    # `score_run` would have refused to produce a number at all.
    assert report["scorer"]["id"] == "arc_v1"
    assert report["scorer"]["sha256"].startswith("sha256:")

    # Every check ran against a real card rather than being skipped, and the
    # one this arm's budget arithmetic depends on is among them.
    verdicts = {c["id"]: c["verdict"] for c in report["checks"]}
    assert verdicts["S-0"] == "PASS"                    # a card was captured
    assert verdicts["S-1"] == "PASS"                    # actions reconcile
    assert set(verdicts.values()) == {"PASS"}

    # It is in the run record too, not only beside it.
    run_json = _read(os.path.join(run_dir, "run.json"))
    assert run_json["score"]["verdict"] == "PASS"
    assert run_json["score"]["scorer"]["id"] == "arc_v1"

    # The scoring layer's own copy landed where this run was told to put it.
    assert _read(str(tmp_path / "scores" / (summary["run_id"] + ".json"))) \
        ["verdict"] == "PASS"

    # A clean reconciliation is not an event: nothing was appended after the
    # run closed, so `run_end` is still the last word.
    events = [r["event"] for r in _records(tmp_path, summary["run_id"])]
    assert events[-1] == "run_end"
    assert "incident" not in events


# --------------------------------------------------------------- the negative
def test_a_planted_score_mismatch_comes_back_red(tmp_path):
    """The negative control. A card that agrees with itself and not with the
    ledger must go FAIL and leave a record behind.

    Without this the positive test above proves only that something wrote the
    word PASS. The forgery is coherent on purpose -- it survives every check
    that reads the card alone, and dies on the one that reads the card against
    the run.
    """
    summary, run_dir = _play(tmp_path, doctor=_forge_actions)

    report = _read(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))
    assert report["verdict"] == "FAIL"
    assert summary["score_verdict"] == "FAIL"
    assert report["failed_checks"] == ["S-1"]

    # It failed for the stated reason and not for some other one: the card's
    # own arithmetic is still perfect, and the disagreement is 9 against 6.
    checks = {c["id"]: c for c in report["checks"]}
    assert checks["S-10"]["verdict"] == "PASS"          # coherent forgery
    assert checks["S-12"]["verdict"] == "PASS"          # canonical records
    assert checks["S-1"]["scorecard"] == checks["S-1"]["ledger"] + 3

    # And the ledger carries the complaint. §5 of LEDGER_FORMAT.md keeps the
    # score itself out of the ledger; the failure is what belongs in it.
    records = _records(tmp_path, summary["run_id"])
    incidents = [r for r in records if r["event"] == "incident"]
    assert [r["kind"] for r in incidents] == ["score_mismatch"]
    assert "S-1" in incidents[0]["detail"]
    # After `run_end`, never instead of it: the ledger is append-only and a
    # later record must not be able to replace an earlier verdict.
    assert [r["event"] for r in records][-2:] == ["run_end", "incident"]

    run_json = _read(os.path.join(run_dir, "run.json"))
    assert run_json["score"]["verdict"] == "FAIL"


def test_the_same_run_without_the_forgery_is_green(tmp_path):
    """Non-vacuity for the control above: the only difference is the three
    actions added to the card."""
    summary, run_dir = _play(tmp_path)
    assert _read(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))["verdict"] == "PASS"
    assert not [r for r in _records(tmp_path, summary["run_id"])
                if r["event"] == "incident"]


# ------------------------------------------------------------- degrade, don't
def test_a_run_with_no_scorecard_is_undetermined_and_not_pass(tmp_path):
    """`UNDETERMINED` is not `PASS` (SCORING.md §4). A scorer that answered
    PASS for "nothing to compare" would reproduce baseline-arms' 22 silently
    lost cards exactly."""
    summary, run_dir = _play(tmp_path, doctor=_drop_card)

    report = _read(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))
    assert report["verdict"] == "UNDETERMINED"
    assert "S-0" in report["undetermined_checks"]
    assert summary["score_verdict"] == "UNDETERMINED"

    # An obligation that could not be discharged is recorded, not dropped.
    incidents = [r for r in _records(tmp_path, summary["run_id"])
                 if r["event"] == "incident"]
    assert [r["kind"] for r in incidents] == ["score_unreconciled"]

    # And the run itself still finished normally -- the game was played, the
    # actions were spent and counted.
    assert summary["budget"]["actions_ok"] == 6


def test_a_scorer_that_cannot_run_at_all_does_not_take_the_run_down(
        tmp_path, monkeypatch):
    """The harness's own failure mode. `score_run` raises on a freeze that no
    longer verifies -- and a run that has already spent its actions must not
    lose its record over the scoring of it."""
    from proxy import scoring                            # noqa: PLC0415

    def refuse(*a, **kw):
        raise scoring.ScorerDriftError("arc_v1.py hashes to sha256:dead...")

    monkeypatch.setattr(scoring, "score_run", refuse)
    summary, run_dir = _play(tmp_path)

    assert summary["outcome"] != "raised"
    report = _read(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))
    assert report["verdict"] == "UNDETERMINED"
    assert report["undetermined_checks"] == ["S-H0"]
    assert "ScorerDriftError" in report["error"]
    assert report["incident_filed"] is True

    incidents = [r for r in _records(tmp_path, summary["run_id"])
                 if r["event"] == "incident"]
    assert [r["kind"] for r in incidents] == ["score_unreconciled"]

    # run.json is still written, and it says the score is not to be trusted
    # rather than omitting the question.
    assert _read(os.path.join(run_dir, "run.json"))["score"]["verdict"] == \
        "UNDETERMINED"


def test_without_the_wiring_the_run_has_no_verdict_at_all(tmp_path):
    """Non-vacuity for the whole file. `score=False` is the state this arm was
    in until A18: the game is played, the ledger is complete, `run.json` is
    written -- and nothing anywhere says whether the numbers agree."""
    summary, run_dir = _play(tmp_path, score=False)

    assert not os.path.exists(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))
    assert summary["score_verdict"] is None
    assert _read(os.path.join(run_dir, "run.json"))["score"] is None


# ------------------------------------------------------ where the copies land
def test_a_rehearsals_score_does_not_land_in_the_shared_index():
    """`proxy/var/scores/` is the index that accompanies the shared ledger. The
    artefact is always written -- production semantics -- but a run that is not
    archive material writes it beside itself, for the reason `FIXTURE_RUNS_DIR`
    exists one directory over."""
    assert run_mod._scores_dir_for(None) is None         # the archive: shared
    assert run_mod._scores_dir_for(run_mod.RUNS_DIR) is None
    fixture = run_mod._scores_dir_for(run_mod.FIXTURE_RUNS_DIR)
    assert fixture == os.path.join(os.path.abspath(run_mod.FIXTURE_RUNS_DIR),
                                   "scores")


# ------------------------------------------- DELIVERY_RULING.md §4 axis 1
def test_main_forwards_the_ledger_path_and_defaults_a_live_leg_to_the_shared_one(
        tmp_path, monkeypatch):
    """The config-only gap, closed and pinned.

    `Run` and `play()` have taken `ledger_path` since they were written and
    `main()` never passed it, so this arm's records had no route into
    `proxy/var/ledger.jsonl` however it was invoked -- which is the entire
    reason axis 1 reads zero. No game is played here: `play` is replaced, so
    the assertion is about what `main()` decides, at zero cost.
    """
    from proxy.paths import LEDGER_PATH                  # noqa: PLC0415

    seen = {}

    def capture(game_id, slug, factory, **kwargs):
        seen.clear()
        seen.update(kwargs)
        return {"outcome": "captured", "run_id": "r-capture"}

    monkeypatch.setattr(run_mod, "play", capture)
    pool = str(tmp_path / "scratch-pool.jsonl")

    # A live leg: the shared ledger, by default and without a flag.
    assert run_mod.main(["--game", GAME, "--pool", pool, "--budget", "1"]) == 0
    assert seen["ledger_path"] == LEDGER_PATH

    # A rehearsal: its own run directory, so a mock run cannot make axis 1 read
    # as satisfied by a run that never left this machine.
    assert run_mod.main(["--mock", "--game", GAME, "--pool", pool,
                         "--budget", "1"]) == 0
    assert seen["ledger_path"] is None

    # And an explicit path wins over both.
    explicit = str(tmp_path / "elsewhere.jsonl")
    assert run_mod.main(["--mock", "--game", GAME, "--pool", pool,
                         "--budget", "1", "--ledger", explicit]) == 0
    assert seen["ledger_path"] == explicit


def test_the_cli_really_writes_where_it_was_told(tmp_path):
    """The forwarding above, exercised rather than captured: one whole mock
    game through `main()`, and the records are in the named file."""
    from proxy.ledger import read_ledger                 # noqa: PLC0415

    ledger_path = str(tmp_path / "cli-ledger.jsonl")
    code = run_mod.main([
        "--mock", "--game", GAME, "--budget", "2",
        "--pool", str(tmp_path / "scratch-pool.jsonl"),
        "--ledger", ledger_path,
        "--runs-root", run_mod.FIXTURE_RUNS_DIR,
        "--slug", "pytest-a18cli-" + os.path.basename(str(tmp_path))])
    assert code == 0

    records = read_ledger(ledger_path)
    assert [r["event"] for r in records][0] == "run_start"
    assert {r["arm"] for r in records} == {"theoria"}
    # ... and the run scored itself on the way out, through the CLI too.
    run_dir = os.path.join(run_mod.FIXTURE_RUNS_DIR,
                           "pytest-a18cli-" + os.path.basename(str(tmp_path)))
    assert _read(os.path.join(run_dir, run_mod.SCORE_ARTEFACT))["verdict"] \
        in ("PASS", "UNDETERMINED")


def test_the_scorer_is_reached_through_the_package_not_reimplemented():
    """One scorer, shared by every arm (Theoria.md Phase 1, 同壳). A copy in
    this territory would be a second scorer with one name, and the numbers of
    two arms would stop being comparable -- which is the entire experiment."""
    source = open(os.path.join(ARM, "harness", "run.py"), encoding="utf-8").read()
    assert "from proxy import scoring" in source
    for reimplementation in ("def score(", "SCORER_ID", "CALIBRATION"):
        assert reimplementation not in source, reimplementation


def test_a_run_scores_under_production_semantics_not_audit_semantics(
        tmp_path, monkeypatch):
    """`proxy/DELIVERY_RULING.md` §5: `--no-incident/--no-artifact` exist so
    that *looking* at a ledger does not modify it -- running the auditor with
    incidents on twice is how six duplicate records got into the shared ledger.
    A **run** with them off is the opposite mistake and the more expensive one:
    its mismatch would be recorded nowhere. Asserted on the call itself rather
    than on the source text, because the spelling is not the property."""
    from proxy import scoring                            # noqa: PLC0415

    seen = {}
    real = scoring.score_run

    def spy(run_id, **kwargs):
        seen.update(kwargs)
        return real(run_id, **kwargs)

    monkeypatch.setattr(scoring, "score_run", spy)
    _play(tmp_path)

    assert seen["write_incident"] is True
    assert seen["write_artifact"] is True
