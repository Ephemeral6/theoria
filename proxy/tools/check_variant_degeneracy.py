"""Refuse a variant run whose `win_tighten` abolished the win condition.

`proxy/variants.py` reads an absent score as a shortfall, on purpose: the other
direction would let a game that never reports a score win a tightened variant
outright. On a game that reports no score at all, that reading turns
`win_tighten` into "every WIN becomes NOT_FINISHED, at every requirement
value". The variant is unsolvable, but not for the reason its `justification`
claims, and until D-032 nothing in the record said so.

D-032 puts an explicit `degenerate` bit on the `applied` record. This is the
reader that makes the bit cost something. Per D-031: a rule with no detector is
prose, and a bit no code path reads is decoration.

    python -m proxy.tools.check_variant_degeneracy proxy/var/ledger.jsonl
    python -m proxy.tools.check_variant_degeneracy --json <path>

Exit codes:

    0   no degenerate rewrite in the stream
    2   at least one; the run's variant claim does not follow from its
        construction and the item is not exam-eligible (rule R-V22)
    1   the file could not be read

**It reads the marker and nothing else.** It does not re-derive degeneracy from
`score: null`, and that restraint is the point: if the marker is stripped from
the stream this tool passes, which is what makes the marker -- rather than some
lucky second signal -- the thing that catches the defect. The negative control
in `tests/test_variant_degeneracy.py` strips it and asserts exactly that.

**Rule R-V22, the executable half.** An item whose verdict came from a
degenerate rewrite does not count toward the reason score. `--json` reports
`exam_eligible: false` for it, and the non-zero exit means an operator has to
decide about it rather than sweep it along with the greens. The grading side of
that rule lives in `exam/`, which this directory may not edit; what `proxy/`
can guarantee is that the fact reaches the grader in a form it cannot miss.
"""

import argparse
import json
import sys
from typing import Any, Dict, List


def scan_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Judge a list of ledger records. Pure; the file reader is separate so a
    test can hand it records without touching a disk."""
    findings: List[Dict[str, Any]] = []
    variants: Dict[str, Dict[str, Any]] = {}

    for record in records:
        variant = record.get("variant")
        if not isinstance(variant, dict):
            continue
        variant_id = variant.get("variant_id") or "<unnamed>"
        seen = variants.setdefault(
            variant_id, {"variant_id": variant_id,
                         "spec_sha256": variant.get("spec_sha256"),
                         "degenerate_rewrites": 0, "exam_eligible": True})
        for applied in _applied_records(variant.get("applied")):
            if applied.get("op") != "win_tighten":
                continue
            if applied.get("degenerate") is not True:
                continue
            seen["degenerate_rewrites"] += 1
            seen["exam_eligible"] = False
            findings.append({
                "seq": record.get("seq"),
                "variant_id": variant_id,
                "require_score": applied.get("require_score"),
                "reason": applied.get("reason"),
                "occurrence": applied.get("occurrence"),
                "note": applied.get("note"),
            })

    verdict = "REFUSED" if findings else "PASS"
    return {"verdict": verdict, "records": len(records),
            "findings": findings,
            "variants": [variants[k] for k in sorted(variants)]}


def _applied_records(applied: Any) -> List[Dict[str, Any]]:
    """`applied` is one operator's record, or `{"op":"multiple","applied":[..]}`
    -- and `env_proxy` nests a second level when an outbound rewrite and an
    inbound one both fired on the same command, so this recurses rather than
    unwrapping once."""
    if not isinstance(applied, dict):
        return []
    if applied.get("op") == "multiple":
        out: List[Dict[str, Any]] = []
        for inner in applied.get("applied") or []:
            out.extend(_applied_records(inner))
        return out
    return [applied]


def scan_file(path: str) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except ValueError:
                # Not this tool's complaint to make: validate_ledger.py owns
                # unreadable lines. Skipping one here cannot hide a degenerate
                # rewrite that a readable line would have shown.
                continue
            if isinstance(parsed, dict):
                records.append(parsed)
    report = scan_file_report(path, records)
    return report


def scan_file_report(path: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    report = scan_records(records)
    report["path"] = path
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        report = scan_file(args.path)
    except OSError as exc:
        print("cannot read %s: %s" % (args.path, exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("%s: %s (%d records, %d degenerate rewrite(s))"
              % (report["path"], report["verdict"], report["records"],
                 len(report["findings"])))
        for finding in report["findings"][:5]:
            print("  seq %s  variant %s  require_score=%s  reason=%s"
                  % (finding["seq"], finding["variant_id"],
                     finding["require_score"], finding["reason"]))
            if finding.get("note"):
                print("    %s" % finding["note"])
        if len(report["findings"]) > 5:
            print("  ... %d more" % (len(report["findings"]) - 5))
        for variant in report["variants"]:
            if not variant["exam_eligible"]:
                print("  R-V22  variant %s is not exam-eligible: its verdict "
                      "came from an abolished win condition, not a tightened "
                      "one, so it does not count toward the reason score"
                      % variant["variant_id"])

    return 2 if report["verdict"] == "REFUSED" else 0


if __name__ == "__main__":
    sys.exit(main())
