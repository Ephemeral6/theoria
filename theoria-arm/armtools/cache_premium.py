"""What the desk's prompt cache costs, and whether it is worth anything.

**The claim under test** (A32 item 3, from `inner/deskdiet.py`'s own header):
the arm pays a cache-creation premium on every call while `cache_read` was 0 on
21 of 22 calls measured. This module re-asks it at n=103, off the archived
`desk_log.json` usage blocks, with no API call and no spend.

**It is still true, and the archive says something sharper than the claim.**

* Every one of the 4 058 283 cached tokens this arm has ever written was written
  at the **one-hour** TTL: `usage.cache_creation.ephemeral_1h_input_tokens`
  carries all of them and `ephemeral_5m_input_tokens` is 0 on all 103 calls.
  One-hour writes bill at 2x base input; five-minute writes at 1.25x.
* `cache_read_input_tokens` is non-zero on 20 of 103 calls, and **19 of those 20
  are calls where the transport split the reply across messages**
  (`harness/replywholeness.py`). The read is the second message re-reading what
  the first one wrote, inside the same call. It is not one desk call reusing the
  previous desk call's prefix -- that has happened at most once, ever.
* The proof that prompt similarity is not what drives it: on the R2b g50t leg,
  call 6's prompt shares a 104 155-character prefix with call 5's (98.8% of it)
  and read **zero** cache, while call 5 -- whose prefix overlap with call 4 was
  10.5% -- read 47 236 tokens. The CLI writes one cache breakpoint, at the end
  of the prompt; the arm's prompt differs at its tail on every call, so the
  breakpoint's key never matches across calls.

**So the honest arithmetic is not "the 1h premium is wasted", it is "caching is
a net loss here at any TTL".** With W tokens written and R read, cached costs
`k*W + 0.1*R` against `W + R` uncached, so caching pays only when
`R > (k-1)/0.9 * W`: R must exceed 1.11W at the 1h rate and 0.28W at the 5m
rate. This archive's ratio is R/W = 0.169. Both fail.

**What is in the arm's control, and what is not.** `claude -p` exposes no flag
for cache TTL, for breakpoint placement, or for turning caching off, so the arm
cannot choose the cheaper column through this transport -- that is a transport
question and it is already boarded (A28, desk through the model proxy). What the
arm *can* do is write fewer tokens: the premium is levied per cached token, and
`inner/deskdiet.py`'s two knobs shrink the prompt. Both defaulted **off** on
every leg in this archive, which is the negative control this module reports.

    python -m armtools.cache_premium
"""

import argparse
import io
import json
import os
import sys
from typing import Any, Dict, List

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

#: List rates for the model this arm's desk runs on, per token. Not a
#: measurement -- these are published rates, and the check that they are the
#: right ones is `reproduces_bill` below: the same four numbers must rebuild the
#: CLI's own `total_cost_usd` across the whole archive. A rate table that cannot
#: do that has no business pricing a counterfactual.
RATES = {
    "claude-opus-5": {
        "input": 5.0 / 1e6,
        "output": 25.0 / 1e6,
        "cache_write_1h": 10.0 / 1e6,     # 2.00x input
        "cache_write_5m": 6.25 / 1e6,     # 1.25x input
        "cache_read": 0.5 / 1e6,          # 0.10x input
    },
}

#: How close the rebuilt bill must sit to the CLI's own before this module will
#: price anything from it. 2% is loose enough to absorb the haiku side-calls the
#: CLI makes on its own account (they are in `modelUsage` and not in `usage`)
#: and tight enough that a wrong rate column cannot hide.
BILL_TOLERANCE = 0.02


def totals(runs_root: str) -> Dict[str, Any]:
    """Every archived desk call's usage, summed, with the TTL split kept."""
    out = {"calls": 0, "calls_with_usage": 0, "cache_write": 0,
           "cache_write_1h": 0, "cache_write_5m": 0, "cache_read": 0,
           "input": 0, "output": 0, "billed_usd": 0.0,
           "calls_reading_cache": 0, "calls_reading_cache_single_message": 0,
           "models": {}}
    for name in sorted(os.listdir(runs_root)):
        path = os.path.join(runs_root, name, "desk_log.json")
        if not os.path.isfile(path):
            continue
        with io.open(path, encoding="utf-8") as fh:
            try:
                log = json.load(fh)
            except ValueError:
                continue
        for entry in log:
            out["calls"] += 1
            usage = entry.get("usage") or {}
            if not usage:
                continue
            out["calls_with_usage"] += 1
            creation = usage.get("cache_creation") or {}
            read = usage.get("cache_read_input_tokens") or 0
            iterations = usage.get("iterations") or []
            single = (len(iterations) <= 1 and
                      (usage.get("output_tokens") or 0) ==
                      (iterations[0].get("output_tokens") if iterations else None))
            out["cache_write"] += usage.get("cache_creation_input_tokens") or 0
            out["cache_write_1h"] += creation.get("ephemeral_1h_input_tokens") or 0
            out["cache_write_5m"] += creation.get("ephemeral_5m_input_tokens") or 0
            out["cache_read"] += read
            out["input"] += usage.get("input_tokens") or 0
            out["output"] += usage.get("output_tokens") or 0
            out["billed_usd"] += entry.get("cli_cost_usd") or 0.0
            if read:
                out["calls_reading_cache"] += 1
                if single:
                    out["calls_reading_cache_single_message"] += 1
            model = entry.get("model")
            out["models"][model] = out["models"].get(model, 0) + 1
    out["billed_usd"] = round(out["billed_usd"], 6)
    return out


def price(t: Dict[str, Any], rates: Dict[str, float], *,
          ttl: str = "1h", cached: bool = True) -> Dict[str, float]:
    """What this archive would have cost under one caching policy.

    `cached=False` is the no-cache counterfactual: every token that was written
    to or read from the cache becomes plain input at full price. That is the
    honest comparison -- dropping the cache does not make those tokens free, it
    makes them ordinary.
    """
    if not cached:
        lines = {
            "input": (t["input"] + t["cache_write"] + t["cache_read"])
                     * rates["input"],
            "cache_write": 0.0,
            "cache_read": 0.0,
            "output": t["output"] * rates["output"],
        }
    else:
        lines = {
            "input": t["input"] * rates["input"],
            "cache_write": t["cache_write"] * rates["cache_write_%s" % ttl],
            "cache_read": t["cache_read"] * rates["cache_read"],
            "output": t["output"] * rates["output"],
        }
    lines["total"] = sum(lines.values())
    return {k: round(v, 6) for k, v in lines.items()}


def breakeven_read_ratio(rates: Dict[str, float], ttl: str) -> float:
    """Reads per written token above which caching at `ttl` starts to pay.

    Cached: `k*W + r*R`. Uncached: `W + R`. Cached is cheaper exactly when
    `R/W > (k - 1) / (1 - r)`, with `k` and `r` as multiples of base input.
    """
    k = rates["cache_write_%s" % ttl] / rates["input"]
    r = rates["cache_read"] / rates["input"]
    return (k - 1.0) / (1.0 - r)


def report(runs_root: str, model: str = "claude-opus-5") -> Dict[str, Any]:
    rates = RATES[model]
    t = totals(runs_root)
    as_billed = price(t, rates, ttl="1h", cached=True)
    at_5m = price(t, rates, ttl="5m", cached=True)
    uncached = price(t, rates, cached=False)

    residual = (abs(as_billed["total"] - t["billed_usd"]) / t["billed_usd"]
                if t["billed_usd"] else None)
    reproduces = residual is not None and residual <= BILL_TOLERANCE

    ratio = (t["cache_read"] / t["cache_write"]) if t["cache_write"] else None
    out: Dict[str, Any] = {
        "model": model,
        "totals": t,
        "ttl_split": {
            "ephemeral_1h": t["cache_write_1h"],
            "ephemeral_5m": t["cache_write_5m"],
            "all_at_1h": (t["cache_write_1h"] == t["cache_write"]
                          and t["cache_write"] > 0),
        },
        "priced": {"as_billed_1h": as_billed, "if_5m": at_5m,
                   "if_uncached": uncached},
        "reproduces_bill": reproduces,
        "reproduction": {
            "modelled_usd": as_billed["total"],
            "cli_reported_usd": t["billed_usd"],
            "relative_residual": (round(residual, 6)
                                  if residual is not None else None),
            "tolerance": BILL_TOLERANCE,
            "note": ("the four rate columns are published list prices, not a "
                     "fit. They earn the right to price a counterfactual only "
                     "by rebuilding the CLI's own total across the archive."),
        },
        "read_write_ratio": (round(ratio, 4) if ratio is not None else None),
        "breakeven_read_write_ratio": {
            "1h": round(breakeven_read_ratio(rates, "1h"), 4),
            "5m": round(breakeven_read_ratio(rates, "5m"), 4),
        },
        "savings_usd": {
            "switching_to_5m": round(as_billed["total"] - at_5m["total"], 6),
            "dropping_the_cache": round(as_billed["total"] - uncached["total"], 6),
        },
        "in_the_arms_control": _levers(),
    }
    out["savings_share_of_bill"] = {
        k: (round(v / t["billed_usd"], 4) if t["billed_usd"] else None)
        for k, v in out["savings_usd"].items()
    }
    out["reading"] = _reading(out)
    return out


def _levers() -> List[Dict[str, Any]]:
    """The knobs, and honestly which of them the arm actually holds."""
    return [
        {"lever": "cache TTL (1h -> 5m)", "held_by": "the CLI",
         "why": ("`claude -p` documents no flag for `cache_control.ttl`. The "
                 "arm cannot choose the cheaper column through this transport."),
         "actionable_now": False},
        {"lever": "cache breakpoint placement", "held_by": "the CLI",
         "why": ("one breakpoint, at the end of the prompt. Stable-prefix "
                 "placement is what would make a write get read, and it is not "
                 "exposed."),
         "actionable_now": False},
        {"lever": "turning caching off", "held_by": "the CLI",
         "why": "no flag; and see A28 for the transport that would expose it.",
         "actionable_now": False},
        {"lever": "how many tokens are written", "held_by": "the arm",
         "why": ("the premium is levied per cached token, so a shorter prompt "
                 "is a smaller premium, whatever the TTL. "
                 "`inner/deskdiet.py`'s `evidence_delta` and `theory_patch` do "
                 "exactly this and defaulted OFF on every leg in this archive."),
         "actionable_now": True},
    ]


def _reading(out: Dict[str, Any]) -> str:
    t = out["totals"]
    if not t["calls_with_usage"]:
        return ("no archived desk call carried a usage block, so nothing was "
                "priced. This is an absence, not a finding of zero.")
    if not out["reproduces_bill"]:
        return ("the rate table does not rebuild the CLI's own total "
                "(modelled $%.4f against billed $%.4f). No counterfactual is "
                "reported from it."
                % (out["reproduction"]["modelled_usd"],
                   out["reproduction"]["cli_reported_usd"]))
    return (
        "Over %d archived desk calls the arm wrote %d cached tokens and read "
        "%d back, a read/write ratio of %.3f. Every written token went in at "
        "the ONE-HOUR TTL (2x input); none at five minutes. Caching pays only "
        "above a ratio of %.2f at 1h and %.2f at 5m, so on this archive it is a "
        "net loss at both: $%.2f over five-minute writes and $%.2f over not "
        "caching at all, %.1f%% of the $%.2f bill. And the reads are not reuse "
        "-- %d of the %d calls that read any cache are calls where the reply "
        "was split across messages, so the read is the second message of the "
        "same call. The lever the arm actually holds is the token count, not "
        "the TTL."
        % (t["calls_with_usage"], t["cache_write"], t["cache_read"],
           out["read_write_ratio"], out["breakeven_read_write_ratio"]["1h"],
           out["breakeven_read_write_ratio"]["5m"],
           out["savings_usd"]["switching_to_5m"],
           out["savings_usd"]["dropping_the_cache"],
           100.0 * out["savings_share_of_bill"]["dropping_the_cache"],
           t["billed_usd"],
           t["calls_reading_cache"] - t["calls_reading_cache_single_message"],
           t["calls_reading_cache"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs-root", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs"))
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    out = report(args.runs_root, args.model)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
            fh.write("\n")
    if not args.quiet:
        print(json.dumps({k: out[k] for k in
                          ("ttl_split", "priced", "reproduction",
                           "read_write_ratio", "breakeven_read_write_ratio",
                           "savings_usd", "savings_share_of_bill")},
                         indent=1, sort_keys=True))
        print()
        print(out["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
