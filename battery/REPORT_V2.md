# Battery v2 — the specified gradient, run at last, and what it cost

**95 runs, 5 arms, 38 metrics, 1433 computed values.** v1 read 31 runs from 4
arms and 417 values. Artefacts in [`artifacts/`](artifacts/), regenerable with
`python -m battery.run_battery`, byte-identical across two consecutive
recomputes (all seven artefacts, verified this round).

Zero API calls, zero model calls, zero network, zero game spend, zero
sealed-pile reads. Still a passive instrument.

> **A note on the name.** The prompt for this round asked for `REPORT_V1`. That
> file already existed and is committed; this is the next report, not a
> rewrite of it. `REPORT_V0.md` and `REPORT_V1.md` are left standing exactly as
> written, including where v1 was wrong — which, as it turns out, is the first
> finding below.

---

## The headline: v1's number-one gap was already closed when v1 declared it

`REPORT_V1.md` opens with *the Schema arm does not exist* and lists the missing
CC vs Schema gradient as gap one of six. That was false when it was written.

`baseline-arms/SCHEMA_PATH_A.md` landed the upstream Schema-harness
trajectories for all four development-pile games at commit `63ef0bf`,
**2026-07-28T02:53Z**. Battery v1 was committed at `e82558b`, **09:04Z** — six
hours later, in the same tree, on the same day.

The conflation is worth stating precisely, because both halves are real and
only one of them was ever a gap:

| question | status then | status now |
|---|---|---|
| can we **run** Schema and produce our own reproduction score? | no | **still no** — the harness was never released |
| do we have Schema-side **trajectories** on the development pile? | **yes, since 02:53Z** | yes |

v1 read "no Schema arm" off `SCHEMA_LOCATE.md`, which is a document about the
*harness*, and never revisited it. Process 1 does not need a reproduction
score: it asks whether a metric separates two arms, and for that an upstream
ledger is sufficient material. `SCHEMA_PATH_A.md` §6 draws exactly this line
and says of the second row: *Phase 2 指标电池要的 Schema 侧材料 ✅ 本轮解决*.

`⟨复现值⟩` in `Theoria.md:271` stays empty. Nothing here fills it (D-B-019).

**The Schema arm, as ingested:** 8 runs — 4 development-pile games × 2 upstream
collections — with a median of **450 environment steps** against `bare_cc`'s
median of **27**.

---

## Process 1, on the gradient the design actually names

`discriminate_arms()` pairs `bare_cc` against `schema_repro` **by game**, which
controls for the world. That is the thing v1's arm contrast could not do, and
the reason that contrast was filed separately and licensed nothing.

**10 of 38 metrics pair on ≥2 games. Eight of those are rankable.**

| id | family | δ (CC→Schema) | medians CC / Schema | direction held? | tier | 预注册 | 验证材料 |
|---|---|---|---|---|---|---|---|
| P1 | planning | +1.000 | 0.794 / 1.015 | **yes** | reference | agrees | 82 runs · S1, m4-pilot, envelope, unlabelled, claude_fable_opus |
| P2 | planning | +1.000 | −0.155 / 0.0082 | **yes** | reference | no-effect | 74 runs · S1, m4-pilot, envelope, unlabelled, claude_fable_opus |
| E4 | economy | −0.875 | 0.249 / 0.0536 | **yes** | reference | wrong-direction | 74 runs · S1, m4-pilot, envelope, unlabelled, claude_fable_opus |
| X1 | exploration | −0.625 | 0.278 / 0.0846 | **yes** | reference | wrong-direction | 81 runs · S1, m4-pilot, envelope, unlabelled, both upstream |
| X4 | exploration | −0.625 | 0.0931 / 0.0109 | **yes** | reference | no-effect | 81 runs · S1, m4-pilot, envelope, unlabelled, both upstream |
| **X3** | exploration | **−0.562** | 0.0150 / **−0.0074** | **NO** | reference | agrees | 73 runs · S1, m4-pilot, envelope, unlabelled, both upstream |
| P3 | planning | −0.375 | 0.130 / 0.0009 | **yes** | **main** | wrong-direction | 79 runs · S1, m4-pilot, envelope, unlabelled, both upstream |
| X2 | exploration | −0.188 | 0.975 / 0.941 | **NO** (weak) | reference | wrong-direction | 81 runs · S1, m4-pilot, envelope, unlabelled, both upstream |
| P5 | planning | — | — | diagnostic | reference | not-ranked | 88 runs · all six |
| X5 | exploration | — | — | diagnostic | reference | not-ranked | 88 runs · all six |

The 验证材料 column is **generated from the recompute**, not asserted, in both
this table and [`METRICS.md`](METRICS.md) — so it cannot drift from what
actually happened. Every verdict reads `underpowered`: four paired games cannot
reach p<0.05 however cleanly a metric separates, and that is unchanged since
v0. **The effect sizes are the only thing here anyone should read.**

### The one sentence that describes the battery's real state

> **P3 is the only metric in the battery that is both in the main table and
> validated on the specified gradient.**

Main table after this round: E3, K11, K7, M3, M6, P3. Of those, five have no
process-1 verdict at all. Of the eight metrics that finally have a real
cross-arm effect size, seven were demoted to `reference` by process 4 in the
same recompute. The battery's validated metrics and its main-table metrics are
very nearly disjoint sets, and nobody had a way to see that before this round
because neither pass had ever run on real material.

### X3 is falsified, and it was the family's signature

X3 — novelty front-loading — is the exploration family's declared signature and
the one metric v1 reported as *separating as declared*. On the real gradient it
separates **backwards**, at |δ| = 0.562, and the audit raises its
wrong-direction warning automatically.

The Schema arm's front-load index is **negative**: novelty is *higher* in the
last quarter than the first. That is not noise, it is what a capable agent
looks like — one that keeps clearing levels finds new states late, while an arm
that dies on step three saw everything it will ever see in its first quarter.
The design's story ("once the manual closes there is nothing left to be
surprised by") predicts the opposite curve, and the strongest control arm
available produces the wrong sign.

X2 also fails its declared direction, weakly and for the same reason.

---

## The pre-registration scoreboard, scored honestly

`PREDICTIONS.md`'s v2 section was written to disk **in full before either
reconnaissance report was read** — the fix `REPORT_V1.md` made item 1 on the v2
list. Both surveys were commissioned under a written prohibition on values, and
the seal declares the two leaks that got through anyway (upstream scores are
encoded in four directory names; `SCHEMA_PATH_A.md` gives file and byte counts).
At writing time the author did not know which metrics the material could even be
computed on.

**Strict score: 7 hits, 11 misses out of 18.** Honouring the registered
conditional — the economy block said in advance that if upstream logged no
usage the whole family resolves to `no-data`, "a finding, not a failure of the
prediction" — it is **11 of 18**. Both numbers are reported because picking the
flattering one is the exact failure this file exists to prevent.

**What was right, and it is the structural half:**

* **The prediction the batch was really for held exactly.** v1 blamed its 21
  unvalidated metrics on the missing Schema arm. v2 predicted that diagnosis was
  wrong, because the material that arrived is *trajectories, not a model*. After
  adding a whole second control arm, **the unvalidated count is still 21 —
  unchanged, metric for metric**: the entire epistemic family, the entire
  mechanism family, and P4. No baseline can fix this. The missing ingredient is
  a *theory-bearing control arm*, which is not constructible from a baseline.
* P4, M1–M6 and K1–K14 stayed `not-applicable` on both control arms, as
  registered.
* The economy family collapsed to `no-data`, as the conditional registered: the
  corpus contains **no cost field under any spelling**, and the Codex-side
  collection carries no token counts at all.

**What was wrong, and it was wrong systematically.** Five behavioural
predictions missed — X1, X3, X4, P2, P3 — and every one missed in the *same*
direction. The author reasoned that the length-and-failure confound would make
the long-running Schema arm look *worse* on exploration and planning metrics.
It made it look **better** on every one. `bare_cc` runs are dominated by API
refusals and early death; the Schema arm walks large state spaces without
circling. The confound is real, and it points the opposite way from the
pre-registered reasoning.

---

## Process 3 — de-redundancy, with a defect fixed

`Theoria.md` process 3 is *相关性聚类，一族留代表* — cluster by correlation,
keep a representative **per family**. Through v1 the code kept one per
*cluster*, and on v2's richer material that became a live defect: K6
(epistemic) correlates with X1 and X4 (exploration) at |ρ| ≥ 0.9 over five
shared runs, and the old rule elected X1 and quietly retired the only
epistemic metric in the group. An exploration metric cannot stand in for an
epistemic one.

Cross-family clusters are now flagged rather than trusted, each family keeps
its own representative, and every retirement carries its ρ, its shared-run
count and its reason into [`audit/REDUNDANCY.md`](audit/REDUNDANCY.md).

**5 metrics retired into representatives, 33 remain:**

| retired | family | represented by | ρ | shared runs |
|---|---|---|---|---|
| E7 | economy | E4 | +0.985 | 70 |
| X4 | exploration | X1 | +0.903 | 87 |
| K14 | epistemic | K5 | −1.000 | 5 |
| K7 | epistemic | K5 | +1.000 | 5 |
| K8 | epistemic | K10 | −0.968 | 5 |

Retired is **not deleted** — all five are still computed, reported and
correlated, and excluded only from being counted as separate findings.

One result deserves emphasis because it looks like a bug and is not:
**257 of 703 metric pairs share enough runs to correlate — the identical count
as v1, after tripling the run count.** Adding 64 runs made no new pair of
metrics comparable. The un-comparability is structural, not a sample-size
problem: no run in the repository has both books and model calls.

The three K-family clusters rest on 5 shared runs across near-identical
manuals. ρ = ±1.000 over five points is not evidence, and the artefact says so
on each.

---

## Process 4 — the register became executable, and the main table fell 19 → 6

The gaming register was **prose**: one sentence per metric on how to cheat it,
plus two hand-set booleans that `tier_of()` ran a mechanical rule over. The
suite only ever checked that an entry *existed*, never that it was *true*. A
wrong `defended: True` therefore kept a gameable metric in the main table and
nothing in 117 tests noticed.

`battery/audit/exploits/` replaces the claim with a demonstration: for each of
the 38 metrics, an actual `Run` scoring at or near the metric's best value
while possessing none of the capability it claims to measure, with `succeeded`
read from `evaluate()` rather than asserted. Three independent adversarial
audits produced them. **38 exploits, 37 land. 17 register entries contradicted.
13 metrics demoted by demonstration.**

The four that matter most, each contradicting a `defended: True`:

* **P4 is monotone in failure.** It is `ok_steps / optimal`, direction `lower`,
  and **1.0 is not a floor**: one action against a 12-step plan scores 0.083 —
  better than any solved run can score. Nothing checks the goal was reached,
  `intent="solve"` is set for every ledgered run whatever the outcome, and five
  real runs stopped at exactly ten cumulative failures. `Step.won` is populated
  by the adapters and **read by no metric in the battery**.
* **K2, the flagship off-trace discriminator, scores 1.000 over a held-out set
  of one pair.** `model.py` documents at length why `held_out_frame` exists to
  prevent exactly the comparison this enables — and no metric reads the field.
* **K12 reads six self-reported booleans** from a file its own producer wrote.
  Six beats declared closed with zero environment actions and no clause changed
  scores 1.000, identical to A2. `Beat.env_actions` is carried and read by
  nothing.
* **E2 — a `Theoria.md` Phase 4 *primary endpoint* — fails twice.** Its head is
  `ceil(n × 0.25)`, so a perfectly flat-cost run scores 0.333 at 9 turns and
  0.250 at 12. Run length is set by the crash, not by the arm. That
  manufactured swing is **the size of E2's entire observed range across every
  real run** (0.162–0.321). Its second registered defence — "pairs by game" —
  has never fired once: no arm in the repository carries a priced Schema-side
  call, so **zero** E2 pairs can form.

A further structural finding from the epistemic audit: **the epistemic family
cannot rank two manuals.** For any pair of manuals differing by one concept or
one clause, at least one `higher`-direction metric prefers each. Deleting
negatively-scoring concepts improves K6 and K14 while worsening K5; stating a
generalisation you cannot fully evidence improves K2 and K3 while worsening K4.
A single `omnibus_manual()` that describes nothing holds nineteen of twenty
metrics at their best reading simultaneously. That is upstream of gameability,
and it lands on the family that is *also* entirely unvalidated.

**One inconsistency is left standing rather than normalised.** The three audits
did not agree on whether a `neutral` direction is itself a defence, so some
diagnostics fell to `reference` and some did not. The artefact marks neutral
tiers advisory and explains that *direction*, not tier, is what excludes a
diagnostic from an ordering. Normalising the disagreement would have hidden
that a hand-set boolean is still doing work here.

---

## Also this round

**The S1 campaign, 56 more `bare_cc` runs.** D-B-018 excluded the ledger shards
because another session was appending to them live. That premise expired: they
are quiescent, carry terminal status, and their `run_id` set is disjoint from
`ledger.jsonl`. Their labels were also being dropped silently — S1 writes
`scenario` in `out/campaign/`, not `campaign` in `out/campaign_cells.jsonl`, so
`load_campaigns()` saw nothing and called 48 runs `unlabelled`. Same failure
mode as D-B-013, one campaign later.

**Untracked material is absent from every git worktree.** `schema_traces/` and
`out/{shards,campaign}/` are gitignored, so a recompute on a branch silently
dropped a whole arm and a whole campaign rather than failing. Both now resolve
through an environment variable, and the resolved path plus the upstream
manifest digest go into provenance — "which copy of an untracked 87 MB payload
produced this number" has to stay an answerable question.

**The ar25 degraded material is kept, deliberately.** It is a good sample for
an instrument, not bad data: a metric that cannot survive a run where the API
refused most actions is a metric that will not survive Phase 3.

**Four things the Schema adapter refuses to do**, each because the alternative
would have produced a fact-shaped guess: no turn axis is invented (upstream
anonymised ids with independent per-file counters — the intersection of
`events.jsonl` tool-call ids with session-side ids is *empty* in all eight run
directories); no cost is synthesised; `Step.failed` is not derived from `dead`
(a game state, not a refused action — conflating them would hand this arm
`bare_cc`'s API failure rate as if it were capability); and `Theory` stays
`None`, because the upstream world model exists only as Python source and
prose, and reading it is a separate decision with its own contamination
argument.

**Licence.** Upstream declares none (`SCHEMA_LOCATE.md` §2.3). The payload
stays gitignored; only aggregate statistics enter any artefact — no frame, no
action sequence, no transcript, no per-step record (D-B-020).
`SCHEMA_PATH_A.md` §7.1 flags that citing specific numbers may still need a
licence judgement. **That judgement is not this track's to make and has not
been made**; it is escalated in `PARTNER_SYNC.md`.

---

## What v2 still cannot see

| gap | why |
|---|---|
| **A theory-bearing control arm** | the real blocker, and newly quantified: adding an entire second control arm moved the unvalidated count by **zero**. 21 of 38 metrics — all of epistemic, all of mechanism, P4 — have never been checked against any known gradient, and no baseline can check them |
| **The economy family on any arm with a theory** | unchanged. A0, a0-spike and A2 make no model calls; the Schema corpus records no cost. Claim C2's signature has still never been computed where it would mean something |
| **Arm separated from harness** | the Schema side is somebody else's agent on somebody else's infrastructure. Every effect size above is a capability gradient bundled with a plumbing gradient, and P1/P5/E4 are visibly the plumbing |
| **Statistical power** | unchanged since v0. 4 paired games; 6 non-tied pairs is the floor for p<0.05. The second arm bought pairing quality, not power |
| **M3 cross-level transfer (claim C3)** | still no multi-level run, and M3 is now additionally known to have no reachable value at all |
| **Repair with a control** | unchanged and unfixable in principle: an arm with no manual cannot have a repair loop |

## What v3 needs, in order

1. **Fix or retire E2 before Phase 4.** It is a primary endpoint that a crash
   can flatter. The length effect is a one-line fix — interpolate the cost at
   the 25% mark instead of rounding up to a whole turn — and the concentration
   failure needs something genuinely new.
2. **Read the fields the model already carries.** `Step.won`, `held_out_frame`
   and `Beat.env_actions` are populated by adapters and read by no metric, and
   each is the missing defence for a metric demoted this round (P4, K2, K12).
   These are the cheapest three fixes on the list.
3. **Decide what the epistemic family ranks**, or stop claiming it ranks
   anything. It cannot currently order two manuals self-consistently.
4. **Retire X3 or redefine it.** It separates the specified gradient backwards.
5. **Six paired games.** Unchanged from v0 and v1, and still upstream of
   everything else.
