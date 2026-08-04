"""S47: the one `400` that is weather, and the many that are not.

`forward.py` retried on the status line alone, and its comment said a non-429
4xx is the upstream telling us something true. Four live legs on 2026-07-31
falsified that for exactly one response: `400` + `error: SERVER_ERROR` +
`message: "game <id> not found"`, where the byte-identical retry succeeded
seconds later. 494 of 570 outbound commands were that response.

The tests that matter here are the **negative** ones. A retry predicate that
says "try again" too readily does not fail loudly; it fails as a quota bill,
multiplied by `max_attempts`, drawn on a pool that is shared with every other
campaign. So each conjunct of the signature gets a test that removes it and
asserts the retry does not happen:

    conjunct removed                     test
    ------------------------------------ -------------------------------------
    status is 400                        the scorecard `404` is not retried
    error is the upstream's SERVER_ERROR  a `VALIDATION_ERROR` 400 is not retried
    message is exactly `game <id> ...`    an unanchored message is not retried
    the id is *this request's* id        another game's id is not retried

The third and fourth are the two the reporting arm insisted on, and the second
is the "a real 400 must still stop after one attempt" control.

    cd proxy && python -m pytest tests/test_forward_retry_predicate.py
"""

import email.message
import io
import json
import urllib.error

import pytest

from proxy import forward as fwd
from proxy.env_proxy import ARC_GAME_NOT_FOUND, game_not_found_retry
from proxy.spend_gate import SpendGate, SpendGateError, SpendPolicy
from proxy.variants import Variant

from test_redteam import ARC_KEY, Sink, env_proxy_over, post_json

GAME = "g50t-5849a774"
OTHER = "sk48-d8078629"

#: The wave, verbatim from `theoria-arm/runs/20260731T1240Z-A3-level2-carried/
#: ledger.jsonl` seq 4. The body has exactly these two keys.
WAVE = {"error": "SERVER_ERROR", "message": "game %s not found" % GAME}

#: The negative sample that lives in the same four legs: a scorecard the server
#: auto-closed. It also ends in "not found", which is why the substring is not
#: the signature.
SCORECARD_GONE = {"error": "VALIDATION_ERROR",
                  "message": "scorecard 32ca4788-e9a7-424e-926c-a47b557c03a9 not found"}

OK = {"state": "NOT_FINISHED", "frame": [[[0]]], "score": 0,
      "levels_completed": 0, "guid": "30be5721-565d-4b0f-aeca-c7a97e576619"}


# -- helpers ----------------------------------------------------------------

def policy(tmp_path, *, usd=100.0, actions=1000):
    return SpendPolicy({"v": "1.0", "pool": "test-pool", "usd_ceiling": usd,
                        "action_ceiling": actions,
                        "ledger": str(tmp_path / "spend.jsonl"),
                        "default_ttl_seconds": 3600.0,
                        "lock_timeout_seconds": 5.0,
                        "default_run_caps": {"usd": 10.0, "actions": 500}},
                       source=None)


@pytest.fixture
def permit(tmp_path):
    gate = SpendGate(policy(tmp_path))
    return gate.permit(gate.reserve("s47", usd_cap=10.0, action_cap=500),
                       usd=0.0, actions=1)


def _headers():
    message = email.message.Message()
    message["Content-Type"] = "application/json"
    return message


class Script:
    """A scripted `_OPENER.open`: one `(status, body)` per attempt.

    Non-2xx is raised as `HTTPError`, which is what the real opener chain does
    and which `forward()` handles in its own branch -- a fake that returned 400
    as a normal response would exercise a path production never takes.
    """

    def __init__(self, *replies):
        self.replies = list(replies)
        self.opened = 0

    def __call__(self, request, timeout=None):
        status, body = self.replies[min(self.opened, len(self.replies) - 1)]
        self.opened += 1
        payload = json.dumps(body).encode()
        if status >= 400:
            raise urllib.error.HTTPError("http://up/x", status, "err",
                                         _headers(), io.BytesIO(payload))

        class _Ok:
            def __enter__(_self):
                _self.status = status
                _self.headers = _headers()
                _self.url = "http://up/x"
                _self.read = lambda: payload
                return _self

            def __exit__(_self, *exc):
                return False
        return _Ok()


def run(monkeypatch, permit, script, retry_body, *, max_attempts=5):
    monkeypatch.setattr(fwd._OPENER, "open", script)
    return fwd.forward("http://up/x", "POST", {}, b"{}", max_attempts=max_attempts,
                       backoff=0.0, permit=permit, retry_body=retry_body)


# -- 1. the predicate on its own --------------------------------------------

def test_the_wave_is_the_only_thing_the_predicate_accepts():
    retryable = game_not_found_retry(GAME)
    assert retryable(400, {}, json.dumps(WAVE).encode()) is True


def test_the_scorecard_404_is_not_retried():
    """Negative sample 1, mandatory. A card the server auto-closed is a real and
    consequential failure that happens to end in the same two words."""
    retryable = game_not_found_retry(GAME)
    assert retryable(404, {}, json.dumps(SCORECARD_GONE).encode()) is False
    # Even at 400 it is refused, so the status conjunct is not carrying the
    # whole negative on its own.
    assert retryable(400, {}, json.dumps(SCORECARD_GONE).encode()) is False


def test_a_message_naming_another_game_is_not_retried():
    """Negative sample 2, mandatory. Without this conjunct the predicate
    recognises a sentence shape rather than this game -- and a message naming a
    game the request did not ask for means the id really was wrong, which is a
    client defect and not weather."""
    retryable = game_not_found_retry(GAME)
    body = json.dumps({"error": "SERVER_ERROR",
                       "message": "game %s not found" % OTHER}).encode()
    assert retryable(400, {}, body) is False


def test_a_genuine_400_is_not_retried():
    """Negative sample 3. The upstream is allowed to say true things in a 400,
    and a retry policy that only knows how to say 'again' is the one that burns
    the quota."""
    retryable = game_not_found_retry(GAME)
    for body in ({"error": "VALIDATION_ERROR", "message": "game %s not found" % GAME},
                 {"error": "RATE_LIMIT", "message": "game %s not found" % GAME},
                 {"error": "SERVER_ERROR", "message": ""},
                 {"error": "SERVER_ERROR"},
                 {"message": "game %s not found" % GAME}):
        assert retryable(400, {}, json.dumps(body).encode()) is False, body


def test_the_message_is_anchored_not_contained():
    retryable = game_not_found_retry(GAME)
    for message in ("the game %s not found today" % GAME,
                    "game %s not found; retry later" % GAME,
                    "not found",
                    "game not found",
                    "xgame %s not found" % GAME):
        body = json.dumps({"error": "SERVER_ERROR", "message": message}).encode()
        assert retryable(400, {}, body) is False, message


def test_a_body_that_is_not_a_json_object_is_not_retried():
    """HTML from a load balancer, a bare string, a list. None of them is the
    upstream saying SERVER_ERROR, and guessing is how a predicate widens."""
    retryable = game_not_found_retry(GAME)
    for raw in (b"<html>502 Bad Gateway</html>", b"", b"null", b"[]",
                b'"game %s not found"' % GAME.encode(), b"{"):
        assert retryable(400, {}, raw) is False, raw


def test_without_a_game_id_there_is_no_body_rule_at_all():
    """`/api/scorecard/*` names no game. Returning `None` rather than a
    predicate that cannot check conjunct 3 keeps 'no id' from silently becoming
    'any id'."""
    assert game_not_found_retry(None) is None
    assert game_not_found_retry("") is None
    assert game_not_found_retry("?") is None       # `_command`'s absent-id value


def test_the_id_is_matched_case_insensitively_but_it_is_still_matched():
    """A case variant must not make S47 a silent no-op.

    The id compare folds case, matching `guard.py:stem()`, which lowercases so
    that a case variant cannot walk past the seal, and matching
    `harness/arc.py:FULL_ID`, which admits an uppercase stem. An exact codepoint
    compare -- the first version here -- meant an upstream echoing `G50T-...`
    for a request naming `g50t-...` got no retry, no `body_retry` marker, no
    incident and no failing test: the fix doing nothing while looking correct.

    Folding is safe in the direction that matters, and this asserts both halves:
    a case-varied id still matches, and a *different* id still does not.
    """
    assert ARC_GAME_NOT_FOUND.match("GAME %s NOT FOUND" % GAME).group("game_id") == GAME

    retryable = game_not_found_retry(GAME)
    for message in ("GAME %s NOT FOUND" % GAME,          # the sentence shouted
                    "game %s not found" % GAME.upper(),  # the id shouted
                    "GaMe %s NoT fOuNd" % GAME.upper()):
        body = json.dumps({"error": "SERVER_ERROR", "message": message}).encode()
        assert retryable(400, {}, body) is True, message

    # ...and folding did not soften the conjunct it exists to enforce.
    other = json.dumps({"error": "SERVER_ERROR",
                        "message": "game %s not found" % OTHER.upper()}).encode()
    assert retryable(400, {}, other) is False

    # `error` is compared exactly, deliberately: the upstream's label is a
    # constant it sends, not a spelling to be guessed at.
    lower = json.dumps({"error": "server_error",
                        "message": "game %s not found" % GAME}).encode()
    assert retryable(400, {}, lower) is False




# -- 2. forward()'s loop -----------------------------------------------------

def test_the_wave_collapses_into_one_response(monkeypatch, permit):
    script = Script((400, WAVE), (400, WAVE), (200, OK))
    response = run(monkeypatch, permit, script, game_not_found_retry(GAME))

    assert response.status == 200
    assert response.attempts == 3
    assert [a["status"] for a in response.attempt_log] == [400, 400, 200]
    assert script.opened == 3


def test_a_body_retry_is_marked_in_the_attempt_log(monkeypatch, permit):
    """A collapsed row otherwise cannot be told from a rate-limit retry, and the
    reason for collapsing this wave at all is that its size stops being
    invisible."""
    script = Script((400, WAVE), (200, OK))
    response = run(monkeypatch, permit, script, game_not_found_retry(GAME))

    assert response.attempt_log[0]["body_retry"] is True
    assert "body_retry" not in response.attempt_log[1]


def test_the_retry_is_bounded_by_max_attempts(monkeypatch, permit):
    """A wave that never clears must stop, and stop where the existing bound
    says. This is the ceiling that makes an in-forward retry cheaper to reason
    about than a caller-level one.

    The last attempt is asserted **unmarked**, not skipped. `body_retry` means
    "this attempt was retried", and on the last attempt of an exhausted call
    nothing is retried -- the loop stops and the caller gets the refusal. The
    first version of this assertion read `attempt_log[:-1]`, which excluded
    exactly the entry that was being marked wrongly, so the over-count survived
    a green suite. A counter over `body_retry` would have read one retry too
    many for every exhausted call.
    """
    script = Script((400, WAVE))
    response = run(monkeypatch, permit, script, game_not_found_retry(GAME),
                   max_attempts=4)

    assert response.status == 400
    assert response.attempts == 4
    assert script.opened == 4
    assert all(a["body_retry"] for a in response.attempt_log[:-1])
    assert "body_retry" not in response.attempt_log[-1]
    assert sum(1 for a in response.attempt_log if a.get("body_retry")) == 3


def test_a_wave_that_clears_marks_every_attempt_that_was_retried(monkeypatch, permit):
    """The other side of the same field: when the call is not exhausted, every
    refusal really was retried and every one is marked."""
    script = Script((400, WAVE), (400, WAVE), (400, WAVE), (200, OK))
    response = run(monkeypatch, permit, script, game_not_found_retry(GAME),
                   max_attempts=5)

    assert response.status == 200
    marked = [a["attempt"] for a in response.attempt_log if a.get("body_retry")]
    assert marked == [1, 2, 3]
    assert "body_retry" not in response.attempt_log[-1]


def test_every_body_retry_costs_the_pool_one_action(monkeypatch, permit):
    """The permit is checked and counted before every socket. Moving the retry
    into `forward()` moves ledger rows, not sockets -- the pool pays the same
    either way, and a test that let it pay less would be measuring a fiction."""
    script = Script((400, WAVE), (400, WAVE), (200, OK))
    run(monkeypatch, permit, script, game_not_found_retry(GAME))

    assert permit.attempts_made == 3


def test_a_real_400_still_stops_after_one_attempt(monkeypatch, permit):
    script = Script((400, SCORECARD_GONE), (200, OK))
    response = run(monkeypatch, permit, script, game_not_found_retry(GAME))

    assert response.status == 400
    assert response.attempts == 1
    assert script.opened == 1, "a truthful refusal was retried"
    assert permit.attempts_made == 1


def test_another_games_id_still_stops_after_one_attempt(monkeypatch, permit):
    body = {"error": "SERVER_ERROR", "message": "game %s not found" % OTHER}
    script = Script((400, body), (200, OK))
    response = run(monkeypatch, permit, script, game_not_found_retry(GAME))

    assert response.attempts == 1
    assert script.opened == 1


def test_without_the_predicate_the_wave_is_not_retried(monkeypatch, permit):
    """The parameter widens and can never narrow: unset, this is byte-for-byte
    the behaviour that shipped before S47."""
    script = Script((400, WAVE), (200, OK))
    response = run(monkeypatch, permit, script, None)

    assert response.status == 400
    assert response.attempts == 1
    assert "body_retry" not in response.attempt_log[0]


def test_the_predicate_is_asked_about_nothing_but_declined_errors(monkeypatch, permit):
    """Two ways the hook could reach further than it should, and both are shut.

    A predicate asked about a `429` could vote *against* a retry the status set
    had already granted -- narrowing, when the parameter exists only to widen.
    A predicate asked about the `200` that ends the retry could answer yes, and
    then this loop would discard a response the pool has already paid for.
    """
    asked = []

    def nosy(status, headers, body):
        asked.append(status)
        return True                       # the worst possible answer, every time

    script = Script((429, {"error": "slow down"}), (200, OK))
    response = run(monkeypatch, permit, script, nosy)

    assert response.status == 200
    assert response.attempts == 2, "a success was thrown away and re-bought"
    assert asked == [], "the predicate was consulted outside its window"


def test_a_predicate_that_raises_is_not_swallowed(monkeypatch, permit):
    """Turning a caller's bug into the silent answer 'do not retry' would be the
    answer that looks correct in every log."""
    def broken(status, headers, body):
        raise RuntimeError("predicate is wrong")

    script = Script((400, WAVE))
    with pytest.raises(RuntimeError):
        run(monkeypatch, permit, script, broken)
    assert permit.attempts_made == 1     # the socket that happened is still counted


def test_transport_failures_are_unchanged_by_the_predicate(monkeypatch, permit):
    class _Boom:
        def __enter__(self): raise OSError("upstream is down")
        def __exit__(self, *exc): return False

    monkeypatch.setattr(fwd._OPENER, "open", lambda *a, **k: _Boom())
    response = fwd.forward("http://up/x", "POST", {}, b"{}", max_attempts=3,
                           backoff=0.0, permit=permit,
                           retry_body=game_not_found_retry(GAME))

    assert response.attempts == 3
    assert all("body_retry" not in a for a in response.attempt_log)


# -- 3. end to end: one command, one row ------------------------------------

def _steps(proxy_ledger_path):
    with open(proxy_ledger_path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return [r for r in rows if r.get("event") == "env_step"]


def test_the_wave_becomes_one_env_step_with_an_attempt_log(tmp_path):
    """The finding, closed. Three outbound attempts, one ledger row -- which is
    what `LEDGER_FORMAT.md` always said `attempts` meant, and what the wave was
    the single exception to."""
    replies = [(400, WAVE), (400, WAVE), (200, OK)]

    def reply(handler):
        status, body = replies[min(len(handler.server.seen) - 1, len(replies) - 1)]
        return status, body, {"Content-Type": "application/json"}

    with Sink(reply) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, _ = post_json(proxy.base_url, "/api/cmd/RESET",
                                     {"game_id": GAME, "card_id": "c-1"})

    assert status == 200
    assert len(upstream.seen) == 3, "the retry did not reach the upstream"

    steps = _steps(str(tmp_path / "l.jsonl"))
    assert len(steps) == 1, "the retry became a second row again"
    http = steps[0]["http"]
    assert http["status"] == 200
    assert http["attempts"] == 3
    assert [a["status"] for a in http["attempt_log"]] == [400, 400, 200]
    assert http["attempt_log"][0]["body_retry"] is True


def test_the_action_path_is_covered_and_not_just_reset(tmp_path):
    """Where the wave actually lives. In `20260731T1430Z-A3-level2-carried-r3`,
    199 of the 200 refusals are `ACTIONn` and one is `RESET` -- so a fix that
    reached only `RESET` would close half a percent of the finding while looking
    finished. `_command` reads `game_id` from the request body for both, which
    is what makes conjunct 3 available on an action at all."""
    replies = [(400, WAVE), (200, OK)]

    def reply(handler):
        status, body = replies[min(len(handler.server.seen) - 1, len(replies) - 1)]
        return status, body, {"Content-Type": "application/json"}

    with Sink(reply) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, _ = post_json(proxy.base_url, "/api/cmd/ACTION5",
                                     {"game_id": GAME, "card_id": "c-1",
                                      "guid": OK["guid"]})

    assert status == 200
    assert len(upstream.seen) == 2
    steps = _steps(str(tmp_path / "l.jsonl"))
    assert len(steps) == 1
    assert steps[0]["action"]["name"] == "ACTION5"
    assert steps[0]["http"]["attempts"] == 2
    assert steps[0]["http"]["attempt_log"][0]["body_retry"] is True


def test_a_command_that_names_no_game_never_reaches_the_predicate(tmp_path):
    """`_command` falls back to `"?"` when the body carries no `game_id`, and
    `game_not_found_retry("?")` returns no predicate for it. That turns out to be
    belt on top of braces: the sealed-pile guard refuses an unknown game **403
    before any socket opens**, so this request never reaches `forward()` at all.

    Asserted as the guard's 403 rather than as a 400 that was not retried,
    because that is what actually happens; a test that asserted the weaker thing
    would keep passing if the guard were removed."""
    def reply(handler):
        return 400, {"error": "SERVER_ERROR", "message": "game ? not found"}, \
            {"Content-Type": "application/json"}

    with Sink(reply) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, _ = post_json(proxy.base_url, "/api/cmd/RESET",
                                     {"card_id": "c-1"})

    assert status == 403
    assert upstream.seen == [], "a game-less command reached the upstream"
    assert game_not_found_retry("?") is None


def test_a_remapping_variant_still_gets_the_original_games_predicate(tmp_path):
    """A variant may rewrite the *action*; it never rewrites the game.

    `_command` builds the predicate from `game_id`, which is read from the
    request body before any variant runs, and forwards to `forwarded_path`,
    which the remap may have changed. Nothing asserted that those two stayed
    correctly separated -- and if the predicate had been derived from the
    forwarded path instead, an ablation leg would silently lose the retry while
    a plain leg kept it, which is the shape of a difference that gets attributed
    to the ablation.
    """
    variant = Variant({
        "variant_id": "t-swap", "base_game": GAME, "claim": "solvable",
        "operators": [{"op": "remap_action", "from": "ACTION3", "to": "ACTION4"}],
        "justification": ("Relabelling is a bijection on the action alphabet, "
                          "so it cannot change what is achievable."),
    })
    replies = [(400, WAVE), (200, OK)]

    def reply(handler):
        status, body = replies[min(len(handler.server.seen) - 1, len(replies) - 1)]
        return status, body, {"Content-Type": "application/json"}

    with Sink(reply) as upstream:
        with env_proxy_over(upstream.url, tmp_path, variant=variant) as proxy:
            status, _, _ = post_json(proxy.base_url, "/api/cmd/ACTION3",
                                     {"game_id": GAME, "card_id": "c-1",
                                      "guid": OK["guid"]})

    assert status == 200
    assert [s["path"] for s in upstream.seen] == ["/api/cmd/ACTION4"] * 2, \
        "the remap did not apply, so this proves nothing about the separation"
    steps = _steps(str(tmp_path / "l.jsonl"))
    assert len(steps) == 1, "the wave was not collapsed under a remapping variant"
    assert steps[0]["http"]["attempts"] == 2
    assert steps[0]["http"]["attempt_log"][0]["body_retry"] is True


def test_a_truthful_400_is_still_one_row_and_one_attempt(tmp_path):
    def reply(handler):
        return 400, SCORECARD_GONE, {"Content-Type": "application/json"}

    with Sink(reply) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, _ = post_json(proxy.base_url, "/api/cmd/RESET",
                                     {"game_id": GAME, "card_id": "c-1"})

    assert status == 400
    assert len(upstream.seen) == 1, "a truthful refusal was retried upstream"
    steps = _steps(str(tmp_path / "l.jsonl"))
    assert len(steps) == 1
    assert steps[0]["http"]["attempts"] == 1
    assert "attempt_log" not in steps[0]["http"]


def test_scorecard_traffic_gets_no_body_rule(tmp_path):
    """`/api/scorecard/*` names no game, so conjunct 3 has nothing to check
    against and the predicate is not built at all. The 404 in the archives is
    the reason this path must stay exactly as it was."""
    def reply(handler):
        return 404, SCORECARD_GONE, {"Content-Type": "application/json"}

    with Sink(reply) as upstream:
        with env_proxy_over(upstream.url, tmp_path) as proxy:
            status, _, _ = post_json(proxy.base_url, "/api/scorecard/close",
                                     {"card_id": "c-1"})

    assert status == 404
    assert len(upstream.seen) == 1, "scorecard traffic was retried"
