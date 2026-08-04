"""What S47's body predicate would have done to the four live legs of 2026-07-31.

`forward()` gained a `retry_body` predicate and `env_proxy` gained
`game_not_found_retry`. The claim being made for them is an accounting claim:
the `game <id> not found` wave stops buying one `env_step` row per attempt,
because the retry now happens inside one `forward()` call instead of above the
proxy in `theoria-arm/harness/arc.py`. 570 rows bought 72 actions across four
legs, and 494 of those rows are the wave.

A claim about rows can be checked against rows. This tool replays the four
archived ledgers through the **real** predicate and reports what the ledger
would have looked like -- and, in the same breath, that the two things which
must not move did not move:

  * **`sockets_unchanged`.** The change moves rows, not sockets. Every archived
    attempt is still consumed by exactly one simulated request, so the outbound
    request count -- the unit the spend pool charges -- is identical before and
    after. A "saving" here would mean the simulation had dropped an attempt the
    upstream really answered, which is a bug in the simulation and not a
    result.
  * **`actions_agree`.** Recomputed, not asserted, on the simulated row set:
    `scorecard.total_actions == len(200 && non-RESET rows)`
    (`theoria-arm/armtools/archive.py:178`, with the scorecard located the way
    `theoria-arm/armtools/refusal.py:_scorecard` locates it -- the response of
    the last `env_meta` row carrying `environments`). If collapsing the wave
    changed which rows count as landed actions, the collapse is wrong.

## It drives the shipped predicate, not a copy of it

`game_not_found_retry` is imported and called. A regex re-typed into this file
would prove that this file agrees with itself. The predicate is fed
`(status, headers, body_bytes)` exactly as `forward()` feeds it:
`status = row["http"]["status"]`, `headers = {}`, and
`body_bytes = json.dumps(row["response"]).encode()`.

**Stated limitation.** The ledger's `response` is the parsed body with `frame`
removed (`proxy/env_proxy.py:_command` writes `rest`), so re-serialising it is
not the byte stream the upstream sent. It is faithful for *this* predicate,
which reads only `error` and `message` and neither of which is `frame`; it
would not be faithful for a predicate that cared about byte order, whitespace,
or a field the ledger drops. Nothing here can tell you what a future predicate
would have done to these legs.

## The collapse model is `forward()`'s loop, not an idealisation

`forward()` retries up to `max_attempts` times and then returns whatever the
last attempt said. So a run of K wave refusals does **not** become one row when
K exceeds the budget: the proxy gives up, the arm sees a refusal, the arm
retries, and that is a second row. The simulation walks the leg's `env_step`
rows in `seq` order and consumes them the way the loop would:

  * a simulated request consumes successive archived attempts while the
    predicate calls each one retryable, up to `max_attempts` attempts;
  * the first attempt the predicate does not call retryable is consumed too and
    is the emitted row's final status -- that is the response `forward()`
    returns;
  * a request emitted because the budget ran out while still retryable is
    followed by another simulated request over the remaining attempts, because
    the arm retries what the proxy gave up on.

An archived row's own `http.attempts` is what it costs against the budget, so a
row that was already retried internally (on a `RETRY_STATUSES` status line)
costs what it really cost. In these four legs every row is `attempts: 1`.

Two rules that are not in the loop but are in the data:

  * a row that was never forwarded (a guard or variant refusal) is never
    retryable and cannot be a continuation of an earlier attempt -- nothing left
    the process, so there was no upstream answer to retry;
  * consuming stops at the end of the leg.

A stricter variant of the model was checked by hand: requiring that a
continuation attempt carry the same `request_sha256` and action name as the
attempt before it, since the proxy replays a byte-identical body. On these four
legs it gives the identical answer, so the simpler rule above is not hiding a
merge across two different commands.

## Cost

Zero network, zero spend, zero API calls, zero actions. It opens no socket,
calls no `forward()`, mints no permit and touches no `SpendGate`. It reads
JSONL files and calls one pure function.

    python -m proxy.tools.refusal_replay \
        --leg theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl \
        --leg theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl \
        --leg theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl \
        --leg theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/ledger.jsonl \
        --verify -o report.json
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from ..env_proxy import game_not_found_retry
from ..ledger import read_ledger

#: The pooled numbers `armtools/refusal.py` publishes for the four 2026-07-31
#: legs. `--verify` asserts them so that a moved archive is a loud failure
#: rather than a quietly different answer to the same question.
PUBLISHED = {"env_steps": 570, "wave_attempts": 494, "total_actions": 72}

#: A sweep, so the report answers "how many rows for which budget?" rather than
#: only "how many rows for the default?". `max_attempts` is a proxy
#: configuration knob (`EnvProxyConfig.max_attempts`, default 5), and the row
#: count is a function of it, not a constant.
SWEEP = (1, 2, 3, 4, 5, 6, 8, 10, 16)


def _http(record: Dict[str, Any]) -> Dict[str, Any]:
    value = record.get("http")
    return value if isinstance(value, dict) else {}


def env_steps(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The leg's `env_step` rows in `seq` order.

    `seq` and not `step_idx`: `step_idx` counts command rows only, while `seq`
    is the ledger's own append order and is what "the next attempt" means.
    """
    steps = [r for r in records if r.get("event") == "env_step"]
    steps.sort(key=lambda r: r.get("seq") or 0)
    return steps


def scorecard(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The run's closing scorecard, located exactly as
    `theoria-arm/armtools/refusal.py:_scorecard` locates it: the `response` of
    the **last** `env_meta` row whose response carries `environments`."""
    found = None
    for record in records:
        if record.get("event") == "env_meta":
            response = record.get("response")
            if isinstance(response, dict) and response.get("environments"):
                found = response
    return found


def attempts_of(record: Dict[str, Any]) -> int:
    """What this archived row cost in outbound requests.

    `http.attempts` is what `_charge` billed the pool (`permit.attempts_made`),
    so it is the right unit and the only one. A row missing the field is
    counted as one; a row that never went out is counted as zero, because the
    pool was never asked to pay for it.
    """
    http = _http(record)
    if not http.get("forwarded"):
        return 0
    return int(http.get("attempts") or 1)


def is_wave(record: Dict[str, Any]) -> bool:
    """Whether the shipped predicate would have retried this archived attempt.

    This is the whole point of the tool: `game_not_found_retry` is the function
    `env_proxy` hands to `forward()`, called here with the arguments `forward()`
    calls it with. `headers` is `{}` -- the predicate does not read them and the
    ledger does not keep them, and inventing a plausible header block would be
    inventing evidence.
    """
    http = _http(record)
    if not http.get("forwarded"):
        # Nothing left the process, so there is no upstream answer to retry.
        return False
    predicate = game_not_found_retry(record.get("game_id"))
    if predicate is None:
        return False
    # The ledger's `response` is the parsed body minus `frame`; see the module
    # docstring for why re-serialising it is faithful for this predicate and
    # only for this predicate.
    body = json.dumps(record.get("response")).encode("utf-8")
    return bool(predicate(http.get("status"), {}, body))


def simulate(steps: List[Dict[str, Any]], max_attempts: int
             ) -> List[Dict[str, Any]]:
    """The `env_step` rows the new `forward()` would have written.

    One entry per simulated proxy request: the archived row whose status the
    request would have returned, how much of the budget it burned, how many
    outbound requests that really was, and why it stopped. `budget` means the
    predicate still wanted to retry and the loop was out of attempts -- the case
    that keeps this a simulation of `forward()` rather than a wish about it.

    `budget_used` and `sockets` differ only for an unforwarded row, which costs
    a turn of the loop but opened nothing. Keeping them apart is what lets
    `sockets_unchanged` be recomputed from the simulation instead of copied off
    the archive.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    emitted: List[Dict[str, Any]] = []
    index = 0
    while index < len(steps):
        used = 0
        sockets = 0
        cursor = index
        final: Optional[Dict[str, Any]] = None
        reason = "budget"
        while cursor < len(steps):
            row = steps[cursor]
            cost = max(attempts_of(row), 1)     # a consumed row is an attempt
            if used and used + cost > max_attempts:
                break                           # the loop is out of attempts
            if used and not _http(row).get("forwarded"):
                # An unforwarded row is this proxy refusing, not the upstream
                # answering; it cannot be the continuation of a retry.
                break
            used += cost
            sockets += attempts_of(row)
            cursor += 1
            final = row
            if not is_wave(row):
                reason = "terminal"
                break
            if used >= max_attempts:
                break
        emitted.append({"final": final, "budget_used": used, "sockets": sockets,
                        "rows_consumed": cursor - index, "reason": reason})
        index = cursor
    return emitted


def _actions_agree(rows: List[Dict[str, Any]],
                   card: Optional[Dict[str, Any]]) -> Tuple[Optional[bool], int]:
    """`archive.py:178`, recomputed over whatever row set it is handed.

    Returns the verdict and the successful-action count. `None` when the leg
    has no scorecard: there is then nothing to agree with, and reporting `False`
    would be reporting a disagreement that nobody had.
    """
    landed = [r for r in rows
              if _http(r).get("status") == 200
              and (r.get("action") or {}).get("name") != "RESET"]
    if card is None:
        return None, len(landed)
    return card.get("total_actions") == len(landed), len(landed)


def replay_records(records: List[Dict[str, Any]], max_attempts: int,
                   leg: str = "-", path: Optional[str] = None) -> Dict[str, Any]:
    """One leg's report, from records already in memory.

    Split out from `replay_leg` so the simulator can be tested on synthetic
    rows. The archives are four files on one machine; a test that can only run
    where they are is a test that stops running.
    """
    steps = env_steps(records)
    card = scorecard(records)
    emitted = simulate(steps, max_attempts)
    after_rows = [e["final"] for e in emitted if e["final"] is not None]

    agree_before, landed_before = _actions_agree(steps, card)
    agree_after, landed_after = _actions_agree(after_rows, card)

    outbound_before = sum(attempts_of(r) for r in steps)
    # Summed off the simulation, not off the archive: the equality of these two
    # is the invariant under test, so deriving one from the other would test
    # nothing.
    outbound_after = sum(e["sockets"] for e in emitted)
    consumed_rows = sum(e["rows_consumed"] for e in emitted)

    report: Dict[str, Any] = {
        "leg": leg,
        "path": path,
        "max_attempts": max_attempts,
        "env_steps_before": len(steps),
        "env_steps_after": len(emitted),
        "wave_attempts": sum(1 for r in steps if is_wave(r)),
        "outbound_attempts_before": outbound_before,
        "outbound_attempts_after": outbound_after,
        "sockets_unchanged": outbound_before == outbound_after,
        "actions_agree_before": agree_before,
        "actions_agree_after": agree_after,
        "scorecard_total_actions": None if card is None else card.get("total_actions"),
        "successful_actions": landed_after,
        "successful_actions_before": landed_before,
        "rows_out_of_budget": sum(1 for e in emitted if e["reason"] == "budget"),
        "longest_collapse": max((e["rows_consumed"] for e in emitted), default=0),
        # Every archived row is consumed by exactly one simulated request. If
        # this ever disagrees with `env_steps_before`, the walk dropped or
        # double-counted an attempt and no other number here can be trusted.
        "rows_consumed": consumed_rows,
        "env_steps_after_by_max_attempts": {
            str(budget): len(simulate(steps, budget)) for budget in SWEEP},
    }
    return report


def replay_leg(path: str, max_attempts: int) -> Dict[str, Any]:
    """One leg's report, read off disk. Read-only: it opens the ledger and
    writes nothing back."""
    return replay_records(
        read_ledger(path), max_attempts,
        leg=os.path.basename(os.path.dirname(os.path.abspath(path))),
        path=path)


def _pool(legs: List[Dict[str, Any]], max_attempts: int) -> Dict[str, Any]:
    def total(key: str) -> int:
        return sum(leg[key] or 0 for leg in legs)

    def every(key: str) -> Optional[bool]:
        values = [leg[key] for leg in legs if leg[key] is not None]
        return all(values) if values else None

    outbound_before = total("outbound_attempts_before")
    outbound_after = total("outbound_attempts_after")
    sweep = {str(budget): sum(leg["env_steps_after_by_max_attempts"][str(budget)]
                              for leg in legs) for budget in SWEEP}
    return {
        "legs": len(legs),
        "max_attempts": max_attempts,
        "env_steps_before": total("env_steps_before"),
        "env_steps_after": total("env_steps_after"),
        "wave_attempts": total("wave_attempts"),
        "outbound_attempts_before": outbound_before,
        "outbound_attempts_after": outbound_after,
        "sockets_unchanged": outbound_before == outbound_after,
        "actions_agree_before": every("actions_agree_before"),
        "actions_agree_after": every("actions_agree_after"),
        "scorecard_total_actions": total("scorecard_total_actions"),
        "successful_actions": total("successful_actions"),
        "rows_consumed": total("rows_consumed"),
        "rows_out_of_budget": total("rows_out_of_budget"),
        "env_steps_after_by_max_attempts": sweep,
        "row_reduction": (
            round(1.0 - total("env_steps_after") / total("env_steps_before"), 4)
            if total("env_steps_before") else None),
    }


def failures(legs: List[Dict[str, Any]], pooled: Dict[str, Any],
             verify: bool) -> List[str]:
    """Every invariant that did not hold, named.

    A list rather than the first breach: a run that lost both `sockets_unchanged`
    and `actions_agree_after` is telling you something different from a run that
    lost one, and stopping at the first would hide which.
    """
    out: List[str] = []
    for leg in legs:
        name = leg["leg"]
        if not leg["sockets_unchanged"]:
            out.append("%s: sockets_unchanged (%d before, %d after)"
                       % (name, leg["outbound_attempts_before"],
                          leg["outbound_attempts_after"]))
        if leg["rows_consumed"] != leg["env_steps_before"]:
            out.append("%s: rows_consumed %d != env_steps_before %d"
                       % (name, leg["rows_consumed"], leg["env_steps_before"]))
        if leg["actions_agree_before"] is not True:
            out.append("%s: actions_agree_before is %r"
                       % (name, leg["actions_agree_before"]))
        if leg["actions_agree_after"] is not True:
            out.append("%s: actions_agree_after is %r"
                       % (name, leg["actions_agree_after"]))
        if leg["successful_actions"] != leg["successful_actions_before"]:
            out.append("%s: the collapse changed the landed-action count, "
                       "%d -> %d" % (name, leg["successful_actions_before"],
                                     leg["successful_actions"]))
        if leg["env_steps_after"] > leg["env_steps_before"]:
            out.append("%s: the collapse grew the ledger" % name)

    if verify:
        # The archive is the evidence. If it has moved, the result is about a
        # different archive and must not be reported under these numbers.
        for key, expected in (("env_steps", "env_steps_before"),
                              ("wave_attempts", "wave_attempts"),
                              ("total_actions", "scorecard_total_actions")):
            got = pooled[expected]
            if got != PUBLISHED[key]:
                out.append("verify: pooled %s is %r, published %r -- the "
                           "archive has moved" % (key, got, PUBLISHED[key]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--leg", action="append", default=[], required=True,
                    help="a leg's ledger.jsonl (read-only); repeatable")
    ap.add_argument("--max-attempts", type=int, default=5,
                    help="EnvProxyConfig.max_attempts, which is what bounds "
                         "forward()'s loop (default 5)")
    ap.add_argument("--verify", action="store_true",
                    help="also assert the published pooled numbers "
                         "(570 env_step / 494 wave / 72 actions)")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    missing = [path for path in args.leg if not os.path.exists(path)]
    if missing:
        print("no such ledger: %s" % ", ".join(missing), file=sys.stderr)
        return 2

    legs = [replay_leg(path, args.max_attempts) for path in args.leg]
    pooled = _pool(legs, args.max_attempts)
    problems = failures(legs, pooled, args.verify)
    report = {
        "tool": "refusal_replay",
        "predicate": "proxy.env_proxy.game_not_found_retry",
        "network": "none", "spend": "none", "actions_charged": 0,
        "max_attempts": args.max_attempts,
        "legs": legs,
        "pooled": pooled,
        "invariants": {
            "sockets_unchanged": pooled["sockets_unchanged"],
            "actions_agree_before": pooled["actions_agree_before"],
            "actions_agree_after": pooled["actions_agree_after"],
            "rows_accounted": pooled["rows_consumed"] == pooled["env_steps_before"],
        },
        "failures": problems,
        "verdict": "PASS" if not problems else "FAIL",
    }
    blob = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob + "\n")
    print(blob)
    for problem in problems:
        print("FAIL " + problem, file=sys.stderr)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
