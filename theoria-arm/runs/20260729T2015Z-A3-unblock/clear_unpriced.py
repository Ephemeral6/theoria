"""Clear the one `unpriced` row blocking every dollar in the shared pool.

Run with no arguments it only *reports*: what it would file, and what the pool
would become. `--commit` is the flag that writes, and it writes exactly one
`price_correction` record. The default is a dry run because this ledger is
append-only -- there is no second attempt at getting the number right, and a
script whose default behaviour is to spend money is a script that eventually
runs by accident.

Background. Pool `theoria-shared-2026-07` holds exactly one spend row flagged
`unpriced` (seq 7418). While it stands, `spend_gate.check()` refuses every
`usd > 0` request from *every* session sharing the pool -- not just the
campaign that produced it. Pure ACTION spend (`usd == 0`) is unaffected. The
only documented exit is `SpendGate.price_unpriced()`, which appends; it cannot
retract the row, and it rejects `usd <= 0`.

The number. The call in question is call 4 of run `r-96e128ffb1c64bad`. It has
no provider `usage` block anywhere in the repo, because it never reached the
provider: 145 ms elapsed between the previous call settling (seq 7417,
00:36:50.361Z) and this one raising (seq 7418, 00:36:50.506Z), while the three
successful calls in the same run took 180s, 241s and 208s of API time. It
raised `ModelError: unparseable CLI output:` with an empty stdout. The best
measurement of what it cost is therefore **$0.00**.

$0.00 is what `price_unpriced` will not accept, so this files the tightest
defensible upper bound instead: $0.146292, the maximum over ten comparable
calls (arm=theoria, beat=theorize, model claude-haiku-4-5-20251001, transport
claude-code-cli). Those ten were re-derived from `pricing_v1.json` and
reproduce the CLI's own `costUSD` to within 2.78e-17, so the bound is measured
rather than assumed.

What this does not fix, and deliberately says out loud: the row's recorded
`usd: 4.0` is the arm's `model_call_ceiling_usd` placeholder, not a
measurement, and it stays on the books forever. After this correction the pool
is overstated by roughly $4.15 for a call that cost nothing. That is a
property of an append-only ledger meeting a bad placeholder policy, not
something a correction can undo -- the placeholder policy itself is fixed
separately, on the arm side.
"""

from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)

from proxy.spend_gate import Reservation, SpendGate      # noqa: E402

# The blocking row, verbatim from proxy/var/spend_gate.jsonl seq 7418.
RESERVATION_ID = "res-d9f50ec3c0ba4a9d"
CAMPAIGN = ("theoria-arm:A3-campaign-devpile:g50t-5849a774:"
            "20260729T0035Z-a3-desk-live-proof2")
USD = 0.146292
RESOLVES = 1

REASON = (
    "Call 4 of run r-96e128ffb1c64bad (spend_gate seq 7418) has no provider "
    "usage block anywhere in the repo: its run ledger holds exactly three "
    "model_call records and run.json's usage_total sums to those three alone. "
    "It raised 'ModelError: unparseable CLI output:' with empty stdout 145ms "
    "after the previous call settled (seq 7417 00:36:50.361Z -> seq 7418 "
    "00:36:50.506Z), against same-run comparable API durations of 136.6s-241.3s, "
    "so no provider round-trip occurred and the true cost is $0.00. The usd:4.0 "
    "on the record is theoria-arm's model_call_ceiling_usd placeholder, not a "
    "measurement. price_unpriced refuses $0.00, so this files the tightest "
    "defensible upper bound instead: $0.146292 = max over 10 comparable calls "
    "(arm=theoria, beat=theorize, model=claude-haiku-4-5-20251001, "
    "transport=claude-code-cli), each re-derived from pricing_v1 "
    "sha256:27ce4bb488204fb429efff841c4ec7a63c536d717b36b103fe22004eca5b1f42 "
    "to within 2.78e-17 of the CLI's self-reported costUSD. Filed by RES-1 "
    "cycle 21, 2026-07-29, to unblock pool-wide dollar spend; evidence in "
    "theoria-arm/runs/20260729T2015Z-A3-unblock/."
)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    commit = "--commit" in argv

    gate = SpendGate()
    before = gate.totals()

    print("pool      %s" % gate.policy.pool)
    print("before    $%.6f / $%.2f   unpriced_calls=%d"
          % (before.usd, before.ceiling_usd, before.unpriced_calls))

    if before.unpriced_calls == 0:
        print("\nNothing to do: the pool is not blind. Somebody else cleared "
              "it, or this already ran. Not filing a second correction -- "
              "resolves must not exceed the blindness that exists.")
        return 0
    if before.unpriced_calls != RESOLVES:
        print("\nREFUSING: expected exactly %d unpriced call(s), found %d. "
              "This correction was reasoned about one specific row; a second "
              "one appeared and needs its own provenance before anything is "
              "filed." % (RESOLVES, before.unpriced_calls))
        return 1

    entry = before.by_reservation.get(RESERVATION_ID)
    if entry is None:
        print("\nREFUSING: reservation %s is not in the ledger." % RESERVATION_ID)
        return 1

    print("would file $%.6f  resolves=%d  against %s"
          % (USD, RESOLVES, RESERVATION_ID))
    print("after     $%.6f   unpriced_calls=0 (projected)" % (before.usd + USD))

    if not commit:
        print("\nDRY RUN -- nothing written. Re-run with --commit to file it.")
        return 0

    reservation = Reservation(
        reservation_id=RESERVATION_ID, campaign=CAMPAIGN,
        usd_cap=entry["usd_cap"], action_cap=entry["action_cap"],
        expires_epoch=0.0, holder={"agent": "RES-1"})

    after = gate.price_unpriced(reservation, usd=USD, resolves=RESOLVES,
                                reason=REASON)
    print("\nFILED.")
    print("after     $%.6f / $%.2f   unpriced_calls=%d"
          % (after.usd, after.ceiling_usd, after.unpriced_calls))
    print(json.dumps({"usd": after.usd, "actions": after.actions,
                      "unpriced_calls": after.unpriced_calls,
                      "free_usd": after.free_usd}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
