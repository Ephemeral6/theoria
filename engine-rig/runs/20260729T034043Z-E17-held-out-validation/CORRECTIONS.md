# E17 · corrections — what the adversarial review overturned

`ADVERSARIAL-heldout.md` (19 findings, 615 lines) attacked the first version of
this run. It overturned six claims outright. Nothing below is a defence; each
entry says what was claimed, what is true, and what was changed. **RESULTS.md is
left as first written** — its value is that it is the pre-correction text — and
this file supersedes it wherever they disagree. `ENGINE_TABLE.md` carries the
corrected wording, not the original.

The review's own summary of the damage is fair and is quoted rather than
paraphrased: *"The arithmetic is clean and the honesty machinery mostly works …
What does not survive is the interpretation."*

---

## C1 · The `zero_space` 100.0 % measured nothing (review F1, F13) — SUSTAINED

**Claimed:** "Under a random 70/30 transition split the recovered laws
extrapolate perfectly — 100.0 % of global laws hold on the withheld
transitions."

**True:** a `parityworld` difference vector is a function of the *operation*
alone, so 60 transitions carry at most 9 distinct rows. Every held-out row is
bit-identical to a training row, in 120 / 120 worlds. The re-check passes by
substitution. The review's proof is better than its argument: it made
`random_transition_split` return **overlapping** train and test sets and **no
published digit moved**.

That is the ticket's own defect one indirection further out — E17 exists because
"已测" meant "self-consistent on the data it was fitted to", and Z-S1 re-checked
the laws on a *copy* of that data.

**Changed:** the harness now measures and publishes
`heldout_row_novelty` — how many withheld difference vectors the fit had not
already consumed. Z-S1: **0 of 2160 new**. Z-S2: **7200 of 7200 new**. The table
now states that 13.1 % is the held-out number and 100.0 % is a control that came
out vacuous, and says so before quoting it. `tests/test_heldout.py` pins the
novelty measurement so it cannot be quietly dropped.

## C2 · The `lp_potential` emit-gate "pass" was scored against the wrong graph (F5, F15) — SUSTAINED

**Claimed:** "The pass is that the emit boundary already holds: 0 of 1408
certificates reach `candidates.jsonl`. So the hole is in `check_exactly`, not at
the emit gate."

**True:** the harness fitted on the reduced graph and then gated on the
**complete** one — asking whether the guard fires when handed the very evidence
the hold-out premise says the caller does not have. `lp_potential/__init__.py`
says in as many words that production cannot reach that branch. Handed the graph
a partial-evidence caller actually holds, **all 1408 are emitted, including all
58 false ones**, each carrying `holds: true` and `sound_over_graph: true` into
the shared candidate stream.

**Changed:** the harness now runs the gate both ways and publishes
`emit_gate_let_through_reduced_graph` (**1408**) and
`false_certificates_emitted_reduced_graph` (**58**) beside the original 0. The
table's "the pass is…" sentence is struck and replaced by "the emit gate does
not save it", with both numbers. `tests/test_heldout.py::test_the_emit_gate_is_
measured_on_the_graph_the_caller_would_hold` pins it.

## C3 · "Alone among the eight rows, this engine's 已验证 was not circular" (F7, F16) — SUSTAINED, and backwards

**Claimed:** L-L2's 0 admissibility violations in 506 held-out states showed
`lp_potential`'s re-check had never been circular.

**True:** `inv_closed` over the complete move set *entails* admissibility on
every finite-distance state — potential never rises, so a state with a path to
the goal has `pot(s) ≥ pot(g)`, and no path can be shorter than `h`. No
configuration exists in which the count could be non-zero. Confirmed on all 1408
held-out certificates: every one of the 1778 violations lives where `inv_closed`
fails, none where it holds. The states are outside the LP's *constraint set* and
inside its *argument*, which quantifies over move instances.

**Changed:** the sentence is struck. The figure is retained and relabelled as a
consistency check on the harness, with the entailment stated.

## C4 · A pre-registered validity criterion was ticked and not met (F8) — SUSTAINED

**Claimed:** validity table row "every miss carries a concrete witness — yes",
and "1940 laws miss in total. **Every one** is emitted with …".

**True:** `run.py` wrote `misses[:200]` of 1940 (10.3 %) and capped every
witness list at 20. §5.3 of the pre-registration requires all of them.

**Changed:** all caps removed except one (`emit_gate_let_through_reduced_graph`,
capped at 50 and labelled, because it is 1408 near-identical rows). Every
`zero_space` miss and every `lp_potential` false certificate, `inv_closed` miss
and admissibility violation now carries its witness. This was the failure mode
the pre-registration was written to prevent, and it happened anyway.

## C5 · The 92.9 % `cell_local` "surprise" is a corpus-geometry artefact (F10) — SUSTAINED

**Claimed:** "the run's one real surprise … thinner evidence manufactures
encoding-local laws that are not there."

**True:** the *mechanism* is real; the *magnitude* is a fact about the corpus.
`parityworld` windows are contiguous on a line, so cells 0 and n−1 are touched by
exactly one operation each; withhold it and that cell looks constant. All misses
sit on cells 0 and n−1, nowhere else. Rebuilt cyclic, `92.9 → 100.0` and the
global rate `13.1 → 66.7`.

**Changed:** the table now states the boundary-artefact explanation and both
cyclic figures, probed out of the review's own report.

## C6 · The standing rule bound nothing (F17) — SUSTAINED

**Claimed:** a rule that a cell "may not say 「已验证」" without held-out
validation.

**True:** no cell used either phrase, no test enforced it, and it forbade a word
nothing said — unfalsifiable in both directions. Contrast `边界未测`, which has a
test.

**Changed:** the two phrases are module constants, and
`tests/test_engine_table.py::test_the_standing_rule_on_verified_is_published_and_
names_the_held_out_rows` now asserts the rule is published *and* that exactly the
two rows E17 measured are the two allowed to quote a held-out figure. The rule's
corpus scope is stated in the file: both measurements are on synthetic families
the harness generates, and no live-game data has been held out for any engine.

## C7 · `value_hit` is not a second metric (F2) — SUSTAINED, minor

It is logically equivalent to `delta_hit` for any split of a path. RESULTS.md
reported "they came out identical everywhere" as an observation; it is forced.
The review's mutant P6 rewired all three published probes from `delta_hit` to
`value_hit` and no digit moved.

**Changed:** `tests/test_heldout.py::test_the_published_rate_probe_reads_delta_
hit_not_value_hit` feeds the probe a case where the two differ, so the rewiring
is now detectable even though real data cannot separate them.

## C8 · The counting / arithmetic "agreement" is an identity (F6) — SUSTAINED, minor

`check_exactly` has already proved every listed move non-increasing, so the only
geometry that can raise the potential is the withheld one. `gate_raising_moves ≠
[]` iff `heldout_inv_closed` is false, by construction. **Changed:** the table
now says "an identity rather than two detectors".

## C9 · The `k` disaggregation was post-hoc and only the code said so (F19) — SUSTAINED, minor

**Changed:** the disclosure is now in the table cell where the number is read.

---

## What survived the review

Stated because a correction file that lists only damage is its own kind of
dishonesty. The reviewer re-derived all four `zero_space` rates and all thirteen
`lp_potential` counts from code it wrote itself, including an independent peg
state space and BFS: **every one reproduces to the digit**. Two re-runs are
byte-identical to the committed `results.json`. All 14 / 14 `MANIFEST.json`
hashes verify. `ef382c9` is genuinely an ancestor of the results commit and
`PREREGISTRATION.md` is byte-unchanged since. `504 passed, 27 skipped, exit 0`
was the real pytest result. The smallest `peg4` witness is exactly right — the
reviewer checked all three conditions by hand in rationals. **26.4 % is stable
across `n`** (31.2 / 31.7 / 23.8 / 25.9 % at n = 4…7) and moves monotonically to
8.5 % when two geometries are withheld; the reviewer tried to break it and could
not. Corpus-scope limits were already stated plainly (F14). The E9 numeral
tripwire caught both probe mutants (F18). And the run's refusal to set a pass
threshold was called out as correct.

## The mutation finding, and what was done about it

19 mutants, **14 survived**, in a clean pattern: everything inside `engines/` or
`tools/` was caught, everything inside `heldout/` survived. `heldout/` had **no
tests** — nothing under `tests/` imported it. Three surviving mutants fitted
directly on the held-out data and pushed the published rate to 100 %, and the
pre-registered gate `fit_matches_engine` is structurally incapable of catching
them: the only case it examines is the one where nothing is withheld.

`tests/test_heldout.py` (16 tests) was written against that mutation table
rather than against the code listing. Re-checked in
`measured/mutation-recheck.txt`: M1 (leaking split), M2 (fit on everything), M9
(a hold-out that deletes nothing), M10 (a validity gate that always passes), M11
(admissibility scoring that skips violations) and P6 (probes rewired to the
other metric) now all fail the suite. `fit_matches_engine` is still incapable of
detecting leakage on its own — that is why the leakage detection lives in
`test_withholding_an_operation_strictly_enlarges_the_recovered_space` and in the
published novelty counts instead.
