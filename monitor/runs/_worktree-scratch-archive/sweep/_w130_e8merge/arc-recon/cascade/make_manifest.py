"""Build `cascade/MANIFEST.json` from what is actually on disk.

    python -m cascade.make_manifest --run-dir <dir>

Every artefact line is a real sha256 over real bytes, computed here rather than
transcribed, so the manifest cannot drift from the tree it describes. The
results block is read out of the per-game summaries, not retyped.

LOCATION, AND WHY IT DIFFERS FROM P-11. P-11's manifest sits in
`arc-recon/runs/P-11/`. P-20's work order scopes this ticket to *adding*
`arc-recon/cascade/` and nothing else, so the manifest lives inside that
subtree. Same content, different address; noted here rather than left as a
silent inconsistency for whoever collects the manifests.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ARC_RECON = os.path.dirname(HERE)
REPO = os.path.dirname(ARC_RECON)
sys.path.insert(0, ARC_RECON)

from cascade import spec                                   # noqa: E402


def sha256_of(path: str) -> Dict[str, Any]:
    with open(path, "rb") as fh:
        blob = fh.read()
    return {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}


def git(*args: str) -> str:
    try:
        return subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return ""


def build(run_dir: str, out_path: str) -> Dict[str, Any]:
    artifacts: Dict[str, Any] = {}
    for root, _dirs, names in os.walk(HERE):
        if "__pycache__" in root:
            continue
        for name in sorted(names):
            path = os.path.join(root, name)
            # A manifest cannot hash itself: the hash would be of the previous
            # version and would be wrong the moment this file is written.
            if os.path.abspath(path) == os.path.abspath(out_path):
                continue
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            artifacts[rel] = sha256_of(path)

    results: Dict[str, Any] = {}
    spent = 0
    for game in sorted(spec.SEQUENCES):
        path = os.path.join(run_dir, "summary.%s.json" % game)
        if not os.path.exists(path):
            results[game] = {"ran": False}
            continue
        with open(path, encoding="utf-8") as fh:
            summary = json.load(fh)
        spent += summary.get("actions_executed", 0)
        results[game] = {
            "ran": True,
            "actions_executed": summary.get("actions_executed"),
            "http_calls": summary.get("http_calls"),
            "cascade": summary.get("cascade"),
            "available_actions": summary.get("available_actions"),
            "win_levels": summary.get("win_levels"),
            "stopped_early_at": summary.get("stopped_early_at"),
            "steps_matching_offline_expectation":
                sum(1 for s in summary.get("steps", []) if s.get("matches_expected") is True),
            "steps_contradicting_offline_expectation":
                sum(1 for s in summary.get("steps", []) if s.get("matches_expected") is False),
            "steps_with_no_offline_expectation":
                sum(1 for s in summary.get("steps", []) if s.get("matches_expected") is None),
        }

    return {
        "prompt_id": "P-20",
        "title": "cascade semantics adjudicated online: does one action ever return several frames",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "run_dir": os.path.relpath(run_dir, REPO).replace(os.sep, "/"),
        "action_budget": {
            "cap_for_this_ticket": spec.BUDGET_TOTAL,
            "cap_per_game": spec.BUDGET_PER_GAME,
            "planned": spec.total_actions(),
            "spent": spent,
            "sealed_pile_api_calls": 0,
            "detail": "Executed ACTIONs only, as everywhere else in this repo: "
                      "RESET is a command, not an action, and the scorecard "
                      "counts successful ACTIONs. Failed commands execute "
                      "nothing and are recorded but not charged.",
        },
        "determinism": "No stochastic step. The sequences are frozen in "
                       "cascade/spec.py before the run; the expectations are "
                       "derived offline from data/precheck.json. The only "
                       "non-reproducible inputs are live API responses, and "
                       "every one of them is in the run directory's ledgers.",
        "results": results,
        "artifacts": artifacts,
    }


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out", default=os.path.join(HERE, "MANIFEST.json"))
    args = parser.parse_args(argv)
    manifest = build(os.path.abspath(args.run_dir), os.path.abspath(args.out))
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s (%d artefacts, %d actions spent)"
          % (args.out, len(manifest["artifacts"]),
             manifest["action_budget"]["spent"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
