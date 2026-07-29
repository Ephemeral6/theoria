"""How a backfilled manifest decides what it knows.

Two derivations got this wrong on the same pair of runs, and both were the same
kind of mistake: a field was filled from the strongest source *the code knew
about* rather than the strongest source *the run left behind*.

  * `prompt_id` fell through to the scorecard's `p8` tag and filed two
    A3 campaign legs under "P-8", because the legs died before closing a card
    and the tag was the only thing left. The reservation's campaign string had
    the item id in it the whole time.
  * `scorecards_opened_and_never_closed` was computed from the run's own ledger
    only. A run that dies before closing its card is exactly the run a salvage
    is for -- so the manifest that most needed to know about the salvage was
    the one structurally unable to see it.

These tests are over the real archive where they can be, because that is the
artefact the claim is about.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                       # noqa: E402

from armtools import backfill                           # noqa: E402
from proxy.ledger import read_ledger                    # noqa: E402

RUNS_DIR = _bootstrap.path("runs")


# ------------------------------------------------- the campaign string parser
def _start(campaign):
    """One `run_start` record, which is all `_campaign_prompt_id` reads."""
    return [{"event": "run_start", "spend_gate": {"campaign": campaign}}]


def test_the_campaign_string_yields_the_item_the_money_was_booked_under():
    assert backfill._campaign_prompt_id(_start(
        "theoria-arm:A3-campaign-devpile:g50t-5849a774:20260729T004020Z-leg01"
    )) == "A3-campaign-devpile"


@pytest.mark.parametrize("campaign", [
    "theoria-arm:A3:g50t",                     # three fields, not four
    "theoria-arm:A3:g50t:leg01:extra",         # five
    "theoria-arm::g50t-5849a774:leg01",        # the prompt field is empty
    "theoria-arm: :g50t-5849a774:leg01",       # ...and whitespace is empty too
    "",
    None,
    {"not": "a string"},
])
def test_anything_but_four_full_fields_declines_rather_than_guessing(campaign):
    """A half-understood campaign string must not become a prompt id.

    The failure this guards is silent: field 1 of a malformed string is still
    *a* string, so a lenient parser would file the run under something like
    "g50t-5849a774" and the manifest would look complete while being wrong.
    """
    assert backfill._campaign_prompt_id(_start(campaign)) is None


def test_no_run_start_at_all_is_not_an_error():
    assert backfill._campaign_prompt_id([]) is None


def test_the_campaign_outranks_the_tag_but_not_the_closed_card():
    """The ordering is the whole point, so it is pinned rather than described.

    The tag is a label; the campaign is the identity the reservation was booked
    under; `opaque.prompt_id` survived a round trip through the API. Strongest
    last-writer wins, and the two weaker sources must not shadow a stronger one.
    """
    campaign = "theoria-arm:A3-campaign-devpile:g50t-5849a774:leg01"
    tagged = {"event": "env_meta",
              "http": {"path": "/api/scorecard/open", "status": 200},
              "request": {"tags": ["p8"]},
              "response": {"card_id": "card-1"}}

    both = _start(campaign) + [tagged]
    assert backfill.prompt_id_of(both, "leg01", RUNS_DIR)["value"] \
        == "A3-campaign-devpile"

    # With no campaign to read, the tag is still better than nothing.
    assert backfill.prompt_id_of(
        _start(None) + [tagged], "leg01", RUNS_DIR)["value"] == "P-8"


# --------------------------------------------- orphans, across the whole tree
def _closed_anywhere():
    """Every card id the archive can prove was closed, and by which run."""
    closed = {}
    for name in sorted(os.listdir(RUNS_DIR)):
        ledger = os.path.join(RUNS_DIR, name, "ledger.jsonl")
        if not os.path.exists(ledger):
            continue
        for card in backfill.recovered_scorecards(read_ledger(ledger)):
            if card.get("card_id"):
                closed[card["card_id"]] = name
    return closed


def _manifests():
    for name in sorted(os.listdir(RUNS_DIR)):
        path = os.path.join(RUNS_DIR, name, "MANIFEST.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                yield name, json.load(fh)


def test_no_manifest_calls_a_card_lost_that_another_run_closed():
    """The invariant `build` was violating, stated over the real archive.

    `scorecards_opened_and_never_closed` carries a note saying "no run -- this
    one or any other in the archive -- ever closed it". That sentence is a
    claim about the whole tree, so it is checked against the whole tree. Before
    this, `20260729T004020Z-leg01` made exactly that claim about card
    `2ec0e679...` while `20260729T004020Z-leg01-salvage` sat next to it holding
    the API's own count of 9 actions for that same card.
    """
    closed = _closed_anywhere()
    wrong = [(name, card, closed[card])
             for name, manifest in _manifests()
             for card in manifest.get("scorecards_opened_and_never_closed", [])
             if card in closed]
    assert not wrong, [
        "%s calls %s never-closed, but %s closed it" % (n, c, by)
        for n, c, by in wrong]


def test_a_run_whose_card_was_salvaged_can_be_navigated_to_the_number():
    """Reachability, which is what `verify_provenance`'s check 5 asks for.

    A run that spent actions must lead a reader to an API-confirmed count. For
    a run that died before closing, the only path is the pointer -- and it has
    to name a run that really holds the card, not merely be present.
    """
    closed = _closed_anywhere()
    seen = 0
    for name, manifest in _manifests():
        pointer = manifest.get("scorecard_recovered_by")
        if not pointer:
            # Not merely "no pointer": a run that opened a card, did not close
            # it, and has no pointer either is the regression this test exists
            # for.  Skipping it silently is how the test came to be unable to
            # fail for its own stated reason -- removing the pointer removed
            # the only thing it looked at.
            orphans = manifest.get("scorecards_opened_and_never_closed") or []
            recovered = [c for c in orphans if c in closed]
            assert not recovered, (
                "%s declares card(s) %s lost, but the archive shows %s closed "
                "them -- the pointer is missing, not the number"
                % (name, recovered, [closed[c] for c in recovered]))
            continue
        seen += 1
        assert closed.get(pointer["card_id"]) == pointer["slug"], (
            "%s points at %s for card %s, but the archive says %s closed it"
            % (name, pointer["slug"], pointer["card_id"],
               closed.get(pointer["card_id"])))
        assert pointer.get("total_actions") is not None, (
            "%s's pointer carries no count, so it settles nothing" % name)
    assert seen, ("no manifest in the archive carries a recovery pointer, so "
                  "this test just checked nothing -- it is stated over the "
                  "whole archive and needs a subject in it")


def test_a_salvaged_card_outranks_the_campaign_string():
    """The ranking the code declares must be the ranking the code applies.

    `prompt_id_of` calls `opaque.prompt_id` its strongest source and the
    campaign string a weaker one -- but it used to search only the run's own
    records for the strong one. A run that died before closing its card
    therefore fell through to the campaign string, whose `prompt_id` field is
    `harness/run.py`'s module-level default rather than anything observed.
    The result on disk was worse than being wrong: `…004020Z-leg01` said
    `A3-campaign-devpile` while `…004020Z-leg01-salvage`, holding that same
    card, said `P-8`.

    Stated over the archive because the invariant is about the archive: no run
    may disagree with the salvage that closed its own card.
    """
    by_slug = dict(_manifests())
    checked = 0
    for name, manifest in by_slug.items():
        pointer = manifest.get("scorecard_recovered_by")
        if not pointer:
            continue
        other = by_slug.get(pointer["slug"])
        if other is None or not other.get("prompt_id"):
            continue
        checked += 1
        assert manifest.get("prompt_id") == other["prompt_id"], (
            "%s is filed under %r but %s, which closed its card, is filed "
            "under %r -- the archive contradicts itself about one card"
            % (name, manifest.get("prompt_id"), pointer["slug"],
               other["prompt_id"]))
    assert checked, ("no run in the archive is paired with the salvage that "
                     "closed its card, so this test checked nothing")
