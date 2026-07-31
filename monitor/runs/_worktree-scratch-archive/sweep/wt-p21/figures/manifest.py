"""Emit the run manifest for a P-21 figure build.

    python figures/manifest.py --run-dir figures/runs/<UTC>-p21

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

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import build_all  # noqa: E402
import sources  # noqa: E402
import theme  # noqa: E402

PROMPT_ID = "P-21"


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


def build_manifest() -> dict:
    inputs, excluded = collect_inputs()
    artifacts = collect_artifacts()
    return {
        "prompt_id": PROMPT_ID,
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
            "Figure 4 (transfer) is not in this build -- its data lives in cold-start-a3 "
            "and belongs to the arm that owns it.",
            "Figure 2 ships with the bare_cc arm across the model ladder: there is no "
            "Schema arm (baseline-arms/SCHEMA_LOCATE.md) and the Theoria arm has no cost "
            "ledger yet. The extractor keys the arm axis off each record's own 'arm' "
            "field, so adding the third column is configuration, not code.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--run-dir", required=True, help="figures/runs/<UTC>-p21")
    args = ap.parse_args(argv)

    run_dir = args.run_dir if os.path.isabs(args.run_dir) else os.path.join(sources.REPO_ROOT, args.run_dir)
    os.makedirs(run_dir, exist_ok=True)
    target = os.path.join(run_dir, "MANIFEST.json")

    manifest = build_manifest()
    body = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)

    print(f"wrote {os.path.relpath(target, sources.REPO_ROOT)}")
    print(f"  {manifest['n_artifacts']} artefacts, {manifest['n_inputs']} inputs, "
          f"{len(manifest['excluded_inputs'])} declared-absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
