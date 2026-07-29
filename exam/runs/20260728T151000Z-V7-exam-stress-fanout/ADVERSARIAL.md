# V7 — the adversarial pass

`FINDINGS.md` carries the results; `RUN_STATE.md` is the narrative. **This file is
the record of the pass that tried to destroy both**, and of what survived it.
It is referenced by name from `RUN_STATE.md` and from the `reason=` string of both
strict xfails in the suite, so it has to stay in step with them.

**Provenance.** V7 was claimed by RES-2 at `2026-07-28T15:02:17Z`; that session
died and the monitor released the item at 18:08:25Z. RES-3 re-claimed it at
`2026-07-29T04:48:57Z`, ran the adversarial pass, and re-verified this file on
`2026-07-29T06:15Z` from a clean worktree before delivery. The re-verification is
not a re-reading: every script under `adversarial/` was executed again, and the
section "What the re-verification changed" is what that second run cost. **It
does not cover every figure here** — the `free`/`memorised`/`theory` partition of
claim 3 has only ever been computed by the tool that reports it, which is stated
in that claim and listed again under "What this pass did not attack".

**Method.** Each headline claim was handed to an independent context whose brief
was to *refute it*, not to check it — with the instruction to prefer "overstated"
over "confirmed" when the evidence was thin. Every correction the pass produced
was then re-derived by the corrector from the primary artefacts, not relayed from
the attacker's report. Where the attacker and the corrector disagreed, the
disagreement is written down rather than resolved silently.

**Passive throughout.** Zero API calls, zero model calls on any generation or
grading path, zero network, zero sealed-pile contact. Everything here runs
against the twenty synthetic worldgen worlds and the four hand-built papers.

## The scoreboard

| # | Claim as first written | Verdict |
|---|---|---|
| 1 | The exam's own leak checker refuses all twenty generated papers | **survived**, count corrected 160 → 236 |
| 1b | (implied) a test exists that should have caught it | **refuted** — the test is vacuous |
| 2 | A **theory-free** prior scores 1.000 on twelve of twenty worlds | **numbers survived, adjective refuted** |
| 3 | 41 % of the paper has zero discrimination; residue 69 items / 12 worlds | **41 % not independently attacked**; residue corrected to 16 items / 14 worlds |
| 4 | The marker never misjudges — misjudgement is all in the verdict label | **survived on its rubric, false off it** (§4b) |
| 5 | A full-suite run failed 11 tests and the cause is not established | **cause established; the first hypothesis refuted** |

Claims attacked: 4. **Claims 1–4 are numbered to match `FINDINGS.md`'s sections
1–4; 1b and 5 are not.** 1b is an attack the pass generated on itself while
working claim 1 and lives inside FINDINGS §1; claim 5 has no FINDINGS section at
all — it is written up in `RUN_STATE.md`, and FINDINGS §5 is an unrelated section
about the three verdict classes. Claim 5 was not a result of the run either: it
was an unexplained failure the run had written down as unexplained, and the pass
was told to explain it or say it could not.

`MANIFEST.json`'s terser `adversarial_pass` block maps onto this table as:
`claims_attacked: 4` = claims 1/2/3/4; `survived: 2` = 1 and 3;
`refuted_or_overstated: 2` = 2 and 4; 1b and 5 sit outside the tally.

---

## Claim 1 — the leak gate refuses 20/20 papers

**Attacked with** `adversarial/c1_leak.py` (re-derives the gate over every world,
counting *which* probe fired on *which* item, and re-runs the count with the
`rule:` tag removed).

**Survived.** 20 of 20 worlds refused, **236 of 236 items** hit by their own
declared leak probe, `items_with_structural_hit: 0` — the refusal is carried by
the declared `leak_probes` string match and not by the structural check.
(`check_paper` has a third finding source, the metadata check; `c1_leak.py`
declares `metadata_findings` and never increments it, so "not structural" is
measured and "probe only" is not.)

**Corrected: 160 → 236.** The retracted 160 was `20 × 8`, an artefact of reading
the `LeakageError` message, which truncates its findings list at eight. The
count above is taken from the probe test directly and never formats the message.
A number derived from an error string is a number derived from a display limit.

**Corrected: "a one-line fix" → three places at least.** Setting `tags=(split,)`
leaves **16 items across exactly 4 worlds** still refused —
`t1-walk-maze`, `t1-push-open`, `t2-switch-push`, `t3-full-house`, four items
each. The residue is not the tag: it is `Paper.world`, whose `world_id`
`t1-walk-maze` contains the probe string `walk` and whose `families` contains
`push`. `world_id` cannot be dropped without breaking provenance, so the fix has
to decide something rather than delete something.

Per-probe totals — the same field counted a second way rather than an independent
corroboration, since `heldout_worldgen.py:203` sets `leak_probes=(rule,)` and all
236 items hit, which makes the agreement with §2's per-rule counts a tautology:
`blocked_by_wall` 80, `walk` 80, `push` 12, `walk_through_door`
12, `collect_token` 12, `toggle_switch` / `blocked_by_block` /
`walk_through_cycler` / `teleport_twoway` 8 each, `blocked_by_door` 4,
`latch_already_set` 4.

## Claim 1b — the test that should have caught it is vacuous

**Attacked with** `adversarial/c1b_vacuity.py`, written after the pass asked the
obvious follow-up: a repository this careful surely has a test for exactly this.
It does: `exam/tests/test_worldgen_papers.py:71`,
`test_the_sheet_names_no_rule_the_open_files_do_not_already_name`. It has never
made a non-vacuous assertion.

Two independent reasons, both measured:

* **The matcher never lines up.** The needle is `'"%s"' % rule` — JSON-quoted,
  `"walk"` — while the sheet carries `"rule:walk"`. The closing quote is on the
  wrong side of the colon, so the assertion passes with the rule name plainly
  present in the text it is searching. All 12 executed assertions are this case.
* **The carve-out absorbs the rest.** The other 3 of 15 pairs are `push`, skipped
  by the `continue` because `spec.json` names the family.

Totals: **15 (world, rule) pairs executed, 12 vacuous, 3 carved out, 0 genuine
passes, 0 that would fail.** The test is also parametrised over
`SAMPLE = ("t1-push-open", "t2-switch-push", "t3-full-house")` — it never looks
at 17 of the 20 worlds. Extended to all twenty it would be **59 pairs, 56
vacuous, 3 carved out, 0 genuine**.

This is why the leak went unseen for as long as it did: not "no test", but a test
whose name is exactly right and whose body asserts nothing. A vacuous test is
worse than a missing one, because the missing one does not appear in a coverage
argument.

**Corrected here, too: a test written for the leak can itself be vacuous.** The
pass's first proposed regression test reproduced the same quoting mistake in a
new file. It was thrown away rather than committed.

## Claim 2 — the prior is not theory-free

**Attacked with** `adversarial/c2_ablate.py` (sheet-field and orientation
ablations through the real marker) and re-derived with `adversarial/v_recheck.py`
(per-rule table, identity of every miss).

**The numbers survived, byte for byte.** 12 of 20 worlds at 1.000, 18 of 20
beating their bluffer floor, 109 of 139 frame-changing items (78.4 %), overall
0.8008. None of them moved.

**The adjective did not.** Two ablations put a number on the world knowledge the
eight lines carry:

| variant | overall | perfect worlds |
|---|---|---|
| baseline | 0.8008 | 12 |
| `legend` without `agent` | **0.4110** | 0 |
| `legend` without `wall` | 0.4619 | 0 |
| `legend` without `floor` | 0.8008 | 12 |
| no `legend` at all | 0.4110 | 0 |
| `DELTA` reversed | **0.2034** | 0 |
| `DELTA` transposed | **0.1017** | 0 |

0.4110 is the bluffer floor to four figures: without `legend["agent"]` the prior
cannot locate the agent, returns the input frame unchanged, and *is* the
constant "nothing happens" examinee. The orientation ablations are the sharper
result — both land far *below* the floor, so a relabelling of which way is up
costs four fifths of the score. **A convention whose relabelling is that
expensive is not an absence of theory; it is a theory that happened to be
right.** The defensible claim is *legend plus orientation plus eight lines*, and
the first two came in from outside.

To reproduce the ablations without the script: deep-copy each item's sheet side
and delete one key from its `legend` dict (`agent`, `wall`, `floor`), or pop
`legend` entirely; nothing else changes and `Item.truth` is never read.
`DELTA` is `{"UP":(-1,0),"DOWN":(1,0),"LEFT":(0,-1),"RIGHT":(0,1)}`; "reversed"
negates every vector, "transposed" swaps the row and column components.

## Claim 3 — the zero-discrimination share, and the residue

**Attacked with** claim 2's artefacts, not with a script of its own — and that is
this claim's weakness, stated up front. Nothing under `adversarial/` recomputes
the `free`/`memorised`/`theory` partition; the 97 / 70 / 69 figures come from
`exam/tools/discrimination.py`, the run's own new tool, which is also the tool
this section reports two defects in. **So "97 of 236 free (41.1 %) held" means
"was not attacked", not "survived an attack."** What can be said independently is
that the 97 free items are exactly the items a constant bluffer already takes,
and 97/236 = 0.41102 is the bluffer floor `prior_sweep.json` reports — an
arithmetic consistency check, not a re-derivation. A second implementation of the
partition is still owed.

**The residue did get worse under attack**, and this is a real result rather than
a check: measured against §2's prior instead of against the three voters, the
informative residue falls from **69 items to 16** — and to **zero on fourteen
worlds, not twelve**. *This file's first draft said the fall was "30 → 16", which
repeats the exact category error FINDINGS §3 retired: 30 is `139 − 109`, the
frame-changing items the prior missed, a different quantity that spans
`memorised` items too. The two numbers are not commensurable and 69 is the one
the `theory` class denotes.*

**Corrected: the barren set is quota-dependent.** "The rule the world is named
for is the one rule its paper does not examine" is true at `per_class=2` and is a
statement about the sampler's matched quota, not about the catalogue. Stated
without the quota it reads as a property of the exam, which it is not. (FINDINGS
§3 carried the qualifier in its 100 %-stasis paragraph but not on the bolded
sentence itself until the re-verification of 2026-07-29 put it there.)

**Corrected: §2 and §3 were one finding counted twice.** Nine of the twelve
perfect worlds contain no rule but `walk` and `blocked_by_wall`, so "a cheap
prior takes twelve worlds" and "the named rule is unexamined" are the same fact
seen from two directions. Named in FINDINGS §2 as the third correction; the
cross-reference from §3 back to it was added on 2026-07-29, because a
double-count named in only one of the two places it applies is still a
double-count for a reader who reads the other.

**Two tool defects fixed rather than reported.** `discrimination.py::main` exited
0 on a dead item — the one condition the tool exists to catch was the one it
could not fail on. And a test named for a bluffer comparison never made one.

## Claim 4 — marker misjudgement, and §4b where it fails

**Attacked with** `adversarial/c4_marker.py`: 236 worldgen items, ground truth in
eight wrappers, 21 spellings of silence, and per-item mutations of the truth
(one-cell, transposed, reversed, ragged).

**Survived on the held-out rubric, at 11 712 probes**: 0 cases where the marker
paid for an answer it should not have, 0 where silence was paid, 0 where ground
truth was marked wrong. On the held-out paper, misjudgement really is confined to
the verdict label and never reaches the mark.

**Corrected: the claim said "everywhere", and off that rubric it is false.**
The same attack against the four hand-built papers pays for silence six times,
five of them on the adaptation paper:

```
adaptation   []           -> 6.500 of 144      all of it on adapt.collateral.v1
adaptation   'unsolvable' -> 12.000 of 144     all of it on adapt.collateral.v1
adaptation   0            -> 1.000 of 144      adapt.detect.v1
adaptation   False        -> 1.000 of 144
adaptation   'None'       -> 1.000 of 144
verdict      'unsolvable' -> 9.000 of 34
```

`"unsolvable"` and `0` are legible answers that happen to be right somewhere,
which is defensible. **`[]` is not.** `rubrics_adaptation.py::_read_set` uses the
*whole answer* as the value of every set-valued key when the answer is not a
dict, so one `[]` asserts the empty set for `rules_falsified`,
`claims_to_reexamine` and `claims_now_false` at once and collects the weight of
each wherever the truth happens to be empty. The module's own `_read_claim`
calls `[]` illegible, and `test_selftest.py:286` asserts exactly that — so the
marker pays, on one rubric, for a token it declares unreadable on another.

The tell was in the test file all along: the "submission of nothing" test is
parametrised `[GARBAGE, "", {}, None]`, and `[]` is conspicuously absent from a
list it obviously belongs to.

**Pinned, not fixed.**
`test_selftest.py::test_the_bare_empty_list_is_not_paid_on_the_adaptation_paper`,
`xfail(strict=True)`. Fixing `_read_set` moves V4's already-published calibration
numbers, so it belongs in an item that re-derives them; `strict=True` means the
day someone fixes it, the suite goes red and they are forced to.

## Claim 5 — the unexplained failing run

Not a result: a **failure the run had honestly recorded as unexplained** —
11 failed / 297 passed on one full-suite run, never reproducing serially. The
pass was told to explain it or to say it could not.

**Explained, and it is a real concurrency defect in `exam/`.**
`verdict.py::_emit_spec` writes 17 variant specs into
`exam/artifacts/variant_specs/` — a **shared, tracked, non-temporary** directory —
through `model.write_json`, whose `open(path, "w")` truncates on open, and then
reads each one straight back with `Variant.load(path)` at `verdict.py:479`. Two
`verdict.build()` calls in different processes share that directory, so one
builder's read can land inside another's truncation window and gets zero bytes.

Evidence, re-run rather than relayed:

```
6 workers x 12 verdict.build()          -> 2 JSONDecodeError, both at verdict.py:479
pytest test_selftest.py + 4 hammers     -> 1 failed, 33 passed   (x2 runs)
```

Both pytest transcripts converge on the identical choke point through *different*
call sites — `verdict.py:761` in one, `verdict.py:985` in the other, both into
`:479` → `proxy/variants.py:108` → `json.decoder` with `s = ''`. The victim test
is whichever happens to be running: the attacker's run
(`pytest_under_race.txt`) killed
`test_no_sheet_names_the_genre_of_the_world_it_asks_about`, and the corrector's
independent re-run of the same experiment (`pytest_under_race_2.txt`) killed
`test_a_submission_of_nothing_scores_nothing_on_every_paper[None]` — the exact
test at the exact parameter the run had recorded as unexplained. Two runs of one
experiment, two different victims: **the defect is not attached to any one
test**, which is why it looked like noise.

**The first hypothesis is refuted.** The run had floated that the bad suite was
issued right after `discrimination` in write mode and might have been clobbered
by it. Nothing in `exam/` reads
`exam/artifacts/matrix/discrimination_worldgen.json` — it is a write-only output,
so that path cannot reach the self-test. The shared file that matters is the
variant spec.

**Severity.** The 17 spec files are tracked, so the truncation window is also a
window in which a committed artefact is momentarily zero bytes. Every number this
run and V4 published stands — the defect makes builds crash, not mismark — but
the suite is not safe to run concurrently with anything that builds the verdict
paper.

**Pinned, not fixed.**
`test_verdict.py::test_a_concurrent_builder_cannot_hand_emit_spec_an_empty_spec`,
`xfail(strict=True)`, reproduces the interleaving *without* a race by truncating
the shared path at the moment `Variant.load` opens it. A real concurrency test
would be flaky, and a flaky strict xfail is worse than none. Everything happens
under `tmp_path`; the tracked specs are never touched, because leaving a
committed artefact zero bytes long is the damage the test exists to describe.

---

## What the re-verification of 2026-07-29 changed

Three things the pass itself got wrong. Only the first and third needed the
re-run; the second was sitting in output the pass had already produced and
misread, which is its own lesson about what "verified" bought.

* **`c2_ablate.py` reports `beats_floor: 19`; the published figure is 18, and 18
  is right.** The marker returns `report.fraction` already rounded to 6 dp.
  `prior_sweep.py:100` compares `round(prior,6) > round(floor,6) + 1e-9` and
  correctly calls `t2-unsolvable-nodoor` (8.0/12.0) a tie; `c2_ablate.py:46`
  compares the rounded fraction against an *unrounded* floor —
  `0.666667 > 0.6666666666...` — and counts it a win. The defect is in the
  attacking script, not in the published number, and it inflates by one on every
  row where the prior ties a floor whose 6-dp rounding goes up. Left in place and
  written down here rather than patched: an adversarial script edited after it
  has been quoted is no longer the script that produced the quote.
* **`legend["floor"]` is not load-bearing.** Removing it gives 0.8008 / 12
  perfect worlds — bit-identical to baseline. §2's "the legend is one
  load-bearing half" is carried entirely by `agent` and `wall`; the third glyph
  the prior reads costs nothing to remove. **This one is not a yield of the
  re-run.** `c2_ablate.py:64` loops `("agent", "wall", "floor")` and has printed
  that row on every execution since it was written, the first included; the pass
  quoted the two rows that supported its correction and did not read the third.
  A re-run cannot catch that class of error, and did not — a reviewer reading the
  existing output did.
* **`flipcheck.py` does not demonstrate what its own docstring claims.** It says
  it proves *both* strict xfails flip. Run as a script it prints nothing at all —
  it is an eight-line plugin fragment with no `__main__` — and its only action is
  rebinding `rubrics_adaptation._read_set`, which can reach the `[]` xfail and
  cannot touch the `_emit_spec` one. Nothing in the run directory recorded how to
  invoke it. The recipe, established here, with both transcripts saved beside it
  (`adversarial/flipcheck_control.txt`, `adversarial/flipcheck_xpass.txt`) so this
  claim rests on an artefact like every other one in this file:

  ```
  # control -> flipcheck_control.txt:  1 xfailed in 5.09s
  PYTHONPATH=. python -m pytest \
    exam/tests/test_selftest.py::test_the_bare_empty_list_is_not_paid_on_the_adaptation_paper -rxX -q
  # with the defect patched -> flipcheck_xpass.txt:  1 failed in 5.32s  [XPASS(strict)]
  PYTHONPATH=".;<run>/adversarial" python -m pytest -p flipcheck \
    exam/tests/test_selftest.py::test_the_bare_empty_list_is_not_paid_on_the_adaptation_paper -rxX -q
  ```

  The second xfail's flippability rests on `flipcheck_race.py` instead, which is
  weaker evidence and should be read as such: it shows the injected interleaving
  still kills the *current* `_emit_spec` while two candidate fixes survive it —

  ```
  current _emit_spec           -> JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  fix A: validate in memory    -> OK  a2var-i1-atrium-nodown
  fix B: private read-back     -> OK  a2var-i1-atrium-nodown
  ```

  — i.e. the injection is fix-sensitive and the xfail *can* flip, not a
  demonstration that it *does*.

## Reproducing this file

From the worktree root, `PYTHONPATH=.`, all offline:

```
python .../adversarial/c1_leak.py          claim 1     (worldgen only, safe to parallelise)
python .../adversarial/c1b_vacuity.py      claim 1b    (worldgen only)
python .../adversarial/c2_ablate.py        claim 2     (worldgen only)
python .../prior_sweep.py                  claim 2     (worldgen only)
python .../adversarial/v_recheck.py        claims 2,4  builds verdict -- run serially
python .../adversarial/c4_marker.py        claim 4     builds verdict -- run serially
python .../adversarial/flipcheck_race.py   claim 5     builds verdict -- run serially
python -m pytest -p flipcheck <the [] test> claim 4    flipcheck.py, plugin recipe above
python -m pytest exam/tests -q             308 passed, 2 xfailed  (~107 s)
```

**Run the verdict-building ones one at a time.** They build the verdict paper,
which is the defect claim 5 describes; running two at once reproduces it against
you.

**`race.py`, `race2.py` and `hammer.py` are deliberately *not* in that list**:
they write into the shared tracked `exam/artifacts/variant_specs/` for minutes at
a time. `race_w1.txt` … `race_w6.txt` are `race.py`'s output from six concurrent
workers. `pytest_under_race.txt` and `pytest_under_race_2.txt` are *pytest's*
output from a suite run while `hammer.py` loaded the same directory from four
other processes — `hammer.py` itself prints nothing. `race2.py` is a
traceback-capturing variant whose output was not kept; the two tracebacks that
survive are the pytest ones. Their evidence is quoted under claim 5; re-run them
only in a throwaway worktree.

Confirmed after the full re-verification: `git status --short -- exam/artifacts/`
is empty. Nothing under `exam/artifacts/` was dirtied by any script above.

## What this pass did not attack

* **The twenty examiners' per-world reports** (`worlds/<id>.report.md`) were not
  individually re-derived. The two claims that reached `FINDINGS.md` from them
  were — the leak gate and the cheap prior — and those are claims 1 and 2 above.
  The rest are one context's word.
* **The discrimination partition itself.** Nothing here re-implements
  `free`/`memorised`/`theory`. The 97 / 70 / 69 split, and therefore the 41.1 %
  headline of claim 3, rests on `exam/tools/discrimination.py` alone — a tool
  written by the same run, in which this pass then found two defects. The
  arithmetic is consistent with `prior_sweep.json` (97/236 = 0.41102, the bluffer
  floor), which is a check and not a second opinion. **A second implementation of
  the partition is the largest single thing still owed on this item.**
* **The stale committed artefact.** `exam/artifacts/matrix/heldout_worldgen.json`
  carries `rubric_digest 4afe3d17…` against a live registry digest of
  `e06bdf52…`. Recorded in `RUN_STATE.md`, not regenerated, and not attacked
  here: it needs its own item, with a test that fails when a tracked artefact's
  digest falls behind the registry.
* **Whether either strict xfail is the right shape.** Both pin defects the pass
  chose not to fix, and both fixes have to decide a design question (should
  `SPEC_DIR` be per-process at all; what should `_read_set` do with a non-dict).
  The pass argued the deferral and did not attack it.
* **Anything outside `exam/`.** No claim here is about ARC, about a real
  examinee, or about the framework's own arms. Twenty synthetic worlds and one
  marker.
