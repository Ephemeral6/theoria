"""Block until the `claude -p` session quota comes back, then exit 0.

The A7 smoke test found the arm's model side refusing every call with
"You've hit your session limit / resets 8:20pm (Asia/Shanghai)". That is not a
budget gate and not an API fault -- it is the 5-hour session window, which
`SPEND_GATE.md` section 5 lists explicitly as a resource the shared pool does
not watch. Nothing can be measured until it resets, so this waits for it rather
than burning twelve cells' worth of money discovering the same refusal nine
more times.

The probe is a real `claude -p` call and therefore real spend, so it goes
through the gate like everything else on this track. It is one word of prompt
against the cheap tier; the entire wait costs a few cents at the outside.

    python baseline-arms/runs/<id>-a7/await_quota.py --until 2026-07-28T12:20:00Z
"""

import argparse
import calendar
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))

from harness import bare_cc, spend                                # noqa: E402

PROBE = "Reply with the single word: ok"
LIMIT_MARKERS = ("session limit", "usage limit", "rate limit", "resets")


def parse_utc(stamp: str) -> float:
    return calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))


def probe(binding) -> tuple:
    """(available, detail). Charged to the pool either way."""
    binding.check_model_call()
    try:
        env = bare_cc.call_model(PROBE, bare_cc.MODEL_TIERS["cheap"],
                                 os.path.expanduser("~"), timeout=120)
    except bare_cc.ModelError as exc:
        binding.record_model_call(None, detail={"probe": "await_quota",
                                                "error": str(exc)[:200]})
        return False, str(exc)[:200]
    binding.record_model_call(env.get("total_cost_usd"),
                              detail={"probe": "await_quota",
                                      "is_error": bool(env.get("is_error"))})
    text = str(env.get("result") or "")
    if env.get("is_error"):
        return False, text[:200]
    if any(marker in text.lower() for marker in LIMIT_MARKERS):
        return False, text[:200]
    return True, text[:80]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", required=True,
                    help="ISO8601 Z; do not probe before this")
    ap.add_argument("--interval", type=int, default=300,
                    help="seconds between probes once past --until")
    ap.add_argument("--give-up-after", type=int, default=4 * 3600,
                    help="seconds past --until before reporting failure")
    args = ap.parse_args(argv)

    target = parse_utc(args.until)
    now = time.time()
    if now < target:
        wait = target - now
        print("waiting %.0f min until %s (session quota reset)"
              % (wait / 60, args.until), flush=True)
        time.sleep(wait)

    binding = spend.open_binding("phase3-variance-envelope-quota-probe",
                                 0.50, 4,
                                 holder={"purpose": "A7 quota probe"},
                                 ttl_seconds=6 * 3600)
    deadline = target + args.give_up_after
    try:
        while True:
            available, detail = probe(binding)
            stamp = time.strftime("%H:%M:%SZ", time.gmtime())
            if available:
                print("%s quota is back: %r" % (stamp, detail), flush=True)
                return 0
            print("%s still limited: %r" % (stamp, detail), flush=True)
            if time.time() >= deadline:
                print("giving up %.1f h past the stated reset; this is a stop, "
                      "not a failure to try" % (args.give_up_after / 3600),
                      flush=True)
                return 1
            time.sleep(args.interval)
    finally:
        binding.release("quota probe finished")


if __name__ == "__main__":
    sys.exit(main())
