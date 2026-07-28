"""Compare a QC stage's measured verdict against the pinned known miss.

`verify.py`'s QC stages do not gate on `pass`, and that is a deliberate decision
with a written reason — see that file's docstring and
`qc/KNOWN_MISS.json._why_it_exists`. What they gate on instead is **deviation
from the pin**: the exact verdict this territory publishes is recorded by hand in
`KNOWN_MISS.json`, and anything else — better, worse, or absent — is a failure.

Three outcomes, and the third is the one the old code could not express:

| outcome | meaning | gates |
|---|---|---|
| `PINNED` | the measured verdict is the published one, to the field | no |
| `DEVIATION` | it is something else, in either direction | **yes** |
| `NO_VERDICT` | the stage did not produce a verdict this run | **yes** |

`NO_VERDICT` exists because `run_qc` returns 1 for "ran fine, missed the bar" and
Python returns 1 for an uncaught `ImportError`, so a process exit code cannot
tell those apart. Under the previous code both printed `[miss]` and exited 0,
which means the whole QC layer could have stopped executing without anyone
noticing. So a stage is required to have **rewritten its artifact during this
run** — the mtime is stamped before the stage is launched and must move — and the
artifact must parse and carry the pinned paths. `run_qc` writes its report
unconditionally on every completed run, so a stale mtime means it did not finish.

A verdict that *improves* is a deviation too, and gates. That is not pedantry: an
improvement means the pin is now a lie about what this territory ships, and the
only way a pin stays worth reading is if going stale is loud. The fix is to
re-run QC and transcribe the new numbers, never to widen the pin.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORLDGEN = os.path.dirname(HERE)

#: Default location of the hand-written pin. Overridable so the negative
#: control can implant one without touching the shipped file.
KNOWN_MISS = os.path.join(HERE, "KNOWN_MISS.json")

PINNED = "PINNED"
DEVIATION = "DEVIATION"
NO_VERDICT = "NO_VERDICT"


def load_pin(path: Optional[str] = None) -> Dict[str, Any]:
    with open(path or KNOWN_MISS, "r", encoding="utf-8") as handle:
        return json.load(handle)


def stage_pin(stage_key: str, path: Optional[str] = None) -> Dict[str, Any]:
    pin = load_pin(path)
    try:
        return pin["stages"][stage_key]
    except KeyError:
        raise KeyError(
            "%s has no pin for stage %r; every QC stage in verify.STAGES must "
            "be pinned, or it is ungated again" % (path or KNOWN_MISS, stage_key))


def artifact_stamp(artifact: str) -> Optional[float]:
    """The mtime to compare against after the stage runs, or None if absent."""
    try:
        return os.path.getmtime(artifact)
    except OSError:
        return None


def _dig(blob: Any, path: List[str]) -> Any:
    for key in path:
        if not isinstance(blob, dict) or key not in blob:
            return None
        blob = blob[key]
    return blob


def _diff_dict(measured: Any, expected: Dict[str, Any], where: str) -> List[str]:
    if not isinstance(measured, dict):
        return ["%s: expected an object, measured %r" % (where, measured)]
    problems = []
    for key in sorted(set(expected) | set(measured)):
        if key not in expected:
            problems.append("%s.%s: not pinned, measured %s"
                            % (where, key, json.dumps(measured[key], sort_keys=True)))
        elif key not in measured:
            problems.append("%s.%s: pinned %s, absent from the artifact"
                            % (where, key, json.dumps(expected[key], sort_keys=True)))
        elif measured[key] != expected[key]:
            problems.append("%s.%s: pinned %s, measured %s"
                            % (where, key,
                               json.dumps(expected[key], sort_keys=True),
                               json.dumps(measured[key], sort_keys=True)))
    return problems


def compare(pin: Dict[str, Any], report: Dict[str, Any]) -> List[str]:
    """Every field of the pin against the artifact. Empty list means PINNED."""
    problems: List[str] = []

    spec = pin["verdict"]
    where = ".".join(spec["path"])
    problems += _diff_dict(_dig(report, spec["path"]), spec["expected"], where)

    rows = pin.get("rows")
    if rows:
        table = _dig(report, rows["path"])
        base = ".".join(rows["path"])
        if not isinstance(table, dict):
            return problems + ["%s: expected an object of rows, measured %r"
                               % (base, table)]
        expected_rows = rows["expected"]
        for name in sorted(set(expected_rows) | set(table)):
            if name not in expected_rows:
                problems.append("%s.%s: row is not pinned — the sample changed"
                                % (base, name))
                continue
            if name not in table:
                problems.append("%s.%s: pinned row absent — the sample shrank"
                                % (base, name))
                continue
            row = table[name]
            if rows.get("subkey"):
                row = _dig(row, [rows["subkey"]])
            measured = {}
            if isinstance(row, dict):
                measured = {f: row[f] for f in rows["fields"] if f in row}
            expected = {f: expected_rows[name][f] for f in rows["fields"]
                        if f in expected_rows[name]}
            problems += _diff_dict(measured, expected, "%s.%s" % (base, name))

    return problems


def check(pin: Dict[str, Any], artifact: str,
          stamp: Optional[float]) -> Tuple[str, List[str]]:
    """Judge one QC stage. Returns `(outcome, problems)`.

    `stamp` is `artifact_stamp(artifact)` taken **before** the stage ran.
    """
    now = artifact_stamp(artifact)
    if now is None:
        return NO_VERDICT, [
            "the stage wrote no verdict: %s does not exist. A QC stage that "
            "cannot report is a failure, not a miss." % artifact]
    if stamp is not None and now == stamp:
        return NO_VERDICT, [
            "the stage did not rewrite %s during this run (mtime unchanged). "
            "run_qc writes its report on every completed run, so this is a "
            "stage that died before finishing — not a measured miss. Whatever "
            "is on disk is from an earlier run and says nothing about this one."
            % artifact]
    try:
        with open(artifact, "r", encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, ValueError) as exc:
        return NO_VERDICT, ["%s did not parse: %s" % (artifact, exc)]

    problems = compare(pin, report)
    if problems:
        return DEVIATION, problems
    return PINNED, []
