## 7 · The metrics battery, recomputed over existing trajectories

### 7.1 A passive instrument, and what it cost

`Theoria.md` Phase 2 asks for a second reader of the same ledger: 同一本账,两次
使用 — the scorer reads it for a score, the battery reads it for a capability
spectrum.

This section reports **v2**, the state the artefacts are in
(`battery/artifacts/capability_spectrum.json` self-reports `battery_version:
"v2"`): **95 runs across 5 arms and 4 development-pile games, 38 metrics over
five families, 1 433 computed values**, with a further 2 066 metric slots
`not-applicable` and 111 `insufficient-data`, recorded per run rather than
aggregated away. v0 — which earlier drafts of this section reported — was 26 runs
across 2 arms and 29 metrics; v1 was 31 runs and 417 values. All three reports are
kept unedited, including where v1 was wrong (`battery/REPORT_V0.md`,
`battery/REPORT_V1.md`, `battery/REPORT_V2.md`).

The instrument is still passive: zero API calls, zero model calls, zero network,
zero game spend, zero sealed-pile reads (`battery/REPORT_V2.md`). Artefacts
regenerate with `python -m battery.run_battery` (`battery/run_battery.py`) and were
byte-identical across two consecutive recomputes. **One** of the seven carries the
verified pile digest and the sha256 of its inputs, so a changed number traces to a
changed input (`battery/artifacts/capability_spectrum.json`,
`provenance.input_digests`); the other six carry no provenance block at all. The
digests are a property of that one file, not of the artefact set, and this paper
had the stronger claim in it until the sentence was checked.

Two caveats on that reproducibility claim, both from the battery's own decision
log. The determinism *test* runs against a synthetic fixture rather than against
the published artefacts (`battery/DECISIONS.md` D-B-008; earlier drafts cited
D-B-001, which is about the pile guardrail). And two of the five arms live in
gitignored payloads — the upstream Schema traces and the S1 campaign shards are
absent from every git worktree, so a recompute on a clean checkout silently drops
a whole arm and a whole campaign unless `THEORIA_SCHEMA_TRACES` and
`THEORIA_BASELINE_ARMS` are set (`battery/STATUS.md`).

All four Phase 2 processes — 区分力 (discriminative power), 方向预注册
(directional pre-registration), 去冗余 (de-redundancy), 抗游戏审计 (anti-gaming
audit) — have now run on real material. The rest of this section is what they
returned, and most of it is unflattering to the instrument.

### 7.2 The gradient the design specifies, run at last

`Theoria.md` Phase 2 process 1 names a particular contrast: bare Claude Code
against Schema. v0 and v1 could not run it and substituted the model ladder within
`bare_cc`, which `battery/DECISIONS.md` D-B-004 argues is the weaker comparison.
v2 runs the specified one, pairing `bare_cc` against `schema_repro` **by game** in
its sign test — though not, as §7.2a explains, in the effect sizes,
which controls for the world (`battery/artifacts/discrimination_arms.json`).

The arm is **8 runs** — 4 development-pile games × 2 upstream collections — of
released upstream trajectories. It is not a reproduction: the Schema harness was
never published, so no reproduction score exists and the `⟨复现值⟩` cell in
`Theoria.md` stays empty (`baseline-arms/SCHEMA_LOCATE.md`; `battery/DECISIONS.md`
D-B-019). Process 1 does not need one — it asks whether a metric separates two
arms, and an upstream ledger is sufficient material for that.

**Ten of 38 metrics pair on at least two games; eight are rankable.** Effect sizes
and medians below are read from `battery/artifacts/discrimination_arms.json`:

| id | family | Cliff's δ (CC → Schema) | median CC / Schema | direction held? | tier | Schema-side runs |
|---|---|---|---|---|---|---|
| P1 | planning | +1.000 | 0.794 / 1.015 | yes | reference | **4 of 8** |
| P2 | planning | +1.000 | −0.155 / 0.008 | yes | reference | **4 of 8** |
| E4 | economy | −0.875 | 0.249 / 0.054 | yes | reference | **4 of 8** |
| X1 | exploration | −0.625 | 0.278 / 0.085 | yes | reference | 8 of 8 |
| X4 | exploration | −0.625 | 0.093 / 0.011 | yes | reference | 8 of 8 |
| **X3** | exploration | **−0.562** | 0.015 / **−0.007** | **no** | reference | 8 of 8 |
| P3 | planning | −0.375 | 0.130 / 0.001 | yes | **main** | 8 of 8 |
| X2 | exploration | −0.188 | 0.975 / 0.941 | **no** | reference | 8 of 8 |

**Every verdict in that table reads `underpowered`**, for the reason §7.5 gives;
the effect sizes are the only thing in it anyone should read.

The last column is not decoration, and it is a caveat this paper adds rather than
one the source report draws out. The Schema arm is two upstream collections of
four games each, and **only one of them records model calls at all** — the
Claude-side collection carries 197–564 per run, the Codex-side carries zero
(`battery/artifacts/capability_spectrum.json`, `model_calls` per run). P1, P2 and
E4 all divide by model calls, so their Schema side rests entirely on the
Claude-side collection. Their effect sizes therefore compare bare Claude Code
against *one vendor's* upstream agent, which is a narrower comparison than the
other five rows and a confound beyond the arm-and-harness bundle already declared. One sentence
describes the battery's state better than the table does:

> **P3 is the only metric in the battery that is both in the main table and
> validated on the specified gradient.**
> — `battery/REPORT_V2.md`

### 7.2a The effect sizes are not paired, and on P3 the two statistics disagree

The sentence above is the battery's own summary and this paper carried it, but the
metric it rests on does not survive a look at how its two numbers are computed.

**Cliff's δ is an unpaired statistic.** `battery/audit/stats.py`'s `cliffs_delta`
is `P(high > low) − P(high < low)` over *all* cross-arm pairs of the four per-game
values; it never matches a game against itself. Only the sign test pairs. So
"pairing by game, which controls for the world" is true of the column the table
does not ask you to read and false of the column it does — §7.2 above tells the
reader the effect sizes "are the only thing in it anyone should read", and those
are precisely the numbers the pairing does not reach.

**On P3 the two statistics point opposite ways.** Its δ of −0.375 is recorded with
`agrees_with_declared_direction: true`, while its paired sign test over the same
four games is **1 win, 2 losses, 1 tie, p = 1.0**
(`battery/artifacts/discrimination_arms.json`, `metrics.P3`). The unpaired
comparison says the direction held; the paired one, on the same data, has the
metric losing twice as often as it wins. X2 sits in the same position. Whatever
"validated on the specified gradient" means for P3, it cannot mean that the
gradient's own paired test agreed.

A second consequence of n = 4 per side: every δ here is a multiple of 1/16, so the
table's −0.562 and −0.188 print three decimals onto a quantity with seventeen
reachable values. §7.4 calls exactly that presentational overstatement out when K2
does it over a denominator of three. It is the same error, in the table this
section asks the reader to trust most.

None of this makes the effect sizes worthless — they are the only cross-arm signal
the pilot has. It makes the sentence above an overstatement, and it means the
battery's flagship claim about P3 rests on a distinction between two of its own
statistics that neither the report nor, until now, this paper had drawn.

The main table holds nine metrics — E2, E3, K7, K11, K12, M3, M6, P3, P4
(`battery/artifacts/gaming_audit.json`, `main`). Of the eight with a real
cross-arm effect size, seven sit in the `reference` tier. Only two of those seven
were *demoted* there by the anti-gaming audit — P2 and X3, whose `register_tier`
reads `main`; the other five were registered `reference` before this round and had
no main table to fall from (`battery/artifacts/gaming_audit.json`,
`metrics[*].register_tier`). The correction does not soften the finding: the
battery's validated metrics and its main-table metrics are very nearly disjoint
sets, and since neither pass had run on real material before v2, nobody had a way
to see that.

**X3 separates the gradient backwards, and X3 was the family's signature.**
Novelty front-loading is the exploration family's declared signature and the one
metric v1 reported as separating as declared. Here the Schema arm's front-load
index is *negative* — novelty is higher in the last quarter than the first — and
the audit raises the warning automatically: "separates the gradient strongly
(|d| = 0.562) but in the opposite direction to the one declared … Do not use until
resolved" (`battery/artifacts/discrimination_arms.json`, X3 `warning`).
`battery/REPORT_V2.md` reads it as capability rather than noise: an arm that keeps
clearing levels finds new states late, while an arm that dies on step three saw
everything it will ever see in its first quarter. X2 fails its declared direction
too, weakly and for the same reason. The design's story — once the manual closes
there is nothing left to be surprised by — predicts the opposite curve, and the
strongest available control arm produces the wrong sign.

The confound is in the artefact rather than in prose: the Schema side is somebody
else's agent on somebody else's infrastructure, so every effect size above is a
capability gradient bundled with a plumbing gradient
(`battery/artifacts/discrimination_arms.json`, `confounds`). Its median run is
**450 environment steps** against `bare_cc`'s **27** (`battery/REPORT_V2.md`).

### 7.3 The pre-registration discipline, including its holes

`battery/PREDICTIONS.md` fixes a directional ordering over the arms for every
registered metric, append-only from the commit that introduced it — "a prediction
that can be edited after the fact is not a prediction". Its v2 section was written
to disk in full **before either reconnaissance report was read**, and its seal
declares the two leaks that got through the written prohibition on values anyway.

**The v2 scoreboard is 7 hits and 11 misses out of 18 read strictly, and 11 of 18
if the registered conditional is honoured** — the economy block said in advance
that if upstream logged no usage the whole family resolves to `no-data`, "a
finding, not a failure of the prediction". Both numbers are in
`battery/REPORT_V2.md`, because picking the flattering one is the failure the file
exists to prevent.

One qualification, because the artefacts and the report disagree and this paper's
precedence rule follows the artefacts. `battery/REPORT_V2.md` states flatly that
"the economy family collapsed to `no-data`". **Four** of the seven economy metrics
did — E2, E3, E5, E7. E1 and E6 return `not-ranked`, being direction-less
diagnostics that no collapse could have touched, and **E4 did not collapse at
all**: it appears in §7.2's table with a real cross-arm effect size
(`battery/artifacts/discrimination_arms.json`, `metrics.E1`–`metrics.E7`,
`verdict`).
The reason is that E4 is a curvature fit over *context tokens* rather than over
cost — its `needs` field asks for `model_calls`, not for a price — so it survives
a corpus that carries no cost field under any spelling
(`battery/artifacts/capability_spectrum.json`, card `E4`). The report's sentence
is right about the family's cost-bearing members and wrong as stated; the
conditional it invokes was registered about *usage*, and one collection logged
some.

The structural prediction held and the behavioural ones did not, and that
asymmetry is the interesting part. v1 blamed its 21 unvalidated metrics on the
missing Schema arm; v2 predicted that diagnosis was wrong, because what arrived is
trajectories rather than a model. After adding an entire second control arm the
unvalidated count is **still 21, metric for metric**
(`battery/artifacts/validation_material.json`, `n_unvalidated: 21`). Against that,
five behavioural predictions missed — X1, X3, X4, P2, P3 — and every one in the
same direction: the author reasoned that the length-and-failure confound would
make the long-running Schema arm look *worse*, and it looked better on all five.

The older structural admission still stands beside the seal: the author built the
metric definitions, and a definition can be tuned toward a hoped-for result
without ever seeing data. Processes 1 and 4 exist to catch that, and neither
substitutes for a second pair of eyes (`battery/STATUS.md`, W-1).

### 7.4 A metric can be perfect and still be measuring the wrong thing

A0's manual scores **K4 evidence coverage = 1.000** and **K2 held-out accuracy =
0.000**, on the same manual, from the same recompute — K4 over 7 annotated
clauses, K2 over **3** state-action pairs with 0 agreements
(`battery/artifacts/capability_spectrum.json`, run `a0-base`). The n = 3 is not
decoration: three decimal places over a denominator of three is a presentational
overstatement, and the abstract should carry the denominator.

The two are not in tension by accident. The manual scores perfect coverage
*because* it refused the one generalisation it lacked evidence for:
`cold-start-a0/THEORIZE_LOG.md` R-05 rejects "the Button is presumably pressable
from any of the four directions" because the evidence for three of those four is
"not thin, zero". That refusal makes every clause fully supported, and it is exactly why the
uncovered pairs are the ones the manual gets wrong.

> **Evidence coverage rewards precisely the caution that held-out accuracy
> punishes.** A battery reporting K4 alone would show a flawless manual.
> — `battery/REPORT_V0.md`

The consequence went into the code: K4 sits in the reference tier carrying the
instruction that "K4 must never be reported without K2 beside it". It was
registered there rather than demoted there: its `status` is `register confirmed by
demonstration` — the audit's majority outcome, 21 of 38 — and its `defended` field
is `false`, so what the demonstration confirmed is an admitted, undefended hole
rather than a defence that held (`battery/artifacts/gaming_audit.json`,
`metrics.K4`). The recompute also puts numbers on §1's
hook — replay accuracy 0.987 against held-out accuracy 0.000 — on the metric the
field already optimises.

v2 adds that **K2's own defence failed, in the manner its pre-registration named
in advance.** The seal registered the honest failure mode as *defence theatre*: a
change that makes a metric harder to game only in the precise way that was
demonstrated. K2 was required to declare its sampling frame; a frame is free text,
so the adversary writes one — the exploit now declares "the single pair we withheld
after checking that the manual already got it right" and scores 1.000 as before,
and K2 stays in the reference tier (`battery/REPORT_V2.md`, v2.1). The change
bought something else: `a0-base` now carries a frame, so its K2 = 0.000 over 3
adversarial gaps and a0-spike's K2 = 1.000 over 39 960 exhaustive cases finally
travel with the fact that makes them non-comparable
(`battery/artifacts/capability_spectrum.json`, K2 `support.frame`). Comparability
was bought; safety was not.

### 7.5 The pilot ledger cannot certify any metric, and says so

Unchanged from v0 through v2, and it bounds everything above:

> A two-sided sign test over 4 paired games has a smallest attainable p of
> **0.125**. No metric can reach p < 0.05 on this data however cleanly it
> separates. **Six** non-tied paired games are the minimum for the test to be
> able to clear the bar at all.
> — `battery/REPORT_V0.md`

The floor is emitted on every run — `min_attainable_p` nested under each ranked
metric's `sign_test`, plus a top-level `power` string — so nobody reads 0.125 as a
near miss (`battery/artifacts/discrimination_arms.json`). Three of §7.2's eight
rows sit at a worse floor still: P3, X2 and X3 each lose a game to a tie, which
drops them to three paired games and a `min_attainable_p` of **0.25**. The 0.125
above is the best case in that table, not the uniform one. Tripling the run count
from 31 to 95 did not move it: v2 bought pairing quality, not power. Six paired
games remains the floor, and remains a Phase 3 design input rather than something
this paper can fix.

### 7.6 Two metrics measuring something other than capability, and only one was a discovery

**E5 (cost per action) is a price list, and that was deducible.** It is cost per
action and the arms are three models at different token prices, so the conclusion
follows with no data at all. On the model ladder it separates at δ = +1.000 with
the wrong-direction warning (`battery/artifacts/discrimination.json`). It is
reported because the audit acted on it, not because a pass discovered it.

**P1 (actions per model call) is the genuine finding, and v2 changed what the
finding is.** In v0, P1 separated the model ladder at δ = −1.000 and *backwards*,
correlating with the step-failure rate at ρ = −0.83: between 27 % and 45 % of pilot
steps failed outright on HTTP 500s and "game not found", and P1 divides successful
actions by all calls, so a run whose infrastructure failed more looks like one that
planned less. That reading survives — on the ladder P1 still separates at
δ = −0.750 with the warning raised — but on the *specified* gradient it separates at
**δ = +1.000, in the declared direction**. The two passes disagree in sign, and the
artefact says in advance that this is not a defect: they "are confounded in
different directions and disagreement between them is information rather than
noise" (`battery/artifacts/discrimination.json`, `role`). The honest reading is
that P1 is sensitive to plumbing in both — API failure rate on the ladder, upstream
infrastructure quality on the arm gradient — which is why it sits in the reference
tier on both. v0's response is still in the code: **P5 `step_failure_rate`** is a
diagnostic, so the confound reaches a reader before P1 does.

ρ = −0.83 is carried by no artefact in `battery/artifacts/` — it appears only in
`battery/REPORT_V0.md` and `battery/STATUS.md` W-4 — so it is quoted as a report's
statement about v0 rather than as a v2 measurement. The v2 recompute does measure
the same pair, and more strongly on far more material: P1 against P5 at
**ρ = −0.899 over 82 shared runs** (`battery/artifacts/redundancy.json`, `matrix`).
The v0 value cannot be reproduced; the finding it stands for survived being
re-measured, which is the better of the two things that could have happened to it.

### 7.7 The anti-gaming register became executable, and the main table moved twice

Through v1 the register was **prose**: one sentence per metric on how to cheat it,
plus two hand-set booleans that a mechanical rule read. The suite only ever
checked that an entry *existed*, never that it was *true*, so a wrong
`defended: True` kept a gameable metric in the main table and nothing noticed.

`battery/audit/exploits/` replaces the claim with a demonstration: for each of the
38 metrics, an actual run scoring at or near the metric's best value while
possessing none of the capability it claims to measure, with `succeeded` read from
`evaluate()` rather than asserted. **38 exploits exist, 34 still land, and 17
register entries were contradicted by their own demonstration**
(`battery/artifacts/gaming_audit.json`: `n_demonstrated` 38, `n_disagreements` 17,
`main` 9, `reference` 29). The main table fell from 19 to 6 on demonstration and
returned to 9 after four defences were implemented. The endpoints are re-derivable
from the artefact as the metrics whose `register_tier`, and whose `tier`, read
`main`; the intermediate 6 is not, and comes from `battery/REPORT_V2.md`, which
names the six by hand and reconciles them arithmetically — 19 − 13 demoted = 6,
then 13 − 3 returned = 10, which is the artefact's `demoted_by_demonstration`, and
6 + 3 = 9. Four exploits matter most, each contradicting a `defended: True`:

* **P4 was monotone in failure** — `ok_steps / optimal`, direction `lower`, and
  1.0 was not a floor: one action against a 12-step plan scored 0.083, better than
  any solved run can score. `Step.won` was populated by the adapters and read by no
  metric. Closed by refusing to score a run that never reached the goal.
* **K2 scored 1.000 over a held-out set of one pair.** Defence attempted and
  failed, as §7.4 describes.
* **K12 read six self-reported booleans** from a file its own producer wrote. Six
  beats declared closed, with zero environment actions and no clause changed,
  scored 1.000. Closed by requiring the episode to show evidence.
* **E2 — a `Theoria.md` Phase 4 primary endpoint — failed twice.** Its head was
  `ceil(n × 0.25)`, so a flat-cost run scored 0.333 at 9 turns and 0.250 at 12, and
  run length is set by the crash rather than by the arm; that manufactured swing
  was the size of E2's entire observed range across every real run — 0.162–0.321
  when the exploit was written, 0.162–0.297 in the current artefact, the top having
  fallen when the fix landed (`battery/artifacts/capability_spectrum.json`,
  `runs[*].metrics.E2.value`). Interpolating at the 25 % mark closed it. The **concentration** attack survives
  untouched: dump the bill on turn one and score 0.993 over twenty turns.

E2's return to the main table deserves the argument `battery/REPORT_V2.md` gives it
rather than a patch. The mechanical rule demotes only for *accidental* gaming; the
length artefact was the accidental route and it is closed, and the audit judged the
concentration attack non-accidental, so the rule promoted E2 — not overridden by
hand, because hand-overriding a mechanical tier on a metric the same round had
already touched is the tuning the process exists to forbid. It should be read as a
warning rather than a clearance: a Phase 4 primary endpoint reachable at 0.993
without understanding anything is not safe merely because reaching it takes intent.

One further finding is upstream of gameability: **the epistemic family cannot rank
two manuals.** For any pair differing by one concept or one clause, at least one
`higher`-direction metric prefers each — deleting negatively-scoring concepts
improves K6 and K14 while worsening K5; stating a generalisation you cannot fully
evidence improves K2 and K3 while worsening K4. A single manual that describes
nothing holds nineteen of the twenty metrics in that audit's scope at their best
reading at once — the scope being the fourteen epistemic metrics plus the six
mechanism ones, and the twentieth, the only one the empty manual cannot reach,
being M3 (`battery/audit/exploits/mechanism_epistemic.py`, `omnibus_manual`).
That lands on the two families which are also entirely unvalidated.

### 7.8 A confound on a pre-registered primary endpoint

E2, the front-load index, is one of Phase 4's three pre-registered primary
endpoints and the signature of claim C2: understanding is bought early and spent
late (`battery/REPORT_V0.md`). Within `bare_cc`, the more capable model front-loads
more — δ = +1.000 in the declared direction, 4 wins of 4 paired games, sign-test
p = 0.125 against a floor of 0.125 (`battery/artifacts/discrimination.json`, E2
`sign_test`). No arm in that comparison has a theory. If capability alone produces
front-loading, then front-loading is not specific to *having* a theory.

This paper does not draw the conclusion. It is a four-game pilot that §7.5 has just
said can certify nothing, and it is registered as **a confound to separate before
Phase 4 freezes**, not as evidence about claim C2. Two things sharpen the
registration without resolving it. The specified gradient cannot check it at all —
E2's process-1 verdict there is `no-data`, because the Schema corpus records no cost
under any spelling, so **zero** E2 pairs can form
(`battery/artifacts/discrimination_arms.json`, E2) — and one of E2's two registered
defences, "pairs by game", has therefore never fired once. The ablation arm is the
instrument well placed to separate the confound, and it is Phase 3 work that has
not happened. Two defences did go into the code: E2 and E3 refuse runs shorter than
eight turns, since a run ending on turn four looks maximally front-loaded while
having understood nothing (`battery/artifacts/gaming_audit.json`).

### 7.9 De-redundancy, and a defect it exposed

`Theoria.md` process 3 is 相关性聚类,一族留代表 — cluster by correlation, keep a
representative **per family**. Through v1 the code kept one per *cluster*, and on
v2's richer material that became a live defect: K6 (epistemic) correlates with X1
and X4 (exploration) at |ρ| ≥ 0.9, and the old rule elected an exploration metric
and quietly retired the only epistemic metric in the group. Cross-family clusters
are now flagged rather than trusted, each family keeps its own representative, and
every retirement carries its ρ, its shared-run count and its reason into
`battery/audit/REDUNDANCY.md`.

v2 finds **32 clusters over 38 metrics and retires 5 into representatives** — E7
into E4 (70 shared runs), X4 into X1 (87), **K14 and K7 into K5** (5 each), K8 into K10
(5) — with exactly one cross-family cluster, {K6, X1, X4}
(`battery/artifacts/redundancy.json`).

**One of those five retirements is a metric this paper also lists in the main
table, and the two artefacts do not know about each other.** K7 is retired into K5
by process 3 at ρ = 1.000 over 5 shared runs, and it is simultaneously one of the
nine metrics process 4 leaves in the main table — `battery/artifacts/redundancy.json`
`eliminated` and `battery/artifacts/gaming_audit.json` `main` both say so, and §7.7
above prints K7 among the nine without noticing. Neither process is wrong on its own
terms: the anti-gaming audit asks whether a metric can be cheated and the
de-redundancy pass asks whether it says anything a representative does not, and a
metric can pass the first while failing the second. But nothing downstream
reconciles them, so **the main table as published contains a metric the battery has
already retired**, and a reader assembling "the nine metrics worth reporting" gets
one that process 3 says is K5 under another name. On five shared runs across
near-identical manuals, which is the evidence base the same subsection warns is too
thin to be evidence.

Retired is not deleted, only excluded from
being counted as a separate finding; and the two K-only clusters — {K10, K8} and
{K14, K5, K7}, three retirements between them — rest on 5 shared runs across
near-identical manuals. The artefact does not flag that cluster by cluster, which
is where this paper previously said it did: it carries one global `coverage_note`
reading that the picture "reflects thin data, not twenty independent findings",
and a `warning` on the cross-family cluster alone.

A cluster count near the metric count is not reassuring, and the artefact refuses
to let it read as thirty independent findings: **257 of 703 metric pairs share
enough runs to correlate at all — the identical count as v1, after tripling the run
count.** Adding 64 runs made no new pair comparable, because the un-comparability is
structural rather than a sample-size problem: no run in the repository has both
books and model calls.

### 7.10 What the battery still cannot see

| gap | why |
|---|---|
| **A theory-bearing control arm** | the real blocker, and v2 quantified it: adding an entire second control arm moved the unvalidated count by **zero**. 21 of 38 metrics — all of epistemic, all of mechanism, and P4 — have never been checked against any known gradient (`battery/artifacts/validation_material.json`), and no baseline can check them, because an arm with no books cannot be scored on the epistemic family |
| **The economy family on any arm with a theory** | A0, a0-spike and A2 make no model calls, and the Schema corpus records no cost. Claim C2's signature has still never been computed where it would mean something |
| **Arm separated from harness** | the Schema side is somebody else's agent on somebody else's infrastructure; P1, P5 and E4 are visibly the plumbing |
| **Statistical power** | unchanged since v0: 4 paired games, and 6 non-tied pairs is the floor for p < 0.05 |
| **M3 cross-level transfer (claim C3)** | still no multi-level run, and M3 is additionally known to have no reachable value at all |
| **P4 solution redundancy on a truthful trace** | needs ground truth *and* a solve attempt. A0 has the truth but its trace is a coverage walk; the ledger runs are solve attempts with no truth |
| **Repair with a control** | unchanged and unfixable in principle: an arm with no manual cannot have a repair loop |

**What v3 needs, in order** (`battery/REPORT_V2.md`): fix or retire E2 before
Phase 4, since a primary endpoint a crash can flatter is not a primary endpoint;
read the fields the model already carries; decide what the epistemic family ranks,
or stop claiming it ranks anything; retire or redefine X3; and get six paired
games, unchanged from v0 and still upstream of everything else.

The second of those five is already out of date, in the direction of progress, and
this paper reproduced it as current until the list was checked against the code
rather than against the report. `battery/REPORT_V2.md` names `Step.won`,
`held_out_frame` and `Beat.env_actions` as fields the adapters populate and no
metric reads; **all three are read now**, by the same v2.1 defences §7.7 describes.
`Step.won` is aggregated in `battery/model.py` and gates P4 through the capability
guard in `battery/metrics/__init__.py`, so P4 returns `not-applicable` on a run
that never won; `held_out_frame` gates K2 in `battery/metrics/epistemic.py`; and
`Beat.env_actions`, summed into `Repair.env_actions` in `battery/model.py`, is read
by K12 and K13 in the same module. The report is left
standing unedited by policy, which is right for a record and is exactly why a
reader who treats its recommendations as current will be one round behind it.

One stale string closes the section, because this paper's binding rule exists to
make such things visible. `CLAUDE.md`'s pile digest `3feca53e…41bbc19a` reads as a
file hash and is not one: it is taken over the canonical JSON minus its own
`sha256` field, while the file itself hashes to `d3140eff…` after LF
normalisation and to a third value, `f2ef44d1…`, on a Windows checkout. All three
reproduce exactly. The third is not a curiosity: `arc-recon/data/piles.json` is
stored LF in the index and has no `.gitattributes` covering it, so with
`core.autocrlf=true` every Windows working copy materialises 111 CRLF pairs and
hashes differently from the same blob on Linux — which is why a digest quoted as
"the file's hash" is a digest that depends on who checked it out. The cut is
intact and has never been modified; only the description misleads
(`battery/DECISIONS.md` D-B-011).
