"""一刀切堆 -- split the public set into a development pile and a sealed pile.

Theoria.md Phase 1 calls this non-negotiable and says to do it *before* any
iteration or trajectory mining: a game that has been touched is burnt, so the
knife has to fall first. This script is that knife, and it is deterministic and
pre-registered so that "we did not peek" is checkable later rather than
promised.

Method (fixed before looking at any game's mechanics):

  * Stratify by tag family, because the development pile has to be
    representative -- iterating the framework on `keyboard` games and then
    claiming it generalises to `click` games would be self-deception of the same
    kind the pile cut exists to prevent.
  * Development pile = 4 games: one `click`, one `keyboard`, two
    `keyboard_click` (the largest family). The lone untagged game stays sealed,
    so the sealed pile retains a family the development pile never shows us.
  * Within each stratum, ids are sorted lexicographically and drawn with a
    published seed through splitmix64 -- no cherry-picking, and anyone can
    re-run the draw.

What this run is allowed to know about a game: its id, title, tags and baseline
action counts. That is catalogue metadata, not mechanics, so listing the public
set does not contaminate it. The contamination register below records every game
as `never_audited` accordingly.
"""

import hashlib
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from common.rng import SplitMix64          # noqa: E402  published, deterministic

from client import DATA_DIR                # noqa: E402

GAMES_PATH = os.path.join(DATA_DIR, "games.json")
PILES_PATH = os.path.join(DATA_DIR, "piles.json")

SEED = 0x7EA17A                            # published; changing it invalidates the cut
DEV_QUOTA = {"click": 1, "keyboard": 1, "keyboard_click": 2}
SEALED_FAMILIES = ["<untagged>"]


def family_of(game: Dict[str, Any]) -> str:
    tags = game.get("tags") or []
    return "+".join(sorted(tags)) if tags else "<untagged>"


def stratify(games: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    strata: Dict[str, List[str]] = {}
    for game in games:
        strata.setdefault(family_of(game), []).append(game["game_id"])
    return {family: sorted(ids) for family, ids in sorted(strata.items())}


def draw(strata: Dict[str, List[str]], quota: Dict[str, int], seed: int) -> List[str]:
    """Seeded draw without replacement, in a fixed family order."""
    rng = SplitMix64(seed)
    picked: List[str] = []
    for family in sorted(quota):
        pool = list(strata.get(family, []))
        for _ in range(quota[family]):
            if not pool:
                raise RuntimeError("family %r cannot fill its quota" % family)
            picked.append(pool.pop(rng.below(len(pool))))
    return sorted(picked)


def build(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    strata = stratify(games)
    dev = draw(strata, DEV_QUOTA, SEED)
    all_ids = sorted(game["game_id"] for game in games)
    sealed = [game_id for game_id in all_ids if game_id not in dev]

    piles = {
        "cut_version": "v1",
        "n_public": len(all_ids),
        "seed": SEED,
        "method": (
            "stratified by tag family; quota %s; the untagged singleton stays "
            "sealed; within a family, ids sorted lexicographically and drawn with "
            "splitmix64(seed)" % json.dumps(DEV_QUOTA, sort_keys=True)
        ),
        "strata": strata,
        "dev_pile": dev,
        "sealed_pile": sealed,
        "sealed_only_families": SEALED_FAMILIES,
        # Theoria.md's three contamination levels. Everything starts clean: this
        # cut was made from catalogue metadata alone.
        "contamination_register": {
            game_id: "never_audited" for game_id in all_ids
        },
        "contamination_levels": [
            "never_audited",
            "scores_only",
            "trajectories_reviewed",
        ],
        "rules": [
            "The sealed pile is not played, inspected, or read about until the "
            "development-pile work is frozen.",
            "This includes upstream released artifacts belonging to sealed games "
            "-- reading those teaches the mechanics just as well as playing.",
            "Any change to this file after a game has been played invalidates the "
            "cut and must be recorded as an incident.",
        ],
    }
    return piles


def canonical(piles: Dict[str, Any]) -> str:
    return json.dumps(piles, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(piles: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical(piles).encode("utf-8")).hexdigest()


def main() -> int:
    if not os.path.exists(GAMES_PATH):
        print("run recon.py first -- %s is missing" % GAMES_PATH)
        return 2
    with open(GAMES_PATH, encoding="utf-8") as fh:
        games = json.load(fh)

    if os.path.exists(PILES_PATH):
        with open(PILES_PATH, encoding="utf-8") as fh:
            existing = json.load(fh)
        print("piles.json already exists (sha256 %s)." % existing.get("sha256", "?"))
        print("Refusing to re-cut: a cut that moves after play has begun is an incident.")
        return 2

    piles = build(games)
    piles["sha256"] = digest(piles)
    with open(PILES_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(piles, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("pile cut v1 -- %d public games" % piles["n_public"])
    print("  strata: %s" % {k: len(v) for k, v in piles["strata"].items()})
    print("  development pile (%d):" % len(piles["dev_pile"]))
    for game_id in piles["dev_pile"]:
        game = next(g for g in games if g["game_id"] == game_id)
        print("      %-18s %-6s %s" % (game_id, game["title"], family_of(game)))
    print("  sealed pile: %d games -- untouched from here on" % len(piles["sealed_pile"]))
    print("  sha256: %s" % piles["sha256"])
    print("  -> %s" % PILES_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
