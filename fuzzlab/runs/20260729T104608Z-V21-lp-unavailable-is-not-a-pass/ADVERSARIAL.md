# V-21 — adversarial review

Reviewed: `e1319503` (the fix) and — because it landed on the branch *while this
review was running* — `863e899d` (the counterfeit table, `minimize`'s cause axis,
the docs). Both are on `agent/v21-lp-unavailable-is-not-a-pass`. Working tree also
carries uncommitted edits to `fuzzlab/BUGS.md` and `fuzzlab/README.md`; where a
finding is already fixed there but not in any commit, it says so.

Everything below was run. Scripts are in
`runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/adversarial/`.

The headline: **the classification is right and the negative sample is real.**
I could not break (a) in the way the item feared, and I could not break (c) at
all. What I did break is the arithmetic underneath the new column, the taxonomy's
own boundary one line above the new code, a `minimize` regression shipped in
`863e899d`, and several sentences that are wider than the code — the exact defect
class this item exists to remove.

---

## 1. BLOCKER — `invariant_worlds_unavailable` counts *findings*, not *worlds*, and the coverage column it sits beside can go negative

`fuzzlab/campaign.py:93-96`

```python
ran = {
    name: n_worlds - by_invariant.get(name, Counter())[finding.SKIPPED]
    for name in invariants
}
```

and `fuzzlab/campaign.py:117-120`

```python
unavailable = {
    name: by_cause_class.get(name, {}).get(finding.UNAVAILABLE, 0)
    for name in invariants
}
```

Both subtract/count **findings**. Both are published under names that say
**worlds** (`invariant_worlds_evaluated`, `invariant_worlds_unavailable`,
`campaign.py:135-136`), and the V-21 docstring at `campaign.py:100-107` says
"`invariant_worlds_evaluated` says how many worlds an invariant judged". That
identity holds only if no invariant ever files more than one skip for one world.
`fuzzlab/props/cegis_miner.py:279-286` files a skip **inside a loop over rules and
`continue`s** (the `continue` is at `:286`), so it does not hold.

Experiment (`adversarial/multiskip.py`), 12 worlds, `COMBINATION_BUDGET` forced to
1 so the existing budget skip fires per rule:

```
invariant_worlds_evaluated: {..., "frontier_is_complete_to_size": -56, ...}
skips_by_cause           : {..., "frontier_is_complete_to_size": {"frontier_size_over_budget": 68}, ...}
skipped total            : 68
max skips for one (invariant, world): [(('frontier_is_complete_to_size', 8210080730272582832), 8), ...]
```

**`invariant_worlds_evaluated` = −56 out of 12 worlds.** `invariant_worlds_unavailable`
is computed by the identical shape, so the moment any property files two
`unavailable` skips on one world — a second solver call in one invariant, a sweep
that calls `_solve` per state, `infinite_means_unreachable` growing a second
`_solve` — the number V-21 exists to publish will exceed the world count and the
gate's message ("`%r world(s) went unjudged`", `tests/test_battery.py:88-93`) will
be false.

Today `lp_potential` files exactly one skip per invariant per world, so the column
reads correctly. That is the definition of *reconcilable only by luck*. A reader
would conclude the artifact reports worlds; it reports findings, and the two agree
by an unstated and unenforced invariant.

**Wrongly concluded if unfixed:** that `invariant_worlds_unavailable: 11` means
eleven worlds. It means eleven findings. And that the coverage column is a count —
it is an unclamped subtraction that has been observed at −56.

---

## 2. MAJOR — `test_the_skip_breakdown_reconciles_with_the_skip_count` cannot see finding #1, and its second assertion is an identity

`fuzzlab/tests/test_battery.py:99-115`

```python
assert by_cause == report["skipped"] == by_class
for name, row in report["skips_by_cause"].items():
    assert sum(row.values()) == WORLDS - report["invariant_worlds_evaluated"][name]
```

`campaign.py:94` defines `evaluated[name] = WORLDS - skip_count(name)`, so the
right-hand side *is* `skip_count(name)`, and the left-hand side is the same count
re-derived from the same findings. The assertion is `x == x`.

Proved by experiment rather than by algebra — the same −56 report from finding 1:

```
by_cause==skipped==by_class -> True
per-invariant reconcile assertion passes -> True  while evaluated = -56
```

The test is green on a report whose coverage column is negative. Its docstring
claims it guards against "the `unavailable` row could read 0 because a cause
stopped being counted" — the first assertion (`by_cause == report["skipped"]`)
does catch *that* specific drift, because `report["skipped"]` comes from a
separate `Counter` pass at `campaign.py:87`. The second assertion catches nothing
and should not be presented as a reconciliation.

Additionally: four of the six parametrisations (`mdl_segmenter`, `zero_space`,
`fd_adapter`, `probe_frontier`) file **zero** skips at 25, 60 and 500 worlds
(campaign output below), so for those engines the whole test is `0 == 0 == 0`.

---

## 3. MAJOR — `certificate_error` is filed `declined`, and by the taxonomy's own words it is `unavailable`

`fuzzlab/props/finding.py:89` — `"certificate_error": DECLINED`.

`finding.py:37-40` defines the class it was not put in:

> `unavailable` -- a tool did not compute: a solver limit, an unbounded
> relaxation, **numerical difficulties**. Nobody knows what the answer was.

and `finding.py:31-33` defines the class it was put in:

> `declined` -- a fact about the configuration or the evidence. The property had
> nothing to judge and that is the correct state of the world.

What `CertificateError` actually is, from the engine
(`engine-rig/engines/lp_potential/potential.py:401-404`):

```python
raise CertificateError(
    "LP weights %r fail exact re-checking: %r"
    % ([str(w) for w in weights], certificate.conditions)
)
```

HiGHS returned **status 0** — it says a certificate exists. The float weights were
then snapped with `Fraction.limit_denominator` and failed exact re-checking
(D-007). Nobody knows whether a linear pagoda exists for that configuration; the
*arithmetic* broke. That is verbatim the `unavailable` definition, and it is not
"the property had nothing to judge and that is the correct state of the world".

This is the same confusion V-21 was written to remove, sitting one `except` clause
above the new code: `props/lp_potential.py:210-211` now routes `LpUnavailable` to
`unavailable` while `props/lp_potential.py:212-213` routes `CertificateError` to a
cause classified `declined` (same pattern at `:244/:246`, `:292/:294`, `:331/:333`). A world whose exact re-check blew up passes
`test_nothing_went_unjudged_because_a_tool_could_not_compute` and is counted, in
`skips_by_cause_class`, beside the engine correctly declining.

It reads 0 today (500-world campaign: `certificate_error` does not appear in
`skips_by_cause`), so this is latent, not live — which is precisely how the
`LpUnavailable` hole sat until E-15 made it reachable.

**Also arguable, weaker, listed for completeness:** `evidence_not_alignable`
(`finding.py:78`) is filed at `props/cegis_miner.py:551-555` with the reason
"the oracle cannot line its evidence up with the engine's" — the *oracle* could
not compute, not the world being uninteresting; and
`effects_not_readable_as_translation` (`finding.py:79`,
`props/cegis_miner.py:613-619`) is "N transitions could not be read as one rigid
mover translation, so their effects were not judged". Both are defensible under
"or the evidence" in the `declined` definition, and both are 30+ findings on a
500-world run. I am not calling them misfiled; I am saying the phrase "or the
evidence" is load-bearing enough that it should be argued in `finding.py`, not
assumed. `certificate_error` is not in that grey zone.

**Every cause in `CAUSE_CLASS` against its call site** (the audit the brief asked
for), `finding.py:71-99`:

| cause | class | call site | verdict |
|---|---|---|---|
| `unminable` | declined | `cegis_miner.py:210` | correct — documented segmentation refusal, a fact about the world |
| `no_separating_guard` | declined | `cegis_miner.py:216` | correct — the fixed vocabulary cannot separate this evidence |
| `no_transitions` | declined | `cegis_miner.py:441` | correct |
| `mover_path_not_fixed_by_pixels` | declined | `cegis_miner.py:451` | correct — the pixels do not fix a trajectory |
| `mined_track_is_not_the_mover` | declined | `cegis_miner.py:478` | correct |
| `evidence_not_alignable` | declined | `cegis_miner.py:555` | grey (above) |
| `effects_not_readable_as_translation` | declined | `cegis_miner.py:618` | grey (above) |
| `frontier_size_over_budget` | budget | `cegis_miner.py:283` | correct, and the one that fires in a loop (finding 1) |
| `pddl_error` | declined | `fd_adapter.py:94` | correct — outside the supported STRIPS subset |
| `ground_bfs_budget` | budget | `fd_adapter.py:143,178` | correct |
| `no_states` | declined | `zero_space.py:109` | correct |
| `feature_sweep_over_budget` | budget | `zero_space.py:180` | correct |
| `no_certificate` | declined | `lp_potential.py:147` | correct — this is the whole point of the item |
| `certificate_error` | declined | `lp_potential.py:156` | **MISFILED** (above) |
| `no_state_list` | declined | `lp_potential.py:303,342` | correct-ish; it is a fuzzlab/world-generator gap, not the engine declining, but it is not "a tool failed to compute" either |
| `sweep_budget` | budget | `lp_potential.py:307,347` | correct |
| `bfs_budget` | budget | `lp_potential.py:223,367` | correct by the letter (fuzzlab's own threshold, quotable in advance) though it is the oracle not knowing; the taxonomy's split is stated, so I accept it |
| `solver_unavailable` | unavailable | `lp_potential.py:193-201` | correct |

---

## 4. MAJOR — `863e899d` broke `minimize --kind skipped`, and the help text says the opposite of what happens

`fuzzlab/minimize.py:76-92` (`signature()` now appends `.cause` for skips) against
`fuzzlab/minimize.py:100-102` (`want` appends the cause **only if `--cause` was
passed**). No skip finding can ever match a three-part `want` any more.

```
$ python -m fuzzlab.minimize --engine lp_potential --invariant three_conditions_hold \
      --kind skipped --pool 25 --archive <scratch>
searching 25 seeds for lp_potential.three_conditions_hold.skipped
no world in 25 reproduced lp_potential.three_conditions_hold.skipped

$ ... --kind skipped --cause no_certificate --pool 25 ...
  "reproducers": 13,
  "scanned": 25,
  "signature": "lp_potential.three_conditions_hold.skipped.no_certificate"
smallest: size 20, seed 0xcf08227e47a1cac5
```

13 reproducers in 25 seeds became 0. And `minimize.py:174-178` documents the
inverse of the behaviour:

> `--cause` … Skips of different causes are different events; **without this the
> search draws from every pool at once.**

Without it the search draws from **no** pool at all, and `main()` returns 1 with
"no world … reproduced", which reads as "this skip never happens".

Consequence for the committed archive:
`fuzzlab/archive/cegis_miner.frontier_guards_are_consistent.skipped.json` carries
`"signature": "cegis_miner.frontier_guards_are_consistent.skipped"` and its
`smallest.finding` has keys `['data','detail','engine','family','invariant','kind','seed','seed_hex']`
— **no `cause`**. That archived reproducer can no longer be re-derived by the tool
that produced it, under either invocation, and nothing in the suite notices.

---

## 5. MAJOR — "gated, not merely filed" is true of a 25-world pytest run and false of the 500-world artifact anyone reads

Claimed in four committed places:

* `fuzzlab/props/finding.py:41-43` — "`tests/test_battery.py` fails the suite when it is not"
* `fuzzlab/props/lp_potential.py:184-185` — "so the number is gated rather than filed"
* `fuzzlab/README.md:80-81` (committed) — "a `totals.unavailable` above zero means the run measured less than its coverage column claims, **and the suite fails on it**"
* `fuzzlab/BUGS.md` §V-21 Disposition — "so the number is **gated, not merely filed**"

The gate is `tests/test_battery.py:65-97`, which runs `campaign.run_engine(engine,
SEED, 25, quiet=True)` — 25 worlds per engine, with the real solver. The published
artifact is 500 worlds per engine. Nothing asserts on `totals` at all:

```
$ grep -rn "totals" fuzzlab/tests/
(no matches)
```

And the campaign itself does not care. `campaign.py:238-241` returns non-zero only
for generator errors. Experiment (`adversarial/starved_campaign.py`), 12 worlds,
real HiGHS at `maxiter=0`, every world unjudged:

```
campaign.main exit code with a blind solver: 0
```

`verify.py:68-71` — the new V-21 lines — only `print()`. `verify.py:52-53` appends
to `failures` solely on a non-zero subprocess return code, so `python -m
fuzzlab.verify` prints "N world(s) unjudged because a tool could not compute" and
then prints `green` and exits 0.

So: a HiGHS numerical failure that first appears at world 100 of the standing
campaign produces an artifact with `totals.unavailable > 0`, a green `verify`, and
a green `pytest`. The sentence "the suite fails on it" is wider than the code —
which is the *exact* defect shape this item was opened to remove.

**Partially fixed, uncommitted.** The working-tree `README.md` diff replaces that
clause with an accurate one ("`python -m pytest fuzzlab` fails on a non-zero
`unavailable` in the short per-engine campaign it runs; a hand-run `python -m
fuzzlab.campaign` prints the number rather than exiting non-zero"). `finding.py`,
`lp_potential.py` and `BUGS.md` still overclaim, and the README fix is not in any
commit.

---

## 6. MAJOR — `mutation.py` was not updated, and V-21 made its blind spot worse

`fuzzlab/mutation.py:114-139`. `run_mutant` builds `by_kind` for `VIOLATED` and
`RAISED` only; `worlds_evaluated` (`mutation.py:124`) counts every world where the
mutant applied and changed something, and never inspects skips. `mutation.json`
has no cause, cause-class or unavailable column at all.

`MUTATION.md` states the rule this violates — "a mutant that pushes worlds into
`skipped` has *unmeasured* them, not survived them" — and nothing enforces it.

Before V-21 an `LpUnavailable` under a mutant surfaced as `raised_only`
("detection in the weak sense", `mutation.py:18-21`). After V-21 it is a skip:
invisible, counted in `worlds_evaluated`, and the row prints `SURVIVED`. The fix
converted a weak signal into no signal in the one tool whose entire output is a
list of accusations.

Not observable today — I ran it:

```
$ python -m fuzzlab.mutation --engine lp_potential --worlds 20 --out <scratch>
lp_potential     6 mutants over 20 worlds
  lp-certify-solvable       unsound  eval=4  inert=16  killed by certificate_implies_unreachable,three_conditions_hold
  lp-raise-one-move         unsound  eval=4  inert=16  killed by three_conditions_hold
  lp-hide-the-raised-move   unsound  eval=4  inert=16  SURVIVED
  lp-overstate-margin       inconsistent eval=9 inert=11 killed by three_conditions_hold
  lp-heuristic-off-by-one   unsound  eval=9  inert=11  killed by heuristic_is_admissible
  lp-infinite-on-reachable  unsound  eval=9  inert=11  killed by heuristic_is_admissible,infinite_means_unreachable
mutants: 6   survivors: 1
```

— no current mutant raises `LpUnavailable`, so nothing is miscounted *now*.
`MUTATION.md:700-735` argues at length why no such mutant was added. That argument
is sound about `expect_kill`; it does not address the fact that `run_mutant`'s
`worlds_evaluated` denominator is now wrong for any future one, and it should say
so rather than closing the subject.

---

## 7. MAJOR — three committed pointers to a `RUN_STATE.md` that does not exist, and the pre-registration's own survivor-reporting promise is unmet

`fuzzlab/runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/` contains no
`RUN_STATE.md`, and `fuzzlab/RUN_STATE.md` has no V-21 section
(`grep -n "V-21\|V21" fuzzlab/RUN_STATE.md` → no matches; last commit touching it
is `1845e269`, the E-4 item).

Committed references to it:

* `fuzzlab/MUTATION.md:735` — "Results and survivors in `COUNTERFEITS.json` and that directory's `RUN_STATE.md`."
* `fuzzlab/tests/test_solver_unavailable.py:115` — "It is recorded as a survivor in `COUNTERFEITS.json` and in the run's `RUN_STATE.md`"
* `MANIFEST.json` `artifacts` — declares `RUN_STATE.md`: "narrative, deviations from the pre-registration, and the disposition of every adversarial finding"

`PREREGISTRATION.md` §5 promised: "Survivors are reported as survivors, in
`RUN_STATE.md`, without being retro-fitted with a test that makes them look
predicted."

`BUGS.md:439` records incident **R5** on this same file: *"`RUN_STATE.md` and
`MANIFEST.json` referenced an `ADVERSARIAL-1.md` that did not exist."* The item
has reproduced its own recorded incident, in the same directory, in the same week.

The survivor writeup does exist — in the **uncommitted** `BUGS.md` diff. It is
honest and good (it says outright that the closing assertion came after the
survivor, and that the pre-registered "hardest counterfeit" prediction was wrong).
It is just not where three committed files say it is, and not where the
pre-registration said it would be.

---

## 8. MAJOR — the two-class → three-class deviation has no deviation record, and `budget` weakens the gate exactly where it is least measured

`PREREGISTRATION.md` §1.2 pre-registered **two** classes:

> `finding.py` declares a taxonomy `CAUSE_CLASS` mapping each cause to
> **`declined`** … or **`unavailable`** …

`finding.py:52-57` ships **three**. There is no deviation record anywhere — no
`RUN_STATE.md` (finding 7), and `MANIFEST.json` does not mention it.

**Is it legitimate?** On the merits, yes, and I tried hard to argue otherwise.
Under a two-class taxonomy, `sweep_budget`, `bfs_budget`, `ground_bfs_budget`,
`feature_sweep_over_budget` and `frontier_size_over_budget` would all have had to
be `unavailable` (they are certainly not facts about the configuration), the gate
would be red on a green tree, and by the item's own standard — a gate whose
failures are mostly false is a gate people learn to ignore — it would have been
turned off. Splitting them out is the right call.

**But it is a goalpost move in one specific direction and that is not written
down.** `budget` is the class into which a future "we could not afford to compute
this" will naturally be filed, and it is ungated. `bfs_budget` in particular is
the *oracle* failing to decide reachability — "so 'unreachable' could not be
proved either way" (`props/lp_potential.py:220-223`) — which is "nobody knows",
routed away from the gate on the grounds that the threshold was chosen in advance.
The distinction is real, but it means the gate covers exactly one cause today
(`solver_unavailable`) out of eighteen. That is a much narrower claim than the
pre-registration's, and a reader of §1.2 would not know the boundary had moved.

`c-relabel-as-budget` in the counterfeit table shows the boundary is at least
tested (killed, 2 failing).

---

## 9. MINOR — the fix commit's own claim about `raised == 0` is honest, but `failures()`'s widening rests on a fact no test pins

Checked and it holds. 500-world campaign, all six engines
(`campaign.stdout.txt` in this run directory, regenerated by me at 60 worlds in
`adversarial/campaign60/`):

```
mdl_segmenter   gridworld      4 inv   500 worlds  violated=0 raised=0 skipped=0    unavail=0
cegis_miner     gridworld      6 inv   500 worlds  violated=0 raised=0 skipped=210  unavail=0
zero_space      parityworld    4 inv   500 worlds  violated=0 raised=0 skipped=0    unavail=0
lp_potential    jumpgraph      4 inv   500 worlds  violated=0 raised=0 skipped=932  unavail=0
fd_adapter      blockworld     3 inv   500 worlds  violated=0 raised=0 skipped=0    unavail=0
probe_frontier  hypset         5 inv   500 worlds  violated=0 raised=0 skipped=0    unavail=0
totals: raised 0, violated 0, unavailable 0, skipped 1142, worlds_checked 3000
```

So widening `failures()` breaks nothing and makes nothing vacuous — the pre-registration's
T7 argument is correct. The MINOR is that the property it relies on ("every
documented exception is caught at its property") is asserted in three docstrings
(`finding.py:14-17`, `finding.py:229-235`, `README.md`) and enforced nowhere. There
is no `ast` guard over `props/*.py` for "every `except <DocumentedError>` returns a
`skipped`", in the way `test_finding_contract.py` guards `cause`. The next
documented engine exception will re-open V-21 at a new entrance, and the only thing
that will notice is `test_short_campaign_passes_the_gate_the_docstring_describes`
at 25 worlds — which is a real net, and is the reason this is MINOR and not MAJOR.

---

## 10. MINOR — `verify.py` overwrites the committed `fuzzlab/out/` artifact it then reads, and the artifact is now schema-stale

`verify.py:35-36` runs `python -m fuzzlab.campaign --worlds 60` **without
`--out`**, so it writes `fuzzlab/out/{campaign,seeds,findings}` — nine tracked
files (`git ls-files fuzzlab/out`). `verify.py:55-58` then reads
`fuzzlab/out/campaign.json` and reports its `totals` as "last campaign totals".

The committed artifact was last written by `404e1360` and predates V-21:

```
$ python -c "... json.load(open('fuzzlab/out/campaign.json'))"
totals: {"generator_errors":0,"invariants":26,"raised":0,"skipped":152,"violated":0,"worlds_checked":360}
has skips_by_cause: False
engine0 keys: [... no invariant_worlds_unavailable, no skips_by_cause, no unavailable ...]
```

and `fuzzlab/out/findings.jsonl` rows carry the *old* convention — `cause` inside
`data`, no top-level `cause`/`cause_class`. So `verify.py:68` (`totals.get("unavailable")`)
is dead against the committed file, and the README's claim that `campaign.json`
publishes `invariant_worlds_unavailable` and `skips_by_cause` is false of the only
`campaign.json` in the repository. Either regenerate `out/` in this item or say in
`README.md` that it is a snapshot from a previous item.

(Newly generated artifacts *are* correct — `adversarial/campaign60/findings.jsonl`
top-level keys are `['cause','cause_class','data','detail','engine','family','invariant','kind','seed','seed_hex']`
with no duplicate `data.cause`. No consumer breakage: the extra keys are additive,
and `minimize`/`mutation`/the archive read attributes off live `Finding` objects,
not off the JSONL.)

---

## 11. MINOR — `863e899d` swept a reviewer's scratch directory into the branch

`git show 863e899d --stat` includes:

```
.../adversarial/campaign60/campaign.json     357 +
.../adversarial/campaign60/findings.jsonl    152 +
.../adversarial/campaign60/seeds.jsonl       360 +
.../adversarial/revert_both.py                 9 +
.../adversarial/revert_catch.py                7 +
.../adversarial/revert_failures.py             5 +
```

Those six files are **mine**. I created them under
`runs/.../adversarial/` (the location this review was told to use) between
`e1319503` and `863e899d`, and the commit picked them up wholesale. Nobody read
them before committing them. CLAUDE.md's rule is about `git add -A` at the repo
root; the mechanism and the hazard are identical one directory down. The commit
message does not mention them.

Also uncommitted-but-present and referenced from committed files:
`MANIFEST.json`, `COUNTERFEITS.json`, `COUNTERFEITS-recheck.json`,
`COUNTERFEITS.stdout.txt`, `campaign/` were untracked at `e1319503` and only
`campaign.stdout.txt` (not `campaign/campaign.json`) is tracked at `863e899d` —
so the 500-world evidence for T7 is still not in git.

---

## 12. NIT — `test_a_starved_solver_judges_nothing`'s `== 0` is stronger than the property it stands for

`fuzzlab/tests/test_solver_unavailable.py:83-92` asserts
`evaluated[name] == 0` for all four. Verified independently that this survives the
presolve world: on 1 of the 12 worlds HiGHS settles infeasibility in presolve and
returns a genuine `no_linear_pagoda` even at `maxiter=0` — my starved artifact
shows `{"no_certificate": 1, "solver_unavailable": 11}` per invariant, and
`test_the_starved_solver_really_is_a_real_highs_limit` confirms every raised
outcome is `status="budget"`, `solver_status=1`, `decided=False`. `evaluated`
reaches 0 only because that world also skips (as a *declined*). If a future scipy
presolve ever **certified** one of these worlds, `evaluated` would be 1 and this
test would go red for a non-defect. `test_blinding_the_solver_lowers_coverage...`
(`:142-160`) already states the property as a comparison for exactly this reason;
`:89` should too, or should say why the stronger form is safe.

---

## 13. NIT — the `unavailable` cause-class and the engine's `status="budget"` collide in one artifact

`props/lp_potential.py:190` writes `lp_status=outcome.status` into the skip's
`data`. For the common case (HiGHS status 1) that string is `"budget"`
(`engine-rig/engines/lp_potential/potential.py:46`), while fuzzlab has a *different*
cause class also called `budget` meaning "this battery chose not to pay"
(`finding.py:54`). A row in `findings.jsonl` therefore reads:

```json
{"cause":"solver_unavailable","cause_class":"unavailable","data":{"lp_status":"budget",...}}
```

Two meanings of "budget" in one record, one of which is the class this record is
deliberately *not* in. Rename the payload key (`highs_status_word`) or say in
`finding.py:34-36` that the collision exists.

---

## 14. NIT — `finding.CAUSE_CLASS` has no test that the gate can ever go red on a real run

`tests/test_battery.py:65-97` only ever observes `unavailable == 0`. The only
place the gate is shown failing is `tests/test_solver_unavailable.py` via a
starved solver, and `counterfeits.py`'s `c-unavailable-always-zero` /
`c-unavailable-counted-as-evaluated` (both killed). That is adequate coverage; it
is worth noting only because the gate test's docstring
(`test_battery.py:74-79`) says "if HiGHS hits numerical difficulties on some
future world, this goes red" and no test demonstrates that path at 25 worlds.

---

# Checked, and could not break

Honest list, including what I could not test.

1. **(b) The negative sample is real and it is not decoration.** I reverted the
   catch by rebinding `props._skip_solver_unavailable` to re-raise (a pytest
   plugin, `adversarial/revert_catch.py`, applied at `pytest_configure` so it is
   in force before any fixture) and re-ran the file:

   ```
   FAILED test_solver_unavailable.py::test_a_starved_solver_judges_nothing
   FAILED test_solver_unavailable.py::test_a_starved_solver_is_attributable_not_merely_absent
   FAILED test_solver_unavailable.py::test_unavailable_is_not_the_same_field_as_a_clean_decline
   FAILED test_solver_unavailable.py::test_blinding_the_solver_lowers_coverage_it_does_not_raise_it
   FAILED test_solver_unavailable.py::test_a_starved_solver_does_not_pass_the_gate
   ```

   5 of 7 go red. The two that stay green are correct to stay green:
   `test_removing_the_catch_lets_the_starved_solver_through` *is* the reverted
   state (it rebinds the same helper, so under the plugin it is a no-op), and
   `test_the_starved_solver_really_is_a_real_highs_limit` tests the engine, not
   the fix — it is the anti-vacuity guard, and it is the right test to have.
   **Neither is decoration.**

2. **The `failures()` widening is independently pinned.** Reverting only
   `failures()` to `VIOLATED`-only (`adversarial/revert_failures.py`) over the
   whole suite:

   ```
   FAILED test_finding_contract.py::test_failures_counts_an_unexpected_raise
   FAILED test_solver_unavailable.py::test_removing_the_catch_lets_the_starved_solver_through
   ```

   Two independent nets, one unit and one end-to-end. The two halves of the fix
   are each separately falsifiable.

3. **`test_removing_the_catch_lets_the_starved_solver_through` is not a strawman.**
   `props/lp_potential.py` pre-fix had no `except LpUnavailable` at all; the
   post-fix clause is `except LpUnavailable as exc: return _skip_solver_unavailable(...)`,
   so rebinding the helper to `raise exc` reproduces propagation out of the
   invariant into `finding.run_invariants`, which is byte-for-byte the pre-fix
   control flow at every observable (`raised` count, `skips_by_cause`,
   `invariant_worlds_evaluated`). I verified the reproduced pathology matches
   `before.json` exactly: `raised > 0`, `evaluated == worlds` for all four, no
   `solver_unavailable` anywhere.

4. **The fixture leak is really fixed.** `_PRISTINE_SOLVE` is captured at module
   import (`test_solver_unavailable.py:59`) and `_run_with` restores in a
   `finally` (`:62-68`), so requesting `starved_run` and `live_run` in one test
   yields genuinely different runs. Demonstrated by the numbers themselves: live
   `evaluated = 5` per invariant, starved `evaluated = 0`, in the same test
   function. The leak would have shown as 0/0.

5. **`maxiter=0` is a real HiGHS status 1, not a short circuit.** Independently
   confirmed the 11-of-12 claim: my own starved campaign artifact gives
   `skips_by_cause = {"no_certificate": 1, "solver_unavailable": 11}` per
   invariant, and `outcome.status == "budget"`, `solver_status == 1`,
   `decided is False` on all 11. The 12th world genuinely decides in presolve.
   The assertions remain meaningful given that world — `evaluated == 0` still
   holds because the presolve world is *also* a skip (see NIT 12 for the
   fragility).

6. **(c) `campaign.json` really can tell the two apart, from the artifact alone.**
   I built both worlds myself (`adversarial/starved_campaign.py`, 12 worlds each,
   real solver vs `maxiter=0`) and read the JSON rather than the tests:

   ```
   ===== STARVED (a tool could not compute) =====
   totals: {"raised":0,"skipped":48,"unavailable":44,"violated":0,"worlds_checked":12}
   invariant_worlds_evaluated   = {all four: 0}
   invariant_worlds_unavailable = {all four: 11}
   skips_by_cause               = {each: {"no_certificate":1,"solver_unavailable":11}}
   skips_by_cause_class         = {each: {"declined":1,"unavailable":11}}

   ===== CLEAN (checked and found nothing) =====
   totals: {"raised":0,"skipped":28,"unavailable":0,"violated":0,"worlds_checked":12}
   invariant_worlds_evaluated   = {all four: 5}
   invariant_worlds_unavailable = {all four: 0}
   skips_by_cause               = {each: {"no_certificate":7}}
   skips_by_cause_class         = {each: {"declined":7}}
   ```

   A reader who has never seen this code can distinguish them: `evaluated` 0 vs 5,
   `unavailable` 44 vs 0, and the cause breakdown names the reason in words. The
   fields are self-describing and `skips_by_cause` is not derivable from
   `evaluated`. Top-level `skips_by_cause` (`campaign.py:249-259`) keys on
   cause-class first, so `grep '"unavailable\.'` over the file is the whole audit,
   as advertised. **Nothing is double-counted** on a real 60-world and 500-world
   run: `sum(skips_by_cause) == skipped == sum(skips_by_cause_class)` for every
   engine, and `skipped(name) == worlds - evaluated(name)` for every invariant.
   The caveat is finding 1 — that agreement is contingent on one skip per world,
   not enforced.

7. **The classification did not just move the problem into another box, for the
   path it covers.** I looked for somewhere an `LpUnavailable` could still land
   unseen: `props/lp_potential.py` calls the engine only through `_solve`
   (`:126-127`), used in exactly four places, all four now wrapped; no other
   `props/*.py` imports `engines.lp_potential`; `campaign.py`, `minimize.py` and
   the archive route everything through `finding.run_invariants` or
   `module.check`, so an escape becomes a `raised`, and `raised` is now a
   `failures()` member gated per-engine at `test_battery.py:46-62`. The one place
   it *does* land unseen is `mutation.py` — finding 6.

8. **The `if not states or len(states) > SWEEP_BUDGET` split is
   behaviour-preserving.** `props/lp_potential.py:339-347` vs the pre-fix single
   guard: same control flow, same two outcomes, and the only payload difference is
   that the empty-list branch no longer emits `n_states=0`, which nothing reads.
   The split is required (the two need different causes) and it is correct.

9. **T8 holds.** `git diff --stat 41e72b34..HEAD -- engine-rig` is empty. No byte
   of `engine-rig/` was modified. The house rule is respected.

10. **The full suite is green.** `python -m pytest fuzzlab -q` → 129 passed, as the
    commit message claims (72 + 57 dots, 0 failures).

11. **Committed artifacts were not clobbered.** `git status` shows only `BUGS.md`
    and `README.md` modified; `fuzzlab/out/` is untouched. Every campaign I ran
    used `--out` into this run directory. (See finding 10 for why that is a
    *problem* rather than a virtue.)

## What I did not manage to test

* **I could not make the `unavailable` gate go red on a real world without
  injecting a starved solver.** Whether HiGHS ever produces status 3 or 4 on a
  natural `jumpgraph` world is unknown to me; 500 worlds produced neither. So
  finding 1's concrete danger (two `unavailable` skips on one world) is
  demonstrated only by analogy with `cegis_miner`'s budget skip, not directly on
  `lp_potential`.
* **I did not re-run `counterfeits.py`.** I read it and the recorded results; I
  did not independently verify that the 16 kills are kills or that
  `c-drop-the-outcome-payload` is now closed. `COUNTERFEITS.json` and
  `COUNTERFEITS-recheck.json` were untracked at `e1319503` and only partially
  tracked after `863e899d`, so I could not check them against git history either.
* **I did not test `minimize --kind raised` or the archive round-trip** beyond
  reading the one committed archive file's schema.
* **I did not exercise `fd_adapter`'s real Fast Downward path** — `.toolchain/` is
  absent here, so the adapter is on the BFS stub and 3 engine-rig tests skip. Any
  `unavailable`-shaped outcome from a real FD build is untested by me.
* **I did not verify `verify.py` end to end**, because running it would have
  overwritten the committed `fuzzlab/out/` artifacts (finding 10). Finding 5's
  claim about `verify` exiting 0 on non-zero `unavailable` is from reading
  `verify.py:42-78` plus the measured `campaign.main` exit code of 0; it is not a
  full end-to-end run.
* **The branch moved under me.** `863e899d` landed mid-review. Findings 1, 2, 3, 5,
  6, 7 were re-checked against it; anything that lands after this file is written
  is unreviewed.
