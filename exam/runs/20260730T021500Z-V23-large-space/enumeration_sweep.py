"""What would it cost to raise the cap? -- the cost curve of `enumerate_states`.

`_large_space()` asserts that enumeration is out of reach.  `enumeration_probe.py`
shows the assertion is at least *true at the shipped cap*: all four class (ii)
levels truncate at 200,000.  This script asks the next question -- how far the
cap could be raised before the machine says no -- by running the same
enumeration on one class (ii) level (`gantry`, item ii1) at a ladder of caps and
measuring states/second and peak resident memory at each rung.

Each rung runs in its own subprocess so peak working set is that rung's alone,
and the parent polls it: a rung is killed if it passes MEM_LIMIT_BYTES or
TIME_LIMIT_SECONDS.  Neither budget is decoration -- this box had ~6 GB free
when the ladder was written, and `enumerate_states` keeps a full command path
per visited state, so memory is the binding constraint long before time is.

Run:  python exam/runs/20260730T021500Z-V23-large-space/enumeration_sweep.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

OUT = os.path.join(HERE, "enumeration_sweep.json")

#: The rung ladder.  200_000 is the shipped `MAX_ENUMERATION`; the rest climb
#: until a budget refuses one.
CAPS = [200_000, 1_000_000, 3_000_000, 10_000_000, 30_000_000]

#: ~6 GB was free on this box. 2.5 GB leaves the rest of the machine alone and
#: is well clear of swapping.
MEM_LIMIT_BYTES = 2_500 * 1024 * 1024

#: "As high as completes in ~60 s", and the ladder stops at the first rung that
#: needs more.  Nothing here is allowed near the 90 s the instruction forbids.
TIME_LIMIT_SECONDS = 60.0

TARGET = 10 ** 12                # verdict.py:88 LARGE_SPACE_THRESHOLD


# ------------------------------------------------------------- the worker

def worker(cap: int) -> None:
    import psutil
    from exam.grading.rubrics_verdict import Level, enumerate_states
    from exam.papers import verdict as V

    doc = V.variant_of(V.comb_room("gantry", 60, None), "gantry",
                       remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})
    level = Level(doc)
    proc = psutil.Process()
    baseline = proc.memory_info().rss
    t0 = time.perf_counter()
    result = enumerate_states(level, cap=cap)
    seconds = time.perf_counter() - t0
    info = proc.memory_info()
    peak = getattr(info, "peak_wset", info.rss)
    sys.stdout.write("@@RESULT@@" + json.dumps({
        "cap": cap,
        "states": result["states"],
        "truncated": result["truncated"],
        "seconds": seconds,
        "baseline_rss_bytes": baseline,
        "peak_rss_bytes": peak,
    }) + "\n")


# ------------------------------------------------------------- the ladder

def run_rung(cap: int) -> dict:
    cmd = [sys.executable, os.path.abspath(__file__), "--worker", str(cap)]
    import psutil
    started = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    watch = psutil.Process(proc.pid)
    observed_peak = 0
    stopped = None
    while proc.poll() is None:
        try:
            rss = watch.memory_info().rss
            observed_peak = max(observed_peak, rss)
            if rss > MEM_LIMIT_BYTES:
                stopped = "memory_limit"
                proc.kill()
                break
        except psutil.Error:
            break
        if time.perf_counter() - started > TIME_LIMIT_SECONDS:
            stopped = "time_limit"
            proc.kill()
            break
        time.sleep(0.05)
    out, err = proc.communicate()
    elapsed = time.perf_counter() - started
    if stopped is not None:
        return {"cap": cap, "completed": False, "stopped_by": stopped,
                "observed_peak_rss_bytes": observed_peak,
                "wall_seconds_before_kill": round(elapsed, 3)}
    marker = "@@RESULT@@"
    line = next((l for l in out.splitlines() if l.startswith(marker)), None)
    if line is None:
        return {"cap": cap, "completed": False, "stopped_by": "worker_error",
                "stderr": err.strip()[-800:]}
    payload = json.loads(line[len(marker):])
    payload["completed"] = True
    payload["observed_peak_rss_bytes"] = max(observed_peak,
                                             payload["peak_rss_bytes"])
    return payload


def main() -> None:
    rungs = []
    for cap in CAPS:
        print("rung cap=%d ..." % cap, end=" ", flush=True)
        rung = run_rung(cap)
        rungs.append(rung)
        if not rung.get("completed"):
            print("STOPPED (%s) after %.1fs, peak %.2f GB"
                  % (rung.get("stopped_by"),
                     rung.get("wall_seconds_before_kill", 0.0),
                     rung.get("observed_peak_rss_bytes", 0) / 2 ** 30))
            break
        rung["states_per_second"] = round(rung["states"] / rung["seconds"], 1)
        rung["bytes_per_state"] = round(
            (rung["peak_rss_bytes"] - rung["baseline_rss_bytes"])
            / rung["states"], 1)
        print("%d states in %.2fs (%.0f st/s), peak %.3f GB, %.0f B/state"
              % (rung["states"], rung["seconds"], rung["states_per_second"],
                 rung["peak_rss_bytes"] / 2 ** 30, rung["bytes_per_state"]))

    done = [r for r in rungs if r.get("completed")]
    largest = done[-1] if done else None
    extrapolation = None
    if largest:
        rate = largest["states_per_second"]
        per_state = largest["bytes_per_state"]
        seconds = TARGET / rate

        # The measured rate is NOT constant -- it falls off rung by rung,
        # because `enumerate_states` stores a full command path per state and
        # `paths[nxt] = path + [command]` copies it, so the work per state grows
        # with BFS depth. Quoting only the linear figure would flatter the
        # method. Fit t = a * N^b over the completed rungs and quote both.
        exponent = None
        power_law = None
        if len(done) >= 2:
            import math
            lo, hi = done[0], done[-1]
            exponent = (math.log(hi["seconds"] / lo["seconds"])
                        / math.log(hi["states"] / lo["states"]))
            coeff = hi["seconds"] / (hi["states"] ** exponent)
            pl_seconds = coeff * (TARGET ** exponent)
            power_law = {
                "fitted_exponent_b_in_t_eq_a_N_pow_b": round(exponent, 4),
                "fitted_over_rungs": [lo["cap"], hi["cap"]],
                "implied_seconds": pl_seconds,
                "implied_years": pl_seconds / (86400.0 * 365.25),
                "why": (
                    "b > 1 because the enumerator keeps one command path per "
                    "state and copies it on every expansion; the cost per state "
                    "rises with BFS depth. Measured rungs: "
                    + "; ".join("%d states in %.2fs (%.0f st/s)"
                                % (r["states"], r["seconds"],
                                   r["states_per_second"]) for r in done)),
            }

        extrapolation = {
            "target_states": TARGET,
            "basis_rung_cap": largest["cap"],
            "basis_states_per_second": rate,
            "basis_bytes_per_state": per_state,
            "linear_in_states": {
                "implied_seconds": round(seconds, 1),
                "implied_days": round(seconds / 86400.0, 2),
                "implied_years": round(seconds / (86400.0 * 365.25), 3),
            },
            "power_law_fit": power_law,
            "implied_bytes": int(TARGET * per_state),
            "implied_terabytes": round(TARGET * per_state / 1e12, 1),
            "caveat": (
                "Both figures are LOWER bounds on the true cost and the time "
                "one is the weaker. Rate is measured while the whole working "
                "set is resident; at 10^12 states nothing is resident and every "
                "dictionary probe is a disk seek, so the real running time is "
                "not states/rate. And 10^12 is itself only the class (ii) "
                "THRESHOLD -- the shipped gantry bound is 2^120 = 1.33e36, 24 "
                "orders of magnitude past it, and no reduction in constants "
                "closes 24 orders of magnitude. The bound is not tight-ish; it "
                "is not in the same universe."),
        }

    document = {
        "level": {"item": "ii1", "level_id": "gantry",
                  "constructor": "comb_room('gantry', 60, None) + "
                                 "remap LEFT<->RIGHT",
                  "switches": 120, "step_limit": None},
        "budgets": {"mem_limit_bytes": MEM_LIMIT_BYTES,
                    "time_limit_seconds": TIME_LIMIT_SECONDS,
                    "note": "the ladder stops at the first rung that needs more"},
        "rungs": rungs,
        "extrapolation_to_large_space_threshold": extrapolation,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % OUT)
    if extrapolation:
        lin = extrapolation["linear_in_states"]
        print("10^12 states, linear in N   => %.3g s (%.2f days), %.1f TB "
              "at %.0f B/state"
              % (lin["implied_seconds"], lin["implied_days"],
                 extrapolation["implied_terabytes"],
                 extrapolation["basis_bytes_per_state"]))
        if extrapolation["power_law_fit"]:
            pl = extrapolation["power_law_fit"]
            print("10^12 states, fitted N^%.3f => %.3g s (%.3g years)"
                  % (pl["fitted_exponent_b_in_t_eq_a_N_pow_b"],
                     pl["implied_seconds"], pl["implied_years"]))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(int(sys.argv[2]))
    else:
        main()
