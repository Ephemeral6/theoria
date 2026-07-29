# E14 — a crash is not a finding

Prompt `E14-crash-is-not-a-finding`, lane `verify`, branch
`agent/e14-crash-is-not-a-finding`, base `bcea980`.
Zero API calls, zero model calls, zero network, zero sealed-pile contact.

This report is the **second pass**. An adversarial subagent refuted part of the
first, and its review is stored verbatim in `ADVERSARIAL-VERBATIM.md` — not
paraphrased, including the parts that say I reproduced this ticket's own disease
inside this ticket's fix. What it changed is listed under "What the adversarial
review broke", below, and the numbers here are the post-correction ones.

## The deliverable number

> Of the exhaustiveness / coverage / no-violation claims standing in the
> committed artifacts, how many were made on top of an **uncounted crash**?

**Zero.** Of **13** committed claims audited, **12** were exercised by the
instrumented re-run and every one came back with a crash count of 0; **1** was
**not exercised** and is reported as such rather than folded into the clean
column. Across all 14 instrumented claims, **0 crashes were observed anywhere**.

`raw/reconciliation.json`, `raw/reconcile.stdout.txt`.

| claim | artifact | committed | re-run |
|---|---|---|---|
| certify constraint 9 `unambiguous` | `runs/20260728T015354Z-g50t-first-contact/certify_reconstructed.json` | `ok: true`, "no (state, action) among 8 x 1 admitted two rules" | `ok: true`, crashes **0**, **8/8** pairs adjudicated |
| plan `unsat` / "the whole reachable set was enumerated" | same file | `status: no_goal_declared` | **NOT EXERCISED** — that manual declares no winning condition, so BFS never ran |
| a0 mined rule set: 4 of 12 effect classes published as disjunctive | `a0-spike/artifacts/a0_report.json` | no field distinguished a crash from a finding | all 4 are genuine `NoSeparatingGuard`; crashes **0** |
| a0 `certify.replay_exact`, `certify.exactly_one_successor` (2 claims) | `a0-spike/artifacts/a0_report.json` | `true`, 1966 transitions | `true`, crashes **0** |
| a0 `adaptation repair[v].replay_exact` / `.exactly_one_successor`, 4 variants (8 claims) | `a0-spike/artifacts/adaptation.json` | `true`, no crash field existed | `true`, crashes **0** |
| plan `unsat`, worked example, unreachable goal, **through `plan()`** | *(new instance, added here)* | — | `unsat`, `exhaustive: true`, 3 states, crashes **0** |

Three things about that zero, all of which cut against me:

* **It is a weak zero on the worst site.** The only archived arm run carries a
  manual with no goal, so `plan.py`'s `unsat` exit — the site the ticket is
  really about — was never reached by any *published* claim. I added a fourth
  instance so the site executes, but no committed artifact rests on it. The
  instrument is proven; the arm-side corpus is one run deep.
* **"No crash was recorded" and "no crash happened" are different sentences.**
  Before this change the committed artifacts could only support the first. They
  now support the second. That is the value of the zero — the old reports were
  not wrong, they were *unfalsifiable*, and the number could not have been
  computed at all without the instrumentation.
* **The denominator was originally 3, and that was a choice, not a finding.**
  The adversarial review pointed out that the audited call site also produces
  `a0_report.json:certify` and all four `repair` blocks of `adaptation.json`.
  Those are now in, which is how 3 became 13.

Three further committed claims are **deliberately outside** the population, with
the reason recorded in `reconciliation.json` and in the code:
`certify_generated.replay_exact`, `held_out.exact` and
`levels[*].theorem.unsolvable` all stay `true` under an injected mining crash,
and *should* — `certify_generated(module, episodes)` and the held-out loop
predict through the module compiled from `theory/theory.dsl` and never see
`rules`, and `unsolvability_certificate(level)` takes only a `Level` and
compares two parities. Gating them on a mining crash would report a defect at a
site that has none, which is the same error pointing the other way.

The a0 result deserves saying out loud: the published DNF rule set
(`blocked_*_1`, `blocked_*_2`, ...) was **correct**. All four disjunctive
classes reach `NoSeparatingGuard`, the miner's designed verdict. What was wrong
is that `a0_report.json` contained nothing a reader could use to know that.

## What changed

### 1. Crash counts in the artifact

`theoria-arm/inner/plan.py` — `_tier_bfs`. The bare `except Exception: continue`
around `step(state, action)` now records into `StepCrashLog`: count, type
histogram, successors pruned, and up to 8 verbatim samples with the action and
the expansion index. The count is never capped; only the sample is. The account
is stamped onto the entry **once, after the search returns**, in a wrapper —
not per exit. That is structural: it is what makes "a new exit forgets the
account" impossible rather than merely fixed, and the first pass got it wrong
exactly that way.

`theoria-arm/inner/certify.py` — `_ambiguity`. Both swallow points instrumented:
the `break` that truncates state reconstruction (`phase: reconstruct`) and the
`pass` that skipped a pair in the sweep (`phase: sweep`). The report now carries
`pairs_checked` beside `pairs_nominal` — the old detail line multiplied
`len(states) x len(actions)`, a *nominal* product that counted crashed pairs
inside the claimed coverage. Two adjacent bugs fixed with it: the loop swept
`states[:400]` while the sentence reported `len(states)`, which could be 401;
and the default for a missing `AmbiguousTransition` was `Exception`, which made
`except ambiguous` swallow every crash and file it as a constraint-9 **clash** —
a positive finding about the world manufactured out of a bug, with
`pairs_checked` exceeding `pairs_nominal` and a crash count of zero. It is now a
sentinel class nothing raises.

`a0-spike/pipeline/stages.py` — `mine`. The bare `except Exception` conflated the
miner's **designed verdict** (`NoSeparatingGuard`, which genuinely means "this
class admits no single conjunctive guard") with any crash at all. Split:
`NoSeparatingGuard` is a finding and lands in `account.no_separating_guard`;
everything else is a crash and lands in `account.crashes`. Every rule carries
`disjunctive_because` — `"no_separating_guard"` or `"synthesis_crashed"` — and
`unsound_after_crash`.

### The gating

Every field claiming exhaustiveness / coverage / no-violation is emitted **next
to** the crash count and is false whenever that count is non-zero:

| field | site | when crashes > 0 |
|---|---|---|
| `status: "unsat"` + `exhaustive: true` | `plan._tier_bfs` | `status: "unsat_unsound"`, `exhaustive: false`, `error: "step raised N time(s) ..."`; "the whole reachable set" no longer appears |
| `optimal: true` on the `sat` path | `plan.plan` | `optimal: false` + `error`; BFS is length-optimal only if no successor was dropped |
| `ok: true` (constraint 9) | `certify._ambiguity` | `ok: false`, `error`, `pairs_checked < pairs_nominal`; "admitted two rules" no longer appears |
| `all_guards_searched` / `disjunction_is_a_finding` | `stages.MiningAccount` | both `false`, every emitted rule stamped `unsound_after_crash: true` |
| `certify.replay_exact` / `.exactly_one_successor` | `stages.certify(..., account)` | both `false` + `error`; ungated values kept as `*_before_crash_gate` |
| `repair.replay_exact` / `.exactly_one_successor` | `adapt.repair` | both `false` + `error` |
| exit codes | `run_a0.main`, `adapt.main` | non-zero; the count is a conjunct of the verdict, not a footnote under it |

A zero count is printed too, always. A printed zero is evidence; an absent one
is indistinguishable from a check that never looked. A *false* printed zero is
worse than either — which is what the review found on the `sat` path.

### 4. The gold standard's shape, copied

`engine-rig/bench/ladder.py:74-82,226` on a budget overrun writes
`proved_unsolvable: False` **and** `error: "over budget: ..."`, and records
`stub_max_expansions` positively. Copied on both counts:

* the negative claim is written explicitly false rather than omitted, and it
  travels with an `error` string naming the cause;
* the ceiling goes into the artifact positively. `_tier_bfs` emits
  `search_ceiling: {node_cap, deadline_s}` and `_ambiguity` emits `sample_cap`
  and `cap_reached`, so a reader can check "3 < 120000" from the artifact
  instead of trusting a sentence saying the search did not run out.

## 3. The negative sample, and the proof it is not vacuous

`negative_sample.py` produces `raw/negative_sample.json` and
`raw/negative_sample.stdout.txt`. Three columns per site. A `step` / a
`synthesize` **constructed** to raise — an exception type neither site declares,
so it can only land in the handlers under audit.

```
theoria-arm/inner/plan.py  _tier_bfs   [status / exhaustive]
    control          unsat          exhaustive=True   crashes=0   states=3
    POISONED         unsat_unsound  exhaustive=False  crashes=1   states=1   -> red? True
    counting removed unsat          exhaustive=True   crashes=0   states=1   -> waved through? True

theoria-arm/inner/certify.py  _ambiguity   [ok (constraint 9)]
    control          ok=True   crashes=0  1/1 pairs
    POISONED         ok=False  crashes=1  0/1 pairs   -> red? True
    counting removed ok=True   crashes=0  0/1 pairs   -> waved through? True

a0-spike/pipeline/stages.py  mine   [all_guards_searched / disjunction_is_a_finding]
    control          searched=True   crashes=0   no_sep_guard=4  unsound_rules=0
    POISONED         searched=False  crashes=12  no_sep_guard=0  unsound_rules=17  -> red? True
    counting removed searched=True   crashes=0   no_sep_guard=0  unsound_rules=17  -> waved through? True
```

The `plan` row is the ticket's thesis printed as three numbers: the control
enumerates **3** states and says so; the poisoned run enumerates **1** and, with
the counting removed, still reports `unsat` / `exhaustive: True` / "the whole
reachable set (1 states) was enumerated". **The predictor got worse and the
health certificate got cleaner.**

The `certify` row is the same disease: `ok: true`, "no (state, action) among
1 x 1 admitted two rules" — on **zero** pairs actually adjudicated.

Same as tests: `theoria-arm/tests/test_arm.py` (+8), `a0-spike/tests/test_a0.py`
(+6), each site with a control so a gate that fired unconditionally would fail
rather than pass. The adversarial reviewer independently reverted the gate in
each of the three sources and confirmed the substantive tests then FAIL — a test
that passes on un-fixed code is worthless, and one of mine was (see below).

**Caveat on both ablations.** Removing `record` removes the *gate*. It does not
remove the second mechanism the same change added at two of the three sites: in
a0 the per-rule `disjunctive_because: "synthesis_crashed"` stamp is set on the
exception branch itself (`unsound_rules` stays 17), and in certify
`pairs_checked` increments only on a non-raise, so `pairs_checked (0) <
pairs_nominal (1)` still betrays the crash. Pre-E14 code had neither field at
either site. So those columns are ablations of the gate, not byte-faithful
reproductions of the old code. Only the `plan` column is byte-faithful (checked
against `git show HEAD:theoria-arm/inner/plan.py`). The first pass gave this
caveat to a0 only; the review demanded it for certify too, correctly.

## What the adversarial review broke

Stored verbatim in `ADVERSARIAL-VERBATIM.md`. Verdicts: (a) **REFUTED**,
(b) **PARTIALLY REFUTED**, (c) **PARTIALLY REFUTED**. Corrections applied:

1. **The `sat` exit published a false zero.** `step_crashes` was a snapshot
   taken before the search and refreshed at only two of the exits. A search that
   crashed and then found the goal reported `count: 0`. Fixed structurally —
   stamped once in a wrapper after the search returns. This was this ticket's
   own disease surviving inside this ticket's fix, and it is the single most
   embarrassing thing in this run.
2. **`optimal: true` was ungated.** It is an exhaustiveness claim; the reviewer
   built a case where the crashing action was the *shortcut*, so BFS reported
   length 3 and `optimal: True` when a 2-step route had been pruned. Now gated.
3. **`adapt.repair` counted and then ignored.** `replay_exact` and
   `exactly_one_successor` stayed `true` under 12 injected crashes, with the
   count sitting harmlessly beside them. Now gated; `adapt.main()` returns 1 and
   prints a crash row.
4. **This report contradicted its own artifact** — the first version said "1/1
   pairs adjudicated" where `reconciliation.json` says 8/8. Fixed above.
5. **The reason given for bypassing `plan()` was false.** `reconcile.py` claimed
   the PDDL tier answered `sat` first. It does for `goal Cart.pos = (0, 0)`
   (`gen_pddl` hardcodes objects to cell 0,0) but not for the `(2, 2)` goal the
   script actually uses — the tier refuses correctly and BFS runs. The sentence
   was true of an earlier draft and was not re-checked when the goal changed.
   The instance now runs through `plan()`, which is also where correction 1 was
   hiding.
6. **The denominator was too narrow** — 3 became 13; three further claims are
   explicitly declared out of population with their dependency evidence, which
   is a partial decline of this correction rather than compliance with it.
7. **The certify ablation needed the caveat I gave only to a0.** Added, in the
   script that generates the column.
8. **`test_the_green_light_reads_the_crash_count` grepped source** and passed on
   semantically reverted code. Replaced with a behavioural test that runs
   `run_a0.main()` under an injected crash (with `ARTIFACTS` redirected into
   `tmp_path`) and asserts a non-zero exit.
9. Also taken from the optional list: the missing-`AmbiguousTransition` default
   (`Exception` → sentinel), which was filing crashes as findings about the
   world.

What the review attacked and did **not** break: the gate survives to
`certify.cheap()`'s `report["ok"]` and to `armtools/timeline.py`'s renderer;
crashes out of `nxt.key()`, `is_goal(nxt)` and `BaseException` propagate loudly
rather than being swallowed; a *partial* crash still goes red; the certify
re-run is a faithful reproduction of the committed claim (same 8 states, same
`8 x 1`, byte-identical divergence cells); the arm-side corpus really is one run
deep; and the "1 NOT EXERCISED" classification is the honest call.

Not adopted, and why: optional 9 (`{"ok": True, "scope": "not_attempted"}`
rendering as a tick in `timeline.py`) and 12 (`timeline.py` never prints the
plan status) both mean editing the renderer for behaviour the ticket did not
name; recorded under "Left undone" instead. Optional 11 (the reconstruct loop
`break`ing silently on `arc_action is None`) is real but is not a crash path.

## Suites

`theoria-arm` 51 → **59 passed**. `a0-spike` 44 → **50 passed**. No committed
artifact was modified: `git status` after the full runs, both scripts, and the
adversarial reviewer's own poisoned `run_a0.main()` shows only the seven source
files this ticket changed plus this run directory. (`a0-spike`'s pipeline does
rewrite `artifacts/theory_exec.py` and `artifacts/pddl/*` on every run — they
come back byte-identical, so the known "a test run rewrites a committed
artifact" hazard did not bite here. The new behavioural test redirects
`run_a0.ARTIFACTS` into `tmp_path` so it cannot.)

## Left undone, on purpose

* **No new surprise is fired** when `plan` downgrades to `unsat_unsound`.
  `inner/surprise.py` states the seven kinds are fixed and an eighth is a change
  to `Theoria.md` 1.10(d), not to that file; and firing an existing kind would
  spend a model call in a live run. The survey's separate observation — that
  `search_timeout` fires a surprise and `unsat` does not, so a false `unsat` is
  fully silent — remains true and is not fixed here.
* **`certify.py`'s `{"ok": True, "scope": "not_attempted"}`** when the initial
  state will not render, which `armtools/timeline.py:190` prints as constraint 9
  passing. Same disease, site the ticket did not name, and the fix belongs in
  the renderer. Reported, untouched. The adversarial reviewer's note stands:
  naming it is not fixing it.
* **`armtools/timeline.py` never prints the plan status at all**, so
  `unsat_unsound` does not reach the human-readable artifact. Same reason.
* **The re-run compiles the archived books with today's
  `theory-compiler/.../gen_python.py`**, which has moved twice since the audited
  artifact was committed (`3787e2d`, `76e7560`). So the zero is strictly "today's
  generator, applied to those books, does not crash". The identical `8 x 1`
  detail string and byte-identical divergence cells are the evidence that this
  did not matter here; pinning the generator would mean checking out another
  track's history, which is out of territory.
