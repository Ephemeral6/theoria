"""The sealed-pile guard, enforced at the proxy layer.

The pile cut is binding on both tracks, and until now it has been binding as
*discipline*: every caller was expected to check. Here it becomes a property of
the construction. An arm's only route to the environment is the environment
proxy, and the proxy refuses a sealed game before the upstream socket is
opened. An arm cannot reach a sealed game by writing different code, because it
has no credential with which to go anywhere else.

The data source is `arc-recon/data/piles.json` -- the cut itself, not a copy.
Its integrity is checked on load against the `sha256` the cut recorded, so a
silently edited cut fails closed rather than widening what is reachable.
"""

import hashlib
import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .paths import PILES, REPO

#: Requests whose path matches none of these carry no game id and are judged on
#: the body/query alone.
_GAME_IN_PATH = re.compile(r"/(?:games?|game)/([A-Za-z0-9]{2,6}-[0-9a-f]{8})")
_GAME_ID = re.compile(r"\b([A-Za-z0-9]{2,6}-[0-9a-f]{8})\b")


class SealedGameError(RuntimeError):
    """Raised before any network call that would touch the sealed pile."""


class PilesIntegrityError(RuntimeError):
    """The cut file does not hash to the digest it carries."""


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_piles(path: str = PILES, verify: bool = True) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        piles = json.load(fh)
    if verify:
        recorded = piles.get("sha256")
        body = {k: v for k, v in piles.items() if k != "sha256"}
        actual = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        if recorded != actual:
            raise PilesIntegrityError(
                "%s hashes to %s but records %s. The cut has been edited; "
                "changing it after play has begun is an incident "
                "(piles.json rule 3)." % (path, actual, recorded)
            )
    return piles


def stem(game_id: str) -> str:
    """`ar25-0c556536` -> `ar25`. Callers sometimes pass a bare id without the
    version suffix, and a bare id must be caught by the same rule as a full
    one."""
    return game_id.split("-", 1)[0].lower()


class SealedPileGuard:
    """Decides, for a request, whether it may leave the proxy.

    `unknown` policy is `deny` by default: the cut covers the 25 public games
    and an id outside the register is not something Phase 1 authorised. A
    caller who genuinely needs a new game changes the cut, which is a recorded
    act, rather than discovering that the guard shrugged.
    """

    def __init__(self, piles_path: str = PILES, verify: bool = True,
                 allow_only: Optional[Iterable[str]] = None,
                 unknown_policy: str = "deny"):
        if unknown_policy not in ("deny", "allow"):
            raise ValueError("unknown_policy must be 'deny' or 'allow'")
        self.piles_path = piles_path
        self.piles = load_piles(piles_path, verify=verify)
        self.piles_sha256 = self.piles.get("sha256")
        self.cut_version = self.piles.get("cut_version")
        self.unknown_policy = unknown_policy

        self.sealed: Set[str] = set(self.piles.get("sealed_pile", []))
        self.dev: Set[str] = set(self.piles.get("dev_pile", []))
        self._sealed_stems = {stem(g) for g in self.sealed}
        self._dev_stems = {stem(g) for g in self.dev}

        #: An optional further narrowing, e.g. a single game for one run.
        self.allow_only: Optional[Set[str]] = (
            {stem(g) for g in allow_only} if allow_only is not None else None
        )

    # -- classification ----------------------------------------------------
    def classify(self, game_id: str) -> str:
        s = stem(game_id)
        if s in self._sealed_stems:
            return "sealed"
        if s in self._dev_stems:
            return "dev"
        return "unknown"

    def verdict(self, game_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """(allowed, rule, reason)."""
        kind = self.classify(game_id)
        if kind == "sealed":
            return False, "sealed_pile", (
                "%s is in the sealed pile of %d (piles.json cut %s). Reaching it "
                "-- even for one frame -- teaches its mechanics and poisons the "
                "future exam on that game."
                % (game_id, len(self.sealed), self.cut_version)
            )
        if kind == "unknown" and self.unknown_policy == "deny":
            return False, "unknown_game", (
                "%s is in neither pile of cut %s. The guard fails closed: widen "
                "the cut deliberately rather than by accident."
                % (game_id, self.cut_version)
            )
        if self.allow_only is not None and stem(game_id) not in self.allow_only:
            return False, "not_in_run_allowlist", (
                "%s is outside this run's allowlist %s"
                % (game_id, sorted(self.allow_only))
            )
        return True, None, None

    def assert_playable(self, game_id: str) -> None:
        allowed, rule, reason = self.verdict(game_id)
        if not allowed:
            raise SealedGameError("[%s] %s" % (rule, reason))

    # -- request inspection ------------------------------------------------
    def game_ids_in(self, path: str, query: str, body: Any) -> List[str]:
        """Every game id a request mentions, wherever it hides.

        The guard reads the whole request, not just the field it expects. A
        sealed id smuggled into a click payload is still a sealed id, and a
        guard that only looked at `body["game_id"]` would be a guard by
        convention again.
        """
        found: List[str] = []

        def note(value: Any) -> None:
            if isinstance(value, str):
                for match in _GAME_ID.findall(value):
                    if match not in found:
                        found.append(match)

        for match in _GAME_IN_PATH.findall(path or ""):
            if match not in found:
                found.append(match)
        note(query or "")

        stack = [body]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, (list, tuple)):
                stack.extend(node)
            else:
                note(node)
        return found

    def check_request(self, path: str, query: str, body: Any) -> Dict[str, Any]:
        """The decision the proxy acts on.

        A request naming no game is allowed: `GET /api/games` and scorecard
        open/close carry no game and must work, and they cannot leak a sealed
        game's mechanics.
        """
        ids = self.game_ids_in(path, query, body)
        for game_id in ids:
            allowed, rule, reason = self.verdict(game_id)
            if not allowed:
                return {"decision": "deny", "rule": rule, "reason": reason,
                        "game_id": game_id, "game_ids_seen": ids,
                        "cut_sha256": self.piles_sha256}
        return {"decision": "allow", "game_ids_seen": ids}

    def fingerprint(self) -> Dict[str, Any]:
        """Goes into `run_start`, so a run records which cut it ran under."""
        try:
            where = os.path.relpath(self.piles_path, REPO).replace(os.sep, "/")
        except ValueError:                               # a different drive
            where = self.piles_path
        return {
            "piles_path": where,
            "cut_version": self.cut_version,
            "sha256": self.piles_sha256,
            "n_sealed": len(self.sealed),
            "n_dev": len(self.dev),
            "unknown_policy": self.unknown_policy,
            "allow_only": sorted(self.allow_only) if self.allow_only else None,
        }
