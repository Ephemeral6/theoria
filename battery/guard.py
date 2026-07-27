"""Sealed-pile guardrail for the metrics battery.

The battery is a passive instrument: it reads ledgers and never touches the
network.  That makes it *cheap* to run over anything, which is exactly why it
needs a guardrail — a metric recomputed over a sealed game teaches us that
game's mechanics just as effectively as playing it, and the pile cut
(`CLAUDE.md`, `Theoria.md` Phase 1) is binding on every track.

Two checks live here.

**The cut is intact.**  `arc-recon/data/piles.json` carries its own `sha256`
field, computed over the canonical JSON of the payload with that field removed:

    sha256(json.dumps({k: v for k, v in doc.items() if k != "sha256"},
                      sort_keys=True, separators=(",", ":")))

`verify_cut()` recomputes it.  A mismatch means the split changed after
publication, which `piles.json`'s own rules call an incident — so it raises
rather than warns.  Every artefact the battery writes carries the digest it
verified against, so a reader can tell which cut a number was computed under.

**Sealed games are refused.**  `assert_playable()` rejects any sealed id.
Matching is deliberately loose in the directions that let something through:

* full id            — `bp35-0a0ad940`
* short id           — `bp35`, because the live API accepts the de-suffixed
  form (baseline-arms established this), so a guard keyed only to full ids is
  a sieve;
* case and surrounding whitespace are normalised.

Matching is *strict* in the direction that would let something through by
accident: an id that resolves to no pile at all is refused too.  An unknown id
is not evidence of safety, and a battery that silently scored an unregistered
game would be producing numbers nobody can audit.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PILES_PATH = os.path.join(REPO, "arc-recon", "data", "piles.json")


class SealedPileError(RuntimeError):
    """Raised when the battery is pointed at a sealed game."""


class CutIntegrityError(RuntimeError):
    """Raised when piles.json does not hash to its own recorded digest."""


class UnknownGameError(RuntimeError):
    """Raised for an id that belongs to neither pile."""


def _short(game_id: str) -> str:
    """`bp35-0a0ad940` -> `bp35`.  The API accepts both, so the guard must."""
    return game_id.split("-", 1)[0]


def _norm(game_id: str) -> str:
    return game_id.strip().lower()


def canonical_digest(doc: Dict[str, Any]) -> str:
    """The digest `piles.json` publishes about itself."""
    payload = {k: v for k, v in doc.items() if k != "sha256"}
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class Piles:
    """The pile cut, loaded and verified.

    Construct once and pass it down; every call site then shares one verified
    view of the cut, and the digest that view was verified against travels into
    the artefacts alongside the numbers.
    """

    def __init__(self, doc: Dict[str, Any], *, verify: bool = True) -> None:
        self.doc = doc
        self.recorded_digest: Optional[str] = doc.get("sha256")
        self.computed_digest = canonical_digest(doc)
        if verify:
            self.verify()
        self.dev_pile: List[str] = list(doc.get("dev_pile", []))
        self.sealed_pile: List[str] = list(doc.get("sealed_pile", []))
        self._dev_keys = self._keys(self.dev_pile)
        self._sealed_keys = self._keys(self.sealed_pile)
        overlap = self._dev_keys & self._sealed_keys
        if overlap:
            raise CutIntegrityError(
                "a game resolves to both piles: %s" % sorted(overlap))

    @staticmethod
    def _keys(ids: Iterable[str]) -> set:
        keys = set()
        for gid in ids:
            keys.add(_norm(gid))
            keys.add(_norm(_short(gid)))
        return keys

    def verify(self) -> str:
        if self.recorded_digest is None:
            raise CutIntegrityError("piles.json carries no sha256 field")
        if self.recorded_digest != self.computed_digest:
            raise CutIntegrityError(
                "the pile cut has changed since it was published: "
                "recorded %s, computed %s. piles.json's own rules call this an "
                "incident; the battery will not score anything until it is "
                "resolved." % (self.recorded_digest, self.computed_digest))
        return self.computed_digest

    def classify(self, game_id: str) -> str:
        """`dev` / `sealed` / `unknown`."""
        key = _norm(game_id)
        short = _norm(_short(game_id))
        if key in self._sealed_keys or short in self._sealed_keys:
            return "sealed"
        if key in self._dev_keys or short in self._dev_keys:
            return "dev"
        return "unknown"

    def assert_playable(self, game_id: Optional[str]) -> str:
        """Refuse sealed and unknown ids.  Returns the verdict for dev ids.

        `None` is allowed and returns `"synthetic"`: the A0 worlds are
        self-built and belong to no pile, which is the whole point of them.
        """
        if game_id is None:
            return "synthetic"
        verdict = self.classify(game_id)
        if verdict == "sealed":
            raise SealedPileError(
                "%r is in the sealed pile. The battery does not read sealed-pile "
                "trajectories -- recomputing metrics over one teaches us the "
                "game's mechanics exactly as playing it would." % game_id)
        if verdict == "unknown":
            raise UnknownGameError(
                "%r is in neither pile of %s. Refusing: an unregistered game is "
                "not a safe game, it is an unaudited one." % (game_id, PILES_PATH))
        return verdict

    def provenance(self) -> Dict[str, Any]:
        """What every artefact records about the cut it was computed under."""
        return {
            "cut_version": self.doc.get("cut_version"),
            "dev_pile": sorted(self.dev_pile),
            "n_sealed": len(self.sealed_pile),
            "piles_sha256": self.computed_digest,
        }


def load_piles(path: str = PILES_PATH, *, verify: bool = True) -> Piles:
    with open(path, "r", encoding="utf-8") as fh:
        return Piles(json.load(fh), verify=verify)


def screen(game_ids: Iterable[Optional[str]],
           piles: Optional[Piles] = None) -> Tuple[List[str], List[str]]:
    """Screen a batch up front, so a long recompute fails on line one.

    Returns (accepted, verdicts) or raises on the first sealed/unknown id.
    """
    piles = piles or load_piles()
    accepted: List[str] = []
    verdicts: List[str] = []
    for gid in game_ids:
        verdicts.append(piles.assert_playable(gid))
        accepted.append(gid if gid is not None else "<synthetic>")
    return accepted, verdicts
