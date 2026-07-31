# E3 · sk48, carrying g50t's two books

**Written as the run goes.** `MANIFEST.json` is the canonical account; this is
the narrative beside it. Sections are appended, never rewritten, so a section
dated earlier than the one below it is what was true then.

* prompt: `E3-engines-online`
* game: `sk48-d8078629` (development pile; sealed pile contact: **zero**)
* branch `agent/e3-engines-online`, base commit `e182c95`
* books carried from `runs/20260728T015354Z-g50t-first-contact/books`
  (`theory.dsl` sha256 `6e2694bc…a9e0`, 140 lines; `playbook.dsl` sha256
  `d6406993…107b`, 49 lines)
* budget: 120 actions, $18 ceiling, 3 h wall clock

---

## Before anything was spent

`BUDGET_PLAN.json`, written before the first action.

**S3's shared spend gate does not exist on this commit.** `proxy/spend_gate.py`
is absent and `agent/s3-spend-gate` carries no file matching `*spend*` under
`proxy/`. `armtools/spend_check.gate_status()` looked for it, found nothing,
recorded `absent`, and held no reservation. It is not recorded as a pass.

One correction to the premise E3's brief inherits from S3: browser-ops has
since established by logging into the account panel that **ARC has no quota at
all** — a key's only permission dimension is the game set. So "two campaigns
contending for one ARC quota" does not exist as a product-level problem. The
exposure that *is* real is the Anthropic bill, and it is the whole of this
run's $18.

**The projection, from P-8's measured cost** ($1.2635/call, 516 s/call, 5 calls
for $6.32): $18 buys about 14 desk calls; the evidence gate spends roughly four
actions per call; so 120 actions would cost about **$35**, and this run should
stop on the cost ceiling at roughly **29–61 actions**. Stated before the money,
so the outturn reads as the bill's shape rather than as a shortfall against 120.

## Pre-flight — 0 billed actions

`sk48-d8078629`: 64×64, colours `{0,1,2,3,4,5,6,8,9,14}`, `win_levels` 8,
`available_actions` `[1, 2, 3, 4, 6, 7]`, RESET 200 after 5 attempts,
`scorecard.total_actions` 0. **No `score` field** in the response — the same
Phase 1 obligation gap P-8 reported, unchanged on a second game.

`_legal_actions` filters ACTION6 (D-P8-012), leaving `[1, 2, 3, 4, 7]`: a
five-action opening sweep. tn36 was excluded because its `available_actions` is
`[6]` alone, so this arm would have had no legal action at all (D-E3-009).

## The 400 wave is worse here than on g50t

The opening sweep spent **5 billed actions across 60 HTTP requests** — an
amplification of **12×**, against P-8's 5.7×. The retry envelope is doing most
of the work of talking to this game. Both counts are in `bill_shape.json`, and
the file says in its own text that a curve against billed actions is not a
curve against requests.

## CORRECTION, appended after an adversarial review — read this before the section below

Everything from "The cold transfer" to the end of this file was written before
an adversarial reviewer was pointed at it, and **its headline claim does not
survive**. The numbers below are all correct; the epistemic status I assigned to
them was not. What follows is the correction, verified independently rather than
taken from the reviewer.

**1. The prediction and the observation are the same computation, so their
agreement could never have failed.** Work it through: `problem_from_frames`
builds `board` as frame 0 with every dynamic cell overwritten with background;
the generated `render` is `copy(BOARD)` plus exactly one pixel per present
object; `certify` diffs that against frame 0. A non-dynamic cell therefore
always matches — the board already carries frame 0's value there, and an anchor
found by colour paints the colour that cell already shows. A dynamic cell
matches iff it is background at t0 or owned. So

    cells_unexplained ≡ D0 − covered_by_objects        (identically, every game)
    predicted − observed ≡ K − covered_by_objects

**D0 cancels.** It appears on both sides and could be any integer at all with
the error unchanged. So "the arithmetic frame transferred perfectly: D0 is
right, the subtraction is right" — written below — asserts something this run
has no mechanism to test. Withdrawn.

**2. The "corrected formula" I derived is a definition, not a discovery.**
`D0 − |{declared colours whose raster-first cell needs an owner}|` is exactly
`D0 − covered_by_objects`, which is `books.py`'s own `n_unexplained_at_t0`. It
will be right on every game forever because it is the measured quantity written
backwards. Presenting it as a finding was wrong.

**3. The correction was already in the carried manual, before sk48 existed.**
`responsibility_ceiling_is_two_pixels`, the theorem directly below the formula
and declared `[depends: render_accounting_closed]`, says colours whose
raster-first cells are "both constant board cells, so objects in those colours
would explain nothing they were not already given." That is precisely the
condition sk48 triggered on two of three objects. So the +2 is not something
the new game taught anyone — it is a gap in `inner/transfer.py`, which
implements the formula's one-sentence summary and drops the qualifier the
manual attached to it. **A reading faithful to the theorem cluster predicts 72,
which is exactly right.** The verdict `refuted` is a verdict on my code.

**4. This run cannot distinguish what K means.** On sk48, "distinct declared
colours present at t0", "declared objects" and "located objects" are all 3. The
only datum that separates them is g50t itself — the game the formula was fitted
on.

**5. No theory content transferred, and the reason is sharp.** The carried
manual's generated `ACTIONS` is `[('key', 5)]` and all three of its rules open
with `if action != ('key', 5): return False`. **sk48 does not offer ACTION5** —
its `available_actions` is `[1,2,3,4,6,7]` and the sweep sent 1, 2, 3, 4, 7. So
every rule in the manual is unreachable and `step` is the identity for every
action this arm can send. Replay 0/5 is therefore trivial rather than
structural: the manual predicts a frozen frame while the world moves. And
`void_blocks_and_the_guard_language_is_inverted` asserts the background colour
is 0; on sk48 it is 5, so that theorem is simply false here and nothing checked
it.

**C3 transfer is untested by this run.** That is the honest headline, and the
reason is useful: *a carried manual whose action vocabulary does not intersect
the new game's cannot be tested on it at all.* Any future carry should check
that intersection before it spends anything — it is free to compute.

**6. A defect this exposed: level data crossed anyway.** `NEVER_CARRIED`
excludes `problem.json` so that one game's geometry cannot enter another's
level. Seven of g50t's landmark coordinates arrived in sk48's `problem.json`
verbatim — `start_cell (10,16)`, `gate_cell (40,16)`, `goal_cell (52,46)` and
four more — because `_landmarks_from_theory` reads them from `# arc-cell:`
comments *inside the manual*, which does travel. Fixed in
`transfer.strip_level_data`, with tests; the stripped landmarks are listed in
the provenance and default to the origin, which is the existing visible failure
mode for a coordinate the level cannot supply.

**7. Two smaller errors below.** "Lean refused for the declared reason (state
estimate above the enumeration ceiling)" is false — `lean_state_estimate` is
`null` and the refusal text says "an unknown number"; the estimate was never
computed. And "it compiled" is close to uninformative: `compile_all` sets
`ok = bool(forms["python"])`, the domain text is byte-identical to the one that
already compiled on g50t, and the only problem-side failure mode — an unplaced
landmark — was precluded by exactly the leaked coordinates of point 6.

**What does survive.** The transfer *mechanism* ran end to end at zero model
cost: carry, compute the new level from the carried manual's own declarations,
compile four forms, certify against the new game's frames, all before a model
was called. That machinery is real and is what E3 asked to be built. The engine
supply-chain measurements, the bill-shape numbers and the 400-wave amplification
below are unaffected by any of this.

---

## The cold transfer — zero model calls, and the headline result

> Superseded by the correction above. Kept verbatim because the numbers are
> right and because a run that quietly rewrote its own first reading would be
> exactly the failure this repository keeps writing incident reports about.

The carried manual was compiled against sk48's *computed* level and certified
over the opening sweep **before the desk was called even once**, so every number
below belongs to an unrepaired manual written for a different game.

**It compiled.** Markdown, PDDL and Python all generated; `ok: true`. Lean
refused for the declared reason (state estimate above the enumeration ceiling).
So a manual written for g50t produced a working executable predictor against
sk48's level. That is the mechanical content of the transfer claim, and it held.

**It predicted its own failure number, and missed by 2 in 4096 cells.**

| | |
|---|---|
| D0 — dynamic non-background cells at t0 | 73 |
| K — distinct declared colours present at t0 | 3 |
| predicted unexplained (`D0 − K`) | **70** |
| observed unexplained | **72** |
| verdict | **refuted, by +2** |

The prediction reached disk as a `prediction-only` revision of `transfer.json`
before certify ran; the `cold` revision carries the verdict.

**Why +2, exactly.** `books/problem.json` reports `need_an_owner_at_t0: 73` and
`covered_by_objects: 1`. All three declared objects *located* on sk48
(`Marker` colour 9 at (25,42), `Unused` colour 1 at (38,16), `Spent` colour 2 at
(14,13)) — but only **one** of the three anchors landed on a cell that needed an
owner. The other two anchored on cells the board already explains, and so
explained nothing.

That is the formula's hidden assumption failing, and nothing else. The
arithmetic frame transferred perfectly: D0 is right, the subtraction is right,
and the error is exactly the number of declared colours whose raster-first cell
missed the set of cells needing an owner. The corrected statement is

    unexplained(frame_0) = D0 − |{declared colours whose raster-first cell
                                  is itself a cell needing an owner}|

which reduces to the carried formula precisely when every declared colour's
anchor is load-bearing — which is true on g50t, where it was written, and false
here. A formula that survives a change of world down to a two-cell correction,
with the correction mechanically explained, is a better result for C3 than one
that happened to be exactly right.

**Replay: 0/5.** Expected and structural, for the reason the carried manual
itself states: frame 0 is already 72 cells wrong before any rule fires, so
whole-frame replay cannot pass here at any n.

## The engine supply chain — stable, and the bottleneck

The cold dispatch delivered. All three engines came back without raising; 680
candidate rows were appended and the stream validates against the frozen schema
(`CONTRACTS/candidates_schema.md`) live, mid-run.

| engine | outcome |
|---|---|
| `mdl_segmenter` | delivered, 4 tracks, `connected_components(4)`, **20 ms** |
| `cegis_miner` | delivered, 4 tracks, **4 refusals** — sk48 narrates `vanish` and `recolor`, not just `move` |
| `zero_space` | delivered, 97 cells, 679 features, rank 3, 676 laws (94 global), **THIN**, **347 746 ms** |

Two findings, and the second is the one that matters for planning.

**`cegis_miner` refused on every track, and that is the engine working.** Its
precondition is exactly one `move` event per transition; sk48 narrates `vanish`
and `recolor` as well. This is the second game in a row to refuse it, for a
different reason than g50t's (there the mover fused into a 1006-cell blob). A
refusal with its reason is a delivery; `engines_online.jsonl` keeps `delivered`,
`error`, `skipped` and `n_refusals` in separate columns so the two can never be
read as one.

**`zero_space` is 99.86% of the dispatch, and it is slowest exactly when it is
least informative.** 348 s of a 348 s dispatch. The intuition that more evidence
costs more is backwards here: the cost tracks the *null space dimension*, which
is large precisely when the transitions are too few to constrain the features.
Benchmarked offline, away from the live run:

| shape | features | rank | dimension | time |
|---|---|---|---|---|
| g50t-shaped, random colours | 370 | high | 364 | 21 s |
| sk48-shaped, random colours | 970 | high | 965 | 98 s |
| **sk48 live: 5 transitions** | **679** | **3** | **676** | **348 s** |
| synthetic, 97 cells / 7 colours, rank ~3 | 679 | ~3 | ~676 | **>600 s** (killed) |

The live dispatch has *fewer* features than the 98 s synthetic and took 3.5×
longer, and the deliberately-thin synthetic at the same shape ran past ten
minutes. So the engine is cheapest when its answer is worth something and most
expensive when its own verdict is THIN — which is every early turn of every new
game, i.e. exactly when the arm dispatches it most.

The consequence for this arm is concrete: at ~6 minutes per dispatch and one
dispatch per theorize, the engines and the desk cost comparable wall-clock, and
a 3-hour run buys single-digit turns. `zero_space` is the first thing to look
at if this arm's turn rate ever needs to go up.

**A defect of mine that this record exposed.** Dispatches 0 and 1 both ran over
the same five transitions: 348 s each, 680 candidate rows each, and the second
680 were a copy of the first. `README.md` says a run's repeated sweeps are not
duplication "because each sweep sees more transitions than the last" — which
was exactly not true of these two, because lifting the dispatch out of
`theorize` introduced a sweep that no new evidence separated from the next one.
Fixed: the dispatch now reuses the last result when the store has not grown and
records the reuse as its own row with `elapsed_ms: 0`.

---

## How this run ended: a paid call thrown away by an upstream schema change

**The run was stopped at 9 billed actions and $2.695, deliberately, because
every desk call it made was going to cost $2.70 and produce nothing.**

The first desk call returned. `desk.calls` said 1 and `cli_cost_usd` said
2.694961 — the provider had been paid — but `desk_log.json` was `[]`, no
transcript existed, and the ledger contained **zero `model_call` records**.

Reproduced offline in one run: `proxy/canon.py` refuses

> `model_call` is one of the two shapes and its field set is closed
> (LEDGER_FORMAT.md §4): `'beat'`, `'label'`, `'proxied'`, `'proxy_gap'`,
> `'transport'` are not defined.

P-8 wrote those five straight onto the `model_call` record, and `LEDGER_FORMAT.md`
§4 **closed that field set after P-8 landed**. This arm imports `proxy/` as a
library from the repo root, so the change arrived silently on a commit this
track never touched. Every desk call died in the ledger write, after the money.

Three fixes, all tested:

* **The five moved into `request`**, which is caller-owned on the canonical
  record and already carried `beat`, `label` and `transport`. Nothing is lost
  and no event is invented — `EVENTS` in `proxy/ledger.py` is closed to seven
  names, none of which fits, and adding one would mean editing another track's
  directory. `beat` stays on the ledger, one level deeper, so constraint 8
  remains checkable from the file. `armtools/archive.py` reads both depths, so
  P-8-era ledgers still report their beats instead of `unknown`.
* **A paid reply is no longer discarded by a bookkeeping failure.** The arm's
  own log entry and the transcript are written *before* the ledger, the ledger
  write is wrapped, and a refusal lands in `desk.ledger_failures` and in
  `summary()["calls_missing_from_ledger"]` — an incomplete ledger that says so
  beats a lost call.
* **A test that would have caught it.** P-8's suite checked the record's shape
  against hand-built dicts and passed while the live writer refused the real
  thing. `test_a_desk_call_is_actually_accepted_by_the_frozen_writer` now drives
  `ModelDesk` into a real `proxy.ledger.RunLedger` with only the CLI stubbed.

**The standing lesson.** `_bootstrap.upstream_pin()` hashes every upstream file
this arm depends on into every manifest, precisely so a silent change upstream
cannot silently change these results. It did its job — the hashes are in
P-8's manifests and would have differed — but **nothing compares them between
runs**, so the pin recorded the change and no one was told. A pin that is
written and never diffed is a pin that documents an incident after it has cost
money.

The run's artefacts are kept intact rather than deleted, as P-8 kept its
aborted runs. The cold-transfer measurements above cost no model calls and are
unaffected by this fault. The successor run is
`20260728T083400Z-E3-sk48-carried-v2`, with a $15 ceiling — the campaign's $18
minus what this run spent.
