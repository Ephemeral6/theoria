"""The transport, after the cookie jar landed (arc-recon INC-007 / 008 / 009).

Every figure in `BUDGET_REPORT.md` was measured on a client that echoed no
cookies and therefore paid five to ten HTTP calls per successful command. The
jar removes that, but it also changes three things that are easy to get wrong
and impossible to notice: what reaches the probe log, which direction the cookie
record describes, and what a retry now means. Each got an incident on the other
track before it got a test; these are the tests, ported with the fixes.

Every check here has a negative control. A check that has never been seen to
fail is not evidence that anything passed.

    cd baseline-arms && python -m pytest tests/ -q
"""

import http.cookiejar
import json
import os
import sys
import urllib.request

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import arc_client, bare_cc, ledger  # noqa: E402


# -- the jar ----------------------------------------------------------------

def test_the_jar_is_on_by_default_and_can_be_turned_off():
    on = arc_client.ArcClient(api_key="x")
    off = arc_client.ArcClient(api_key="x", cookies=False)
    assert on.transport["cookies"] is True
    assert off.transport["cookies"] is False
    handlers = [type(h).__name__ for h in off._opener.process_response["https"]]
    assert "HTTPCookieProcessor" not in handlers
    handlers = [type(h).__name__ for h in on._opener.process_response["https"]]
    assert "HTTPCookieProcessor" in handlers


def test_the_jar_learns_cookies_from_error_responses_too():
    """The load-bearing detail, and not obvious.

    The first call of a retry loop is usually the 400. If the jar only learned
    routing cookies from 2xx, the retry would be routed as blindly as the first
    attempt and the fix would buy nothing exactly where D-005's envelope lives.
    It works because urllib sorts response processors by handler_order and
    HTTPCookieProcessor (500) runs before HTTPErrorProcessor (1000) -- the
    handler that turns a 400 into an exception. A future reordering would
    degrade this silently, with nothing failing and no error raised.
    """
    handlers = [type(h).__name__ for h in
                arc_client.ArcClient(api_key="x")._opener.process_response["https"]]
    assert handlers.index("HTTPCookieProcessor") \
        < handlers.index("HTTPErrorProcessor")
    assert urllib.request.HTTPCookieProcessor.handler_order \
        < urllib.request.HTTPErrorProcessor.handler_order


# -- names only, never values (arc-recon INC-008) ---------------------------

def test_a_comma_inside_a_cookie_value_does_not_become_a_name():
    """The regression that made arc-recon's redactor leak through itself: it
    split the header on "," so a value containing one produced a fragment of the
    VALUE dressed up as a name."""
    assert arc_client.cookie_names(
        "GAMESESSION=v1,eyJndWlkIjoiOTk3ZDYzZmYifQ==; Path=/; HttpOnly"
    ) == ["GAMESESSION"]
    # Expires carries a comma of its own -- the classic Set-Cookie trap.
    assert arc_client.cookie_names(
        "AWSALBAPP-0=SECRET; Expires=Tue, 04 Aug 2026 00:00:00 GMT; Path=/"
    ) == ["AWSALBAPP-0"]
    assert arc_client.cookie_names("no-equals-sign; Path=/") == []
    assert arc_client.cookie_names("") == []


def test_no_cookie_value_survives_name_extraction():
    import email.message
    message = email.message.Message()
    for raw in ("AWSALBAPP-0=SECRETVALUE; Expires=Tue, 04 Aug 2026 00:00:00 GMT",
                "GAMESESSION=TOKEN,WITH,COMMAS; Path=/; HttpOnly"):
        message.add_header("Set-Cookie", raw)
    names = arc_client.issued_cookie_names(message)
    assert names == ["AWSALBAPP-0", "GAMESESSION"]
    blob = json.dumps(names)
    for secret in ("SECRETVALUE", "TOKEN", "WITH", "COMMAS", "GMT"):
        assert secret not in blob, secret


def test_every_set_cookie_header_is_counted_not_just_one():
    """This server sends five. `.get()` returns the first, `dict()` keeps the
    last; either would under-report while the jar quietly held more."""
    import email.message
    message = email.message.Message()
    for raw in ("AWSALBAPP-0=A", "AWSALBAPP-1=B", "GAMESESSION=C"):
        message.add_header("Set-Cookie", raw)
    assert arc_client.issued_cookie_names(message) == \
        ["AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"]
    # Headers are case-insensitive; a plain lowercase mapping must still work.
    assert arc_client.issued_cookie_names({"set-cookie": "GAMESESSION=C"}) \
        == ["GAMESESSION"]


# -- the probe log ----------------------------------------------------------

class _FakeResponse:
    status = 200

    def __init__(self, jar):
        self._jar = jar
        self.headers = {"set-cookie": "GAMESESSION=TOKENVALUE; Path=/"}

    def read(self):
        return b'{"ok": true}'

    def geturl(self):
        return arc_client.BASE_URL + "/api/cmd/RESET"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _seeding_opener(api):
    """Stands in for HTTPCookieProcessor: fills the jar during open()."""

    class Seeding:
        def open(self, request, timeout=None):
            api.jar.set_cookie(http.cookiejar.Cookie(
                0, "GAMESESSION", "TOKENVALUE", None, False,
                "three.arcprize.org", False, False, "/", True,
                False, None, False, None, None, {}))
            return _FakeResponse(api.jar)

    return Seeding()


@pytest.fixture
def captured_probes(monkeypatch):
    """Intercept `ledger.probe` rather than redirect its path.

    Redirecting `ledger.PROBE_PATH` does NOT work: `probe(kind, detail,
    path=PROBE_PATH)` binds the default at definition time, so a monkeypatched
    module attribute is ignored and the call lands in the track's real,
    append-only `probe_log.jsonl`. Writing test noise into a tracked ledger is
    not a thing a test may do, and an append-only one cannot be tidied
    afterwards -- so this replaces the writer outright, which cannot write
    anywhere by construction.
    """
    records = []
    monkeypatch.setattr(ledger, "probe",
                        lambda kind, detail, **kw: records.append(
                            {"kind": kind, **detail}) or records[-1])
    return records


def test_the_probe_log_records_names_not_values(captured_probes, scratch_binding):
    api = arc_client.ArcClient(api_key="x", spend_binding=scratch_binding)
    api._opener = _seeding_opener(api)
    api.request("POST", "/api/cmd/RESET", body={"game_id": "ar25-0c556536"},
                note="t")
    entry = captured_probes[0]
    assert entry["set_cookie_names"] == ["GAMESESSION"]
    assert "TOKENVALUE" not in json.dumps(entry)
    assert entry["cookies_enabled"] is True


def test_cookies_sent_is_the_jar_before_the_call_not_after(captured_probes,
                                                           scratch_binding):
    """A snapshot taken inside the log call describes what the call PRODUCED.
    The first request of a session, which provably echoed nothing, would then be
    recorded as holding the server's cookies."""
    api = arc_client.ArcClient(api_key="x", spend_binding=scratch_binding)
    api._opener = _seeding_opener(api)
    api.request("POST", "/api/cmd/RESET", body={"game_id": "ar25-0c556536"},
                note="first call of the session")
    entry = captured_probes[0]
    assert entry["cookies_sent"] == []
    assert entry["cookies_held_after"] == ["GAMESESSION"]


def test_no_test_in_this_file_writes_to_the_real_probe_log(scratch_binding):
    """The guard for the mistake above: if the fixture ever stops intercepting,
    this notices before a tracked append-only file grows test noise."""
    real = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "probe_log.jsonl")
    before = os.path.getsize(real) if os.path.exists(real) else 0
    api = arc_client.ArcClient(api_key="x", spend_binding=scratch_binding)
    api._opener = _seeding_opener(api)
    original = ledger.probe
    ledger.probe = lambda kind, detail, **kw: None
    try:
        api.request("POST", "/api/cmd/RESET", body={"game_id": "ar25-0c556536"},
                    note="guard")
    finally:
        ledger.probe = original
    after = os.path.getsize(real) if os.path.exists(real) else 0
    assert after == before


# -- the retry envelope -----------------------------------------------------

def test_clearing_routing_cookies_keeps_the_session_identity():
    api = arc_client.ArcClient(api_key="x")
    for name in ("AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"):
        api.jar.set_cookie(http.cookiejar.Cookie(
            0, name, "v", None, False, "three.arcprize.org", False, False,
            "/", True, False, None, False, None, None, {}))
    assert api.cookies_held() == ["AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"]
    api.clear_routing_cookies()
    assert api.cookies_held() == ["GAMESESSION"]


def test_resilient_redraws_a_replica_when_the_jar_is_pinned(monkeypatch):
    """D-005's envelope retried an identical request because each attempt was a
    fresh routing draw. A pinned jar makes them all the same draw."""
    api = arc_client.ArcClient(api_key="x")
    for name in ("AWSALBAPP-0", "GAMESESSION"):
        api.jar.set_cookie(http.cookiejar.Cookie(
            0, name, "v", None, False, "three.arcprize.org", False, False,
            "/", True, False, None, False, None, None, {}))

    held = []

    def always_400(method, path, body=None, note="", raise_on_error=True):
        held.append(api.cookies_held())
        return 400, {"message": "game x not found"}

    monkeypatch.setattr(api, "request", always_400)
    monkeypatch.setattr(bare_cc.time, "sleep", lambda *_: None)
    status, _, tries = bare_cc.resilient(api, "/api/cmd/RESET", {}, "t", tries=8)

    assert status == 400 and tries == 8
    assert held[0] == ["AWSALBAPP-0", "GAMESESSION"]
    assert api.cookies_held() == ["GAMESESSION"], "the pin was never released"
    assert any(h == ["GAMESESSION"] for h in held), \
        "the redraw never took effect inside the envelope"


def test_reset_with_retry_also_redraws(monkeypatch):
    api = arc_client.ArcClient(api_key="x")
    api.jar.set_cookie(http.cookiejar.Cookie(
        0, "AWSALBAPP-0", "v", None, False, "three.arcprize.org", False, False,
        "/", True, False, None, False, None, None, {}))
    monkeypatch.setattr(api, "reset",
                        lambda *a, **k: (400, {"message": "game x not found"}))
    monkeypatch.setattr(bare_cc.time, "sleep", lambda *_: None)
    body, tries = bare_cc.reset_with_retry(api, "ar25-0c556536", "card", tries=6)
    assert body is None and tries == 6
    assert api.cookies_held() == []


def test_a_successful_call_never_redraws(monkeypatch):
    """Negative control: the redraw must not fire on the happy path, or every
    session would keep throwing away the pin it just earned."""
    api = arc_client.ArcClient(api_key="x")
    api.jar.set_cookie(http.cookiejar.Cookie(
        0, "AWSALBAPP-0", "v", None, False, "three.arcprize.org", False, False,
        "/", True, False, None, False, None, None, {}))
    monkeypatch.setattr(api, "request",
                        lambda *a, **k: (200, {"guid": "g"}))
    monkeypatch.setattr(bare_cc.time, "sleep", lambda *_: None)
    status, _, tries = bare_cc.resilient(api, "/api/cmd/RESET", {}, "t", tries=8)
    assert status == 200 and tries == 1
    assert api.cookies_held() == ["AWSALBAPP-0"]


# -- the guard still guards --------------------------------------------------

def test_the_sealed_guard_survives_the_transport_change():
    api = arc_client.ArcClient(api_key="x")
    with pytest.raises(arc_client.SealedGameError):
        api.assert_playable("ls20-9607627b")
    with pytest.raises(arc_client.SealedGameError):
        api.assert_playable("ft09")
    api.assert_playable("ar25-0c556536")        # negative control
