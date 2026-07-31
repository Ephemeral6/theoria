# Framework change A — probe economics

Offline. No ARC action, no model call, no network, no spend. Nothing here
touches the sealed pile.

## 1. The measurement (`MEASUREMENT.json`, `measure_legs.py`)

Reproduce with `python measure_legs.py`. It reads only `probes.jsonl` and
`surprises.jsonl` from the four live legs of 2026-07-31.

```
probes designed         56
probes completed        52
frontier monotone drops 0      <-- the finding
off-frontier results    47 (90.4% of completed)
repeat experiments      18 (32.1% of designed)
predicted bits          min 0.5436  median 0.8813  max 1.0000
realised shrink         0.0000 bits
```

Per leg:

| leg | designed | frontier drops | off-frontier | repeats |
|---|---|---|---|---|
| `20260731T1240Z-A3-level2-carried` | 1 | 0 | 0 | 0 |
| `20260731T1310Z-A3-level2-carried-r2` | 9 | 0 | 8 | 4 |
| `20260731T1430Z-A3-level2-carried-r3` | 29 | 0 | 28 | 5 |
| `20260731T1500Z-A3-sk48-carried-l1` | 17 | 0 | 11 | 9 |

Three things the numbers say, in order of how much they cost.

**The frontier never shrank.** Not once, in 56 probes, in any leg. The
frontier sizes only ever go *up* — r3 runs `16,16,16,16, 22×12, 24×13` — because
the frontier is rebuilt by ablation from the current manual on every single turn
and a refutation is thrown away the moment `probes.jsonl` has it. Information
gain per probe, measured as frontier shrink, is **0.000 bits for all 56**.
Against a design-time price of 0.5436–1.0000 bits.

**47 of the 52 completed probes landed off the frontier.** `survived` was
empty: the observed hash matched no hypothesis at all — not `manual`, not
`inert`, not any single-rule ablation. That is not a probe that "refuted
something". Under determinism an observation with no posterior support says the
frontier does not contain the truth, so the partition the entropy was computed
over was the wrong partition and those bits were never realisable. This is the
precise sense in which r3's 28 `probe_refutation` surprises were cheap to earn
and bought no level: each one licenses a model call, and 28 model calls
re-derived a manual whose *shape* — a set of independently ablatable rules —
could not express what the world was doing.

**18 of the 56 were the same experiment twice.** Same action, byte-identical
partition. r3's `P-01..P-04` are two experiments run twice; `sk48-l1` is 9
repeats out of 17. A greedy argmax over a frontier that never changes returns
the same argmax forever, and the probe alphabet collapses: every one of r3's 29
probes was `key 2` or `key 5`, and every one of sk48-l1's 17 was `key 4` or
`key 3`.

**And the existing gate never said no.** `loop.py`'s only floor is
`entropy_bits > 0`. Across all four legs there are **zero** `unrunnable` rows:
the refusal path exists and has never once fired in a live leg.

## 2. The change (`inner/probe.py`, `inner/loop.py`)

`ProbeEconomy` + `ProbeEconomyConfig`. **Default off.** `enabled=False`
reproduces 2026-07-31 exactly: `filter_hypotheses` returns its argument, `gate`
always allows, and `design()`'s report does not grow an `economy` key.

Four rules, one per measured defect, and nothing else:

| rule | measured need | default when on |
|---|---|---|
| `carry_refutations` | 0 frontier drops in 56 probes | `True` |
| `suppress_repeats` | 18/56 = 32.1% exact repeats | `True` |
| `off_frontier_stop` | 47/52 = 90.4% off-frontier | `3` |
| `max_per_generation` | argmax is fixed while the frontier is | `4` |
| `min_bits` | **no measured need** | `0.0` (no-op) |

`min_bits` is set where the measurement leaves it. Every one of the 56 probes
scored 0.5436–1.0000 bits, so no floor would have cut a probe the other rules do
not already cut. The knob is exposed for a future game and defaulted to a no-op
rather than to a number that would look like it was doing something.

A **generation** is the hypothesis-id set. Counters reset when it changes, which
means theorize — and only theorize — re-opens probing. That is the economy in
one line: a probe is worth an action when the theory has changed since the last
one.

Two subtleties the measurement forced:

* **`manual` is never retired** from its own frontier. `manual_survived` is what
  drives theorize; a frontier that has quietly stopped mentioning the manual
  cannot report it.
* **An off-frontier result retires nobody.** When nothing survived, the
  partition was wrong. "Everyone is refuted" is a statement about the frontier,
  not about its members, and retiring all of them would empty a frontier on
  evidence that does not support emptying it.

### Switching it on

```bash
THEORIA_PROBE_ECONOMY=1 <run the leg>          # or
TheoriaArm(..., probe_economy=ProbeEconomyConfig(enabled=True))
```

An explicit config beats the environment. The environment switch is a positive
whitelist — `banana`, `2`, `TRUE!` and the empty string all leave it **off**, so
a misspelt variable cannot silently enable the thing a round is trying to
measure. Optional overrides: `THEORIA_PROBE_OFF_FRONTIER_STOP`,
`THEORIA_PROBE_MAX_PER_GENERATION`, `THEORIA_PROBE_MIN_BITS`.

Every leg writes `probe_economy.json` whether or not the change is on, so an A/B
round is readable from the archive alone.

## 3. The mock campaign (`mock_campaign.py`, `COMPARISON.json`)

Reproduce with `python mock_campaign.py`. Two legs of one scripted deterministic
world, same seed, same 40-action budget, differing only in the flag. Real
`design()`, real `ProbeEconomy`, real `ProbeLog`, real `Register`, real
`probe_frontier`. Scripted: the world, the legal actions, and a theorize that
grows the manual.

```
                                    OFF         ON
actions_spent                        40         40
theorize_rounds                      40          8
probes_fired                         40          5
probes_refused                        0          6
explorations                          0         35
explorations_after_gate_refusal       0          6
explorations_after_no_split           0         29
off_frontier_probes                  40          3
surprises_total                      40          8
final_rule_count                      6          2

the seven surprise counts             OFF        ON
  replay_mismatch                       0         5
  render_mismatch                       0         0
  proof_failure                         0         0
  probe_refutation                     40         3
  execution_mismatch                    0         0
  search_timeout                        0         0
  heuristic_miss                        0         0
```

Off: 40 probes, all 40 off-frontier, 40 refutations, 40 theorize rounds, and the
gate said no zero times — the live shape, reproduced. On: 5 probes, 6 explicit
refusals, and 29 further turns where the filtered frontier no longer split at
all. `probe_refutation` falls 40 → 3 and `theorize_rounds` 40 → 8.

**Which rule actually bites, and where.** In the mock, all 6 gate refusals came
from the off-frontier stop; repeat suppression and the cap never fired. On the
replay of the four real legs the mix is different, which is why all three rules
are in and not just the one the mock exercises:

| rule | refusals on the real-leg replay | refusals in the mock |
|---|---|---|
| off-frontier stop | 19 | 6 |
| repeat suppression | 12 | 0 |
| per-generation cap | 3 | 0 |
| bits floor (0.0) | 0 | 0 |
| **total** | **34 of 56** | **6 of 11 designs** |

Two honest readings of the OFF/ON table, because one of them is a trap:

* **Fewer surprises is not self-evidently better.** A model is called only when
  a surprise fires, so 40 → 8 is a 5× cut in the model bill. That is the
  argument *if* the 40 were buying nothing, which for these 40 is exactly what
  section 1 measured. It is not a general claim that surprises are waste.
* **The mock's `RULES_GROW_EVERY = 8` is doing real work** and is the number
  most worth attacking. Set it to 1 — theorize adds a rule schema on every
  refutation — and OFF and ON become *identical*, because every turn opens a new
  generation and every counter resets. That is not a bug in the change; it is
  the change correctly declining to interfere with a manual that is genuinely
  moving. 8 is r3's measured ratio (28 refutations, 3 distinct hypothesis-id
  sets); r2's was 4 (8 refutations, 2 sets). The first draft of this mock used 1
  and showed a null result, which is recorded here because it is the honest
  boundary of the claim.

## 4. What this does not show

* **No live evidence.** Nothing here was run against ARC. The claim is that the
  change refuses probes the measurement showed were worthless; whether refusing
  them *completes a level* is exactly what the next round is for, and it is not
  demonstrated by any artefact in this directory.
* **The replay in `tests/test_probe_economy.py` is a counterfactual for the
  gate, not for the run.** It replays the recorded design/result stream through
  the policy, which is faithful because every decision is a pure function of
  those rows — but a real leg would have diverged after the first refusal, so
  the measured `(fired, refused)` of `(56, 0)` off and `(22, 34)` on is a
  statement about the gate and not a prediction of the leg.
* **Exploration is not shown to be better than a probe.** When the gate refuses,
  the loop falls to the least-tried legal action. In the mock that path took 35
  of 40 turns. Whether exploration buys more than a refuted probe is unmeasured
  in both directions.
* **The deeper defect is untouched.** Section 1's real finding is that the
  ablation frontier cannot express a rule *interaction* — every hypothesis is
  "the manual minus one rule", so a world whose behaviour couples two rules has
  its truth outside the frontier no matter which action is chosen. Change A
  stops paying for probes against such a frontier. It does not build a better
  frontier. That is a different change and belongs to a different round.

## 5. Gates

Both run from `theoria-arm/`:

* `python -m pytest -q` — see MANIFEST `tests`.
* `python verify.py`.

`tests/test_probe_economy.py` is 27 tests, and every refusal has a matching test
that watches it say **no** plus one that watches it stay silent when the change
is off. `test_the_old_policy_refuses_none_of_the_fifty_six` pins the baseline at
`(56, 0)`; `test_the_new_policy_refuses_most_of_the_fifty_six` pins the change.

## 6. Superseded by the merge onto master (2026-08-01)

**Sections 1–4 above stand as measured. Section 2's table of rules does not.**
This directory was written on `ep/probe-econ`, in parallel with `p12/arm-diag`,
which attacked the same defect from the measurement side and landed on master
first. The merge kept one implementation of each mechanism, so two of the four
rules named above no longer live on `ProbeEconomy`:

| rule | where it lives after the merge |
|---|---|
| `carry_refutations` | `ProbeEconomy`, unchanged — this is the half only this branch had |
| `min_bits` | `ProbeEconomy`, unchanged, still a 0.0 no-op by default |
| `suppress_repeats` | **gone as a knob.** `inner/loop.py` refuses a repeat unconditionally, keyed on `probe.fingerprint(action, predictions)` rather than on the `(action, partition)` signature this branch used |
| `off_frontier_stop` | **gone as a knob.** `inner/loop.py` refuses on `ProbeLog.vacuous_streak >= MAX_VACUOUS_PROBES_IN_A_ROW`, which counts the same event off the number `information_gain_bits` already computes |
| `max_per_generation` | **gone as a knob.** `loop.MAX_PROBES_BETWEEN_THEORIZE` is the one cap |

Consequently `THEORIA_PROBE_OFF_FRONTIER_STOP` and
`THEORIA_PROBE_MAX_PER_GENERATION` are not read by anything; the only override
is `THEORIA_PROBE_MIN_BITS`. Refusing to re-ask a question the record already
answered turned out not to need a switch, so it does not have one — it applies
to the leg that leaves `THEORIA_PROBE_ECONOMY` off as well.

**The headline numbers survive.** Replaying the four legs through the merged
policy still gives `(56, 0)` for the 2026-07-31 code and `(22, 34)` for the
change. The attribution moves, because the merged rules are keyed differently:

| refusals on the real-leg replay | this branch | after the merge |
|---|---|---|
| off-frontier / vacuous streak | 19 | 19 |
| repeat | 12 | 15 |
| per-generation cap | 3 | 0 |
| bits floor (0.0) | 0 | 0 |
| **total** | **34** | **34** |

The cap falls to zero because the two earlier rules now catch strictly more:
master's fingerprint is over the full prediction set rather than the design's
partition, so it recognises three repeats this branch's signature missed, and
those three were exactly what pushed the count to the cap.

**One defect the merge found and fixed.** Carrying refutations forward shrinks
the frontier, and the fingerprint is computed from what every hypothesis
predicted — so with `carry_refutations` on, the same action from the same state
hashed differently once the theory narrowed, and repeats stopped being
recognised (15 caught → 9, three more actions spent). `inner/loop.py` now
fingerprints the *unfiltered* prediction set and scores survivorship on the
live frontier, via `ProbeLog.record_design(identity=...)`. Neither branch could
have seen this alone: it only exists where the two halves meet.

**What still reproduces, and what does not.** `measure_legs.py` reads only the
legs' own `probes.jsonl` and reproduces section 1 against any checkout.
`mock_campaign.py` does not run against the merged `inner/probe.py` — it calls
`ProbeEconomy.record_fired(design)`, and the merged signature takes no
argument, because there is no signature set left to add to. It is deliberately
left byte-identical rather than patched: it is the artefact that produced
`campaign_off.json`, `campaign_on.json` and `COMPARISON.json` under this
branch's four-rule API, and patching it would make the script and the JSONs
beside it describe different policies. Reproduce section 3 at this manifest's
`base_commit` with `ep/probe-econ` applied; section 3's OFF/ON table is a record
of that rule set and not a claim about the merged one.
