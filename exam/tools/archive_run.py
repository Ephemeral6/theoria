"""Archive one exam run under `exam/runs/<run_id>/`.

    python -m exam.tools.archive_run <run_id>

`monitor/METHOD.md` asks every session to leave a run archive whose manifest
carries `prompt_id`, `branch`, `base_commit` and a seed, so an artefact can be
traced back to the work order that produced it and replayed deterministically.
This writes that manifest and the digests of everything the run produced.

Two deliberate choices:

* **The manifest records digests, not a timestamp.**  A wall clock in an
  artefact makes two identical runs differ, which destroys the only cheap check
  we have that a run *was* deterministic.  The run id carries whatever ordering
  a reader needs.

* **The truth files are digested but not copied.**  An archive that ships the
  answer keys next to the sheets recreates, in the archive, exactly the leak the
  exam spent all this effort avoiding.  The keys stay in `artifacts/truth/`; the
  archive records their digests so a later reader can prove the keys they hold
  are the keys that were marked against.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import guard                                              # noqa: E402
from exam.grading.registry import manifest as rubric_manifest       # noqa: E402
from exam.model import (ARTIFACTS, canonical, read_json, sha256,    # noqa: E402
                        sha256_text, write_json)

RUNS_DIR = os.path.join(HERE, "runs")
PROMPT_ID = "P-15"

#: Every deterministic construction in the exam is enumerative or pinned to this
#: seed. It is recorded so a failing run replays; METHOD.md item 9.
SEED = 20260728


def _git(*args: str) -> Optional[str]:
    try:
        out = subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                             text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _digest_tree(root: str) -> Dict[str, str]:
    """path relative to `exam/` -> sha256 of its bytes."""
    out: Dict[str, str] = {}
    if not os.path.isdir(root):
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            with open(path, "rb") as fh:
                import hashlib
                out[os.path.relpath(path, HERE).replace("\\", "/")] = \
                    hashlib.sha256(fh.read()).hexdigest()
    return out


def build_manifest(run_id: str) -> Dict[str, Any]:
    summary_path = os.path.join(ARTIFACTS, "exam_summary.json")
    calib_path = os.path.join(ARTIFACTS, "calibration.json")
    build_path = os.path.join(ARTIFACTS, "build_manifest.json")

    summary = read_json(summary_path) if os.path.exists(summary_path) else {}
    calibration = read_json(calib_path) if os.path.exists(calib_path) else {}
    build = read_json(build_path) if os.path.exists(build_path) else {}

    papers = {row["paper_id"]: {"sheet_sha256": row["sheet_sha256"],
                                "key_sha256": row["key_sha256"],
                                "n_items": row["n_items"],
                                "question_type": row["question_type"]}
              for row in build.get("papers", [])}

    return {
        "run_id": run_id,
        "prompt_id": PROMPT_ID,
        "seed": SEED,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "HEAD"),
        "worktree_dirty": bool(_git("status", "--porcelain")),
        "python": "%d.%d.%d" % sys.version_info[:3],
        "rubric": rubric_manifest(),
        "provenance": guard.provenance(),
        "papers": papers,
        "calibration": {
            "calibrated": calibration.get("calibrated"),
            "failures": calibration.get("failures", []),
            "per_type": {qt: {"paper_id": r["paper_id"],
                              "calibrated": r["calibrated"],
                              "scores": {m: r["modes"][m]["fraction"]
                                         for m in ("oracle", "null", "memoriser",
                                                   "bluffer")
                                         if m in r["modes"]},
                              "structural": r["modes"].get("structural", {})}
                         for qt, r in sorted(calibration.get("per_type", {}).items())},
        },
        "marked": summary.get("marked", []),
        "artifact_digests": _digest_tree(ARTIFACTS),
        "note": ("Answer keys are digested here, never copied. An archive that "
                 "ships the keys beside the sheets rebuilds the leak the exam "
                 "exists to avoid."),
    }


def archive(run_id: str) -> str:
    manifest = build_manifest(run_id)
    path = os.path.join(RUNS_DIR, run_id, "MANIFEST.json")
    write_json(path, manifest)
    return path


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python -m exam.tools.archive_run <run_id>")
        return 2
    path = archive(argv[0])
    manifest = read_json(path)
    print("exam -- archived run %s (prompt %s, seed %d)"
          % (manifest["run_id"], manifest["prompt_id"], manifest["seed"]))
    print("  branch      %s" % manifest["branch"])
    print("  base commit %s" % manifest["base_commit"])
    print("  calibrated  %s" % manifest["calibration"]["calibrated"])
    print("  papers      %d, artefacts digested %d"
          % (len(manifest["papers"]), len(manifest["artifact_digests"])))
    print("  -> %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
