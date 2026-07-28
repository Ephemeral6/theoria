"""One live action through the whole gated path, before twelve cells go through it.

$0.05 of insurance against a wiring bug costing $2-3 mid-campaign. Exercises
exactly what the campaign will: reserve on the shared pool, charge an ARC HTTP
request, charge a `claude -p` call, release. It does NOT append to
`out/campaign_cells.jsonl` -- a smoke test is not a measurement and must not
land in one.

    python baseline-arms/runs/<id>-a7/smoke.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))

from harness import bare_cc, spend                                # noqa: E402

BUDGET = 1
GAME = "g50t-5849a774"
MODEL = bare_cc.MODEL_TIERS["cheap"]

before = spend.SpendGate().totals()
print("pool before: $%.4f / %d actions" % (before.usd, before.actions))

binding = spend.open_binding("phase3-variance-envelope-smoke", 0.60, 80,
                             holder={"purpose": "A7 pre-flight smoke",
                                     "game_id": GAME})
try:
    summary = bare_cc.play(GAME, MODEL, BUDGET, spend_binding=binding, verbose=True)
finally:
    binding.release("smoke finished")

after = spend.SpendGate().totals()
print(json.dumps(summary, indent=2, sort_keys=True))
print("pool after:  $%.4f / %d actions" % (after.usd, after.actions))
print("delta:       $%.4f / %d actions"
      % (after.usd - before.usd, after.actions - before.actions))

# The whole point: the pool moved, and it moved by what the episode says it spent.
assert after.actions > before.actions, "no ARC request reached the pool"
assert after.actions - before.actions >= summary["http_calls_gameplay"], (
    "the pool counted fewer requests than the episode made")
assert abs((after.usd - before.usd) - summary["cost_usd"]) < 0.02, (
    "the pool and the episode disagree about the bill: pool $%.4f, episode $%.4f"
    % (after.usd - before.usd, summary["cost_usd"]))
# NOT `after.usd > before.usd`. The first run of this script asserted that and
# failed on a correct result: the session quota was exhausted, all three model
# retries came back `is_error` with `total_cost_usd: 0.0`, and a refused call
# that was never billed is a *priced* call worth zero -- which the gate records
# as $0.00 and not as unpriced, exactly as spend_gate's own docstring says it
# should. Asserting the money moved would make this test demand that the smoke
# test cost something.
assert after.unpriced_calls == before.unpriced_calls, (
    "a model call could not be priced; the pool's dollar total is now a lower "
    "bound and further dollar spend is blocked pool-wide until price_unpriced()")
print("\nSMOKE OK -- pool charged %d action(s), $%.4f, model outcome %r"
      % (after.actions - before.actions, after.usd - before.usd,
         summary["outcome"]))
