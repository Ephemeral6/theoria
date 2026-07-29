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
§2.2 claims — and because its most useful findings are not concessions. Two of
the four passes found the division of labour structurally enforced in places
where nothing obliged it to be.

The census was run by a reviewer inside the repository, not by the authors of
the code it examined, and its raw reports are cited throughout. §10.7 states
where they live and why the citation is to a preservation copy.

### 10.1 The census, and the ruler it was taken with

Four passes, each scanning for one shape of the failure mode, are preserved at
`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/`:

| Pass | File | Stated scan surface | Judged unsafe |
|---|---|---|---|
| solver status read as an answer | `SURVEY-solver-status.md` | ~60 points | 3 |
| empty result read as a negative | `SURVEY-empty-as-negative.md` | ~40 points | 8 |
| environment fact read as semantics | `SURVEY-environment-as-semantics.md` | ~240 points | 37 |
| success signal read as truth | `SURVEY-success-as-truth.md` | ~105 points | 8 |

**The headline those tables invite — 340 points, 48 unsafe — is not reported
here, and the reason is itself the finding.** Three things are wrong with it.

First, the four passes did not use one ruler. Two write their criterion down and
the two criteria are different: `SURVEY-solver-status.md:7-11` asks whether a
tool's failure or uncertainty was rendered as *a property of the world*, with
`Theoria.md` constraint 6 (universal assertions carry proofs; a bare UNSAT is
forbidden) as its baseline; `SURVEY-environment-as-semantics.md:6-7` asks the
narrower question of whether an **environment fact** — crash, non-zero exit,
timeout, decode failure, resource cap, concurrency — was turned into an assertion
about the object of study. The other two passes state no criterion at all:
`SURVEY-empty-as-negative.md` opens with its summary table, and
`SURVEY-success-as-truth.md:32-33` gives table *columns*, which is a schema and
not a threshold. **48 of the 56 unsafe judgements, including all 37 of the
largest pass, were made against a criterion that is either unstated or different
from the one under which they are usually quoted.**

Second, the largest pass's own arithmetic does not close.
`SURVEY-solver-status.md:16` states a scan surface of ~60 points; the same file
then names 3 unsafe, 2 latent, 1 declared ablation, 6 documentation-propagation
sites and **64 legitimate** ones — 76 named sites against a stated surface of 60,
with the legitimate list alone exceeding the surface. Nothing in the file
reconciles the two numbers. This is precisely the discipline
`SURVEY-empty-as-negative.md:87-92` proposes as a rule for everyone else:
any audit issuing an affirmative claim must publish both the number of objects
it *should* have covered and the number it *did*, and must withhold the
affirmative claim when they differ. The census does not meet its own criterion.

Third, the counts that were quoted downstream are not enumerations. The "~45
legitimate exit-code readings" that appear in the work item and the inbox
digest appear in no survey; the enumerable figure is 64. The "~97 further
legitimate usages" from the fourth pass is `105 − 8` — arithmetic residue, not a
list; that pass names 15 sites.

**What can be published is what can be counted.** Across all four reports, **85
sites are named as legitimate and 56 as unsafe.** Every number in the rest of
this section is of that kind: read off a named file at a named line, not
inherited from a summary.

### 10.2 Four families, four registered examples

The taxonomy below — *exit code taken as proof; default value taken as truth;
crash taken as discovery; hitting a cap taken as exhaustion* — is a synthesis
made after the fact, not a category system the passes ran under; no survey names
four families. It is used here because it is the smallest description that covers
the 56, and it is labelled as a synthesis for the same reason the counts above
are not rounded up.

Each family gets one example that was already registered or already repaired
before this section was written. None was dug up for the occasion.

**Exit code taken as proof.** `engine-rig/tools/p13_fd_dividend.py` published a
planner's verdict as `unsolvable=done.returncode == 12`, while the same
repository's own constant table
(`engine-rig/engines/fd_adapter/backends.py`) reads
`FD_SEARCH_UNSOLVED_INCOMPLETE = 12` — exit 12 is *search stopped without
finding anything*, not a proof of unsolvability. Repaired: the field is now
written by a predicate, `backends.proves_unsolvable(rung, returncode, log)`,
which requires the rung to be a complete configuration and takes the
exhaustion line from the planner's log, with a conservative default rung.
The consequence for a published number is in §10.5.

**Default value taken as truth.** `worldgen/core/truth.py` derives a
manifest-level claim as
`"invariants_all_hold": all(i.get("holds", True) for i in invariants)`.
Prose-only invariants are appended *without* a `holds` key — only the verified
branch sets one — so an invariant that is **not checkable** defaults to
holding, and the world publishes `invariants_all_hold: true`. The census counted
independently: **13 of 35 built worlds carry at least one unverified invariant,
and every one of them publishes the boolean as true.** The shape worth keeping is
that the same module's Markdown renderer prints `_(prose only, unverified)_`
honestly — the human-readable form tells the truth and the machine-readable form
does not, and only the machine-readable one is consumed downstream.

This is the one of the four that is **not** repaired, and how it is not repaired
belongs in the section: the fix is filed as done on the internal work board while
the line stands byte-for-byte unchanged on the mainline. A done-marker read as a
landed fix is the same error one level up.

**Crash taken as discovery.** `a0-spike/pipeline/stages.py` wrapped CEGIS guard
synthesis in a bare `except Exception:` — without even binding the exception — so
an engine crash was recorded as the finding *this class of transition admits no
single conjunctive guard*, and a DNF rule set was published on the strength of
it. No field anywhere in the report recorded that the fallback had fired.
Repaired: the catch is split, the designed verdict (`no_separating_guard`)
separated from `synthesis_crashed`, the crash routed into the payload, and the
green light made to depend on it — `all_guards_searched` now returns
`not self.crashes`. The companion site in `theoria-arm/inner/plan.py` was the
worst-directioned instance found: **every crash made the health certificate look
cleaner.** It is repaired the same way, and the sentence claiming the reachable
set was enumerated is now unreachable when any successor was pruned.

**Hitting a cap taken as exhaustion.** `engine-rig/engines/lp_potential/potential.py`
returned `None` on `not result.success`, collapsing HiGHS status 2 (genuinely
infeasible — no linear pagoda exists) together with status 1 (iteration cap), 3
(unbounded) and 4 (numerical trouble), while the function's docstring pinned that
`None` to a geometric fact. The engine could not distinguish *does not exist*
from *I ran out*. Repaired: only status 2 returns `None`; every other
non-success raises `LpUnavailable`, whose message states the distinction — "this
is a fact about the solver, not about the configuration, so no unreachability
claim follows from it".

**The direction is the finding.** These are not random errors. In all four
families the defaulting runs one way: an unavailable answer becomes a favourable
one. That asymmetry, not the count, is what makes the class worth a section.

### 10.3 The immune control, and the gold standard

A census that reports only positives leaves a reader unable to judge how strict
the criterion was, so the negatives are published with the same weight: **85
named sites read a failure signal correctly** — 64 in the solver-status pass (51
enumerated table rows plus 13 CI paths named in its prose), 15 in the
success-as-truth pass, 6 in the empty-as-negative pass. The success-as-truth pass
also keeps a third category the ratio above does not have: 7 sites that verify,
but not independently.

The exemplar is `engine-rig/bench/ladder.py`. Its over-budget path returns
`"proved_unsolvable": False` **and** `"error": "over budget: …"` in the same
dictionary — the cap recorded positively rather than absorbed — and the cap
itself is published into the artefact as `stub_max_expansions`, at a value chosen
deliberately small enough that the batch runs off the end of it. The honest
converse is on the other branch: `"proved_unsolvable": not result.solved` is
asserted only where the budget was *not* hit.

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
validate. Every plan this engine publishes has passed that line, and
`probe_frontier`'s `REACHABLE` verdict inherits the guarantee through it.
`engine-rig/engines/fd_adapter/validate.py` contains no import of the searcher.

**The scope of the guarantee is narrower than that sentence, and the source says
so.** `validate.py`'s own docstring names the residual shared premise:
validator and searcher both import `pddl.ground_actions`, which is not merely a
parser — it filters on static preconditions while instantiating, and so decides
which action instances can fire with which effects. A forgotten delete effect
*there* is invisible to the validator. So the correct statement is: **a plan
passing validation is a plan legal under the shared grounding, not one legal
under the PDDL as written.** The census files this correctly, under *verified but
not independent*; the summaries that quote it drop the qualification. It is kept
here.

**The dual shape: computed correctly, published, and then not used as a gate.**
Two instances, both now closed, one still open at the artefact boundary.

* `engine-rig/engines/lp_potential/potential.py` published `"admissible": True`
  as a **literal** in the payload dict, while the real check sat in an
  `admissibility_check` field of the same payload that the headline never read. A
  certificate whose check said `holds: false` still serialised as admissible.
  Now derived: the headline reads the itemised licence, and the licence is
  published beside it. Not a mine that never fired — at the census's own base
  commit the defective field was already sitting in the committed,
  sha256-pinned `engine-rig/artifacts/candidates.jsonl`. (The census's note to
  the contrary, that the artefact contained no such field, is wrong, and wrong in
  the direction that understates the severity.)
* `engine-rig/engines/deadlock_carver/__init__.py` computed
  `PruningReport.same_answer` — an empirical falsifier asking whether the theorem
  changed the instance's answer — serialised it, and published it **beside the
  theorem it refutes**, with neither overriding the other. Now gated: a refuted
  theorem is withheld by default, the alternative policy stamps
  `refuted: True` into the payload, and the counts of what was withheld travel
  with the row. Separately, `same_answer` now raises rather than compare two
  unfinished searches.
* Still open: `engine-rig/engines/zero_space/zerospace.py` degrades its subset
  enumeration past a limit of 8 and records that it did so in a `scope_exhaustive`
  field — which `Law.as_json` deliberately does **not** emit, because
  `engine-rig/artifacts/candidates.jsonl` is sha256-pinned in a release manifest
  and widening the payload would re-hash every row of it. A reader of the
  published stream still cannot tell a proved `scope: "global"` from an
  unsearched one. **This is the cleanest instance in the repository of a fix
  blocked by a release pin rather than by disagreement**, and it is recorded as
  such rather than closed
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
tool had already read. The conclusions hold anyway, for two reasons stated in the
census *before* the accusation: the repository calls Fast Downward only under
`astar(blind())`, a complete, admissible, cost-unbounded configuration, in which
an emptied open list genuinely is a proof; and the independent BFS stub agrees on
all three rows, raising on budget exhaustion rather than returning a silent
`None`. Two facts the census did not state and this section does: **the artefact
predates the fix and was never regenerated**, so the three `true`s committed
today are the output of the defective line rather than of the predicate that
replaced it; and **the artefact cannot be re-adjudicated from itself**, because
the evidence fields the fix introduced are absent from rows written before it
existed — a limitation the repaired tool's own docstring concedes.

So: one number has a fixed method and a stale citation, the other a fixed method
and a stale artefact. Neither is a wrong answer, and neither should have been
reached the way it was.

**The retraction.** The census withdrew one of its own claims, in place and
against its own interest. A cross-check had reported that `p13_fd_dividend.py`
would publish a false negative — prose reading *zero, on both engines* when both
planner runs had crashed. The surveyor checked it and struck it: that prose
branch formats with `%d`, and `"%d" % None` raises, so the path crashes loudly
rather than publishing. The claim was **replaced rather than dropped** — the
adjacent table branch, which formats with `%s` and therefore does print
`None -> None`, was recorded in its place — and the retraction was carried
forward into the digest with the reason given: it is recorded because the
retraction itself needs a record.

**And the retraction is itself incomplete**, which is the part that makes it
worth the space. A downstream worker re-opened it on a different mechanism:
`dividend.json` is written by `json.dump` *before* the human-readable renderer is
called, so in the double-crash scenario the misleading field did reach the JSON
artefact regardless; the `%d` crash protected only the prose. The repair
therefore does not rely on the crash
(`engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth/CORRECTIONS.md`).
A claim, its retraction, and the partial re-opening of the retraction are all on
the record, each signed by a different party.

### 10.6 No held-out validation — what E17 changed, and what it did not

The heaviest finding of the fourth pass was an absence rather than a defect:
**the engine rig had no held-out validation anywhere**, and a search of the
engine package for any spelling of the term returned nothing. `zero_space` is the
clean statement of the problem: the laws it reports *are* the null space of the
observed differences, and its `verify()` re-checks those laws on the same
trajectory they were fitted from, so the assertion guarding the engine is close
to impossible to trigger. A verifier that exists, is independent of the code it
checks, and runs on the evidence that produced the answer, is not validation.

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

**Four qualifications, all of which the numbers above need.**

1. **`zero_space.verify` is still circular.** The held-out work measured *around*
   the defect with a parallel harness; it did not touch the engine. The caller
   still passes the fitting trajectory to the verifier.
2. **The absence the census reported is still literally true of the engines.**
   The held-out code lives in a new top-level package that no engine imports.
3. **One of the round's two headline numbers was taken away by its own
   adversarial review.** A 70/30 transition split had scored **100.0 %**, and
   that measured nothing: mutating the splitter to return *overlapping* train and
   test sets moved no published digit. Novelty is now published with the figures —
   0 of 2160 withheld rows new in the vacuous split, 7200 of 7200 in the one
   reported above. Five further overturns are on the record, including that the
   `lp_potential` emit gate had been scored against the complete graph while
   fitting on the reduced one; handed the partial evidence a caller actually
   holds, **all 1408 certificates are emitted, including all 58 false ones**, each
   carrying `holds: true` into the shared candidate stream. Mutation testing found
   14 of 19 mutants surviving, all inside the new package, which had no tests
   (`engine-rig/runs/20260729T034043Z-E17-held-out-validation/CORRECTIONS.md`).
4. **Both measurements are on synthetic families generated by the harness.** No
   live-game data and no second world family has been held out for any engine, so
   even those two rows have no held-out backing for their live-ARC figures. The
   ticket's third item — making the split rig-wide at fixture-generation time —
   was deliberately *not* done, on the ground that as specified it would hand
   every future engine a meaningless 100 % hit rate: the defect the ticket
   existed to remove, institutionalised
   (`engine-rig/runs/20260729T034043Z-E17-held-out-validation/RUN_STATE.md`).

**What this does not license is a change of wording elsewhere in this paper.**
The obvious response — sweep the body and downgrade every "verified" — was
checked against the text and rejected. The word occurs seven times: once about
a *third party's* world model verified by replaying its recorded history (§1.1);
three times naming a certificate's own `verified` field, and on all three the
sentence's point is that the consuming side refuses to trust it (§1.5, §4.2);
once about the pile digest (§7.1); and twice in §12, where one is the sentence
**"no claim is made to have verified any engine"** and the other explains a
citation the paper declines to make. The Chinese 已验证 does not occur at all. **None of the seven is a claim
to have verified an engine**, so a body-wide rewrite would have changed nothing
that needed changing while corrupting several sentences that were already
correct. The finding belongs in a section, which is where it is.

### 10.7 The provenance of this section

The four census reports cited above exist, at the time of writing, as **untracked
files inside a single machine-local git worktree, on a branch that was never
pushed**. They are on no ref: a search of every local and remote head for their
filenames returns nothing. They are the primary evidence for six work items and
for this section, and one `git clean` would have ended them.

They are therefore cited here through byte-verbatim copies committed into this
paper's run directory
(`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/`,
with their origin and sha256 recorded in the run's `MANIFEST.json`), and the
line references in this section are line numbers in those copies. The
alternative — citing a path that resolves on one laptop — is the documentary
form of the same error this section is about: a claim whose support cannot be
reached by the person reading the claim.

Every source claim above was read from the tree rather than from the census.
The file-and-line audit is
`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/evidence-survey-located.md`,
which also lists the eight places the census reports are themselves wrong, and
the re-check of all of it against the commit this section was written at is
`papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/reverification-at-32f078c.md`
beside it. Two of those eight matter to the
text above and are carried into it: the "mine set but not fired" mitigation in
§10.4, which is false, and the four-family taxonomy of §10.2, which no census
pass wrote.

Two consequences are worth stating plainly. The counts in §10.1 that do not
reconcile were found by reading those files rather than the digests that quote
them, and the digests are what every downstream work item actually cited; the
discrepancy was invisible from the summaries. And the census is not a
reproducible measurement: it was a human reading, its criterion changed between
passes, and re-running it would not be re-running anything. **It is evidence
about this repository at one commit, not a method this paper offers.**
