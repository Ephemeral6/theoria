# Adversarial review, round 3 — against `fd362f02` and `ee9befa0`

An independent reviewer attacked the third-round corrections. **Five of them were
newly wrong**, and one of the new errors replaced a correct figure with an
incorrect one. Every finding below was then independently re-verified by RES-3
against the artefacts before being acted on; the verification commands and their
outputs are what the "confirmed" notes refer to.

The reviewer's own note on the moving target is worth keeping: HEAD advanced from
`fd362f02` to `ee9befa0` mid-review and `CRITERION.md` grew 334 → 357 lines. It
verified against both.

## Ranked

| # | finding | verdict | class |
|---|---|---|---|
| 1 | `~4e36` is wrong; `~6e36` was right. The "correction" shipped the extrapolated *state* count as an *edge* count | **CONFIRMED** | newly wrong |
| 2 | "All returned zero unsound rows" is false: 24 committed rows record `bound_is_sound: false`, and `unsound_rows: 0` is a *filtered* count that also drops the 52% of rows where the predicate was unevaluable | **CONFIRMED** | overclaim + newly wrong |
| 3 | `3.06 ms` **is** in a committed artefact. "≤3.1 ms" was a *satisfied bound over four committed measurements*, not one observation restated. The document now contradicts its own map | **CONFIRMED** | newly wrong, self-contradictory |
| 4 | The interval's lower endpoint `256` is stale; both controls are refused for every `T` tested down to 2. "Robust across ~16 orders" measures nothing about the threshold. "Asserts the cap ordering" mis-describes the code | **CONFIRMED** | newly wrong + (ii) |
| 5 | `engine-rig/DECISIONS.md:780-781` is **D-031**'s sentence citing D-024, not "D-024's own closing sentence" | **CONFIRMED** | newly wrong |
| 6 | The "complete" provenance map omits work item 4's negative controls, the 1,034 rungs, and `n_pos=5`; and repeats an A2 claim RUN_STATE records as unmeasured | **CONFIRMED** | (ii) at one remove |
| 7 | `758 of 1024` is not reproducible from HEAD — the repo's own reconstruction gives m=11, and m=44 where 40 is recorded | **UNVERIFIABLE**, load-bearing | (iii) |
| 8 | ii3's `seconds` column reports the timing of the pass that explicitly did *not* settle ii3 | **CONFIRMED** (minor) | (ii) |
| 9 | `total_seconds: 122.247` is the whole script, not "k=1..9" (~104.6 s); the k≤6 per-rung sum is 0.629 s, not "a few seconds" | **CONFIRMED** | (ii) |
| 10 | `[0, 1]` survives; the monotone-column argument still follows | **STANDS** | — |

## The verifications, so the next reader need not redo them

**1 — the edge count.** `probe_lp_interface.json` → `E_comb` is the only place the
×4.0 is measured. Its last rung is corridor 10: `reachable_states 2,796,200`,
`edges 4,893,348`, and `edges/states = 1.7500` at every rung. Carrying ×4.0 to
corridor 60:

* edges: `4,893,348 × 4^50` = **6.20e36** → `~6e36`, the original figure
* states: `2,796,200 × 4^50` = **3.55e36** → rounds to `~4e36`

So `~4e36` is the extrapolated *state* count wearing the word "edges", off by
exactly the `edges/states` factor the same artefact measures to three decimals.
`exam/DECISIONS.md` never stopped saying `~6e36` and was right the whole time.

**2 — the attacks did not come back clean.** `attack_straddle.json`:
`all_rows` 147 total, **21 with `bound_is_sound: false`**, max `overstatement`
**2.62** (the reviewer said 1.31; that is `control_rows`' max — `all_rows` is
worse); `control_rows` 63 total, **3 false**, max 1.31. Truncated: 109 of 147 and
45 of 63. `unsound_rows: 0` is produced by a filter that drops `truncated` rows
(`attack_straddle.py:81-84`), and all 21 false rows are truncated with
`measured_states: 200000` — the predicate was comparing the bound against the
*cap*, not against a count. `attack_barbell.py:86` handles the same case by
setting `bound_is_sound` to `None` instead (71 such rows). Net: **180 of 347
sweep rows (52%) never produced a meaningful predicate value.**

This makes the section's own thesis stronger, not weaker. The first-order reason
the attacks found nothing is a coverage hole plus a summary field that silently
drops it; "the predicate was weaker than the claim" is the second-order reason.
A section arguing that *"the attack found nothing" is only as strong as its
predicate* had itself quoted that attack's summary field without checking what
the field counted.

**3 — the certificate timing.** `probe_answer_key.json` →
`check_certificate_seconds`: **0.00306, 1e-05, 0.00075, 0.00149**, one per
record. Max 3.06 ms, so "≤3.1 ms" was true, checkable, and sourced. It was not a
bound invented from one observation. And the map row naming
`probe_answer_key.json` as the source of "the reference answer keys and
certificate timings" sat 250 lines from a caveat listing "the
certificate-checking times" among the numbers with no committed artefact — two
claims about the same number, in the document whose subject is provenance.

**4 — the threshold interval.** Run directly, patching
`LARGE_SPACE_THRESHOLD` and calling `_large_space` on both controls:

| T | ctl1 (lb=16) | ctl2 (lb=256) |
|---|---|---|
| 2 | REFUSED (gate 2) | REFUSED (gate 2) |
| 100 | REFUSED (gate 1) | REFUSED (gate 2) |
| 256 | REFUSED (gate 1) | REFUSED (gate 2) |
| 257 … 2^60+1 | REFUSED (gate 1) | REFUSED (gate 1) |

Both controls are refused at **every** T tested, including 2. The refusal simply
migrates to the second gate, `lower_bound <= MAX_ENUMERATION`. So `256` — which
is control 2's own bound — is the endpoint you get if gate 1 is the only refusal,
i.e. the derivation predates the gate the *same commit* added. Over
`(256, 200000]` gate 1 is dead code: any `lb < T ≤ 200,000` also satisfies
`lb ≤ 200,000`.

The honest conclusion is therefore **weaker and more interesting** than the one
claimed: these cases cannot distinguish `10^12` from `2`, so the audit set does
not constrain the threshold from below at all. "Robust across ~16 orders" was a
property of the audit set, not of the threshold — a tautology dressed as a gate,
which is the exact phrase the section uses to reject criterion (a).

Also: "`_large_space` now asserts the cap ordering instead of trusting it" is
wrong about the code, and the code is right. `verdict.py:902` asserts a property
of each *bound*, and its own comment says why that was chosen over an ordering
check: "Checked rather than inherited from the ordering, because the ordering is
not stated anywhere as a requirement and either constant can be moved by someone
who never reads this function." The prose summary was worse than the code it
summarised.

**5 — the attribution.** `engine-rig/DECISIONS.md` headings: `## D-024` at 466,
`## D-031` at **730**, `## D-032` at 792. Lines 780-781 sit inside **D-031**, and
the sentence reads "it is *the same distinction D-024 had to make* for Fast
Downward" — D-031's phrasing drawing an analogy. The pre-`fd362f02` text carried
a bare anchor; the commit narrowed the range correctly and invented a false
provenance in the same breath, inside the paragraph about anchor discipline.

**6 — the map.** Work item 4's five numbers (`6,480 states`, `0.01 s`, `m=4`,
`2^4=16`, `2^8=256`) come from `exam/tests/test_verdict.py:500-553` and have no
map row at all; `0.01 s` is asserted nowhere, appearing only in a test docstring.
The 1,034 reviewer rungs have no artefact and are in neither exception list.
"Verified exhaustively over all role assignments at n_pos=5" is unsourced —
`E_comb`'s `n_pos` runs 10, 15 … 50 and nothing in `probe_lp_interface.json`
mentions 5. And the A2 half (`a2_plain_move: 0`, `a2_latching_move: 1`) is a pair
of Python literals printed as if measured, which RUN_STATE records and the commit
whose stated purpose was to transfer RUN_STATE's corrections did not transfer.

**8 — ii3's timing.** ii3 has `settled_by_partition: false`,
`settled_by_budget: true`, and `timing_seconds`
`{compute_lower_bound: 0.0047, enumerate_quotient: 0.0012, settle_via_components:
0.0016}`. The table's `0.0016` is the components pass — the one the document
elsewhere takes pains to say did *not* settle ii3. The artefact times the budget
check not at all. The `≤5 ms` headline survives (ii3's largest is 0.0047).

**9 — what 122.247 covers.** Per-rung sums from `growth_curve.json`: gantry
k1–9 34.611 s, lattice k2–9 35.044, spindle k1–9 34.286, orchard k2–9 16.462 —
but orchard runs to k=11 (`"10": 2.322`, `"11": 13.484`). The k≤9 rungs total
~104.6 s; `122.247` is the whole script. And the k≤6 rungs sum to **0.629 s**,
not "a few seconds" — the 2.918 s rerun is whole-script wall-clock, a different
quantity, and the document did not distinguish them.

## What the reviewer tried and could not break

Recorded because a documented failed attack is a result, and because the previous
three rounds' failures came from not stating their predicate:

* `[0, 1]` on the multiplicity angle — immune, because the predicate is `min`,
  which is multiplicity-free. `min({0,1}) = 0 ≥ 0` and `1 < 2`, so the
  monotone-column argument follows under either reading.
* the interval's **upper** endpoint — exact and correctly closed: `2^60` keeps
  all labels, `2^60+1` flips ii3.
* the map's artefact side — all 11 evidence artefacts in the run directory
  appear in the table. The gap is on the section side.
* `347` rows and `147 KB` — both correct.
* symbol-name uniqueness — `subset_lower_bound`, `quotient_note` and
  `_large_space(lvl)` are each unique. Two soft spots: bare `_large_space` greps
  ~15 hits, so the anchor is unique only in the parenthesised form; and
  `_self_check`'s *definition* (1509) is **below** all seven call sites while its
  *invocation* (1443) is above them, so "all seven sit above it" is true of the
  call and false of the definition, in a sentence that names the symbol.
* all three surviving `file:line` anchors open onto what they claim, and
  `git diff 415556f8..HEAD` touches none of those three files.

## Zero-contact

No network, no API calls, nothing under `environment_files/`, no sealed-pile game
named or read. Local reads plus in-process Python against `exam/`.
