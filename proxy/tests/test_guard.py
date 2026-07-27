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
