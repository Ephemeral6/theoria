"""Emit the run manifest for a figure build.

    python figures/manifest.py --run-dir figures/runs/<UTC>-<prompt-id>

Follows the shape the other tracks publish (`battery/runs/P-14/MANIFEST.json`,
`proxy/runs/p9-shell-harden/MANIFEST.json`): the sha256 of every artefact and of
every input it was computed from, plus the spend line, so a reader can tell
whether a figure in the repository is the one this pipeline currently produces.

Written into the run directory rather than into `figures/` so that a later build
does not overwrite an earlier run's record.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import build_all  # noqa: E402
import sources  # noqa: E402
import theme  # noqa: E402

#: No defaults, on purpose. These were constants (``P4-figures`` / ``W-1611``)
#: until P8, so any later run that forgot a flag would have written a manifest
#: declaring itself P4's -- and a provenance record naming the wrong prompt is
#: worse than no record, because it reads as authoritative. Making them optional
#: with the old values as defaults would have left exactly that trap armed for
#: whoever ran the command without reading this comment, so ``--prompt-id`` and
#: ``--worker`` are required arguments instead.


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", sources.REPO_ROOT, *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def collect_artifacts() -> dict[str, str]:
    """sha256 of every produced artefact, keyed by path relative to figures/."""
    out: dict[str, str] = {}
    for root in (theme.csv_root(), theme.out_root()):
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for fn in sorted(filenames):
                abs_p = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_p, _HERE).replace(os.sep, "/")
                out[rel] = sources.sha256_file(abs_p)
    sha_file = os.environ.get("FIGURES_SHA") or os.path.join(_HERE, "SOURCES.sha256")
    if os.path.exists(sha_file):
        rel = os.path.relpath(sha_file, _HERE).replace(os.sep, "/")
        out[rel] = sources.sha256_file(sha_file)
    return out


def collect_inputs() -> tuple[dict[str, str], list[dict[str, str]]]:
    inputs: dict[str, str] = {}
    excluded: list[dict[str, str]] = []
    for src in sorted(sources.SOURCES, key=lambda s: s.path):
        if src.exists():
            inputs[src.path] = sources.sha256_file(src.abspath)
        else:
            excluded.append(
                {
                    "path": src.path,
                    "reason": src.note or "declared in sources.py, not present on disk",
                }
            )
    return inputs, excluded


def build_manifest(prompt_id: str, worker: str) -> dict:
    inputs, excluded = collect_inputs()
    artifacts = collect_artifacts()
    return {
        # CLAUDE.md requires prompt_id / branch / base_commit / utc. The clock
        # read is safe *here* and banned in a figure script: this file writes
        # into figures/runs/, and a run stamp never enters an artefact.
        "prompt_id": prompt_id,
        "worker": worker,
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "HEAD"),
        "command": "python figures/build_all.py",
        "verified_by": "figures/verify.sh",
        "figures": list(build_all.FIGURES),
        "themes": list(theme.THEMES),
        "formats": list(theme.FORMATS),
        "artifact_digests": artifacts,
        "n_artifacts": len(artifacts),
        "inputs": inputs,
        "n_inputs": len(inputs),
        "excluded_inputs": excluded,
        # This pipeline reads files. It plays no game, calls no model, opens no
        # socket -- so these three lines are structural, not a measurement.
        "game_spend_usd": 0.0,
        "model_calls": 0,
        "network_requests": 0,
        "sealed_pile_reads": 0,
        "notes": [
            "Every figure is regenerated from tracked data through a CSV intermediate "
            "layer; two builds over the same inputs are byte-identical (verify.sh gate 3).",
            "Figure 2 draws two arms: bare_cc across the model ladder, and theoria. They "
            "are NOT priced in the same unit -- a bare_cc turn buys one model call that "
            "picks one action, a theoria turn buys a desk call that theorises across the "
            "run (5 calls covered 7 actions). The third arm is still absent: there is no "
            "Schema arm in this ledger (baseline-arms/SCHEMA_LOCATE.md), so the model "
            "ladder stands in for it, weakly, per battery/DECISIONS.md D-B-004.",
            "The theoria arm's dollars are the provider's own arithmetic. The repo price "
            "table recomputes 8.3% lower, USD 0.4368 of that a known table defect "
            "(1-hour cache writes priced at the 5-minute multiplier). The disagreement is "
            "reported on the plate, not averaged away.",
            "Figure 7 contrasts A0 with cold-start-a0/prime. It is confounded by "
            "construction and says so: two variables were changed, not one, and the "
            "objection that bites is analytic rather than statistical -- A0-prime's toggle "
            "was designed so every case would have a witness, so the contrast demonstrates "
            "the mechanism rather than testing it.",
            "Three input families -- the theoria runs, the pilot roll-ups and the envelope "
            "shards -- are declared by RULE rather than by name (sources.DISCOVERY), so a "
            "run that lands on disk enters the figures at the next build. Every discovered "
            "file is still hashed into the inputs above. Each rule carries a floor, and "
            "verify.sh gate 8 walks the tree independently to check that what is on disk "
            "reached the picture -- gates 1-7 are all green on a figure that quietly omits "
            "data, which is how two tracked roll-ups went unread until P8.",
            "Figure 2's E2/E3/E4 are the battery's published values, read from "
            "capability_spectrum.json, never recomputed here: a second implementation of a "
            "Phase 4 primary endpoint is a second definition. The live theoria arm has none "
            "of the three -- it is in none of battery v2's arms -- and that is drawn as an "
            "absence with its reason rather than as a low score.",
            "battery/artifacts/arm_contrast.json is a v1-era artefact that predates the "
            "schema_repro arm. Figure 3 takes its column axis from capability_spectrum's "
            "own provenance instead, and reports the disagreement rather than absorbing it.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--run-dir", required=True, help="figures/runs/<UTC>-<prompt-id>")
    ap.add_argument("--prompt-id", required=True, help="the board item this build belongs to")
    ap.add_argument("--worker", required=True, help="who ran it")
    args = ap.parse_args(argv)

    run_dir = args.run_dir if os.path.isabs(args.run_dir) else os.path.join(sources.REPO_ROOT, args.run_dir)
    os.makedirs(run_dir, exist_ok=True)
    target = os.path.join(run_dir, "MANIFEST.json")

    manifest = build_manifest(prompt_id=args.prompt_id, worker=args.worker)
    body = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)

    print(f"wrote {os.path.relpath(target, sources.REPO_ROOT)}")
    print(f"  {manifest['n_artifacts']} artefacts, {manifest['n_inputs']} inputs, "
          f"{len(manifest['excluded_inputs'])} declared-absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
