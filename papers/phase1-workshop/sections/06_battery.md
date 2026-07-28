## 6 · The metrics battery, recomputed over existing trajectories

### 6.1 A passive instrument, and what it cost

`Theoria.md` Phase 2 asks for a second reader of the same ledger: 同一本账，两次
使用 — the scorer reads it for a score, the battery reads it for a capability
spectrum.

v0 was recomputed over every trajectory already in the repository: **26 runs, 4
development-pile games, 2 arms** (`battery/artifacts/capability_spectrum.json`),
at zero new game spend, zero model calls and zero network
(`battery/REPORT_V0.md`). Artefacts regenerate with `python -m battery.run_battery`
and are byte-identical on a re-run; each carries the verified pile digest and the
sha256 of both inputs, so a changed number traces to a changed input
(`battery/DECISIONS.md` D-B-001). Twenty-nine metrics over five families, split
**15 main / 14 reference** mechanically by the anti-gaming audit
(`battery/METRICS.md`). All four Phase 2 processes — 区分力 (discriminative
power), 方向预注册 (directional pre-registration), 去冗余 (de-redundancy), 抗游戏
审计 (anti-gaming audit) — ran; the rest of this section is what they returned.

### 6.2 The pre-registration discipline, including its holes

`battery/PREDICTIONS.md` fixes a directional ordering over the three arms for
every registered metric. It is append-only from the commit that introduced it —
"a prediction that can be edited after the fact is not a prediction" — and was
written before `run_battery.py` had been executed once.

Its seal declaration states what the author had **already seen**. The A0
epistemic inputs were read while building the adapter, so at writing time their
values were known:

> **K1, K2, K7 and K8 on A0 are therefore post-dictions, and are marked `[seen]`
> in the table.**
> — `battery/PREDICTIONS.md`, seal declaration

They are kept because the *arm ordering* they predict is still prospective —
nothing about `bare_cc` or `schema_repro` was visible — but marked rather than
quietly carried. A pre-registration that names its own holes is the point of
writing one.

The structural admission sits beside it: the author built the metric definitions,
and a definition can be tuned toward a hoped-for result without ever seeing data.
Processes 1 and 4 exist to catch that and neither substitutes for a second pair
of eyes; `battery/STATUS.md` records this as W-1, v0's most severe open weakness.

### 6.3 A metric can be perfect and still be measuring the wrong thing

A0's manual scores **K4 evidence coverage = 1.000** and **K2 held-out accuracy =
0.000**, on the same manual, from the same recompute
(`battery/artifacts/capability_spectrum.json`, run `a0-base`: K4 over 7 annotated
clauses, K2 over 3 pairs with 0 agreements).

They are not in tension by accident. The manual scores perfect coverage *because*
it refused the one generalisation it lacked evidence for:
`cold-start-a0/THEORIZE_LOG.md` R-05 rejects "the Button is pressable from any
direction" because the evidence for three of the four directions is "not thin,
zero". That refusal makes every clause fully supported, and it is exactly why the
three uncovered state-action pairs are the three the manual gets wrong.

> **Evidence coverage rewards precisely the caution that held-out accuracy
> punishes.** A battery reporting K4 alone would show a flawless manual.
> — `battery/REPORT_V0.md`

The consequence went into the code: the audit demotes K4 to the reference tier
with the instruction that "K4 must never be reported without K2 beside it"
(`battery/artifacts/gaming_audit.json`). The recompute also puts numbers on §1's
hook — replay accuracy 0.987 against held-out accuracy 0.000 — on the metric the
field already optimises.

### 6.4 The pilot ledger cannot certify any metric, and says so

Every discriminative verdict came back `underpowered` or `no-data`
(`battery/artifacts/discrimination.json`). This is arithmetic, not softness:

> A two-sided sign test over 4 paired games has a smallest attainable p of
> **0.125**. No metric can reach p < 0.05 on this data however cleanly it
> separates. **Six** non-tied paired games are the minimum for the test to be
> able to clear the bar at all.
> — `battery/REPORT_V0.md`

The floor is emitted on every run, as `min_attainable_p` per metric and a
top-level `power` string, so nobody reads 0.125 as a near miss — and it is a
Phase-3 planning input, since a four-game development pile means the confirmatory
design needs repeats per game or a larger pile.

### 6.5 Three metrics found to be measuring something else

Found by running the instrument, not by inspecting it.

**P1 (actions per model call) is largely an API failure-rate readout.** It
separates the model ladder at Cliff's δ = −1.000 and *backwards* — haiku 0.97
actions per call, opus 0.52. Between 27 % and 45 % of pilot steps failed outright
on HTTP 500s and "game not found", and P1 divides *successful* actions by *all*
calls, so a run whose infrastructure failed more looks like one that planned less;
P1 correlates with the failure rate at **ρ = −0.83** (`battery/REPORT_V0.md`;
`battery/STATUS.md` W-4). v0's response is in the code: **P5 `step_failure_rate`**
is added as a diagnostic, so the confound reaches a reader before P1 does.

**E5 (cost per action) is a price list.** δ = +1.000, haiku $0.031/action, sonnet
$0.124, opus $0.279 — a 9× spread tracking token pricing and nothing else;
reference tier. A large effect in the wrong direction is now flagged separately
from the power verdict, as a `warning` field on P1 and E5
(`battery/artifacts/discrimination.json`): burying "this metric is backwards"
under "not enough data" wastes the most informative thing the pass can find.

### 6.6 A confound on a pre-registered primary endpoint

E2, the front-load index, is one of Phase 4's three pre-registered primary
endpoints and the signature of claim C2: understanding is bought early and spent
late (`battery/PREDICTIONS.md`). Within `bare_cc`, **the more capable model
front-loads more** — haiku 0.20, sonnet 0.25, opus 0.28, δ = +1.000 in the
declared direction, 4 wins of 4 paired games
(`battery/artifacts/discrimination.json`). No arm here has a theory. If capability
alone produces front-loading, front-loading is not specific to *having a theory*,
and C2's evidence weakens by however much of the effect capability explains.

Underpowered at n = 4 and possibly an artefact — but a confound the ablation arm
is well placed to separate, and one to check before Phase 4 freezes rather than
after. Two defences went into the code: E2 and E3 now refuse runs shorter than
eight turns, since a run that ends on turn four looks maximally front-loaded
while having understood nothing (`battery/artifacts/gaming_audit.json`).

### 6.7 What the battery still cannot see

Reproduced from `battery/REPORT_V0.md`:

| gap | why |
|---|---|
| **The whole economy family on Theoria** | A0 ran engines and hand adjudication with no LLM in the loop, so it has no model calls. Every economy metric is `not-applicable` on it |
| **Every epistemic metric on the controls** | `bare_cc` has no books. Structural, and predicted as such |
| **P4 solution redundancy — never computed once** | needs ground truth *and* a solve attempt. A0 has the truth but its trace is a coverage walk; the ledger runs are solve attempts with no truth. It is entirely notional in v0 |
| **M3 cross-level transfer (claim C3)** | no run reached a second level |
| **The specified discriminative gradient** | there is no Schema arm and may never be — `baseline-arms/SCHEMA_LOCATE.md`. v0 substitutes the model ladder; D-B-004 argues why that is weaker |

De-redundancy found two clusters at |ρ| ≥ 0.9 out of 29 metrics: X1 revisit rate ~
X4 no-progress streak at ρ = +0.916, same family, and P3 backtrack rate ~ X3
novelty front-load at ρ = +0.909, across families
(`battery/artifacts/redundancy.json`). Twenty-seven clusters from twenty-nine
metrics is *not* reassuring: it mostly reflects thin data, since most metric pairs
share too few runs to correlate at all and `MIN_SHARED_RUNS = 4` correctly refuses
to guess.

**What v1 needs, in order** (`battery/REPORT_V0.md`): more paired games, six being
the floor; separate the front-load confound with the ablation arm; fix K6, whose
A0 mean of +706 bits is carried by one concept at +2125 while two of three are
negative; defend E4, which cannot yet tell a prompt-compaction policy from a
theory that closed; filter K3 for non-triviality, since `0 = 0` is a theorem; and
get a machine-readable manifest from the theory compiler, because `parse_dsl`
re-reads a grammar another track owns.

Two smaller findings close the section. X5's 59 distinct states on the A0 base
trace, counted by digesting frames, agree with the 59 reachable states a
different pipeline recorded in `cold-start-a0/artifacts/trace_summary.json` — an
independent cross-check, pinned by a test. And `CLAUDE.md`'s pile digest
`3feca53e…41bbc19a` reads as a file hash and is not one: it is taken over the
canonical JSON minus its own `sha256` field, while the file itself hashes to
`d3140eff…`. The cut is intact and has never been modified; only the description
misleads (`battery/DECISIONS.md` D-B-011).
