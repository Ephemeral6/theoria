"""The standing negative-control probe: new gates must arrive with their own red.

V11 counted, once, how many of this repository's acceptance entry points have
ever been *demonstrated* to fail. 35 of 127 had not. A count is a photograph;
the defect is a process. Next week's gate will have no negative control either,
because nothing asks it for one. This asks.

What it does
------------

1. **Enumerate** the acceptance entry points on the current tree, mechanically: a
   non-test ``.py`` file with a ``__main__`` block and at least one path that can
   leave the process non-zero. 127 files at the time of writing.
2. **Judge** each one under `criterion.py` -- does a test somewhere construct a
   bad input for *this file* and assert it fails?
3. **Compare** against `KNOWN_GAPS.json`, the hand-kept inventory of the gaps
   this repository currently ships, each with the territory that owns it. The
   shape is `worldgen/qc/KNOWN_MISS.json`'s, and for its reason: pinning the
   measured state is what makes a *deviation* legible without demanding that
   someone else's 35 gaps be closed before this probe can ever be green.

What gates, and what does not
-----------------------------

| finding | meaning | gates |
|---|---|---|
| ``NEW_GAP``     | an entry point that is not in the pin and has no negative control | **yes** |
| ``REGRESSION``  | a pinned ``present`` that is now ``absent`` | **yes** |
| ``NEW_OK``      | a new entry point that arrived with a negative control | no |
| ``IMPROVED``    | a pinned gap that has been closed -- update the pin | no |
| ``RETIRED``     | a pinned path that no longer exists | no |
| ``NOT_A_GATE``  | a pinned path that no longer has a non-zero exit path | no |

Two of these deliberately differ from `worldgen/qc/gate.py`, which gates on any
deviation in either direction:

* ``IMPROVED`` does not gate. There, the pin is three QC stages and going stale
  is cheap to fix; here it is 127 files across nine territories, and a probe that
  turns every repair into a red is a probe that gets switched off. The cost is
  that the pin drifts optimistic, so it prints loudly and the pin records the
  date it was taken.
* ``NOT_A_GATE`` does not gate, because the enumerator that decides what counts
  as a gate has **not** been calibrated against anything. It is a heuristic over
  ``sys.exit`` and ``return <nonzero>``. Gating on an uncalibrated enumerator is
  the mistake this lab exists to name, so it reports and does not block.

Read `runs/<...>-V14-standing-negative-control-probe/CALIBRATION.md` before
trusting any of this. The criterion misses roughly a third of the negative
controls a human would credit, and that number -- not this docstring -- is what
decides whether the probe belongs in a merge gate.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import criterion  # noqa: E402

DEFAULT_PIN = os.path.join(HERE, "KNOWN_GAPS.json")
REPO = os.path.dirname(os.path.dirname(HERE))

NEW_GAP = "NEW_GAP"
REGRESSION = "REGRESSION"
NEW_OK = "NEW_OK"
IMPROVED = "IMPROVED"
RETIRED = "RETIRED"
NOT_A_GATE = "NOT_A_GATE"
PINNED_OK = "PINNED_OK"

GATING = (NEW_GAP, REGRESSION)


# --------------------------------------------------------------------------
# Enumerating what counts as an acceptance entry point
# --------------------------------------------------------------------------

_EXIT_FUNCS = {"exit", "_exit"}
_MAIN_FUNCS = {"main", "_main", "cli", "run_main"}


def can_exit_nonzero(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in _EXIT_FUNCS and node.args and criterion._nonzero_int(node.args[0]):
                return True
        if isinstance(node, ast.Raise):
            exc = node.exc
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) \
                    and exc.func.id == "SystemExit":
                return True
            if isinstance(exc, ast.Name) and exc.id == "SystemExit":
                return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name in _MAIN_FUNCS:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Return) and _returns_nonzero(inner.value):
                    return True
    return False


def _returns_nonzero(value: Optional[ast.AST]) -> bool:
    """``return 1``, and also ``return 0 if ok else 1``.

    The conditional form is how most of this repository spells it -- `return 0 if
    all_ok else 1` appears in `verify_c4.py`, `transcribe_deadlock_certificates.py`,
    `run_matrix.py`, `check_redlines.py` and a dozen others. The first draft of
    this enumerator looked only at `ast.Constant`, so it found none of them, and
    `tests/test_probe.py`'s planted gate -- which is written in exactly that
    style -- was not enumerated at all. The probe's own negative control caught
    it on its first run, which is the entire argument for having one.
    """
    if value is None:
        return False
    if criterion._nonzero_int(value):
        return True
    if isinstance(value, ast.IfExp):
        return _returns_nonzero(value.body) or _returns_nonzero(value.orelse)
    return False


def has_main_block(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                return True
    return False


def enumerate_entry_points(index: criterion.Index) -> List[str]:
    """Every non-test ``.py`` that is runnable and can leave the process non-zero.

    Not calibrated. See this module's docstring for why nothing gates on it.
    """
    found: List[str] = []
    for rel in index.files:
        if criterion.is_test_file(rel):
            continue
        try:
            src = open(os.path.join(index.root, rel), "r", encoding="utf-8").read()
            tree = ast.parse(src, filename=rel)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        if has_main_block(tree) and can_exit_nonzero(tree):
            found.append(rel)
    return sorted(found)


# --------------------------------------------------------------------------
# The probe
# --------------------------------------------------------------------------


def load_pin(path: str) -> Dict[str, dict]:
    with open(path, "r", encoding="utf-8") as handle:
        blob = json.load(handle)
    return blob.get("entries", {})


def run(root: str = REPO, pin_path: str = DEFAULT_PIN,
        detector: str = "A-B") -> Dict[str, object]:
    index = criterion.Index.build(root)
    verdicts = criterion.Verdicts(
        a=criterion.scan_tests(index, absence=True),
        a_strict=criterion.scan_tests(index, absence=False),
        b=criterion.scan_selftests(index),
        naive=criterion.scan_naive(index))

    pin = load_pin(pin_path)
    entry_points = enumerate_entry_points(index)
    on_disk = set(entry_points)

    findings: List[Dict[str, object]] = []
    for rel in entry_points:
        measured = verdicts.verdict(rel, detector)
        record = pin.get(rel)
        if record is None:
            kind = NEW_OK if measured == criterion.PRESENT else NEW_GAP
        elif record["verdict"] == criterion.PRESENT and measured == criterion.ABSENT:
            kind = REGRESSION
        elif record["verdict"] == criterion.ABSENT and measured == criterion.PRESENT:
            kind = IMPROVED
        else:
            kind = PINNED_OK
        findings.append({
            "path": rel, "kind": kind, "measured": measured,
            "pinned": record["verdict"] if record else None,
            "owner": (record or {}).get("owner"),
            "note": (record or {}).get("note"),
            "evidence": [h.as_dict() for h in verdicts.evidence(rel, detector)][:3],
        })

    for rel, record in sorted(pin.items()):
        if rel in on_disk:
            continue
        exists = os.path.exists(os.path.join(index.root, rel))
        findings.append({
            "path": rel, "kind": NOT_A_GATE if exists else RETIRED,
            "measured": verdicts.verdict(rel, detector) if exists else None,
            "pinned": record["verdict"], "owner": record.get("owner"),
            "note": record.get("note"), "evidence": [],
        })

    reds = [f for f in findings if f["kind"] in GATING]
    return {
        "root": criterion._norm(os.path.abspath(root)),
        "pin": criterion._norm(os.path.abspath(pin_path)),
        "detector": detector,
        "entry_points": len(entry_points),
        "pinned": len(pin),
        "findings": findings,
        "counts": {k: sum(1 for f in findings if f["kind"] == k)
                   for k in (NEW_GAP, REGRESSION, NEW_OK, IMPROVED, RETIRED,
                             NOT_A_GATE, PINNED_OK)},
        "red": [f["path"] for f in reds],
        "exit_code": 1 if reds else 0,
    }


def render(report: Dict[str, object], verbose: bool = False) -> List[str]:
    out = ["negative-control probe: %d entry points, %d pinned, detector %s"
           % (report["entry_points"], report["pinned"], report["detector"])]
    counts = report["counts"]
    out.append("  " + "  ".join("%s=%d" % (k, v) for k, v in counts.items() if v))
    for finding in report["findings"]:
        kind = finding["kind"]
        if kind == PINNED_OK and not verbose:
            continue
        if kind == NEW_GAP:
            out.append("RED  %s: a new acceptance entry point with no negative "
                       "control. Nothing in this repository has ever shown it "
                       "failing." % finding["path"])
        elif kind == REGRESSION:
            out.append("RED  %s: pinned as having a negative control; the tree no "
                       "longer has one. owner=%s" % (finding["path"], finding["owner"]))
        elif kind == NEW_OK:
            out.append("new  %s: arrived with a negative control (%s)"
                       % (finding["path"],
                          finding["evidence"][0]["why"] if finding["evidence"] else "?"))
        elif kind == IMPROVED:
            out.append("note %s: pinned as a gap, now covered -- re-pin it. owner=%s"
                       % (finding["path"], finding["owner"]))
        elif kind == RETIRED:
            out.append("note %s: pinned but gone from the tree -- drop it from the pin"
                       % finding["path"])
        elif kind == NOT_A_GATE:
            out.append("note %s: pinned, still present, but no longer has a non-zero "
                       "exit path" % finding["path"])
        elif verbose:
            # Not "ok". `absent, as pinned` is a gap this repository ships and
            # somebody owns; the probe is quiet about it, which is not the same
            # as it being fine.
            out.append("pin  %-62s %s, as pinned   owner=%s"
                       % (finding["path"], finding["measured"], finding["owner"]))
    out.append("PROBE: %s" % ("RED" if report["red"] else "green"))
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="the standing negative-control probe")
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--pin", default=DEFAULT_PIN)
    ap.add_argument("--detector", default="A-B", choices=list(criterion.DETECTORS))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--write-pin", metavar="PATH",
                    help="emit a pin scaffold for the current tree and exit 0. "
                         "Owners and notes still have to be written by hand -- an "
                         "auto-regenerated pin records nothing.")
    args = ap.parse_args(argv)

    if args.write_pin:
        index = criterion.Index.build(args.root)
        verdicts = criterion.Verdicts(
            a=criterion.scan_tests(index, absence=True),
            a_strict=criterion.scan_tests(index, absence=False),
            b=criterion.scan_selftests(index),
            naive=criterion.scan_naive(index))
        entries = {rel: {"verdict": verdicts.verdict(rel, args.detector),
                         "owner": "UNASSIGNED", "note": ""}
                   for rel in enumerate_entry_points(index)}
        with open(args.write_pin, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"entries": entries}, handle, indent=2, sort_keys=True,
                      ensure_ascii=False)
            handle.write("\n")
        print("scaffold written to %s (%d entries)" % (args.write_pin, len(entries)))
        return 0

    report = run(args.root, args.pin, args.detector)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for line in render(report, args.verbose):
            print(line)
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
