"""The model half of the seal's right conjunct, as negative samples.

`test_seal.py` is the environment half: an arm holding no credential cannot
reach the ARC upstream, and the proxy's injected key is the entire difference.
This file is its model-side sibling, and it exists because that half was ruled
to read differently.

**The reading being pinned.** On 2026-08-01 the owner answered the funding
question -- model calls go on the Claude subscription, no vendor API key is to
be configured (`monitor/spec.py` p1-proxy-model, the closing owner-ruling
paragraph; the transport itself is `theoria-arm` D-P8-002, a `claude -p` CLI
envelope). So on the model side "the arm cannot leave the recorded path" no
longer means "the proxy injects a vendor key the arm does not hold". It means:

    CLI envelope + no vendor credential anywhere in the repo or arm environment

and the two halves of this file are that sentence's executable form
(`proxy/DECISIONS.md` D-A20-001).

**The live history this is built on.** `verify-lab/DUAL_PROXY.md` S32 recomputed
the denominators rather than quoting a bare count, because 65 of 65 and 65 of
65,000 are different claims: of **65** `model_call` records ever put through the
model proxy at a real vendor, **65 returned HTTP 401 and 0 returned 2xx**. That
is not an engineering defect. `_forward` rebuilds the outbound headers from
`PASSTHROUGH_REQUEST_HEADERS`, which contains no credential header, and injects
`x-api-key` only from `cfg.api_key` -- and `.env` holds `ARC_API_KEY` and no
vendor name, so there was nothing to inject. Every one of those 65 requests was
genuinely forwarded and genuinely refused by the real upstream.

The tests below reproduce that offline, at zero cost and with no network: the
"vendor" is a `http.server` on 127.0.0.1. Nothing here reads or prints a
credential value; the `.env` half works on variable **names** only.

**Why both halves are needed, and why neither alone is enough.** The name check
alone would pass on a repository whose proxy laundered a credential handed to it
by a client. The 401 check alone would pass on a repository that had quietly
grown a vendor key, because a configured proxy answers 200. Together they say:
there is no vendor credential here, and if one arrived by another route the
transport would not carry it.
"""

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

import pytest

from proxy import model_proxy as model_proxy_mod
from proxy.ledger import Ledger, read_ledger
from proxy.mock.arm_mock import FORBIDDEN_ENV
from proxy.mock.model_mock import DEFAULT_KEY as VENDOR_KEY, MockProvider
from proxy.model_proxy import ModelProxy, ModelProxyConfig
from proxy.paths import DOTENV

# ---------------------------------------------------------------- the vocabulary

#: The only credential variable this repository is allowed to declare. The
#: environment proxy reads it here and injects it (`env_proxy.py`); it is the
#: one key the design says lives in `.env` at all.
ALLOWED_DOTENV_NAMES = frozenset({"ARC_API_KEY"})

#: Vendor credential variable **names**. A silently added one is the failure
#: this file is aimed at: it would not break a test, it would not fail a build,
#: and it would quietly convert the subscription transport back into an API
#: transport -- undoing the owner's ruling by configuration drift rather than by
#: decision. `CLAUDE_CODE_OAUTH_TOKEN` is here because `cli_transport.apply`
#: pops it for exactly this reason: it is a bearer, and a bearer outranks an
#: `x-api-key` in the CLI's own precedence order.
VENDOR_CREDENTIAL_NAMES = frozenset({
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
    "OPENAI_API_KEY",
})

#: What a rogue client would present at the model proxy. Deliberately
#: unmistakable and deliberately not shaped like any real credential: the tests
#: grep whole recorded requests for it.
CLIENT_SUPPLIED = "a-client-supplied-credential-value-0123456789"


# ------------------------------------------------------- 1. credential hygiene

def dotenv_names(path: str) -> "set[str]":
    """The variable **names** declared in a dotenv file. Never the values.

    Deliberately a separate reader from `redact.load_dotenv`, and stricter than
    it in one way that matters: `load_dotenv` drops a name whose value is empty,
    because it is building an injection map and an empty value injects nothing.
    This is building a *hygiene* report, where `ANTHROPIC_API_KEY=` is exactly
    the interesting line -- a variable declared and waiting to be filled in is a
    decision already half-taken, and it should be visible while it is still
    cheap to reverse.

    The value side is never returned, never logged and never compared, so no
    caller of this function -- including a failing assertion's output -- can put
    a credential on a terminal or into a CI log.
    """
    names: "set[str]" = set()
    if not os.path.exists(path):
        return names
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name = line.split("=", 1)[0].strip()
            # `export FOO=bar` is legal in a file meant to be `source`d, and the
            # repository's own loading recipe in CLAUDE.md is `set -a; . ./.env`.
            if name.startswith("export "):
                name = name[len("export "):].strip()
            if name:
                names.add(name)
    return names


def offending_names(names) -> "list[str]":
    """The declared names that are not on the allowlist, sorted."""
    return sorted(set(names) - ALLOWED_DOTENV_NAMES)


def write_dotenv(tmp_path, text: str) -> str:
    path = tmp_path / "dotenv-fixture"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_the_reader_returns_names_and_never_values(tmp_path):
    """The reader is itself a credential-handling surface, so it is tested as one.

    A hygiene check that reads a file full of secrets and then puts a set into an
    assertion message is one failing test away from printing a key into a CI log
    that is kept forever. So: the value never leaves the function, and that is
    pinned rather than assumed.
    """
    secret = "value-that-must-never-come-back-out-0123456789"
    path = write_dotenv(tmp_path, "ARC_API_KEY=%s\n" % secret)

    names = dotenv_names(path)

    assert names == {"ARC_API_KEY"}
    assert secret not in repr(names)
    assert secret not in "".join(names)


def test_a_dotenv_holding_only_the_arc_key_is_clean(tmp_path):
    """The positive control. A check that refuses everything proves nothing."""
    path = write_dotenv(tmp_path,
                        "# the ARC key, injected inside the environment proxy\n"
                        "\n"
                        "ARC_API_KEY=synthetic-not-a-real-key-000000000000\n")
    assert offending_names(dotenv_names(path)) == []


@pytest.mark.parametrize("name", sorted(VENDOR_CREDENTIAL_NAMES))
def test_a_vendor_credential_variable_turns_the_check_red(tmp_path, name):
    """The negative sample: the check must go red on a silently added vendor key.

    This is the whole point of the file's first half. The owner's ruling is a
    statement about configuration, and configuration drifts without anybody
    deciding anything -- somebody debugging a model call adds one line to `.env`
    and the repository is on an API transport again, with the paper's sealing
    claim quietly false and every test still green.
    """
    path = write_dotenv(
        tmp_path,
        "ARC_API_KEY=synthetic-not-a-real-key-000000000000\n"
        "%s=synthetic-vendor-value-000000000000\n" % name)

    assert offending_names(dotenv_names(path)) == [name]


def test_a_vendor_variable_declared_with_an_empty_value_is_still_caught(tmp_path):
    """Stricter than `redact.load_dotenv`, on purpose -- see `dotenv_names`.

    The injection map is right to ignore this line; the hygiene report is right
    to show it. Both readings are correct for their own job, which is why there
    are two readers rather than one shared one.
    """
    from proxy.redact import load_dotenv                       # noqa: PLC0415

    path = write_dotenv(tmp_path,
                        "ARC_API_KEY=synthetic-not-a-real-key-000000000000\n"
                        "ANTHROPIC_API_KEY=\n")

    assert offending_names(dotenv_names(path)) == ["ANTHROPIC_API_KEY"]
    # ...and the divergence is real, not imagined: the injection reader does not
    # see it at all. If that ever stops being true this test should be revisited
    # rather than deleted -- it is documenting a difference, not policing one.
    assert "ANTHROPIC_API_KEY" not in load_dotenv(path)


def test_a_commented_out_vendor_key_is_not_a_declaration(tmp_path):
    """A false red is worse than no check: it trains people to ignore the check.

    A commented line, a blank line and a line with no `=` are all *not*
    declarations, and none of them may raise the alarm.
    """
    path = write_dotenv(
        tmp_path,
        "# ANTHROPIC_API_KEY=we-decided-against-this-on-2026-08-01\n"
        "\n"
        "   \n"
        "this line has no equals sign\n"
        "ARC_API_KEY=synthetic-not-a-real-key-000000000000\n")

    assert dotenv_names(path) == {"ARC_API_KEY"}
    assert offending_names(dotenv_names(path)) == []


def test_an_exported_vendor_key_is_still_a_declaration(tmp_path):
    """`export FOO=...` is the same declaration wearing a hat.

    CLAUDE.md's own recipe for loading this file is `set -a; . ./.env`, i.e. it
    is sourced by a shell, where `export` is ordinary. A checker that missed the
    `export` spelling would be a checker with a documented way around it.
    """
    path = write_dotenv(tmp_path, "export ANTHROPIC_API_KEY=synthetic-000000\n")
    assert offending_names(dotenv_names(path)) == ["ANTHROPIC_API_KEY"]


def test_this_repositorys_dotenv_declares_no_vendor_credential():
    """The live assertion, on the real file, by name only.

    `.env` is gitignored, so this is deliberately not vacuous-by-accident: when
    the file is absent the declared set is empty, which is a *stricter* state
    than the one being asserted -- a proxy started against no dotenv has nothing
    to inject, which is the 65-of-65 condition itself. Both states pass, and
    they pass for the same reason. A worktree checkout is the absent case; the
    main checkout is the present one.
    """
    names = dotenv_names(DOTENV)

    assert offending_names(names) == [], (
        "the repository's dotenv declares variable name(s) outside the "
        "allowlist. Names only are reported here, never values.")
    assert not (names & VENDOR_CREDENTIAL_NAMES)


def test_the_dotenv_allowlist_and_the_arm_side_forbidden_list_agree():
    """The two halves of the seal are asymmetric, and the asymmetry is the point.

    `arm_mock.FORBIDDEN_ENV` is what an **arm process** may not see, and
    `ARC_API_KEY` is on it: the arm must not hold the key the environment proxy
    injects on its behalf. `ALLOWED_DOTENV_NAMES` is what the **repository** may
    declare, and `ARC_API_KEY` is on that too, because the proxy has to read it
    from somewhere.

    Every *vendor* name is on both lists -- forbidden to the arm and undeclarable
    by the repository -- and that is the model side's stricter rule written out.
    Pinned here so that widening either list has to confront the other one
    instead of silently drifting from it.
    """
    assert set(FORBIDDEN_ENV) - {"ARC_API_KEY"} <= VENDOR_CREDENTIAL_NAMES
    assert "ARC_API_KEY" in FORBIDDEN_ENV
    assert "ARC_API_KEY" in ALLOWED_DOTENV_NAMES
    assert not (VENDOR_CREDENTIAL_NAMES & ALLOWED_DOTENV_NAMES)


# ------------------------------------------------ 2. the model-side bypass

class _Recorder(BaseHTTPRequestHandler):
    """Answers everything 200 and remembers exactly what it was handed."""

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):                         # keep output clean
        return

    def do_POST(self):                                         # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        self.server.record(self.path, self.headers, raw)       # type: ignore[attr-defined]
        payload = json.dumps({
            "id": "msg_recorder", "type": "message", "role": "assistant",
            "model": "mock-model-1",
            "content": [{"type": "text", "text": "{}"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class RecordingVendor:
    """A vendor that never refuses, so "it did not arrive" means one thing only.

    `MockProvider` answers 401 to an unauthenticated request, which is exactly
    right for asserting the 401 -- and exactly wrong for asserting that the
    client's own credential did not travel, because a refusal makes "the
    credential is absent from the request" ambiguous with "the request never
    completed". This one serves anything, so a value missing from `hits` was
    removed on the proxy's side of the wire and nowhere else.
    """

    def __init__(self) -> None:
        self.hits: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "RecordingVendor":
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        server.daemon_threads = True
        server.record = self._record                           # type: ignore[attr-defined]
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever,
                                        kwargs={"poll_interval": 0.05},
                                        daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        assert self._server is not None
        host, port = self._server.server_address[:2]
        return "http://%s:%d" % (host, port)

    def _record(self, path: str, headers, raw: bytes) -> None:
        with self._lock:
            self.hits.append({
                "path": path,
                "headers": {k.lower(): v for k, v in headers.items()},
                "body": raw.decode("utf-8", "replace"),
            })

    def blob(self) -> str:
        """Everything that crossed the wire, as one string to search."""
        with self._lock:
            return json.dumps(self.hits)


def keyless_proxy(upstream: str, tmp_path, *, run_id: str = "r-model-seal",
                  api_key: str = "") -> ModelProxy:
    """A model proxy holding **no** vendor credential -- the repository's state.

    `api_key=""` rather than `api_key=None` is load-bearing. `None` means "go and
    look in `.env`, then in the process environment", so on an operator's machine
    that happens to export a vendor key, `None` would silently produce a
    *configured* proxy: the 401 tests would fail confusingly, and -- much worse --
    a real credential would be put on a loopback wire by a test suite that
    advertises itself as holding none. The empty string says "this proxy has no
    key" and cannot be talked out of it.
    """
    cfg = ModelProxyConfig(run_id=run_id, arm="mock_arm", upstream=upstream,
                           api_key=api_key, require_key=False,
                           client_token=None,
                           ledger=Ledger(str(tmp_path / "l.jsonl")))
    return ModelProxy(cfg)


def post(base: str, path: str, body: Dict[str, Any],
         headers: Optional[Dict[str, str]] = None) -> Tuple[int, Any]:
    request = urllib.request.Request(
        base.rstrip("/") + path, data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


def a_request() -> Dict[str, Any]:
    return {"model": "mock-model-1", "max_tokens": 256,
            "messages": [{"role": "user", "content": "[[0,0],[0,0]]"}]}


def records(tmp_path, event: str) -> List[Dict[str, Any]]:
    return [r for r in read_ledger(str(tmp_path / "l.jsonl"))
            if r["event"] == event]


def test_an_unauthenticated_model_call_is_refused_401_by_the_vendor(tmp_path):
    """65-of-65, reproduced offline.

    The repository holds no vendor credential, so the proxy injects none, so the
    vendor refuses. This is the model-side seal in its normal, ruled state -- not
    a defect being tolerated. `verify-lab/DUAL_PROXY.md` S32 measured the same
    thing against the real upstream: 65 `model_call` records, 65 at HTTP 401,
    0 at 2xx.

    The record matters as much as the refusal. A refused call that leaves no
    trace is indistinguishable from a call nobody made, and the count of 401s is
    only auditable because each one is on the ledger.
    """
    with MockProvider(api_key=VENDOR_KEY) as vendor:
        with keyless_proxy(vendor.base_url, tmp_path) as proxy:
            status, body = post(proxy.base_url, "/v1/messages", a_request())

    assert status == 401, body
    assert body["error"]["type"] == "authentication_error"

    calls = records(tmp_path, "model_call")
    assert len(calls) == 1
    assert calls[0]["http"]["status"] == 401


def test_the_positive_control_the_same_call_with_an_injected_key_succeeds(tmp_path):
    """...and the difference is entirely the injected credential.

    Without this the test above proves only that something is broken. Same
    proxy, same vendor, same request; the one changed input is whether the proxy
    holds a key. That isolates the 401 to the absent vendor credential, which is
    precisely the claim S32 makes and the claim the owner's ruling rests on.
    """
    with MockProvider(api_key=VENDOR_KEY) as vendor:
        with keyless_proxy(vendor.base_url, tmp_path,
                           api_key=VENDOR_KEY) as proxy:
            status, body = post(proxy.base_url, "/v1/messages", a_request())

    assert status == 200, body
    assert body["usage"]["input_tokens"] >= 1


@pytest.mark.parametrize("header", ["Authorization", "X-API-Key", "api-key"])
def test_a_credential_the_client_supplies_never_reaches_the_vendor(tmp_path, header):
    """The stripping property, asserted on what the vendor received.

    `_handle` records a `bypass_attempt` for a client-supplied credential header
    and then falls through -- nothing is stopped. What actually keeps the value
    off the wire is `_forward` rebuilding the outbound headers from
    `PASSTHROUGH_REQUEST_HEADERS`, which contains no credential header. Recording
    is the observation point and the allowlist is the enforcement point, and they
    can drift apart in silence.

    So the assertion is over the whole recorded request -- headers and body alike
    -- rather than over the ledger. An assertion that a `bypass_attempt` was
    written would stay green on the day somebody adds `authorization` to that
    tuple; this one would not, which
    `test_the_stripping_assertion_has_teeth` demonstrates by doing exactly that.
    """
    with RecordingVendor() as vendor:
        with keyless_proxy(vendor.base_url, tmp_path) as proxy:
            run_id = proxy.cfg.run_id
            status, _ = post(proxy.base_url, "/v1/messages", a_request(),
                             headers={header: CLIENT_SUPPLIED})

    # Forwarded, not blocked: the incident is an observation, not an
    # intervention, and pretending otherwise would misdescribe the mechanism.
    assert status == 200
    assert len(vendor.hits) == 1
    hit = vendor.hits[0]

    # The outcome: nowhere in what the vendor received.
    assert CLIENT_SUPPLIED not in vendor.blob()
    assert hit["headers"].get("authorization") is None
    assert hit["headers"].get("x-api-key") is None
    assert hit["headers"].get("api-key") is None

    # Recording, which is a separate mechanism and asserted separately.
    incidents = [r for r in records(tmp_path, "incident")
                 if r["run_id"] == run_id and r["kind"] == "bypass_attempt"]
    assert len(incidents) == 1
    assert incidents[0]["header"] == header.lower()

    # The ledger records that a value existed, never the value.
    assert CLIENT_SUPPLIED not in open(str(tmp_path / "l.jsonl"),
                                       encoding="utf-8").read()


def test_the_stripping_assertion_has_teeth(tmp_path, monkeypatch):
    """The negative control on the test above -- verified, not assumed.

    Widen `PASSTHROUGH_REQUEST_HEADERS` by one entry and the client's credential
    reaches the vendor. This test asserts that it *does*, which is what proves
    the previous test is measuring the allowlist rather than passing for some
    incidental reason (a request that never left, a header urllib dropped, a
    value the vault happened to scrub).

    It is also the exact regression: this is what the repository would look like
    the day somebody "fixes" a client's authentication by letting its header
    through.
    """
    monkeypatch.setattr(model_proxy_mod, "PASSTHROUGH_REQUEST_HEADERS",
                        model_proxy_mod.PASSTHROUGH_REQUEST_HEADERS
                        + ("authorization",))

    with RecordingVendor() as vendor:
        with keyless_proxy(vendor.base_url, tmp_path) as proxy:
            post(proxy.base_url, "/v1/messages", a_request(),
                 headers={"Authorization": CLIENT_SUPPLIED})

    assert len(vendor.hits) == 1
    assert CLIENT_SUPPLIED in vendor.blob()
    assert vendor.hits[0]["headers"].get("authorization") == CLIENT_SUPPLIED


def test_even_a_valid_vendor_credential_is_not_laundered_by_the_proxy(tmp_path):
    """The sharpest form: the proxy will not carry a key for a client that has one.

    The client presents the vendor's *real* key -- the one that would have
    worked -- and the call still fails 401, because the proxy strips it and has
    none of its own to inject. This is the half of the ruled reading that the
    dotenv check cannot reach: "no vendor credential in the repo or arm
    environment" would be worth little if a client that acquired one by any
    other route could push it through the recorded path.

    A `bypass_attempt` is raised for it, so the attempt is auditable rather than
    merely unsuccessful, and the key's value never reaches the ledger.
    """
    with MockProvider(api_key=VENDOR_KEY) as vendor:
        with keyless_proxy(vendor.base_url, tmp_path) as proxy:
            run_id = proxy.cfg.run_id
            status, body = post(proxy.base_url, "/v1/messages", a_request(),
                                headers={"X-API-Key": VENDOR_KEY})

    assert status == 401, body

    kinds = [r["kind"] for r in records(tmp_path, "incident")
             if r["run_id"] == run_id]
    assert "bypass_attempt" in kinds
    assert VENDOR_KEY not in open(str(tmp_path / "l.jsonl"),
                                  encoding="utf-8").read()


def test_the_proxy_reports_that_it_injected_no_key(tmp_path):
    """The state a run report publishes, on the keyless path.

    `summary()` is what reaches `run.json`, so `key_injected: false` is how a
    reader months later can tell a subscription-transport run from an API one
    without re-deriving it from 401 counts. Names and booleans only -- the
    summary has never carried a value (RED-19).
    """
    with RecordingVendor() as vendor:
        with keyless_proxy(vendor.base_url, tmp_path) as proxy:
            keyless = proxy.summary()
        with keyless_proxy(vendor.base_url, tmp_path,
                           api_key=VENDOR_KEY) as proxy:
            keyed = proxy.summary()

    assert keyless["key_injected"] is False
    # The control: the field tracks the key rather than being false always.
    assert keyed["key_injected"] is True
    # Presence, never the value -- on either path.
    assert VENDOR_KEY not in json.dumps(keyed)
