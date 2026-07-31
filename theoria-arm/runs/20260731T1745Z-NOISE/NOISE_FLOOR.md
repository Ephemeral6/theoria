# The noise floor: what two identical legs do when nothing changed

`Theoria.md:336` forbids reading one leg's difference as evidence. That rule has
no teeth without a number — *smaller than what* is not evidence? This run
measures that number on the offline path, twenty-four campaign repetitions in
about three minutes and zero dollars, and reports honestly which half of the
question it can answer and which half it cannot.

The headline is two sentences, and they point in opposite directions:

* **Every campaign-level scoreboard column is exactly deterministic offline.**
  Two independent sets of twelve repetitions each — 48 campaigns, 24 per mode —
  spread 0 in all twenty-one columns, in both modes, and the two sets agree
  column-for-column.
* **The per-turn curve underneath those columns is not.** The same surprise
  landed on a different turn in 28% of leg-observations, displaced by up to two
  turns, with nothing changed. Figure 2 and the E2 front-load index read the
  per-turn curve, not the totals.

A total can be perfectly stable while the curve under it moves. That is the
whole finding.

---

## 1. What was run

Two modes, because the offline path has two halves and the published rehearsal
command only runs one of them.

### Mode `cli` — the command the CLI's own help prints

```
python -m harness.campaign --mock --pool <tmp>/poolN.jsonl --out-dir <tmp>/outN
```

Twelve repetitions, as subprocesses, verbatim.

`--mock` without `--desk` sets `offline=True`, and `inner/loop.py:856` then
skips the theorize beat outright (`"skipped: offline dry run makes no model
calls"`). No desk call means no manual; no manual means
`books.load_predictor()` returns nothing; no predictor means plan, certify,
probe design and the engine dispatch are all unreachable and every turn falls
through to `_probe_or_explore`'s exploration branch,
`min(legal, key=lambda a: (self.action_counts.get(a, 0), a))`.

So the seven surprise counts, theorize rounds, certify rounds, engine
dispatches and desk calls are not *measured* zeros in this mode. They are dead
columns reading zero. A noise floor computed only from this would be a table of
confident zeros about machinery the campaign never touched.

### Mode `stub-desk` — the desk held constant, everything else real

Same `Campaign`, run in-process, with `ModelDesk._invoke` replaced by a canned
envelope whose `result` is a **real archived desk answer replayed** — the
`theory.dsl` and `playbook.dsl` of `runs/20260731T1430Z-A3-level2-carried-r3`,
reassembled into the `=== THEORY === / === PLAYBOOK === / === LOG ===` blocks
`inner/theorize.py:BLOCK` parses. The desk is thereby a constant whose value is
a thing that actually happened, while the engines, the four compilers, certify,
plan, probe and the replay checker all run for real.

Any spread that survives *that* is the framework's own, which is exactly the
quantity `Theoria.md:336` needs and the quantity mode `cli` cannot see.

Twelve repetitions. No subprocess is started for the desk, and no dollars move:
the price in the canned envelope is `0.0`, deliberately — a stub that invents
plausible dollars puts fiction into the cost columns.

### The negative control

`install_stub_desk` claims no real `claude` CLI can start under it. A claim like
that is worth nothing until it has been seen to refuse, so
`--negative-control` installs the `claude_bin` raiser **without** the `_invoke`
stub and runs a whole leg under it. Verbatim, from
`negative_control.json`:

```
"direct_call": "DeskWasNotStubbed: armtools.noise_floor forbids starting the
 real `claude` CLI: this measurement is offline and must not spend. Reaching
 claude_bin() means a desk call escaped the stub."
"refused": true
"desk_failures": [
  "{\"error\": \"DeskWasNotStubbed: ...\", \"step_idx\": 6}",
  "{\"error\": \"SpendGateTripped: 1 call(s) in this pool could not be priced,
    so the pool's dollar total is a lower bound and this gate would be checking
    $7.0000 against a number it knows is too small. ...\", \"step_idx\": 7}"
]
```

Two things worth keeping from that. First, the guard fires. Second, **the
refusal does not surface as an exception anywhere `campaign.json` can see it**:
`inner/loop.py` catches a raising desk and files it under `desk_failures`, which
is right, and which means a negative control that had only inspected the
campaign report would have concluded the guard never fired. The first draft of
this control did exactly that and reported `refused: false`.

Third thing, free: one unpriced call poisons the pool for the rest of the leg.
The raised call was charged at its ceiling ($7.00, fiction, scratch pool) and
flagged unpriced, and the *next* call tripped `SpendGateTripped` on the
unpriced-row rule rather than on any budget. Worth knowing before a live leg
meets its first transport failure.

---

## 2. The columns

Twelve repetitions each. `mean / min / max`, summed over the campaign's legs.
`det` = every repetition produced the same value.

### Mode `cli` (12 reps, 4.52 s – 6.08 s each)

| column | mean | min | max | det |
|---|---|---|---|---|
| surprise.execution_mismatch | 0 | 0 | 0 | yes |
| surprise.heuristic_miss | 0 | 0 | 0 | yes |
| surprise.probe_refutation | 0 | 0 | 0 | yes |
| surprise.proof_failure | 0 | 0 | 0 | yes |
| surprise.render_mismatch | 0 | 0 | 0 | yes |
| surprise.replay_mismatch | 0 | 0 | 0 | yes |
| surprise.search_timeout | 0 | 0 | 0 | yes |
| surprise.total | 0 | 0 | 0 | yes |
| theorize_rounds | 0 | 0 | 0 | yes |
| certify_rounds | 0 | 0 | 0 | yes |
| engine_dispatches | 0 | 0 | 0 | yes |
| desk_calls | 0 | 0 | 0 | yes |
| levels_boundaries | 0 | 0 | 0 | yes |
| actions_ok | 40 | 40 | 40 | yes |
| commands_sent | 41 | 41 | 41 | yes |
| steps | 41 | 41 | 41 | yes |
| turns | 36 | 36 | 36 | yes |
| legs_played | 1 | 1 | 1 | yes |
| legs_failed | 2 | 2 | 2 | yes |
| usd | 0.0 | 0.0 | 0.0 | yes |

`moved: []` — nothing. One stop signature, 12/12:
`3 legs in a row made no progress; the last 3 ended in an exception`.

**The thirteen zeros in the top half of that table are dead, not measured.**
Only the bottom seven rows are measurements.

### Mode `stub-desk` (12 reps, 10.28 s – 11.32 s each)

| column | mean | min | max | det |
|---|---|---|---|---|
| surprise.execution_mismatch | 0 | 0 | 0 | yes |
| surprise.heuristic_miss | 0 | 0 | 0 | yes |
| surprise.probe_refutation | 0 | 0 | 0 | yes |
| surprise.proof_failure | 0 | 0 | 0 | yes |
| surprise.render_mismatch | 0 | 0 | 0 | yes |
| **surprise.replay_mismatch** | **4** | **4** | **4** | yes |
| surprise.search_timeout | 0 | 0 | 0 | yes |
| surprise.total | 4 | 4 | 4 | yes |
| theorize_rounds | 6 | 6 | 6 | yes |
| certify_rounds | 8 | 8 | 8 | yes |
| engine_dispatches | 8 | 8 | 8 | yes |
| desk_calls | 18 | 18 | 18 | yes |
| levels_boundaries | 0 | 0 | 0 | yes |
| actions_ok | 160 | 160 | 160 | yes |
| commands_sent | 164 | 164 | 164 | yes |
| steps | 164 | 164 | 164 | yes |
| turns | 146 | 146 | 146 | yes |
| legs_played | 4 | 4 | 4 | yes |
| legs_failed | 0 | 0 | 0 | yes |
| usd | 0.0 | 0.0 | 0.0 | yes |

`moved: []`. One stop signature, 12/12: `3 legs in a row completed no level and
met no new kind of surprise`. The four legs are three on `g50t-5849a774` and
one on `sk48-d8078629`; the campaign stops there, so the third and fourth games
are never reached in either mode.

Six of the seven surprise kinds still never fire. `replay_mismatch` does — one
per leg, four per campaign — because the replayed manual was written for a
different level of a different game and its `step` disagrees with the mock's
transitions immediately. That is one kind out of seven; the other six have no
offline noise floor at all, at either mode.

---

## 3. Where the run-to-run variation actually lives

The audit normalises away a **named** list of volatile fields
(`noise_floor.VOLATILE_KEYS`: timestamps, run ids, slugs, ports, pool paths,
absolute paths, elapsed durations) and then diffs what is left, leg by leg,
across all twelve repetitions. Naming the list is the point: everything not on
it that still moves is a finding, and a normaliser that quietly smoothed away an
unnamed field would turn the audit into a tautology. There is a test for that
(`test_normaliser_still_sees_a_real_difference`).

Sources found, and whether each reaches the scoreboard:

| source | where it shows | reaches a column? |
|---|---|---|
| ephemeral port of the mock ARC / env proxy | `run.json:env_proxy.upstream` | no |
| mock scorecard and guid ids (`card-…`, `guid-…`) | `run.json:env_proxy.card_ids`, `.guids` | no |
| scratch-pool path and its `policy_sha256` | `run.json:spend.pool.*` | no — an artefact of a per-rep pool file, not of the framework |
| leg slug (second-resolution UTC) | every absolute path in every artefact | no |
| `wall_clock_s` per turn | `turn_series.json:rows[].wall_clock_s` | no — 0 vs 1 s, a duration |
| source-file `sha256` in the provenance block | `turn_series.json:provenance.sources.*` | no — these hash files that themselves carry timestamps, so they must move |
| **surprise → turn attribution** | **`curves.json:rows[].surprise_*`** | **yes, to every per-turn column** |

`surprises.jsonl` and `turns.json` are identical after normalising in every
repetition of both modes; `surprises.jsonl` is byte-identical in mode `cli`.
The surprises themselves — how many, of what kind, in what order — do not move.
Only *where the reduction files them* does.

### The one that matters

Pooled over 48 leg-observations per set (12 reps × 4 legs) in mode
`stub-desk`, each carrying exactly one surprise. Two independent sets, run
about twenty minutes apart on the same commit:

| row index the surprise was filed under | set 1 | set 2 | pooled |
|---|---|---|---|
| 0 | 36 | 33 | 69 |
| 1 | 11 | 13 | 24 |
| 2 | 1 | 2 | 3 |

Modal row 0 in both. **Off-mode fraction 0.25 (set 1), 0.3125 (set 2), 0.281
pooled over 96 leg-observations; maximum displacement 2 rows in both.** Per leg
ordinal in set 2: leg01 `{row0: 9, row1: 3}`, leg02 `{row0: 8, row1: 4}`,
leg03 `{row0: 7, row1: 3, row2: 2}`, leg04 `{row0: 9, row1: 3}` — every leg
ordinal moves, so this is not one unlucky leg.

Nothing changed between those repetitions. Same command, same mock world, same
canned desk reply, same machine, same commit. The two sets' *columns* are
identical to the count; only the placement moves.

**Root cause, and the code says it out loud.** `armtools/archive.py:491–497`:

> Surprises join by time, not by index. … The one weakness is resolution:
> `Surprise.ts` is truncated to the second while ledger stamps carry
> milliseconds, so a surprise landing inside a second that straddles a turn
> boundary is genuinely ambiguous. Those are counted and reported rather than
> assigned quietly.

They are counted. In every one of the 48 leg-observations,
`join.surprises_within_1s_of_a_turn_boundary` is `1` — i.e. **100% of the
surprises in this run are ambiguous by the reduction's own test** — and
`join.join_confidence` reads `"exact"` in the same object. The instrument
records the ambiguity and calls the join exact in the same breath. Nothing
reads the first field.

**This is not only a mock-speed artefact.** The largest live leg in the archive
that carries a `turn_series.json`,
`runs/20260728T083400Z-E3-sk48-carried-v2`, reports:

```
surprises_within_1s_of_a_turn_boundary = 22     (of 39 surprises, 27 turns)
join_confidence                        = "exact"
```

Fifty-six per cent of a real leg's surprises were attributed ambiguously, and
the record calls that exact.

**And the caveat does not survive the next hop.** `armtools/curves.py:257`
copies `join["join_confidence"]` into `curves.json` and copies **nothing**
about the ambiguity count. `curves.json` is the file the figure pipeline reads.
Today's four live legs carry `join_confidence` `exact` / `degraded` /
`degraded` / `ambiguous-reconstructed` and no ambiguity count at all.

---

## 4. The rule

Written in the form the item asked for, in three parts, because one number
would be a lie by compression.

> **N-1 (campaign totals, offline).** With the world and the desk both held
> fixed, all twenty-one campaign-level columns had spread 0 over 24 repetitions
> per mode, in two independent sets that agree column-for-column. **The
> framework contributes less than one count of variance to every scoreboard
> total.** Any offline difference of ≥1 in a total is real and is caused by the
> change under test.

> **N-2 (per-turn curves — the binding one).** **A round-to-round change in any
> per-turn series that could be produced by displacing each surprise up to 2
> turns earlier or later is not evidence.** The measured floor is: 28% of
> surprises land off their modal turn (0.25 and 0.3125 in two independent sets
> of 48 leg-observations), maximum displacement 2 turns, at zero change. This
> binds figure 2's rows, the `surprise_*` columns of
> `curves.json`, and anything computed from them —
> `battery/metrics/economy.py`'s E2 front-load index above all, since the
> front-load index is a statement about *where in the turn order* the mass sits
> and this jitter moves exactly that.
>
> Operationally: before reading a change in a per-turn curve, recompute the
> statistic with every surprise displaced ±1 and ±2 turns. If the claimed
> difference lies inside that envelope, it is the join's resolution and not the
> world's.

> **N-3 (live totals — unmeasured, and this run cannot measure it).** The
> offline floor of 0 on the seven surprise counts, theorize rounds, levels and
> desk calls says **nothing** about live variance, because offline the world is
> a fixed-script mock and the desk is either skipped or replayed byte-for-byte.
> Those are the two stochastic elements in a live leg and both were removed on
> purpose. Until live repetitions exist, `Theoria.md:336` stands unrelaxed: a
> single live leg's difference in any of those columns is not evidence, and no
> threshold derived here licenses reading one.

The distinction the item asked for, stated plainly: **every column that is
deterministic offline and varies live is varying because of the world and the
desk, not because of the framework.** After this run that is *all* of them —
the framework's contribution to the totals is zero to the resolution of one
count. The one place the framework does inject variance of its own is the
surprise→turn join, and that is a reduction defect with a known cause, not
irreducible noise.

---

## 5. The offline mock is too deterministic to speak for live — what would be needed

Stated plainly, as the item allows: **yes.** Mode `stub-desk` removes both
stochastic elements by construction, and mode `cli` never reaches them. No
amount of repeating either produces an estimate of live spread in the seven
counts.

The live design that would, and its price, from this arm's own three carried
legs of 2026-07-31 (`runs/20260731T1310Z-…-r2`, `…T1430Z-…-r3`,
`…T1500Z-sk48-carried-l1`):

| leg | usd | actions billed | desk calls | surprises | elapsed |
|---|---|---|---|---|---|
| r2 | 9.56 | 13 | 5 | 12 | 3964 s |
| r3 | 13.44 | 33 | 8 | 29 | 5735 s |
| sk48-l1 | 12.25 | 21 | 9 | 20 | 6735 s |

Mean **$11.75** per carried leg, mean **1.52 h** wall clock.

A repetition set is *n* legs identical in every controllable respect — same
game, same level, same seed books, same prompt, same caps — differing only in
what the world and the desk do.

| n | cost | sequential wall clock | share of the $143.50 pool | what it buys |
|---|---|---|---|---|
| 3 | ~$35 | ~4.6 h | 25% | a range. No usable sd. |
| 5 | ~$59 | ~7.6 h | 41% | first honest min/max/median on the seven counts |
| 8 | ~$94 | ~12.2 h | 65% | a crude sd; enough to state N-3 as a number |
| 12 | ~$141 | ~18.2 h | 98% | matches this run's offline n, and spends the pool |

Actions are not the binding constraint: 15845 pool actions at the sizing ratio
of 9.3 outbound per successful action is roughly 1700 successful actions, and
twelve legs at ~22 actions each is ~260. **Dollars bind, and they bind hard** —
n=12 live is the entire remaining pool and nothing else happens this phase.

The recommendation, which is a recommendation and not a decision: **n=5 on one
dev-pile game, ~$59, ~8 h.** It competes directly with running new Phase-3
rounds, and that trade is a human call. What is *not* a call is that until some
n>1 exists, every live round-to-round comparison in this arm is being read
against an unmeasured floor.

---

## 6. Residual gaps, stated

1. **Six of the seven surprise kinds have no noise floor at any level.** Only
   `replay_mismatch` ever fired offline. `execution_mismatch`,
   `heuristic_miss`, `probe_refutation`, `proof_failure`, `render_mismatch` and
   `search_timeout` read 0 in all 24 repetitions and that 0 is untested, not
   measured.
2. **`levels_boundaries` has no floor at all.** The mock never advances a level
   in any repetition, so the level-boundary machinery — which is where C3's
   transfer claim lives — is entirely unexercised by this measurement.
3. **`stub-desk` is my instrument, not the framework's.** Its determinism is
   evidence about the framework only to the extent that one fixed reply is
   representative. A single canned answer cannot exercise desk-driven
   branching: every repair round gets the same manual back, so the
   `REPAIR_ROUNDS` path and every branch conditioned on what the desk said are
   held at one value.
4. **The published rehearsal command is degenerate, deterministically, 12/12.**
   `--mock --pool` plays leg 1 of game 1 and then fails legs 2 and 3 with
   `FileNotFoundError: no theory.dsl carried in from …/books`, because offline
   skips theorize so leg 1 writes no books and the carry correctly refuses an
   empty manual. Three zero-progress legs end the campaign, and games 2–4 are
   never reached. The command in `harness/campaign.py`'s own `--pool` help text
   therefore exercises one leg and two constructor failures.
5. **`Campaign` has no `--runs-root`.** `run_leg` hardcodes
   `leg_dir = <arm>/runs/<slug>` and does not forward `play(runs_root=…)`, so
   every rehearsal leg lands in the tracked archive — the archive
   `harness/run.py` documents a smoke must stay out of, because
   "`armtools.verify_provenance` refuses a fixture found under it". These 24
   repetitions would have deposited 84 such directories.
   `armtools/noise_floor.py` snapshots `runs/` and deletes exactly what each
   repetition created, after reading the numbers out of it. Nothing else does,
   and nothing stops the next rehearsal from filling the archive again.
6. **The audit's normaliser is a judgement call.** `VOLATILE_KEYS` and the slug
   regex decide what counts as uninteresting motion. The list is short, named in
   source, reported in the artefact (`variation_audit.volatile_seen`), and
   tested against a case where it must *not* smooth — but a field that is both
   volatile and load-bearing would be invisible to this audit, and I have not
   proved none exists.
7. **The surprise→turn defect is reported, not fixed.** Fixing it means either
   giving `Surprise.ts` sub-second resolution or joining on something other than
   the clock, and `armtools/archive.py` is this arm's file but the change would
   move numbers in every archived `curves.json`. That is a decision with a
   downstream blast radius, not a patch to slip into a measurement run.

---

## 7. Reproducing this

```bash
cd theoria-arm
python -m armtools.noise_floor --mode cli       --reps 12 --out <dir>/cli
python -m armtools.noise_floor --mode stub-desk --reps 12 --out <dir>/stub \
       --books runs/20260731T1430Z-A3-level2-carried-r3/books
python -m armtools.noise_floor --negative-control --out <dir>/negctl
python -m pytest tests/test_noise_floor.py -q
```

Total ≈ 3.5 minutes, $0.00, no network, no ARC contact, no model call. The
per-repetition leg artefacts are copied under `<dir>/<mode>/work/repNN/legs/`
and are **not** archived here — they are ~40 MB and the numbers derived from
them are all in `noise-cli.json` and `noise-stub-desk.json`.

Artefacts in this directory:

* `noise-cli.json` — 12 repetitions of the documented rehearsal, per-rep
  columns, the variation audit, the placement histogram.
* `noise-stub-desk.json` — the same for the desk-held-constant mode.
* `noise-cli-set1.json`, `noise-stub-desk-set1.json` — the first, independent
  set of 12+12. Kept because its agreement with the second set is the evidence
  for N-1 and its disagreement with the second set's *placement* histogram is
  the evidence for N-2. Its `variation_audit` has no `surprise_placement` block:
  `placement_histogram` was written after set 1 ran, and set 1's placement
  numbers in §3 were read out of its work tree by hand and then reproduced
  mechanically by set 2. That is a provenance seam and it is stated rather than
  hidden.
* `negative_control.json` — the guard being seen to refuse.
* `MANIFEST.json` — provenance and per-file sha256.

The gate at the time of writing (`cd theoria-arm && python -m pytest -q`):
**457 collected, 455 passed, 2 failed, 0 skipped.** Both failures are
**pre-existing on master and neither is caused by this work**:
`tests/test_arm.py::test_the_archive_stays_accountable`
(`re-deriving every manifest reproduces it byte for byte: drifted:
['20260731T1240Z-A3-level2-carried', '20260731T1310Z-A3-level2-carried-r2',
'20260731T1430Z-A3-level2-carried-r3', '20260731T1500Z-A3-sk48-carried-l1']`)
and `tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive`
(`claude-opus-5: the recorded rate $0.0030474/s is below the worst rate in the
archive, $0.0042222/s`). Both name today's four live legs and both reproduce
with every file added by this run removed from the tree. `tests/test_noise_floor.py`
is 9 passed.
