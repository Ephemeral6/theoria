"""Which refusals are the upstream breathing, and which are this arm being wrong.

87% of the live commands this arm has ever sent came back `400 SERVER_ERROR`
with the detail `game <id> not found`. Nobody treated that as a defect, and
nobody was wrong to: it is not one. But the ledger recorded it identically to a
genuine failure, and three things went quietly bad as a result.

## What the records actually say

Across the four live legs of 2026-07-31 -- 570 `env_step` rows, two games,
four and a half hours -- 494 rows are `400` / `SERVER_ERROR` /
`game <id> not found`, with `frames: null` and `n_frames: 0`. The other 76 are
`200`. The refusal rate per leg is 0.900 / 0.859 / 0.855 / 0.876: stable across
two different games and across hours, which is not the shape of a client that
is malformed (that would be 100%) nor of a flaky network (that would wander).

The decisive record is that the request is **byte-identical across the split**.
On `20260731T1240Z-A3-level2-carried` all eleven `RESET` rows carry
`request_sha256: sha256:726d8f3e...`; ten are `400` and the eleventh is `200`
and returns a full frame and a `guid`. Same body, same URL
(`https://three.arcprize.org/api/cmd/RESET`), same injected headers, same
`card_id`. Nothing on this side varies between the refusal and the success, so
nothing on this side causes the refusal.

The four hypotheses the diagnosis had to kill, and the record that killed each:

* **malformed game id** -- no. The closing scorecard for that same leg lists
  the environment `g50t-5849a774` with `level_count: 7`, a `guid`, and five
  actions. The server knows the id perfectly well.
* **sent before RESET** -- no. `step_idx 0` is a `RESET`, and it is refused.
* **missing session or scorecard token** -- no. The refusals after `step_idx 10`
  carry the same `guid` (`30be5721-...`) as the successes interleaved with them.
* **a race with scorecard open** -- no. The `scorecard/open` at `seq 2` returned
  `200` a full two seconds before the first refused command, and refusals
  continue for the following five minutes.

What is left is the upstream. The API's own error name for it is
`SERVER_ERROR`, which is the upstream saying so in its own words.

## So it is expected behaviour, and the defect is the recording

This arm already knows. `harness/arc.py:_retryable` returns True for a `400`
whose message contains `not found`, and retries up to `ACTION_ATTEMPTS`. The
retry works -- that is why 72 actions landed. Three costs follow from the
recording, not from the condition:

* **`proxy/ledger.py:_next_step` gives every refused attempt its own
  `step_idx`.** `step_idx` therefore counts attempts, not actions. `step_idx 0`
  is a refusal in all four legs, which is why the replay spot-check returned an
  empty answer rather than a wrong one -- it looked for a session that begins
  with a `RESET` frame and there is no such index.
* **the archive could not tell the two apart.** `reconcile()` computed
  `http_amplification = env_steps / successful_actions` over an undifferentiated
  mass of non-200 rows, so a leg dominated by the transient wave and a leg
  dominated by real breakage produced the same number.
* **the sizing constant inherited it.** `harness/spend.py:OUTBOUND_PER_ACTION`
  is 9.3, from 251 outbound / 27 successful actions. That arithmetic reproduces
  exactly from the ledgers; the trouble is that 224 of those 251 requests are
  the transient wave, so the constant describes an upstream weather system and
  is applied as though it described this arm's transport.

This module is the distinction, made computable. It does not change what the
arm does on the wire -- retrying is the correct response and it already
happens. It changes what the record says happened, so that the two cases stop
being the same row.

## The signature, and why every conjunct is load-bearing

`upstream_transient` requires *all* of:

1. the request was forwarded (`http.forwarded` is true) -- an unforwarded row is
   this proxy's own refusal and has nothing to do with the upstream;
2. `http.status == 400`;
3. `response.error == "SERVER_ERROR"` -- the upstream's own name for it;
4. `response.message` is exactly `game <id> not found` where `<id>` is **this
   row's own `game_id`**;
5. no frames came back (`n_frames` falsy and `frames` null).

Conjunct 4 is the one that earns its keep. `"not found"` on its own is not the
signature, and the ledgers prove it: the same four legs contain
`scorecard <redacted:key-shaped> not found` with `error: VALIDATION_ERROR` on a
`404` -- a card that had auto-closed server-side, which is a real and
consequential failure. `harness/arc.py:_retryable` matches `"not found"` in any
`400` message, which is broader than this signature deliberately: this module
is for accounting after the fact, where a false positive silently launders a
real failure into weather, and the retry predicate is for the wire, where a
false negative costs a leg. They are allowed to differ; they are not allowed to
be confused, so both are stated here.

Conjunct 4 also catches the one client-side defect that *would* look like this
wave from a distance: a message naming a game the row did not ask for means the
id really was wrong, and that must not be filed as weather. There is no such
row in any ledger today. The check exists so that if one ever appears it is
classified as `upstream_failure` and shows up as a failure.

    cd theoria-arm && python -m armtools.refusal runs/<leg>
"""

import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

__all__ = (
    "OUTCOMES",
    "TRANSIENT_ERROR",
    "TRANSIENT_MESSAGE",
    "classify",
    "partition",
    "outbound_accounting",
)

#: The upstream's own error name for the wave. A `400` carrying any other
#: `error` is not this condition.
TRANSIENT_ERROR = "SERVER_ERROR"

#: `game <id> not found`, anchored, with the id captured so it can be checked
#: against the row's own `game_id`. Anchored on purpose: a message that merely
#: contains this phrase is not the same as a message that is it.
TRANSIENT_MESSAGE = re.compile(r"^game\s+(?P<game_id>\S+)\s+not found\s*$", re.I)

#: Every value `classify` can return. A closed set, so a caller can exhaust it
#: and a test can assert the partition sums to the row count.
OUTCOMES = frozenset({
    "success",             # forwarded, 200
    "upstream_transient",  # forwarded, the documented `game <id> not found` wave
    "upstream_failure",    # forwarded, non-200, and not the wave
    "unrecorded",          # forwarded, non-200, and the ledger kept no body
    "guard_refused",       # never forwarded: the sealed-pile guard said no
    "variant_refused",     # never forwarded: an ablation variant declined
})


def _http(record: Dict[str, Any]) -> Dict[str, Any]:
    value = record.get("http")
    return value if isinstance(value, dict) else {}


def _response(record: Dict[str, Any]) -> Dict[str, Any]:
    value = record.get("response")
    return value if isinstance(value, dict) else {}


def classify(record: Dict[str, Any]) -> str:
    """Which of `OUTCOMES` this `env_step` row is.

    Total over the five outcomes: a row that matches nothing more specific is
    `upstream_failure`, never `None` and never a sixth bucket invented at the
    call site. A classifier that can return "I don't know" grows an "unknown"
    column that nobody reads, and the whole point here is that unexplained rows
    stay visible as failures.
    """
    http = _http(record)
    status = http.get("status")

    if not http.get("forwarded"):
        # Nothing left this process. `_deny` writes 403 for the sealed-pile
        # guard; a variant's `Refusal` carries whatever status it chose.
        guard = record.get("guard")
        if isinstance(guard, dict) and guard.get("decision") == "deny":
            return "guard_refused"
        if status == 403:
            return "guard_refused"
        return "variant_refused"

    if status == 200:
        return "success"

    # An error row whose body the ledger never kept cannot be classified, and
    # saying "failure" about it would be a claim the record does not support.
    # Three of this arm's live legs predate `_command` recording `rest`: they
    # carry `response: null` on every row, 200s included. They are unanswerable,
    # not failed, and they are counted so that the size of the blind spot is
    # visible instead of being absorbed into a failure tally.
    if record.get("response") is None:
        return "unrecorded"

    if status != 400:
        return "upstream_failure"

    response = _response(record)
    if response.get("error") != TRANSIENT_ERROR:
        return "upstream_failure"

    match = TRANSIENT_MESSAGE.match(str(response.get("message") or ""))
    if not match:
        return "upstream_failure"

    # The message must name the game this row asked about. If it names another
    # one, the id really was wrong and that is a client defect, not weather.
    if match.group("game_id") != record.get("game_id"):
        return "upstream_failure"

    # A refusal that nonetheless returned frames is not a refusal. Contradictory
    # rows are failures, so that the contradiction is looked at.
    if record.get("n_frames") or record.get("frames"):
        return "upstream_failure"

    return "upstream_transient"


def _steps(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in records if r.get("event") == "env_step"]


def partition(records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    """Count of `env_step` rows by outcome. Every outcome present, including
    the zeroes -- a bucket that vanishes when empty cannot be seen to be
    empty, and "no real failures" is exactly the claim a reader needs to be
    able to check."""
    counts = {name: 0 for name in sorted(OUTCOMES)}
    for record in _steps(records):
        counts[classify(record)] += 1
    return counts


def outbound_accounting(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Outbound ARC requests, split by what they bought.

    The unit is the one the spend pool charges: one outbound HTTP request, which
    is `http.attempts` on a forwarded row (`proxy/env_proxy.py:_charge` records
    `permit.attempts_made`). Rows that never reached the wire contribute
    nothing, because the pool was never asked to pay for them.

    Three ratios come out, and they are reported together on purpose:

    * `outbound_per_action` -- the blended number, and the one
      `OUTBOUND_PER_ACTION` is. It is what the pool is actually asked for while
      the wave is running.
    * `outbound_per_action_productive` -- what the same leg would have cost with
      the wave subtracted. This is the transport's own ratio.
    * `transient_share` -- the fraction of outbound spend that bought nothing.

    Reporting only the first is what let a weather constant pass as a transport
    constant for three days. Reporting only the second would under-reserve, and
    under-reserving cost `20260729T004020Z-leg01` its run.

    `scorecard_actions` is the independent witness: the API's own count of what
    it charged. Where a closed scorecard exists it should equal
    `successful_actions`, and `archive.reconcile` already checks that. It is
    carried here so that `charged_upstream` is not this arm marking its own
    homework.
    """
    steps = _steps(records)
    kinds = {name: [] for name in sorted(OUTCOMES)}
    for record in steps:
        kinds[classify(record)].append(record)

    def outbound(rows: List[Dict[str, Any]]) -> int:
        return sum(int(_http(r).get("attempts") or 0)
                   for r in rows if _http(r).get("forwarded"))

    def actions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r for r in rows
                if (r.get("action") or {}).get("name") != "RESET"]

    successes = kinds["success"]
    successful_actions = actions(successes)

    total_outbound = sum(outbound(rows) for rows in kinds.values())
    transient_outbound = outbound(kinds["upstream_transient"])
    failure_outbound = outbound(kinds["upstream_failure"])
    unrecorded_outbound = outbound(kinds["unrecorded"])
    productive_outbound = outbound(successes)

    # ACTION-only view, which is the denominator `OUTBOUND_PER_ACTION` uses.
    action_rows = actions(steps)
    action_outbound = sum(
        int(_http(r).get("attempts") or 0)
        for r in action_rows if _http(r).get("forwarded"))
    n_actions = len(successful_actions)

    def ratio(numerator: int) -> Optional[float]:
        return round(numerator / n_actions, 3) if n_actions else None

    out: Dict[str, Any] = {
        "env_steps": len(steps),
        "partition": {name: len(rows) for name, rows in kinds.items()},
        "outbound_total": total_outbound,
        "outbound_productive": productive_outbound,
        "outbound_transient_retry": transient_outbound,
        "outbound_failed": failure_outbound,
        "outbound_unrecorded": unrecorded_outbound,
        "outbound_action_only": action_outbound,
        "successful_actions": n_actions,
        "resets_ok": len(successes) - n_actions,
        "outbound_per_action": ratio(action_outbound),
        "outbound_per_action_productive": ratio(outbound(actions(successes))),
        "transient_share": (round(transient_outbound / total_outbound, 4)
                            if total_outbound else None),
        "charged_upstream": n_actions,
        "uncharged_upstream": len(kinds["upstream_transient"]),
        # False when any error row has no body: the split between weather and
        # real breakage is then not derivable from this leg at any confidence,
        # and a caller must not read `transient_share` as though it were.
        "decomposable": not kinds["unrecorded"],
    }
    return out


def derive_outbound_per_action(legs: Dict[str, List[Dict[str, Any]]]
                               ) -> Dict[str, Any]:
    """Re-derive `harness/spend.py:OUTBOUND_PER_ACTION` from the ledgers.

    `legs` maps a leg name to its records. The numerator is outbound ARC
    requests on ACTION rows that were **forwarded** -- the unit the pool
    charges, counted only where a socket was actually opened -- and the
    denominator is ACTION rows the upstream answered 200. That is the same
    arithmetic the published constant claims, and it reproduces it exactly
    (251/27 = 9.296 over the four legs the provenance names).

    What is added is the split. The published 9.3 is a blend of two regimes
    that happen to be recorded identically, and the blend is 93% weather:

    * `blended` -- what the pool is asked for while the wave is running.
    * `productive` -- the same legs with the wave subtracted; this arm's
      transport on its own.
    * `decomposable_legs` -- how many legs the split could actually be computed
      on. This is the number that stops the result being oversold. Three of the
      four legs behind 9.3 predate the proxy recording response bodies, so for
      them the split is not derivable at all and they contribute to `blended`
      while contributing nothing to `productive`.

    The published constant is deliberately *not* recomputed downward from this.
    Over-reserving returns its unspent hold; under-reserving cost
    `20260729T004020Z-leg01` its run. What this function exists for is that the
    number now has a derivation a test can run, instead of a literal a comment
    asserts.
    """
    totals = {"outbound_action_forwarded": 0, "successful_actions": 0,
              "outbound_transient": 0, "outbound_productive": 0,
              "outbound_unrecorded": 0}
    per_leg: Dict[str, Any] = {}
    decomposable = 0

    for name, records in legs.items():
        report = outbound_accounting(records)
        per_leg[name] = {
            "outbound_action_only": report["outbound_action_only"],
            "successful_actions": report["successful_actions"],
            "ratio": report["outbound_per_action"],
            "decomposable": report["decomposable"],
        }
        totals["outbound_action_forwarded"] += report["outbound_action_only"]
        totals["successful_actions"] += report["successful_actions"]
        totals["outbound_transient"] += report["outbound_transient_retry"]
        totals["outbound_productive"] += report["outbound_productive"]
        totals["outbound_unrecorded"] += report["outbound_unrecorded"]
        decomposable += 1 if report["decomposable"] else 0

    actions = totals["successful_actions"]
    classifiable = totals["outbound_transient"] + totals["outbound_productive"]
    return {
        "per_leg": per_leg,
        "legs": len(legs),
        "decomposable_legs": decomposable,
        "outbound_action_forwarded": totals["outbound_action_forwarded"],
        "successful_actions": actions,
        "blended": (round(totals["outbound_action_forwarded"] / actions, 3)
                    if actions else None),
        "productive": (round(totals["outbound_productive"] / actions, 3)
                       if actions else None),
        "outbound_transient": totals["outbound_transient"],
        "outbound_unrecorded": totals["outbound_unrecorded"],
        "transient_share_of_classifiable": (
            round(totals["outbound_transient"] / classifiable, 4)
            if classifiable else None),
    }


def _scorecard(records: Iterable[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    found = None
    for record in records:
        if record.get("event") == "env_meta":
            response = _response(record)
            if response.get("environments"):
                found = response
    return found


def main(argv: List[str]) -> int:
    from proxy.ledger import read_ledger

    if not argv:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2

    pooled: Dict[str, Any] = {}
    for target in argv:
        path = (target if target.endswith(".jsonl")
                else os.path.join(target, "ledger.jsonl"))
        if not os.path.exists(path):
            print("no ledger: %s" % path, file=sys.stderr)
            return 2
        records = read_ledger(path)
        report = outbound_accounting(records)
        scorecard = _scorecard(records)
        if scorecard is not None:
            report["scorecard_actions"] = scorecard.get("total_actions")
        print(json.dumps({"leg": target, **report}, sort_keys=True))
        for key in ("outbound_total", "outbound_transient_retry",
                    "outbound_productive", "successful_actions"):
            pooled[key] = pooled.get(key, 0) + (report[key] or 0)

    if len(argv) > 1:
        actions = pooled["successful_actions"]
        pooled["outbound_per_action"] = (
            round(pooled["outbound_total"] / actions, 3) if actions else None)
        pooled["transient_share"] = (
            round(pooled["outbound_transient_retry"] / pooled["outbound_total"], 4)
            if pooled["outbound_total"] else None)
        print(json.dumps({"leg": "POOLED", **pooled}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
