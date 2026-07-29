"""Non-vacuity check for P3.3.

The claim under test is that gating the degradation keys on `scope ==
UNDETERMINED` is what keeps `artifacts/candidates.jsonl` byte-stable.  A check
that only observes "the hash did not change" cannot distinguish a correct gate
from a gate that never fires.  So: monkeypatch `Law.as_json` to emit the same
keys **unconditionally**, re-run the same integration path into a scratch file,
and show the sha256 moves.  Writes only into a temp directory.
"""

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from engines.zero_space import zerospace
from tools import run_all

ARTIFACT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "artifacts", "candidates.jsonl")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def zero_space_ids(path):
    out = []
    for line in open(path, encoding="utf-8"):
        row = json.loads(line)
        if row["engine"] == "zero_space":
            out.append(row["id"])
    return out


def main():
    tmp = tempfile.mkdtemp(prefix="e15p3cf-")
    control = os.path.join(tmp, "control.jsonl")
    mutant = os.path.join(tmp, "mutant.jsonl")

    # --- control: the shipped code, through the same driver -----------------
    run_all.main(["--out", control, "--deterministic", "--force"])

    # --- mutant: the same keys, ungated -------------------------------------
    original = zerospace.Law.as_json

    def ungated(self):
        payload = original(self)
        payload.setdefault("scope_proved", self.scope_exhaustive)
        payload.setdefault("subset_enumeration_limit",
                           self.subset_enumeration_limit)
        payload.setdefault("truncated_cells", list(self.truncated_cells))
        payload.setdefault("error", None)
        return payload

    zerospace.Law.as_json = ungated
    try:
        run_all.main(["--out", mutant, "--deterministic", "--force"])
    finally:
        zerospace.Law.as_json = original

    report = {
        "checked_in_artifact_sha256": sha(ARTIFACT),
        "control_sha256": sha(control),
        "control_matches_artifact": sha(control) == sha(ARTIFACT),
        "mutant_sha256": sha(mutant),
        "mutant_differs_from_control": sha(mutant) != sha(control),
        "n_zero_space_rows": len(zero_space_ids(control)),
        "n_zero_space_ids_changed_by_mutant": sum(
            1 for a, b in zip(zero_space_ids(control), zero_space_ids(mutant))
            if a != b),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
