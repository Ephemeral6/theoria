import copy

import pytest

from proxy.variants import (LEGAL_OPERATORS, Refusal, Variant, VariantRuntime,
                            VariantSpecError, _Remap)

BASE = {
    "variant_id": "t-x",
    "base_game": "ar25-0c556536",
    "claim": "unsolvable",
    "operators": [{"op": "step_limit", "limit": 2}],
    "justification": "A justification long enough to be a real argument about "
                     "why the claim follows from the construction itself.",
}


def spec(**overrides):
    out = copy.deepcopy(BASE)
    out.update(overrides)
    return out


def test_every_shipped_variant_carries_a_constructive_justification():
    variants = Variant.load_all()
    assert len(variants) >= 4
    for variant in variants:
        assert variant.claim in ("solvable", "unsolvable", "unchanged")
        assert len(variant.justification) >= 40
        assert variant.sha256.startswith("sha256:")
        for op in variant.operators:
            assert op["op"] in LEGAL_OPERATORS


def test_the_shipped_set_is_not_all_unsolvable():
    claims = {v.claim for v in Variant.load_all()}
    assert "solvable" in claims, (
        "an exam of only-unsolvable questions cannot separate 'I failed' from "
        "'it is impossible'")


def test_a_spec_without_a_justification_is_refused():
    with pytest.raises(VariantSpecError, match="justification"):
        Variant(spec(justification="too short"))
    missing = {k: v for k, v in BASE.items() if k != "justification"}
    with pytest.raises(VariantSpecError, match="missing required field"):
        Variant(missing)


def test_an_operator_outside_the_wrapper_legal_set_is_refused():
    with pytest.raises(VariantSpecError, match="wrapper-legal set"):
        Variant(spec(operators=[{"op": "edit_world_dynamics", "rule": "x"}]))


def test_an_empty_operator_list_is_refused():
    with pytest.raises(VariantSpecError, match="no operators"):
        Variant(spec(operators=[]))


def test_an_unknown_claim_is_refused():
    with pytest.raises(VariantSpecError, match="claim must be"):
        Variant(spec(claim="probably"))


def test_the_hash_tracks_the_spec():
    a = Variant(spec())
    b = Variant(spec(operators=[{"op": "step_limit", "limit": 3}]))
    assert a.sha256 != b.sha256


def test_forbid_action_is_not_forwarded():
    variant = Variant(spec(operators=[{"op": "forbid_action", "action": "ACTION2"}]))
    runtime = VariantRuntime(variant)
    runtime.after({"frame": [[[0]]], "state": "NOT_FINISHED", "score": 0})

    assert runtime.before("ACTION1") == "ACTION1"
    refusal = runtime.before("ACTION2")
    assert isinstance(refusal, Refusal)
    assert refusal.applied["op"] == "forbid_action"
    assert refusal.body["state"] == "NOT_FINISHED"       # frame unchanged


def test_step_limit_ends_the_episode_and_stays_ended():
    variant = Variant(spec(operators=[{"op": "step_limit", "limit": 2}]))
    runtime = VariantRuntime(variant)
    runtime.before("RESET")
    runtime.after({"frame": [[[0]]], "state": "NOT_FINISHED"})

    assert runtime.before("ACTION1") == "ACTION1"
    assert runtime.before("ACTION1") == "ACTION1"
    third = runtime.before("ACTION1")
    assert isinstance(third, Refusal) and third.body["state"] == "GAME_OVER"
    fourth = runtime.before("ACTION1")
    assert isinstance(fourth, Refusal)                   # and stays over


def test_reset_clears_the_step_counter():
    variant = Variant(spec(operators=[{"op": "step_limit", "limit": 1}]))
    runtime = VariantRuntime(variant)
    runtime.after({"frame": [[[0]]], "state": "NOT_FINISHED"})
    runtime.before("ACTION1")
    assert isinstance(runtime.before("ACTION1"), Refusal)
    runtime.before("RESET")
    assert runtime.before("ACTION1") == "ACTION1"


def test_remap_rewrites_the_outgoing_command():
    variant = Variant(spec(claim="solvable", operators=[
        {"op": "remap_action", "from": "ACTION3", "to": "ACTION4"}]))
    remap = VariantRuntime(variant).before("ACTION3")
    assert isinstance(remap, _Remap) and remap.action_name == "ACTION4"


def test_observation_loss_rewrites_the_state_on_the_last_frame():
    variant = Variant(spec(operators=[
        {"op": "observation_loss", "cells": [[1, 1]], "value": 2}]))
    runtime = VariantRuntime(variant)

    safe, applied = runtime.after({"frame": [[[0, 0], [0, 0]]], "state": "NOT_FINISHED"})
    assert safe["state"] == "NOT_FINISHED" and applied is None

    hit, applied = runtime.after({"frame": [[[0, 0], [0, 2]]], "state": "NOT_FINISHED"})
    assert hit["state"] == "GAME_OVER"
    assert applied["op"] == "observation_loss" and applied["cell"] == [1, 1]


def test_observation_loss_reads_the_last_frame_not_a_transient_one():
    """A conveyor makes intermediate frames transient; a loss declared on one
    would depend on animation timing rather than on the position the arm acts
    from."""
    variant = Variant(spec(operators=[
        {"op": "observation_loss", "cells": [[0, 0]], "value": 2}]))
    runtime = VariantRuntime(variant)
    body, applied = runtime.after(
        {"frame": [[[2, 0], [0, 0]], [[0, 0], [0, 2]]], "state": "NOT_FINISHED"})
    assert body["state"] == "NOT_FINISHED" and applied is None


def test_win_tighten_only_fires_on_a_win():
    variant = Variant(spec(operators=[
        {"op": "win_tighten", "require": {"kind": "score_at_least", "value": 4}}]))
    runtime = VariantRuntime(variant)

    running, applied = runtime.after({"frame": [[[0]]], "state": "NOT_FINISHED", "score": 1})
    assert running["state"] == "NOT_FINISHED" and applied is None

    short, applied = runtime.after({"frame": [[[0]]], "state": "WIN", "score": 3})
    assert short["state"] == "NOT_FINISHED" and applied["op"] == "win_tighten"

    enough, applied = runtime.after({"frame": [[[0]]], "state": "WIN", "score": 4})
    assert enough["state"] == "WIN" and applied is None


def test_win_tighten_rejects_an_unsupported_test():
    with pytest.raises(VariantSpecError, match="win_tighten"):
        Variant(spec(operators=[
            {"op": "win_tighten", "require": {"kind": "vibes", "value": 1}}]))


def test_no_variant_means_no_rewriting():
    runtime = VariantRuntime(None)
    assert runtime.before("ACTION2") == "ACTION2"
    body = {"frame": [[[0]]], "state": "WIN"}
    out, applied = runtime.after(body)
    assert out is body and applied is None
