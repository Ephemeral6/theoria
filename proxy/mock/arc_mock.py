"""A deterministic stand-in for the ARC environment.

It is not a good game. It is a *checkable* one, and each property exists to
exercise one Phase 1 obligation:

  * **Deterministic** -- the same action sequence from RESET always produces
    the same frames, so a replay mismatch means the harness is broken rather
    than the world being noisy.
  * **One action can return several frames.** Stepping onto a conveyor, or
    finishing a level, returns two frames. The precheck observed up to seven
    frames from one command on the real API, so a harness that assumes
    action -> single frame is wrong; this makes that assumption fail loudly.
  * **It has levels**, so `level` / `level_boundary` derivation has something
    to derive, and the score reconciler has something to reconcile.
  * **It requires the credential.** Without a valid `X-API-Key` every gameplay
    route answers 401. That is what makes the sealing test a proof rather than
    an assertion: an arm with no key provably cannot play.

Grid cells: 0 empty, 1 wall, 2 agent, 3 goal, 4 conveyor.
"""

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

EMPTY, WALL, AGENT, GOAL, CONVEYOR = 0, 1, 2, 3, 4

_GLYPH = {"#": WALL, ".": EMPTY, "a": AGENT, "g": GOAL, ">": CONVEYOR}

LEVELS: List[List[str]] = [
    [
        "########",
        "#a.....#",
        "#.####.#",
        "#......#",
        "#.####.#",
        "#..>...#",
        "#.....g#",
        "########",
    ],
    [
        "########",
        "#.....a#",
        "#.####.#",
        "#......#",
        "#.####.#",
        "#......#",
        "#g.....#",
        "########",
    ],
    [
        "########",
        "#.....g#",
        "#.####.#",
        "#..>...#",
        "#.####.#",
        "#......#",
        "#a.....#",
        "########",
    ],
]

#: ACTION id -> (d_row, d_col). ACTION5 is a no-op "interact", kept because the
#: real API exposes an action that does not always move the agent.
MOVES = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1), 5: (0, 0)}
AVAILABLE_ACTIONS = [1, 2, 3, 4, 5]

DEFAULT_KEY = "mock-arc-key-0000000000000000"
DEFAULT_GAME = "ar25-0c556536"


def slide(grid: List[List[int]], pos: Tuple[int, int],
          delta: Tuple[int, int]) -> List[Tuple[int, int]]:
    """One command's worth of movement: the positions the agent passes through.

    Exported because a solver has to model the same transition the world
    applies; two copies of this rule would eventually disagree, and the
    disagreement would look like the environment being non-deterministic.
    """
    d_row, d_col = delta
    if (d_row, d_col) == (0, 0):
        return [pos]
    target = (pos[0] + d_row, pos[1] + d_col)
    if grid[target[0]][target[1]] == WALL:
        return [pos]
    path = [target]
    if grid[target[0]][target[1]] == CONVEYOR:
        slid = (target[0] + d_row, target[1] + d_col)
        if grid[slid[0]][slid[1]] != WALL:
            path.append(slid)
    return path


def _parse(rows: List[str]) -> Tuple[List[List[int]], Tuple[int, int]]:
    grid: List[List[int]] = []
    start = (1, 1)
    for r, row in enumerate(rows):
        line = []
        for c, ch in enumerate(row):
            value = _GLYPH[ch]
            if value == AGENT:
                start = (r, c)
                value = EMPTY
            line.append(value)
        grid.append(line)
    return grid, start


class Session:
    """One RESET's worth of world state. Pure function of the actions applied."""

    def __init__(self, guid: str, game_id: str, card_id: Optional[str]):
        self.guid = guid
        self.game_id = game_id
        self.card_id = card_id
        self.level = 0
        self.levels_completed = 0
        self.actions = 0
        self.state = "NOT_FINISHED"
        self.grid, self.pos = _parse(LEVELS[0])

    # -- rendering ---------------------------------------------------------
    def render(self) -> List[List[int]]:
        frame = [row[:] for row in self.grid]
        if self.state != "WIN":
            frame[self.pos[0]][self.pos[1]] = AGENT
        return frame

    def _load_level(self, index: int) -> None:
        self.level = index
        self.grid, self.pos = _parse(LEVELS[index])

    # -- stepping ----------------------------------------------------------
    def step(self, action_id: int) -> List[List[List[int]]]:
        """Apply one command; return the frame sequence it produced."""
        if self.state == "WIN":
            return [self.render()]

        self.actions += 1
        d_row, d_col = MOVES.get(action_id, (0, 0))
        if (d_row, d_col) == (0, 0):
            return [self.render()]

        path = slide(self.grid, self.pos, (d_row, d_col))
        if path == [self.pos]:
            return [self.render()]                       # bumped a wall

        # One command, one frame per position passed through: a conveyor makes
        # a single action observably a *sequence*.
        frames = []
        for step in path:
            self.pos = step
            frames.append(self.render())

        if self.grid[self.pos[0]][self.pos[1]] == GOAL:
            self.levels_completed += 1
            if self.levels_completed >= len(LEVELS):
                self.state = "WIN"
                frames.append(self.render())
            else:
                self._load_level(self.levels_completed)
                frames.append(self.render())
        return frames

    def body(self, action_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "guid": self.guid,
            "card_id": self.card_id,
            "frame": [self.render()],
            "state": self.state,
            "score": self.levels_completed,
            "levels_completed": self.levels_completed,
            "action_counter": self.actions,
            "available_actions": list(AVAILABLE_ACTIONS),
            "action_input": action_input,
        }


class World:
    """All sessions and scorecards. Deterministic given the command sequence."""

    def __init__(self, api_key: str = DEFAULT_KEY, games: Optional[List[str]] = None):
        self.api_key = api_key
        self.games = games or [DEFAULT_GAME]
        self.lock = threading.Lock()
        self.sessions: Dict[str, Session] = {}
        self.cards: Dict[str, Dict[str, Any]] = {}
        self._resets = 0
        self._cards_opened = 0

    def _digest(self, *parts: Any) -> str:
        blob = json.dumps(parts, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()[:16]

    def open_card(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            self._cards_opened += 1
            # The metadata is part of the id so that two cards opened for
            # different purposes -- a game and a prefix replay's probe -- are
            # distinguishable even in a freshly started world.
            card_id = "card-" + self._digest("card", self._cards_opened, metadata)
            self.cards[card_id] = {"card_id": card_id, "metadata": metadata,
                                   "cards": {}, "won": 0, "played": 0,
                                   "total_actions": 0, "score": 0}
            return {"card_id": card_id}

    def close_card(self, card_id: str) -> Dict[str, Any]:
        with self.lock:
            card = self.cards.get(card_id)
            if card is None:
                return {"error": "no such card_id", "card_id": card_id}
            return json.loads(json.dumps(card))

    def _touch_card(self, session: Session) -> None:
        card = self.cards.get(session.card_id or "")
        if card is None:
            return
        entry = card["cards"].setdefault(
            session.game_id, {"game_id": session.game_id, "total_plays": 0,
                              "scores": [], "actions": 0, "states": []})
        entry["actions"] = session.actions
        entry["scores"] = [session.levels_completed]
        entry["states"] = [session.state]
        card["total_actions"] = sum(g["actions"] for g in card["cards"].values())
        card["score"] = sum(max(g["scores"]) for g in card["cards"].values())
        card["won"] = sum(1 for g in card["cards"].values() if "WIN" in g["states"])
        card["played"] = len(card["cards"])

    def reset(self, game_id: str, card_id: Optional[str]) -> Dict[str, Any]:
        with self.lock:
            self._resets += 1
            guid = "guid-" + self._digest("guid", game_id, card_id, self._resets)
            session = Session(guid, game_id, card_id)
            self.sessions[guid] = session
            card = self.cards.get(card_id or "")
            if card is not None:
                card["cards"].setdefault(
                    game_id, {"game_id": game_id, "total_plays": 0, "scores": [],
                              "actions": 0, "states": []})["total_plays"] += 1
            self._touch_card(session)
            return session.body()

    def action(self, game_id: str, guid: str, action_id: int,
               data: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        with self.lock:
            session = self.sessions.get(guid)
            if session is None:
                return 400, {"error": "unknown guid", "guid": guid}
            if session.game_id != game_id:
                return 400, {"error": "guid belongs to another game"}
            frames = session.step(action_id)
            self._touch_card(session)
            body = session.body(action_input=data)
            body["frame"] = frames
            return 200, body


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "mock-arc/1.0"

    def log_message(self, fmt, *args):
        pass

    @property
    def world(self) -> World:
        return self.server.world                                   # type: ignore[attr-defined]

    def _respond(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return self.headers.get("X-API-Key") == self.world.api_key

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/games":
            if not self._authorized():
                return self._respond(401, {"error": "missing or invalid X-API-Key"})
            return self._respond(200, [{"game_id": g, "title": g.split("-")[0]}
                                       for g in self.world.games])
        self._respond(404, {"error": "no such route", "path": path})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}

        if not self._authorized():
            # The whole sealing argument rests on this branch.
            return self._respond(401, {"error": "missing or invalid X-API-Key"})

        if path == "/api/scorecard/open":
            return self._respond(200, self.world.open_card(body))
        if path == "/api/scorecard/close":
            return self._respond(200, self.world.close_card(body.get("card_id", "")))
        if path == "/api/cmd/RESET":
            game_id = body.get("game_id")
            if game_id not in self.world.games:
                return self._respond(404, {"error": "unknown game_id", "game_id": game_id})
            return self._respond(200, self.world.reset(game_id, body.get("card_id")))
        if path.startswith("/api/cmd/ACTION"):
            try:
                action_id = int(path.rsplit("ACTION", 1)[1])
            except ValueError:
                return self._respond(404, {"error": "no such action", "path": path})
            status, payload = self.world.action(
                body.get("game_id"), body.get("guid"), action_id, body.get("data"))
            return self._respond(status, payload)
        self._respond(404, {"error": "no such route", "path": path})


class MockArc:
    def __init__(self, api_key: str = DEFAULT_KEY, games: Optional[List[str]] = None,
                 host: str = "127.0.0.1", port: int = 0):
        self.world = World(api_key=api_key, games=games)
        self.httpd = ThreadingHTTPServer((host, port), _Handler)
        self.httpd.world = self.world                              # type: ignore[attr-defined]
        self.httpd.daemon_threads = True
        self.host = host
        self._thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        return "http://%s:%d" % (self.host, self.httpd.server_address[1])

    def start(self) -> "MockArc":
        self._thread = threading.Thread(target=self.httpd.serve_forever,
                                        name="mock-arc", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self) -> "MockArc":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()
