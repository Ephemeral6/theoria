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


# ------------------------------------------- the pointer must name a run
def _close_record(run_id, card_id, owner_run_id, total_actions):
    """One ledger record: `run_id` closed `card_id`, which `owner_run_id` opened."""
    return {"v": "1.0", "event": "env_step", "run_id": run_id,
            "http": {"path": "/api/scorecard/close", "status": 200},
            "response": {"card_id": card_id, "total_actions": total_actions,
                         "total_levels_completed": 0, "score": 0.0,
                         "opaque": {"run_id": owner_run_id, "prompt_id": "A3"}}}


def test_the_closing_run_is_kept_not_just_the_file_it_was_logged_in():
    """A ledger is a file; a run is not.

    `runs/a3-gate-mock/ledger.jsonl` holds three run_ids. `recovered_scorecards`
    is handed the whole file, so the identity of the run that made the close
    call -- which the record carries -- was dropped, and a pointer built from it
    could only ever name a directory. Single-run ledgers hide this by making the
    two coincide, which is why nothing in the archive triggers it.
    """
    records = [_close_record("r-aaa", "card-1", "r-dead", 9),
               _close_record("r-bbb", "card-2", "r-other", 4)]
    pairs = backfill.recovered_scorecards_with_closer(records)
    assert [c for c, _ in pairs] == ["r-aaa", "r-bbb"]
    # the older reader keeps working, unchanged
    assert [c["card_id"] for c in backfill.recovered_scorecards(records)] == [
        "card-1", "card-2"]


def test_a_pointer_into_a_multi_run_ledger_names_the_run(tmp_path):
    """The defect, built because the archive does not contain it.

    Three runs share one ledger and only the second closed the dead run's card.
    A pointer that stops at the directory sends a reader to a file holding three
    runs' records with no way to tell which one settled the number.
    """
    runs = tmp_path / "runs"
    (runs / "shared").mkdir(parents=True)
    (runs / "shared" / "ledger.jsonl").write_text(
        "\n".join(json.dumps(r) for r in [
            _close_record("r-first", "card-unrelated", "r-nobody", 1),
            _close_record("r-second", "card-of-the-dead", "r-dead", 9),
            _close_record("r-third", "card-also-unrelated", "r-nobody-else", 2),
        ]) + "\n", encoding="utf-8")

    found = backfill._scorecard_recovered_elsewhere(
        "r-dead", str(runs), self_slug="the-dead-run")

    assert found is not None, "the card is in the archive and was not found"
    assert found["closed_by_run_id"] == "r-second", (
        "the pointer names %r; the run that made the close call is r-second"
        % found.get("closed_by_run_id"))
    assert found["closed_by"] == "shared#r-second"
    assert found["total_actions"] == 9
    # and the directory is still reported, because it is still how you get there
    assert found["slug"] == "shared"


# ------------------------------- the number must be in the field that reports it
def test_a_recovered_count_lands_in_the_quota_block_not_only_in_the_pointer():
    """`quota.billed_actions_from_scorecard: null` was the wrong answer.

    It is this run's card -- opened by it, stamped with its `run_id`; a salvage
    only made the closing call. `…004020Z-leg01` reported null while the count
    of 9 sat one field away in `scorecard_recovered_by`, so a reader of the
    quota block alone saw nothing where the number was.
    """
    bare = {"billed_actions_from_ledger": 9, "billed_actions_from_scorecard": None}
    pointer = {"slug": "leg01-salvage", "closed_by": "leg01-salvage#r-sal",
               "card_id": "2ec0e679", "total_actions": 9}
    out = backfill._quota_with_recovered(dict(bare), pointer)

    assert out["billed_actions_from_scorecard"] == [9]
    assert out["agree"] is True
    assert out["billed_actions_from_scorecard_via"]["closed_by"] == \
        "leg01-salvage#r-sal", "the fill must say whose ledger it came out of"


def test_a_recovered_count_that_disagrees_is_a_finding_here():
    """The salvage note about expected disagreement must not be borrowed.

    On a salvage run, ledger-vs-API disagreement is expected: the card belongs
    to the parent. On the parent, the card is its own, so the two sides count
    the same thing and a mismatch is real.
    """
    out = backfill._quota_with_recovered(
        {"billed_actions_from_ledger": 9, "billed_actions_from_scorecard": None},
        {"slug": "s", "closed_by": "s#r", "card_id": "c", "total_actions": 7})
    assert out["agree"] is False
    assert "IS a finding" in out["note"]


def test_a_run_that_closed_its_own_card_is_left_alone():
    """The negative control: the fill must not touch a run that needs no help."""
    own = {"billed_actions_from_ledger": 5, "billed_actions_from_scorecard": [5],
           "agree": True}
    out = backfill._quota_with_recovered(dict(own), {"slug": "x", "total_actions": 99})
    assert out == own, "a run with its own scorecard was overwritten"


def test_no_pointer_and_no_count_leave_the_null_alone():
    bare = {"billed_actions_from_ledger": 0, "billed_actions_from_scorecard": None}
    assert backfill._quota_with_recovered(dict(bare), None) == bare
    assert backfill._quota_with_recovered(
        dict(bare), {"slug": "x", "total_actions": None}) == bare


# --------------------------------------------- and it has to actually be wired
def test_the_quota_fill_is_wired_into_build_not_merely_available(tmp_path):
    """The five tests above would all still pass with the call site deleted.

    Four of them poke `_quota_with_recovered` directly and the fifth pokes
    `_scorecard_recovered_elsewhere`; none of them goes through `build`. So a
    helper that exists, is correct, is tested, and is never called would look
    exactly like a fix. That is the same failure shape as a gate that is written
    and never invoked -- the one A16 exists to close on the spend path -- and it
    is worth one test on the public path here rather than a second incident.
    """
    runs = tmp_path / "runs"
    dead = runs / "20260729T004020Z-legX"
    dead.mkdir(parents=True)
    steps = [{"v": "1.0", "event": "env_step", "run_id": "r-dead",
              "http": {"path": "/api/cmd/ACTION1", "status": 200},
              "action": {"name": "ACTION1"}} for _ in range(9)]
    (dead / "ledger.jsonl").write_text(
        "\n".join(json.dumps(r) for r in [
            {"v": "1.0", "event": "run_start", "run_id": "r-dead",
             "ts": "2026-07-29T00:40:20Z", "game_id": "g50t-5849a774",
             "spend_gate": {"campaign": "theoria-arm:A3-campaign-devpile:"
                                        "g50t-5849a774:20260729T004020Z-legX"}},
            # `env_meta`, not `env_step` -- that is how the real leg01 ledger
            # logs the open, and it is why the open does not count as an action.
            {"v": "1.0", "event": "env_meta", "run_id": "r-dead",
             "http": {"path": "/api/scorecard/open", "status": 200},
             "response": {"card_id": "card-of-the-dead"}},
        ] + steps) + "\n", encoding="utf-8")

    salvage = runs / "20260729T004020Z-legX-salvage"
    salvage.mkdir()
    (salvage / "ledger.jsonl").write_text(json.dumps(
        _close_record("r-sal", "card-of-the-dead", "r-dead", 9)) + "\n",
        encoding="utf-8")

    manifest = backfill.build("20260729T004020Z-legX", runs_root=str(runs),
                              table={})

    quota = manifest["quota"]
    assert quota["billed_actions_from_scorecard"] == [9], (
        "build() left the quota block reporting %r -- the helper is not on the "
        "path that writes manifests" % quota["billed_actions_from_scorecard"])
    assert quota["agree"] is True
    assert quota["billed_actions_from_scorecard_via"]["closed_by"] == \
        "20260729T004020Z-legX-salvage#r-sal"
    # and the card is no longer counted as lost, which is the older half of it
    assert manifest["scorecards_opened_and_never_closed"] == []


# ------------------ a number the API can never hand back, said out loud
#
# `20260728T025503Z-g50t-e08-fixed` spent 13 billed actions and its session was
# killed before it could make the closing call. Every *other* unclosed card in
# this archive has a salvage behind it, so the number was only ever misfiled --
# recoverable, and recovered. This one is not: the API auto-closes an open card
# about fifteen minutes after the last action, and a closed card 404s on read
# (`arc-recon/ACCESS_CHECK.md` §3). The count is unobtainable **by
# construction**, and no amount of later tooling changes that.
#
# Which leaves two ways for the archive to be wrong about it and one way to be
# right. It can print a total nobody can defend, or it can go red on a gap
# nobody can close -- and a permanent red is the failure mode where somebody
# eventually widens the tolerance until the check stops meaning anything. The
# third option is to subtract it *by disclosure*: the manifest says which card
# and why, and the reconciliation names the run, the card and the count it is
# not reconciling. These tests pin the disclosure in both directions, because an
# exemption an undeclared gap can also claim is not an exemption -- it is a hole
# with better wording.

def _live_start(run_id):
    """A `run_start` that makes `classify` call the directory archive material.

    The non-loopback `env_upstream` is the load-bearing part: with `127.0.0.1`
    the directory classifies as `mock` and every check in `verify_provenance`
    skips it, so a fixture in that state asserts nothing at all.
    """
    return {"v": "1.0", "event": "run_start", "run_id": run_id, "arm": "theoria",
            "ts": "2026-07-28T02:55:03.738Z",
            "env_upstream": "https://three.arcprize.org"}


def _opened(run_id, card_id):
    """The scorecard open, logged as `env_meta`.

    That is how the arm logs it, and it is why opening a card is not itself a
    billed action -- `quota` counts `env_step` records only. A fixture that logs
    the open as a step inflates its own ledger total by one and quietly stops
    testing the arithmetic it was written for.
    """
    return {"v": "1.0", "event": "env_meta", "run_id": run_id,
            "http": {"path": "/api/scorecard/open", "status": 200},
            "request": {"tags": ["p8"]},
            "response": {"card_id": card_id}}


def _closed(run_id, card_id, total_actions, owner=None):
    return {"v": "1.0", "event": "env_meta", "run_id": run_id,
            "http": {"path": "/api/scorecard/close", "status": 200},
            "response": {"card_id": card_id, "total_actions": total_actions,
                         "total_levels_completed": 0, "score": 0.0,
                         "opaque": {"run_id": owner or run_id,
                                    "prompt_id": "P-8"}}}


def _billed(run_id, n):
    return [{"v": "1.0", "event": "env_step", "run_id": run_id,
             "http": {"path": "/api/cmd/ACTION1", "status": 200},
             "action": {"name": "ACTION1"}} for _ in range(n)]


def _write_ledger(run_dir, records):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "ledger.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_a_card_nobody_could_ever_close_is_declared_in_the_scorecard_slot(tmp_path):
    """`scorecard` absent reads as "this run has no scorecard".

    It has one. What it does not have is the number, and those are different
    facts. The absence was a lie of omission sitting in the field a reader looks
    in first -- and `verify_provenance` check 5, which asks every spending run to
    point at its card, could not tell that run apart from one that had simply
    never been given a manifest at all.
    """
    runs = tmp_path / "runs"
    _write_ledger(runs / "killed",
                  [_live_start("r-killed"), _opened("r-killed", "card-lost")]
                  + _billed("r-killed", 13))

    manifest = backfill.build("killed", runs_root=str(runs), table={})

    card = manifest.get("scorecard")
    assert card, ("the `scorecard` slot is empty for a run that opened one; a "
                  "reader is left to infer the loss from an absence")
    assert card["card_id"] == "card-lost"
    assert card["status"] == "opened_never_closed"
    assert card["total_actions"] is None, (
        "a total was invented for a card that 404s on read")
    assert "13" in card["note"], (
        "the note omits the 13 actions the ledger does hold, which is the only "
        "record there is")
    # and the older declaration is still there, because check 6 reads that one
    assert manifest["scorecards_opened_and_never_closed"] == ["card-lost"]


def test_a_run_that_spent_nothing_is_not_given_a_lost_number_to_mourn(tmp_path):
    """The cheap negative control: a pre-flight opens a card and closes nothing.

    `preflight-20260728T012031Z` is exactly that shape in the real archive. It
    spent no action, so there is no number for the API to be withholding, and a
    declaration of loss would file a zero-cost absence in the same column as 13
    genuinely unreconciled actions.
    """
    runs = tmp_path / "runs"
    _write_ledger(runs / "preflight-x",
                  [_live_start("r-pre"), _opened("r-pre", "card-untouched")])

    manifest = backfill.build("preflight-x", runs_root=str(runs), table={})

    assert "scorecard" not in manifest
    assert manifest["scorecards_opened_and_never_closed"] == ["card-untouched"]


def test_a_card_a_salvage_recovered_is_not_declared_lost(tmp_path):
    """The sharp negative control, and the one that would do real damage.

    These runs already have a real API number one directory over, in
    `scorecard_recovered_by`. A declaration of loss beside it would be two
    contradictory statements in the same file -- and worse, it would exempt from
    check 4 a set of actions that reconciles perfectly well, which is the exact
    failure the disclosure route exists to avoid.
    """
    runs = tmp_path / "runs"
    _write_ledger(runs / "dead",
                  [_live_start("r-dead"), _opened("r-dead", "card-c")]
                  + _billed("r-dead", 9))
    _write_ledger(runs / "dead-salvage",
                  [_live_start("r-sal"),
                   _closed("r-sal", "card-c", 9, owner="r-dead")])

    manifest = backfill.build("dead", runs_root=str(runs), table={})

    assert "scorecard" not in manifest, (
        "a recovered card was also declared lost; the manifest now says both")
    assert manifest["scorecard_recovered_by"]["total_actions"] == 9
    assert manifest["scorecards_opened_and_never_closed"] == []


# ------------------------------- and the reconciliation has to act on it
CHECK_FOUR = "billed actions reconcile: ledgers vs closed scorecards"


def _check_four(runs_root, monkeypatch):
    """Check 4's own verdict, from a real `run()` over the fixture tree.

    Not a local reimplementation of the split. A test that recomputes the check
    it is testing asserts that the code equals itself -- measured on check 10,
    where replacing its loop body with `for row in []` left the whole suite
    green.

    `armversion.scan` is stubbed because it walks every ref in a repository
    carrying hundreds of worktrees (136 s, measured). It belongs to check 8,
    whose verdict goes deliberately unread here: these fixture manifests are
    hand-written and re-derivation will not reproduce them, which is check 8
    working rather than a fact about check 4.
    """
    from armtools import armversion, verify_provenance   # noqa: PLC0415

    monkeypatch.setattr(armversion, "scan", lambda *a, **k: {})
    rows = [r for r in verify_provenance.run(str(runs_root)).rows
            if r["check"] == CHECK_FOUR]
    assert len(rows) == 1, "check 4 did not run at all: %r" % rows
    return rows[0]


def _two_run_archive(tmp_path):
    """One run that closed its card, one whose card can never be closed.

    4 billed actions behind a card the API says was billed 4, and 13 behind a
    card that was opened and abandoned. The ledgers total 17; the only API
    arithmetic in existence covers 4 of them.
    """
    runs = tmp_path / "runs"
    _write_ledger(runs / "closed-its-card",
                  [_live_start("r-ok"), _opened("r-ok", "card-ok")]
                  + _billed("r-ok", 4) + [_closed("r-ok", "card-ok", 4)])
    _write_ledger(runs / "session-was-killed",
                  [_live_start("r-killed"), _opened("r-killed", "card-lost")]
                  + _billed("r-killed", 13))
    return runs


def _declare(runs, slug, payload):
    (runs / slug / "MANIFEST.json").write_text(json.dumps(payload),
                                               encoding="utf-8")


def test_a_declared_unclosed_card_reconciles_by_disclosure(tmp_path, monkeypatch):
    """The passing shape -- and the detail string is half of what it asserts.

    Passing quietly on 17-vs-4 would be worse than the red it replaces. This
    check exists to be the number Phase 4 defends, so "we did not count 13 of
    them" has to be legible in the one line the gate prints. The split is
    asserted, and so are the run and the card it names.
    """
    runs = _two_run_archive(tmp_path)
    _declare(runs, "session-was-killed",
             {"scorecards_opened_and_never_closed": ["card-lost"]})

    row = _check_four(runs, monkeypatch)

    assert row["ok"] is True, row["detail"]
    detail = row["detail"]
    assert "ledgers say 17 = 4 reconciled" in detail, detail
    assert "13 declared unreconcilable" in detail, detail
    assert "session-was-killed" in detail and "card-lost" in detail, (
        "the exemption is anonymous: %s" % detail)


def test_an_undeclared_gap_still_fails(tmp_path, monkeypatch):
    """The same 13 actions, with nothing in the archive owning up to them.

    This is the assertion that makes the one above mean anything. If the split
    were driven by "the ledger and the cards disagree" rather than by "a
    manifest says which card and why", every future gap would exempt itself and
    the check would have been repaired into a decoration.
    """
    runs = _two_run_archive(tmp_path)          # no manifest for the killed run

    row = _check_four(runs, monkeypatch)

    assert row["ok"] is False, (
        "13 undeclared actions dropped out of the account silently: %s"
        % row["detail"])
    assert "MISMATCH" in row["detail"]
    assert "ledgers say 17 = 17 reconciled" in row["detail"], row["detail"]


def test_declaring_some_other_card_buys_no_exemption(tmp_path, monkeypatch):
    """The exemption is per card, not per run.

    A declaration naming a card the run never opened must not carry the run's
    real orphan out of the reconciled column with it. Loose matching -- "this
    run declared *something*, so exempt it" -- would let one honest disclosure
    launder every later one.
    """
    runs = _two_run_archive(tmp_path)
    _declare(runs, "session-was-killed",
             {"scorecards_opened_and_never_closed": ["a-card-from-another-run"]})

    row = _check_four(runs, monkeypatch)

    assert row["ok"] is False, row["detail"]
    assert "MISMATCH" in row["detail"]


def test_the_scorecard_slot_alone_is_enough_to_declare(tmp_path, monkeypatch):
    """Either form declares, because two writers write them.

    `backfill.build` emits both the list and the `scorecard` block; a manifest
    written by hand may carry only one. Requiring both would make the exemption
    depend on which tool wrote the file rather than on what the file says.
    """
    runs = _two_run_archive(tmp_path)
    _declare(runs, "session-was-killed",
             {"scorecard": {"card_id": "card-lost",
                            "status": "opened_never_closed",
                            "total_actions": None}})

    assert _check_four(runs, monkeypatch)["ok"] is True


def test_a_scorecard_block_without_the_status_declares_nothing(tmp_path,
                                                               monkeypatch):
    """Only an explicit `opened_never_closed` exempts.

    Otherwise any manifest carrying a `scorecard` key -- including one simply
    asserting a total nobody read back from the API -- would exempt its own run
    from the arithmetic that exists to check exactly that kind of claim.
    """
    runs = _two_run_archive(tmp_path)
    _declare(runs, "session-was-killed",
             {"scorecard": {"card_id": "card-lost", "total_actions": 13}})

    row = _check_four(runs, monkeypatch)

    assert row["ok"] is False, row["detail"]
    assert "MISMATCH" in row["detail"]


def test_the_killed_run_in_this_archive_carries_its_declaration():
    """Over the real artefact, which is what the claim is actually about.

    The fixtures above prove the rule; this proves it was applied to the run the
    rule was written for. Skipped rather than failed where the run is absent --
    this file is read in worktrees that predate it.
    """
    slug = "20260728T025503Z-g50t-e08-fixed"
    path = os.path.join(RUNS_DIR, slug, "MANIFEST.json")
    if not os.path.exists(path):
        pytest.skip("%s is not in this tree" % slug)
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    card = manifest.get("scorecard") or {}
    assert card.get("status") == "opened_never_closed", (
        "the run whose card auto-closed server-side does not say so: %r" % card)
    assert card["card_id"] in manifest["scorecards_opened_and_never_closed"]
    assert card["total_actions"] is None
    assert manifest["quota"]["billed_actions_from_ledger"] == 13
