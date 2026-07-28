"""Red-team suite: attacks on the double proxy's three claims.

This file is adversarial by design. It is not a unit test of intended
behaviour -- it is the standing evidence for `proxy/REDTEAM.md`, and it is meant
to stay resident in the suite so that a finding cannot be quietly lost.

Reading it:

  * Every test here asserts that an attack is **blocked**, and every one of
    them passes. The suite is therefore a standing regression guard: if someone
    later widens the surface, it goes red on the exact attack that widening
    re-opens.
  * A test carrying a `# Landed when this suite was written; closed by P-9`
    comment is one of the 29 attacks that **succeeded** on first contact. The
    comment is the finding, kept verbatim next to the code that closes it,
    because a fix whose reason is lost is a fix somebody eventually reverts.
  * The remaining tests were blocked from the start and are here so that stays
    true.

`proxy/REDTEAM.md` is the report: what was tried, what landed, and the four
limitations that are documented rather than closed.

Rules of engagement honoured here: no network beyond loopback, no real
credential (every key in this file is a synthetic literal), and no sealed-pile
game is ever *played* -- sealed ids appear only as strings in attack payloads
aimed at loopback sinks that this file itself defines.
"""

import base64
import hashlib
import json
import os
import socket
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

import pytest

from proxy.env_proxy import EnvProxy, EnvProxyConfig
from proxy.guard import PilesIntegrityError, SealedPileGuard, load_piles
from proxy.ledger import Ledger, RunLedger, read_ledger
from proxy.model_proxy import ModelProxy, ModelProxyConfig
from proxy.paths import PILES
from proxy.reconcile import reconcile_run, scorecard_score
from proxy.redact import VAULT, Vault, looks_like_credential

# -- fixtures of the attack -------------------------------------------------

#: A sealed-pile id (piles.json cut v1). Used ONLY as a string in payloads
#: aimed at the loopback sinks defined in this file. Nothing here plays it.
SEALED = "ls20-9607627b"
SEALED_STEM = "ls20"
DEV = "ar25-0c556536"

#: Synthetic credentials. Not read from `.env`, not related to any real key.
ARC_KEY = "synthetic-arc-key-AAAABBBBCCCCDDDD"
MODEL_KEY = "synthetic-model-key-EEEEFFFF00001111"
SHORT_KEY = "shortkey"                       # under redact.MIN_SECRET_LEN
FOREIGN_KEY = "7f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"   # 36 chars, UUID-shaped


class Recorder(BaseHTTPRequestHandler):
    """A loopback sink that records every request it is handed.

    `server.seen` accumulates dicts; `server.reply` decides the answer. Two
    instances of this stand in for "the upstream the operator chose" and "some
    other host on the internet", so an egress attack is observable as: which
    sink's list grew.
    """

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):                 # keep pytest output clean
        pass

    def _handle(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        self.server.seen.append({                              # type: ignore[attr-defined]
            "path": self.path,
            "body": raw.decode("utf-8", "replace"),
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "api_key": self.headers.get("X-API-Key") or self.headers.get("x-api-key"),
        })
        status, body, headers = self.server.reply(self)        # type: ignore[attr-defined]
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_DELETE = _handle


def _default_reply(handler) -> Tuple[int, Any, Dict[str, str]]:
    return 200, {"ok": True, "state": "NOT_FINISHED", "frame": [[[0]]],
                 "score": 0, "levels_completed": 0, "usage": {"input_tokens": 1}}, \
        {"Content-Type": "application/json"}


class Sink:
    """A started loopback server plus the list of what it saw."""

    def __init__(self, reply=_default_reply):
        self.seen: List[Dict[str, Any]] = []
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Recorder)
        self.httpd.seen = self.seen                            # type: ignore[attr-defined]
        self.httpd.reply = reply                               # type: ignore[attr-defined]
        self.httpd.daemon_threads = True
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return "http://127.0.0.1:%d" % self.httpd.server_address[1]

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    def __enter__(self) -> "Sink":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self._thread.join(timeout=5)


def env_proxy_over(upstream: str, tmp_path, *, api_key: str = ARC_KEY,
                   run_id: str = "r-red", **kwargs) -> EnvProxy:
    cfg = EnvProxyConfig(run_id=run_id, arm="mock_arm", upstream=upstream,
                         api_key=api_key, require_key=False,
                         ledger=Ledger(str(tmp_path / "l.jsonl")), **kwargs)
    return EnvProxy(cfg)


def model_proxy_over(upstream: str, tmp_path, *, api_key: str = MODEL_KEY,
                     run_id: str = "r-red") -> ModelProxy:
    cfg = ModelProxyConfig(run_id=run_id, arm="mock_arm", upstream=upstream,
                           api_key=api_key, require_key=False,
                           ledger=Ledger(str(tmp_path / "l.jsonl")))
    return ModelProxy(cfg)


def call(url: str, *, method: str = "POST", data: Optional[bytes] = None,
         headers: Optional[Dict[str, str]] = None,
         ) -> Tuple[int, Dict[str, str], str]:
    request = urllib.request.Request(url, data=data, method=method,
                                     headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, dict(response.headers.items()), \
                response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()) if exc.headers else {}, \
            exc.read().decode("utf-8", "replace")


def post_json(base: str, path: str, body: Any,
              headers: Optional[Dict[str, str]] = None):
    return call(base.rstrip("/") + path, data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", **(headers or {})})


def raw_request(host: str, port: int, request_line: str, *,
                extra: bytes = b"", body: bytes = b"") -> bytes:
    """Speak HTTP by hand -- the only way to send a request line urllib refuses
    to build (absolute-URI, CONNECT, a smuggled body)."""
    conn = socket.create_connection((host, port), timeout=5)
    message = (request_line.encode() + b"\r\nHost: 127.0.0.1\r\n"
               + extra
               + (b"Content-Length: %d\r\n" % len(body) if extra.find(b"Transfer-Encoding") < 0 else b"")
               + b"\r\n" + body)
    conn.sendall(message)
    data = b""
    try:
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
    except OSError:
        pass
    finally:
        conn.close()
    return data.split(b"\r\n")[0]


def ledger_bytes(tmp_path) -> str:
    path = str(tmp_path / "l.jsonl")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def incidents(tmp_path, kind: Optional[str] = None) -> List[Dict[str, Any]]:
    return [r for r in read_ledger(str(tmp_path / "l.jsonl"))
            if r.get("event") == "incident" and (kind is None or r.get("kind") == kind)]


# ===========================================================================
# Class A -- egress around the proxies
# ===========================================================================

def _redirect_to(target: str):
    def reply(handler):
        return 302, b"", {"Location": target + "/stolen", "Content-Type": "text/plain"}
    return reply


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-01: urllib follows redirects and carries the injected X-API-Key to the
# redirect target, so a 302 from the upstream (or anyone who can answer as it)
# exfiltrates the ARC credential to a host the operator never chose
def test_red01_a_redirect_does_not_carry_the_credential_off_host(tmp_path):
    with Sink() as thief:
        with Sink(reply=_redirect_to(thief.url)) as upstream:
            with env_proxy_over(upstream.url, tmp_path) as proxy:
                post_json(proxy.base_url, "/api/cmd/RESET", {"game_id": DEV})
        stolen = [r for r in thief.seen if r["api_key"] == ARC_KEY]
    assert stolen == [], (
        "the injected credential was replayed to %d request(s) on a second host"
        % len(stolen))


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-02: the same redirect is recorded as a clean single-attempt 200 to the
# original path -- the ledger contains no trace that the bytes went to another
# host, so the 'complete record' property fails silently
def test_red02_a_redirect_is_visible_in_the_record(tmp_path):
    """Re-aimed after RED-01 was fixed.

    The original attack asserted that a *followed* redirect left no trace.
    Redirects are refused now, so the question becomes the same one in its
    surviving form: is the refusal itself in the record? "Nobody tried" and
    "somebody tried and was stopped" must not look the same.
    """
    with Sink() as thief:
        with Sink(reply=_redirect_to(thief.url)) as upstream:
            with env_proxy_over(upstream.url, tmp_path) as proxy:
                post_json(proxy.base_url, "/api/cmd/RESET", {"game_id": DEV})
        assert thief.seen == [], "precondition: the redirect was NOT followed"
    assert incidents(tmp_path, "redirect_refused")
    step = next(r for r in read_ledger(str(tmp_path / "l.jsonl"))
                if r["event"] == "env_step")
    blob = json.dumps(step)
    assert "302" in blob or "stolen" in blob or str(thief.port) in blob, (
        "the record says status %s, path %s, attempts %s -- nothing about the "
        "redirect" % (step["http"].get("status"), step["http"].get("path"),
                      step["http"].get("attempts")))


def test_red03_an_absolute_uri_request_line_cannot_retarget_the_forward(tmp_path):
    """`POST http://elsewhere/... HTTP/1.1` -- the proxy concatenates the path
    onto its configured upstream, so an absolute URI produces an unusable host
    rather than a second destination."""
    with Sink() as elsewhere, Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status = raw_request(proxy.cfg.host, proxy.port,
                                 "POST %s/api/cmd/RESET HTTP/1.1" % elsewhere.url,
                                 body=b'{"game_id":"ar25-0c556536"}')
        assert b"502" in status
        assert elsewhere.seen == []


def test_red04_a_protocol_relative_path_stays_on_the_configured_host(tmp_path):
    with Sink() as elsewhere, Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            raw_request(proxy.cfg.host, proxy.port,
                        "POST //127.0.0.1:%d/api/cmd/RESET HTTP/1.1" % elsewhere.port,
                        body=b'{"game_id":"ar25-0c556536"}')
        assert elsewhere.seen == []
        assert upstream.seen, "the request went to the operator's upstream"


def test_red05_dot_segments_cannot_leave_the_configured_host(tmp_path):
    with Sink() as elsewhere, Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            raw_request(proxy.cfg.host, proxy.port,
                        "POST /api/../../api/cmd/RESET HTTP/1.1",
                        body=b'{"game_id":"ar25-0c556536"}')
        assert elsewhere.seen == []
        assert upstream.seen


def test_red06_connect_is_refused(tmp_path):
    with Sink() as elsewhere, Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status = raw_request(proxy.cfg.host, proxy.port,
                                 "CONNECT 127.0.0.1:%d HTTP/1.1" % elsewhere.port)
        assert b"501" in status
        assert elsewhere.seen == []


def test_red07_arm_supplied_routing_headers_are_not_honoured(tmp_path):
    """Host / X-Forwarded-Host / X-Upstream are not in the passthrough set, so
    an arm cannot name its own destination."""
    with Sink() as elsewhere, Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            post_json(proxy.base_url, "/api/cmd/RESET", {"game_id": DEV},
                      headers={"X-Upstream": elsewhere.url,
                               "X-Forwarded-Host": "127.0.0.1:%d" % elsewhere.port})
        assert elsewhere.seen == []
        assert upstream.seen
        assert "x-upstream" not in upstream.seen[0]["headers"]


def test_red08_an_unknown_proxy_internal_path_is_never_forwarded(tmp_path):
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, _ = call(proxy.base_url + "/__proxy/../api/cmd/RESET",
                                data=b"{}", headers={"Content-Type": "application/json"})
            assert status == 404
            status, _, body = call(proxy.base_url + "/__proxy/state", method="GET")
            assert status == 200
        assert upstream.seen == []
    assert ARC_KEY not in body


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-09: `/__proxy/` is handled before `_check_arm_is_keyless` and before any
# ledger write, so an arm can talk to the proxy's internals carrying a
# credential header and neither the incident nor the request is recorded
def test_red09_a_credential_header_on_a_proxy_internal_is_still_an_incident(tmp_path):
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            call(proxy.base_url + "/__proxy/health", method="GET",
                 headers={"X-API-Key": "an-arm-supplied-key-value"})
    assert incidents(tmp_path, "bypass_attempt"), (
        "the arm proved it holds a credential and nothing was written")


# ===========================================================================
# Class B -- the arm process reaching the credential
# ===========================================================================

def _echo_key_in_body(handler):
    key = handler.headers.get("X-API-Key")
    return 200, {"state": "NOT_FINISHED", "frame": [[[0]]], "score": 0,
                 "levels_completed": 0, "echo": key}, \
        {"Content-Type": "application/json"}


def _echo_key_in_header(handler):
    key = handler.headers.get("X-API-Key") or ""
    return 200, {"state": "NOT_FINISHED", "frame": [[[0]]]}, \
        {"Content-Type": "application/json", "X-Echo-Key": key}


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-10: the upstream response body is handed to the arm unscrubbed --
# VAULT.scrub runs on the way to the ledger but not on the way to the client,
# so an upstream that reflects the key hands it to the arm
def test_red10_a_reflected_key_does_not_reach_the_arm_in_the_body(tmp_path):
    with Sink(reply=_echo_key_in_body) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            _, _, body = post_json(proxy.base_url, "/api/cmd/RESET",
                                   {"game_id": DEV})
    assert ARC_KEY not in body, "the arm now holds the ARC credential"


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-11: `_meta` returns the upstream's response headers to the arm filtered
# only for hop-by-hop names, so a reflected key in any other header reaches
# the arm -- and response headers are not recorded at all
def test_red11_a_reflected_key_does_not_reach_the_arm_in_a_header(tmp_path):
    with Sink(reply=_echo_key_in_header) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            _, headers, _ = post_json(proxy.base_url, "/api/scorecard/open",
                                      {"arm": "mock_arm"})
    assert ARC_KEY not in json.dumps(headers), "the arm now holds the ARC credential"


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-12: the model proxy writes `response.body` straight back to the arm, so
# the same reflection hands over the provider credential
def test_red12_a_reflected_key_does_not_reach_the_arm_from_the_model_proxy(tmp_path):
    def reply(handler):
        return 200, {"usage": {"input_tokens": 1},
                     "content": [{"type": "text", "text": handler.headers.get("x-api-key")}]}, \
            {"Content-Type": "application/json"}

    with Sink(reply=reply) as upstream:
        with model_proxy_over(upstream.url, tmp_path) as proxy:
            _, _, body = post_json(proxy.base_url, "/v1/messages",
                                   {"model": "m", "messages": []})
    assert MODEL_KEY not in body, "the arm now holds the provider credential"


def test_red13_a_reflected_key_is_still_scrubbed_out_of_the_ledger(tmp_path):
    """The mitigation that does hold: the vault scrubs the recorded copy."""
    with Sink(reply=_echo_key_in_body) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            post_json(proxy.base_url, "/api/cmd/RESET", {"game_id": DEV})
            post_json(proxy.base_url, "/api/scorecard/open", {"arm": "mock_arm"})
    blob = ledger_bytes(tmp_path)
    assert ARC_KEY not in blob
    assert "<redacted>" in blob


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-14: redact.MIN_SECRET_LEN silently declines to register a credential
# shorter than 12 characters, so such a key is never scrubbed and reaches the
# ledger verbatim when the upstream reflects it
def test_red14_a_short_credential_is_still_kept_out_of_the_ledger(tmp_path):
    with Sink(reply=_echo_key_in_body) as upstream:
        with env_proxy_over(upstream.url, tmp_path, api_key=SHORT_KEY) as proxy:
            post_json(proxy.base_url, "/api/scorecard/open", {"arm": "mock_arm"})
    assert SHORT_KEY not in ledger_bytes(tmp_path)


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-15: LEDGER_FORMAT.md 4 claims 'a ledger that has been through the writer
# cannot contain a key'. Only *registered* values are scrubbed, so any
# credential the vault has not seen is written out verbatim
def test_red15_an_unregistered_credential_never_reaches_the_ledger(tmp_path):
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            post_json(proxy.base_url, "/api/scorecard/open",
                      {"arm": "mock_arm", "note": "key=" + FOREIGN_KEY})
    assert FOREIGN_KEY not in ledger_bytes(tmp_path)


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-16: looks_like_credential only matches sk-* or a run of 32+
# alphanumerics, so a 36-character UUID-shaped key -- the shape the ARC
# credential's own mask implies -- raises no credential_in_body incident
def test_red16_a_uuid_shaped_key_in_a_body_raises_an_incident(tmp_path):
    assert looks_like_credential(FOREIGN_KEY), (
        "the detector now knows the UUID shape; that is the fix")
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            post_json(proxy.base_url, "/api/cmd/RESET",
                      {"game_id": DEV, "note": FOREIGN_KEY})
    assert incidents(tmp_path, "credential_in_body")


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-17: Vault.scrub rewrites dict *values* and checks dict *keys* only
# against the sensitive-header list, so a secret used as an object key
# survives onto disk
def test_red17_a_secret_used_as_an_object_key_is_scrubbed(tmp_path):
    secret = "synthetic-dictkey-secret-11112222"
    VAULT.register(secret)
    run = RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r-red", "probe")
    run.env_meta(request={secret: 1}, http={"method": "POST"})
    assert secret not in ledger_bytes(tmp_path)


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-18: scrubbing is exact substring replacement, so a secret split across
# two fields, or base64-encoded, passes through untouched
def test_red18_a_split_or_encoded_secret_is_scrubbed():
    vault = Vault()
    secret = "synthetic-split-secret-33334444"
    vault.register(secret)
    split = vault.scrub({"a": secret[:15], "b": secret[15:]})
    encoded = vault.scrub({"a": base64.b64encode(secret.encode()).decode()})
    assert split["a"] + split["b"] != secret
    # the encoded form is a registered spelling of the same secret, so it is
    # replaced outright rather than surviving as decodable base64
    assert secret not in json.dumps(encoded)
    assert base64.b64encode(secret.encode()).decode() not in json.dumps(encoded)


def test_red19_the_proxy_summary_that_reaches_run_json_carries_no_key(tmp_path):
    """`runner.run_game` copies both proxy summaries into `var/runs/<id>.json`.
    Whatever else leaks, that artefact must not."""
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as env, \
                model_proxy_over(upstream.url, tmp_path) as model:
            blob = json.dumps([env.summary(), model.summary()])
    assert ARC_KEY not in blob and MODEL_KEY not in blob
    assert '"key_injected": true' in blob


# ===========================================================================
# Class C -- guard evasion on the game id
# ===========================================================================

def reaches_upstream(tmp_path, path: str, *, body: bytes = b"{}",
                     content_type: str = "application/json",
                     headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """Send one request through the env proxy; return what the upstream saw."""
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            call(proxy.base_url + path, data=body,
                 headers={"Content-Type": content_type, **(headers or {})})
        return list(upstream.seen)


def mentions_sealed(seen: List[Dict[str, Any]]) -> bool:
    blob = json.dumps(seen).lower()
    return SEALED in blob or SEALED_STEM in blob


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-20: the id extractor requires a `-<8 hex>` suffix, so a bare 4-char stem
# is invisible to the guard. arc-recon INC-005 records that the upstream
# answers short ids with a fake 200, so this is a live request
def test_red20_a_bare_short_sealed_id_is_refused(tmp_path):
    guard = SealedPileGuard()
    assert guard.check_request("/api/cmd/RESET", "", {"game_id": SEALED_STEM})[
        "decision"] == "deny"
    assert not mentions_sealed(
        reaches_upstream(tmp_path, "/api/cmd/RESET",
                         body=json.dumps({"game_id": SEALED_STEM}).encode()))


@pytest.mark.parametrize("spelling", ["LS20-9607627B", "ls20-9607627B",
                                      "Ls20-9607627B"])
# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-21: `classify` lowercases the stem but the extractor's hex class is
# `[0-9a-f]`, so any uppercase in the *hex suffix* makes the whole id
# invisible. An uppercase stem alone is still caught
def test_red21_case_variants_of_a_sealed_id_are_refused(tmp_path, spelling):
    guard = SealedPileGuard()
    assert guard.check_request("/api/cmd/RESET", "", {"game_id": spelling})[
        "decision"] == "deny"


def test_red22_version_suffixes_and_an_uppercase_stem_are_caught(tmp_path):
    """The spelling families the extractor does handle: anything appended after
    the hex suffix, and case in the *stem* (which `classify` lowercases)."""
    guard = SealedPileGuard()
    for spelling in (SEALED + "-v2", SEALED + ".old", SEALED + "/frames",
                     "LS20-9607627b", "Ls20-9607627b"):
        assert guard.check_request("/api/cmd/RESET", "", {"game_id": spelling})[
            "decision"] == "deny", spelling


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-23: query strings are matched raw. A percent-encoded hyphen hides the id
# from the guard and decodes back to it at the upstream
def test_red23_a_percent_encoded_sealed_id_in_the_query_is_refused(tmp_path):
    seen = reaches_upstream(tmp_path, "/api/cmd/RESET?game_id=ls20%2D9607627b")
    assert not any("9607627b" in r["path"] for r in seen)


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-24: only `/game(s)/<id>` is modelled in the path, and the generic id
# regex is never applied to the path at all, so a sealed id anywhere else in
# the URL -- including behind %2F -- is forwarded verbatim path
# /api/scorecard/ls20-9607627b /api/games%2Fls20-9607627b
# /api/v1/ls20-9607627b/frames RED-25: the guard inspects `json.loads(raw)`;
# when that fails the body becomes None and the guard sees nothing -- but
# `_forward` still sends the raw bytes, so any non-JSON encoding carries a
# sealed id straight through body,content_type game_id=ls20-9607627b
# application/x-www-form-urlencoded game_id ls20-9607627b application/json
# game_id ls20-9607627b application/json game_id ls20-9607627b
# application/json /api/cmd/RESET RED-26: the guard matches literal ids only,
# so an id split across two fields or carried as base64 is invisible to it
# body a ls20-9607 b 627b blob blob ls20%2D9607627b /api/cmd/RESET decision
# deny RED-27: no unicode normalisation, so a zero-width space or a full-width
# hyphen inside the id defeats the match spelling ls20​-9607627b ls20－9607627b
# ls20­-9607627b /api/cmd/RESET game_id decision deny RED-28: `check_request`
# is never given the headers, and content-type is on the passthrough list, so
# a sealed id parked in a header parameter leaves the proxy unexamined
def test_red28_a_sealed_id_in_a_passthrough_header_is_refused(tmp_path):
    seen = reaches_upstream(tmp_path, "/api/cmd/RESET",
                            content_type="application/json; game=ls20-9607627b")
    assert not mentions_sealed(seen)


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-29: the guard is stateless -- it knows nothing about guids. A command
# that names only a session reaches whatever game that session belongs to, and
# the ledger records game_id '?'
def test_red29_a_session_scoped_command_cannot_reach_a_sealed_game(tmp_path):
    """The upstream here is a *session-scoped* API: it resolves the game from
    the guid, as a hosted environment reasonably may."""
    stepped: List[str] = []

    # `Recorder` consumes the body before `reply` runs, so the session lookup
    # reads it back off the sink's own record.
    with Sink() as upstream:
        def reply2(handler):
            body = upstream.seen[-1]["body"]
            game = SEALED if "guid-sealed" in body else "unknown"
            stepped.append(game)
            return 200, {"state": "NOT_FINISHED", "frame": [[[0]]]}, \
                {"Content-Type": "application/json"}
        upstream.httpd.reply = reply2                      # type: ignore[attr-defined]
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            post_json(proxy.base_url, "/api/cmd/ACTION1", {"guid": "guid-sealed"})
    assert SEALED not in stepped, "a sealed game was stepped without naming it"


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-30: load_piles compares the file against a digest the file itself
# carries. Recomputing that digest after moving a game out of the sealed pile
# passes the integrity check, and guard.py pins no expected value
def test_red30_a_recomputed_cut_digest_does_not_unseal_a_game(tmp_path):
    piles = load_piles()
    piles["sealed_pile"] = [g for g in piles["sealed_pile"] if g != SEALED]
    piles["dev_pile"] = sorted(piles["dev_pile"] + [SEALED])
    body = {k: v for k, v in piles.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True)
    piles["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    path = str(tmp_path / "piles.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(piles, fh)

    # Since the pinned digest landed, this raises rather than loading: a cut
    # whose contents are not THE cut is refused outright, which is a stronger
    # closed failure than loading it and then denying the game. Either outcome
    # counts; silently playing the game does not.
    try:
        guard = SealedPileGuard(piles_path=path)
    except PilesIntegrityError:
        return
    assert guard.verdict(SEALED)[0] is False, (
        "the cut was re-signed by the attacker and %s is now playable" % SEALED)


def test_red31_a_mangled_cut_fails_closed(tmp_path):
    """Two shapes of tampering that the digest check does catch."""
    piles = load_piles()
    stale = dict(piles, dev_pile=sorted(piles["dev_pile"] + [SEALED]))
    stale_path = str(tmp_path / "stale.json")
    with open(stale_path, "w", encoding="utf-8") as fh:
        json.dump(stale, fh)
    with pytest.raises(PilesIntegrityError):
        SealedPileGuard(piles_path=stale_path)

    # Pile lists renamed away entirely: every id becomes unknown, and unknown
    # is deny by default.
    moved = {k: v for k, v in piles.items() if k not in ("sealed_pile", "dev_pile")}
    moved["piles"] = {"sealed": piles["sealed_pile"], "dev": piles["dev_pile"]}
    body = {k: v for k, v in moved.items() if k != "sha256"}
    moved["sha256"] = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    moved_path = str(tmp_path / "moved.json")
    with open(moved_path, "w", encoding="utf-8") as fh:
        json.dump(moved, fh)
    # Since the pinned digest landed this raises instead: a cut that is not
    # THE cut is refused outright, which is a stronger closed failure than
    # loading it and finding every id unknown. Both are accepted here.
    try:
        guard = SealedPileGuard(piles_path=moved_path)
    except PilesIntegrityError:
        return
    assert guard.verdict(SEALED)[0] is False
    assert guard.verdict(DEV)[0] is False                  # fails closed both ways


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-32: the guard is wired into the environment proxy only. The model proxy
# forwards a prompt naming a sealed game to the provider, and piles.json rule
# 2 counts reading about a sealed game as contamination
def test_red32_the_model_proxy_refuses_a_prompt_naming_a_sealed_game(tmp_path):
    with Sink() as upstream:
        with model_proxy_over(upstream.url, tmp_path) as proxy:
            post_json(proxy.base_url, "/v1/messages",
                      {"model": "m", "messages": [
                          {"role": "user",
                           "content": "describe the mechanics of " + SEALED}]})
        assert not mentions_sealed(upstream.seen)


def test_red33_a_chunked_body_is_not_smuggled_upstream(tmp_path):
    """`_read_body` honours Content-Length only. A chunked body is therefore
    invisible to the guard -- but it is equally invisible to `_forward`, so the
    sealed id does not leave."""
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            raw_request(proxy.cfg.host, proxy.port,
                        "POST /api/cmd/RESET HTTP/1.1",
                        extra=b"Content-Type: application/json\r\n"
                              b"Transfer-Encoding: chunked\r\n",
                        body=b'1b\r\n{"game_id":"ls20-9607627b"}\r\n0\r\n\r\n')
        assert not mentions_sealed(upstream.seen)


def test_red34_a_sealed_id_in_the_ordinary_place_is_still_refused(tmp_path):
    """The control: the attacks above are evasions, not a broken guard."""
    with Sink() as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, body = post_json(proxy.base_url, "/api/cmd/RESET",
                                        {"game_id": SEALED})
        assert status == 403
        assert upstream.seen == []
    assert json.loads(body)["rule"] == "sealed_pile"
    assert incidents(tmp_path, "sealed_pile_request")


# ===========================================================================
# Class D -- forging the record
# ===========================================================================

def write_ledger(path: str, records: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for record in records:
            fh.write(json.dumps(dict(record, v="1.0"), sort_keys=True) + "\n")


def append_ledger(path: str, records: List[Dict[str, Any]]) -> None:
    with open(path, "a", encoding="utf-8", newline="") as fh:
        for record in records:
            fh.write(json.dumps(dict(record, v="1.0"), sort_keys=True) + "\n")


def step_record(idx: int, score, levels, *, run_id: str = "r-forge",
                arm: str = "mock_arm", seq: Optional[int] = None,
                **over) -> Dict[str, Any]:
    record = {
        "event": "env_step", "run_id": run_id, "arm": arm,
        "seq": idx + 1 if seq is None else seq, "ts": "2026-07-28T00:00:00.000Z",
        "game_id": DEV, "card_id": "card-1", "guid": "guid-1", "step_idx": idx,
        "action": {"name": "ACTION1", "id": 1, "data": None},
        "frames": [[[0]]], "n_frames": 1, "frame_hash": "sha256:0",
        "state": "NOT_FINISHED", "score": score, "levels_completed": levels,
        "level": levels, "level_boundary": False,
        "variant": None, "guard": {"decision": "allow"},
        "http": {"method": "POST", "path": "/api/cmd/ACTION1", "status": 200},
    }
    record.update(over)
    return record


def flat_card(levels: Any = 0, score: float = 0.0,
              total_actions: int = 2) -> Dict[str, Any]:
    """The `flat` scorecard shape (what the mock returns, what CardView reads
    without guessing), filled so the frozen scorer's battery has no unrelated
    complaint to make."""
    return {"card_id": "card-1", "score": score, "levels_completed": levels,
            "total_actions": total_actions}


def end_record(scorecard: Any, *, run_id: str = "r-forge",
               arm: str = "mock_arm", seq: int = 900) -> Dict[str, Any]:
    return {"event": "run_end", "run_id": run_id, "arm": arm, "seq": seq,
            "ts": "2026-07-28T00:00:01.000Z", "outcome": "WIN",
            "scorecard": scorecard}


def two_flat_steps(**over) -> List[Dict[str, Any]]:
    """Two ordinary steps that completed nothing -- the run every fixture below
    starts from, so that a FAIL is about the attack and nothing else."""
    return [step_record(0, 0, 0, **over), step_record(1, 0, 0, **over)]


def test_red35_a_second_run_end_cannot_whitewash_a_mismatch(tmp_path):
    """Blocked by obligation S-7 ('the run has exactly one run_end'), which
    landed in `proxy/scoring/arc_v1.py` while this suite was being written."""
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, two_flat_steps() + [end_record(flat_card(levels=1,
                                                                score=1.0))])
    assert reconcile_run("r-forge", path, write_incident=False)["verdict"] == "FAIL"

    append_ledger(path, [end_record(flat_card(), seq=901)])
    report = reconcile_run("r-forge", path, write_incident=False)
    assert report["verdict"] == "FAIL", "a later run_end replaced the first"
    assert any("S-7" in p for p in report["problems"])


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-36: `observed` keeps only isinstance(x, int) values, so steps whose
# levels_completed is a float are dropped from the derivation in silence and
# the run reconciles clean against a card claiming zero
def test_red36_non_integer_levels_do_not_vanish_from_the_derivation(tmp_path):
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, [step_record(0, 0, 0.0, level=0),
                        step_record(1, 0, 2.0, level=0),
                        end_record(flat_card(levels=0))])
    report = reconcile_run("r-forge", path, write_incident=False)
    assert report["verdict"] == "FAIL", (
        "a step recorded levels_completed 2.0 and the reconciler read the run "
        "as %r level(s) without saying so: %s"
        % (report["ledger_levels_completed"], report))


def test_red37_a_boolean_level_count_is_not_accepted_as_a_number(tmp_path):
    """`True` as a level count is caught -- by S-2 and S-6 disagreeing, not by
    a type check, but caught."""
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, [step_record(0, 0, 0),
                        step_record(1, 0, True, level=0, level_boundary=True),
                        end_record(flat_card(levels=1))])
    assert reconcile_run("r-forge", path, write_incident=False)["verdict"] == "FAIL"


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-38: reconcile partitions by run_id alone. One env_step appended under a
# second `arm` joins the derivation, so a run whose steps disagree with its
# card is made to agree by writing one more step as `probe`
def test_red38_records_from_another_arm_do_not_join_the_derivation(tmp_path):
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, [step_record(0, 0, 0),
                        end_record(flat_card(levels=1, score=1.0,
                                             total_actions=2))])
    assert reconcile_run("r-forge", path, write_incident=False)["verdict"] == "FAIL"

    append_ledger(path, [step_record(1, 1, 1, arm="probe", seq=902,
                                     level=0, level_boundary=True)])
    assert reconcile_run("r-forge", path, write_incident=False)["verdict"] == "FAIL"


def test_red46_a_scorecard_that_contradicts_itself_is_caught(tmp_path):
    """Blocked by obligation S-10: the card's declared totals are checked
    against its own environments."""
    from proxy.scoring.arc_v1 import CardView
    forged = {"card_id": "card-1", "score": 0.0,
              "total_levels": 3, "total_levels_completed": 1,
              "total_environments": 1, "total_actions": 2,
              "environments": [{"id": DEV, "levels_completed": 0,
                                "level_count": 3, "actions": 2,
                                "runs": [{"state": "NOT_FINISHED",
                                          "actions": 2}]}]}
    assert CardView(forged).aggregate_errors
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, two_flat_steps() + [end_record(forged)])
    report = reconcile_run("r-forge", path, write_incident=False)
    assert report["verdict"] == "FAIL"
    assert any("S-10" in p for p in report["problems"])


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-39: duplicate `seq` -- LEDGER_FORMAT.md 2's definition of a corrupt
# file, and the signature of an appended forgery -- is caught only by the
# standalone validator, which nothing on the audit path calls. read_ledger
# accepts it and the reconciliation obligation reports PASS
def test_red39_duplicate_seq_is_detected_on_the_audit_path(tmp_path):
    from proxy.tools.validate_ledger import validate_records
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, [step_record(0, 0, 0, seq=7), step_record(1, 0, 0, seq=7),
                        end_record(flat_card(), seq=7)])
    records = read_ledger(path)                    # accepted without complaint
    assert any(p["kind"] == "duplicate_seq" for p in validate_records(records)), (
        "positive control: the standalone validator does catch it")
    assert reconcile_run("r-forge", path, write_incident=False)["verdict"] == "FAIL", (
        "three records share seq=7 and the obligation still says the run is clean")


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-40: nothing authenticates a record. A ledger written by hand, by an arm,
# or by anything with write access to the file reconciles PASS -- the
# reconciler checks the file against itself, never against the world
def test_red40_a_wholly_fabricated_run_does_not_reconcile(tmp_path):
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, two_flat_steps(run_id="r-fake") + [
        end_record(flat_card(), run_id="r-fake"),
    ])
    report = reconcile_run("r-fake", path, write_incident=False)
    assert report["verdict"] != "PASS", (
        "a file no proxy ever wrote was certified clean: %s" % report)


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-41: the writer accepts a frame_hash that does not hash its own frames --
# canon checks n_frames against frames but never the hash -- so the forgery
# has to be found later by a validator nobody is obliged to run
def test_red41_the_writer_refuses_a_frame_hash_that_does_not_hash(tmp_path):
    path = str(tmp_path / "l.jsonl")
    led = Ledger(path)
    with pytest.raises(Exception) as exc:
        led.append("env_step", "r-forge", "probe",
                   game_id=DEV, step_idx=0,
                   action={"name": "RESET", "id": None, "data": None},
                   frames=[[[9, 9]]], n_frames=1,
                   frame_hash="sha256:" + "0" * 64,
                   level=0, level_boundary=False,
                   guard={"decision": "allow"}, http={"status": 200})
    assert "frame_hash" in str(exc.value)
    assert read_ledger(path) == [], "and nothing reached the file"


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-42: the cost ban is a check on top-level field names. A dollar figure
# nested inside the `usage` object -- which is copied through verbatim by
# contract -- reaches the ledger
def test_red42_a_cost_figure_cannot_be_nested_into_usage(tmp_path):
    path = str(tmp_path / "l.jsonl")
    run = RunLedger(Ledger(path), "r-forge", "probe")
    with pytest.raises(Exception) as exc:
        run.model_call("anthropic", "m", request=None, response=None,
                       usage={"input_tokens": 10, "cost_usd": 3.5}, http={})
    assert "cost_usd" in str(exc.value)
    assert "cost_usd" not in ledger_bytes(tmp_path)


def test_red43_top_level_cost_spellings_are_refused(tmp_path):
    """The half of the ban that holds, on every event shape."""
    run = RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r-forge", "probe")
    for field in ("cost", "cost_usd", "total_cost_usd", "price_usd"):
        with pytest.raises(ValueError):
            run.model_call("anthropic", "m", request=None, response=None,
                           usage={}, http={}, **{field: 1.0})
        with pytest.raises(ValueError):
            run.env_meta(http={}, **{field: 1.0})


# Landed when this suite was written; closed by P-9. Kept as a
# regression guard -- the finding it records is:
# RED-44: one appended line with an unknown `v` makes read_ledger raise for
# the whole file, so every run in it becomes unauditable -- and the file is
# append-only, so the poison line cannot be removed
def test_red44_one_unreadable_line_does_not_destroy_the_whole_ledger(tmp_path):
    """Re-aimed after RED-40 was fixed.

    The original built its ledger by hand, which no longer reconciles at all --
    that is RED-40's fix. So the run is written through the real writer, and
    the question stays exactly the same: does one poison line appended under
    *another* run_id destroy the auditability of this one?
    """
    path = str(tmp_path / "l.jsonl")
    _write_a_real_run(path)
    before = reconcile_run("r-red", path, write_incident=False)

    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps({"v": "2.0", "event": "env_step",
                             "run_id": "r-other"}) + "\n")
    after = reconcile_run("r-red", path, write_incident=False)

    assert after["verdict"] == before["verdict"], (
        "a line appended under another run_id changed this run's verdict from "
        "%s to %s" % (before["verdict"], after["verdict"]))
    assert after["ledger_health"]["unreadable_lines"] == 1, (
        "and the unreadable line is reported rather than swallowed")


def _write_a_real_run(path: str) -> None:
    """One small run written through the actual writer, so it is canonical."""
    from proxy.ledger import Ledger, RunLedger
    run = RunLedger(Ledger(path), "r-red", "probe", game_id=DEV)
    run.run_start(game_id=DEV)
    run.env_step(DEV, {"name": "RESET", "id": None, "data": None},
                 frames=[[[0]]], card_id="c1", levels_completed=0,
                 http={"status": 200})
    run.env_step(DEV, {"name": "ACTION1", "id": 1, "data": None},
                 frames=[[[1]]], card_id="c1", levels_completed=0,
                 response={"win_levels": 8}, http={"status": 200})
    run.run_end(outcome="done", scorecard={
        "card_id": "c1",
        "environments": [{"actions": 1, "completed": False, "id": DEV,
                          "level_count": 8, "levels_completed": 0, "resets": 0,
                          "runs": [{"actions": 1, "levels_completed": 0,
                                    "guid": "g", "state": "NOT_FINISHED"}],
                          "score": 0.0}],
        "opaque": {}, "score": 0.0, "tags": [], "tags_scores": [],
        "total_actions": 1, "total_environments": 1,
        "total_environments_completed": 0, "total_levels": 8,
        "total_levels_completed": 0})


def test_red45_a_run_without_a_readable_scorecard_fails(tmp_path):
    """The obligation that does hold: a missing or unreadable scorecard is a
    FAIL, not a shrug."""
    path = str(tmp_path / "l.jsonl")
    write_ledger(path, two_flat_steps())
    report = reconcile_run("r-forge", path, write_incident=False)
    assert report["verdict"] == "FAIL"
    assert scorecard_score(None) is None

    write_ledger(path, two_flat_steps()
                 + [end_record({"totally": "unknown"})])
    assert reconcile_run("r-forge", path, write_incident=False)["verdict"] == "FAIL"
