"""External adjudications over recorded campaign cells.

A budget gate that the spending session can talk itself out of is not a gate.
But a gate that has fired on evidence which an outside reviewer has since ruled
non-representative is not a gate either -- it is a permanent stop. This module
is the narrow, auditable channel between those two failures.

An adjudication is a record that says: *these named cells are not evidence about
the arm, for this stated reason, decided by this named authority, and it
suspends exactly this one gate clause.* Three properties make it safe:

  * **It cannot move a threshold.** Nothing here changes a cap. The only thing
    an adjudication can do is remove named cells from one clause's input.
  * **It cannot suspend a spend clause.** `SUSPENDABLE` is an allowlist holding
    `G4` and nothing else. G1/G1b/G2 (money), G6a/G6b (time) and G7 (sealed-pile
    contact) are structurally out of reach -- an adjudication naming them raises
    rather than being quietly ignored. Money that was spent stays spent no
    matter who reviews it.
  * **It cannot absorb the future.** Cells are named by `run_id`, one by one.
    There is no game-level or pattern rule, so an adjudication written today
    cannot silently swallow a cell recorded tomorrow.

`BUDGET_REPORT.md` section 11.3 records the thing this exists to prevent: raising
`actions_failed >= 10` until the gate turned green would have made the campaign
finish and the report look good, at the price of muting a real signal. The
distinction this module draws is between *muting the signal* and *recording that
someone with standing looked at the signal and ruled on it* -- the second is
allowed, in writing, with the ruling visible in `campaign_gate.json`.

The file is append-only, like every other record surface on this track. A
mistaken adjudication is corrected by appending a `revoked` record, never by
editing.
"""

import json
import os
from typing import Any, Dict, Iterable, List, Optional

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(TRACK, "out")
ADJUDICATIONS_PATH = os.path.join(OUT_DIR, "campaign_adjudications.jsonl")

# The allowlist. Widening it is a code change with a diff and a reviewer, which
# is the whole point -- see the module docstring and BUDGET_REPORT.md 11.3.
SUSPENDABLE = ("G4",)

KINDS = ("degraded", "revoked")


class AdjudicationError(ValueError):
    """A malformed or over-reaching adjudication. Raised, never warned."""


def validate(record: Dict[str, Any]) -> Dict[str, Any]:
    """Structural check. Returns the record so callers can validate-and-use."""
    required = ("kind", "finding", "authority", "recorded_at", "recorded_by",
                "run_ids", "scope", "reason", "evidence")
    missing = [k for k in required if k not in record]
    if missing:
        raise AdjudicationError("adjudication is missing %s" % ", ".join(missing))

    if record["kind"] not in KINDS:
        raise AdjudicationError("kind must be one of %s, got %r"
                                % (KINDS, record["kind"]))

    run_ids = record["run_ids"]
    if not isinstance(run_ids, list) or not run_ids:
        raise AdjudicationError("run_ids must be a non-empty list")
    for rid in run_ids:
        if not isinstance(rid, str) or not rid:
            raise AdjudicationError("run_ids must be non-empty strings, got %r" % (rid,))
        if any(ch in rid for ch in "*?["):
            raise AdjudicationError(
                "run_ids are named one by one; %r looks like a pattern. A rule "
                "that matches cells not yet recorded would let one ruling absorb "
                "future evidence." % rid)
    if len(set(run_ids)) != len(run_ids):
        raise AdjudicationError("run_ids contains duplicates")

    scope = record["scope"]
    if not isinstance(scope, list) or not scope:
        raise AdjudicationError("scope must be a non-empty list of gate clause ids")
    for clause in scope:
        if clause not in SUSPENDABLE:
            raise AdjudicationError(
                "clause %r is not suspendable. Only %s may be adjudicated; the "
                "spend clauses (G1/G1b/G2), the clocks (G6a/G6b) and the "
                "sealed-pile clause (G7) never can be."
                % (clause, ", ".join(SUSPENDABLE)))

    if not isinstance(record["evidence"], list) or not record["evidence"]:
        raise AdjudicationError("evidence must be a non-empty list of citations")
    if record["authority"] == "baseline-arms":
        raise AdjudicationError(
            "a track cannot adjudicate its own gate; authority must name an "
            "outside reviewer (e.g. 'monitor')")
    return record


def append(record: Dict[str, Any], path: str = ADJUDICATIONS_PATH) -> Dict[str, Any]:
    validate(record)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
    return record


def load(path: str = ADJUDICATIONS_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(validate(json.loads(line)))
    return out


def suspended(clause: str,
              records: Optional[Iterable[Dict[str, Any]]] = None,
              path: str = ADJUDICATIONS_PATH) -> Dict[str, Dict[str, Any]]:
    """`run_id` -> the adjudication that removes it from `clause`'s input.

    A later `revoked` record naming the same run_id and clause puts the cell
    back. Order in the file is the order of decision.
    """
    if clause not in SUSPENDABLE:
        return {}
    records = list(load(path) if records is None else records)
    out: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        if clause not in rec["scope"]:
            continue
        for rid in rec["run_ids"]:
            if rec["kind"] == "degraded":
                out[rid] = rec
            elif rec["kind"] == "revoked":
                out.pop(rid, None)
    return out
