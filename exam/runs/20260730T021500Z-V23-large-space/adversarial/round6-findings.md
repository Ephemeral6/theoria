# Adversarial round 6 — V6-V23, auditing round five's *fixes*

Method: round five found 14 defects; RES-3 dispositioned all 14 over cycles
96-104, landing `b43427f0` … `e4b25676`. This round does not re-find round five's
bugs. It asks, of each fix: **does the fix say something true, does it say it in
the place the claim lives, and does the artefact it points at emit the numbers
the document quotes.** Everything below was re-run or recomputed; nothing is
taken from a commit message.

Anchors are symbols and JSON keys, never line numbers — the three previous rounds
each shipped a rotted line anchor and two of those were findings in their own
right.

Base: worktree `.worktrees/v6-v23-large-space`, tip `e4b25676`, tree clean at
start and restored at end.

---

## F6-1 (HIGH) — `CRITERION.md`'s account of the A2 measurement quotes an artefact state that was superseded two commits *before* the paragraph was written

`CRITERION.md`, work item 3, the paragraph headed "**The A2 side was a
hand-written literal, and the fix took two attempts (round five).**" describes
the shipped `D_verdict` as:

> the A2 side is enumerated over **five small levels** chosen to cover every
> branch of `Level.step` … `a2_coefficient_sums_measured` of `[0, 1]` over
> `a2_transitions_enumerated` = **51,164** transitions across
> `a2_states_enumerated` = **12,791** states, `a2_step_branches_covered` listing
> all six branches …

The committed artefact `probe_lp_interface.json` emits, in `D_verdict`:

| field | `CRITERION.md` | `probe_lp_interface.json` |
|---|---|---|
| levels enumerated (`a2_level_ids`) | five | **nine** |
| `a2_transitions_enumerated` | 51,164 | **51,880** |
| `a2_states_enumerated` | 12,791 | **12,970** |

All three of the document's figures are the artefact's *previous* values. The
four extra levels — `updraft`, `cistern`, `quarry`, `meander` — were added to
`_measure_a2_coefficient_sums` in `9cf779a3`, which also regenerated the JSON;
51,164 and 12,791 are exactly the sums over the first five rows of
`D_verdict.a2_levels` (256+1536+8192+40960+220 = 51,164;
64+384+2048+10240+55 = 12,791).

The document paragraph carrying the stale figures was introduced in `824b9fb4`,
which is a **later** commit than `9cf779a3`. So this is not lag — the paragraph
was written after the artefact moved and describes the state before it.

`RUN_STATE.md` has the correct numbers ("`a2_transitions_enumerated: 51880` over
`a2_states_enumerated: 12970`"), so the run document and the criterion document
disagree about the same three numbers — the precise defect `CRITERION.md` names
for `~6e36` ("for one commit the run document and the decision record disagreed").

Commands:

```bash
cd exam/runs/20260730T021500Z-V23-large-space
grep -n "51,164\|12,791\|five small levels" CRITERION.md
python -c "import json;d=json.load(open('probe_lp_interface.json'))['D_verdict'];print(d['a2_transitions_enumerated'],d['a2_states_enumerated'],len(d['a2_level_ids']))"
# -> 51880 12970 9
git log -S'V.updraft(), V.cistern()' --oneline -- probe_lp_interface.py   # 9cf779a3
git log -S'51,164' --oneline -- CRITERION.md                              # 824b9fb4  (later)
```

Severity: HIGH. This is *wrong*, not unsourced: the artefact named as the source
emits different numbers, and one of them (the level count) is the sample size the
generalisation argument rests on.

---

## F6-2 (MEDIUM-HIGH) — the `a2_thin_coverage` declaration exists in the artefact and in `RUN_STATE.md`, and `CRITERION.md` still states the coverage claim it qualifies, unqualified

This is the fix RES-3 flagged as weakest, and the code half of it is sound (see
"not refuted", item 1). The failure is the recurring one: the correction landed
in two of the three places the claim lives.

`a2_thin_coverage` is the declared limitation — `{"button press": 1}` as a thin
kind, `{"button": 2, "door_closed": 2, "door_open": 2, "portal": 1}` as thin
branches, threshold 3. `RUN_STATE.md` names it. `CRITERION.md` enumerates
`D_verdict`'s fields one by one in the paragraph quoted in F6-1 —
`a2_coefficient_sum_by_kind`, `a2_transitions_by_kind`,
`a2_coefficient_sums_measured`, `a2_transitions_enumerated`,
`a2_states_enumerated`, `a2_step_branches_covered`, `a2_enumeration_bound`,
`a2_shipped_level_enumerated` — and **omits `a2_thin_coverage`**, while asserting
in the same breath:

> `a2_coefficient_sum_by_kind` and `a2_transitions_by_kind` (a plain move and a
> blocked transition sum to 0, a latching move and **a button press to +1**) …
> `a2_step_branches_covered` **listing all six branches**

Those are precisely the two statements the thin block exists to qualify: "a
button press sums to +1" is one observation, and "all six branches" is four
branches resting on 1, 2, 2 and 2 observations. `CRITERION.md` also calls
`a2_shipped_level_enumerated: false` "**the last field** being the honest part",
which is only true if `a2_thin_coverage` is not in the record — it is.

Command:

```bash
cd exam/runs/20260730T021500Z-V23-large-space
grep -niE "a2_thin_coverage|\bthin\b|thinly" CRITERION.md    # NO MATCH
grep -n "a2_thin_coverage" RUN_STATE.md probe_lp_interface.json | head
```

(Plain `grep -c thin` on this file returns 26 — every one of them inside
"something", "nothing", "within". The word-boundary form is the one that
answers the question.)

Severity: MEDIUM-HIGH. Not false — every sentence in `CRITERION.md` is literally
true — but the document is *less honest than the artefact it summarises*, which
inverts the direction this ticket's own rule runs in ("a document should not claim
more than the file it points at"). The declaration is the whole fix; it is absent
from the document that ships the claim.

---

## F6-3 (MEDIUM) — the shipped `D_verdict.how` string says the corridor sweep gives "4x the latch bits"; the same artefact's own rows say 2.5x

`probe_lp_interface.json`'s `D_verdict.how` — a published field, not a comment —
closes with the sentence that carries the whole generalisation:

> the step from these levels to every size is the monotonicity argument above,
> **supported by the corridor-length sweep (4x the latch bits, identical sums and
> kinds)**, not by a sweep of the shipped size.

`D_verdict.a2_levels` in the same file gives the sweep's `latch_bits`:

| level | latch_bits |
|---|---|
| `lp-iface-comb2` | 4 |
| `lp-iface-comb3` | 6 |
| `lp-iface-comb4` | 8 |
| `lp-iface-comb5` | **10** |

10 / 4 = **2.5×**, not 4×. Nothing else in the sweep is 4× either: states go
64 → 10,240 (160×) and transitions 256 → 40,960 (160×). The same string is in
`probe_lp_interface.py`'s `_measure_a2_coefficient_sums` docstring ("4x the latch
bits, identical sums and identical kinds"). Introduced in `b43427f0`; survived
`9cf779a3`.

Command:

```bash
cd exam/runs/20260730T021500Z-V23-large-space
python -c "import json;print([(r['level_id'],r['latch_bits']) for r in json.load(open('probe_lp_interface.json'))['D_verdict']['a2_levels']])"
grep -n '4x the latch' probe_lp_interface.py probe_lp_interface.json
```

Severity: MEDIUM. It is **wrong**, and it is the empirical half of the argument
that licences carrying a 9-level measurement to the shipped 20-corridor board —
overstated by 60%, in the one field a reader is told to read instead of the
docstring. The qualitative claim it is making ("more latch bits, identical sums
and kinds") is true; the multiplier is not.

---

## F6-4 (MEDIUM-HIGH) — the criterion-(b) widening changed exactly one line of `CRITERION.md`, and three other statements about the same coverage were left asserting the pre-fix state

`e4b25676` touched four files, and its `CRITERION.md` diff is `2 +-` — the single
provenance-map row. The rest of the document, and `RUN_STATE.md`, still describe
the four-of-seven artefact:

1. **`CRITERION.md`, the ruling section** ("The ruling: (c) ∧ (b), and the claim
   narrows to match") closes: *"(b) derived there and measured elsewhere — by
   `test_class_ii_levels_actually_truncate_the_enumerator` … and by
   `enumeration_probe.json` **for four of them**."* The probe now measures all
   seven. This is the section that states the ruling; the corrected row is a table
   at the top of the file.
2. **`CRITERION.md`, the round-five paragraph** (`grep -n "four of seven"`, second
   hit): *"Round five also found the criterion-(b) map row overstated (it covers
   four of seven records; **the row now says so**)."* The row no longer says so —
   `e4b25676` rewrote it to "all seven records it speaks for". The sentence is a
   claim about a row four lines above it in the same file, and it is false.
3. **`RUN_STATE.md`'s F5-14 bullet**: *"`CRITERION.md`'s map row now says so.
   **Left open on purpose:** the better fix is to widen `enumeration_probe.py` to
   all seven records rather than to annotate the map … **Not done here.**"* It was
   done, in `e4b25676`, which did not touch `RUN_STATE.md`.

Commands:

```bash
cd exam/runs/20260730T021500Z-V23-large-space
git show --stat --format= e4b25676        # CRITERION.md | 2 +-  ; RUN_STATE.md absent
grep -n "four of them\|four of seven" CRITERION.md
grep -n "Left open on purpose" RUN_STATE.md
```

Severity: MEDIUM-HIGH. Statements 2 and 3 are **wrong**, not merely stale:
statement 2 asserts something false about a row in its own file, and statement 3
records as deliberately open a finding the same run then closed. Statement 1
under-reports the run's own evidence. This is the fourth consecutive round in
which a correction landed in one location and not in the others that carry the
same claim — and the first in which two of the missed locations are in the *same
file* as the fix.

---

## F6-5 (MEDIUM) — round five's concession that "only the label `n_pos=5` was wrong" is itself wrong: `n_pos` **is** `lp_potential`'s name for the LP row width

`CRITERION.md`, work item 3, withdrawing round four's withdrawal:

> But `n_pos` is probe B and E's rung parameter, and the exhaustive loop is in
> probe D over the LP row width `n`, which is `n = 5` in the committed generator
> … Round four conflated two different `n`s and withdrew a true claim; **only the
> *label* "n_pos=5" was wrong.**

There is only one `n` here. In `engine-rig/engines/lp_potential/potential.py`,
`solve` reads `n = int(graph["n_pos"])` and builds each move row as
`row = [0.0] * (2 * n)` with `row[move.dst] += 1.0; row[move.src] -= 1.0;
row[move.over] -= 1.0` — so `n_pos` **is** the LP row width, and in
`engine-rig/interop/peg1d.py` it is likewise the board-position count that fixes
the bitstring length. `probe_d` in `probe_lp_interface.py` sets `n = 5` and runs
`src, over, dst` over `range(5)` against `row = [0.0] * 5`: that is the engine's
own move-row construction at `n_pos = 5`. Probe B/C/E vary the same quantity;
probe D fixes it at 5. They are not two different `n`s.

So the pre-round-four wording — "verified exhaustively over all role assignments
at `n_pos=5`" — was accurate in the engine's own vocabulary, and the concession
withdraws a second true thing while withdrawing round four's withdrawal of the
first.

Consequence, and it is the checkable part: three files still carry that wording
and are therefore **correct as written, not stale** —
`exam/DECISIONS.md` ("verified exhaustively over all role assignments at
n_pos=5"), `exam/STATUS.md` ("verified exhaustively at n_pos=5"), and this run's
own `invariant_path_probe.md` ("exhaustively over all 5³ = 125 role assignments
at `n_pos=5`", which is row "work item 3" of the provenance map). Under
`CRITERION.md`'s current text a reader would file all three as
document-corrected-but-not-the-file instances and "fix" three correct
statements. `D_role_assignments` was also renamed to `{"n": 5, ...}`, which drops
the one word that ties the loop to the engine field it models.

Commands:

```bash
grep -n 'graph\["n_pos"\]' -A 8 engine-rig/engines/lp_potential/potential.py
grep -n 'n = 5' -A 8 exam/runs/20260730T021500Z-V23-large-space/probe_lp_interface.py
grep -rn "n_pos=5" exam/DECISIONS.md exam/STATUS.md \
    exam/runs/20260730T021500Z-V23-large-space/invariant_path_probe.md
```

Severity: MEDIUM. Wrong, not unsourced. Round three, four, five and now this
clause have each corrected this one sentence and each introduced a new error —
which is the ticket's own thesis holding on the ticket.

---

## F6-6 (LOW) — the stated reason for putting `coverage` inside the stable hash does not hold; the decision does

`e4b25676`'s message: *"The `coverage` block was put **inside** the hash
deliberately: if it sat outside, F5-14 could recur — a row silently dropped, or a
record going unmeasured — without the hash noticing."*

`deterministic.items` has been inside the hash since the artefact's first version
(`deterministic` keys at `a29e3dc0` were `cap`, `items`, `large_space_threshold`,
`note`). Both named failure modes are per-row facts in `items`, so both move the
hash whether or not `coverage` is inside it. Measured, by recomputing the hash
over `deterministic` **minus** `coverage`:

| perturbation | hash over `deterministic` − `coverage` | changed? |
|---|---|---|
| none (baseline) | `fbe8c479ce09…` | — |
| row `iii8` dropped | `e77a9cce5bac…` | yes |
| `iii7` marked `measured: false` | `1d46f24a0ab8…` | yes |

The decision is still right — an aggregate ought to be pinned with the rows it
aggregates, and `coverage.criterion_b_records_expected` is a constant that lives
nowhere else in the hashed subset. But the argument offered for it is not the
argument that supports it.

Command:

```bash
cd exam/runs/20260730T021500Z-V23-large-space
python -c "
import json,hashlib,copy
d=json.load(open('enumeration_probe.json'))['deterministic']
f=lambda o:hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12]
s=lambda o:(lambda c:(c.pop('coverage'),c)[1])(copy.deepcopy(o))
print(f(s(d)))
x=copy.deepcopy(d); x['items']=[r for r in x['items'] if r['item']!='iii8']; print(f(s(x)))"
```

Severity: LOW. Unsourced reasoning, not a wrong artefact.

---

## Load-bearing claims attacked and NOT refuted

Each of these was attacked directly and survived. Where a claim was reproduced
rather than argued, the reproduction is named.

1. **`a2_thin_coverage`'s computed content matches the code exactly, and every
   factual claim in its `note` is true and checkable from the same artefact.**
   `_measure_a2_coefficient_sums` filters `count_by_kind` and `count_by_branch` on
   `< THIN` with `THIN = 3`; the artefact's `kinds` is `{"button press": 1}`
   (the other three kinds are 12,166 / 11,376 / 28,337) and `branches` is
   `{"button": 2, "door_closed": 2, "door_open": 2, "portal": 1}` (the other two
   are 39,710 / 12,163). The note's two substantive claims both hold:
   *"all of them inside `atrium`"* — `D_verdict.a2_levels`'s `atrium` row carries
   exactly `button 2, door_closed 2, door_open 2, portal 1` and the sole
   `button press`, and every other row carries none of them; and *"the only
   shipped level with a button, a door or a portal"* — in `exam/papers/verdict.py`
   only `a2_echo` passes `button=`, `door=`, `portal=` to `_level`, whose defaults
   are all `None`, and no other constructor or operator sets them
   (`grep -n '"button"\|"door"\|"portal"' exam/papers/verdict.py` → the four
   default lines only). The declaration says something true and checkable.

2. **The `a2_thin_coverage` limitation cannot damage the conclusion it qualifies,
   and RES-3's "the general claim rests on monotonicity" hedge is an argument,
   not a hand-wave.** Two independent reasons, both checkable in source:
   * `_enumerate_a2_level` computes `bits = popcount(nmask ^ mask) + pressed_now`
     *after* raising on `mask & ~nmask` or `pressed and not npressed`. Given those
     assertions, `bits >= 0` identically — so **no enumerated A2 transition can
     have coefficient sum −1 regardless of sample size**. The measurement's
     conclusion ("−1 is none of these") does not depend on `button press` having
     been seen more than once; a thin sample could only have hidden a *different
     non-negative* value, which would not touch the comparison against
     `lp_potential`'s −1.
   * The monotonicity the hedge invokes is a property of the code at every board
     size, not an induction from these levels. `rubrics_verdict.Level.step`'s
     five return paths return `pressed` unchanged or `True`, never `False`; and
     `_latched_at` is `latched | (1 << idx)`. The mutual-exclusion bullet is
     likewise structural: the button branch is `return cart, True`, so the cart
     does not move and cannot newly latch. The bullets in the docstring are
     derivable from `step`, and the loop's assertions are their empirical check —
     which is what "argument checked by assertion" claims.

   The one place the record is looser than its own wording: `D_verdict.how` says
   "each transition's occupancy-vector delta **was summed**", and the cart's
   contribution is never computed — it is argued to be 0 in the next sentence of
   the same field. Disclosed in place, so not a finding.

3. **The enumeration probe really does call `V.build()` and filter on the test's
   own predicate.** `records()` in `enumeration_probe.py` is
   `paper = V.build()` then
   `[it for it in paper.items if it.truth["state_space"]["naive_enumeration_feasible"] is False]`.
   `test_class_ii_levels_actually_truncate_the_enumerator` in
   `exam/tests/test_verdict.py` uses the identical comprehension. No hardcoded
   level list survives; `EXPECTED_CRITERION_B_RECORDS = 7` is compared against
   `len(covered)` in the status ladder, never used to build it. Levels come from
   `item.truth["level_blob"]`, i.e. the shipped blob.

4. **The three conjuncts are what the code checks, and `no_solution_inside_cap`
   is genuinely independent — RES-3's "load-bearing" claim is right, and I can now
   show it rather than argue it.** `rubrics_verdict.enumerate_states` records
   `solved = paths[nxt]` and **keeps going**; it has no early return. So
   `truncated: True` and `solution is not None` can co-occur. Demonstrated:

   ```bash
   python -c "
   import sys; sys.path.insert(0,'.')
   from exam.grading import rubrics_verdict as RV
   from exam.papers import verdict as V
   d=V.comb_open('indep-check',12,1,12); d['require_all_switches']=False
   r=RV.enumerate_states(RV.Level(d), cap=RV.MAX_ENUMERATION)
   print(r['truncated'], r['states'], len(r['solution']))"
   # -> True 200000 11
   ```

   A solvable board that truncates at the cap *and* yields a plan inside it exists,
   so the third conjunct is not implied by the first two, and for iii6/iii7/iii8
   it is the one doing work. The margin is not a knife edge either: those three
   have `witness_length: 416` in
   `exam/artifacts/truth/p15-verdict-a2.truth.json`, and BFS exhausts 200,000
   states long before depth 416.

5. **i1-i5 and ii1-ii4 come back with identical numbers.** Diffing the pre-`e4b25676`
   artefact against the shipped one field by field: for all nine old rows, **every
   key present in the old row has the same value in the new row**. The only
   differences are eight added keys per row (`criterion_b_applies`,
   `criterion_b_conjuncts`, `criterion_b_holds`, `item_id`, `measured`,
   `measurement_bound`, `shipped_record`, `unmeasured_reason`). Strictly, the rows
   are not "byte-identical" — they grew — but every measured number is. That does
   retroactively confirm the old hardcoded reconstructions matched the shipped
   blobs.

6. **The coverage block is inside the stable hash, and the stable-subset
   definition is what the file says it is.** `main()` computes
   `blob = json.dumps(deterministic, sort_keys=True, separators=(",", ":"))` and
   `deterministic` has keys `cap`, `coverage`, `items`, `large_space_threshold`,
   `note`, `status` — so `coverage` is hashed. Recomputing the hash from the
   committed JSON reproduces `4abe483e6b78…` exactly, and perturbing any
   `coverage` field changes it. And the docstring's claim that everything under
   `deterministic` is a pure function of the repo holds: **re-running the probe in
   this worktree printed `deterministic sha256 4abe483e6b78…`, byte-identical**,
   with only `timings_nondeterministic` moving. `build()`'s side effect on
   `exam/artifacts/variant_specs/` left the tree clean, exactly as the docstring
   promises (`git status --short` after the run showed only
   `enumeration_probe.json`). Artefact restored with `git checkout --`.

7. **F5-13 is correctly left standing; RES-3 did not under-close it.** All seven
   records in `exam/artifacts/truth/p15-verdict-a2.truth.json` with
   `state_space.naive_enumeration_feasible is False` — ii1-ii4 and iii6/iii7/iii8,
   m = 120/120/60/118/120/120/120 — still carry `enumeration_attempted: false`,
   `truncated: null` and `enumerated: null`, and `state_space`'s key set
   (`arithmetic, cap, enumerated, enumeration_attempted, lower_bound,
   naive_enumeration_feasible, positional_states, truncated`) contains no
   criterion-(b) measurement at all. "Both conditions are recorded as
   measurements" remains false *of the record*. Refusing to let the (b) closure
   close F5-13 was the right call.

8. **The re-stamped `MANIFEST.json` verifies independently.** Recomputed sha256
   over every listed path from a clean tree: **25 entries, 0 mismatches, 0 missing
   files.** The only file present in the run directory and not listed is
   `BASELINE-cycle94.md`, which is tracked (`git ls-files` resolves it) and which
   the manifest's `note` deliberately excludes as another session's cycle log —
   so the omission is declared, not silent. `prompt_id`, `branch`, `base_commit`
   (`415556f8`) and `utc` are all present. The self-verified stamp is correct.

9. **The suite count is confirmed.** `cd exam && python -m pytest -q` →
   **`470 passed, 2 xfailed in 142.91s`**. RES-3's report is exact.

10. **The map row's own supporting claims hold.** `coverage.superseded_coverage`
    reads "four of seven (ii1-ii4 only); the three solvable_hard records
    iii6/iii7/iii8 were absent -- round five F5-14", and
    `git show a29e3dc0:…/CRITERION.md` line 16 is the row it supersedes, saying
    exactly that. `criterion_b_records_by_class` is
    `{large_unsolvable: 4, solvable_hard: 3}`; `criterion_b_records_holding: 7`;
    `criterion_b_failures: []`; `unmeasured: []`; `status` is the OK string. All
    seven `criterion_b_conjuncts` are `{truncated, states_reached_cap,
    no_solution_inside_cap}` all true, with `states_visited: 200000` on each.

## Sealed-pile constraint

Nothing here touched `arc-recon/`, `environment_files/`, or any game. No claim was
left unverifiable for pile reasons.

## Tree state

Clean apart from this file. `enumeration_probe.json` was regenerated to test
reproduction and restored with `git checkout --`; nothing else was written.
This file is **not** in `MANIFEST.json` — round 5's report was added to the
manifest when it was accepted, and re-stamping is the owner's call, not the
reviewer's.

## One-line verdict on round five's fixes

The *engineering* held everywhere I could reach it — the criterion-(b) widening,
its three-conjunct predicate, the stable hash, the 25-entry manifest re-stamp and
the decision to leave F5-13 open are all correct, and the `a2_thin_coverage`
declaration is both true and stronger than RES-3 credits it with being — but the
*documentation* repeated the run's signature defect for a fourth round: three
numbers and a level count in `CRITERION.md` describe an artefact two commits
stale (F6-1), the thin-coverage declaration never reached the document that ships
the claim (F6-2), the one-line map-row fix left two contradicting statements in
its own file and one in `RUN_STATE.md` (F6-4), and one clause of round five's own
correction is wrong in the way round four's was (F6-5).

