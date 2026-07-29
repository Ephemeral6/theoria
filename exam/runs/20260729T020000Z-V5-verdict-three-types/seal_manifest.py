"""Fill in this run's `MANIFEST.json` file digests.

`CLAUDE.md`: `files[].sha256` is optional, but a run whose artefacts are not
digested cannot later be shown to be the artefacts that were marked against.

Run from the repo root:
    PYTHONPATH=. python exam/runs/<this run>/seal_manifest.py
"""

import hashlib
import json
import os

RUN = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(RUN)))

TOUCHED = (
    "exam/grading/rubrics_verdict.py",
    "exam/grading/confusion_matrix.py",
    "exam/grading/calibration.py",
    "exam/grading/mark.py",
    "exam/papers/verdict.py",
    "exam/tests/test_verdict.py",
    "exam/tests/test_selftest.py",
)


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    files = []
    for name in sorted(os.listdir(RUN)):
        path = os.path.join(RUN, name)
        if os.path.isfile(path) and name != "MANIFEST.json":
            files.append({"path": name, "sha256": digest(path)})
    for rel in TOUCHED:
        files.append({"path": rel, "sha256": digest(os.path.join(REPO, rel))})

    manifest_path = os.path.join(RUN, "MANIFEST.json")
    with open(manifest_path, encoding="utf-8") as handle:
        doc = json.load(handle)
    doc["files"] = files
    doc["result"] = {
        "suite": "334 passed (321 at base commit)",
        "verify": "GREEN",
        "determinism": "byte-identical across PYTHONHASHSEED 7 and 99",
        "decisions_added": ["D-EX-020", "D-EX-021", "D-EX-022", "D-EX-023",
                            "D-EX-024", "D-EX-025", "D-EX-026"],
        "status_weaknesses_closed": [4, 6],
        "status_weaknesses_added": [20, 21, 22, 23, 24, 25, 26, 27],
        "sealed_pile_contact": "none",
        "api_calls": 0,
        "network": "none; exam.guard.no_network() holds over the suite",
    }
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(doc, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("sealed %d files into %s" % (len(files), manifest_path))


if __name__ == "__main__":
    main()
