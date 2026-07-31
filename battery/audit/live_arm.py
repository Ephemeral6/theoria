"""The live arm's readings — measurement-only companion material.

`battery/artifacts/` was computed over five arms (`bare_cc`, `schema_repro`,
`theoria_a0`, `theoria_a0_spike`, `theoria_a2`) and is a **reading of record**
under the BATTERY_V1 freeze.  The live Theoria arm now has committed leg
archives (`theoria-arm/runs/`, A3 campaign), and this module points the frozen
instrument at them: every one of the 38 registered metrics is evaluated on
every live leg, through `battery.adapters.theoria_live`, and the result is a
tracked, byte-reproducible artefact under `battery/artifacts_live/`.

**Why this is a separate file and not a sixth arm in `run_battery.py` — the
constraint, per the pre-registration's own text:**

* `battery/PREDICTIONS.md` is frozen (BATTERY_V1 `freeze:prereg`, whole-file
  *and* prefix digest).  Its registered arm orderings name `theoria` — but a
  directional prediction can only be *settled*, never *added*, without a new
  freeze version: "a prediction registered after the instrument was frozen
  needs a new freeze version recording when it arrived" (BATTERY_V1 §3.1).
  Nothing here settles a prediction either: settlement is scoreboard work for
  a report, and a companion artefact that quietly scored the prereg would be
  publishing confirmation-shaped numbers out of a measurement file.
* `PREREG_V9.md` §5: 不修改任何已提交产物 — the frozen artefacts under
  `battery/artifacts/` are not rewritten, so the live arm cannot be folded
  into `capability_spectrum.json` and friends without a new freeze version.
* Process 1's gradient is CC vs Schema (`Theoria.md:325`, frozen in
  `audit/discriminate.py`'s `CONTROL_ARMS`).  The live arm is not a control
  arm; adding it to the discrimination machinery would change frozen code
  whose edit moves published numbers (`run_battery.py`, BATTERY_V1 §2.2) —
  the offence §8 names.  The `live_tiers` amendment of 2026-07-31 set the
  path this module follows instead: new module, new test, new
  `artifacts_live/` reading, freeze buckets extended, blocks re-rendered,
  dated amendment appended — and the only frozen files edited are the freeze
  machinery itself.

So: **these are readings, not confirmations.**  No tier moves, no prediction
is scored, no discrimination verdict changes.  What the file buys is that the
认识 (epistemic) and 经济 (economy) families finally read *real* live legs —
a manual certified against a live game's transitions, dollars actually spent
through the spend gate — instead of only offline bundles and controls.

The artefact is byte-reproducible for a fixed tree (no timestamp, no absolute
path, sorted keys) and pins the sha256 of every input file it read, so
`battery/verify.py`'s live-arm rung can turn red the moment the committed
companion stops matching an in-process recompute — the same staleness
contract `live_tiers` established.

    python -m battery.audit.live_arm            # writes the tracked default
    python -m battery.audit.live_arm --out P    # anywhere except artifacts/
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))          # battery/audit
BATTERY = os.path.dirname(HERE)                            # battery
REPO = os.path.dirname(BATTERY)

#: The tracked default output. `battery/freeze.py` lists it under READINGS.
DEFAULT_OUT = os.path.join(BATTERY, "artifacts_live", "live_arm_readings.json")

#: Files a leg archive may contribute; each one that exists is digested into
#: the artefact so staleness has a named cause.
_INPUT_FILES = ("ledger.jsonl", "turn_series.json", "curves.json",
                "turns.json", "surprises.jsonl", "certify.json",
                "probes.jsonl", "books/theory.dsl", "books/playbook.dsl")


def _sha256(path: str) -> str:
    """LF-normalised digest, `battery.freeze`'s own hash — one definition."""
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.freeze import sha256_file
    return sha256_file(path)


def build(runs_root: Optional[str] = None) -> Dict[str, Any]:
    """The live arm's spectrum, recomputed in-process.

    Everything is derived: the runs from the adapter, every value from the
    frozen metric registry's own `evaluate`, the input digests from the
    files.  Nothing is typed in, so this module cannot hold an opinion of its
    own about any number.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.adapters.theoria_live import LIVE_ROOT, collect
    from battery.guard import load_piles
    from battery.metrics import REGISTRY, evaluate

    root = runs_root or LIVE_ROOT
    piles = load_piles()               # raises if the cut has drifted
    runs, excluded = collect(root, piles=piles)

    values = {run.run_id: evaluate(run) for run in runs}

    run_rows: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}
    for run in runs:
        run_rows[run.run_id] = {
            "arm": run.arm,
            "source": run.source,
            "campaign": run.campaign,
            "model": run.model,
            "game_id": run.game_id,
            "pile": run.pile,
            "intent": run.intent,
            "steps": len(run.steps),
            "failed_steps": sum(1 for s in run.steps if s.failed),
            "model_calls": len(run.calls),
            "turns": len(run.turn_costs()) or None,
            "notes": run.notes,
            "metrics": {mid: value.as_dict()
                        for mid, value in sorted(values[run.run_id].items())},
        }
        leg_dir = os.path.join(root, run.run_id)
        digests = {}
        for rel in _INPUT_FILES:
            path = os.path.join(leg_dir, rel.replace("/", os.sep))
            if os.path.exists(path):
                digests[rel] = _sha256(path)
        inputs[run.run_id] = digests

    # Per-family, per-metric rollup: which metrics carry at least one real
    # live reading.  This is the sentence the artefact exists to support.
    families: Dict[str, Dict[str, Any]] = {}
    for metric_id in sorted(REGISTRY):
        card = REGISTRY[metric_id]
        statuses: Dict[str, int] = {}
        measured: Dict[str, Any] = {}
        for run_id in sorted(values):
            value = values[run_id][metric_id]
            statuses[value.status] = statuses.get(value.status, 0) + 1
            if value.ok:
                measured[run_id] = value.value
        families.setdefault(card.family, {})[metric_id] = {
            "direction": card.direction,
            "by_status": dict(sorted(statuses.items())),
            "measured": measured,
        }

    measured_by_family = {
        family: sorted(m for m, row in metrics.items() if row["measured"])
        for family, metrics in sorted(families.items())
    }

    return {
        "what": ("every registered battery metric evaluated on the live "
                 "Theoria arm's committed leg archives (theoria-arm/runs/, "
                 "A3 campaign), via battery.adapters.theoria_live. "
                 "Measurement-only companion material: PREDICTIONS.md is "
                 "frozen append-only under BATTERY_V1 freeze:prereg, "
                 "PREREG_V9 §5 forbids rewriting the committed "
                 "artefacts, and process 1's gradient (CC vs Schema) does "
                 "not include this arm -- so nothing here settles a "
                 "prediction, moves a tier, or enters a discrimination "
                 "verdict. No timestamp on purpose: for a fixed tree this "
                 "file is byte-reproducible."),
        "constraint": ("readings, not confirmations. The frozen instrument "
                       "(metric bodies, adapters' shared parsers, registry) "
                       "is applied unchanged; the frozen artefacts under "
                       "battery/artifacts/ are untouched; the live arm "
                       "enters no frozen comparison. Folding it into "
                       "run_battery.py's arm set or scoring it against the "
                       "pre-registered orderings requires a new freeze "
                       "version (BATTERY_V1.md §8)."),
        "arm": "theoria",
        "source": "theoria-arm-live",
        "runs_root": "theoria-arm/runs",
        "n_runs": len(runs),
        "n_games": len({r.game_id for r in runs if r.game_id}),
        "games": sorted({r.game_id for r in runs if r.game_id}),
        "piles": sorted({r.pile for r in runs}),
        "excluded": excluded,
        "inputs": inputs,
        "runs": run_rows,
        "families": families,
        "measured_by_family": measured_by_family,
        "n_measured_cells": sum(
            1 for run_id in values for v in values[run_id].values() if v.ok),
    }


def serialise(doc: Dict[str, Any]) -> str:
    """Canonical bytes: sorted keys, two-space indent, LF, trailing newline."""
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(out_path: str = DEFAULT_OUT,
          runs_root: Optional[str] = None) -> str:
    """Build and write.  Refuses the frozen directory before touching anything.

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
        description="write the live-arm readings companion artefact")
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
