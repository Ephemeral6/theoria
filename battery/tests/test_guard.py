"""The guardrail is the one piece of this track that must not be wrong."""

import copy
import json

import pytest

from battery.guard import (
    CutIntegrityError,
    Piles,
    SealedPileError,
    UnknownGameError,
    canonical_digest,
    load_piles,
    screen,
)


@pytest.fixture(scope="module")
def piles():
    return load_piles()


def test_the_published_cut_verifies(piles):
    """piles.json hashes to its own recorded digest."""
    assert piles.recorded_digest == piles.computed_digest
    assert piles.computed_digest.startswith("3feca53e")
    assert piles.computed_digest.endswith("41bbc19a")


def test_dev_pile_is_the_four_games_CLAUDE_md_names(piles):
    assert sorted(piles.dev_pile) == [
        "ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99",
    ]
    assert len(piles.sealed_pile) == 21


def test_sealed_full_id_is_refused(piles):
    for gid in piles.sealed_pile:
        with pytest.raises(SealedPileError):
            piles.assert_playable(gid)


def test_sealed_short_id_is_refused(piles):
    """The API accepts de-suffixed ids, so a full-id-only guard is a sieve."""
    for gid in piles.sealed_pile:
        short = gid.split("-", 1)[0]
        with pytest.raises(SealedPileError):
            piles.assert_playable(short)


def test_sealed_case_and_whitespace_variants_are_refused(piles):
    gid = piles.sealed_pile[0]
    short = gid.split("-", 1)[0]
    for variant in (gid.upper(), gid.title(), "  %s  " % gid,
                    short.upper(), "\t%s\n" % short):
        with pytest.raises(SealedPileError):
            piles.assert_playable(variant)


def test_dev_ids_pass_in_every_form(piles):
    for gid in piles.dev_pile:
        short = gid.split("-", 1)[0]
        assert piles.assert_playable(gid) == "dev"
        assert piles.assert_playable(short) == "dev"
        assert piles.assert_playable(gid.upper()) == "dev"
        assert piles.assert_playable(" %s " % short) == "dev"


def test_unknown_ids_are_refused_not_waved_through(piles):
    """An unregistered game is not a safe game."""
    for gid in ("zz99-deadbeef", "zz99", "", "arc25-0c556536"):
        with pytest.raises(UnknownGameError):
            piles.assert_playable(gid)


def test_a_dev_suffix_typo_does_not_become_a_sealed_bypass(piles):
    """`sk48-<wrong>` still resolves by short id, and sk48 is a dev game."""
    assert piles.assert_playable("sk48-0000000") == "dev"
    # ...and the same shape over a sealed prefix is still caught.
    with pytest.raises(SealedPileError):
        piles.assert_playable("bp35-0000000")


def test_synthetic_worlds_have_no_game_id_and_are_allowed(piles):
    assert piles.assert_playable(None) == "synthetic"


def test_a_tampered_cut_refuses_to_load(piles):
    doc = copy.deepcopy(piles.doc)
    doc["sealed_pile"].remove(doc["sealed_pile"][0])
    doc["dev_pile"].append("bp35-0a0ad940")
    with pytest.raises(CutIntegrityError):
        Piles(doc)


def test_a_cut_with_no_digest_refuses_to_load(piles):
    doc = copy.deepcopy(piles.doc)
    del doc["sha256"]
    with pytest.raises(CutIntegrityError):
        Piles(doc)


def test_a_game_in_both_piles_refuses_to_load(piles):
    doc = copy.deepcopy(piles.doc)
    doc["dev_pile"] = list(doc["dev_pile"]) + ["bp35-0a0ad940"]
    doc["sha256"] = canonical_digest(doc)
    with pytest.raises(CutIntegrityError):
        Piles(doc)


def test_screen_fails_on_the_first_sealed_id_not_after_the_recompute(piles):
    with pytest.raises(SealedPileError):
        screen(["ar25-0c556536", "bp35", "g50t-5849a774"], piles)
    accepted, verdicts = screen(["ar25-0c556536", None, "g50t"], piles)
    assert verdicts == ["dev", "synthetic", "dev"]
    assert accepted == ["ar25-0c556536", "<synthetic>", "g50t"]


def test_provenance_travels_with_every_artefact(piles):
    prov = piles.provenance()
    assert prov["piles_sha256"] == piles.computed_digest
    assert prov["n_sealed"] == 21
    assert json.dumps(prov, sort_keys=True)  # serialisable, for the artefacts
