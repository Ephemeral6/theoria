"""The campaign rate budget — Theoria.md:299's arithmetic, redone in the unit that exists.

Theoria.md Phase 1 asks for a campaign action budget:

    战役动作预算 = 三臂 × 局数 × 回合 + 戳探 + 前缀重放传送,必须落在限额内
    (…must fall inside the limit)

`ACCESS_CHECK.md` §6 established that the limit that clause was written against
does not exist: **no per-key action quota is documented anywhere**, and the
product has no place to show one (`browser-ops/TERMS.md` §7.5 — the logged-in
panel has no quota, usage, or billing field at all). What is documented is a
**rate**: 600 requests per minute.

§6 then drew the conclusion that a volume budget has nothing to bust and moved
on. That is right about volume and wrong to stop there, because the clause's
obligation survives the change of unit — it just becomes a different sum. This
module is that sum. A rate limit is charged against **requests in any 60-second
window**, so the budget is not `total ÷ duration`; an average is exactly the
statistic a rate limit does not care about. What it cares about is the peak, and
the peak is set by three things:

    concurrency  ×  how fast one process can issue  ×  what it does between

and the last term is where the answer stops being obvious. §6 named retry storms
as the shape that gets near the limit. It is the opposite: the retry envelope
*self-limits*, because its own backoff is a rate limiter — 40 attempts spread
over ~173 s cannot exceed ~18 rpm no matter how hard it tries. The shape that
gets near the limit is the **fast, healthy, think-free** one: a scripted prefix
replay issuing back-to-back requests at transport speed, which is precisely
Theoria.md:299's own 前缀重放传送 term.

Everything here is offline arithmetic over tracked files. It spends nothing.

    cd arc-recon && python rate_budget.py            # the budget, and a verdict
    cd arc-recon && python rate_budget.py --json
    cd arc-recon && python rate_budget.py --measure  # re-derive inputs from data, report drift
    cd arc-recon && python rate_budget.py --observed # rates actually recorded by canary sweeps

Exit 0 = every declared scenario fits with margin. Exit 1 = a scenario breaches
the documented limit, or a declared input has drifted from the data it came
from. Exit 0 with AMBER rows = fits, but past the warning fraction.

**What this is not.** A bound derived from a documented number is not a
calibration. Zero 429s have ever been observed here (audited over 3,736 logged
requests), the backoff curve after one is undocumented, and `precheck.py`
implements a *linear* ramp against a regime the docs call exponential. So this
module answers "does the plan of record fit inside the published limit" — which
is what Phase 1 asked — and not "what does the server actually do when you
cross it", which only a 429 can answer and none of ours ever has.
"""

import argparse
import json
import math
import os
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from client import DATA_DIR                                   # noqa: E402
from precheck import (                                        # noqa: E402
    ACTION_ATTEMPTS,
    ACTION_DELAY_BASE,
    ACTION_DELAY_CAP,
    RESET_ATTEMPTS,
    RESET_DELAY_BASE,
    RESET_DELAY_CAP,
)

BUDGET_PATH = os.path.join(DATA_DIR, "rate_budget.json")
LEDGER_PATH = os.path.join(DATA_DIR, "recon_ledger.jsonl")
CANARY_RUNS_PATH = os.path.join(DATA_DIR, "canary_runs.jsonl")

WINDOW_S = 60.0

# How far a measured input may sit from its declaration before `--measure`
# calls it drift. Round-trip times are weather; the point of the check is to
# catch a declaration that has gone stale by a factor, not to chase noise.
DRIFT_TOLERANCE = 0.25

ENVELOPES = {
    "reset": (RESET_ATTEMPTS, RESET_DELAY_BASE, RESET_DELAY_CAP),
    "action": (ACTION_ATTEMPTS, ACTION_DELAY_BASE, ACTION_DELAY_CAP),
}


def load_budget(path: str = BUDGET_PATH) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------
# The backoff schedule, read rather than restated
# --------------------------------------------------------------------------

def backoff_delays(envelope: str) -> List[float]:
    """The sleeps `precheck.send_command` will take, in order.

    Imported from precheck rather than copied: a rate budget computed from a
    stale copy of the retry envelope is worse than no rate budget, because it
    is wrong in the confident direction.
    """
    attempts, base, cap = ENVELOPES[envelope]
    return [min(base * (k + 1), cap) for k in range(attempts - 1)]


def storm_request_times(envelope: str, rtt_s: float) -> List[float]:
    """Start time of each attempt in one exhausted retry envelope."""
    times, clock = [], 0.0
    for delay in [0.0] + backoff_delays(envelope):
        clock += delay
        times.append(clock)
        clock += rtt_s
    return times


def peak_in_window(times: List[float], window_s: float = WINDOW_S) -> int:
    """Most requests in any `window_s` window — the statistic a rate limit uses.

    Sliding window over start times. An average would pass a schedule that
    fires everything in the first ten seconds and idles; the limit would not.
    """
    if not times:
        return 0
    best, right = 0, 0
    for left in range(len(times)):
        while right < len(times) and times[right] - times[left] < window_s:
            right += 1
        best = max(best, right - left)
    return best


# --------------------------------------------------------------------------
# One worker's rate
# --------------------------------------------------------------------------

def worker_rpm(shape: Dict[str, Any], rtt_s: float) -> Dict[str, Any]:
    """Sustained and peak requests-per-minute for a single process of this shape.

    Sustained is the steady state: one command costs `think + attempts×rtt +
    backoff`, and issues `attempts` requests. Peak is the worst 60 s window,
    which for a storming worker is strictly higher than its sustained rate and
    for a think-free worker is the same number.
    """
    attempts = float(shape.get("attempts_per_command", 1.0))
    think_s = float(shape.get("think_s", 0.0))
    envelope = shape.get("envelope", "action")

    if attempts > 1.0:
        # A storming worker's pace is its backoff schedule. Charge only the
        # sleeps it actually reaches.
        delays = backoff_delays(envelope)[:max(int(round(attempts)) - 1, 0)]
        backoff_s = sum(delays)
        times = storm_request_times(envelope, rtt_s)[:int(round(attempts))]
    else:
        backoff_s = 0.0
        # Back-to-back commands, one request each, evenly spaced. Enumerated
        # rather than divided so that peak and sustained come off the same code
        # path -- computing the peak as `floor(60/interval)` put it *below* the
        # sustained rate, which is arithmetically impossible and would have
        # understated every think-free row.
        per_request = think_s + rtt_s
        span = int(math.ceil(WINDOW_S / per_request)) + 1 if per_request > 0 else 0
        times = [k * per_request for k in range(span)]
    peak = peak_in_window(times)

    seconds_per_command = think_s + attempts * rtt_s + backoff_s
    sustained = (attempts / seconds_per_command) * 60.0 if seconds_per_command else 0.0
    return {
        "seconds_per_command": round(seconds_per_command, 3),
        "sustained_rpm": round(sustained, 2),
        "peak_rpm": float(peak),
    }


def breach_concurrency(peak_rpm: float, limit: float) -> Optional[int]:
    """How many concurrent processes of this shape it takes to cross the limit.

    The number an operator can actually act on: `None` means one process alone
    already breaches.
    """
    if peak_rpm <= 0:
        return None
    n = int(math.floor(limit / peak_rpm)) + 1
    return n if n >= 1 else None


# --------------------------------------------------------------------------
# The budget
# --------------------------------------------------------------------------

def evaluate(budget: Dict[str, Any]) -> Dict[str, Any]:
    limit = float(budget["limit"]["requests_per_minute"])
    warn_at = limit * float(budget["policy"]["warn_fraction"])
    rtt = float(budget["measured"]["rtt_min_s"])
    shapes = {s["id"]: s for s in budget["worker_shapes"]}

    rows, worst = [], 0.0
    for scenario in budget["scenarios"]:
        shape = shapes[scenario["worker"]]
        one = worker_rpm(shape, rtt)
        concurrency = int(scenario["concurrency"])
        aggregate_peak = one["peak_rpm"] * concurrency
        aggregate_sustained = one["sustained_rpm"] * concurrency
        worst = max(worst, aggregate_peak)

        if aggregate_peak > limit:
            verdict = "BREACH"
        elif aggregate_peak > warn_at:
            verdict = "AMBER"
        else:
            verdict = "OK"

        rows.append({
            "scenario": scenario["id"],
            "worker": shape["id"],
            "concurrency": concurrency,
            "total_commands": scenario.get("total_commands"),
            "per_process_sustained_rpm": one["sustained_rpm"],
            "per_process_peak_rpm": one["peak_rpm"],
            "aggregate_sustained_rpm": round(aggregate_sustained, 2),
            "aggregate_peak_rpm": round(aggregate_peak, 2),
            "headroom_x": (round(limit / aggregate_peak, 2)
                           if aggregate_peak > 0 else None),
            "breach_at_concurrency": breach_concurrency(one["peak_rpm"], limit),
            "verdict": verdict,
        })

    return {
        "limit_rpm": limit,
        "warn_rpm": warn_at,
        "rtt_min_s": rtt,
        "rows": rows,
        "worst_aggregate_peak_rpm": round(worst, 2),
        "verdict": ("BREACH" if any(r["verdict"] == "BREACH" for r in rows)
                    else "AMBER" if any(r["verdict"] == "AMBER" for r in rows)
                    else "OK"),
    }


# --------------------------------------------------------------------------
# Re-deriving the declared inputs from the tracked data
# --------------------------------------------------------------------------

def measure_rtt(path: str = LEDGER_PATH) -> Optional[Dict[str, Any]]:
    values = []
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            elapsed = entry.get("elapsed_ms")
            if isinstance(elapsed, int) and elapsed >= 0:
                values.append(elapsed / 1000.0)
    if not values:
        return None
    values.sort()
    return {"n": len(values), "rtt_min_s": round(values[0], 3),
            "rtt_p50_s": round(statistics.median(values), 3)}


def measure_amplification(path: str = CANARY_RUNS_PATH) -> Optional[Dict[str, Any]]:
    """Attempts per command on the current transport, from the canary's own runs.

    A sweep issues one RESET per game plus its actions, so commands are
    `actions_executed + len(targets)` — not `actions_executed`, which would
    overstate amplification by the RESETs it forgot to count.
    """
    if not os.path.exists(path):
        return None
    post, pre = [], []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                run = json.loads(line)
            except ValueError:
                continue
            commands = (run.get("actions_executed", 0)
                        + len(run.get("targets") or []))
            calls = run.get("http_calls")
            if not commands or not isinstance(calls, int):
                continue
            bucket = post if (run.get("transport") or {}).get("cookies") else pre
            bucket.append(calls / commands)
    out: Dict[str, Any] = {}
    if post:
        out["attempts_per_command_post_cookie"] = round(max(post), 3)
        out["n_post"] = len(post)
    if pre:
        out["attempts_per_command_pre_cookie"] = round(max(pre), 3)
        out["n_pre"] = len(pre)
    return out or None


def check_drift(budget: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], bool]:
    """Compare declared inputs against the data files they were taken from."""
    declared = budget["measured"]
    found: Dict[str, Any] = {}
    rtt = measure_rtt()
    if rtt:
        found.update(rtt)
    amp = measure_amplification()
    if amp:
        found.update(amp)

    checks, drifted = [], False
    for key in ("rtt_min_s", "rtt_p50_s",
                "attempts_per_command_post_cookie",
                "attempts_per_command_pre_cookie"):
        if key not in declared or key not in found:
            checks.append({"input": key, "declared": declared.get(key),
                           "measured": found.get(key), "status": "unchecked"})
            continue
        d, m = float(declared[key]), float(found[key])
        rel = abs(m - d) / d if d else (0.0 if m == 0 else 1.0)
        ok = rel <= DRIFT_TOLERANCE
        drifted = drifted or not ok
        checks.append({"input": key, "declared": d, "measured": m,
                       "relative_change": round(rel, 3),
                       "status": "ok" if ok else "DRIFT"})
    return checks, drifted


def observed_rates(path: str = CANARY_RUNS_PATH) -> List[Dict[str, Any]]:
    """Rates actually recorded by canary sweeps.

    Only sweeps taken after S5 added `elapsed_s` carry one. Older runs are
    reported as unmeasured rather than back-filled from a guess — the whole
    point of the field is that the rate was not recorded before it existed.
    """
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                run = json.loads(line)
            except ValueError:
                continue
            out.append({
                "t": run.get("t"),
                "http_calls": run.get("http_calls"),
                "elapsed_s": run.get("elapsed_s"),
                "observed_rpm": run.get("observed_rpm"),
                "measured": run.get("elapsed_s") is not None,
            })
    return out


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def render(result: Dict[str, Any]) -> str:
    lines = [
        "campaign rate budget -- documented limit %d req/min, AMBER above %d"
        % (result["limit_rpm"], result["warn_rpm"]),
        "single-process floor: one request every %.3f s (fastest ever measured)"
        % result["rtt_min_s"],
        "",
        "%-18s %-14s %5s %10s %10s %9s %8s  %s"
        % ("scenario", "worker", "conc", "peak rpm", "sust rpm",
           "headroom", "breach@", "verdict"),
    ]
    for row in result["rows"]:
        lines.append(
            "%-18s %-14s %5d %10.1f %10.1f %8sx %8s  %s"
            % (row["scenario"], row["worker"], row["concurrency"],
               row["aggregate_peak_rpm"], row["aggregate_sustained_rpm"],
               row["headroom_x"] if row["headroom_x"] is not None else "-",
               row["breach_at_concurrency"] or "-",
               row["verdict"]))
    lines += ["", "worst aggregate peak: %.1f rpm of %d  -->  %s"
              % (result["worst_aggregate_peak_rpm"], result["limit_rpm"],
                 result["verdict"])]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Campaign rate budget against the documented 600 rpm limit. "
                    "Offline; spends nothing.")
    parser.add_argument("--json", action="store_true",
                        help="machine-readable output")
    parser.add_argument("--measure", action="store_true",
                        help="re-derive declared inputs from the tracked data "
                             "and report drift")
    parser.add_argument("--observed", action="store_true",
                        help="rates actually recorded by canary sweeps")
    args = parser.parse_args(argv)

    budget = load_budget()
    result = evaluate(budget)
    failed = result["verdict"] == "BREACH"

    if args.observed:
        runs = observed_rates()
        measured = [r for r in runs if r["measured"]]
        if args.json:
            print(json.dumps({"runs": runs}, indent=2, sort_keys=True))
        else:
            print("canary sweeps: %d recorded, %d carry a measured rate"
                  % (len(runs), len(measured)))
            for run in runs:
                print("  %-22s http=%-5s %s"
                      % (run["t"], run["http_calls"],
                         ("%.1f rpm over %.1f s"
                          % (run["observed_rpm"], run["elapsed_s"]))
                         if run["measured"] else
                         "rate not recorded (pre-S5 sweep)"))
            if not measured:
                print("\nNo sweep has yet recorded a rate. `elapsed_s` was added "
                      "by S5;\nthe next scheduled sweep is the first observation.")
        return 1 if failed else 0

    if args.measure:
        checks, drifted = check_drift(budget)
        failed = failed or drifted
        if args.json:
            print(json.dumps({"budget": result, "inputs": checks}, indent=2,
                             sort_keys=True))
        else:
            print(render(result))
            print("\ndeclared inputs vs the data they came from:")
            for check in checks:
                print("  %-38s declared=%-8s measured=%-8s %s"
                      % (check["input"], check["declared"], check["measured"],
                         check["status"]))
            if drifted:
                print("\nDRIFT: a declared input no longer matches its source. "
                      "Re-derive the budget\nbefore trusting it.")
        return 1 if failed else 0

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render(result))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
