"""Red-team attacks on the economy family (E1-E5, E7).

Every builder is zero-argument, deterministic, and lays out data only.
"""

from battery.audit.v9.attack import Attack
from battery.model import Run, Step, Call, Concept, Clause, Theory, Beat, Repair, Truth


# --------------------------------------------------------------------------
# E1 -- neutral, usd. Total recorded model cost. Controllability required.
# --------------------------------------------------------------------------

def build_E1_dial_high():
    return Run(run_id="v9-E1-dial-high", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, cost_usd=250.0, input_tokens=1000)
                      for i in range(12)])


def build_E1_dial_low():
    return Run(run_id="v9-E1-dial-low", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, cost_usd=0.0001, input_tokens=1000)
                      for i in range(12)])


def attack_E1_dial():
    return Attack(
        metric_id="E1", name="dial",
        build=build_E1_dial_high,
        build_low=build_E1_dial_low,
        claim="E1 is whatever number I write in cost_usd; identical run shape, "
              "12 calls either way, values 3000.0 vs 0.0012 (factor 2.5e6)",
        accidental=False,
        rationale="Writing a cost field is a deliberate act, so no agent lands "
                  "here by accident; but nothing in the metric ties cost_usd to "
                  "tokens, model, or work, so the field is a free parameter.",
        benign_window="E1 is harmless only read as a boolean -- 'this run was "
                      "billed at all' -- never as a magnitude compared between arms.",
    )


def build_E1_unbilled_high():
    return Run(run_id="v9-E1-unbilled-high", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, cost_usd=0.5,
                           input_tokens=20000, output_tokens=800)
                      for i in range(200)])


def build_E1_unbilled_low():
    return Run(run_id="v9-E1-unbilled-low", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           cost_usd=(0.5 if i == 0 else None),
                           input_tokens=20000, output_tokens=800)
                      for i in range(200)])


def attack_E1_unbilled():
    return Attack(
        metric_id="E1", name="unbilled-tail",
        build=build_E1_unbilled_high,
        build_low=build_E1_unbilled_low,
        claim="Two runs with byte-identical token usage (200 calls, 20k input "
              "tokens each) report 100.0 vs 0.5 because cost_usd=None is summed "
              "as zero, not as missing",
        accidental=True,
        rationale="Harnesses routinely fail to attach a price to some responses "
                  "(cache hits, streamed calls, retried calls, a provider that "
                  "omits usage on error), and `c.cost_usd or 0.0` silently reads "
                  "'unpriced' as 'free' -- so an arm with a lossy billing logger "
                  "looks cheap without doing anything.",
        benign_window="Same as above: only 'was anything billed', and only when "
                      "every call is known to carry a price.",
    )


# --------------------------------------------------------------------------
# E2 -- higher, share. Cost in first 25% of turns. Target >= 0.95.
# --------------------------------------------------------------------------

def build_E2_first_turn_bill():
    return Run(run_id="v9-E2-first-turn", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           cost_usd=(1.0 if i == 0 else 0.0),
                           input_tokens=1000)
                      for i in range(40)])


def attack_E2_first_turn():
    return Attack(
        metric_id="E2", name="first-turn-bill",
        build=build_E2_first_turn_bill,
        claim="E2 = 1.0 on a run that spends everything on turn 0 and then logs "
              "39 turns costing exactly nothing",
        accidental=True,
        rationale="Any harness that bills a single large system-prompt call up "
                  "front and then runs a cheap scripted loop produces exactly "
                  "this shape; 'front-loaded' is a cost-timestamp pattern, not "
                  "evidence that understanding happened in turn 0.",
    )


def build_E2_unbilled_tail():
    return Run(run_id="v9-E2-unbilled-tail", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           cost_usd=(0.5 if i < 3 else None),
                           input_tokens=30000, output_tokens=1200)
                      for i in range(40)])


def attack_E2_unbilled_tail_():
    return Attack(
        metric_id="E2", name="unbilled-tail",
        build=build_E2_unbilled_tail,
        claim="E2 = 1.0 on a run whose 40 turns all burn 30k input tokens, "
              "because only the first three carry a price at all",
        accidental=True,
        rationale="A billing logger that drops out partway (token refresh, "
                  "provider omitting usage after the first N responses) turns a "
                  "flat spend profile into a perfect front-load; the metric "
                  "cannot distinguish 'stopped spending' from 'stopped logging'.",
    )


def build_E2_batched_turn_zero():
    return Run(run_id="v9-E2-batched", arm="attacker", source="v9",
               calls=[Call(idx=i,
                           turn=(0 if i < 30 else i - 29),
                           cost_usd=(1.0 if i < 30 else 0.1),
                           input_tokens=5000)
                      for i in range(40)])


def attack_E2_batched():
    return Attack(
        metric_id="E2", name="batched-turn-label",
        build=build_E2_batched_turn_zero,
        claim="E2 = 0.973 with spend that never front-loads at all -- 30 equal "
              "calls are simply all labelled turn=0, so the bucketing does the work",
        accidental=True,
        rationale="turn is a harness label, not a fact about the world: any "
                  "wrapper that batches sub-agent or tool-loop calls under one "
                  "outer turn collapses arbitrarily much spend into bucket 0, "
                  "and E2 rewards the labelling convention rather than the arm.",
    )


# --------------------------------------------------------------------------
# E3 -- lower, share. Turn fraction to reach 90% of cost. Target <= 0.05.
# --------------------------------------------------------------------------

def build_E3_first_turn_bill():
    return Run(run_id="v9-E3-first-turn", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           cost_usd=(1.0 if i == 0 else 0.0),
                           input_tokens=1000)
                      for i in range(100)])


def attack_E3_first_turn():
    return Attack(
        metric_id="E3", name="first-turn-bill",
        build=build_E3_first_turn_bill,
        claim="E3 = 0.01 -- 90% of the bill lands by turn 1 of 100, because "
              "turns 2..100 cost zero",
        accidental=True,
        rationale="Identical shape to the E2 attack and just as easy to produce "
                  "by accident: one expensive setup call plus a long free loop. "
                  "E3 also *improves* the more idle turns you pad on, so a run "
                  "that stalls looks better converged than one that works.",
    )


def build_E3_padded_tail():
    return Run(run_id="v9-E3-padded", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           cost_usd=(0.4 if i < 2 else None),
                           input_tokens=25000)
                      for i in range(400)])


def attack_E3_padded_tail_():
    return Attack(
        metric_id="E3", name="padded-unbilled-tail",
        build=build_E3_padded_tail,
        claim="E3 = 0.005 on 400 uniformly expensive turns of which only the "
              "first two are priced",
        accidental=True,
        rationale="Combines the two free levers: unpriced calls read as free, "
                  "and the denominator is the number of turns you logged. "
                  "Logging more turns strictly lowers E3, so verbosity is scored "
                  "as economy.",
    )


def build_E3_batched_turn_zero():
    return Run(run_id="v9-E3-batched", arm="attacker", source="v9",
               calls=[Call(idx=i,
                           turn=(0 if i < 360 else i - 359),
                           cost_usd=1.0,
                           input_tokens=5000)
                      for i in range(400)])


def attack_E3_batched():
    return Attack(
        metric_id="E3", name="batched-turn-label",
        build=build_E3_batched_turn_zero,
        claim="E3 = 0.0244 on a perfectly flat spend profile -- all 400 calls "
              "cost exactly $1.00; 360 of them are merely labelled turn=0",
        accidental=True,
        rationale="turn is a harness label. A wrapper that batches its tool loop "
                  "under one outer turn early on and one call per turn later "
                  "produces this; the cost curve is uniform, so E3 is reporting "
                  "the logging convention, not when the bill settled. Note the "
                  "8-turn floor does bite: the same trick with 100 calls "
                  "collapsed to 6 turns and E3 refused with 'fewer than 8 turns'.",
    )


# --------------------------------------------------------------------------
# E4 -- lower, unitless. quad R^2 - linear R^2 on context tokens. Target <= 0.001
# --------------------------------------------------------------------------

def build_E4_flat_context():
    return Run(run_id="v9-E4-flat", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=120000, cost_usd=0.9)
                      for i in range(60)])


def attack_E4_flat():
    return Attack(
        metric_id="E4", name="flat-context",
        build=build_E4_flat_context,
        claim="E4 = 0.0 on a run that pins 120k context tokens on every one of "
              "60 turns -- the worst possible context hygiene scores perfectly",
        accidental=True,
        rationale="An arm that stuffs the whole context window from turn one and "
                  "never grows (because it cannot) has zero variance, r2() "
                  "short-circuits to 0.0 for both fits, and the difference is "
                  "0.0; saturating the window is common and is scored as ideal.",
    )


def build_E4_linear_context():
    return Run(run_id="v9-E4-linear", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=4000 + 2000 * i,
                           cost_usd=0.5)
                      for i in range(60)])


def attack_E4_linear():
    return Attack(
        metric_id="E4", name="exactly-linear-context",
        build=build_E4_linear_context,
        claim="E4 ~ 0.0 on context that grows without bound (4k -> 122k tokens), "
              "as long as it grows in a straight line",
        accidental=True,
        rationale="A fixed-size transcript append per turn -- the default of "
                  "almost every chat harness -- is exactly linear, so unbounded "
                  "context growth is invisible to E4; the metric measures "
                  "curvature, not size.",
    )


def build_E4_sawtooth_context():
    return Run(run_id="v9-E4-sawtooth", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           input_tokens=20000 + 20000 * (i % 5),
                           cost_usd=0.5)
                      for i in range(60)])


def attack_E4_sawtooth():
    return Attack(
        metric_id="E4", name="compaction-sawtooth",
        build=build_E4_sawtooth_context,
        claim="E4 ~ 0.0 on a 20k-100k sawtooth: periodic compaction defeats both "
              "fits equally",
        accidental=True,
        rationale="Auto-compaction every N turns is standard harness behaviour "
                  "and destroys any polynomial trend, so an arm gets the target "
                  "score from its wrapper's memory policy rather than its own "
                  "discipline.",
    )


# --------------------------------------------------------------------------
# E5 -- lower, usd/action. Cost / successful actions. Target <= 0.001.
# --------------------------------------------------------------------------

def build_E5_cheap_flail():
    return Run(run_id="v9-E5-cheap-flail", arm="attacker", source="v9",
               steps=[Step(idx=i, action="noop", state_key="s0")
                      for i in range(2000)],
               calls=[Call(idx=0, turn=0, cost_usd=0.000000001)])


def attack_E5_cheap_flail_():
    return Attack(
        metric_id="E5", name="cheap-flail",
        build=build_E5_cheap_flail,
        claim="E5 = 0.0 -- one nanocent call, 2000 identical no-op actions that "
              "never change the state key",
        accidental=False,
        rationale="Declaring a 1e-9 price is deliberate. But it shows the metric "
                  "has no floor: 'successful' means only `not failed`, so the "
                  "denominator counts actions no one checked, and nothing "
                  "requires the cost to be commensurate with them.",
    )


def build_E5_step_spam():
    return Run(run_id="v9-E5-step-spam", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % (i % 5), state_key="s%d" % (i % 3))
                      for i in range(200000)],
               calls=[Call(idx=i, turn=i, cost_usd=0.05, input_tokens=8000)
                      for i in range(100)])


def attack_E5_step_spam_():
    return Attack(
        metric_id="E5", name="step-spam",
        build=build_E5_step_spam,
        claim="E5 = 0.000025 on a realistic $5.00 bill, purely by emitting "
              "200000 cycling no-op actions",
        accidental=True,
        rationale="Any arm with a cheap action channel -- a bulk/batched env "
                  "API, a scripted sweep, a retry loop that re-issues the same "
                  "move -- inflates the denominator for free, and E5 reads "
                  "thrashing as efficiency.",
    )


def build_E5_unbilled_calls():
    return Run(run_id="v9-E5-unbilled", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i,
                           failed=(i % 7 == 0))
                      for i in range(600)],
               calls=[Call(idx=i, turn=i,
                           cost_usd=(0.000001 if i == 0 else None),
                           input_tokens=40000, output_tokens=2000)
                      for i in range(500)])


def attack_E5_unbilled():
    return Attack(
        metric_id="E5", name="unbilled-calls",
        build=build_E5_unbilled_calls,
        claim="E5 = 0.0 on 500 calls of 40k input tokens each, because 499 of "
              "them carry cost_usd=None",
        accidental=True,
        rationale="Same lossy-billing failure as E1/E2 but on the ratio: the "
                  "numerator is recorded cost while the denominator is recorded "
                  "actions, and only one of the two is required to be complete "
                  "(the `cost` capability passes on a single priced call).",
    )


# --------------------------------------------------------------------------
# E7 -- lower, unitless. quad R^2 - linear R^2 on prompt_chars. Target <= 0.001
# --------------------------------------------------------------------------

def build_E7_flat_prompt():
    return Run(run_id="v9-E7-flat", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, prompt_chars=400000, cost_usd=0.9)
                      for i in range(60)])


def attack_E7_flat():
    return Attack(
        metric_id="E7", name="flat-prompt",
        build=build_E7_flat_prompt,
        claim="E7 = 0.0 while re-reading a 400000-character prompt on every one "
              "of 60 turns",
        accidental=True,
        rationale="Re-sending a maximal fixed prompt every turn is the laziest "
                  "possible context policy and has zero variance, so r2() "
                  "returns 0.0 for both fits and the difference is 0.0.",
    )


def build_E7_linear_prompt():
    return Run(run_id="v9-E7-linear", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, prompt_chars=20000 + 12000 * i,
                           cost_usd=0.5)
                      for i in range(60)])


def attack_E7_linear():
    return Attack(
        metric_id="E7", name="exactly-linear-prompt",
        build=build_E7_linear_prompt,
        claim="E7 ~ 0.0 on prompts that grow 20k -> 728k chars in a straight line",
        accidental=True,
        rationale="Appending a fixed-size block of re-read material per turn is "
                  "linear by construction; E7 only penalises acceleration, so "
                  "the metric is blind to a 36x blow-up in what the arm re-reads.",
    )


def build_E7_sawtooth_prompt():
    return Run(run_id="v9-E7-sawtooth", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i,
                           prompt_chars=50000 + 90000 * (i % 4),
                           cost_usd=0.5)
                      for i in range(60)])


def attack_E7_sawtooth():
    return Attack(
        metric_id="E7", name="compaction-sawtooth",
        build=build_E7_sawtooth_prompt,
        claim="E7 ~ 0.0 on a periodic 50k-320k prompt sawtooth",
        accidental=True,
        rationale="A wrapper that truncates or re-summarises on a fixed cadence "
                  "produces a periodic signal that neither polynomial explains, "
                  "so both R^2 collapse together and the difference vanishes.",
    )


ATTACKS = [
    attack_E1_dial,
    attack_E1_unbilled,
    attack_E2_first_turn,
    attack_E2_unbilled_tail_,
    attack_E2_batched,
    attack_E3_first_turn,
    attack_E3_padded_tail_,
    attack_E3_batched,
    attack_E4_flat,
    attack_E4_linear,
    attack_E4_sawtooth,
    attack_E5_cheap_flail_,
    attack_E5_step_spam_,
    attack_E5_unbilled,
    attack_E7_flat,
    attack_E7_linear,
    attack_E7_sawtooth,
]
