"""a7 — the adversarial reviewer's round, and it is NOT blind.

Charge (b) of the adversarial review was *"is 'not gameable' just a failure of
imagination?"*, and the answer for E1 was yes.  E1 came out of the blind round
in the main table for one reason: its only landed attack was typed
`accidental=False`, and `accidental` is the single field the pre-registration
admits cannot be measured from a `Run`.  A reviewer that could see the whole
audit found four attacks that are accidental by any reading — a currency-unit
mistake, one ledger row per HTTP retry, a model swap, and a prompt-caching
flag — each swinging E1 by 10x to 30x over byte-identical decisions.

**These attacks are recorded separately and labelled sighted, because they
are.**  Their author had read `gaming.py`, the blind attacks, the defences and
the verdict table.  That makes them weaker evidence about *the shape of the
attack surface* than a1–a6 — which is what blinding buys — and exactly as
strong as a1–a6 about *whether this particular metric can be reached without
the capability*, which is a question about the code.  Mixing them into the
blind modules would have destroyed the first property to no benefit.

The M3 probes are here for the same reason: to put on record that M3's
survival is non-implementation.  All three come back `insufficient-data`
because `cross_level_first_use_delay` has no path that calls `ok(...)` —
including `fifty-levels-negative`, which is the exact record D2 already exists
to refuse two functions higher in the same file.
"""

from battery.audit.v9.attack import Attack
from battery.model import Call, Run, Step, Truth


def build_E1_cents_hi():
    """A provider that reports cost in cents, written straight into cost_usd."""
    return Run(run_id="r-E1-cents-hi", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=1000, cost_usd=1.2)
                      for i in range(40)])


def build_E1_cents_lo():
    """Byte-identical traffic, the same bill converted to dollars."""
    return Run(run_id="r-E1-cents-lo", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=1000, cost_usd=0.012)
                      for i in range(40)])


def build_E1_retry_hi():
    """One ledger row per HTTP attempt: a 429 storm bills the same 40
    decisions twelve times over."""
    return Run(run_id="r-E1-retry-hi", arm="attacker", source="v9",
               calls=[Call(idx=i * 12 + k, turn=i, input_tokens=1000,
                           attempt=k, cost_usd=0.05)
                      for i in range(40) for k in range(12)])


def build_E1_retry_lo():
    """The same 40 decisions from a harness that collapses retries."""
    return Run(run_id="r-E1-retry-lo", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=1000, attempt=0,
                           cost_usd=0.05)
                      for i in range(40)])


def build_E1_model_hi():
    """Identical trajectory on a frontier model."""
    return Run(run_id="r-E1-model-hi", arm="attacker", source="v9",
               model="expensive", intent="solve",
               steps=[Step(idx=i, action="A", state_key="s%d" % i)
                      for i in range(40)],
               calls=[Call(idx=i, turn=i, input_tokens=2000, output_tokens=400,
                           cost_usd=0.075)
                      for i in range(40)])


def build_E1_model_lo():
    """The same trajectory, same tokens, on the small model."""
    return Run(run_id="r-E1-model-lo", arm="attacker", source="v9",
               model="cheap", intent="solve",
               steps=[Step(idx=i, action="A", state_key="s%d" % i)
                      for i in range(40)],
               calls=[Call(idx=i, turn=i, input_tokens=2000, output_tokens=400,
                           cost_usd=0.0025)
                      for i in range(40)])


def build_E1_cache_hi():
    """Prompt caching off: every turn re-reads the manual as input tokens."""
    return Run(run_id="r-E1-cache-hi", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=50000, cost_usd=0.15)
                      for i in range(40)])


def build_E1_cache_lo():
    """Caching on, one flag in the harness, same manual, same decisions."""
    return Run(run_id="r-E1-cache-lo", arm="attacker", source="v9",
               calls=[Call(idx=i, turn=i, input_tokens=1000,
                           cache_read_tokens=49000, cost_usd=0.015)
                      for i in range(40)])




# ---------------------------------------------------------------- M3 -----
def build_M3_two_levels():
    return Run(run_id="r-M3-two", arm="attacker", source="v9",
               steps=[Step(idx=i, action="A", state_key="s%d" % i,
                           level=(0 if i < 10 else 1)) for i in range(20)],
               truth=Truth(levels=2,
                           mechanisms={"door": {"first_seen": 0, "first_used": 0}}))


def build_M3_many_levels():
    return Run(run_id="r-M3-many", arm="attacker", source="v9",
               steps=[Step(idx=i, action="A", state_key="s%d" % i, level=i)
                      for i in range(50)],
               truth=Truth(levels=50,
                           mechanisms={"m%d" % i: {"first_seen": 100,
                                                   "first_used": 0}
                                       for i in range(50)}))


def build_M3_one_level():
    return Run(run_id="r-M3-one", arm="attacker", source="v9",
               steps=[Step(idx=i, action="A", state_key="s%d" % i, level=0)
                      for i in range(20)],
               truth=Truth(levels=1,
                           mechanisms={"door": {"first_seen": 5,
                                                "first_used": 5}}))


def attack_E1_unit_bug():
    return Attack(
        "E1", "unit-bug", build_E1_cents_hi,
        "E1 = 48.0 vs 0.48 on byte-identical traffic; the provider reported "
        "cents and the adapter wrote the number into cost_usd",
        True,
        "A currency-unit mistake is the canonical accident, needs no intent, "
        "and E1 has no plausibility band, no tokens-to-dollars cross-check "
        "and no per-call unit price to contradict it.",
        build_low=build_E1_cents_lo)


def attack_E1_retry_rows():
    return Attack(
        "E1", "retry-rows", build_E1_retry_hi,
        "E1 = 24.0 vs 2.0 for the same 40 decisions; one ledger row per HTTP "
        "attempt during a rate-limit storm",
        True,
        "`Call.attempt` exists precisely because one harness in this "
        "repository writes a row per attempt. E1 sums rows. Rate limiting is "
        "the environment's behaviour, not the arm's.",
        build_low=build_E1_retry_lo)


def attack_E1_model_swap():
    return Attack(
        "E1", "model-swap", build_E1_model_hi,
        "E1 = 3.0 vs 0.10 -- 30x -- for the identical 40-step trajectory and "
        "identical token counts, differing only in Run.model",
        True,
        "Model choice is a launcher flag. E1 carries `model` on the Run and "
        "never divides by a unit price, so the economy family reads the price "
        "list rather than the arm.",
        build_low=build_E1_model_lo)


def attack_E1_cache_flag():
    return Attack(
        "E1", "cache-flag", build_E1_cache_hi,
        "E1 = 6.0 vs 0.60 with the same 50k-token context every turn; prompt "
        "caching is on in one run and off in the other",
        True,
        "Caching is a harness flag with no bearing on what the arm decided. "
        "`Call.context_tokens` already sums the three token fields, so the "
        "battery can see the contexts are identical and E1 still reports a "
        "tenfold difference.",
        build_low=build_E1_cache_lo)


def attack_M3_two_levels_zero_delay():
    return Attack(
        "M3", "two-levels-zero-delay", build_M3_two_levels,
        "two levels, one mechanism, first_used == first_seen -> delay 0",
        True, "an annotator who defaults first_used to first_seen")


def attack_M3_fifty_levels_negative():
    return Attack(
        "M3", "fifty-levels-negative", build_M3_many_levels,
        "fifty levels, fifty mechanisms all used 100 steps before seen",
        True, "two counters with different origins, exactly the M1 accident "
              "that D2 refuses -- and M3 would accept, if it answered at all")


def attack_M3_single_level():
    return Attack(
        "M3", "single-level", build_M3_one_level,
        "one level, so transfer is undefined; the control",
        False, "a control, not an attack")
