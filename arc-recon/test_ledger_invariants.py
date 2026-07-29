"""The ledger invariant, and the proof that it can go red.

`test_hygiene.py`'s docstring is the standing rule here and it is repeated
because this file is the reason it exists:

> "Every check here has a negative control. A check that has never been seen to
> fail is not evidence that anything passed -- INC-003 is exactly the case where
> a comparison that could not fail reported PASS for two runs that had both
> died."

So each shape `tools/ledger_invariants.py` claims to detect is planted here and
asserted to be found, and a clean row is asserted to stay clean. A detector that
flags everything is as useless as one that flags nothing, and only the pair of
assertions distinguishes either from a working one.

**Every planted value is obviously synthetic.** `CLAUDE.md`'s credential rule
covers test fixtures by name, and a fixture holding a realistic-looking bearer
token would be the exact artefact this module exists to keep out of the tree.
The plants match the *shape* and nothing else, and they are built in memory —
`scan_rows` exists so that a negative control never has to write one to disk.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tools import ledger_invariants as inv        # noqa: E402

#: Obviously not a credential. Long enough to trip the shapes, and it is the
#: string the leak-probe test below looks for in the report.
FAKE = "SYNTHETIC-NOT-A-REAL-TOKEN-000000"
FAKE_JWT = "eyJSYNTHETIC-NOT-REAL"


def _clean_row():
    return {
        "t": "2026-07-28T00:00:00Z", "method": "GET",
        "url": "https://three.arcprize.org/api/games",
        "note": "list available games", "status": 200, "elapsed_ms": 1,
        "request_headers": {"Accept": "application/json",
                            "X-API-Key": inv.REDACTED},
        "request_body": None, "response_body": "[]",
        "set_cookie": "<redacted INC-008>",
        "set_cookie_names": ["GAMESESSION"],
    }


# --------------------------------------------------------- the real artefact

def test_the_shipped_ledger_satisfies_its_own_invariant():
    """Over the file on disk, whoever wrote each line.

    This is the assertion `probe_stickiness.py` could not have failed by writing
    its own opener, because it does not ask who wrote the line.
    """
    report = inv.assert_clean()
    assert report["total_lines"] > 0
    assert report["malformed_lines"] == []


def test_every_other_tracks_ledger_is_scanned_too():
    report = inv.audit_all()
    assert report["ledgers_scanned"] >= 1
    assert report["all_clean"] is True
    assert "arc-recon/data/recon_ledger.jsonl" in report["ledgers"]
    assert report["caveat"], "a clean sweep must ship its own scope statement"


def test_an_absent_ledger_is_reported_absent_and_not_clean():
    """`clean: None`, not `clean: True`. A file that is not there is not a file
    that passed, and folding the two together is how a sweep starts reporting
    green for tracks it never opened."""
    report = inv.audit_all()
    for row in report["ledgers"].values():
        if row.get("present") is False:
            assert row["clean"] is None
            break


# ------------------------------------------------------- the negative controls

@pytest.mark.parametrize("planted,expect_field", [
    # INC-008 verbatim: the raw Set-Cookie header, values and all.
    ({"set_cookie": "GAMESESSION=%s; Path=/; HttpOnly" % FAKE}, "set_cookie"),
    # INC-008's other half: the value smuggled into a NAME list, which is what
    # the redactor itself once produced by splitting on a comma inside a value.
    ({"set_cookie_names": ["GAMESESSION=%s" % FAKE]}, "set_cookie_names"),
    ({"cookies_sent": ["AWSALBAPP-0=%s" % FAKE]}, "cookies_sent"),
    ({"cookies_held": ["GAMESESSION=%s" % FAKE]}, "cookies_held"),
    ({"cookies_held_after": ["x=%s" % FAKE]}, "cookies_held_after"),
    # The credential the ledger was built around.
    ({"request_headers": {"X-API-Key": FAKE}}, "request_headers.X-API-Key"),
    ({"request_headers": {"Authorization": "Bearer %s" % FAKE}},
     "request_headers.Authorization"),
    ({"request_headers": {"Cookie": "GAMESESSION=%s" % FAKE}},
     "request_headers.Cookie"),
    # A bearer shape in a header nobody classified as secret.
    ({"request_headers": {"X-Trace": FAKE_JWT}}, "request_headers.X-Trace"),
    # In the URL, which no writer redacts today because none has put one there.
    ({"url": "https://three.arcprize.org/api/games?api_key=%s" % FAKE},
     "url?api_key"),
    ({"url": "https://three.arcprize.org/api/games?session_token=%s" % FAKE},
     "url?session_token"),
    ({"url": "https://three.arcprize.org/api/%s" % FAKE_JWT}, "url"),
    # The next INC-008: a field nobody predicted, failing closed.
    ({"session_token": FAKE}, "session_token"),
    ({"auth_blob": FAKE}, "auth_blob"),
    ({"my_api_key": FAKE}, "my_api_key"),
    # A JWT shape in free text.
    ({"note": "opened with %s" % FAKE_JWT}, "note"),
    ({"transport_error": "refused after %s" % FAKE_JWT}, "transport_error"),
])
def test_the_detector_goes_red_on_each_shape_it_claims(planted, expect_field):
    row = dict(_clean_row())
    row.update(planted)
    found = inv.scan_rows([(1, row)])
    assert found, "planted %r and the scanner found nothing" % sorted(planted)
    assert any(v["field"] == expect_field for v in found), found


def test_the_literal_secret_is_caught_wherever_it_lands():
    """Tier 2, which does not need to know the schema.

    The point of this tier is the field nobody thought of, so the plant goes in
    `response_body` — a field tier 4 deliberately does not scan, because game
    frames are arbitrary data and a shape check there would cry wolf every run.
    """
    row = dict(_clean_row(), response_body='{"x": "%s"}' % FAKE)
    assert inv.scan_rows([(1, row)], secret=FAKE)
    # ...and the same row is clean when that string is not the secret.
    assert inv.scan_rows([(1, row)], secret="a-different-string") == []


def test_a_clean_row_stays_clean():
    """The other half. A detector that flags everything proves nothing either."""
    assert inv.scan_rows([(1, _clean_row())], secret=FAKE) == []


def test_a_declared_field_is_not_flagged_merely_for_its_name():
    """`set_cookie_names` matches the credential-name pattern and is correct.

    Tier 3 fails closed on *undeclared* fields; if it fired on declared ones too
    the real ledger could never be green, and the tier would have been softened
    into a warning within a day. Both halves are asserted: the declared fields
    really do match the pattern (so the exemption is load-bearing rather than
    incidental), and a row made only of them is clean.
    """
    matching = {f for f in inv.DECLARED_FIELDS if inv.CREDENTIAL_NAME.search(f)}
    assert matching, "no declared field matches the pattern; tier 3 exempts nothing"

    # The rest are declared because tier 1 governs them by name rather than
    # because tier 3 would otherwise refuse them, and the two reasons should not
    # be conflated: a field in the second group carries no exemption at all.
    tier_one_governed = {"request_headers", "set_cookie"} \
        | set(inv.COOKIE_NAME_FIELDS)
    assert set(inv.DECLARED_FIELDS) - matching <= tier_one_governed, (
        "declared, unmatched by the pattern, and governed by no tier-1 rule — "
        "so the declaration is a suppression rather than a statement: %s"
        % sorted(set(inv.DECLARED_FIELDS) - matching - tier_one_governed))

    assert inv.scan_rows([(1, _clean_row())]) == []


def test_every_credential_shaped_field_in_the_real_ledger_is_declared():
    """Tier 3 is not vacuous on the artefact it guards.

    If the shipped ledger contained an undeclared credential-shaped field this
    would be red — and if it contained *no* such field at all, the tier would be
    untested against reality, so this also asserts the intersection is non-empty.
    """
    seen = set()
    with open(inv.LEDGER_PATH, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                seen.update(json.loads(line).keys())
    shaped = {f for f in seen if inv.CREDENTIAL_NAME.search(f)}
    assert shaped, "no credential-shaped field in the ledger; tier 3 is untested"
    assert shaped <= set(inv.DECLARED_FIELDS), sorted(shaped - set(inv.DECLARED_FIELDS))


# ------------------------------------------------- the module's own two rules

def test_a_report_never_carries_the_value_it_found():
    """The rule that keeps the scanner from becoming a second copy of the leak.

    Reports get printed, pasted into commit messages and written into run
    directories. A violation is `(line, field, shape)` and nothing else, and this
    asserts it over the serialised report rather than by reading the code.
    """
    row = dict(_clean_row())
    row.update({"set_cookie": "GAMESESSION=%s; Path=/" % FAKE,
                "session_token": FAKE,
                "request_headers": {"X-API-Key": FAKE}})
    found = inv.scan_rows([(1, row)], secret=FAKE)
    assert len(found) >= 3
    blob = json.dumps(found, sort_keys=True)
    assert FAKE not in blob, "the report echoed the value back"
    assert "GAMESESSION=" not in blob


def test_the_live_key_comparison_reports_whether_it_ran():
    """A check that did not run must not read as a check that passed.

    `.env` is gitignored and absent in a fresh worktree, so this tier genuinely
    does not always run. `live_key_comparison` is the field that says which
    happened; without it a scan of a ledger full of keys, on a machine with no
    `.env`, would print `clean`.
    """
    report = inv.scan(check_secret=False)
    assert report["live_key_comparison"] == "not requested"
    report = inv.scan(secret="a-string-that-is-in-no-ledger")
    assert report["live_key_comparison"] == "supplied by caller"
    assert report["clean"] is True


def test_malformed_lines_are_not_silently_clean(tmp_path):
    """A line the scanner cannot parse is a line nothing has checked."""
    path = tmp_path / "ledger.jsonl"
    path.write_text(json.dumps(_clean_row()) + "\nnot json at all\n",
                    encoding="utf-8")
    report = inv.scan(str(path), check_secret=False)
    assert report["malformed_lines"] == [2]
    assert report["clean"] is False, "a line nothing could read came back clean"


def test_the_scanner_finds_a_planted_offender_on_disk(tmp_path):
    """`scan` and `scan_rows` are the same predicate, asserted rather than assumed.

    The negative controls run in memory so that no fixture holding a
    credential-shaped string is ever written into the tree. That leaves the file
    reader itself unexercised against an offender, and this closes it — outside
    the repository, under pytest's temp directory, deleted with the run.
    """
    row = dict(_clean_row(), set_cookie="GAMESESSION=%s; Path=/" % FAKE)
    path = tmp_path / "ledger.jsonl"
    path.write_text(json.dumps(_clean_row(), sort_keys=True) + "\n"
                    + json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    report = inv.scan(str(path), check_secret=False)
    assert report["clean"] is False
    assert [v["line"] for v in report["violations"]] == [2]
    assert FAKE not in json.dumps(report, sort_keys=True)

    with pytest.raises(inv.LedgerInvariantError) as excinfo:
        inv.assert_clean(str(path))
    assert FAKE not in str(excinfo.value), "the exception echoed the value back"


# -------------------------------------------------------- the shape of the fix

def test_the_second_writer_is_still_there_and_the_invariant_still_holds():
    """The whole argument for putting this on the resource, as an assertion.

    INC-008's repair was not "make `client._record` the only writer".
    `probe_stickiness.py` still opens the ledger itself, because it needs
    response headers `_record` does not capture, and that is a legitimate need
    rather than abuse. If someone later collapses it to a single writer, this
    test failing should prompt reading `tools/ledger_invariants.py`'s docstring
    before deleting it: the invariant does not depend on the collapse, and a
    single entry point is only worth it where a capability can actually be taken
    away.
    """
    source = open(os.path.join(HERE, "probe_stickiness.py"), encoding="utf-8").read()
    assert 'open(LEDGER_PATH, "a"' in source, (
        "the second writer is gone; the invariant does not need it gone, and "
        "this test is a prompt to read why, not a requirement to keep it")
    inv.assert_clean()
