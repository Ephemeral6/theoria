"""`win_tighten` on a game that reports no score: the two paths, and the guard.

The finding this pins is `exam/SEALED_DRILL.md` §4. On a world that keeps no
score, `win_tighten` rewrote every `WIN` to `NOT_FINISHED` at every requirement
value -- it did not tighten the win condition, it abolished it -- and the
`applied` record it left behind was indistinguishable from an honest shortfall.

Two whole runs are played here rather than hand-built bodies, because the claim
is about what a *session* leaves in the ledger:

  * `scoreless_run` -- the mock reports `score: null` throughout;
  * `scoring_run`   -- the mock scores normally and the requirement is set high
    enough that `win_tighten` fires anyway, for a shortfall.

Both are put in front of the guard, and both are falsified: the scoreless one is
refused and then *passed* once the marker is stripped, and the scoring one is
passed and then *refused* once a marker is forged into it. A guard only ever
seen to fire on one kind of session is not a negative control (D-014); it is a
guard that might be reacting to the session rather than to the defect.
"""

import contextlib
import copy
import json
import types

import pytest

from proxy import redact
from proxy.ledger import INCIDENT_KINDS, read_ledger
from proxy.mock.arc_mock import DEFAULT_GAME, DEFAULT_KEY as ARC_KEY, MockArc
from proxy.mock.model_mock import DEFAULT_KEY as MODEL_KEY, MockProvider
from proxy.runner import run_game
from proxy.tools.check_variant_degeneracy import main as check_main, scan_records
from proxy.variants import (DEGENERATE_NOTE, REASON_ABSENT, REASON_BELOW,
                            Variant, VariantRuntime)


def _variant(require, variant_id):
    return Variant({
        "variant_id": variant_id,
        "base_game": DEFAULT_GAME,
        "claim": "unsolvable",
        "operators": [{"op": "win_tighten",
                       "require": {"kind": "score_at_least", "value": require}}],
        "justification": "The server's win is kept but a score floor is added on "
                         "top of it, so the tightened win is a strict subset of "
                         "the original one.",
    })


@contextlib.contextmanager
def _vault_without_toy_secrets():
    """Hold the process-wide redaction vault to secrets of a credible length
    for the duration of a run.

    Not a convenience. `redact.VAULT` is process-global and never cleared;
    `Vault.scrub` scrubs dictionary **keys** as well as values (RED-17); and
    `register(force=True)` deliberately ignores the length floor so that a
    short real credential is still protected (RED-14). Each of those three is
    right on its own. Together, one neighbour in this suite --
    `test_spend_gate.py`, which builds an `EnvProxyConfig(api_key="k")` -- makes
    every later ledger in the same process write `<redacted>ind` where the
    canon says `kind`. It is why these two incident assertions passed alone and
    failed in suite order, and it is a defect in `redact.py` rather than in
    anything V22 touched: a genuinely short live key would corrupt field names
    in a real ledger the same way. Filed separately; worked around here rather
    than fixed under a ticket that is about `win_tighten`, and worked around by
    dropping only sub-`MIN_SECRET_LEN` entries, so every real credential this
    run uses stays registered and the seal these tests run under is unchanged.
    """
    saved = list(redact.VAULT._secrets)
    redact.VAULT._secrets[:] = [s for s in saved if len(s) >= redact.MIN_SECRET_LEN]
    try:
        yield
    finally:
        redact.VAULT._secrets[:] = saved


def _play(tmp_path, variant, scoreless, budget=60):
    ledger_path = str(tmp_path / "ledger.jsonl")
    with _vault_without_toy_secrets(), \
            MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME], scoreless=scoreless) as arc, \
            MockProvider(api_key=MODEL_KEY) as provider:
        run_game(DEFAULT_GAME, arm="mock_arm", budget=budget,
                 env_upstream=arc.base_url, model_upstream=provider.base_url,
                 env_key=ARC_KEY, model_key=MODEL_KEY, require_keys=False,
                 variant=variant, ledger_path=ledger_path,
                 runs_dir=str(tmp_path / "runs"))
    return read_ledger(ledger_path)


@pytest.fixture(scope="module")
def scoreless_run(tmp_path_factory):
    """A run against a world that reports no score. `win_tighten` here removes
    the win condition rather than tightening it."""
    return _play(tmp_path_factory.mktemp("scoreless"),
                 _variant(2, "t-absent"), scoreless=True)


@pytest.fixture(scope="module")
def scoring_run(tmp_path_factory):
    """A run against the normal scoring world, with the floor set above
    anything the game can reach -- so `win_tighten` fires on every WIN, for a
    shortfall. This is the session that must *pass* the guard: not because
    nothing happened, but because what happened was the honest case."""
    return _play(tmp_path_factory.mktemp("scoring"),
                 _variant(99, "t-below"), scoreless=False)


def _applied(records, op="win_tighten"):
    out = []
    for record in records:
        variant = record.get("variant")
        if not isinstance(variant, dict):
            continue
        applied = variant.get("applied")
        if isinstance(applied, dict) and applied.get("op") == op:
            out.append(applied)
    return out


# -- the split itself ------------------------------------------------------

def test_absent_and_below_are_not_the_same_record():
    """P1. The whole defect was that these two produced equal records."""
    runtime = VariantRuntime(_variant(4, "t-unit"))
    absent, applied_absent = runtime.after(
        {"frame": [[[0]]], "state": "WIN", "score": None})
    below, applied_below = runtime.after(
        {"frame": [[[0]]], "state": "WIN", "score": 3})

    assert absent["state"] == below["state"] == "NOT_FINISHED"
    assert applied_absent["reason"] == REASON_ABSENT
    assert applied_below["reason"] == REASON_BELOW
    assert applied_absent["degenerate"] is True
    assert applied_below["degenerate"] is False
    assert applied_absent != applied_below
    # The record goes into a ledger line, so the distinction has to survive the
    # only encoding it will ever be read through.
    assert json.loads(json.dumps(applied_absent))["degenerate"] is True


def test_the_absent_case_still_rewrites_the_win():
    """The conservative direction is deliberate and is not what changed. If
    this ever goes green the other way, a game that never reports a score wins
    a tightened variant outright."""
    runtime = VariantRuntime(_variant(1, "t-unit"))
    body, applied = runtime.after({"frame": [[[0]]], "state": "WIN", "score": None})
    assert body["state"] == "NOT_FINISHED"
    assert applied is not None


def test_a_sufficient_score_is_still_left_alone():
    runtime = VariantRuntime(_variant(4, "t-unit"))
    body, applied = runtime.after({"frame": [[[0]]], "state": "WIN", "score": 4})
    assert body["state"] == "WIN" and applied is None


def test_only_the_first_absent_rewrite_carries_the_sentence():
    """A scoreless game produces the same rewrite on every WIN. The bit is on
    all of them; the explanation is on the first, so the first is not buried
    under copies of itself."""
    runtime = VariantRuntime(_variant(2, "t-unit"))
    first = runtime.after({"frame": [[[0]]], "state": "WIN", "score": None})[1]
    second = runtime.after({"frame": [[[0]]], "state": "WIN", "score": None})[1]

    assert first["note"] == DEGENERATE_NOTE and first["occurrence"] == 1
    assert "note" not in second and second["occurrence"] == 2
    assert second["degenerate"] is True
    assert runtime.degenerate_wins == 2
    assert runtime.first_degenerate["occurrence"] == 1


def test_a_shortfall_never_counts_as_a_degeneracy():
    runtime = VariantRuntime(_variant(4, "t-unit"))
    runtime.after({"frame": [[[0]]], "state": "WIN", "score": 0})
    runtime.after({"frame": [[[0]]], "state": "WIN", "score": 3})
    assert runtime.degenerate_wins == 0
    assert runtime.first_degenerate is None


# -- the scoreless session -------------------------------------------------

def test_a_scoreless_session_marks_every_rewrite(scoreless_run):
    applied = _applied(scoreless_run)
    assert applied, "the run produced no win_tighten record at all"
    assert all(a["degenerate"] is True for a in applied)
    assert all(a["reason"] == REASON_ABSENT for a in applied)
    assert [a for a in applied if a.get("note")], "no rewrite carried the sentence"


def test_a_scoreless_session_is_refused_by_the_guard(scoreless_run):
    """P3a."""
    report = scan_records(scoreless_run)
    assert report["verdict"] == "REFUSED"
    assert report["findings"]
    assert all(v["exam_eligible"] is False for v in report["variants"])


def test_stripping_the_marker_lets_the_scoreless_session_through(scoreless_run):
    """P3b, and the reason the guard reads the marker and nothing else.

    If the guard also re-derived degeneracy from `score: null`, this would stay
    red and the marker would be decoration -- true, recorded, and load-bearing
    for nothing. It goes green, so the marker is what catches it."""
    stripped = copy.deepcopy(scoreless_run)
    removed = 0
    for record in stripped:
        applied = (record.get("variant") or {}).get("applied")
        if isinstance(applied, dict) and "degenerate" in applied:
            applied.pop("degenerate")
            removed += 1
    assert removed > 0

    report = scan_records(stripped)
    assert report["verdict"] == "PASS"
    assert report["findings"] == []


def test_the_scoreless_session_records_an_incident_exactly_once(scoreless_run):
    """The second consumer. The bit is read in the live path, not only by a
    tool someone has to remember to run."""
    incidents = [r for r in scoreless_run
                 if r["event"] == "incident" and r["kind"] == "variant_degenerate"]
    assert len(incidents) == 1
    assert incidents[0]["detail"] == DEGENERATE_NOTE
    assert incidents[0]["reason"] == REASON_ABSENT
    assert incidents[0]["variant_id"] == "t-absent"


def test_variant_degenerate_is_a_declared_incident_kind():
    assert "variant_degenerate" in INCIDENT_KINDS


# -- the scoring session ---------------------------------------------------

def test_the_scoring_session_fires_win_tighten_for_a_shortfall(scoring_run):
    """The guard's PASS below has to be a fact about the session, not about
    nothing having happened in it."""
    applied = _applied(scoring_run)
    assert applied, "the requirement was not high enough to fire at all"
    assert all(a["reason"] == REASON_BELOW for a in applied)
    assert all(a["degenerate"] is False for a in applied)
    assert all(isinstance(a["score"], int) for a in applied)


def test_the_scoring_session_passes_the_guard(scoring_run):
    """P3c."""
    report = scan_records(scoring_run)
    assert report["verdict"] == "PASS"
    assert all(v["exam_eligible"] is True for v in report["variants"])


def test_the_scoring_session_can_still_be_refused(scoring_run):
    """P3d. A guard that passes a scoring session because it cannot fire on one
    has not been tested on it. Forge one marker and it must go red."""
    forged = copy.deepcopy(scoring_run)
    planted = 0
    for record in forged:
        applied = (record.get("variant") or {}).get("applied")
        if isinstance(applied, dict) and applied.get("op") == "win_tighten":
            applied["degenerate"] = True
            planted += 1
            break
    assert planted == 1

    report = scan_records(forged)
    assert report["verdict"] == "REFUSED"
    assert len(report["findings"]) == 1


def test_the_scoring_session_records_no_incident(scoring_run):
    assert not [r for r in scoring_run
                if r["event"] == "incident" and r["kind"] == "variant_degenerate"]


# -- the guard as a program ------------------------------------------------

def test_the_guard_exits_non_zero_on_a_refused_stream(tmp_path, scoreless_run, capsys):
    """P2 in its bluntest form: something exits non-zero."""
    path = tmp_path / "scoreless.jsonl"
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                            for r in scoreless_run), encoding="utf-8")
    assert check_main([str(path)]) == 2
    out = capsys.readouterr().out
    assert "REFUSED" in out and "R-V22" in out

    assert check_main([str(path), "--json"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["variants"][0]["exam_eligible"] is False


def test_the_guard_exits_zero_on_a_scoring_stream(tmp_path, scoring_run):
    path = tmp_path / "scoring.jsonl"
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                            for r in scoring_run), encoding="utf-8")
    assert check_main([str(path)]) == 0


def test_the_guard_reports_an_unreadable_path_rather_than_passing_it(tmp_path):
    assert check_main([str(tmp_path / "nope.jsonl")]) == 1


def test_the_guard_only_speaks_for_win_tighten():
    """Written because a mutant survived: dropping the `op` filter changed no
    test. `degenerate` is a `win_tighten` word -- R-V22 excludes a *win_tighten*
    variant from the reason score -- so a guard that refused any record
    carrying the key would be refusing on someone else's behalf."""
    record = {"seq": 3, "event": "env_step", "variant": {
        "variant_id": "t-other", "spec_sha256": "sha256:x",
        "applied": {"op": "observation_loss", "cell": [1, 1], "value": 2,
                    "degenerate": True}}}
    assert scan_records([record])["verdict"] == "PASS"


def test_the_incident_is_written_once_even_if_the_edge_is_seen_twice():
    """Also written because a mutant survived. `degenerate_wins != 1` already
    fires once per session in a single-threaded run, so the `degeneracy_reported`
    set looks redundant -- it is not: two commands for the same game can be in
    flight at once (`ThreadingHTTPServer`), and both would see the counter at 1.
    Calling the notifier twice is the deterministic stand-in for that race."""
    from proxy import env_proxy as ep

    runtime = VariantRuntime(_variant(2, "t-race"))
    runtime.after({"frame": [[[0]]], "state": "WIN", "score": None})
    assert runtime.degenerate_wins == 1

    written = []
    stub = types.SimpleNamespace(
        state=ep._State(),
        cfg=types.SimpleNamespace(
            variant=runtime.variant,
            run=types.SimpleNamespace(
                incident=lambda kind, detail, **fields: written.append(kind))))

    ep._Handler._note_degeneracy(stub, runtime, "g-1")
    ep._Handler._note_degeneracy(stub, runtime, "g-1")
    assert written == ["variant_degenerate"]


def test_the_guard_sees_a_marker_nested_under_multiple():
    """`env_proxy` wraps an outbound rewrite and an inbound one into
    `{"op":"multiple"}`, so a guard that unwrapped only the top level would
    miss exactly the runs that had two operators."""
    record = {"seq": 7, "event": "env_step", "variant": {
        "variant_id": "t-nested", "spec_sha256": "sha256:x",
        "applied": {"op": "multiple", "applied": [
            {"op": "remap_action", "from": "ACTION1", "to": "ACTION2"},
            {"op": "multiple", "applied": [
                {"op": "win_tighten", "reason": REASON_ABSENT,
                 "degenerate": True, "require_score": 2}]}]}}}
    report = scan_records([record])
    assert report["verdict"] == "REFUSED"
    assert report["findings"][0]["seq"] == 7
