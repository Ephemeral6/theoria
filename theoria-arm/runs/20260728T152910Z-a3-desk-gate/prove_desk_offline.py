"""The desk axis, end to end, offline, into the same scratch pool the mock run used.

`harness/run.py --mock` proves the *action* axis: it drives the real arm
against `proxy/mock`, and every outbound request lands in the pool under one
named campaign. It cannot prove the *dollar* axis, because the only way to make
this arm spend a dollar is to start a real `claude -p` subprocess and pay for
it.

So the subprocess is stubbed at `ModelDesk._invoke` -- the single seam between
this arm and money -- and everything above it is the shipped code: the same
`check` before, the same pricing rule, the same `record` after. Three envelopes
that between them exercise every settlement path:

    1. a normal reply, priced by the CLI's own `total_cost_usd`
    2. a call that raises before an envelope -> ceiling, `unpriced: true`
    3. an envelope with no price at all      -> ceiling, `unpriced: true`

The order is not arbitrary and the first draft got it wrong, which is worth
recording: with the unpriced call second, the *third* call was refused before
it started with `UNPRICED_SPEND`. That is the gate working exactly as designed
-- one blind call makes the pool's dollar total a lower bound, so no further
dollar may be checked against it until a human accounts for the gap with
`price_unpriced()` -- and it is a real operational consequence of charging a
ceiling rather than a zero. It is stated here rather than tuned away.

$0.00 is spent. No network, no API key, no subprocess.

    python runs/20260728T152910Z-a3-desk-gate/prove_desk_offline.py <pool.jsonl>
"""

import json
import os
import sys

ARM = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ARM)

import _bootstrap                                            # noqa: E402,F401

from harness import spend as spend_mod                       # noqa: E402
from harness.modelcall import ModelDesk                      # noqa: E402
from harness.run import _scratch_policy                      # noqa: E402
from proxy.spend_gate import SpendGate                       # noqa: E402


class FakeRun:
    """What `ModelDesk` uses off a `RunLedger`. The ledger write is not the
    thing under test here; the pool records are."""

    def __init__(self):
        self.run_id = "r-proof-desk"
        self.model_calls = []

    def model_call(self, **fields):
        self.model_calls.append(fields)


def bind(pool_path, campaign):
    gate = SpendGate(_scratch_policy(pool_path))
    expect = {"pool": gate.policy.pool,
              "ledger_abspath": os.path.abspath(gate.ledger_path)}
    caps = spend_mod.plan_caps(actions=6, commands=2000, cost_ceiling_usd=20.0,
                               gate=gate)
    binding = spend_mod.open_binding(
        "theoria-arm:A3-campaign-devpile:g50t-5849a774:" + campaign,
        caps, gate=gate, expect_pool=expect,
        holder={"proof": "prove_desk_offline.py"})
    run = FakeRun()
    run.spend_binding = binding
    desk = ModelDesk(run, model="claude-opus-5", cost_ceiling_usd=20.0)
    return gate, binding, desk


def script(desk, *scripted):
    queue = list(scripted)

    def invoke(prompt, model):
        envelope, boom = queue.pop(0)
        if boom is not None:
            raise boom
        return envelope, 91234, ""

    desk._invoke = invoke                    # the only seam that costs money


def totals(gate):
    return json.dumps({k: v for k, v in gate.totals().as_dict().items()
                       if k in ("usd_spent", "actions_spent", "unpriced_calls")},
                      sort_keys=True)


def main(pool_path):
    priced = ({"result": "the manual, revised", "subtype": "success",
               "total_cost_usd": 1.489011,
               "usage": {"input_tokens": 41203, "output_tokens": 2871}}, None)
    timeout = (None, RuntimeError("claude -p timed out after 1800s"))
    no_price = ({"result": "answered, but the envelope forgot to say what it "
                           "cost", "subtype": "success", "usage": {}}, None)

    # -- phase A: priced, then a call that raises, then the latch -----------
    print("== phase A: one priced call, one that raises, and then the stop ==")
    gate, binding, desk = bind(pool_path, "a3-gate-desk-proof")
    script(desk, priced, timeout, priced)
    try:
        print("A1 " + desk.call("frame + diffs + engine report", beat="theorize"))
        try:
            desk.call("frame + diffs", beat="probe_design")
        except spend_mod.SpendGateError:
            raise
        except RuntimeError as exc:
            print("A2 raised, and still charged: %s" % exc)
        try:
            desk.call("frame + diffs", beat="theorize")
            print("A3 NOT REACHED -- the gate should have stopped the run")
        except spend_mod.SpendGateTripped as stop:
            # 闸门红了立刻停. One blind call makes the pool's dollar total a
            # lower bound, so the next dollar cannot be checked against it.
            print("A3 refused before it started: %s -- %s"
                  % (stop.rule, str(stop).split(".")[0]))
    finally:
        binding.release("phase A finished")
    print("   pool:", totals(gate), "\n")

    # -- phase B: an envelope that cannot price itself ----------------------
    # A fresh pool, because phase A left this one blind on purpose.
    print("== phase B: an envelope with no price is charged its ceiling ==")
    other = os.path.join(os.path.dirname(os.path.abspath(pool_path)),
                         "scratch-pool-b.jsonl")
    gate_b, binding_b, desk_b = bind(other, "a3-gate-desk-proof-unpriced")
    script(desk_b, no_price)
    try:
        print("B1 " + desk_b.call("frame + diffs", beat="theorize"))
    finally:
        binding_b.release("phase B finished")
    print("   pool:", totals(gate_b))
    print(json.dumps(desk_b.summary()["spend_gate"]["caps"]["arithmetic"],
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
