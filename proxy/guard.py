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

import base64
import binascii
import hashlib
import json
import os
import re
import unicodedata
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .paths import PILES, REPO

#: A full game id. Case-insensitive on **both** halves: the red team walked
#: `ls20-9607627B` straight through a `[0-9a-f]` character class (RED-21).
#:
#: Anchored on both sides against alphanumerics rather than on `\b`, because
#: `\b` treats `_` as a word character and this scan now looks at strings that
#: have been concatenated: `"game_id" + "ar25-0c556536"` must not read as an
#: id called `idar25-0c556536`. It also keeps a UUID from matching -- a
#: `card_id` or a `guid` is not a game.
_GAME_ID = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z0-9]{2,6})-([0-9A-Fa-f]{8})(?![A-Za-z0-9])")

#: The same shape, matched **overlapping and without the left anchor**, for use
#: on the concatenation of a body's values only.
#:
#: Two reasons it differs from `_GAME_ID`. First, the join has no word
#: boundaries to respect -- it is an artefact, not something a server will
#: read -- so anchoring on the left there only decides *which* of several
#: overlapping candidates is reported, and the leftmost is the wrong one:
#: in `"x_ab" + "ls20-9607627b"` a left-anchored scan returns `abls20-9607627b`
#: and, because `re.findall` does not overlap, the real `ls20-9607627b` is
#: consumed and never seen. Second, a zero-width lookahead yields every start
#: position, so every candidate stem is offered to the register instead of
#: just one.
#:
#: Everything this finds is then filtered against the registered stems -- see
#: `_ids_in_join`. That filter is what makes dropping the anchor safe.
_GAME_ID_JOINED = re.compile(
    r"(?=([A-Za-z0-9]{2,6})-([0-9A-Fa-f]{8})(?![A-Za-z0-9]))")

#: Any run of alphanumerics, used to catch a **bare stem**. `ls20` on its own
#: matched nothing before (RED-20), and a bare stem is not a typo: INC-005
#: recorded that the live API answers short ids with a fake 200, so a request
#: naming one is a request that reaches the game.
_TOKEN = re.compile(r"[A-Za-z0-9]+")

#: Characters that are invisible but change a match. Stripped before scanning.
_INVISIBLE = dict.fromkeys(
    [0x00AD, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF] + list(range(0x0000, 0x0009))
)

#: A base64-ish blob worth trying to decode once. Long enough that ordinary
#: words do not qualify.
_B64 = re.compile(r"[A-Za-z0-9+/=_-]{12,}")

#: The digest the cut published, pinned **here in code**.
#:
#: `load_piles` used to verify the file against a digest the file itself
#: carried, which certifies nothing: re-signing a doctored cut passes (RED-30).
#: A cut is a promise made once, so the promise lives outside the thing it
#: constrains. This value is also in `CLAUDE.md`, which is where a human would
#: go to check it.
EXPECTED_PILES_SHA256 = (
    "3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a"
)


class SealedGameError(RuntimeError):
    """Raised before any network call that would touch the sealed pile."""


class PilesIntegrityError(RuntimeError):
    """The cut file does not hash to the digest it carries."""


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_piles(path: str = PILES, verify: bool = True,
               expected: Optional[str] = EXPECTED_PILES_SHA256) -> Dict[str, Any]:
    """Load the cut, and check it against a digest it does not control.

    Two checks, and the second is the one that matters. The first — file
    against its own `sha256` field — catches an edit made without re-signing.
    The second — file against `EXPECTED_PILES_SHA256`, a constant in this
    module — catches an edit made *with* re-signing, which the first cannot,
    because a document that certifies itself certifies nothing.
    """
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
        if expected is not None and actual != expected:
            raise PilesIntegrityError(
                "%s hashes to %s; the pinned digest is %s. A re-signed cut "
                "passes its own integrity field, which is why the guard does "
                "not rely on it. Widening the cut after play has begun is an "
                "incident (piles.json rule 3), and it is recorded as one -- "
                "not accommodated by editing this constant."
                % (path, actual, expected)
            )
    return piles


def _b64_readings(blob: str) -> List[str]:
    """Decode a base64-ish blob, both alphabets, tolerating missing padding.

    One level only. An id hidden two encodings deep is still findable by an
    attacker who controls both ends, and chasing it forever costs more than it
    buys; one level covers the case the red team actually landed (RED-26).
    """
    out: List[str] = []
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        for padding in ("", "=", "=="):
            try:
                raw = decoder(blob + padding)
            except (binascii.Error, ValueError):
                continue
            try:
                out.append(raw.decode("utf-8"))
            except UnicodeDecodeError:
                out.append(raw.decode("latin-1", "replace"))
            break
    return out


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
                 unknown_policy: str = "deny",
                 expected_sha256: Optional[str] = EXPECTED_PILES_SHA256):
        if unknown_policy not in ("deny", "allow"):
            raise ValueError("unknown_policy must be 'deny' or 'allow'")
        self.piles_path = piles_path
        self.piles = load_piles(piles_path, verify=verify,
                                expected=expected_sha256)
        self.piles_sha256 = self.piles.get("sha256")
        self.cut_version = self.piles.get("cut_version")
        self.unknown_policy = unknown_policy

        self.sealed: Set[str] = set(self.piles.get("sealed_pile", []))
        self.dev: Set[str] = set(self.piles.get("dev_pile", []))
        self._sealed_stems = {stem(g) for g in self.sealed}
        self._dev_stems = {stem(g) for g in self.dev}
        #: Both piles' stems. A bare stem in a request is a game id -- the API
        #: answers short ids (INC-005) -- so the scan has to recognise one, and
        #: it can only do that against the register.
        self._all_stems = self._sealed_stems | self._dev_stems

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
    def _texts(self, path: str, query: str, body: Any, raw: Any,
               headers: Any) -> Tuple[List[str], Optional[str]]:
        """Every piece of text a request is made of, and the join, separately.

        The red team got a sealed id past the old scan six different ways, and
        five of them were the same mistake: the guard looked at the fields it
        expected. So this collects *everything* -- the path, the query, every
        header value and name, the raw bytes as text (which is the only thing
        left when the body will not parse), and every string in the parsed body
        including dictionary **keys**.

        The second return value is the concatenation of the body's values, in
        key order, which is what catches an id split across two fields --
        `{"a": "ls20-", "b": "9607627b"}` is one id to the server and was two
        harmless strings to the guard. The join is over **values only**:
        including the keys would interleave them between the halves and defeat
        the point. It is partial -- a different key order breaks it, and D-022
        says so -- but partial and closing beats open.

        It is returned apart from the real texts rather than appended to them
        because it is not text any server will read; it is a probe the guard
        manufactures, and ids found only in it have to be judged by a stricter
        rule. See `_ids_in_join`.
        """
        texts: List[str] = [path or "", query or ""]

        if isinstance(raw, (bytes, bytearray)):
            texts.append(bytes(raw).decode("utf-8", "replace"))
        elif isinstance(raw, str):
            texts.append(raw)

        if headers is not None:
            try:
                items = headers.items()
            except AttributeError:
                items = []
            for name, value in items:
                texts.append(str(name))
                texts.append(str(value))

        values: List[str] = []
        keys: List[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, value in sorted(node.items(), key=lambda kv: str(kv[0])):
                    keys.append(str(key))
                    walk(value)
            elif isinstance(node, (list, tuple)):
                for item in node:
                    walk(item)
            elif isinstance(node, str):
                values.append(node)
            elif node is not None and not isinstance(node, bool):
                values.append(str(node))

        walk(body)
        texts.extend(values)
        texts.extend(keys)
        return texts, ("".join(values) if len(values) > 1 else None)

    @staticmethod
    def _normalise(text: str) -> List[str]:
        """One string in, the several readings of it a server might see.

        Percent-encoding, full-width characters and zero-width joiners all
        change what the guard matches without changing what the upstream
        receives -- so the guard has to look at the decoded forms too, not
        instead.
        """
        readings = [text]

        decoded = text
        for _ in range(3):                   # bounded: %2525 is still a thing
            once = urllib.parse.unquote_plus(decoded)
            if once == decoded:
                break
            decoded = once
            readings.append(decoded)

        for reading in list(readings):
            folded = unicodedata.normalize("NFKC", reading).translate(_INVISIBLE)
            if folded != reading:
                readings.append(folded)

        return readings

    def _ids_in_text(self, text: str, depth: int = 0) -> List[str]:
        found: List[str] = []
        for reading in self._normalise(text):
            for stem_part, hex_part in _GAME_ID.findall(reading):
                candidate = "%s-%s" % (stem_part, hex_part)
                if candidate not in found:
                    found.append(candidate)
            for token in _TOKEN.findall(reading):
                if token.lower() in self._all_stems and token not in found:
                    found.append(token)
            if depth == 0:
                for blob in _B64.findall(reading):
                    for decoded in _b64_readings(blob):
                        for nested in self._ids_in_text(decoded, depth + 1):
                            if nested not in found:
                                found.append(nested)
        return found

    def _ids_in_join(self, text: str) -> List[str]:
        """Ids in the manufactured join -- registered stems only.

        The join is the guard's own construction, so anything found in it that
        is **not a game this cut knows about** is an artefact of the
        concatenation rather than something the request named. Reporting those
        denies real work for ids nobody sent: `{"arm": "bare_cc", "game_id":
        "ar25-0c556536"}` joins to `bare_ccar25-0c556536`, whose 6-character
        stem `ccar25` is in neither pile, so the request was refused as
        `unknown_game`. Any value ending in one or two alphanumerics does this;
        `bare_cc` is simply the one that is an arm's name.

        Filtering to the register is what makes it safe to drop `_GAME_ID`'s
        left anchor here, and dropping the anchor makes this scan strictly
        **stronger** than the one it replaces: with overlapping candidates,
        `{"a": "x_abls20-", "b": "9607627b"}` now yields `ls20-9607627b` and
        denies as `sealed_pile`. The anchored, non-overlapping scan returned
        only `abls20-9607627b` and, under `unknown_policy="allow"`, let the
        sealed id through.

        What is given up is `unknown_game` discovery for an id that is split
        across two fields *and* whose stem is in neither pile -- which is never
        a sealed game, since the sealed set is a fixed enumeration.
        """
        found: List[str] = []
        for reading in self._normalise(text):
            for stem_part, hex_part in _GAME_ID_JOINED.findall(reading):
                if stem_part.lower() not in self._all_stems:
                    continue
                candidate = "%s-%s" % (stem_part, hex_part)
                if candidate not in found:
                    found.append(candidate)
            for token in _TOKEN.findall(reading):
                if token.lower() in self._all_stems and token not in found:
                    found.append(token)
        return found

    def game_ids_in_text(self, text: Optional[str]) -> List[str]:
        """Every game id or registered stem a single piece of text mentions.

        The public form of `_ids_in_text`, for callers that have prose rather
        than a request -- specifically the arm's model desk, which has to keep
        game identifiers out of a *prompt* (`Theoria.md:353`'s 硬规) and had no
        scanner but a naive substring test against the one game it knew about.

        Reusing this scanner rather than writing a second one is the point.
        `s in prompt` over 25 stems is not a smaller version of this check, it
        is a different and wrong one: `sk48` would fire inside `task48`, `ar25`
        inside `similar25`, and a desk that refuses ordinary English is a desk
        that gets its guard switched off. What is here instead is token-bounded
        (`_TOKEN` against the register), sees percent-encoded, NFKC and
        zero-width-stripped readings, and follows one level of base64 -- all
        properties the red team paid for on the request path.

        It does **not** run the manufactured value-join: there are no fields to
        join in a prompt, and the join's ids are judged by a stricter rule that
        does not apply to prose.
        """
        return self._ids_in_text(text or "")

    def game_ids_in(self, path: str, query: str, body: Any,
                    raw: Any = None, headers: Any = None) -> List[str]:
        """Every game id a request mentions, wherever it hides."""
        found: List[str] = []
        texts, joined = self._texts(path, query, body, raw, headers)
        for text in texts:
            for game_id in self._ids_in_text(text):
                if game_id not in found:
                    found.append(game_id)
        if joined is not None:
            for game_id in self._ids_in_join(joined):
                if game_id not in found:
                    found.append(game_id)
        return found

    def check_request(self, path: str, query: str, body: Any,
                      raw: Any = None, headers: Any = None,
                      known_game: Optional[str] = None,
                      is_command: bool = False) -> Dict[str, Any]:
        """The decision the proxy acts on.

        A non-command request naming no game is allowed: `GET /api/games` and
        scorecard open/close carry no game and must work, and they cannot leak
        a sealed game's mechanics.

        A **command** naming no game is denied. A command is always about some
        game; if the request does not say which, and the session it names is
        not one this proxy opened, then the proxy cannot tell what it is about
        -- and a guard that cannot tell has to refuse (RED-29).
        """
        ids = self.game_ids_in(path, query, body, raw=raw, headers=headers)
        if known_game and known_game not in ids:
            ids = ids + [known_game]

        for game_id in ids:
            allowed, rule, reason = self.verdict(game_id)
            if not allowed:
                return {"decision": "deny", "rule": rule, "reason": reason,
                        "game_id": game_id, "game_ids_seen": ids,
                        "cut_sha256": self.piles_sha256}

        if is_command and not ids:
            return {"decision": "deny", "rule": "unattributable_command",
                    "reason": "this command names no game, and its session is "
                              "not one this proxy opened. The guard cannot "
                              "tell which game it is about, so it refuses: an "
                              "unattributable command is how a sealed game "
                              "gets played through a session opened elsewhere.",
                    "game_id": None, "game_ids_seen": ids,
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
