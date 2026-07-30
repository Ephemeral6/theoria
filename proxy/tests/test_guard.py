import json

import pytest

from proxy.guard import (PilesIntegrityError, SealedGameError, SealedPileGuard,
                         load_piles, stem)

SEALED = "dc22-fdcac232"
DEV = "ar25-0c556536"


def test_the_cut_file_hashes_to_the_digest_it_carries():
    piles = load_piles()                                 # verify=True by default
    assert piles["cut_version"] == "v1"
    assert len(piles["sealed_pile"]) == 21
    assert len(piles["dev_pile"]) == 4


def test_an_edited_cut_fails_closed(tmp_path):
    piles = load_piles()
    piles["sealed_pile"] = [g for g in piles["sealed_pile"] if g != SEALED]
    path = str(tmp_path / "piles.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(piles, fh)
    with pytest.raises(PilesIntegrityError):
        SealedPileGuard(piles_path=path)


def test_sealed_games_are_refused():
    guard = SealedPileGuard()
    assert guard.classify(SEALED) == "sealed"
    with pytest.raises(SealedGameError, match="sealed_pile"):
        guard.assert_playable(SEALED)


def test_a_bare_id_without_the_version_suffix_is_caught_too():
    guard = SealedPileGuard()
    assert guard.classify(stem(SEALED)) == "sealed"
    assert guard.verdict("dc22")[0] is False


def test_development_pile_games_are_allowed():
    guard = SealedPileGuard()
    assert guard.classify(DEV) == "dev"
    guard.assert_playable(DEV)


def test_an_id_in_neither_pile_fails_closed_by_default():
    guard = SealedPileGuard()
    allowed, rule, _ = guard.verdict("zz99-deadbeef")
    assert allowed is False and rule == "unknown_game"
    assert SealedPileGuard(unknown_policy="allow").verdict("zz99-deadbeef")[0] is True


def test_a_sealed_id_is_found_wherever_it_hides():
    guard = SealedPileGuard()
    # Not in the field the guard "expects" -- nested inside a click payload.
    verdict = guard.check_request(
        "/api/cmd/ACTION6", "", {"game_id": DEV, "data": {"note": SEALED}})
    assert verdict["decision"] == "deny"
    assert verdict["game_id"] == SEALED

    verdict = guard.check_request("/api/cmd/RESET", "game_id=" + SEALED, None)
    assert verdict["decision"] == "deny"


def test_requests_naming_no_game_are_allowed():
    guard = SealedPileGuard()
    assert guard.check_request("/api/games", "", None)["decision"] == "allow"
    assert guard.check_request("/api/scorecard/open", "", {"arm": "x"})["decision"] == "allow"


def test_a_run_allowlist_narrows_further():
    guard = SealedPileGuard(allow_only=[DEV])
    assert guard.verdict(DEV)[0] is True
    other = "g50t-5849a774"                               # also development pile
    allowed, rule, _ = guard.verdict(other)
    assert allowed is False and rule == "not_in_run_allowlist"


def test_the_fingerprint_carries_the_cut_hash():
    fingerprint = SealedPileGuard().fingerprint()
    assert fingerprint["sha256"].startswith("3feca53e")
    assert fingerprint["n_sealed"] == 21


# -- the join is the guard's own construction, and must not invent games -----

def test_an_arm_name_beside_a_game_id_does_not_invent_a_third_game():
    """`_texts` joins the body's values to catch an id split across two fields.
    With keys sorted, `{"arm": ..., "game_id": ...}` joins to
    `bare_ccar25-0c556536`, whose 6-character stem `ccar25` is in neither pile
    -- so the guard refused a development game as `unknown_game`, for an id
    nobody sent. Any value ending in one or two alphanumerics does this; an
    arm's name is merely where it was found.

    Fails closed, so this was a false denial and never a leak. Its cost is that
    the arm loses its scorecard: `MockArm.play` ignores the 403 and the run
    finishes with `card_id=None`, reconciling UNDETERMINED instead of aborting.
    """
    guard = SealedPileGuard()
    for arm in ("bare_cc", "schema_repro", "theoria", "probe", "replay",
                "mock_arm"):
        for game in ("ar25-0c556536", "g50t-5849a774", "sk48-d8078629",
                     "tn36-ef4dde99"):
            verdict = guard.check_request("/api/scorecard/open", "",
                                          {"arm": arm, "game_id": game})
            assert verdict["decision"] == "allow", (arm, game, verdict)


def test_a_short_value_before_a_game_id_does_not_invent_one_either():
    """The mechanism is the alphanumeric tail, not the underscore and not the
    arm field -- so it is asserted on the shape rather than on one name."""
    guard = SealedPileGuard()
    for before in ("v2", "x-y2", "a.b1", "q", "2", "tag:v2", "card-x"):
        verdict = guard.check_request(
            "/api/cmd/RESET", "", {"a": before, "b": "ar25-0c556536"},
            is_command=True)
        assert verdict["decision"] == "allow", (before, verdict)


def test_red_a_sealed_id_split_behind_a_stub_is_still_caught():
    """The failing path, and the reason the join's scan drops the left anchor.

    `re.findall` does not overlap, so a stub in front of a split id used to let
    a phantom consume it: `{"a": "x_ab" + stem + "-", "b": "&lt;hex8&gt;"}` yielded
    only `ab&lt;stem&gt;-&lt;hex8&gt;`, an unregistered stem. Under the default
    `unknown_policy="deny"` that still refused, but for the wrong reason and
    under `unknown_policy="allow"` it refused nothing at all -- the sealed id
    was never seen. Scanning the join for every overlapping candidate and
    keeping the registered ones catches it as what it is.
    """
    for policy in ("deny", "allow"):
        guard = SealedPileGuard(unknown_policy=policy)
        verdict = guard.check_request(
            "/api/cmd/RESET", "",
            {"a": "x_ab" + stem(SEALED) + "-", "b": SEALED.split("-", 1)[1]},
            is_command=True)
        assert verdict["decision"] == "deny", (policy, verdict)
        assert verdict["rule"] == "sealed_pile", (policy, verdict)
        assert verdict["game_id"] == SEALED, (policy, verdict)


def test_a_sealed_id_split_across_two_fields_is_still_caught():
    """D-022's original case, unchanged by the narrowing.

    It is caught on the bare stem `dc22` -- found in the first value on its own
    (RED-20), before the join is reached -- rather than on the reassembled id.
    Asserted as the stem for that reason: the join is the second line of
    defence here, not the first.
    """
    guard = SealedPileGuard()
    verdict = guard.check_request(
        "/api/cmd/RESET", "",
        {"a": stem(SEALED) + "-", "b": SEALED.split("-", 1)[1]},
        is_command=True)
    assert verdict["decision"] == "deny"
    assert verdict["rule"] == "sealed_pile"
    assert verdict["game_id"] in (SEALED, stem(SEALED))
