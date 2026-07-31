# V6-V23 (class (ii) large-space unsolvable) — recon + two lenses, RES-3 cycle 85–86

Not yet claimed (blocked on exam territory by my own V26). Written to disk so it
survives this session. Sources: three subagents, read-only, all numbers measured.

## Recon — the ticket's own claims, audited

TRUE: SEALED_DRILL.md:243-254 records the gap; DRILL.json:302-305 has
`classes_absent: ["large_unsolvable"]`, pinned by test_sealed_drill.py:364.
worldgen's largest world t3-full-house = 2654 reachable states (max of 20;
second is 436).

CORRECTED — the 2^m bound is **executable code, not prose**:
`subset_lower_bound()` verdict.py:379, returns `2**m` at :461, guarded by an
AssertionError at :448-457 that dip sources lie on one switch-free hazard-free
lane (the unguarded version once returned 2^60 for a level with 1830 reachable
states — D-EX-021), and spot-checked constructively by test_verdict.py:387.

THE REAL GAP: `_large_space()` verdict.py:767 never enumerates — hardcodes
`"exhaustive_feasible": False, "enumerated": None` at :776-781, and
test_verdict.py:364 **pins** `enumerated is None`. `_small_space()` :744 does
run the enumerator. So the asymmetry is deliberate and tested-in.

The measurement primitive already exists and is simply never called:
`enumerate_states(level, cap=200_000)` rubrics_verdict.py:741 already returns
`truncated=True` at the cap (:768). Precedent for driving it as a measurement:
runs/20260729T020000Z-V5-verdict-three-types/verify_checker_claims.py:107-109.

Other constraints: `GridWorld.reachable(limit=200_000)` worldgen/core/world.py:259
**raises** over the limit, so a genuinely large world crashes worldgen's build.
`lp_potential.solve` potential.py:270 requires a **materialised** state graph
(reads graph["states"], graph["edges"]) — architecturally cannot run on a space
too large to enumerate. That is work item 3's real obstacle.
`LARGE_SPACE_THRESHOLD = 10**12` verdict.py:88 has **no DECISIONS entry anywhere**.
D-024 adjudicates Fast Downward **exit codes**, not wall clock — a timeout rule
EXTENDS it, and must not be written as if it cites it. Cleanest quotable form is
DECISIONS.md:779-781, "a proof and a shrug must not share a return value".
Mechanisms give 2^k per entity (switch_door.py:69, count_lock.py:66) but no
catalogue world uses more than 1 switch / 3 tokens. No parametric size knob.

## Lens 1 — hostile reviewer. The section is refutable as written.

Measured: ii1 2^120 vs **180** positional states; ii2 2^120 vs 180; ii3 2^60 vs
600; ii4 2^118 vs 177. **The largest graph a competent solver touches is 600 nodes.**

The 2^m blow-up comes from switches that are monotone and, in verdict.py:562-564's
own words, "gate no geometry" — exactly what every standard technique eliminates
for free. Delete relaxation would likely dispose of ii1/ii2/ii4 **in the FD
translator** as goal-simplified-to-false, zero expansions. ii3 is
`relaxed_distance 199` against `step_limit 150` (:1035-1037) — root-node prune.
120 pairwise-interchangeable switches ⇒ ~121 symmetry classes. A 120-bit monotone
latch mask is a ~120-node BDD. ii4's certificate **is** a linear pagoda, squarely
in lp_potential's complete part.

Sharpest form: the answer key itself is produced by BFS over the 180-node
quotient (`_region_rep`, verdict.py:1330-1335). And the quotient's disclaimer at
:789-796 is **backwards for this use** — it warns the quotient can say "reachable"
when the level is unsolvable, i.e. the error is one-sided and the safe side is
the *refutation* side. An over-approximation saying "unreachable" is a sound
unsolvability proof. D-EX-022 withdrew that number from the reasoning; it should
have been the alarm bell.

Criterion ranking: (d) measured failure of real complete solvers at declared
budgets > (c) proved lower bound on configurations > (b) our own enumerator
truncating (circular — we chose the enumerator; only honest use is _small_space's
positive claim) > (a) count over a threshold (asserted, not derived).

The D-024 crux resolves, but narrowly: a timeout carries **zero** information
about "is this unsolvable" (universal over plans, consistent with both truth
values) but is a **partial direct observation** of "is exhaustive search
infeasible" (itself a resource claim). Riders: existential not universal (name
the portfolio); evidential value is monotone in solver strength (which is exactly
why (b) is inadmissible — our enumerator is the weakest possible searcher); and
no inversion (`search_credible` rubrics_verdict.py:868-873 prices a reason rather
than setting a truth, so it survives, but it is one indirection away).

**Adopting (d) is fatal on these boards: the strong solvers will not time out,
they will win in milliseconds.** So the honest move is to weaken, not strengthen:
claim only that an examinee answering by explicit forward enumeration over
(cart, button, latch mask) cannot terminate; state that each item is settled by
relaxed reachability or an admissible heuristic at the root and that the quotient
is 180 states; and reframe what class (ii) measures as **method selection under an
apparent search barrier**. Rename `exhaustive_feasible: False` to
`naive_enumeration_feasible: False` and print the 180 next to the 10^36.
The sentence a reviewer would reject over is rubrics_verdict.py:11-12.

## Still outstanding
Lens 2 (experimental feasibility: real timings, a parametric k-comb growth curve,
and whether the negative control already exists) had not returned when this was
written. Check for it before starting.

## Lens 3 — experimental feasibility. All numbers measured on this machine.

**The measurement the repo never took, and it costs 3.6 s for all four items:**
every one of ii1/ii2/ii3/ii4 truncates `enumerate_states` at the 200k cap
(0.94 / 0.96 / 0.55 / 1.03 s). The bound itself costs ~2 ms. Today the truth
files record `truncated: false` — literally true only because no enumeration was
attempted, but it **reads as if one ran and came back clean**. Fixing that is
item 1 and it is nearly free.

**Direct demonstration of 10^12 is off the table.** Measured sweep on ii1:
200k states = 0.97 s / 108 MB; 3.2M = 64 s / 1.45 GB; throughput *degrades* with
size (206k → 50k states/s). Extrapolated, 10^12 needs **176 TB and ≥26 days**.
Affordable ceiling is ~5e6 states in a minute, ~2e5 in a second. "Raise
MAX_ENUMERATION" is dead on arrival — it buys one order of magnitude for 60 s.

**The buildable artifact is the parametric growth curve, and it is strong.**
Comb families enumerated to completion at k=1..9 match an exact closed form at
*every* k with no fitting: gantry/lattice measured = **2k · 4^k = 2k · 2^m**;
orchard = (2·4^k − 8)/3, ratio → **8/3**. So the shipped bounds are true and
loose by exactly 120× and 2.67×. ii1 and ii2 produce byte-identical counts — the
hazard seals the room exactly as the wall does, they are the same measured space.
Cost to ship as a test: **2.3 s**. Exponent verified over 5.1 orders of magnitude
of measured states, which is what licenses extrapolating to the shipped k=60.

**A LIVE DEFECT in the negative-control battery (work item 4 is partly done).**
Four controls: (A) 120 walled-off switches → refused by the threshold, m
collapses to 0, correct. (C) observation_loss and (D) forbid-DOWN → refused by
the lane AssertionError at :451, already tested. **(B) 60 switch entries all on
one cell → `subset_lower_bound` returns 2^60 = 1.15e18 and `_large_space` stamps
`exhaustive_feasible: False` on a level with 359 reachable states — an
overstatement of 3.2e15.** Neither the assertion nor the threshold refuses it.
It is caught only by `Level.wellformed_problems()` in `_self_check()`, which runs
at verdict.py:1278 — **after** every `_large_space()` call has already written the
false truth record. Existing `test_a_duplicated_switch_is_refused_by_the_builder`
asserts only that wellformed_problems flags it, NOT that the bound refuses.
Fix is two lines plus a real test.

Checked and found NOT defective: the two-sided-lane budget overstatement in m is
real but small and never produced a bound above the measured count in any swept
configuration; glyph/`switches` mismatch is unchecked but fails safe.

**Nothing hangs when a class-(ii) item is added.** `verdict.build()` = 0.38 s,
`enumerate_states` totals 2 ms across the whole build (it never touches a comb
level), test_verdict.py 50 passed 1 xfailed in 2.0 s. No blanket enumeration in
build or test path. But **adding a fifth class-(ii) item breaks three hard-coded
calibration counts** (test_verdict.py:481 `9.0/34.0` → 10/36, `{"none": 17}` → 18,
and :462 needs re-checking) plus artifact regeneration. Mechanical, but must land
in the same change or the suite goes red.

Could not measure: ii3 spindle has no closed form (step-limited, so the
k-families do not model it); its true count is unknown and a complete measurement
at the shipped budget of 150 is not reachable. Lens 3 ran only test_verdict.py,
not the full suite.
