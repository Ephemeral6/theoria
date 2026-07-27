"""The sealing tests.

Phase 1's third closure property is *no bypass*: an arm cannot reach the
environment except through the proxy. That is a claim about construction, so
these tests try to construct the bypass and show it fails.
"""

import json
import urllib.error
import urllib.request

import pytest

from proxy.env_proxy import EnvProxy, EnvProxyConfig
from proxy.guard import SealedPileGuard
from proxy.ledger import Ledger, read_ledger
from proxy.mock.arc_mock import DEFAULT_GAME, DEFAULT_KEY, MockArc
from proxy.mock.arm_mock import FORBIDDEN_ENV, NotSealedError, assert_sealed

SEALED_GAME = "dc22-fdcac232"


def post(base, path, body, headers=None):
    request = urllib.request.Request(
        base.rstrip("/") + path, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


def proxy_over(arc, tmp_path, run_id="r-seal", **kwargs):
    cfg = EnvProxyConfig(run_id=run_id, arm="mock_arm", upstream=arc.base_url,
                         api_key=DEFAULT_KEY, require_key=False,
                         ledger=Ledger(str(tmp_path / "l.jsonl")), **kwargs)
    return EnvProxy(cfg)


# -- the arm holds nothing -------------------------------------------------

def test_a_clean_arm_environment_passes_the_seal_check():
    assert_sealed({"ARC_BASE_URL": "http://127.0.0.1:1", "PATH": "/usr/bin"})


@pytest.mark.parametrize("name", FORBIDDEN_ENV)
def test_an_arm_that_can_see_a_credential_refuses_to_start(name):
    with pytest.raises(NotSealedError, match=name):
        assert_sealed({name: "sk-ant-something-long-enough-to-be-a-key"})


# -- going around the proxy fails ------------------------------------------

def test_the_upstream_refuses_a_request_that_carries_no_key():
    """The constructive half: an arm holding no credential cannot play, because
    the environment answers 401 to anyone who cannot present one."""
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc:
        status, body = post(arc.base_url, "/api/cmd/RESET", {"game_id": DEFAULT_GAME})
        assert status == 401
        assert "X-API-Key" in body["error"]

        status, _ = post(arc.base_url, "/api/cmd/RESET", {"game_id": DEFAULT_GAME},
                         headers={"X-API-Key": "a-guess"})
        assert status == 401


def test_the_same_request_through_the_proxy_succeeds(tmp_path):
    """...and the difference is entirely the proxy's injected key. The arm's
    request is byte-identical to the one that just failed."""
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc, \
            proxy_over(arc, tmp_path) as proxy:
        status, body = post(proxy.base_url, "/api/cmd/RESET",
                            {"game_id": DEFAULT_GAME})
        assert status == 200 and body["state"] == "NOT_FINISHED"


def test_a_credential_the_arm_sends_is_stripped_and_recorded(tmp_path):
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc, \
            proxy_over(arc, tmp_path) as proxy:
        status, _ = post(proxy.base_url, "/api/cmd/RESET", {"game_id": DEFAULT_GAME},
                         headers={"X-API-Key": "an-arm-supplied-key-value"})
        # The upstream got the proxy's key, not the arm's, so the call worked.
        assert status == 200

    incidents = [r for r in read_ledger(str(tmp_path / "l.jsonl"))
                 if r["event"] == "incident"]
    assert any(r["kind"] == "bypass_attempt" for r in incidents)
    assert "an-arm-supplied-key-value" not in open(
        str(tmp_path / "l.jsonl"), encoding="utf-8").read()


def test_the_ledger_never_contains_the_key(tmp_path):
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc, \
            proxy_over(arc, tmp_path) as proxy:
        post(proxy.base_url, "/api/scorecard/open", {"arm": "mock_arm"})
        post(proxy.base_url, "/api/cmd/RESET", {"game_id": DEFAULT_GAME})

    blob = open(str(tmp_path / "l.jsonl"), encoding="utf-8").read()
    assert DEFAULT_KEY not in blob


# -- the sealed pile guard, at the proxy -----------------------------------

def test_a_sealed_game_is_refused_before_the_socket_opens(tmp_path):
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME, SEALED_GAME]) as arc, \
            proxy_over(arc, tmp_path) as proxy:
        status, body = post(proxy.base_url, "/api/cmd/RESET",
                            {"game_id": SEALED_GAME})
        assert status == 403
        assert body["rule"] == "sealed_pile"

    # The mock upstream would happily have served it: the refusal is the
    # proxy's, which is the point -- an arm cannot reach past it.
    with MockArc(api_key=DEFAULT_KEY, games=[SEALED_GAME]) as arc:
        status, _ = post(arc.base_url, "/api/cmd/RESET", {"game_id": SEALED_GAME},
                         headers={"X-API-Key": DEFAULT_KEY})
        assert status == 200


def test_a_refusal_is_recorded_three_ways(tmp_path):
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc, \
            proxy_over(arc, tmp_path) as proxy:
        post(proxy.base_url, "/api/cmd/RESET", {"game_id": SEALED_GAME})

    records = read_ledger(str(tmp_path / "l.jsonl"))
    kinds = [r["event"] for r in records]
    assert "guard_block" in kinds                        # the refusal itself
    assert "incident" in kinds                           # and as an incident
    assert "env_step" in kinds                           # and as a step with no frames

    step = next(r for r in records if r["event"] == "env_step")
    assert step["guard"]["decision"] == "deny"
    assert step["frames"] is None
    assert step["http"]["forwarded"] is False

    block = next(r for r in records if r["event"] == "guard_block")
    assert block["game_id"] == SEALED_GAME
    assert block["cut_sha256"].startswith("3feca53e")


def test_a_sealed_id_smuggled_into_a_payload_is_still_refused(tmp_path):
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc, \
            proxy_over(arc, tmp_path) as proxy:
        status, body = post(proxy.base_url, "/api/cmd/ACTION6",
                            {"game_id": DEFAULT_GAME,
                             "data": {"note": "compare with " + SEALED_GAME}})
        assert status == 403 and body["game_id"] == SEALED_GAME


def test_a_run_allowlist_is_enforced_at_the_proxy(tmp_path):
    guard = SealedPileGuard(allow_only=[DEFAULT_GAME])
    with MockArc(api_key=DEFAULT_KEY, games=[DEFAULT_GAME]) as arc, \
            proxy_over(arc, tmp_path, guard=guard) as proxy:
        assert post(proxy.base_url, "/api/cmd/RESET",
                    {"game_id": DEFAULT_GAME})[0] == 200
        status, body = post(proxy.base_url, "/api/cmd/RESET",
                            {"game_id": "g50t-5849a774"})
        assert status == 403 and body["rule"] == "not_in_run_allowlist"
