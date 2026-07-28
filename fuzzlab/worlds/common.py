"""Shared world plumbing: canonical serialisation and fingerprints."""

import hashlib
import json
from typing import Any, Dict


def canonical(value: Any) -> str:
    """Sorted-key, no-whitespace JSON -- the byte form a fingerprint is taken over."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class World:
    """Base class: a world is its spec plus whatever the engines consume.

    Subclasses fill `family` and implement `spec_json()`.  `fingerprint()` is
    taken over the *spec*, not the rendered world, so a generator change that
    silently alters rendering from the same parameters shows up as a property
    failure rather than as a fingerprint mismatch that hides it.
    """

    family = "world"

    def spec_json(self) -> Dict[str, Any]:                # pragma: no cover
        raise NotImplementedError

    @property
    def seed(self) -> int:                                # pragma: no cover
        raise NotImplementedError

    def fingerprint(self) -> str:
        return fingerprint({"family": self.family, "spec": self.spec_json()})

    def row(self) -> Dict[str, Any]:
        """One line of the seed table."""
        return {
            "family": self.family,
            "seed": self.seed,
            "fingerprint": self.fingerprint(),
            "spec": self.spec_json(),
        }
