"""Validator for candidates.jsonl against CONTRACTS/candidates_schema_v0.2.md.

The v0.1 validator (`engine-rig/tools/validate_candidates.py`) stays the
authority for v0.1 and is untouched by this file. This one is a **second,
independent implementation** of the v0.2 rules, written from the contract text
rather than derived from the v0.1 source, and it deliberately imports neither
that module nor anything else from `engine-rig`: the tracks meet at data files.
Two validators that share code are one validator with two names, and then
"v0.1 still works" is not a claim anyone has checked.

What v0.2 adds, and nothing else (see the contract for which engine forced
which):

* `engine` gains `deadlock_carver`, `ic3_pdr`
* `kind` gains `deadlock_theorem`, `pruning_account`
* `evidence.basis` — optional, an object naming the units of `transitions`
  and of `coverage`. **No default**: absent means "the basis is whatever this
  engine's README says", which is exactly the v0.1 situation.
* `derived_from` — optional, a list of `id`s this candidate was built from.
* `contract` — optional, the contract string this row targets.

Everything else is v0.1 verbatim, and "verbatim" is checked rather than
asserted: `tests/test_validate_candidates_v02.py` runs both validators over the
same corpus and fails on any row v0.1 accepts and v0.2 rejects. That test is
there because the first draft of this file quietly dropped v0.1's
zero-denominator rule and its blank-line rule, and added an id-uniqueness rule
v0.1 never had — three "additive" changes that were not additive. An
independent review caught all three; the test is what makes the claim checkable
instead of asserted.

**No id-uniqueness check, deliberately.** In `engine-rig`'s deterministic mode
an `id` is `uuid5` over the row's content, i.e. a content address, so a repeated
id proves two byte-identical proposals rather than a rewrite — and appending a
line modifies nothing, which is all append-only forbids. Running a producer
twice into one file is legal under v0.1 and stays legal here.

A v0.1-legal row is v0.2-legal, and a v0.1-legal *file* is a v0.2-legal file.
The converse is false and is meant to be: a row using any v0.2 feature fails the
v0.1 validator loudly, which is better than a v0.1 consumer silently reading a
`deadlock_theorem` as an invariant.

Usage:
    python -m tools.validate_candidates_v02 <path> [<path> ...]
    python -m tools.validate_candidates_v02 --strict-basis <path>
"""

import json
import re
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

CONTRACT = "candidates_schema@0.2"
# A row may name the contract it was written against. v0.1 rows cannot (the key
# would be `unexpected`), so absent means "v0.1 or an unlabelled v0.2 row" and
# never "v0.1" on its own.
KNOWN_CONTRACTS = {"candidates_schema@0.1", "candidates_schema@0.2"}

REQUIRED_KEYS = {"id", "engine", "kind", "payload", "evidence", "status", "timestamp"}
OPTIONAL_KEYS = {"derived_from", "contract"}

ENGINES_V01 = {
    "mdl_segmenter",
    "cegis_miner",
    "zero_space",
    "lp_potential",
    "fd_adapter",
    "probe_frontier",
}
ENGINES_ADDED = {"deadlock_carver", "ic3_pdr"}
ENGINES = ENGINES_V01 | ENGINES_ADDED

KINDS_V01 = {
    "object_hypothesis",
    "rule_hypothesis",
    "invariant",
    "heuristic",
    "plan",
    "probe_design",
}
KINDS_ADDED = {"deadlock_theorem", "pruning_account"}
KINDS = KINDS_V01 | KINDS_ADDED

# The units a count can be in. Drawn from what the eight engines actually count
# today, not invented: every value here is some engine's emitted `coverage` or
# `transitions` argument.
#
# `expansions` and `generated_nodes` are separate because `deadlock_carver`'s
# pruning account divides one by the other — and by the numerator and
# denominator coming from *different runs*, at that. `basis.coverage` names the
# **denominator**, which is the part that decides whether two fractions are
# comparable; a numerator from elsewhere stays a payload matter.
BASES = {
    "transitions",
    "frames",
    "plan_steps",
    "ground_actions",
    "expansions",
    "generated_nodes",
    "states",
    "hypotheses",
    "moves",
    "edges",
}
BASIS_KEYS = {"transitions", "coverage"}

COVERAGE_RE = re.compile(r"^\d+/\d+$")


def _is_json_object(value: Any) -> bool:
    return isinstance(value, dict)


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        return False


def _valid_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_row(row: Any, where: str = "", strict_basis: bool = False) -> List[str]:
    """Errors in one row. Empty list means the row conforms to v0.2.

    `strict_basis` is off by default and is not part of the contract: it turns
    "no `evidence.basis`" into an error. A stream that has finished migrating
    can run with it on; the contract itself may not require it, because
    requiring it would make every v0.1 row illegal and this revision is
    additive.
    """
    prefix = ("%s: " % where) if where else ""
    errors: List[str] = []
    if not _is_json_object(row):
        return [prefix + "line is not a JSON object"]

    keys = set(row)
    for missing in sorted(REQUIRED_KEYS - keys):
        errors.append(prefix + "missing key %r" % missing)
    for extra in sorted(keys - REQUIRED_KEYS - OPTIONAL_KEYS):
        errors.append(prefix + "unexpected key %r" % extra)

    if "id" in row and not _valid_uuid(row["id"]):
        errors.append(prefix + "id is not a uuid: %r" % (row["id"],))

    if "engine" in row and row["engine"] not in ENGINES:
        errors.append(prefix + "engine not in the v0.2 enum: %r" % (row["engine"],))
    if "kind" in row and row["kind"] not in KINDS:
        errors.append(prefix + "kind not in the v0.2 enum: %r" % (row["kind"],))

    if "payload" in row and not _is_json_object(row["payload"]):
        errors.append(prefix + "payload is not a JSON object")

    if "status" in row and row["status"] != "candidate":
        errors.append(
            prefix + "status must be \"candidate\" (engines do not adjudicate), "
            "got %r" % (row["status"],))

    if "timestamp" in row and not _valid_timestamp(row["timestamp"]):
        errors.append(prefix + "timestamp is not ISO8601: %r" % (row["timestamp"],))

    errors.extend(_validate_evidence(row.get("evidence"), prefix, strict_basis)
                  if "evidence" in row else [])
    errors.extend(_validate_derived_from(row, prefix))

    if "contract" in row and row["contract"] not in KNOWN_CONTRACTS:
        errors.append(
            prefix + "contract is not one this validator knows: %r (known: %s)"
            % (row["contract"], sorted(KNOWN_CONTRACTS)))
    return errors


def _validate_evidence(evidence: Any, prefix: str, strict_basis: bool) -> List[str]:
    errors: List[str] = []
    if not _is_json_object(evidence):
        return [prefix + "evidence is not a JSON object"]

    transitions = evidence.get("transitions")
    if not isinstance(transitions, list):
        errors.append(prefix + "evidence.transitions is not a list")
    elif not all(isinstance(t, int) and not isinstance(t, bool) for t in transitions):
        errors.append(prefix + "evidence.transitions holds a non-integer")

    coverage = evidence.get("coverage")
    if not isinstance(coverage, str) or not COVERAGE_RE.match(coverage):
        errors.append(prefix + "evidence.coverage is not \"<k>/<n>\": %r" % (coverage,))
    else:
        k, n = (int(x) for x in coverage.split("/"))
        # Both rules are v0.1's, kept exactly. Dropping the zero-denominator one
        # would bless a row on which a consumer's `k / n` raises, and this
        # revision is not allowed to change what an existing field may hold.
        if n == 0:
            errors.append(prefix + "evidence.coverage denominator is zero")
        elif k > n:
            errors.append(
                prefix + "evidence.coverage %r has a numerator above its "
                "denominator" % (coverage,))

    extra = set(evidence) - {"transitions", "coverage", "basis"}
    for key in sorted(extra):
        errors.append(prefix + "unexpected key %r in evidence" % key)

    if "basis" in evidence:
        basis = evidence["basis"]
        if not _is_json_object(basis):
            errors.append(
                prefix + "evidence.basis is not a JSON object; it names the units "
                "of `transitions` and of `coverage` separately, because a row "
                "may legitimately count them differently")
        else:
            for key in sorted(set(basis) - BASIS_KEYS):
                errors.append(prefix + "unexpected key %r in evidence.basis" % key)
            for key in sorted(set(basis) & BASIS_KEYS):
                if basis[key] not in BASES:
                    errors.append(
                        prefix + "evidence.basis.%s is not one of %s: %r"
                        % (key, sorted(BASES), basis[key]))
    elif strict_basis:
        errors.append(
            prefix + "evidence.basis is absent and --strict-basis is on. The "
            "contract makes this field optional; absent means \"the basis is "
            "whatever this engine's README says\".")
    return errors


def _validate_derived_from(row: dict, prefix: str) -> List[str]:
    """`derived_from` is ids, may be empty, and may not name the row itself.

    What is deliberately **not** checked: that the ids appear in this file. A
    stream can legitimately be split, merged, or shipped in pieces, and a
    reference into a sibling file is the normal case rather than an error. What
    a validator can decide locally is the shape and the self-reference; a
    resolver is a different tool with a different input.
    """
    if "derived_from" not in row:
        return []
    value = row["derived_from"]
    if not isinstance(value, list):
        return [prefix + "derived_from is not a list of ids"]
    errors = []
    for item in value:
        if not _valid_uuid(item):
            errors.append(prefix + "derived_from holds a non-uuid: %r" % (item,))
        elif "id" in row and str(item) == str(row["id"]):
            errors.append(prefix + "derived_from names the row's own id")
    return errors


def validate_stream(lines: Iterable[str], where: str = "",
                    strict_basis: bool = False) -> List[str]:
    errors: List[str] = []
    for number, line in enumerate(lines, start=1):
        label = "%s:%d" % (where, number) if where else "line %d" % number
        if not line.strip():
            # v0.1's rule, kept: one object per line, so a blank line is a
            # malformed stream and not whitespace to be tolerated.
            errors.append("%s: blank line (the stream is one object per line)"
                          % label)
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append("%s: not valid JSON (%s)" % (label, exc))
            continue
        errors.extend(validate_row(row, label, strict_basis=strict_basis))
    return errors


def validate_file(path: str, strict_basis: bool = False) -> List[str]:
    with open(path, encoding="utf-8") as handle:
        return validate_stream(handle, where=path, strict_basis=strict_basis)


USAGE = ("usage: python -m tools.validate_candidates_v02 [--strict-basis] "
         "<path> [<path> ...]")


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    flags = [a for a in args if a.startswith("--")]
    # A mistyped flag must not run the check in the mode the caller did not
    # ask for and then report OK — a silent lax pass reads exactly like a
    # passing strict one.
    unknown = [f for f in flags if f != "--strict-basis"]
    if unknown:
        print("unknown option(s): %s\n%s" % (" ".join(unknown), USAGE),
              file=sys.stderr)
        return 2
    strict_basis = "--strict-basis" in flags
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print(USAGE, file=sys.stderr)
        return 2

    total = 0
    failed = False
    for path in paths:
        errors = validate_file(path, strict_basis=strict_basis)
        with open(path, encoding="utf-8") as handle:
            rows = sum(1 for line in handle if line.strip())
        total += rows
        if errors:
            failed = True
            for error in errors:
                print(error, file=sys.stderr)
    if failed:
        print("FAIL (%s, %d row(s) read)" % (CONTRACT, total))
        return 1
    print("OK (%s, %d row(s))" % (CONTRACT, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
