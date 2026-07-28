"""Transcribe `deadlock_carver` candidate rows into certificate documents.

The emitting half of `deadlock_certificate_v0.1` belongs to `engine-rig` and is
not written here — the same division `ic3_certificate_v0.1` records, for the
same reason: the side holding the engine's internal state should write the
export, and this track does not put a character into the other track's tree.

Until that export exists, the fixtures this track tests against are transcribed
**field by field** from candidate rows the other track has already published, and
`tests/test_deadlock_certificate.py` re-runs this transcription and fails if the
committed fixture has drifted from the row. So the fixture cannot quietly become
something the producer never said.

    python -m tools.transcribe_deadlock_certificates            # check
    python -m tools.transcribe_deadlock_certificates --write    # rewrite fixtures
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CANDIDATES = os.path.join(REPO, "engine-rig", "artifacts", "candidates.jsonl")
FIXTURES = os.path.join(HERE, "..", "tests", "fixtures")

SCHEMA = "deadlock_carver/conditional_unsolvability_certificate@1"

#: Which rows become fixtures, and under what name. Both closure forms are
#: represented on purpose: the corner is the degenerate case (nothing deletes a
#: pattern atom at all) and the pair is the one that needs the mutex reasoning.
WANTED = {
    "at(b1,c11)": "deadlock_open4far_b1c11.json",
    "at(b1,c12) AND at(b2,c13)": "deadlock_open4far_b1c12_b2c13.json",
}


def rows() -> List[Dict]:
    with open(CANDIDATES, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def transcribe(row: Dict) -> Dict:
    payload = row["payload"]
    return {
        "schema": SCHEMA,
        "claim": payload["claim"],
        "conclusion": payload["rendering"],
        "domain": payload["domain"],
        "problem": payload["problem"],
        "pattern": [list(atom) for atom in payload["pattern"]],
        "pattern_text": payload["pattern_text"],
        "closure": payload["closure"],
        "n_deleting_actions": payload["n_deleting_actions"],
        "blocked_actions": payload["blocked_actions"],
        "goal_conflict": payload["goal_conflict"],
        "coverage": row["evidence"]["coverage"],
        "produced_by": "engine-rig/engines/deadlock_carver",
        "provenance": {
            "source": "engine-rig/artifacts/candidates.jsonl",
            "row_id": row["id"],
            "row_timestamp": row["timestamp"],
            "transcribed_by": "theory-compiler/tools/transcribe_deadlock_certificates.py",
            "note": ("A transcription, not an engine-rig artefact. The emitting half "
                     "of this schema belongs to engine-rig and is not written by this "
                     "track; until it exists the consumer is tested against this copy, "
                     "and a test re-runs the transcription to keep the two identical."),
        },
    }


def build() -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for row in rows():
        payload = row.get("payload") or {}
        if payload.get("producer") != "deadlock_carver":
            continue
        if payload.get("form") != "conditional_unsolvability":
            continue
        if payload.get("problem") != "sokoban-open4far":
            continue
        name = WANTED.get(payload.get("pattern_text"))
        if name:
            out[name] = transcribe(row)
    missing = set(WANTED.values()) - set(out)
    if missing:
        raise SystemExit("no candidate row for: %s" % sorted(missing))
    return out


def render(doc: Dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="rewrite the fixtures instead of checking them")
    args = parser.parse_args(argv)

    drifted = []
    for name, doc in sorted(build().items()):
        path = os.path.join(FIXTURES, name)
        text = render(doc)
        if args.write:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            print("wrote %s" % name)
            continue
        if not os.path.exists(path):
            drifted.append("%s does not exist" % name)
        else:
            with open(path, encoding="utf-8") as handle:
                if handle.read() != text:
                    drifted.append("%s differs from the candidate row" % name)
    for line in drifted:
        print(line, file=sys.stderr)
    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
