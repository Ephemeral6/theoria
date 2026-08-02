"""Write this run's MANIFEST.json.

Two kinds of path go in `files`, and the difference matters:

* the run's own artefacts, which are the evidence this ticket produced;
* the **inputs it adjudicated** -- `exam/endpoint.py` and
  `exam/tools/endpoint_verdict.py`.  Row 9.15's `clears_when` says the
  conversion layer must "exist **and be hashed**", and before this run it was
  hashed nowhere in the repo: the seven control transcripts were sealed by
  `exam/runs/20260801T0000Z-EP-endpoint2-prereg/MANIFEST.json`, but the code
  that reads them was not.  That is the wrong half to leave loose -- a control
  is only a control relative to the judge that scores it.  freeze hashes the
  judge here because freeze is the territory whose gate depends on it.

Run from the repo root.
"""

import hashlib
import json
import os
import subprocess

RUN = "freeze/runs/20260802T085225Z-S45-launch-blockers"

ADJUDICATED_INPUTS = [
    "exam/endpoint.py",
    "exam/tools/endpoint_verdict.py",
    "exam/grading/confusion_matrix.py",
    "exam/grading/mark.py",
    "exam/artifacts/endpoint_controls/oracle.answers.json",
    "exam/artifacts/endpoint_controls/abstainer.answers.json",
    "exam/artifacts/endpoint_controls/memoriser.answers.json",
    "exam/artifacts/endpoint_controls/bluffer.answers.json",
    "exam/artifacts/endpoint_controls/denier.answers.json",
    "exam/artifacts/endpoint_controls/overclaimer.answers.json",
    "exam/artifacts/endpoint_controls/null.answers.json",
    "exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json",
]

TOUCHED = [
    "freeze/launch_blockers.json",
    "freeze/launch_gate.py",
    "freeze/STATS_RULES.md",
    "freeze/CLAIMS_TEXT.md",
    "freeze/RESIDUALS.json",
    "freeze/build_manifest.py",
]


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    return subprocess.run(("git",) + args, capture_output=True,
                          text=True).stdout.strip()


def entries(paths, role):
    out = []
    for p in sorted(paths):
        if not os.path.isfile(p):
            continue
        out.append({"path": p.replace(os.sep, "/"), "role": role,
                    "bytes": os.path.getsize(p), "sha256": sha256(p)})
    return out


def main():
    own = []
    for name in sorted(os.listdir(RUN)):
        p = os.path.join(RUN, name)
        if os.path.isfile(p) and name != "MANIFEST.json":
            own.append(p)

    doc = {
        "prompt_id": "S45-launch-blockers-915-916-and-the-reason-floor",
        "branch": "agent/s45-launch-blockers-915-916-and-the-reason-floor",
        "base_commit": git("rev-parse", "master"),
        "head_commit": git("rev-parse", "HEAD"),
        "utc": "2026-08-02T08:52:25Z",
        "worker": "W-9201",
        "territory": "freeze",
        "what": (
            "freeze's own ruling on launch blockers 9.15 and 9.16, on ⟨c_min⟩, "
            "and on the reason-floor fork raised by exam's 2026-08-01 ask. "
            "Every verdict here was produced by running the command, not by "
            "reading the ask."),
        "spend_usd": 0.0,
        "spend_note": "offline throughout; no API call, no game contact, "
                      "sealed pile untouched (21 ids scanned against every "
                      "changed file, zero hits)",
        "files": (entries(own, "run-artefact")
                  + entries(ADJUDICATED_INPUTS, "adjudicated-input")
                  + entries(TOUCHED, "delivered")),
    }
    with open(os.path.join(RUN, "MANIFEST.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s/MANIFEST.json (%d files)" % (RUN, len(doc["files"])))


if __name__ == "__main__":
    main()
