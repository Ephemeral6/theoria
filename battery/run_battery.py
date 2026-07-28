"""Recompute the whole capability spectrum from the ledgers on disk.

    python -m battery.run_battery [--out DIR]

Passive by construction: it opens files, and nothing else. No API calls, no
model calls, no network. Everything it reads already exists.

Determinism is a requirement here, not a nicety. Two runs over unchanged
inputs produce byte-identical artefacts, which is what makes a recompute
auditable: a reviewer re-runs it and diffs. That rules out timestamps in the
output (the artefacts carry input digests instead), unordered iteration, and
any float that could differ in its last bit between machines -- which is why
`audit/stats.py` is hand-rolled rather than scipy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from battery.adapters import (
    load_a0_runs, load_a0_spike_runs, load_ledger_runs,
)
from battery.adapters.a2 import load_a2_runs
from battery.audit import discriminate
from battery.audit.contrast import contrast
from battery.audit.discriminate import power_note
from battery.audit.gaming import audit as gaming_audit
from battery.audit.gaming import tier_of
from battery.audit.redundancy import cluster
from battery.audit.validation import material
from battery.guard import Piles, load_piles
from battery.metrics import REGISTRY, Value, evaluate
from battery.model import Run

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(HERE, "artifacts")
A0_ROOT = os.path.join(REPO, "cold-start-a0")

# Offline theory-bearing bundles, each with its own adapter.  They are kept
# separate rather than merged into one "theoria" arm because they differ in the
# only respect the repair metrics care about: A2 patches a located clause,
# a0-spike re-mines the world.  Collapsing them would average a patch and a
# rebuild into a number describing neither.
BUNDLES = [
    ("cold-start-a0", A0_ROOT, load_a0_runs),
    ("a0-spike", os.path.join(REPO, "a0-spike"), load_a0_spike_runs),
    ("cold-start-a2", os.path.join(REPO, "cold-start-a2"), load_a2_runs),
]

SOURCES = [
    ("baseline-arms ledger", os.path.join(REPO, "baseline-arms", "ledger.jsonl")),
]

# Read, and deliberately not read.  `baseline-arms/out/shards/` holds a third
# campaign that another session is writing right now -- untracked, several
# megabytes, and growing between one recompute and the next.  Ingesting it
# would make the artefacts non-reproducible and would fold an unmerged
# in-flight campaign into a published number.  It is named here so that
# "not ingested" is a recorded decision rather than an oversight.
EXCLUDED_SOURCES = [
    {
        "path": "baseline-arms/out/shards/",
        "reason": ("a concurrent session's S1 campaign: untracked, actively "
                   "appended during this recompute, and not the variance "
                   "envelope. Ingesting live untracked input would break "
                   "byte-reproducibility."),
    },
]


def file_digest(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_runs(piles: Piles, *, ledgers: Optional[Sequence[str]] = None,
                 a0_root: Optional[str] = None,
                 bundles: Optional[Sequence[str]] = None) -> List[Run]:
    """Every run the battery can see, guardrail already applied by adapters.

    Sources are injectable so the determinism test can run the real pipeline
    over a frozen fixture. It has to: `baseline-arms/ledger.jsonl` is
    append-only and another session may be writing to it right now, so two
    back-to-back recomputes over the live file can legitimately differ.

    `bundles` names which offline theory bundles to load, by name. `a0_root`
    is kept as an override for the A0 bundle alone because the determinism
    test and several adapter tests already point it at fixtures.
    """
    runs: List[Run] = []
    for path in (ledgers if ledgers is not None
                 else [p for _, p in SOURCES]):
        runs.extend(load_ledger_runs(path, piles=piles))

    wanted = set(bundles) if bundles is not None else {n for n, _, _ in BUNDLES}
    for name, root, loader in BUNDLES:
        if name not in wanted:
            continue
        if name == "cold-start-a0":
            if a0_root is None:
                continue
            root = a0_root
        runs.extend(loader(root, piles=piles))
    return sorted(runs, key=lambda r: (r.source, r.run_id))


def write_json(path: str, payload: Any) -> None:
    """One writer, one encoding, LF everywhere -- so a diff means a change."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    body = json.dumps(payload, sort_keys=True, indent=2,
                      ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


def spectrum(runs: Sequence[Run],
             values: Dict[str, Dict[str, Value]]) -> Dict[str, Any]:
    rows = {}
    for run in runs:
        rows[run.run_id] = {
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
            "repairs": len(run.repairs),
            "metrics": {mid: value.as_dict()
                        for mid, value in sorted(values[run.run_id].items())},
        }
    return rows


def coverage_summary(values: Dict[str, Dict[str, Value]]) -> Dict[str, Any]:
    out = {}
    for metric_id in sorted(REGISTRY):
        statuses: Dict[str, int] = {}
        for run_id in sorted(values):
            status = values[run_id][metric_id].status
            statuses[status] = statuses.get(status, 0) + 1
        out[metric_id] = {
            "family": REGISTRY[metric_id].family,
            "tier": tier_of(metric_id),
            "direction": REGISTRY[metric_id].direction,
            "by_status": statuses,
        }
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="artefact directory (default: battery/artifacts)")
    parser.add_argument("--ledger", action="append", default=None,
                        help="ledger JSONL to read; repeatable. Defaults to "
                             "the baseline-arms ledger.")
    parser.add_argument("--a0", default=A0_ROOT,
                        help="A0 bundle root, or 'none' to skip it")
    args = parser.parse_args(argv)

    a0_root = None if args.a0 == "none" else args.a0
    # `--a0 none` means "ledgers only", and has meant that since v0. Extending
    # it to the two new bundles keeps the existing determinism and adapter
    # tests isolated from the live repository rather than silently pulling
    # three more sources into them.
    bundles = [] if a0_root is None else None
    piles = load_piles()          # raises if the cut has drifted
    runs = collect_runs(piles, ledgers=args.ledger, a0_root=a0_root,
                        bundles=bundles)
    if not runs:
        print("no runs found; nothing to recompute", file=sys.stderr)
        return 1

    values = {run.run_id: evaluate(run) for run in runs}

    ledger_paths = (args.ledger if args.ledger is not None
                    else [p for _, p in SOURCES])
    inputs = {os.path.basename(p): file_digest(p) for p in ledger_paths}
    if a0_root:
        inputs["a0 raw_trace.jsonl"] = file_digest(os.path.join(
            a0_root, "artifacts", "raw_trace.jsonl"))

    n_games = len({r.game_id for r in runs if r.game_id})
    payload = {
        "battery_version": "v1",
        "provenance": {
            "cut": piles.provenance(),
            "input_digests": inputs,
            "excluded_sources": EXCLUDED_SOURCES,
            "n_runs": len(runs),
            "n_games": n_games,
            "arms": sorted({r.arm for r in runs}),
            "campaigns": sorted({r.campaign or "unlabelled" for r in runs}),
        },
        "cards": {mid: REGISTRY[mid].as_dict() for mid in sorted(REGISTRY)},
        "coverage": coverage_summary(values),
        "runs": spectrum(runs, values),
    }

    discrimination = discriminate(runs, values)
    discrimination["power"] = power_note(n_games)

    write_json(os.path.join(args.out, "capability_spectrum.json"), payload)
    write_json(os.path.join(args.out, "discrimination.json"), discrimination)
    # Process 1 and the arm contrast go to different files on purpose: one
    # validates metrics on control arms, the other reports what the validated
    # instrument reads across arms, and merging them is how a battery ends up
    # citing its own results as evidence that its metrics are sound.
    write_json(os.path.join(args.out, "arm_contrast.json"),
               contrast(runs, values))
    write_json(os.path.join(args.out, "validation_material.json"),
               material(runs, values, discrimination))
    write_json(os.path.join(args.out, "redundancy.json"), cluster(values))
    write_json(os.path.join(args.out, "gaming_audit.json"), gaming_audit())

    ok_counts = sum(1 for r in values for v in values[r].values() if v.ok)
    contrasted = contrast(runs, values)
    validated = material(runs, values, discrimination)
    print("runs           %d (%d games, arms: %s)"
          % (len(runs), n_games, ", ".join(sorted({r.arm for r in runs}))))
    print("campaigns      %s"
          % ", ".join(sorted({r.campaign or "unlabelled" for r in runs})))
    print("metrics        %d registered, %d computed values"
          % (len(REGISTRY), ok_counts))
    print("main table     %s" % ", ".join(gaming_audit()["main"]))
    print("reference      %s" % ", ".join(gaming_audit()["reference"]))
    print("arm contrast   %d of %d metrics have data on both sides"
          % (contrasted["n_metrics_with_overlap"], contrasted["n_metrics"]))
    print("unvalidated    %d metrics never computed on a control arm: %s"
          % (validated["n_unvalidated"], ", ".join(validated["unvalidated"])))
    print("power          %s" % discrimination["power"])
    print("artefacts      %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
