"""The desk's traffic, through the model proxy, into the ledger.

`DUAL_PROXY.md` §4 makes reaching verdict (a) -- "both proxies validated on
real traffic" -- turn on a provider credential this repository does not have.
That is still true of the last step and only of the last step. Everything
*before* it is testable offline, and until P-12 none of it had been tested at
all: the model proxy had never carried one request whose shape a real
`claude -p` produces, so "the only missing piece is a funded key" was a
prediction rather than a measurement.

It was also wrong. Putting a real CLI request through the proxy for the first
time found a second, independent blocker that the 401s had been hiding
(`test_a_date_shaped_token_in_the_system_prompt_is_not_a_game`), and a funded
key would not have moved it an inch.

Two layers here, deliberately:

* the **stub** tests replay the request the vendor CLI was measured making --
  `POST /v1/messages?beta=true`, `stream: true`, `x-api-key`, a system prompt --
  and always run. They are the regression surface;
* `test_the_real_cli_reaches_the_provider_through_the_model_proxy` runs the
  actual binary and skips when it is absent, on the same footing as the Fast
  Downward toolchain in `engine-rig`. It is what makes the stub honest: the
  stub's request shape came from that run and would drift silently otherwise.

Nothing here touches the network. The far end is `proxy.mock.model_mock`, on
loopback, and the near end is either an in-process HTTP client or a CLI whose
only configured endpoint is the proxy's own port. Zero spend, zero sealed-pile
contact.
"""

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request

import pytest

from proxy.cli_transport import TOKEN_PREFIX, DeskTransport, mint_client_token
from proxy.guard import SealedPileGuard
from proxy.ledger import Ledger, read_ledger
from proxy.mock.model_mock import DEFAULT_KEY as MODEL_KEY, MockProvider
from proxy.model_proxy import ModelProxy, ModelProxyConfig

#: A token of the shape the vendor CLI's own system prompt was measured to
#: contain: a short word, a hyphen, eight hex digits. It is not a game id and
#: is in neither pile -- which is exactly why the guard used to refuse it.
DATE_SHAPED_TOKEN = "code-20250219"

#: The headers the real CLI sent, names taken verbatim from the P-12 probe.
#: Values are ours; only the *set* matters to the proxy.
CLI_HEADER_NAMES = (
    "accept", "accept-encoding", "anthropic-beta",
    "anthropic-dangerous-direct-browser-access", "anthropic-version",
    "content-type", "user-agent", "x-app", "x-claude-code-session-id",
    "x-stainless-arch", "x-stainless-lang", "x-stainless-os",
    "x-stainless-package-version", "x-stainless-retry-count",
    "x-stainless-runtime", "x-stainless-runtime-version",
    "x-stainless-timeout",
)


def cli_shaped_body(system: str = DATE_SHAPED_TOKEN, stream: bool = True,
                    user: str = "reply with one word"):
    """The body shape the CLI was measured sending: the same top-level keys, a
    system prompt, `max_tokens`, and `stream`."""
    return {
        "model": "claude-haiku-4-5",
        "max_tokens": 256,
        "messages": [{"role": "user", "content": user}],
        "system": [{"type": "text", "text":
                    "You are Claude Code. Session %s." % system}],
        "metadata": {"user_id": "probe"},
        "stream": stream,
        "tools": [],
        "thinking": {"type": "disabled"},
        "context_management": {},
    }


def post(url, body, headers):
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST",
                                     headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def cli_headers(token=None, extra=None):
    headers = {name: "probe" for name in CLI_HEADER_NAMES}
    headers["content-type"] = "application/json"
    headers["accept"] = "application/json"
    headers["anthropic-version"] = "2023-06-01"
    if token:
        headers["x-api-key"] = token
    headers.update(extra or {})
    return headers


def model_proxy(tmp_path, *, token=None, upstream, run_id="r-cli",
                guard=None, require_client_token=False):
    cfg = ModelProxyConfig(run_id=run_id, arm="mock_arm", upstream=upstream,
                           api_key=MODEL_KEY, require_key=False,
                           client_token=token,
                           require_client_token=require_client_token,
                           guard=guard,
                           ledger=Ledger(str(tmp_path / "ledger.jsonl")))
    return ModelProxy(cfg)


def model_calls(tmp_path):
    return [r for r in read_ledger(str(tmp_path / "ledger.jsonl"))
            if r["event"] == "model_call"]


def incidents(tmp_path, kind=None):
    return [r for r in read_ledger(str(tmp_path / "ledger.jsonl"))
            if r["event"] == "incident" and (kind is None or r["kind"] == kind)]


# -- the finding this cell exists for --------------------------------------

def test_a_date_shaped_token_in_the_system_prompt_is_not_a_game(tmp_path):
    """The blocker the 401s were hiding, pinned in the direction that failed.

    Before P-12 the model proxy built its guard with `unknown_policy="deny"`,
    the environment proxy's setting. On a request that *addresses* a game that
    is right: one id, named on purpose, and an id outside the register is not
    something the cut authorised. On a **prompt** it is a false-positive
    machine. `_GAME_ID` matches two-to-six alphanumerics, a hyphen and eight
    hex digits, and the very first real `claude -p` request ever put through
    this proxy carried `code-20250219` inside the CLI's own system prompt. The
    proxy answered 403 `unknown_game`, the CLI reported `Failed to
    authenticate`, and no provider key on earth would have changed it.

    So this is the regression: an id-shaped token that is in neither pile goes
    through, and the call lands in the ledger.
    """
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url) as proxy:
            status, _ = post(proxy.base_url + "/v1/messages?beta=true",
                             cli_shaped_body(), cli_headers())
    assert status == 200, "an id-shaped token in a prompt is not a game id"
    assert len(model_calls(tmp_path)) == 1


def test_the_environment_proxys_setting_is_the_one_that_failed(tmp_path):
    """The same request, against a guard configured the old way, still 403s.

    Without this the test above passes for the wrong reason -- a guard that had
    stopped detecting anything would satisfy it just as well.
    """
    strict = SealedPileGuard(unknown_policy="deny")
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url,
                         guard=strict) as proxy:
            status, body = post(proxy.base_url + "/v1/messages?beta=true",
                                cli_shaped_body(), cli_headers())
    assert status == 403
    assert json.loads(body)["rule"] == "unknown_game"
    assert model_calls(tmp_path) == []


# -- the guard, demonstrated rather than asserted (DUAL_PROXY §4 step 3) ----

def test_a_planted_sealed_id_is_refused_by_the_proxys_own_guard(tmp_path):
    """`model_proxy`'s `check_request`, refusing a sealed game on the model
    path, at the proxy rather than at the arm.

    The id is not written here. It is read out of the cut at test time, which
    is the only way to plant one without putting a sealed identifier in a
    tracked file -- the thing the cut exists to prevent.
    """
    guard = SealedPileGuard(unknown_policy="allow")
    sealed_id = sorted(guard.sealed)[0]
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url) as proxy:
            status, body = post(
                proxy.base_url + "/v1/messages?beta=true",
                cli_shaped_body(user="what is the winning policy for %s"
                                     % sealed_id),
                cli_headers())
    assert status == 403
    assert json.loads(body)["rule"] == "sealed_pile"
    assert model_calls(tmp_path) == [], "a refused prompt must not reach upstream"

    blocks = [r for r in read_ledger(str(tmp_path / "ledger.jsonl"))
              if r["event"] == "guard_block"]
    assert blocks and blocks[0]["surface"] == "model_proxy"
    assert incidents(tmp_path, "sealed_pile_in_prompt")

    blob = open(str(tmp_path / "ledger.jsonl"), encoding="utf-8").read()
    assert sealed_id in blob, "the refusal has to name what it refused"


def test_a_development_pile_id_in_a_prompt_is_refused_too(tmp_path):
    """D-P12-002. `SealedPileGuard.verdict` allows a dev game -- it answers
    "may this be played", and dev games may. The 硬规 is a different question:
    no game id, of any pile, in model context. The arm enforces it; so does
    the proxy now, which is what makes it a property of the path."""
    guard = SealedPileGuard(unknown_policy="allow")
    dev_id = sorted(guard.dev)[0]
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url) as proxy:
            status, body = post(
                proxy.base_url + "/v1/messages?beta=true",
                cli_shaped_body(user="the frame for %s" % dev_id),
                cli_headers())
    assert status == 403
    assert json.loads(body)["rule"] == "game_id_in_prompt"
    assert model_calls(tmp_path) == []


# -- the client leg --------------------------------------------------------

def test_a_minted_token_gets_in_and_is_not_recorded_as_a_bypass(tmp_path):
    token = mint_client_token()
    assert token.startswith(TOKEN_PREFIX)
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url,
                         token=token) as proxy:
            status, _ = post(proxy.base_url + "/v1/messages?beta=true",
                             cli_shaped_body(), cli_headers(token=token))
    assert status == 200
    assert len(model_calls(tmp_path)) == 1
    assert incidents(tmp_path, "bypass_attempt") == [], (
        "the desk presenting the token this run minted for it is not an "
        "attempt to bypass anything; recording it as one buries the real "
        "signal under one incident per call")


def test_a_bearer_form_of_the_minted_token_is_accepted(tmp_path):
    """The CLI presents `Authorization: Bearer …` whenever its config
    directory holds stored credentials, so both shapes have to be read."""
    token = mint_client_token()
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url,
                         token=token) as proxy:
            status, _ = post(
                proxy.base_url + "/v1/messages?beta=true", cli_shaped_body(),
                cli_headers(extra={"authorization": "Bearer " + token}))
    assert status == 200
    assert incidents(tmp_path, "bypass_attempt") == []


def test_a_stranger_on_the_port_is_refused_before_the_key_is_spent(tmp_path):
    """The reason the client leg exists at all.

    An unauthenticated loopback port in front of an injected provider key is an
    open relay to that key for every process on the machine. It was tolerable
    only while no funded key existed -- which is precisely the condition this
    cell is trying to remove.
    """
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url,
                         token=mint_client_token()) as proxy:
            status, body = post(proxy.base_url + "/v1/messages?beta=true",
                                cli_shaped_body(),
                                cli_headers(token="not-the-token"))
    assert status == 401
    assert json.loads(body)["rule"] == "client_token_required"
    assert model_calls(tmp_path) == [], "refused before anything was forwarded"
    assert incidents(tmp_path, "bypass_attempt"), "and recorded, not merely refused"


def test_no_token_configured_is_the_old_behaviour_exactly(tmp_path):
    """Additive, per CONTRACT_CHANGES.md §2: a proxy built the way every
    existing caller builds one behaves as it did, including recording a
    client-supplied credential as a bypass attempt."""
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url) as proxy:
            status, _ = post(proxy.base_url + "/v1/messages?beta=true",
                             cli_shaped_body(),
                             cli_headers(extra={"authorization": "Bearer x"}))
    assert status == 200
    assert incidents(tmp_path, "bypass_attempt")


def test_a_proxy_cannot_advertise_authentication_it_cannot_perform(tmp_path,
                                                                   monkeypatch):
    monkeypatch.delenv("THEORIA_MODEL_PROXY_TOKEN", raising=False)
    with pytest.raises(ValueError):
        ModelProxyConfig(run_id="r", arm="mock_arm", upstream="http://127.0.0.1:1",
                         api_key=MODEL_KEY, require_key=False,
                         require_client_token=True,
                         ledger=Ledger(str(tmp_path / "l.jsonl")))


def test_the_minted_token_never_reaches_the_provider(tmp_path):
    """The sealing property, from the other side. `_forward` copies four
    whitelisted headers and injects the run's provider key; the client's own
    credential -- minted or not -- is not among them."""
    seen = {}
    token = mint_client_token()

    with MockProvider(api_key=MODEL_KEY) as provider:
        original = provider.httpd.RequestHandlerClass.do_POST

        def do_POST(self):                              # noqa: N802
            seen["headers"] = {k.lower(): v for k, v in self.headers.items()}
            return original(self)

        provider.httpd.RequestHandlerClass.do_POST = do_POST
        try:
            with model_proxy(tmp_path, upstream=provider.base_url,
                             token=token) as proxy:
                status, _ = post(proxy.base_url + "/v1/messages?beta=true",
                                 cli_shaped_body(), cli_headers(token=token))
        finally:
            provider.httpd.RequestHandlerClass.do_POST = original

    assert status == 200
    assert seen["headers"].get("x-api-key") == MODEL_KEY
    assert token not in json.dumps(seen["headers"])
    assert "authorization" not in seen["headers"]
    assert token not in open(str(tmp_path / "ledger.jsonl"), encoding="utf-8").read()


# -- what lands in the ledger (the gate item) -------------------------------

def test_the_usage_block_lands_verbatim_through_the_proxy_path(tmp_path):
    """`LEDGER_FORMAT.md` §4: the provider's `usage` block, not reshaped, not
    summed -- and for a stream, merged from the two halves the provider splits
    it across, with no key renamed and no total invented."""
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url) as proxy:
            status, _ = post(proxy.base_url + "/v1/messages?beta=true",
                             cli_shaped_body(stream=True), cli_headers())
    assert status == 200
    call, = model_calls(tmp_path)
    assert call["http"]["status"] == 200
    assert call["http"]["stream"] is True
    assert call["http"]["path"] == "/v1/messages"
    assert call["usage"]["input_tokens"] > 0        # from message_start
    assert call["usage"]["output_tokens"] > 0       # from message_delta
    assert set(call["usage"]) == {"input_tokens", "output_tokens",
                                  "cache_creation_input_tokens",
                                  "cache_read_input_tokens"}
    assert call["pricing_ref"]["table"] == "pricing_v1"
    assert "cost" not in call and "cost_usd" not in call
    assert call["response"]["assembled"]["text"]


def test_a_non_streamed_call_records_the_body_whole(tmp_path):
    with MockProvider(api_key=MODEL_KEY) as provider:
        with model_proxy(tmp_path, upstream=provider.base_url) as proxy:
            post(proxy.base_url + "/v1/messages?beta=true",
                 cli_shaped_body(stream=False), cli_headers())
    call, = model_calls(tmp_path)
    assert call["http"]["stream"] is False
    assert call["response"]["content"][0]["text"]
    assert call["request"]["system"], "the request body, whole"


# -- the transport helper ---------------------------------------------------

def test_the_transport_hands_the_desk_a_credential_free_config_dir():
    with DeskTransport("http://127.0.0.1:1") as transport:
        env = transport.apply({"ANTHROPIC_AUTH_TOKEN": "inherited-bearer",
                               "PATH": "x"})
        assert env["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:1"
        assert env["ANTHROPIC_API_KEY"] == transport.token
        assert os.path.isdir(env["CLAUDE_CONFIG_DIR"])
        assert os.listdir(env["CLAUDE_CONFIG_DIR"]) == []
        # The measured precedence: a bearer beats an x-api-key, so an
        # inherited one would put an unknown credential on the wire under a
        # configuration that looks correct.
        assert "ANTHROPIC_AUTH_TOKEN" not in env
        assert env["PATH"] == "x"
        directory = transport.config_dir
    assert not os.path.exists(directory)


def test_the_transports_description_carries_no_token_value():
    with DeskTransport("http://127.0.0.1:1") as transport:
        described = json.dumps(transport.describe())
    assert transport.token not in described
    assert "token_len" in described


def test_two_transports_do_not_share_a_token():
    with DeskTransport("http://127.0.0.1:1") as a, \
            DeskTransport("http://127.0.0.1:1") as b:
        assert a.token != b.token


# -- the real binary, when there is one -------------------------------------

def claude_bin():
    for name in ("claude.cmd", "claude.exe", "claude"):
        found = shutil.which(name)
        if found:
            return found
    return None


@pytest.mark.skipif(claude_bin() is None,
                    reason="the `claude` CLI is not on PATH; the stub tests "
                           "above carry the shape it was measured producing")
def test_the_real_cli_reaches_the_provider_through_the_model_proxy(tmp_path):
    """The whole path, with the actual vendor binary at the near end.

    This is the test that makes `DUAL_PROXY.md` §4's step 2 answerable. It
    proves five things at once, none of which had ever been demonstrated:

    * `claude -p` honours `ANTHROPIC_BASE_URL` and speaks `/v1/messages`;
    * pointed at a credential-free `CLAUDE_CONFIG_DIR` it presents the token we
      minted, not the operator's OAuth bearer;
    * the model proxy authenticates it, strips it, and injects its own key;
    * the far end answers in the provider's shape and the CLI parses it;
    * a `model_call` at status 200 with the provider's `usage` verbatim lands
      in the ledger.

    What it does not prove, and what nothing offline can: that a *funded*
    provider key at the far end returns 200. That is the one remaining step,
    and it is an owner action -- `DUAL_PROXY.md` §4 step 1.
    """
    with MockProvider(api_key=MODEL_KEY) as provider:
        token = mint_client_token()
        with model_proxy(tmp_path, upstream=provider.base_url, token=token,
                         require_client_token=True) as proxy:
            with DeskTransport(proxy.base_url, token=token,
                               parent_dir=str(tmp_path)) as transport:
                env = transport.apply(dict(os.environ))
                cwd = tempfile.mkdtemp(dir=str(tmp_path))
                proc = subprocess.run(
                    [claude_bin(), "-p", "--model", "claude-haiku-4-5",
                     "--output-format", "json", "--max-turns", "2"],
                    cwd=cwd, env=env,
                    input=json.dumps({"frame": [[[0]]]}) + "\nreply with the action",
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=300)
            summary = proxy.summary()

    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    envelope = json.loads(proc.stdout)
    assert envelope.get("api_error_status") is None, envelope.get("result")
    assert envelope["is_error"] is False
    assert envelope["result"], "the CLI parsed a reply out of the loopback provider"

    assert summary["calls"] >= 1 and summary["errors"] == 0
    assert summary["client_authenticated"] is True
    assert summary["key_injected"] is True

    calls = model_calls(tmp_path)
    assert calls, "the desk's call has to be in the ledger, not only in stdout"
    call = calls[0]
    assert call["http"]["status"] == 200
    assert call["http"]["path"] == "/v1/messages"
    assert call["usage"]["input_tokens"] > 0
    assert call["usage"]["output_tokens"] > 0
    assert call["pricing_ref"]["table"] == "pricing_v1"

    # The CLI's own accounting and the proxy's agree that tokens moved. They
    # are two independent measurements of the same call; the point of routing
    # through the proxy is that the second one exists at all.
    assert envelope["usage"]["input_tokens"] == call["usage"]["input_tokens"]
    assert envelope["usage"]["output_tokens"] == call["usage"]["output_tokens"]

    # The sealing property, end to end: neither credential is in the file.
    blob = open(str(tmp_path / "ledger.jsonl"), encoding="utf-8").read()
    assert MODEL_KEY not in blob and transport.token not in blob
