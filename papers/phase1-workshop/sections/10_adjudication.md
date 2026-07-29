## 10 · Does the adjudication surface exist? A census of the implementation

§2.2 states the division this framework is built on: **engines emit candidates,
never verdicts**, and what enters the manual is written down by the LLM. That is
a claim about a design. Whether it survives contact with the implementation is a
different question, and it has one characteristic failure mode: a tool's
*failure state* — a non-zero exit code, a default value, a crash, a budget cap —
read as a *property of the world*. When that happens the adjudication surface has
not been overridden, it has been quietly erased: there is nothing left for the
LLM to adjudicate, because the engine already answered.

This section reports a four-pass read-only census of the repository against that
failure mode. It is placed here, as a result, rather than in §11 with the
limitations, because it is the only measurement in this paper of the mechanism
§2.2 claims, and because one of its findings is that the division is
*structurally* enforced in the one place it would matter most (§10.4).

The census was run by a different working session of the same model, in the same
repository — the relationship §4.2 describes between the two tracks, which is
weaker than an outside audit and is not claimed as more. The surveying lane also
wrote most of the repairs reported below, so it is not independent of those
either. §10.7 states where the raw reports live, why the citation is to a
preservation copy, and what the census cannot establish.

### 10.1 The census, and why this section publishes no total

Four passes, each scanning for one shape of the failure mode, are preserved at
`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/`.
The figures below are **each pass's own summary line**, not a re-count:

| Pass | File | Scan surface, as stated | Unsafe, as stated |
|---|---|---|---|
| solver status read as an answer | `SURVEY-solver-status.md` | ~60 points | 3 |
| empty result read as a negative | `SURVEY-empty-as-negative.md` | ~40 points | 8 |
| environment fact read as semantics | `SURVEY-environment-as-semantics.md` | ~240 points | 37 |
| success signal read as truth | `SURVEY-success-as-truth.md` | ~105 points | 8 |

**No total is published here, and no rate.** The obvious headline — around 340
points examined, 48 judged unsafe — does not survive, and neither does any
replacement assembled by adding these columns up, which gives 445 and 56. Four reasons, in increasing
order of severity.

First, **the passes did not use one ruler.** One states the criterion under which
the census is usually quoted: `SURVEY-solver-status.md:7-11` asks whether a
tool's failure or uncertainty was rendered as *a property of the world*, with
`Theoria.md` constraint 6 — universal assertions carry proofs, a bare UNSAT is
forbidden — as its baseline. A second states a *different* one:
`SURVEY-environment-as-semantics.md:6-7` asks the narrower question of whether an
**environment fact** — crash, non-zero exit, timeout, decode failure, resource
cap, concurrency — was turned into an assertion about the object of study. The
remaining two state none: `SURVEY-empty-as-negative.md` opens with its summary
table, and `SURVEY-success-as-truth.md:32-33` gives table *columns*, which is a
schema and not a threshold. Fifty-three of the fifty-six unsafe judgements were
made under a criterion that is unstated or different from the one they are
quoted under.

Second, **the passes' own arithmetic does not close.**
`SURVEY-solver-status.md:16` states a scan surface of ~60 points and then names
more than seventy sites, of which the *legitimate* list alone — 51 table rows at
`:274-376` plus 11 backticked paths in the prose at `:367-374`, over 10 distinct
files — is of the same order as the whole stated surface.
`SURVEY-environment-as-semantics.md:12` states 37 unsafe while its three unsafe
tables enumerate **40** rows (`:28-35`, `:41-64`, `:76-83`). Neither file
reconciles the two numbers. This is precisely the discipline
`SURVEY-empty-as-negative.md:87-92` proposes as a rule for everyone else: an
audit issuing an affirmative claim must publish both the number of objects it
*should* have covered and the number it *did*, and must withhold the affirmative
claim when they differ. No pass meets its own criterion.

Third, **the counts quoted downstream are not enumerations.** The "~45 legitimate
exit-code readings" that reached the work items and the digests
(`monitor/inbox/archive/20260729T063000Z-RES-3-the-pattern-you-named-appears-three-more-times.md:168-169`)
appears in no survey. The "~97 further legitimate usages" from the fourth pass
(`monitor/inbox/archive/20260729T104500Z-RES-3-the-dual-exists-and-it-has-a-different-shape.md:100`)
is `105 − 8` — arithmetic residue, not a list.

Fourth, and decisively: **the passes overlap, and where they overlap they
disagree.** `engine-rig/engines/lp_potential/potential.py:170-171` is graded
安全 — safe — at `SURVEY-solver-status.md:308` and unsafe at
`SURVEY-environment-as-semantics.md:77`. `probe_frontier/reach.py:94-99` is safe
at `:290` and unsafe at `:80`. `cegis_miner/miner.py:323` is safe at `:339` and
mismeasured at `:131`. Any sum over the four passes therefore counts some sites
twice, and counts at least three of them on both sides of the ledger at once.

An earlier draft of this section replaced the disputed 340 / 48 with an
enumerated 85 / 56 and called that the countable figure. It is not: the 85 omits
the largest pass's positives entirely, the 56 is the sum of the four summary
lines this section had just impeached, and both inherit the double-counting
above. **The honest report is per-pass figures with their provenance and no
aggregate at all.** The census cannot say what fraction of this repository's
adjudication points are unsafe, and this section does not claim to know.

### 10.2 Four families, four registered examples

The taxonomy below — *exit code taken as proof; default value taken as truth;
crash taken as discovery; hitting a cap taken as exhaustion* — is a synthesis
made after the fact, not a category system the passes ran under; no survey names
four families. It is used here because it is the smallest description that covers
the unsafe rows, and it is labelled as a synthesis for the same reason the counts
above are refused.

Each family gets one example that was registered or repaired before this section
was written.

**Exit code taken as proof.** `engine-rig/tools/p13_fd_dividend.py` published a
planner's verdict as `unsolvable=done.returncode == 12`, while the same
repository's own constant table
(`engine-rig/engines/fd_adapter/backends.py`) reads
`FD_SEARCH_UNSOLVED_INCOMPLETE = 12` — exit 12 is *search stopped without
finding anything*, not a proof of unsolvability. Repaired: the field is now
written by a predicate, `backends.proves_unsolvable(rung, returncode, log)`,
which requires the rung to be a complete configuration and takes the exhaustion
line from the planner's log, with a conservative default rung. The consequence
for a published number is in §10.5.

**Default value taken as truth.** `worldgen/core/truth.py` derives a
manifest-level claim as
`"invariants_all_hold": all(i.get("holds", True) for i in invariants)`.
Prose-only invariants are appended *without* a `holds` key — only the verified
branch sets one — so an invariant that is **not checkable** defaults to holding,
and the world publishes `invariants_all_hold: true`. Thirteen worlds carry at
least one unverified invariant and every one of them publishes the boolean as
true. The thirteen are the census's count; the denominator is re-derived here,
because the census never states one — `worldgen/out/worlds/` holds 35
directories with a `ground_truth.json`, so it is **13 of 35**. The shape worth
keeping is that the same module's Markdown renderer prints
`_(prose only, unverified)_` honestly: the human-readable form tells the truth
and the machine-readable form does not, and only the machine-readable one is
consumed downstream.

This is the one of the four that is **not** repaired, and how it is not repaired
belongs in the section: the fix is filed as done on the internal work board while
the line stands byte-for-byte unchanged on the mainline. A done-marker read as a
landed fix is the same error one level up.

**Crash taken as discovery.** `a0-spike/pipeline/stages.py` wrapped CEGIS guard
synthesis in a bare `except Exception:` — without even binding the exception — so
an engine crash was recorded as the finding *this class of transition admits no
single conjunctive guard*, and a disjunctive rule set was published on the
strength of it. No field anywhere in the report recorded that the fallback had
fired. Repaired: the catch is split, the designed verdict
(`no_separating_guard`, which *is* a finding about the world) separated from
`synthesis_crashed`, the crash routed into the payload, and the green light made
to depend on it — `all_guards_searched` now returns `not self.crashes`. The
companion site in `theoria-arm/inner/plan.py` was the worst-directioned instance
the census found: **every crash made the health certificate look cleaner.** It is
repaired the same way, and the sentence claiming the reachable set was enumerated
is now unreachable when any successor was pruned.

**The repair does not reach backwards, and §3.5 of this paper cites the arm it
did not reach.** `a0-spike/artifacts/a0_report.json` was last written before the
fix. Its `mine` block carries 20 rules, of which twelve are
`blocked_<direction>_1`, `_2`, `_3` — the three-way disjunction the fallback path
emits — and the file contains no `reason`, `no_separating_guard` or
`synthesis_crashed` field anywhere. So it cannot be determined *from the artefact*
whether that disjunction is the miner's designed verdict about the world or an
unrecorded crash. What §3.5 quotes from that arm — 341 transitions certified, 8
mismatches on unreachable states, 39,960 well-formed states at 0 mismatches,
1,966 actions, and the T-10 detection latencies — are measurements of the
*adjudicated theory* against the world and do not depend on which path produced
the guard shape. Those numbers stand. The provenance of the guard shape does not.

**Hitting a cap taken as exhaustion.** `engine-rig/engines/lp_potential/potential.py`
returned `None` on `not result.success`, collapsing HiGHS status 2 (genuinely
infeasible — no linear pagoda exists) together with status 1 (iteration cap), 3
(unbounded) and 4 (numerical trouble), while the function's docstring pinned that
`None` to a geometric fact. The engine could not distinguish *does not exist*
from *I ran out*. Repaired: only status 2 returns `None`; every other
non-success raises `LpUnavailable`, whose message states the distinction — "this
is a fact about the solver, not about the configuration, so no unreachability
claim follows from it".

**On direction, the census does not support the strong claim.** In all four
families above the defaulting runs one way: an unavailable answer becomes a
favourable one, and in the `theoria-arm` case the certificate improves with every
crash. It is tempting to generalise that to the corpus, and the corpus refuses.
`SURVEY-environment-as-semantics.md:37-64` is a group of **24 rows devoted to the
opposite direction** — an environment failure turned into a *negative* verdict
about the system under test, such as a read-only pin check failing closed or a
tool error closing a merge interlock — and `:92-107` marks a fourth group's
direction explicitly conservative. The asymmetry is a property of the four
families exhibited here, not a measured property of the repository. No pass
counted sites by direction, and this section does not.

### 10.3 The immune control, and the gold standard

A census that reports only positives leaves a reader unable to judge how strict
the criterion was, so the negatives are published — per pass, and without a
ratio, for the reasons §10.1 gives:

* `SURVEY-solver-status.md:274-376` names **51 table rows** that read a solver
  status correctly, plus **11 backticked paths** across 10 files in its prose.
* `SURVEY-environment-as-semantics.md:138-230` names **28 distinct Python sites**
  as exemplars, and grades cap handling in a further 20-row table at `:113-134`.
* `SURVEY-success-as-truth.md:43-79` names **8** exemplars — and files **7 more**
  separately, under a heading warning that verified-but-not-independent is *the
  category most easily misread as safe*. Two of those 7 are defects this section
  reports elsewhere: `zero_space.verify`'s circularity (§10.6) and `validate.py`'s
  shared grounding premise (§10.4). They are not immune controls and are not
  counted as any.
* `SURVEY-empty-as-negative.md:30-58` names **6**.

The exemplar is `engine-rig/bench/ladder.py`. Its over-budget path returns
`"proved_unsolvable": False` **and** `"error": "over budget: …"` in the same
dictionary — the cap recorded positively rather than absorbed — and the cap
itself is published into the artefact as `stub_max_expansions`, at a value its
own comment says was chosen small enough that the batch runs off the end of it.
The honest converse is on the other branch: `"proved_unsolvable": not
result.solved` is asserted only where the budget was *not* hit.

**One qualification, which the census did not make and which the paper's own
argument requires.** `ladder.py` excludes over-budget rows from its failure list
(`if row.get("error") and "over budget" not in str(row["error"]):`). That is
defensible — a non-answer is not a fault — but it means the gold standard is a
claim about the **artefact**, not about the **gate**. The distinction is the
subject of §10.4 and it applies to the exemplar too.

### 10.4 What the division of labour does guarantee, and what it does not

**The strongest positive result: no planner in this rig grades its own answer.**
The failure mode's most dangerous form — *a solver returned a plan, therefore the
instance is solvable* — does not occur here, and it does not occur structurally
rather than by promise. In `engine-rig/engines/fd_adapter/__init__.py`, both
branches of the tier fork — the BFS stub and the two Fast Downward rungs —
converge on one line that calls `validate_plan(domain, problem, plan.actions)`
with no `if`, no `try`, no tier test and no conditional expression in front of
it. The only early returns are the *no-plan* paths, where there is nothing to
validate. Every plan this engine publishes has passed that line;
`probe_frontier`'s `REACHABLE` verdict inherits the guarantee by routing through
the same entry point, and `engine-rig/bench/ladder.py`, which calls the stub's
search directly, calls the validator itself rather than skipping it.
`engine-rig/engines/fd_adapter/validate.py` contains no import of the searcher.

**The scope of the guarantee is narrower than that sentence, and the source says
so.** `validate.py`'s own docstring names the residual shared premise: validator
and searcher both import `pddl.ground_actions`, which is not merely a parser — it
filters on static preconditions while instantiating, and so decides which action
instances can fire with which effects. A forgotten delete effect *there* is
invisible to the validator. So the correct statement is: **a plan passing
validation is a plan legal under the shared grounding, not one legal under the
PDDL as written.** The census files this correctly, under *verified but not
independent*; the summaries that quote it drop the qualification. It is kept.

**The dual shape: computed correctly, published, and then not used as a gate.**
Three instances — two now closed, one still open at the artefact boundary.

* `engine-rig/engines/lp_potential/potential.py` published `"admissible": True`
  as a **literal** in the payload dict, while the real check sat in an
  `admissibility_check` field of the same payload that the headline never read. A
  certificate whose check said `holds: false` still serialised as admissible.
  Now derived: the headline reads the itemised licence, and the licence is
  published beside it. Not a mine that never fired — at the census's own base
  commit the defective field was already sitting in the committed,
  sha256-pinned `engine-rig/artifacts/candidates.jsonl`. (The census's note to the
  contrary, that the artefact contained no such field, is wrong, and wrong in the
  direction that understates the severity.)
* `engine-rig/engines/deadlock_carver/__init__.py` computed
  `PruningReport.same_answer` — an empirical falsifier asking whether the theorem
  changed the instance's answer — serialised it, and published it **beside the
  theorem it refutes**, with neither overriding the other. Now gated: a refuted
  theorem is withheld by default, the alternative policy stamps `refuted: True`
  into the payload, and the counts of what was withheld travel with the row.
  Separately, `same_answer` now raises rather than compare two unfinished
  searches.
* Still open: `engine-rig/engines/zero_space/zerospace.py` degrades its subset
  enumeration past a limit of 8 and records that it did so in a
  `scope_exhaustive` field — which `Law.as_json` deliberately does **not** emit,
  because `engine-rig/artifacts/candidates.jsonl` is sha256-pinned in a release
  manifest and widening the payload would re-hash every row of it. A reader of
  the published stream still cannot tell a proved `scope: "global"` from an
  unsearched one. It is the clearest case the census found of a fix blocked by a
  release pin rather than by disagreement, and it is recorded as such rather than
  closed
  (`engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md`).

### 10.5 Two published numbers that rest on a re-derivation, and one retraction

Two figures published elsewhere in this repository were produced by a method that
should not have been able to produce them. **In both cases the conclusion is
currently true and the method was unsound.** The distinction is the whole point
of the section and it is not a softening: neither of these is a retracted result.

**`lp_potential`'s 29.2 % incompleteness rate** (`engine-rig/ENGINE_TABLE.md`;
not quoted anywhere in this paper). The engine could not yield this number,
because `potential.py` discarded the bit that distinguishes infeasibility from an
iteration cap. A reviewer rebuilt the LP independently and re-derived it: of 639
silences, **638 are still infeasible at bounds of 100, 10⁴ and 10⁶** and one is
an artefact of a hard-coded weight box. The rate survives to the published
precision — *because the reviewer re-derived the bit the engine threw away*, not
because the engine kept it. The method is now fixed (§10.2) and the rerun has not
happened: the table still cites the reviewer's reconstruction. A second limit
that the summaries drop and the table itself is scrupulous about: for those 638,
"no linear pagoda exists" rests on HiGHS returning float infeasibility with **no
exact Farkas dual produced** — a solver's claim, not a proof.

**The three `fd_unsolvable: true` rows** in
`engine-rig/runs/p13-fd-real/dividend.json`. Three of seven cross-check rows
assert unsolvability, and the field that asserts it was written by the bare
`returncode == 12` of §10.2, with no check of rung, log, or the plan file the
tool had already read. The conclusions hold anyway, for two reasons the census
states *before* the accusation: that tool calls Fast Downward only under
`astar(blind())` — a complete, admissible, cost-unbounded configuration, in which
an emptied open list genuinely is a proof — and the independent BFS stub agrees
on all three rows, raising on budget exhaustion rather than returning a silent
`None`. The rig as a whole is **not** pinned to blind search:
`engine-rig/bench/ladder.py`
runs `lmcut`, `ipdb` and a satisficing alias, and the adapter's default heuristic
is `lmcut`. The guarantee belongs to the calling tool, not to the repository.
Two facts the census did not state and this section does: **the artefact predates
the fix and was never regenerated**, so the three `true`s committed today are the
output of the defective line rather than of the predicate that replaced it; and
**the artefact cannot be re-adjudicated from itself**, because the evidence fields
the fix introduced are absent from rows written before it existed — a limitation
the repaired tool's own docstring concedes.

So: one number has a fixed method and a stale citation, the other a fixed method
and a stale artefact. Neither is a wrong answer, and neither should have been
reached the way it was.

**The retraction.** The census withdrew one of its own claims, in place. A
cross-check had reported that `p13_fd_dividend.py` would publish a false
negative — prose reading *zero, on both engines* when both planner runs had
crashed. The surveyor checked it and struck it: that prose branch formats with
`%d`, and `"%d" % None` raises, so the path crashes loudly rather than
publishing. The claim was **replaced rather than dropped** — the adjacent table
branch, which formats with `%s` and therefore does print `None -> None`, was
recorded in its place — and the retraction was carried into the digest with its
reason: the retraction itself needs a record.

**The retraction is itself incomplete.** A downstream worker re-opened it on a
different mechanism: `dividend.json` is written by `json.dump` *before* the
human-readable renderer is called, so in the double-crash scenario the misleading
field did reach the JSON artefact regardless; the `%d` crash protected only the
prose. The repair therefore does not rely on the crash
(`engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md`).

### 10.6 No held-out validation — what E17 changed, and what it did not

The heaviest finding of the fourth pass was an absence rather than a defect:
**the engine rig had no held-out validation anywhere**, and a search of the
engine package for any spelling of the term returned nothing. `zero_space` is the
clean statement of the problem: the laws it reports *are* the null space of the
observed differences, and its `verify()` re-checks those laws on the same
trajectory they were fitted from — `engine-rig/ENGINE_TABLE.md` puts it more
sharply than the census did, saying the check **cannot fail by construction**. A
verifier that exists, is independent of the code it checks, and runs on the
evidence that produced the answer, is not validation.

A dedicated round of work has since landed, and it changes the picture for **two
of eight engine rows** (`engine-rig/ENGINE_TABLE.md`):

* `zero_space` — leave-one-operation-out: a global hit rate of **13.1 %** across
  1680 laws on withheld operations, against 92.9 % cell-local.
* `lp_potential` — leave-one-geometry-out across 289 instances: **26.4 % of 1408
  certificates** still satisfy their closure condition on the withheld geometry,
  and **58 are outright false** against brute-force ground truth.

The other six rows have no held-out validation of any kind, and the rule is
machine-enforced rather than promised: `engine-rig/tests/test_engine_table.py`
asserts that a row may carry the held-out marker **iff** the engine is one of
those two. The table's own standing rule is that a cell without held-out
validation may say *self-consistent on the observed evidence* and may not say
*verified*.

**Five qualifications, all of which the numbers above need.**

1. **`zero_space.verify` is still circular.** The held-out work measured *around*
   the defect with a parallel harness; it did not touch the engine. The caller
   still passes the fitting trajectory to the verifier.
2. **The absence the census reported is still literally true of the engines.**
   The held-out code lives in a new top-level package that no engine imports.
3. **13.1 % is a dial, not a constant, and the table says so.** An equally
   defensible one-fifth training split lands at **35.3 %**, and leaving two
   operations out at **2.0 %**. The table attributes the gap to the corpus's line
   geometry: rebuilt cyclic, so that every cell is touched by the same number of
   operations, the same cut gives 66.7 % global against 100.0 % cell-local. The
   mechanism is real; the magnitude is a fact about the corpus.
4. **One of the round's two headline numbers was taken away by its own
   adversarial review.** A 70/30 transition split had scored **100.0 %**, and
   that measured nothing: mutating the splitter to return *overlapping* train and
   test sets moved no published digit. Novelty is now published with the figures —
   0 of 2160 withheld rows new in the vacuous split, 7200 of 7200 in the one
   reported above. Five further overturns are on the record, including that the
   `lp_potential` emit gate had been scored against the complete graph while
   fitting on the reduced one; handed the partial evidence a caller actually
   holds, **all 1408 certificates would be emitted, including all 58 false
   ones**, each carrying `holds: true` into the shared candidate stream. That is
   a counterfactual the harness measured, not an emission that happened — no such
   row is in the published stream. Mutation testing found 14 of 19 mutants
   surviving, all inside the new package, which had no tests
   (`engine-rig/runs/20260729T034043Z-E17-held-out-validation/CORRECTIONS.md`).
5. **Both measurements are on synthetic families generated by the harness.** No
   live-game data and no second world family has been held out for any engine, so
   even those two rows have no held-out backing for their live-ARC figures. The
   ticket's third item — making the split rig-wide at fixture-generation time —
   was deliberately *not* done, on the ground that as specified it would hand
   every future engine a meaningless 100 % hit rate: the defect the ticket
   existed to remove, institutionalised
   (`engine-rig/runs/20260729T034043Z-E17-held-out-validation/RUN_STATE.md`).

**What this does not license is a change of wording elsewhere in this paper.**
The census's finding was commissioned with an instruction to sweep the body and
downgrade every "verified" to *self-consistent on the observed evidence* until
held-out validation landed. It has landed, for two rows, and the sweep was
checked against the text and is not needed for the rest. The word occurs **eight
times outside this section**: once about a *third party's* world model verified
by replaying its recorded history (§1.1); three times naming a certificate's own
`verified` field, where each sentence's point is that the consuming side refuses
to trust it (§1.5, §4.2); once about the pile digest (§7.1); and three times in
§12 — one is §12's note that its own citations were cross-verified against two
sources, one is the sentence **"no claim is made to have verified any engine"**,
and one explains a citation the paper declines to make. **None of the eight is a
claim to have verified an engine.** 已验证 appears nowhere in the body outside
this paragraph. A find-and-replace would have changed nothing that needed
changing and corrupted sentences that were already correct.

### 10.7 The provenance of this section, and what it cannot establish

The four census reports cited above exist as **untracked files inside a single
machine-local git worktree, on a branch that was never pushed**. The originals
are on no ref, local or remote, and the run directory's own manifest does not
list them. They are the primary evidence for six work items and for this section.

They are therefore cited here through byte-verbatim copies committed into this
paper's run directory
(`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/`,
with their origin and sha256 recorded in the run's `MANIFEST.json`), and the line
references in this section are line numbers in those copies. Citing a path that
resolves on one laptop is the documentary form of the error this section is
about: a claim whose support cannot be reached by the person reading the claim.

Every source claim above was read from the tree rather than from the census. The
file-and-line audit is
`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/evidence-survey-located.md`,
and its re-check against the commit this section was written at is
`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/reverification-at-32f078c.md`.
Between them they record eight corrections to the material this section was built
from: two to the census reports themselves — including the "mine set but not
fired" mitigation contradicted in §10.4 — four to the work item that commissioned
this section, among them the four-family taxonomy of §10.2 and the two
unenumerable counts of §10.1, and two to downstream documents.

**Three things the census cannot establish, which bound every sentence above.**

* **No threshold was declared in advance.** Nothing says what number of unsafe
  sites would have counted as §2.2 failing, and §10.1 explains why no such number
  is even available. This paper treats pre-registration as decisive elsewhere
  (§1.2, §7.3); this measurement has none, and no base rate from any other
  codebase to compare against. It can say *these particular sites read a failure
  state as a fact about the world*. It cannot say whether that is many.
* **It is not reproducible.** It was a human reading, its criterion changed
  between passes, and re-running it would not be re-running anything. It is
  evidence about this repository at one commit, not a method this paper offers.
* **It is not independent of what it audits.** The surveying lane wrote most of
  the repairs it reports and filed the work items that institutionalised them, in
  the same repository, as another session of the same model. That is the hole
  §11.3 names in the A0/A0′ seal, one level up: the party that found the defects
  also graded the fixes.
