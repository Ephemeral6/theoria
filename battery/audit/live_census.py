"""The live archive's census -- what the battery sees, and what it does not.

`battery/audit/live_arm.py` and `battery/audit/live_economy.py` both read the
live arm through `battery.adapters.theoria_live.collect`, which returns two
lists: the legs it loaded, and the legs it *refused with a reason*.  Both
companions publish both lists, and `verify.py`'s rungs 7 and 8 gate them
against an in-process recompute, so a leg that lands in the archive without
the readings being regenerated turns the territory red.

**That gate is complete only for legs the adapter's `discover` hands to
`load_leg`.**  `discover` filters by content before anything is loaded: the
ledger's own `run_start` must declare `arm: "theoria"` *and* a
`spend_gate.campaign` starting with `theoria-arm:A3-campaign`.  A leg archive
that fails the campaign test is not refused -- it is never seen.  It appears
in no `runs` map, in no `excluded` list, in no rung's count, and no recompute
can turn red over it, because the recompute agrees: neither walk ever looked
at it.

Measured on this tree (2026-08-04, master 4846e66d): fourteen directories
under `theoria-arm/runs/` carry a `ledger.jsonl` whose `run_start` declares
`arm: "theoria"` and an `env_upstream` of `https://three.arcprize.org` -- real
live legs on the real environment -- and are invisible to every live
companion, because they predate the A3 campaign's spend gate and so declare no
campaign at all.  Eight of them recorded env steps; between them they bill 42
model calls and 23.86 USD of real spend.  The two companions read 14 legs; the
archive holds 28 live-arm ledgers.

**This module is the census that makes that difference visible.**  It walks
the archive itself -- every directory, not a filtered subset -- and gives each
`ledger.jsonl` a named disposition:

* `scored`    -- the adapter loaded it and a companion carries its metrics;
* `excluded`  -- the adapter refused it, and the refusal's own reason is
                 carried through verbatim (mock upstream, zero steps, ...);
* `invisible` -- the ledger declares this arm but `discover`'s campaign test
                 drops it before `load_leg`, so no companion and no rung has
                 ever seen it;
* `foreign`   -- the ledger declares a different arm; not this territory's;
* `unreadable`-- there is a `ledger.jsonl` but its first record is not a
                 `run_start`, so nothing can be concluded from it.

Two things follow that are worth stating separately from the count.

**The pile guard sits downstream of the campaign filter.**
`load_leg` calls `piles.assert_playable(game_id)` -- default deny, raises on a
sealed or unknown id -- but `discover` decides what reaches `load_leg`.  A leg
archived without the campaign label therefore never meets the guard.  On this
tree all fourteen invisible legs name development-pile games, so nothing was
crossed; that is a fact about the material, not a property of the code.  This
census runs the same guard on **every** ledger-bearing directory it finds, so
the sealed-pile line is checked over the whole archive rather than over the
adapter's filtered view of it.

**A census is not a promotion.**  Nothing here loads an invisible leg as a
`Run`, evaluates a metric on it, or moves it into a companion.  Whether those
legs *should* be scored is a question about the arm's campaign labelling and
belongs to `theoria-arm`, not to a measurement territory: the pre-A3 legs ran
before the spend gate existed, and folding them into a reading that
`BATTERY_V1.md` describes as "the A3 campaign's legs" would silently redefine
what the published numbers cover.  So the census reports the difference and
names the owner; it does not close it by itself.

The second half of the artefact answers the economy question the same way.
`E2` (front-load index) and `E3` (convergence point) both decline under
`battery/metrics/economy.py`'s `MIN_TURNS_FOR_SHAPE = 8`: a bill shape needs at
least eight decision turns.  The census records, per scored leg, the decision
turns on the archive's exact axis, and how many legs clear the floor -- so the
question "do more legs give the bill shape more to say?" is answered from a
table instead of from an impression.

The artefact is byte-reproducible for a fixed tree (no timestamp, no absolute
path, sorted keys) and pins the sha256 of every ledger it read, so
`battery/verify.py`'s census rung turns red the moment the archive moves and
the census does not follow -- the same staleness contract rungs 6, 7 and 8
carry.

    python -m battery.audit.live_census            # writes the tracked default
    python -m battery.audit.live_census --out P    # anywhere except artifacts/
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))          # battery/audit
BATTERY = os.path.dirname(HERE)                            # battery
REPO = os.path.dirname(BATTERY)

#: The tracked default output. `battery/freeze.py` lists it under READINGS.
DEFAULT_OUT = os.path.join(BATTERY, "artifacts_live", "live_census.json")


def _sha256(path: str) -> str:
    """LF-normalised digest, `battery.freeze`'s own hash -- one definition."""
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.freeze import sha256_file
    return sha256_file(path)


def _rows(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    return out
    return out


def _billed(rows: List[Dict[str, Any]]) -> Tuple[int, Optional[float]]:
    """Billed call count and USD, summed exactly as the adapter sums them.

    `None` for the money when no call carried a price: an unpriced ledger is
    an absence, and a 0.0 in a spend column reads as "free".
    """
    calls = [r for r in rows if r.get("event") == "model_call"]
    total = 0.0
    priced = False
    for row in calls:
        usage = ((row.get("response") or {}).get("modelUsage")) or {}
        for entry in usage.values():
            if entry.get("costUSD") is not None:
                total += float(entry["costUSD"])
                priced = True
    return len(calls), (round(total, 9) if priced else None)


def _upstream_host(value: Any) -> Optional[str]:
    """Scheme and host of `env_upstream`, no path, no query.

    Enough to tell a live upstream from a local mock -- which is the only
    thing this census reads it for -- and nothing more.
    """
    text = str(value or "")
    if not text:
        return None
    if "//" not in text:
        return text.split("/", 1)[0] or None
    scheme, rest = text.split("//", 1)
    return "%s//%s" % (scheme, rest.split("/", 1)[0])


def build(runs_root: Optional[str] = None) -> Dict[str, Any]:
    """The census, recomputed in-process from the archive and the adapter.

    Everything is derived: the scored set from the same `collect` the
    companions call, the exclusions with the adapter's own reasons, the
    invisible set from a walk of the archive that no filter narrows.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.adapters import theoria_live as adapter
    from battery.audit.live_economy import exact_axis
    from battery.guard import load_piles
    from battery.metrics.economy import MIN_TURNS_FOR_SHAPE

    root = runs_root or adapter.LIVE_ROOT
    piles = load_piles()               # raises if the cut has drifted

    runs, excluded = adapter.collect(root, piles=piles)
    scored = {run.notes.get("slug") or run.run_id: run for run in runs}
    refused = {row["slug"]: row.get("reason") or "?" for row in excluded}

    dirs = sorted(n for n in (os.listdir(root) if os.path.isdir(root) else [])
                  if os.path.isdir(os.path.join(root, n)))

    dispositions: Dict[str, Any] = {}
    inputs: Dict[str, str] = {}
    n_with_ledger = 0

    for slug in dirs:
        ledger_path = os.path.join(root, slug, "ledger.jsonl")
        if not os.path.exists(ledger_path):
            continue
        n_with_ledger += 1
        inputs[slug] = _sha256(ledger_path)
        rows = _rows(ledger_path)
        start = rows[0] if rows and rows[0].get("event") == "run_start" else None

        if start is None:
            dispositions[slug] = {
                "disposition": "unreadable",
                "reason": ("ledger.jsonl does not open with a run_start "
                           "record, so nothing can be concluded from it"),
            }
            continue

        arm = start.get("arm")
        campaign = (start.get("spend_gate") or {}).get("campaign")
        game_id = start.get("game_id")
        env_steps = sum(1 for r in rows if r.get("event") == "env_step")
        n_calls, usd = _billed(rows)

        row: Dict[str, Any] = {
            "arm": arm,
            "campaign": campaign,
            "game_id": game_id,
            "env_upstream": _upstream_host(start.get("env_upstream")),
            "env_steps": env_steps,
            "model_calls": n_calls,
            "billed_usd": usd,
        }

        if arm != adapter.ARM:
            row["disposition"] = "foreign"
            row["reason"] = ("the ledger declares arm %r, not %r -- another "
                             "territory's material" % (arm, adapter.ARM))
            row["pile"] = None
            dispositions[slug] = row
            continue

        # Default deny over the WHOLE archive, not over the adapter's filtered
        # view of it: this is the guard `discover` can skip past.  Raises on a
        # sealed or unknown id, exactly as `load_leg` would have.
        row["pile"] = piles.assert_playable(game_id)

        if slug in scored:
            row["disposition"] = "scored"
            row["reason"] = None
        elif slug in refused:
            row["disposition"] = "excluded"
            row["reason"] = refused[slug]
        else:
            row["disposition"] = "invisible"
            row["reason"] = (
                "the ledger declares arm 'theoria' but its spend_gate "
                "campaign is %r, which does not start with %r, so "
                "theoria_live.discover drops it before load_leg. It is in no "
                "companion's runs map and in no companion's excluded list: "
                "not refused, never seen." % (campaign, adapter.CAMPAIGN_PREFIX))
        dispositions[slug] = row

    invisible = sorted(s for s, r in dispositions.items()
                       if r["disposition"] == "invisible")
    live_invisible = [s for s in invisible
                      if (dispositions[s].get("env_upstream") or "")
                      .startswith("https://")]
    unseen_steps = sum(dispositions[s]["env_steps"] for s in invisible)
    unseen_calls = sum(dispositions[s]["model_calls"] for s in invisible)
    unseen_priced = [dispositions[s]["billed_usd"] for s in invisible
                     if dispositions[s]["billed_usd"] is not None]

    # ---- the shape floor: what the economy family can and cannot say.
    per_leg: Dict[str, Any] = {}
    clearing: List[str] = []
    for slug, run in sorted(scored.items()):
        axis, _summary = exact_axis(run, os.path.join(root, slug))
        turns = None
        reason = None
        if isinstance(_summary, dict):
            turns = _summary.get("decision_turns")
            reason = _summary.get("reason")
        per_leg[slug] = {
            "decision_turns": turns,
            "billed_calls": _summary.get("billed_calls")
            if isinstance(_summary, dict) else None,
            "axis": _summary.get("axis") if isinstance(_summary, dict) else None,
            "reason": reason,
            "clears_floor": bool(turns is not None
                                 and turns >= MIN_TURNS_FOR_SHAPE),
        }
        if per_leg[slug]["clears_floor"]:
            clearing.append(slug)

    return {
        "what": ("a census of theoria-arm/runs/: every directory that carries "
                 "a ledger.jsonl, with the disposition the battery gives it "
                 "-- scored, excluded-with-a-reason, invisible (dropped by "
                 "theoria_live.discover's campaign test before load_leg and "
                 "so absent from every companion and every rung), foreign, or "
                 "unreadable. Plus the decision-turn count per scored leg "
                 "against MIN_TURNS_FOR_SHAPE, which is what gates E2/E3. No "
                 "timestamp on purpose: for a fixed tree this file is "
                 "byte-reproducible."),
        "constraint": ("a census, not a promotion. Nothing here loads an "
                       "invisible leg as a Run, evaluates a metric on it, or "
                       "moves it into a companion; no tier moves and no "
                       "prediction is scored. Whether the pre-campaign legs "
                       "belong in the readings is a question about the arm's "
                       "campaign labelling and belongs to theoria-arm. This "
                       "file reports the difference and names the owner."),
        "runs_root": "theoria-arm/runs",
        "campaign_prefix": adapter.CAMPAIGN_PREFIX,
        "n_dirs": len(dirs),
        "n_with_ledger": n_with_ledger,
        "counts": {
            "scored": sum(1 for r in dispositions.values()
                          if r["disposition"] == "scored"),
            "excluded": sum(1 for r in dispositions.values()
                            if r["disposition"] == "excluded"),
            "invisible": len(invisible),
            "foreign": sum(1 for r in dispositions.values()
                           if r["disposition"] == "foreign"),
            "unreadable": sum(1 for r in dispositions.values()
                              if r["disposition"] == "unreadable"),
        },
        "dispositions": dispositions,
        "invisible": {
            "slugs": invisible,
            "on_live_upstream": sorted(live_invisible),
            "with_env_steps": sorted(
                s for s in invisible if dispositions[s]["env_steps"] > 0),
            "env_steps": unseen_steps,
            "model_calls": unseen_calls,
            "billed_usd": (round(sum(unseen_priced), 9)
                           if unseen_priced else None),
            "unpriced_legs": sorted(
                s for s in invisible
                if dispositions[s]["billed_usd"] is None),
            "note": ("env_steps, model_calls and billed_usd are summed over "
                     "the invisible legs only: this is live-arm material the "
                     "battery's companions do not read and no rung can turn "
                     "red over. billed_usd is null, never 0.0, when no "
                     "invisible leg carried a price -- absence, not zero."),
        },
        "shape_floor": {
            "min_turns_for_shape": MIN_TURNS_FOR_SHAPE,
            "per_leg": per_leg,
            "n_scored": len(per_leg),
            "n_clearing": len(clearing),
            "clearing": sorted(clearing),
            "note": ("E2 and E3 are the two economy metrics that read the "
                     "bill's shape, and both decline below "
                     "MIN_TURNS_FOR_SHAPE decision turns. The floor is "
                     "per-leg: it is cleared by a long leg, never by more "
                     "legs. Read n_clearing beside n_scored before reading "
                     "any sentence about what the bill shape shows."),
        },
        "inputs": inputs,
    }


def serialise(doc: Dict[str, Any]) -> str:
    """Canonical bytes: sorted keys, two-space indent, LF, trailing newline."""
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(out_path: str = DEFAULT_OUT,
          runs_root: Optional[str] = None) -> str:
    """Build and write. Refuses the frozen directory before touching anything.

    The refusal is `live_tiers.refuse_frozen_destination`, imported: one
    definition of "inside the frozen directory", not two.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.audit.live_tiers import refuse_frozen_destination
    resolved = refuse_frozen_destination(out_path)
    doc = build(runs_root)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialise(doc))
    return resolved


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="write the live-archive census companion artefact")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="destination (default: %(default)s); anything "
                             "resolving inside battery/artifacts/ is refused")
    args = parser.parse_args(argv)
    try:
        path = write(args.out)
    except ValueError as exc:
        print("REFUSED: %s" % exc)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
