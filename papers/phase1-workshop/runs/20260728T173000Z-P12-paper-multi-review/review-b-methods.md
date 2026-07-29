# Review B — methods referee

**Remit.** Is the evidence sufficient for each claim, and is the paper internally
consistent in how it measures things? Written without sight of the other
reviewers. Line references are `PAPER.md:<line>` unless stated. Every artefact
claim below was checked against the file on disk; no artefact was regenerated,
no network was touched, no sealed-pile game was read.

**Summary judgement.** This is an unusually candid paper and the candour is
real — most of the limitations I would normally have to extract are already
written down. That makes the residual failures more serious, not less, because
they are the ones the paper's own discipline did not catch. I find **five
blocking issues**. Two of them (B1, B2) are not presentational: one headline
section reports as open a problem the repository records as closed, and the
battery's headline statistic does not measure what the surrounding sentence says
it measures. A third (B3) omits a control value from the one section framed as a
controlled measurement.

The paper's binding rule — every quantitative claim carries its artefact path —
is a good rule and it works. Where it fails it fails in one specific way: the
paper cites a *report's prose* where an *artefact* exists and disagrees, or
cites the earlier half of a file that later supersedes itself. That is the
pattern behind B1, M9 and M10.

---

## 1 · Claim-by-claim sufficiency

The abstract numbers eight results; §10.5 states one claim. Taken in order.

### Abstract (1) — replay-perfect, world-wrong, predicted in advance

*Evidence.* `cold-start-a0/artifacts/score_vs_truth.json`
(`base.behavioural.accuracy` 0.987288, agree 233 / pairs 236;
`held_out.accuracy` 0.0 over 3 pairs) and
`cold-start-a0/artifacts/trace_summary.json` (`covered_pairs` 233,
`uncovered_pairs` naming the three). Both verified. The three uncovered pairs
are exactly the three the manual gets wrong — I checked the two lists element by
element and they match.

*Sufficient?* For the existence claim, yes. For the pre-registration claim, only
partly — see §4 below and **M1**. A sceptic demands one thing the paper cannot
supply from the paper: an ordering guarantee not written by the same script. The
paper knows this and says so (`PAPER.md:59`, "a declaration written by the
authors' own script, not a control"). What it then does with that admission is
the problem: it declines the one cheap corroboration available.

*n.* The held-out accuracy is n = 3. §7.4 calls out that three decimal places
over a denominator of three is a presentational overstatement (`PAPER.md:1452`
ff.) and requires the abstract to carry the denominator; the abstract does
(`PAPER.md:64`). Credit where due — this is the paper policing itself correctly.

### Abstract (2) — A0′, reversibility beats coverage

*Evidence.* `cold-start-a0/prime/artifacts/prime_report.json`: `run_a.score_vs_truth`
228/228, `trace.a0p-base.coverage` "107/228", `engines.executable_probes` 13,
`run_b.score_vs_truth_before` 0.991228 → `_after` 1.0, `revisions` 1. All
verified. The paper's note that Run B's replay is a bare boolean while the
frame/pixel shape sits under `run_a` (`PAPER.md:187–193`) is exactly right and is
the kind of disclosure that earns trust.

*Sufficient?* The paper demotes this itself — "demonstrates the mechanism rather
than tests it", analytic entailment, `PAPER.md:146–160`. That demotion is correct
and unusually honest. But see **M11**: the demotion is not carried through to
§1.3 and §10.5, which still call it a *controlled comparison*.

### Abstract (3) — A1, weights across a data boundary, empty axiom list

*Evidence.* `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`,
`theory-compiler/STATUS.md`, negative control at `PAPER.md:783` ff.

*Sufficient?* The negative control is the right instrument and the paper is
straight about its scope ("run inside the same project rather than by a third
party", `PAPER.md:785`). The two-track independence is correctly deflated to
defence-in-depth (`PAPER.md:747–751`). **But §4.4 is factually stale — see B1.**
And n = 1 fixture, stated (`PAPER.md:826`).

### Abstract (4) — the two Lean files

*Evidence.* `cold-start-a2/artifacts/exhibit_report.json`: `certify_cheap`
184 frames / 14 904 pixels / 0 anomalies; `certify_cheap_vs_full_sweep` 248
frames, 44 anomalies, first at t184 cell (6,4); `certify_lean.axiom_reports`
`[{"axioms": [], "name": "unsolvable"}]`. All verified, including the paper's
correct note that the "128 unexplained of 20 088" figure is *not* in the
artefact and is cited to the report instead (`PAPER.md` §5.4).

*Sufficient?* Yes for what it claims, and §11.3 already says the exhibit "is not
evidence about anything" beyond being a teaching object and an instrument test
(`PAPER.md:2740` region). §5.6's correction of its own source report is the
strongest single act of self-discipline in the draft. One residue: the artefact
records `plan.backend: null` for A2's UNSAT, while §10.3 asserts every planning
number in the paper is the BFS stub. That is a provenance gap, not an error
(**minor 5**).

### Abstract (5) — the battery

*Evidence.* Verified in detail: `capability_spectrum.json` 95 runs, arms
{bare_cc 80, schema_repro 8, theoria_a2 4, theoria_a0 2, theoria_a0_spike 1};
1 433 + 2 066 + 111 = 3 610 = 95 × 38 ✓; `gaming_audit.json`
`n_demonstrated` 38, exploits with `demonstrated.succeeded == true` = 34 ✓,
`n_disagreements` 17 with `defended` in `fields_contradicted` on 14 ✓;
`redundancy.json` 32 clusters / 5 eliminated / 257 of 703 ✓;
`validation_material.json` `n_unvalidated` 21 ✓.

The arithmetic is clean. The **statistics are not** — see B2 and M8.

### Abstract (6) — A3 transfer

*Evidence.* `cold-start-a3/artifacts/bill_table.*`, `arm_l2_transfer.json`
(cost-to-first-plan `world_frames` 1, `world_actions` 0; counts
`world_actions` 10, `theorize_rounds` 0, `engine_stages` 0),
`negative_controls.json` (`all_caught: true`, `static_layer_caught_any: false`),
`arm_l2neg.json` / `arm_l2rew.json` (replay 13 anomalies, 8 of 891 pixels, Lean
green with empty axioms in both). All verified.

*Sufficient?* **No — see B3.** The 252/252 headline is reported without the
control's identical 252/252 from the same file.

### Abstract (7) — the exam

*Evidence.* `exam/artifacts/leakage.json` (363 + 58 + 1 284 + 85 = 1 790 probes,
0 hits, `label_sets_checked: []` on handover and adaptation ✓);
`exam/artifacts/calibration.json` (oracle 1.0 / null 0.0 on all four; held-out
memoriser replay 1.0 vs held-out 0.15; verdict bluffer sensitivity 1.0,
specificity 0.0; adaptation memoriser `silently_wrong` 2). All verified.

*Sufficient?* **No.** Three separate problems — **M2** (the one real result
carries a "not reportable" flag the paper drops), **M3** (two statements of fact
contradicted by a tracked artefact), **M4** (a band the paper says was not
widened, was widened).

### Abstract (8) — the live run that spent nothing

**Blocking — see B4.** No single run has the three properties the sentence
attributes to one run.

### §10.5, the one claim

Six conjuncts. Five survive with the qualifications above. The third — "that
reversibility of a mechanism mattered more than breadth of trajectory **in the
one controlled comparison run**" (`PAPER.md:2242` region) — is inconsistent with
§3.3's own demotion (M11).

---

## 2 · BLOCKING

### B1 · §4.4 and §10.3 report E-06 as open; the repository records it discharged

`PAPER.md:767` — "The manual's `goal count(Peg, alive) = 1` was **not** proved";
`PAPER.md:786` — quotes `theory-compiler/STATUS.md` calling it
"本 sprint 唯一的开放问题 (this sprint's only open problem)"; `PAPER.md:2221–2228`
repeats it in the limitations. §4.4 is explicitly framed as "the headline of the
section rather than its caveat".

It is closed in the tree:

* `cold-start-a0/THEORIZE_LOG.md:362` — `| E-06 | … | **discharged** — the
  certificate covers what it covers, exhaustion closes the rest, each goal
  attributed to its method |`, with a full entry at line 488: *"Discharged
  2026-07-28 by using the other method the compiler already had … `lean` 4.9.0
  exits 0 … `'unsolvable' does not depend on any axioms`."*
* `theory-compiler/STATUS.md:165` — `| 8 | **E-06 的证明那一半**（再追加）| 清偿`,
  and a section at line 223, `E-06 的证明那一半已清偿`.
* The sentence the paper quotes lives at `theory-compiler/STATUS.md:337`, inside
  the older `未清偿：新增台账 E-06` block at line 325 — i.e. the paper quotes the
  half of a file that the same file later supersedes.
* `git log -- cold-start-a0/THEORIZE_LOG.md` dates the discharge to commit
  `672044a`, 2026-07-28 10:24:29, "close E-06 by using the second method it
  already had".

This matters beyond a date. The paper's stated policy for exactly this situation
is written down at `PAPER.md:2229` ff. for Fast Downward: *"None of the three was
edited, as no report in this repository is; where they disagree the paper cites
all of them and says which is later."* On E-06 the paper cites only the earlier
one. The substantive point §4.4 wants — a pipeline that refuses to narrow a
theorem it cannot certify — survives, and the *method* gap genuinely stands
(exhaustion is `O(reachable set)`, and `MAX_ENUMERATED_STATES` refuses a larger
board). But "was not proved" and "the only open problem" are now false, and they
are the section's headline and the limitations section's fifth bullet.

**Required:** re-derive §4.4 and §10.3's A1 bullet against the current ledger,
state both halves and which is later, and keep the method-gap claim (which is
the durable one) rather than the proposition-unproved claim (which is not).

Two consequences ride along:

* `PAPER.md:2113` — "A0's run produced an expressivity ledger of **five** gaps
  (E-01 … E-05)" — and `PAPER.md:806` — "E-01 through E-05 … are all discharged
  in `CONTRACTS/dsl_grammar_v0.2.md`". The ledger at
  `cold-start-a0/THEORIZE_LOG.md:357–365` now runs **E-01 through E-09**, with
  E-07 discharged via a v0.2 revision item, and E-08/E-09 added and discharged on
  2026-07-28 22:41 and 2026-07-29 01:52. §10.1(d) is the paper's *disclosure*
  clause about grammar scaffolding; understating the ledger by four entries is
  the wrong place to be behind.
* `PAPER.md:314` and `PAPER.md:2483` both state that `ic3_pdr` and
  `deadlock_carver` are "not exercised by any result". The E-06 entry records
  `ic3_pdr`'s certificate as **now consumed** (`theory_compiler/ic3_certificate.py`,
  `CONTRACTS/ic3_certificate_v0.1.md`, "measured on the peg4 fixture:
  `computational` empty axiom set"). Whether that touches any result *this paper
  reports* needs an explicit check and a sentence, not silence. (**M13**)

### B2 · The battery's effect sizes do not pair by game, and the paper says they do

`PAPER.md:1340` ff.: "v2 runs the specified one, pairing `bare_cc` against
`schema_repro` **by game**, which controls for the world". `PAPER.md:1358`: "the
effect sizes are the only thing in it anyone should read."

`battery/audit/stats.py:55` —

```python
def cliffs_delta(highs, lows):
    greater = sum(1 for h in highs for l in lows if h > l)
    lesser  = sum(1 for h in highs for l in lows if h < l)
    return (greater - lesser) / (len(highs) * len(lows))
```

This is the **unpaired**, all-pairs statistic. `battery/audit/discriminate.py:190`
hands it `[highs[g] for g in shared]` and `[lows[g] for g in shared]` — four
per-game means each — so every reported δ compares Schema-on-`ar25` against
bare_cc-on-`tn36` as readily as like against like. Only the sign test at the next
line pairs. **So the column the paper tells the reader to read is precisely the
column that does not control for the world**, and the sentence asserting that it
does is two paragraphs above it.

This is not academic. It produces a visible sign inversion on the battery's own
flagship metric:

| metric | δ (unpaired) | paired sign test | paired p |
|---|---|---|---|
| P3 | −0.375, `agrees_with_declared_direction: true` | wins **1**, losses **2**, ties 1 | **1.0** |
| X2 | −0.1875, direction "no" | wins 1, losses 2, ties 1 | **1.0** |

(`battery/artifacts/discrimination_arms.json`, `metrics.P3`, `metrics.X2`.)

P3 is the metric `battery/REPORT_V2.md` singles out and the paper quotes in bold
at `PAPER.md:1371`: *"P3 is the only metric in the battery that is both in the
main table and validated on the specified gradient."* On the paired reading that
the same section says "controls for the world", **P3 went the wrong way on two of
the three non-tied games and its p-value is 1.0.** The paper reports P3's δ, its
tier, its Schema-side run count and its `direction held? yes` — and never the
1–2. A reader is left believing the battery has one validated metric; what it has
is one metric whose unpaired effect size and paired test disagree.

Second, subordinate problem: with four values per side, δ can only take multiples
of 1/16. Every reported δ in the table is k/16 — 1.0, −14/16, −10/16, −9/16,
−6/16, −3/16. Printing −0.562 and −0.188 (and truncating −0.5625 and −0.1875
rather than rounding) is the same presentational overstatement §7.4 condemns for
K2's denominator of three (`PAPER.md:1452` ff.), applied to the paper's own
headline table. The base of the statistic — 4 per-game **means**, over ~20 runs
per game on the CC side and 1–2 on the Schema side — is never stated. Note also
that the column header says "median CC / Schema" while the artefact medians are
medians *of per-game means*; "median" is doing two jobs.

**Required:** either report a paired effect size (e.g. the sign-test win/loss
tuple, which is already in the artefact) alongside every δ, or delete the
"controls for the world" clause and say plainly that the δ column is unpaired.
Report P3's 1–2 wherever P3's "validated" status is claimed.

### B3 · §6.2 reports the transfer arm's 252/252 and omits the control's identical 252/252

`PAPER.md:1159`: "Scored against the referee's copy, the **carried** manual is
right on 252 of 252 reachable (state, action) pairs of a level it never
explored".

`cold-start-a3/artifacts/score_vs_truth.json` has **three** rows:

| level | note | pairs | accuracy |
|---|---|---|---|
| a3-l1 | the manual on the level it was induced from | 248/248 | 1.0 |
| a3-l2 | **THE CARRIED MANUAL** on a level it never explored | 252/252 | 1.0 |
| a3-l2 | **the control arm's manual, induced from level 2's own sweep** | 252/252 | 1.0 |

§6.1 introduces three arms and says the three-arm design "is what makes the
comparison a measurement rather than an anecdote" (`PAPER.md:1105` region). A
measurement that quotes the treatment value and drops the numerically identical
control value from the same file is not a measurement as presented. The correct
statement is: *accuracy does not distinguish the arms at all; the entire result
is in the bill.* §6.2's bill table does carry that, and the prose around it is
good — but a reader who takes "252 of 252 … of a level it never explored" as the
transfer arm's achievement has been misled by omission, and the omission is one
row of one JSON file away.

**Required:** print all three rows, and say in the sentence that the cold start
also reaches 252/252 so accuracy is not where the transfer effect lives.

### B4 · Abstract result (8) attributes to one run the properties of two, and §9.2 says so

`PAPER.md:109–113`: "**(8)** A live run against the real API that exercised the
whole credential path — key injected in one place, **sealed pile untouched by a
check on the bytes** — for **zero billable actions**."

* The preflight (`theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json`)
  has zero billable actions (`budget.actions_ok: 0`, `ceiling_actions: 0`) and
  **no byte scan**: there is no `sealing` block; the manifest's keys are
  `arm, arm_version, base_commit, branch, budget, constraint_8, cost, files,
  game_id, ledger, outcome, prompt_id, provenance, …`.
* The byte scan lives in
  `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`
  (`sealing.game_ids_anywhere_in_the_records: ["g50t-5849a774"]`,
  `sealed_game_ids_found: []`, `sealed_pile_untouched: true`) — and **that run
  spent**: `budget.actions_ok: 7`, `commands_sent: 40`,
  `cost.cli_reported_usd: 6.317658`.

§9.2 states this correctly: "The preflight manifest predates that scan and
carries only the counters" (`PAPER.md:2010` region). So the abstract contradicts
the body. The abstract's exemption from the citation rule is "each figure in it
is cited where it recurs in the body" — here the recurrence refutes it.

**Required:** split result (8), or drop the byte-scan clause from it.

### B5 · §9.4 is titled "What was spent, in the end" and does not report what was spent

`PAPER.md:2046–2051` reports the first-contact run as "7 successful actions, 40
commands sent, 5 model calls, a score of 0.0 and 0 of 7 levels completed". The
same manifest records `cost.cli_reported_usd: 6.317658` and
`cost.delta_usd: -0.52232`, plus a recorded instrument defect:

> `cost.cache_ttl_diagnosis.verdict`: "116470 of this run's cache-creation
> tokens were 1-hour writes. `proxy/cost.py` priced them at the 5-minute
> multiplier … the table under-states this run by about $0.4368."

A section whose title promises the spend, in a paper whose abstract headline for
this section is "one live run that spent nothing", must report the $6.32 and the
pricing defect. The paper's §10.1(a) says "This paper reports no cost comparison
between arms" — fine; that is not the same as declining to report a figure the
artefact carries under a heading that asks for it. I would call this blocking
because the omission runs in the flattering direction on the one section about
money.

Related and unreported (**M5**): that same preflight manifest declares itself
irreproducible.

> `provenance.arm_version_lookup`: `"verdict": "no_match"`, `"detail": "no commit
> reachable from any ref carries this arm_version, so the run executed against a
> working tree that was never committed in that state. **The run is therefore not
> reproducible from git alone.**"`

The first-contact run, by contrast, records `"verdict": "matched"`. §9 lists four
things the run does not establish (`PAPER.md:2000` ff.); this belongs as a fifth,
and it is the one that bites hardest on a section whose closing sentence is "the
live chain runs end to end".

---

## 3 · MAJOR

**M1 · "Those logs … were written before the scores existed" is false as stated,
and git — which the paper declines to appeal to — is what shows it.**
`PAPER.md:322`. `cold-start-a0/artifacts/score_vs_truth.json` has exactly one
commit, `38500b3`, 2026-07-28 01:03:04. `cold-start-a0/THEORIZE_LOG.md` has six
commits *after* it: `406d69f` 09:20, `85da550` 09:33, `672044a` 10:24, `3f3f396`
10:41, `76e7560` 22:41, `4dd8e0f` 2026-07-29 01:52.

I diffed all six. They are confined to the §E expressivity ledger (E-06 … E-09);
the adjudication entries R-01…R-05, L-02, O-01 are untouched. **So the load-bearing
claim survives and the blanket sentence does not.** Fix the sentence to name the
adjudication entries.

But the more interesting result is what happens when a referee takes up the
invitation §1.1 declines. `PAPER.md:59` says "the only thing that could make it
auditable is git history, which this paper does not appeal to." I appealed to it:

* **A0's seal gains nothing from it.** `848d683` ("M3 — theorize, by hand, with
  the reasoning kept") is 2026-07-28 01:02:02 and `38500b3` ("M6 — the score") is
  01:03:04 — **62 seconds apart**, one batch at the end of a session. The history
  is consistent with the seal and corroborates nothing.
* **The battery's pre-registration does check out.** `19eafb2` 14:20:35
  "pre-register the CC vs Schema contrast, before reading the recon" precedes
  `82a6925` 14:29:44 "battery v2: the Schema arm…" by nine minutes, and
  `58e5f6b` 14:53:37 "pre-register four defences before writing any of them"
  precedes `5f85971` 15:07:36 "battery v2.1: four defences". That is real,
  external, cheap corroboration of the paper's most-leaned-on discipline, and
  the paper does not cite it.

The asymmetry is the finding: the corroboration exists and is free where the
paper's claim is strongest, and is unavailable where the claim is weakest. Say
that, rather than declining git wholesale.

**M2 · The exam's one real result carries a flag the paper drops.**
`PAPER.md:1781`: "Two fresh subagent readers … each scored 46.0/46.0 on the
handover paper." Both reports
(`exam/artifacts/reports/p15-handover-a0.reader-tier{1,2}.report.json`) carry:

> `axes.capability_unclaimed`: "29 answers were submitted by an examinee that
> declares no 'handover_bundle' capability. The mark stands on the answers, but
> **the examinee cannot be reported as a handover arm** until it says what it
> handed over."

The instrument says its own result may not be reported as a handover result, and
the paper reports it as one. §8.2 and §8.4 already do the honest work on
saturation and on `tier2_minus_tier1: null` — this belongs beside them.

**M3 · Two statements of fact in §8 are contradicted by a tracked artefact.**
`PAPER.md:1784`: "Held-out, adaptation and verdict have never been answered by
anything but the four fakes; **no answers or reports exist for them in the
tree**." `PAPER.md:1867`: "**no cheater response or transcript is archived**."

`exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` exists, is
tracked (`git ls-files` lists it; `git check-ignore` returns 1), and holds all 17
of the verdict cheater's claims plus a per-item `meta.exploit_per_item` giving
the exploit used on each. "No reports" is true; "no answers" and "no transcript
archived" are false, and the second is the sentence the paper uses to downgrade
the cheater's numbers to prose.

**M4 · "Replaced rather than widened" — the band was also widened.**
`PAPER.md:1776`. `exam/DECISIONS.md:153–157`, whose own heading the paper is
following: *"The band `("heldout","bluffer") = [0, 0.35]` … The band is now
`[0, 0.50]` and the work is done by two new checks."* `calibration.json` confirms
the live band is `in [0, 0.5]` with the bluffer at 0.45. Both things happened; the
paper reports only the flattering one, and then contradicts itself at
`PAPER.md:1858` ff. ("One band has already been changed once — recorded, and
correctly"). Say "widened *and* supplemented by two mix-invariant checks", which
is what D-EX-010 actually records and is still to the project's credit.

**M6 · "A0" denotes two different worlds and §8 uses it unqualified.**
`PAPER.md:1744` quotes the held-out rubric: "on a **7x7 A0 board** a typical
transition changes two cells". Everywhere in §1 and §3 "A0" is `cold-start-a0`'s
**9×9** cart/button/door/portal world (81 pixels per frame — 276 × 81 = 22 356,
111 × 81 = 8 991, 184 × 81 = 14 904, 11 × 81 = 891, all consistent). The exam's
`p15-heldout-a0` is over a **box-pushing** world with answer labels
`push / blocked_crossing / blocked_landing / blocked_wall`
(`exam/artifacts/leakage.json`) — i.e. `a0-spike`'s world, the one §3.5 goes out
of its way to say is "a *separate* A0 cold start, on a different world … not
comparable" (`PAPER.md:1090` region). §8.5 finally names `a0-spike` at
`PAPER.md:1874` region, four subsections late. Qualify every "A0" in §8, or
rename the exam's papers in the prose.

**M7 · K7 is in the main table and retired as redundant, and the paper says both
without reconciling them.** `PAPER.md:1375` lists the nine main-table metrics
including K7 (`gaming_audit.json`, `main` ✓). §7.9 lists the five retirements
including "K14 and K7 into K5" (`redundancy.json`: `representatives` omits E7,
K7, K8, K14, X4 ✓). A metric simultaneously in the main table and retired into
another metric's representative is either a defect in the two processes'
interaction or a distinction the paper needs to draw explicitly. As written the
reader meets K7 twice in incompatible roles ten paragraphs apart.

**M8 · The p-values that sit *at* the floor carry no information, and the prose
around E2 does not fully respect that.** §7.5 states the floor correctly
(2·2⁻⁴ = 0.125; 2·2⁻³ = 0.25) and the artefact emits `min_attainable_p` on every
ranked metric — good, and better than most papers do. But at
`PAPER.md:1600` region §7.8 reports E2 as "δ = +1.000 in the declared direction,
4 wins of 4 paired games, **sign-test p = 0.125 against a floor of 0.125**". A
p-value equal to the floor is not a weak result; it is the *only* value a
perfectly separating metric can return under this design, and it is therefore
zero bits about E2. The same is true of P1 and E4 in §7.2's table (both
`p_value: 0.125` at floor 0.125, one 4–0 and one 0–4). §7.8 then spends a
paragraph on what the confound would mean "if capability alone produces
front-loading", correctly declining to draw the conclusion — but a reader who has
just been shown a p-value will read the paragraph as hedged evidence rather than
as no evidence. Recommend: state once that on this design a reported p is either
the floor (maximal separation) or 1.0 (anything else), and drop the p-values from
the tables entirely. Combined with B2 this leaves the win/loss tuple as the only
honest summary, which is fine — it is already in the artefact.

**M9 · §8.3 picks one of two conflicting source statements about the held-out
leak.** `PAPER.md:1824`: "the held-out paper's world description published the
dynamics in prose, taking a reader from **47.5 % to essentially full marks**"
(matching `exam/DECISIONS.md:220`). `exam/README.md:225–230` records the second
pass differently:

> the held-out cheater was *most* confident — 0.97 — on six claims that were
> **all wrong**, because the leak it found handed it a prior … that is false of
> A0 … **A confirmed leak can have negative yield.** An unverified cheater is
> just another confident agent.

Two passes, two outcomes, one of them the more interesting methodological
finding. The paper reports the one that makes the leak look bigger and the
instrument look better at catching it. Under the draft's own precedence rule
("where they disagree the paper cites all of them"), both belong.

**M10 · §3.3's coverage row and accuracy row are the same 233/236, rendered two
ways, and the coverage figure's artefact is never cited.** `PAPER.md:510`:
`| state-action coverage | 233/236 = **99 %** | 107/228 = **47 %** |` and two rows
later `| accuracy vs ground truth | 233/236 = **98.73 %** | 228/228 = 100 % |`.

`OPEN_ITEMS.md:102` already flags the double rendering and it is still open. I
raise it again because it is worse than typography. The identity of the two
fractions **is the paper's central finding** — the manual is wrong on exactly the
pairs the trace never covered — and presenting them as two independent table rows
with different roundings hides the very thing being claimed. Separately, the
accuracy figure is cited to `score_vs_truth.json`; the *coverage* figure is
cited only to `A0P_REPORT.md` §1, when the artefact exists and is decisive:
`cold-start-a0/artifacts/trace_summary.json`, `covered_pairs: 233`, with
`uncovered_pairs` listing exactly `cart=(2,2) pressed=0 act=DOWN`,
`cart=(3,1) pressed=0 act=RIGHT`, `cart=(4,2) pressed=0 act=UP` — the same three
in `score_vs_truth.json`'s `held_out.examples`. That file is the strongest
evidence in §3 and the paper does not cite it. This is the binding rule failing
on the paper's best number.

**M11 · "Controlled comparison" is used after the paper has demoted it.** §3.3
concludes that A0/A0′ "**demonstrates the mechanism rather than tests it**" and
that "the outcome follows from the construction; nothing was learned that was not
built in" (`PAPER.md:146–160`). That demotion is correct. But `PAPER.md:230–233`
(§1.3 item 1) still advertises "a **controlled** A0/A0′ contrast", and
`PAPER.md:2242` region (§10.5, the one claim) still says "in the one **controlled
comparison** run". A demonstration by construction is not a controlled
comparison, and §10.5 is the sentence a reader will quote. Align the wording, or
say "the one constructed contrast".

**M12 · A3's "blind" control is contaminated and self-reported, and §6.4's
headline number depends on a canonicalisation the same party wrote.** §6.6
discloses A3-I1 honestly (`PAPER.md:1256` region). Two residues. First, the
striking figure — "agree on **0 %** of clauses as written, and on **all 20** once
canonicalised" (`PAPER.md:1224` region) — is a statement about a canonicalisation
map, and `domain_agreement.json`'s `canonical_agreed_rules` shows what it does
(`act=push(Cart,down)` → `act=push(MOVER,down)`, `exit_a` → `LM@3`, `Switch` →
`TOGGLE`, `Door` → `BARRIER`). Whoever chose that renaming chose the answer; the
0 %/100 % spread is a property of the map, not a measurement of two independent
authors converging. The paper's reading — "how much of a manual is convention
rather than content" — is the right reading, but the sentence should say the map
is ours. Second, "which its author flagged as his most extrapolated clause
**before being asked**" is an unfalsifiable self-report presented as a control.

**M13 · `ic3_pdr`'s exercise status needs re-checking.** See B1's second
consequence. `PAPER.md:314`, `PAPER.md:2483`.

---

## 4 · Pre-registration — what does it actually buy?

The paper leans on directional pre-registration in six places: abstract (1) and
(5), §1.3 item 4, §7.3, §7.8 ("pre-registered primary endpoint"), §8.2
("pre-registered bands"). What it buys, honestly assessed:

**It buys a real thing in one place.** `battery/PREDICTIONS.md`'s v2 seal is
strong on its own terms — the predictions were written before the recon reports
were read, so the *set of rows* was fixed before their computability was known,
which is what makes it impossible to quietly drop the rows that would look bad.
The seal declares two leaks it could not prevent (directory names encoding
upstream scores; file counts). And, uniquely in this paper, **git corroborates
it** (M1). I would put the commit hashes in §7.3.

**It buys much less than the paper's rhetoric implies, and the paper's admission
is present but under-weighted.** The admission is at `PAPER.md:1445` region:

> the author built the metric definitions, and a definition can be tuned toward
> a hoped-for result without ever seeing data. Processes 1 and 4 exist to catch
> that, and neither substitutes for a second pair of eyes.

and again at §10.4. That is the right sentence. It is **not proportionate** for
three reasons the paper does not draw out:

1. *Direction is one bit.* A pre-registered direction on a metric whose
   definition you also wrote constrains almost nothing: you can choose the
   definition so the direction is nearly certain, and the seal cannot see that.
   The v2 scoreboard is 7 hits / 11 misses strictly (`PAPER.md:1400` region,
   `battery/REPORT_V2.md:121`) — a miss rate above chance-on-a-coin, which the
   paper rightly does not flatter, but which also tells you the predictions were
   not gamed. That is the best available evidence *against* the concern and the
   paper does not use it. Use it.
2. *Processes 1 and 4 do not check the definitions; they are also the author's.*
   §7.7's "34 of 38 exploits still land" is an author scoring the author. The
   four exploits that **fail** (E2, K12, M3, P4 —
   `gaming_audit.json`, `demonstrated.succeeded == false`) are evidence that the
   author did not think of an attack, not evidence that the metric is safe. The
   paper reads `n_disagreements: 17` as harsh self-criticism, which it is; it is
   equally consistent with an exploit suite scoped to the register it was
   scoring. Neither reading can be excluded from inside.
3. *Five metrics are declared post-dictions and the count is quietly asymmetric.*
   §10.4 lists K1, K2, K7, K8 (v0 seal) and K14 (v1 table) as `[seen]`
   (`PAPER.md:2296` region), matching `PREDICTIONS.md:30`. Good. But K7 and K8 are
   also two of the five metrics **retired by de-redundancy** in §7.9, and K2 is
   the metric whose defence failed in §7.4. The overlap between "post-diction",
   "retired" and "defence failed" is three of five, and nobody says so.

**A0's pre-registration is a different and weaker object,** and the paper is more
careful here than anywhere else: §1.1's insistence that R-05 named three
*directions* and not three coordinate pairs, and its refusal to inherit the M6
gloss, is exemplary (`PAPER.md:42–51`). Keep it. Add M1's finding — that the
git record, when consulted, places M3 and M6 62 seconds apart and corroborates
nothing.

---

## 5 · The self-built-world problem

**What can be concluded.** That the pipeline runs end to end; that the failure
mode can be produced on demand; that the instrument returns the same verdict for
a true and a false theorem; that the loop closes on a produced failure. All four
are existence claims about an artefact, and self-built worlds are adequate
evidence for existence claims. The paper says exactly this at `PAPER.md:120–124`
("The contribution is an instrument and a demonstration artefact … not a result
about world models"), and that framing is correct and should not be softened.

**What cannot.** Anything about frequency, difficulty, generality, or the
behaviour of the framework on a world it did not author. In particular: how often
replay-invisible holes occur; whether the probe designer finds holes it was not
told about; whether the DSL is expressive enough for a world the DSL's author did
not build; whether an LLM would write these manuals at all.

**Does the paper stay inside the line?** Mostly yes, and with more discipline
than I expected. §11.3's closing paragraph is the single best sentence in the
draft — "§5's procedure is … analytically guaranteed by the construction. …
**It is not evidence about anything**, and the abstract should not read as though
it were." Three places cross the line anyway:

* §3.3's "controlled comparison" survives into §1.3 and §10.5 (**M11**).
* §6.2's 252/252 reads as a transfer achievement when the control matches it
  (**B3**).
* §6.3's negative controls are presented as testing the safety valve. They test
  it against **two perturbations the same author chose**, both of which edit the
  transition function and neither of which edits the board — which is exactly the
  distinction the result turns on ("The free half of the valve saw nothing. The
  static check reads the board, and neither control touches the board",
  `PAPER.md:1204` region). The conclusion is analytically entailed by the choice
  of perturbation in the same way §3.3's is by the choice of mechanism, and
  unlike §3.3 the paper does not say so. §6.5's six-item list is otherwise
  excellent; add a seventh.

**§3.3 specifically — is it a controlled comparison?** No, and the paper already
says no, twice, in the section itself. Two variables move by design (mechanism,
explorer budget) and the paper adds four more it found (`PAPER.md:96–101`: 7 vs 21
rules, 59 vs 57 states, 236 vs 228 pairs, Button vs Switch). Then the analytic
entailment argument removes the comparison's status entirely: A0′'s toggle was
designed so every direction-by-polarity combination has a witness
(`cold-start-a0/prime/THEORIZE_LOG.md` R-03, sixteen clauses at coverage 1/1), and
the adjudication rule then mechanically admits what it mechanically rejected. The
outcome is a theorem about the adjudication rule, not a finding about worlds.
The paper's own verdict — "demonstrates the mechanism rather than tests it" — is
right; it just needs to propagate.

---

## 6 · Anything measured against itself

A list, since the paper does not have one and would be stronger with it:

| # | component | validated by | shares |
|---|---|---|---|
| 1 | battery metric definitions | processes 1 & 4 | same author (§7.3, §10.4 — disclosed) |
| 2 | anti-gaming register | `battery/audit/exploits/` | same author; a failing exploit is not evidence of safety (**not disclosed**) |
| 3 | pre-registration seal | its own declaration | same author; git available and unused (**M1**) |
| 4 | exam marker | four synthetic subjects | same author; oracle and null both derive from `Item.truth`, so oracle = 1.000 tests key/marker agreement, not marking correctness. §8.4's own sentence — "a marking bug produces a plausible number, and a plausible number is indistinguishable from a result" — applies to the calibration too, and is not applied to it |
| 5 | exam leak checker | the cheater subagent | same project; §8.3 discloses that the static checks did nothing and that the cheater found both leaks — good — but the cheater is also ours |
| 6 | A1 empty axiom list | negative control | same project, disclosed (`PAPER.md:785`) |
| 7 | A2 repaired manual | `test_the_repair_agrees_with_the_control_on_that_rule` | control manual in the same directory; §5.7 argues passing is a result. Weakened by P-03: if the frontier is unresolved, agreement with the control on the `when` clause is agreement on the one branch both adjudications took, and the artefact says the manual is not uniquely determined |
| 8 | A3 blind arm | its own disclosure of contamination | **M12** |
| 9 | A0 seal | script-written `seal` field | disclosed (`PAPER.md:59`) |
| 10 | A0 world + adjudication | same instance | disclosed twice (§1.1, §10.3) |

Rows 2 and 4 are the two that are not disclosed and should be. Row 4 is the more
serious: the exam's headline self-criticism is that a marker cannot be checked by
reading it, and the only thing that checks this marker is four subjects the same
author wrote against a key the same author wrote.

One structure worth naming that is *not* a circularity, and the paper undersells
it: `exam/README.md:131–134` records that with the cheater on the confusion
matrix, **`oracle` and `cheater-v4` are identical in every cell — 1.000 and 1.000
throughout, full coverage — differing only in the score.** "A reader handed the
sheet and nothing else is indistinguishable from ground truth on the pair." That
is a far sharper statement of the verdict leak than §8.3's "17 of 17 claims with
no board reasoning", and it is the paper's best single piece of evidence that its
leak instrumentation works. Put it in.

---

## 7 · MINOR

1. `PAPER.md:13` — draft status says "~23 200 words"; `wc -w PAPER.md` = **23 667**.
2. `PAPER.md:1296` — "95 runs across 5 arms and **4 development-pile games**".
   Seven of the 95 (`theoria_a0` ×2, `theoria_a0_spike` ×1, `theoria_a2` ×4) have
   `game_id: null`; `discrimination_arms.json` correctly uses `control_runs: 88`.
   The base of "95" and the base of "4 games" are different sets.
3. `PAPER.md:1560–1561` — "The main table … returned to 9 after **four** defences
   were implemented", then the reconciliation "6 + **3** = 9". Both are true
   (K2's defence failed) but the sentence as written does not say so; it reads as
   an arithmetic slip.
4. `PAPER.md:1238` — "**Three** level constants were supplied … the goal cell and
   the two portal exits". `provenance_l2_transfer.json` records `supplied_fields:
   3` = `goal_cell`, `landmarks`, `name`; `landmarks` is one field holding two
   exits. The paper's three items and the artefact's three fields are different
   partitions of the same thing. Say "three fields — the goal cell, the landmark
   pair, and the level name".
5. `cold-start-a2/artifacts/exhibit_report.json` records `plan.backend: null`,
   while `PAPER.md:2237` region asserts every planning number came from the BFS
   stub, citing `A2_REPORT.md` §8. The artefact does not carry the backend for
   A2's UNSAT.
6. `PAPER.md:1822` — "17 of 17 claims with **no board reasoning at all**". The
   archived cheater's own `meta.exploit_per_item` records `vq-1881c8c383`:
   "none — self-declared coin flip" and `vq-17af763cab`: "X3/world reasoning
   (self-declared contaminated)". Fifteen of seventeen, or reword.
7. `PAPER.md:1346` table — X3 printed −0.562 against `-0.5625`, X2 −0.188
   against `-0.1875`. Truncated, not rounded. (The artefact's own warning string
   also says 0.562, so this is inherited — but see B2 on why three decimals are
   unearned here at all.)
8. §7.2's "Schema-side runs: 4 of 8" for P1/P2/E4 is a good catch and correctly
   the paper's own addition. Worth one further sentence: for those three metrics
   the per-game "mean" collapses to a **single run** per game, so the
   corresponding `medians` are medians of four single observations.
9. `PAPER.md:1499` quotes the floor block as "Unchanged from v0 through v2".
   `min_attainable_p` is emitted per metric in v2 and the wording could be read
   as saying the *reporting* is unchanged; it is the *bound* that is unchanged.

---

## 8 · What I would need to change my verdict

In descending order of value per unit of work:

1. **Re-derive §4.4 and §10.3's A1 bullet against the current E-ledger** (B1).
   No new experiment; one careful read of `THEORIZE_LOG.md` §E and
   `theory-compiler/STATUS.md`.
2. **State the δ column's base and pairing, and report P3's 1–2** (B2). No new
   computation; the numbers are already in `discrimination_arms.json`.
3. **Print all three rows of `cold-start-a3/artifacts/score_vs_truth.json`** (B3).
4. **Split abstract result (8); add the $6.32 and the `no_match` provenance to
   §9** (B4, B5, M5).
5. **Carry `capability_unclaimed` into §8.2; correct §8.2's and §8.4's
   statements about archived cheater material; correct "replaced rather than
   widened"** (M2, M3, M4).
6. **Cite `trace_summary.json` for A0's coverage and say that the two 233/236s
   are the same numbers** (M10).
7. **Cite the pre-registration commit hashes in §7.3, and say that the same
   check does not corroborate A0's seal** (M1, §4). This would make the paper's
   pre-registration discipline the strongest thing in it rather than the most
   assertible.

Items 1–3 are, in my judgement, disqualifying as the draft stands: a headline
open problem that is closed, a headline statistic that does not measure what its
sentence claims, and a controlled comparison missing its control value. None of
the three requires an experiment. All three are the paper's own artefacts
disagreeing with the paper's own prose, which is precisely the failure the
binding rule exists to prevent — and which, to the draft's credit, the binding
rule is what let me find.
