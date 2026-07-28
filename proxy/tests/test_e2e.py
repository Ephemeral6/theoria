"""The acceptance run: one arm, one game, through both proxies.

The ticket's bar is that the ledger lands on disk and the game replays from it
with equal frame hashes. Everything else here is the surrounding obligation --
score reconciliation, cost conversion, variant enforcement -- checked on the
same run rather than in isolation.
"""

import json

import pytest

from proxy.cost import PriceTable, price_run
from proxy.ledger import read_ledger
from proxy.mock.arc_mock import DEFAULT_GAME, DEFAULT_KEY as ARC_KEY, MockArc
from proxy.mock.model_mock import DEFAULT_KEY as MODEL_KEY, MockProvider
from proxy.reconcile import reconcile_run
from proxy.replay import replay_run
from proxy.runner import run_game
from proxy.variants import Variant


def play(tmp_path, variant=None, budget=60, stream=False, game=DEFAULT_GAME):
    ledger_path = str(tmp_path / "ledger.jsonl")
    with MockArc(api_key=ARC_KEY, games=[game]) as arc, \
            MockProvider(api_key=MODEL_KEY) as provider:
        record = run_game(game, arm="mock_arm", budget=budget,
                          env_upstream=arc.base_url, model_upstream=provider.base_url,
                          env_key=ARC_KEY, model_key=MODEL_KEY, require_keys=False,
                          variant=variant, ledger_path=ledger_path, stream=stream,
                          runs_dir=str(tmp_path / "runs"))
    return record, ledger_path


@pytest.fixture(scope="module")
def played(tmp_path_factory):
    return play(tmp_path_factory.mktemp("e2e"))


# -- the run itself --------------------------------------------------------

def test_the_arm_finishes_the_game(played):
    record, _ = played
    assert record["summary"]["outcome"] == "WIN"
    assert record["summary"]["levels_completed"] == 3


def test_the_arm_never_saw_a_key(played):
    record, ledger_path = played
    assert record["env_proxy"]["key_injected"] is True
    assert record["model_proxy"]["key_injected"] is True
    blob = open(ledger_path, encoding="utf-8").read()
    assert ARC_KEY not in blob and MODEL_KEY not in blob


def test_the_ledger_has_exactly_the_documented_shapes(played):
    _, ledger_path = played
    records = read_ledger(ledger_path)
    assert {r["event"] for r in records} <= {
        "run_start", "run_end", "env_step", "model_call", "env_meta"}

    for step in [r for r in records if r["event"] == "env_step"]:
        assert set(step) >= {"v", "event", "seq", "ts", "run_id", "arm", "game_id",
                             "card_id", "guid", "step_idx", "action", "frames",
                             "n_frames", "frame_hash", "state", "score",
                             "levels_completed", "level", "level_boundary",
                             "variant", "guard", "http"}
    for call in [r for r in records if r["event"] == "model_call"]:
        assert set(call) >= {"call_idx", "provider", "model", "request",
                             "response", "usage", "pricing_ref", "http"}
        assert "cost" not in call and "cost_usd" not in call


def test_scorecard_open_and_close_are_env_meta_not_env_step(played):
    _, ledger_path = played
    paths = [r["http"]["path"] for r in read_ledger(ledger_path)
             if r["event"] == "env_step"]
    assert all(p.startswith("/api/cmd/") for p in paths)
    meta = [r["http"]["path"] for r in read_ledger(ledger_path)
            if r["event"] == "env_meta"]
    assert "/api/scorecard/open" in meta and "/api/scorecard/close" in meta


def test_one_command_can_return_several_frames(played):
    """The cascade ruling depends on this being possible; a harness that
    modelled action -> single frame would silently drop observations."""
    _, ledger_path = played
    counts = [r["n_frames"] for r in read_ledger(ledger_path)
              if r["event"] == "env_step"]
    assert max(counts) > 1


def test_level_boundaries_land_in_the_ledger(played):
    _, ledger_path = played
    steps = [r for r in read_ledger(ledger_path) if r["event"] == "env_step"]
    assert sum(1 for s in steps if s["level_boundary"]) == 3
    assert [s["level"] for s in steps][-1] == 2


def test_model_calls_are_tied_to_the_step_they_decided(played):
    _, ledger_path = played
    calls = [r for r in read_ledger(ledger_path) if r["event"] == "model_call"]
    assert calls and all(isinstance(c["step_idx"], int) for c in calls)
    assert all(c["usage"]["input_tokens"] > 0 for c in calls)
    assert all(c["request"]["model"] == "mock-model-1" for c in calls)


# -- the two obligations ---------------------------------------------------

def test_the_run_replays_with_equal_frame_hashes(played, tmp_path):
    record, ledger_path = played
    with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME]) as arc:
        report = replay_run(record["run_id"], ledger_path=ledger_path,
                            env_upstream=arc.base_url, env_key=ARC_KEY,
                            require_key=False)
    assert report["verdict"] == "PASS"
    assert report["steps_compared"] == record["summary"]["steps"] + 1   # + RESET
    assert report["mismatches"] == []


def test_the_replay_uses_its_own_probe_scorecard(played, tmp_path):
    record, ledger_path = played
    with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME]) as arc:
        report = replay_run(record["run_id"], ledger_path=ledger_path,
                            env_upstream=arc.base_url, env_key=ARC_KEY,
                            require_key=False)
    records = read_ledger(ledger_path)
    original_cards = {r["card_id"] for r in records
                      if r["event"] == "env_step" and r["run_id"] == record["run_id"]}
    replay_cards = {r["card_id"] for r in records
                    if r["event"] == "env_step" and r["run_id"] == report["replay_run_id"]}
    assert original_cards and replay_cards
    assert original_cards.isdisjoint(replay_cards)

    start = next(r for r in records if r["event"] == "run_start"
                 and r["run_id"] == report["replay_run_id"])
    assert start["scorecard_kind"] == "probe"


def test_a_tampered_ledger_makes_the_replay_fail(played, tmp_path):
    """The check has to be able to fail, or passing means nothing."""
    record, ledger_path = played
    forged = str(tmp_path / "forged.jsonl")
    with open(ledger_path, encoding="utf-8") as src, \
            open(forged, "w", encoding="utf-8", newline="") as dst:
        for line in src:
            entry = json.loads(line)
            if entry.get("event") == "env_step" and entry.get("step_idx") == 2:
                entry["frame_hash"] = "sha256:" + "0" * 64
            dst.write(json.dumps(entry, sort_keys=True) + "\n")

    with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME]) as arc:
        report = replay_run(record["run_id"], ledger_path=forged,
                            env_upstream=arc.base_url, env_key=ARC_KEY,
                            require_key=False)
    assert report["verdict"] == "FAIL"
    assert report["first_divergence"] == 2
    assert any(r["event"] == "incident" and r["kind"] == "replay_mismatch"
               for r in read_ledger(forged))


def test_the_ledger_score_equals_the_scorecard_score(played):
    record, ledger_path = played
    report = reconcile_run(record["run_id"], ledger_path, write_incident=False)
    assert report["verdict"] == "PASS", report
    # The two sides agree in the unit they both report: levels completed. The
    # card's `score` is a fraction (3 of 3 levels -> 1.0) and the step field is
    # a count, so asserting they are equal would be asserting two different
    # things are the same number and calling the coincidence a check.
    assert report["ledger_levels_completed"] == 3
    assert report["scorecard_levels_completed"] == 3
    assert report["scorecard_score"] == 1.0
    assert report["scorer"]["id"] == "arc_v1"
    assert report["level_boundaries"] == 3


def test_reconciliation_catches_a_disagreement(played, tmp_path):
    record, ledger_path = played
    forged = str(tmp_path / "forged_score.jsonl")
    with open(ledger_path, encoding="utf-8") as src, \
            open(forged, "w", encoding="utf-8", newline="") as dst:
        for line in src:
            entry = json.loads(line)
            if entry.get("event") == "run_end" and entry.get("scorecard"):
                entry["scorecard"]["score"] = 99
            dst.write(json.dumps(entry, sort_keys=True) + "\n")

    report = reconcile_run(record["run_id"], forged, write_incident=True)
    assert report["verdict"] == "FAIL"
    assert any(r["event"] == "incident" and r["kind"] == "score_mismatch"
               for r in read_ledger(forged))


def test_cost_is_a_conversion_over_the_recorded_usage(played):
    _, ledger_path = played
    table = PriceTable.load()
    report = price_run(read_ledger(ledger_path), table)
    assert report["model_calls"] > 0
    assert report["pricing"]["table"] == "pricing_v1"
    assert report["usd_total"] == 0.0            # the mock model is free

    priced = table.cost("claude-opus-5", {"input_tokens": 1_000_000,
                                          "output_tokens": 1_000_000,
                                          "cache_read_input_tokens": 1_000_000})
    assert priced["usd"] == pytest.approx(5.0 + 25.0 + 0.5)


# -- streaming and variants ------------------------------------------------

def test_streamed_usage_is_merged_from_both_halves(tmp_path):
    record, ledger_path = play(tmp_path, stream=True)
    calls = [r for r in read_ledger(ledger_path) if r["event"] == "model_call"]
    assert calls and all(c["http"]["stream"] for c in calls)
    for call in calls:
        assert call["usage"]["input_tokens"] > 0         # from message_start
        assert call["usage"]["output_tokens"] > 0        # from message_delta
        assert call["response"]["assembled"]["text"]
        assert call["response"]["stream_events"]


def test_a_forbidden_direction_makes_the_game_unwinnable(tmp_path):
    """v002 claims unsolvable by a monotone-invariant argument. The exam's
    answer comes from that argument; this only checks the wrapper enforces
    what the argument assumed."""
    variant = Variant.find("v002-forbid-down")
    record, ledger_path = play(tmp_path, variant=variant, budget=25)
    assert record["summary"]["outcome"] != "WIN"
    assert record["summary"]["levels_completed"] == 0

    steps = [r for r in read_ledger(ledger_path) if r["event"] == "env_step"]
    forbidden = [s for s in steps
                 if (s["variant"] or {}).get("applied", {})
                 and s["variant"]["applied"].get("op") == "forbid_action"]
    assert forbidden, "the arm never tried the forbidden action"
    assert all(s["http"]["forwarded"] is False for s in forbidden)
    assert all(s["variant"]["variant_id"] == "v002-forbid-down" for s in steps)
    assert all(s["variant"]["spec_sha256"] == variant.sha256 for s in steps)


def test_a_step_limit_ends_the_episode(tmp_path):
    variant = Variant.find("v001-step-limit-3")
    record, ledger_path = play(tmp_path, variant=variant, budget=20)
    assert record["summary"]["outcome"] == "GAME_OVER"
    assert record["summary"]["steps"] <= 5

    applied = [s["variant"]["applied"] for s in read_ledger(ledger_path)
               if s["event"] == "env_step" and (s["variant"] or {}).get("applied")]
    assert any(a["op"] == "step_limit" for a in applied)


def test_a_relabelled_game_is_still_winnable(tmp_path):
    """v004's claim is that relabelling is a bijection, so composing any
    winning policy with the inverse relabelling wins again.

    That is a proof, not an experiment, and the experiment has to match it
    exactly: the *same* policy the base game was won with, with ACTION3 and
    ACTION4 swapped on the way out, wins the wrapped game. A policy that did
    not know about the swap would lose here, and that would say nothing about
    solvability -- only about the policy.
    """
    from proxy.mock.arm_mock import MockArm

    class InverseRelabelledArm(MockArm):
        SWAP = {3: 4, 4: 3}

        def decide(self, frame, step):
            chosen = super().decide(frame, step)
            return self.SWAP.get(chosen, chosen)

    variant = Variant.find("v004-swap-left-right")
    ledger_path = str(tmp_path / "ledger.jsonl")
    with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME]) as arc, \
            MockProvider(api_key=MODEL_KEY) as provider:
        record = run_game(
            DEFAULT_GAME, arm="mock_arm", budget=60,
            env_upstream=arc.base_url, model_upstream=provider.base_url,
            env_key=ARC_KEY, model_key=MODEL_KEY, require_keys=False,
            variant=variant, ledger_path=ledger_path,
            runs_dir=str(tmp_path / "runs"),
            arm_factory=lambda env_base, model_base: InverseRelabelledArm(
                env_base=env_base, model_base=model_base, check_sealed=False))

    assert record["summary"]["outcome"] == "WIN"
    remapped = [s for s in read_ledger(ledger_path)
                if s["event"] == "env_step" and (s["variant"] or {}).get("applied")]
    assert remapped, "the swap never fired, so nothing was demonstrated"
    assert all(s["variant"]["applied"]["op"] == "remap_action" for s in remapped)


def test_a_variant_run_replays_too(tmp_path):
    variant = Variant.find("v001-step-limit-3")
    record, ledger_path = play(tmp_path, variant=variant, budget=20)
    with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME]) as arc:
        report = replay_run(record["run_id"], ledger_path=ledger_path,
                            env_upstream=arc.base_url, env_key=ARC_KEY,
                            require_key=False)
    assert report["verdict"] == "PASS"
    assert report["variant"]["variant_id"] == "v001-step-limit-3"
