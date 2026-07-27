"""A deterministic stand-in for a model provider.

It answers `POST /v1/messages` in the provider's response shape, including a
`usage` block, and supports `stream: true` so the model proxy's SSE usage
extraction has something to extract from.

It is a *solver*, not a language model: given the frame in the prompt it runs a
breadth-first search over the same transition rule the mock world applies, and
returns the next action. That keeps the end-to-end run deterministic -- a
replay has to reproduce the frames exactly, which it cannot do if the decider
is stochastic -- and it is honest about what this is: the mock model is a
fixture, not a claim about model behaviour.
"""

import json
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

from .arc_mock import AGENT, GOAL, MOVES, WALL, slide

DEFAULT_KEY = "mock-model-key-000000000000000"
DEFAULT_MODEL = "mock-model-1"


def find(grid: List[List[int]], value: int) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == value:
                return (r, c)
    return None


def next_action(grid: List[List[int]]) -> int:
    """Breadth-first search for the first action on a shortest route to the goal.

    Ties are broken by ascending action id, so the answer is a function of the
    grid alone.
    """
    start = find(grid, AGENT)
    goal = find(grid, GOAL)
    if start is None or goal is None:
        return 5                                        # nothing to do; no-op

    seen = {start}
    queue = deque([(start, None)])
    while queue:
        pos, first = queue.popleft()
        if pos == goal:
            return first if first is not None else 5
        for action_id in sorted(MOVES):
            delta = MOVES[action_id]
            if delta == (0, 0):
                continue
            path = slide(grid, pos, delta)
            landing = path[-1]
            if landing == pos or landing in seen:
                continue
            if grid[landing[0]][landing[1]] == WALL:
                continue
            seen.add(landing)
            queue.append((landing, first if first is not None else action_id))
    return 5


def _grid_from_request(body: Dict[str, Any]) -> Optional[List[List[int]]]:
    """The arm puts the frame in the last user message as JSON. Anything else
    is answered with a no-op rather than an error -- a stand-in provider that
    500s would mask harness bugs behind transport failures."""
    for message in reversed(body.get("messages") or []):
        content = message.get("content")
        chunks = ([content] if isinstance(content, str)
                  else [b.get("text", "") for b in content or []
                        if isinstance(b, dict)])
        for chunk in chunks:
            try:
                parsed = json.loads(chunk)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("frame"), list):
                frame = parsed["frame"]
                return frame[-1] if frame and isinstance(frame[0], list) else None
    return None


def _usage(body: Dict[str, Any], reply: str) -> Dict[str, Any]:
    """A stand-in usage block with the provider's own key names. It is a
    character count, not a tokenizer -- what matters here is that the ledger
    copies whatever keys arrive, verbatim."""
    prompt = json.dumps(body.get("messages") or [], sort_keys=True)
    return {
        "input_tokens": max(1, len(prompt) // 4),
        "output_tokens": max(1, len(reply) // 4),
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "mock-provider/1.0"

    def log_message(self, fmt, *args):
        pass

    @property
    def api_key(self) -> str:
        return self.server.api_key                                 # type: ignore[attr-defined]

    def _respond(self, status: int, payload: Any,
                 content_type: str = "application/json") -> None:
        body = (payload if isinstance(payload, bytes)
                else json.dumps(payload).encode("utf-8"))
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}

        if self.headers.get("x-api-key") != self.api_key:
            return self._respond(401, {"type": "error", "error": {
                "type": "authentication_error", "message": "invalid x-api-key"}})

        if path != "/v1/messages":
            return self._respond(404, {"type": "error", "error": {
                "type": "not_found_error", "message": "no such route"}})

        grid = _grid_from_request(body)
        action_id = next_action(grid) if grid else 5
        reply = json.dumps({"action": action_id,
                            "why": "shortest route to the goal"})
        model = body.get("model", DEFAULT_MODEL)
        usage = _usage(body, reply)

        if body.get("stream"):
            return self._respond(200, _sse(model, reply, usage).encode("utf-8"),
                                 content_type="text/event-stream")

        self._respond(200, {
            "id": "msg_mock",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": reply}],
            "stop_reason": "end_turn",
            "usage": usage,
        })


def _sse(model: str, reply: str, usage: Dict[str, Any]) -> str:
    """Usage split across `message_start` and `message_delta`, as the real
    provider does -- the proxy has to merge the two halves."""
    start_usage = {k: v for k, v in usage.items() if k != "output_tokens"}
    events = [
        ("message_start", {"type": "message_start", "message": {
            "id": "msg_mock", "type": "message", "role": "assistant",
            "model": model, "content": [], "usage": start_usage}}),
        ("content_block_start", {"type": "content_block_start", "index": 0,
                                 "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                 "delta": {"type": "text_delta", "text": reply}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("message_delta", {"type": "message_delta",
                           "delta": {"stop_reason": "end_turn"},
                           "usage": {"output_tokens": usage["output_tokens"]}}),
        ("message_stop", {"type": "message_stop"}),
    ]
    return "".join("event: %s\ndata: %s\n\n" % (name, json.dumps(payload))
                   for name, payload in events)


class MockProvider:
    def __init__(self, api_key: str = DEFAULT_KEY,
                 host: str = "127.0.0.1", port: int = 0):
        self.httpd = ThreadingHTTPServer((host, port), _Handler)
        self.httpd.api_key = api_key                               # type: ignore[attr-defined]
        self.httpd.daemon_threads = True
        self.host = host
        self._thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        return "http://%s:%d" % (self.host, self.httpd.server_address[1])

    def start(self) -> "MockProvider":
        self._thread = threading.Thread(target=self.httpd.serve_forever,
                                        name="mock-provider", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self) -> "MockProvider":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()
