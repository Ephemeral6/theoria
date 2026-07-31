# Adversarial round 5 — V6-V23, class (ii)

Method: for every number, claim and citation in `CRITERION.md` and `RUN_STATE.md`,
ask *which committed file emits this, and can I open it and see this exact value*.
Scripts re-run where deterministic. Written incrementally.

Base: worktree `.worktrees/v6-v23-large-space`, tip `08820583`.

---

## F5-1 (HIGH) — round four's correction landed in the document but not in the code it corrects

`CRITERION.md:80-97` withdraws the claim that the threshold interval is
`(256, 1.15e18]` and "robust across ~16 orders", concluding: *"'Robust across ~16
orders' was a property of the audit set masquerading as a property of the
constant — a tautology dressed as a gate."*

The sentence it withdraws is still shipped verbatim in the source file the same
section points at as the place the constant "now carries its argument":

`exam/papers/verdict.py:99-103`
```
#: ordering rather than trusting it. Measured margins: every shipped class (ii)
#: item clears this by 6 to 24 orders (smallest bound 2^60 = 1.15e18), and any
#: threshold in (256, 1.15e18] labels the same seven records and refuses both
#: negative controls, so the choice is robust across ~16 orders rather than
#: knife-edge. The constant is a floor with margin, not a measurement.
```

- Claimed (`CRITERION.md:74-76`): "The constant now carries its argument at its
  definition: the requirement is only `> MAX_ENUMERATION` ... It is a floor with
  margin, not a measurement."
- Observed: the definition's comment carries that argument **plus** the refuted
  one, unmarked, in the same paragraph.

`RUN_STATE.md:207-210` also still carries the refuted sentence uncorrected:
"any threshold in (256, 1.15e18] labels the same seven records and refuses both
negative controls — robust across ~16 orders". `RUN_STATE.md` has a third-session
section that closes each correction; this one is not closed there.

Severity: HIGH. A withdrawn claim still shipped in a tracked source file is
exactly the failure mode the ticket exists for, and the document asserts the
opposite about that file.

---

## F5-2 (HIGH) — `verdict.py` contradicts itself about the guard, and `CRITERION.md` quotes only the half that agrees with it

`CRITERION.md:99-105`:
> One further correction to round three's wording: it said "`_large_space` now
> asserts the cap ordering instead of trusting it". It does not, and the code is
> right where the prose was wrong. ... and its own comment says why that was
> chosen over an ordering check — "the ordering is not stated anywhere as a
> requirement and either constant can be moved by someone who never reads this
> function".

The quoted comment exists (`exam/papers/verdict.py:899-901`). But the *same file*
says the refuted thing at `exam/papers/verdict.py:98-99`:

```
#: does not silently reclassify an item -- and `_large_space` now asserts the
#: ordering rather than trusting it.
```

- Claimed: the wrong prose was round three's, and "the code is right where the
  prose was wrong."
- Observed: the wrong prose is *in the code*, 800 lines above the comment
  `CRITERION.md` quotes as the authority. `RUN_STATE.md:202` repeats it a third
  time ("`_large_space` now asserts the ordering.") and is not corrected in the
  third-session section either.

By the document's own standard ("A summary of a guard should not claim more than
the guard", `CRITERION.md:105`), `verdict.py:98-99` is that defect, uncaught.

Severity: HIGH.

---

## F5-3 (CRITICAL) — the fix for round four's "hand-written literal" finding is a measurement that cannot terminate, and its artefact was never regenerated

Round four's finding (`CRITERION.md:337-343`, `RUN_STATE.md:340-345`):
`D_verdict`'s `a2_plain_move: 0` / `a2_latching_move: 1` are Python literals
printed as if measured.

`probe_lp_interface.py` was subsequently changed (commit `722b6e8e`) to measure
them. `probe_lp_interface.py:216-247`:

```
    # Those two numbers used to be written here as the literals `% 0` and `% 1`,
    # ... Now enumerated off a real A2
    # level, so the record measures both sides of the claim it makes.
    a2 = _measure_a2_coefficient_sums()
```

`_measure_a2_coefficient_sums` (`probe_lp_interface.py:36-49`) BFSes the full
`(cart, pressed, mask)` space of `V.comb_open("lp-iface-a2", 20, 1, 20)` — a comb
at corridor 20 with **40 distinct latch bits**.

Measured directly (45 s run of exactly that loop):

```
switches: 40   distinct latch bits: 40
predicted reachable (2k*4^k, k=20) = 4.398e+13     <- this run's OWN closed form
ABORTED after 45s: seen=7547299 frontier=191 transitions=30188432
```

7.5e6 of 4.4e13 states in 45 s. The probe does not terminate; at that rate it is
~76 years. The module docstring (`probe_lp_interface.py:3`) still says "Five
probes, all offline, all under a second each except where noted".

Consequences, all checkable:

- **`probe_lp_interface.json` is stale against its own generator.** Committed
  `D_verdict` (artefact, unchanged since `1486875e`):
  `{"a2_latching_move": 1, "a2_plain_move": 0, "expressible": false,
  "lp_move_coefficient_sum": -1}` — 4 keys.
  Current generator emits 7: it adds `a2_coefficient_sums_measured`,
  `a2_transitions_enumerated`, `a2_level_id`, `how`.
  `git log -1 -- probe_lp_interface.py` → `722b6e8e`;
  `git log -1 -- probe_lp_interface.json` → `1486875e`.
- The correction's own comment states the fix in the **past tense** ("Now
  enumerated off a real A2 level, so the record measures both sides") while the
  record measures neither new side and the enumeration has never run.
- The fix chosen for "an unmeasured claim" is an enumeration over a board of
  exactly the size this ticket's whole thesis says cannot be enumerated
  (`naive_enumeration_feasible: False`, cap 200,000; this board is 4.4e13).
- This is the third artefact-stale-against-generator instance in this run
  (`probe_answer_key.json` pre-rename was the first, `DRILL.json` the declared
  second), and the only one not disclosed anywhere.

Severity: CRITICAL. A committed artefact that its committed generator cannot
reproduce, presented in `CRITERION.md`'s provenance map as the emitted evidence
for work item 3.

---

## F5-4 (MEDIUM) — round four's "the figure 5 appears nowhere" is itself wrong

`CRITERION.md:334-336`:
> Earlier drafts said this was "verified exhaustively over all role assignments
> at **n_pos=5**"; no such run is in the artefact, whose `n_pos` values run
> 10, 15 … 50, and the figure 5 appears nowhere — so the *exhaustiveness* is
> unsourced even though the coefficient sum is measured.

Observed, `probe_lp_interface.py:202-214`:
```
    sums = set()
    n = 5
    for src in range(n):
        for over in range(n):
            for dst in range(n):
                ...
    print("  coefficient-sum over all %d role assignments (n=%d): %s"
          % (n ** 3, n, sorted(sums)))
    OUT["D_coefficient_sums"] = sorted(sums)
```

The exhaustive loop *is* at n = 5, it is `5**3 = 125` role assignments (the same
125 `RUN_STATE.md:342` cites), and `D_coefficient_sums: [-1.0]` in the artefact is
that loop's output. The exhaustiveness is sourced — in the committed generator.

The correction conflated two different `n`s: probe D's LP row width `n` and probe
B/E's `n_pos` rung parameter (10, 15 … 50). "The figure 5 appears nowhere" is true
of the JSON and false of the run: `probe_lp_interface.py:203` is `n = 5`.

Severity: MEDIUM. A round-four correction that withdrew a true claim.

---

## F5-5 (HIGH) — the line anchors were "switched to symbol names" in `CRITERION.md` only; a committed artefact of the same run still publishes nine rotted `verdict.py` anchors

`CRITERION.md:227-233` and `RUN_STATE.md:328-332` record the fix: anchors into
`verdict.py` replaced by symbol names, because "an anchor into a file its own
commit edits will rot again" (P21/P22).

`repro_duplicate_switch.json` — cited in `CRITERION.md`'s own provenance map
(row "the duplicate-switch overstatement") — carries field `wellformed_runs_at`:

```
"exam/papers/verdict.py:1278 `_self_check(items)` -> :1354
 `level.wellformed_problems()`; every `_large_space()` call sits at
 verdict.py:1010/1030/1055/1081/1212/1241/1267, all above it"
```

Observed in `exam/papers/verdict.py` at HEAD `08820583`:

| claimed | observed |
|---|---|
| `_self_check` at 1278 | **1509** |
| `wellformed_problems()` at 1354 | **1525** |
| `_large_space(lvl)` at 1010/1030/1055/1081/1212/1241/1267 | **1175/1195/1220/1246/1377/1406/1432** |

All nine are wrong. Same strings at `repro_duplicate_switch.py:16` and
`:115-117`. The *ordering* claim ("all above it") still holds; every number does
not. This is a published artefact, not a comment.

Severity: HIGH.

---

## F5-6 (MEDIUM) — a *fourth* rotted line anchor, in `RUN_STATE.md`, into a file this run's own commits grew

`RUN_STATE.md:145`: "Already at `exam/STATUS.md:597-598`; repeated because the
rename passes through that line."

- At base commit `415556f8`: `exam/STATUS.md:597` **is** item 28, "The `searcher`
  probe cannot see a wrong `search_credible`." The anchor was correct when written.
- At HEAD `08820583`: item 28 is at `exam/STATUS.md:608-610`. Lines 597-598 now
  read "most 600 nodes in at most 5 ms against bounds of 1.15e18 to 1.33e36, so /
  `exhaustive_feasible: False` was false and is withdrawn for" — i.e. this run's
  own new item 27.

Rotted 11 lines, by this run's own edit to that file, which is the exact P21/P22
mechanism round three's fix was justified by. Rounds 3 and 4 de-numbered
`verdict.py` anchors and left this one.

Secondary: `RUN_STATE.md:142` names it "**The calibration gate** cannot catch a
wrong `search_credible`", while `exam/STATUS.md:608` names "**The `searcher`
probe**". `calibration.py:318` and `rubrics_verdict.py:869` both verify (both read
`search_credible`), but STATUS.md's separate "calibration gate" item is at line
478 and is about something else.

Severity: MEDIUM.

---

## F5-7 (MEDIUM) — the file cited as proof that "filed" is no longer just a word is in no commit on any ref

`CRITERION.md:484` and `RUN_STATE.md:126-130` both cite
`monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`,
`RUN_STATE.md:130` adding "which is a real file rather than a word."

Observed:
- absent from this worktree: `ls monitor/inbox/ | grep 071500` → nothing;
- `git log --all --oneline -- monitor/inbox/20260730T071500Z-RES-3-*` → **empty**
  (no commit on any ref anywhere in the repo contains it);
- it exists only as an **untracked** working-tree file in the *main* worktree,
  `C:\Users\user\Desktop\theoria\monitor\inbox\...` (4525 bytes, `git status` `??`).

RES-3's seven earlier inbox notes are all tracked (`git ls-files monitor/inbox/`),
so the convention is that these get committed. The paragraph whose subject is
"'Filed' implies a ticket exists; none did ... the cheapest to have checked — one
`ls`" is itself checked by one `ls` and fails on the branch it ships on.

Severity: MEDIUM (qualified: `monitor/inbox/` holds 95 untracked files alongside
135 tracked, so this may be an intended drop-box state — but not on this branch,
and not by RES-3's own precedent).

---

## F5-8 (MEDIUM) — "6 is the largest rung that can be enumerated to completion under `MAX_ENUMERATION` at all" is refuted by the artefact cited in the same sentence

`CRITERION.md:296-299` (and `RUN_STATE.md:69-71`):
> gantry at k=7 is 229,376 states, past the shipped cap, so 6 is the largest rung
> that can be enumerated to completion under `MAX_ENUMERATION` at all.

`growth_curve.json`'s own `families[orchard].rows`:

| k | measured_states | < MAX_ENUMERATION (200,000)? |
|---|---|---|
| 7 | 10,920 | yes |
| 8 | 43,688 | yes |
| 9 | **174,760** | **yes** |
| 10 | 699,048 | no |

gantry k=7 = 229,376 reproduces exactly. But orchard completes at k=9 under the
cap. The true statement is "6 is the largest rung at which *all four* families
complete", which is what the ladder needs; "at all" overstates it by three rungs,
against the artefact quoted beside it.

Severity: MEDIUM.

---

## F5-9 (LOW-MEDIUM) — "`edges/states = 1.7500` … at every rung" is measured at 4 of 9 rungs and is exact at none

`CRITERION.md:319-320`: `~4e36` is the state count "wearing the word 'edges', off
by exactly the `edges/states = 1.7500` that the same artefact measures at every
rung".

Computed from `probe_lp_interface.json`'s `E_comb` (the artefact has no
`edges/states` field; this is derived):

| corridor | states | edges | edges/states |
|---|---|---|---|
| 2 | 40 | 68 | **1.7000** |
| 3 | 168 | 292 | **1.7381** |
| 4 | 680 | 1,188 | **1.7471** |
| 5 | 2,728 | 4,772 | **1.7493** |
| 6 | 10,920 | 19,108 | **1.7498** |
| 7 | 43,688 | 76,452 | 1.749954 |
| 8 | 174,760 | 305,828 | 1.749988 |
| 9 | 699,048 | 1,223,332 | 1.7499971 |
| 10 | 2,796,200 | 4,893,348 | 1.7499993 |

It is 1.7500 to 4 d.p. at 4 of 9 rungs, is 1.70 at the first, and is exactly
1.7500 at none. The ratio the arithmetic actually uses (4,893,348 / 2,796,200) is
the last rung only.

Severity: LOW-MEDIUM — "at every rung" in a passage whose whole point is
distinguishing measured from asserted.

---

## F5-10 (HIGH) — round four restored `≤3.1 ms` in `CRITERION.md` and left the decision record holding the withdrawn position

`CRITERION.md:358-373` restores the bound and calls round three's removal "wrong
twice": "the figure is a true bound over four committed measurements ... Restored,
with the four values printed ... The 3.66 ms rerun is prose-only and is not what
the bound rests on."

`exam/DECISIONS.md` — the durable record — was not updated and says the opposite,
in two places:

- `exam/DECISIONS.md:1119-1120`: "`rubrics_verdict.check_certificate`,
  purpose-built for this world, **single-digit milliseconds per item** (`"<=3.1
  ms"` as first written restated one observation as a bound; see D-EX-029)".
- `exam/DECISIONS.md:1253-1258`, under the heading "Correction to this entry's own
  neighbourhood": "D-EX-028's closing survey states `check_certificate` runs at
  '<=3.1 ms per item'. That restates one wall-clock observation as a bound, and a
  timing is not a bound — reruns give 3.06 ms and 3.66 ms ... **The defensible
  claim is the order of magnitude.**"

`RUN_STATE.md:314-316` also still carries the withdrawal, under "What it found not
reproducible, and what is being corrected in the documents rather than defended",
with no closing note in the third-session section.

So after round four the run document and the decision record disagree about one
number — precisely the defect `CRITERION.md:317-318` names for `~6e36` ("for one
commit the run document and the decision record disagreed, with the decision
record holding the correct value"). Round four fixed that instance and created a
new one in the opposite direction in the same commit.

Method note: `CRITERION.md:373` discards the 3.66 ms rerun because it is
prose-only. The repo's precedence rule ranks evidence *for* a claim; using it to
discard a counter-observation *against* a bound is a different move. The bound is
true over the four committed samples; it is not established as a bound.

Severity: HIGH.

---

## F5-11 (MEDIUM) — the "≤5 ms" headline fails on rerun, while the document says no claim rests on a timing

`CRITERION.md:41-43`: "**All timings are machine-dependent.** No claim here rests
on one."

`CRITERION.md:163-164`, the headline of the substantive section: "settled by an
exhaustive computation over a graph of at most 600 nodes, **in at most 5
milliseconds**." The same sentence ships in three further places:
`RUN_STATE.md:19`, `exam/papers/verdict.py:914` (inside the
`naive_enumeration_feasible` comment, i.e. in tracked source), and
`exam/STATUS.md:596-597`.

Re-ran `crux_quotient_settles.py` on this machine (deterministic fields
byte-identical to HEAD; only `timing_seconds` moved):

| item | committed max | rerun max |
|---|---|---|
| ii1 | 0.0021 | 0.0027 |
| ii2 | 0.0019 | 0.0025 |
| ii3 | **0.0047** | **0.0051** |
| ii4 | 0.0012 | 0.0017 |

ii3's `compute_lower_bound` reruns at 5.1 ms — the headline is false on the first
rerun on the same machine. The **600-node** half is structural and reproduces
exactly; the millisecond half does not. A claim does rest on a timing, in four
files, one of them source.

Severity: MEDIUM.

---

## F5-12 (MEDIUM) — "Both are now rows" — one of the two is not a row

`CRITERION.md:50-52`: "The reviewer's own 1,034 rungs likewise had no artefact and
appeared in no exception list. **Both are now rows.**"

Observed: the provenance map (`CRITERION.md:14-25`) has ten rows. Work item 4's
numbers are row 9 ("**not an artefact** — `exam/tests/test_verdict.py`"). There is
**no row for the 1,034-rung sweep**: `grep -n "1,034" CRITERION.md` returns only
lines 51 and 407, and 407 is the prose citing it. It is also still absent from the
exception list at `CRITERION.md:30-39`.

The round-four correction to a completeness claim is itself incomplete, in the
paragraph that concludes "a completeness claim over a document that is still being
edited is a claim with a short shelf life".

Severity: MEDIUM.

---

## F5-13 (MEDIUM-HIGH) — the ruling says both conditions "are recorded as measurements"; the record says condition (b) was never attempted

`CRITERION.md:139-150`:
> An item is class (ii) when **both** hold, **and both are recorded as
> measurements**:
> 1. **(c)** a constructive lower bound of 2^m ...
> 2. **(b)** the reference enumerator ... **measured to truncate at the shipped
>    cap on this level. Measured, not assumed.**

Observed, by running `V.build()` and reading all seven records whose
`state_space.naive_enumeration_feasible is False`:

```
m                     = [120, 60, 118, 120, 120, 120, 120]   # matches RUN_STATE:188
enumeration_attempted = False   (all seven)
truncated             = None    (all seven)
```

And `_large_space` (`exam/papers/verdict.py:886-909`) applies exactly two gates,
**both functions of `lower_bound` alone**: `lower_bound < LARGE_SPACE_THRESHOLD`
and `lower_bound <= MAX_ENUMERATION`. There is no (b) gate in the builder; the
truncation claim is *derived* from (c), as `enumeration_refused_because` says.

(b) *is* measured — by `test_class_ii_levels_actually_truncate_the_enumerator`
(all seven; `assert len(items) == 7`) and by `enumeration_probe.json` (four of the
seven). But "both are recorded as measurements" is false of the record, which
records the opposite for (b), and the conjunction the code enforces is
threshold ∧ cap over one quantity, not (c) ∧ (b).

This is the criterion-vs-code gap in its surviving form: the earlier record was
*counterfactual* (`"truncated": False`) and is now *honest* (`None` +
`enumeration_attempted: False`), but the prose describing it did not narrow with
the record.

Severity: MEDIUM-HIGH.

---

## F5-14 (LOW) — the provenance map's criterion-(b) row covers four of seven records

`CRITERION.md:16`: "| the ruling, criterion (b) | `enumeration_probe.json` |".

That artefact's `deterministic.items` holds nine rows: i1-i5 (`_small_space`) and
ii1-ii4 (`_large_space`). The three `solvable_hard` records that also carry
`naive_enumeration_feasible: False` — the ones `RUN_STATE.md:78-81` makes a point
of ("`_large_space` is called by seven items, not four") — are absent. Their (b)
evidence is the test only.

Severity: LOW.

---

## Trivia (not findings; recorded so they are not re-found)

- `CRITERION.md:419` cites `attack_straddle.py:81-84` for the truncated-row
  filter. The `rows` filter is 81-83; line 84 begins the separate `control` filter,
  which does the same thing. Off by one statement boundary. `attack_barbell.py:86`
  is exact.
- `CRITERION.md:361` prints `0.00001` where the artefact stores `1e-05`.
- Another session is concurrently writing this run directory
  (`BASELINE-cycle94.md`, untracked, mtime 16:47). Not touched.

---

## Load-bearing claims attacked and NOT refuted

Reproduced or verified exactly. I could not break any of these.

1. **The crux table** (`CRITERION.md:166-171`) — every cell traces to
   `crux_quotient_settles.json`: ii1 1.329e36 / 300 nodes / 0.0010
   (`settle_via_components`); ii2 300 (`cut_graph_nodes`) / 0.0001
   (`settle_via_cut_set`) / cut cell `[4,2]`; ii3 600 nodes / distance 199 /
   budget 150 / `settled_by_budget: true`, `settled_by_partition: false`; ii4
   3.323e35 / `surviving_column_deltas: [0,1]` / `goal_column 1 < start_column 2`
   / 0.0. Round three's `{0,0,+1}` → `[0, 1]` fix is correct.
2. **ii3's three timings** 0.0047 / 0.0012 / 0.0016 are all in the artefact, and
   0.0016 is indeed `settle_via_components` — the pass that did *not* settle ii3.
   Round four's reasoning there is right.
3. **The crux script is deterministic.** Re-ran it: every field except
   `timing_seconds` is byte-identical to HEAD, and no output value is a literal
   (`settled_by_partition`, `settled_by_cut_set`, `settled_by_budget`,
   `settled_by_monotone_column`, `surviving_column_deltas` are all computed at
   `crux_quotient_settles.py:73-147`).
4. **Round four's threshold sweep.** Patched `LARGE_SPACE_THRESHOLD`, called
   `_large_space` on both controls: T=2 → both refused at gate 2; T=17 → ctl1 at
   gate 1, ctl2 at gate 2; T≥257 → both at gate 1. "Both controls are refused at
   every T tested, down to T=2" holds, and gate 1 is genuinely redundant over
   (256, 200000]. The upper endpoint is exact: ii3's bound is 2^60 to the digit.
5. **Round four's `m=11` / `m=44` reconstruction.** Ran the removed pre-fix loop
   from `test_verdict.py:1127-1135`: **m=11 (2^11=2048)** at `_straddle_board()`
   and **m=44** at corridor 60 — exactly what `CRITERION.md:441-444` reports
   against the prose's 10 and 40. The "cannot be settled from anything committed"
   finding stands.
6. **`test_verdict.py`'s work-item-4 assertions.** `6480` (:518), `m == 4` (:522),
   `lower_bound == 16` (:523), `2 ** 8` (:549), `bound["m"] == 8` (:1122),
   `m == 29` (:1151). `0.01 s` really does appear only in the docstring (:506).
7. **`growth_curve.json` arithmetic, all of it.** `total_seconds: 122.247`;
   per-rung k≤9 sum = **104.597** ("~104.6"); k≤6 sum = **0.629**; orchard k=10
   = 2.322, k=11 = 13.484; balance 1.844 = the budget probe. gantry k=7 =
   **229,376**. Largest measured count **4,718,592** ("4.7e6").
   `verified_orders_of_magnitude = 5.771` ("5.77"). Closed forms `2k·4^k` (m=2k)
   and `(2·4^k−8)/3` (m=2(k−1)) hold at every row. `growth_curve.py` is **not**
   budget-driven — the extra orchard rungs come from a declared `kmax_bonus: 2`
   (:159) — so `enumeration_sweep.py` is the only non-reproducing script, as stated.
8. **`probe_lp_interface.json`'s E_comb arithmetic.** Last rung corridor 10,
   2,796,200 states, 4,893,348 edges. `4,893,348 × 4^50 = 6.203e36` ("6.20e36")
   and `2,796,200 × 4^50 = 3.545e36` ("3.55e36"). The ×4.0 state scaling
   converges to 4.0000. `exam/DECISIONS.md:1096` does say `~6e36`, so round four's
   account of that divergence is right.
9. **`D_coefficient_sums == [-1.0]`** in the artefact, and `potential.py:306-308`
   is exactly `row[dst] += 1.0 / row[src] -= 1.0 / row[over] -= 1.0`.
10. **The certificate timings.** `probe_answer_key.json` records
    `MEASURED.check_certificate_seconds` = 0.00306 / 1e-05 / 0.00075 / 0.00149 —
    the four values `CRITERION.md:361` prints; max 3.06 ms. (What the *bound*
    means is F5-10; the four numbers are sourced.)
11. **Both attack artefacts, every count.** straddle: 147 `all_rows`, **21**
    `bound_is_sound: false`, max `overstatement` **2.62144**, all 21 truncated at
    `measured_states: 200000`; 63 `control_rows`, **3** false, max **1.31072**.
    barbell: 200 rows, **71** `None`. 147+200 = **347**. Truncated straddle rows
    (109) + barbell `None` (71) = **180** = 51.9% ≈ **52%**. Every number exact.
12. **`enumeration_probe.json` measures criterion (b)** for ii1-ii4: all four
    `truncated: True`, `hit_cap: True`, `states_visited: 200000`,
    m = 120/120/60/118.
13. **`repro_duplicate_switch.json`**: `true_reachable_states: 359`,
    `switch_entries: 60`, `distinct_switch_cells: 1`; 2^60/359 = 3.21e15 ("3.2e15").
14. **The seven-call-site and `_self_check` ordering claim.** Seven
    `_large_space(lvl)` sites at verdict.py 1175/1195/1220/1246/1377/1406/1432,
    all above `_self_check` (1509), which is the only caller of
    `wellformed_problems()` (1525). Every symbol name `CRITERION.md` uses exists.
15. **The three kept line anchors.** `Theoria.md:259` is the 判决题 line and does
    split verdict items three ways with (ii) = "大空间不可解……我们的主场".
    `engine-rig/DECISIONS.md:780-781` is "a proof and a shrug must not / share a
    return value", and it is D-031's sentence (heading at **730**) citing D-024
    (heading at **466**) — round four's correction is exact.
    `worldgen/core/world.py:259` is `def reachable(self, limit: int = 200_000)`
    and it does `raise RuntimeError` above the limit (:269-270).
16. **`rubrics_verdict.py:869` and `calibration.py:318`** both read
    `search_credible`, as claimed.
17. **`DRILL.json`**: `coverage.classes_absent == ["large_unsolvable"]`, and
    `classes_absent_because` names 2654 states (t3-full-house), matching
    `RUN_STATE.md:292`.
18. **The corridor-4 silent `certified`** is measured and recorded — not in the
    JSON but in `invariant_path_probe.md:156-171` ("the goal state ... **is in the
    forward closure from the start** — the level is **SOLVABLE**"; 1188/1188 edge
    deltas mismatched, which `E_delta_mismatch` in the JSON confirms). Every
    `E_comb` row is `certified`, including corridor 4.
19. **The seven shipped records are unchanged** at m = 60, 118, 120×5, and the
    spindle `arithmetic` does print the measured sweep: "the step budget (150)
    affords the first 60 of them at a cost of **149 commands**".
20. **`ic3_pdr` exists** (`engine-rig/engines/ic3_pdr/`) — CLAUDE.md's six-engine
    list is what is stale, not this document.

## Sealed-pile constraint

Nothing here touched `arc-recon/`, `environment_files/`, or any game. No claim
was left unverifiable for pile reasons.

## One-line verdict on round four

Round four's *analytical* corrections held under reproduction — the threshold
sweep, the m=11/m=44 reconstruction, the ii3 timing attribution, the `~6e36`
restoration and the D-024/D-031 attribution all check out — but three of them did
not land where the claim lives (`verdict.py`'s own comment, `exam/DECISIONS.md`,
the map's missing 1,034-rung row), one withdrew a true claim (`n = 5`), and the
code fix it triggered in `probe_lp_interface.py` is a measurement that cannot
terminate, against an artefact that was never regenerated.

