"""A keyless arm.

It exists to demonstrate the shape every real arm has under the double proxy:
two base URLs from the environment, and nothing else. There is no credential in
this file, none in its process environment, and no code path that would use one
if there were. It is deliberately dumb -- observe, ask, execute, record -- so
that anything interesting in the ledger came from the proxies, not from here.

`assert_sealed()` is the arm-side half of the sealing test: an arm that finds a
credential in its own environment refuses to start, because a run where the arm
*could* have gone around the proxy proves nothing about a run where it didn't.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

#: Names an arm must not be able to see. The environment proxy holds the first;
#: the model proxy holds the rest.
FORBIDDEN_ENV = ("ARC_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                 "OPENAI_API_KEY")


class NotSealedError(RuntimeError):
    """The arm can see a credential, so this run cannot demonstrate sealing."""


def assert_sealed(env: Optional[Dict[str, str]] = None) -> None:
    env = os.environ if env is None else env
    leaked = sorted(name for name in FORBIDDEN_ENV if env.get(name))
    if leaked:
        raise NotSealedError(
            "the arm can see %s. An arm holding a credential can leave the "
            "recorded path, so the run would not be closed." % ", ".join(leaked))


def _post(base: str, path: str, body: Dict[str, Any],
          headers: Optional[Dict[str, str]] = None,
          timeout: float = 30.0) -> Tuple[int, Any]:
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        base.rstrip("/") + path, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            content_type = response.headers.get("Content-Type", "")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        status = exc.code

    if "text/event-stream" in content_type.lower():
        return status, _from_sse(raw)
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, {"error": raw}


def _from_sse(raw: str) -> Dict[str, Any]:
    """Reassemble a streamed message into the non-streaming shape.

    The proxy passes the provider's bytes through untouched -- it records, it
    does not translate -- so an arm that asks for a stream has to read one.
    """
    text: List[str] = []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            event = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "content_block_delta":
            delta = event.get("delta") or {}
            if delta.get("type") == "text_delta":
                text.append(delta.get("text", ""))
    return {"content": [{"type": "text", "text": "".join(text)}]}


class MockArm:
    def __init__(self, env_base: Optional[str] = None,
                 model_base: Optional[str] = None,
                 model: str = "mock-model-1",
                 arm: str = "mock_arm",
                 stream: bool = False,
                 check_sealed: bool = True):
        if check_sealed:
            assert_sealed()
        self.env_base = env_base or os.environ["ARC_BASE_URL"]
        self.model_base = model_base or os.environ["MODEL_BASE_URL"]
        self.model = model
        self.arm = arm
        self.stream = stream
        self.model_calls = 0

    # -- the outer loop ----------------------------------------------------
    def play(self, game_id: str, budget: int = 40) -> Dict[str, Any]:
        _, card = _post(self.env_base, "/api/scorecard/open",
                        {"arm": self.arm, "game_id": game_id})
        card_id = card.get("card_id")

        status, frame = _post(self.env_base, "/api/cmd/RESET",
                              {"game_id": game_id, "card_id": card_id})
        if status >= 400:
            _post(self.env_base, "/api/scorecard/close", {"card_id": card_id})
            return {"outcome": "reset_failed", "status": status, "detail": frame,
                    "card_id": card_id, "actions": 0, "model_calls": 0}

        guid = frame.get("guid")
        actions: List[int] = []
        step = 0
        outcome = "budget_exhausted"

        while step < budget:
            state = frame.get("state")
            if state in ("WIN", "GAME_OVER"):
                outcome = state
                break
            step += 1
            action_id = self.decide(frame, step)
            actions.append(action_id)
            status, frame = _post(
                self.env_base, "/api/cmd/ACTION%d" % action_id,
                {"game_id": game_id, "card_id": card_id, "guid": guid})
            if status >= 400:
                outcome = "refused_%d" % status
                break
        else:
            state = frame.get("state")
            if state in ("WIN", "GAME_OVER"):
                outcome = state

        if frame.get("state") in ("WIN", "GAME_OVER"):
            outcome = frame["state"]

        _, closed = _post(self.env_base, "/api/scorecard/close", {"card_id": card_id})
        return {"outcome": outcome, "card_id": card_id, "guid": guid,
                "game_id": game_id, "actions": actions,
                "steps": len(actions), "model_calls": self.model_calls,
                "score": frame.get("score"),
                "levels_completed": frame.get("levels_completed"),
                "scorecard": closed}

    # -- the inner loop ----------------------------------------------------
    def decide(self, frame: Dict[str, Any], step: int) -> int:
        """One model call per action. The frame goes into the prompt as JSON so
        the stand-in provider can read it; a real arm would render it however
        its inner loop prefers."""
        observation = json.dumps({"frame": frame.get("frame"),
                                  "state": frame.get("state"),
                                  "score": frame.get("score"),
                                  "available_actions": frame.get("available_actions")},
                                 sort_keys=True)
        request = {
            "model": self.model,
            "max_tokens": 256,
            "messages": [{"role": "user", "content": observation}],
        }
        if self.stream:
            request["stream"] = True

        status, response = _post(self.model_base, "/v1/messages", request,
                                 headers={"X-Theoria-Step": str(step)})
        self.model_calls += 1
        if status >= 400:
            return 5                                   # no-op; the ledger has the error

        return self._action_from(response)

    @staticmethod
    def _action_from(response: Any) -> int:
        text = ""
        if isinstance(response, dict):
            for block in response.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")
        try:
            parsed = json.loads(text)
            action_id = int(parsed["action"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return 5
        return action_id if 1 <= action_id <= 9 else 5
