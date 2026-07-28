# RUN_STATE — theoria-arm

Where the runs stand. One section per run; the numbers here are copied from
`runs/<slug>/MANIFEST.json`, which is generated, so this file is a summary and
never a source. A number that appears only here is a mistake.

---

## `preflight-20260728T012057Z` — the live chain, for zero quota

**Purpose.** Prove that the key, the guard, the proxy and the retry envelope
all work before an action is spent. RESET is not billed, so opening a
scorecard, sending one RESET and closing costs nothing.

**Result: PASS**, and two findings.

| | |
|---|---|
| RESET | 200, **after 18 attempts** |
| env_steps in the ledger | 18 (17 × 400, 1 × 200) |
| billed actions | 0 — `scorecard.total_actions: 0` |
| key injected inside the proxy | yes; the arm holds nothing |
| guard | `3feca53e…41bbc19a`, cut `v1`, 4 dev / 21 sealed |
| incidents | 0 bypass attempts, 0 credential-in-body, 0 sealed-pile requests |
| frame | one 64×64 grid, colours `{0, 1, 5, 8, 9}` |
| `available_actions` | `[1, 2, 3, 4, 5]` (no ACTION6 on this game) |
| `win_levels` | 7 |
| `levels_completed` | 0 |

**Finding 1 — the wave is live.** 18 attempts for one RESET. `arc-recon`'s
40-attempt envelope is load-bearing right now, not a historical artefact.
`proxy/forward.py`'s 5 attempts, which exclude 400 entirely, would have
returned a hard failure here. This is why the retry lives arm-side
(`DECISIONS.md` D-P8-003), and why the ledger carries 18 `env_step` records for
one successful command.

**Finding 2 — no `score` field.** Confirmed on live data: the response key set
is `action_input, available_actions, frame, full_reset, game_id, guid,
levels_completed, state, win_levels`. `LEDGER_FORMAT.md` §3's score obligation
cannot be computed against this API. Recorded as `INC-TA-002`.

---

## `20260728T015354Z-g50t-first-contact` — the first online contact

**Purpose.** P-8: connect the inner loop, proved four times offline
(`a0-spike`, `cold-start-a0`, A1, `cold-start-a2`), to a real environment
through the double proxy. The goal is not to win — it is that the loop turns
online and the books balance.

**Settings.** `g50t-5849a774`, 109 successful actions (120 minus the 11 spent
on the two aborted attempts, so the red line holds across all three), 3000 HTTP
commands, `claude-opus-5` at the desk, $16 ceiling, 7200s wall clock, no
variant.

**Three attempts. The first two aborted on defects in this arm** (landmarks the
level generator never placed; a desk that had tools and spent its turn writing
its answer to a file). Both are archived intact under `runs/*-aborted/` with an
`ABORTED.md` each, and accounted for in `INCIDENTS.md` INC-TA-004. The third is
the run below: `runs/20260728T015354Z-g50t-first-contact/`.

### The run, from its own `MANIFEST.json`

| | |
|---|---|
| actions | **7** successful, 0 failed, 1 RESET |
| HTTP commands | 40 → amplification **5.71** |
| scorecard | `total_actions 7`, `score 0.0`, `levels_completed 0` of 7 |
| ledger `env_step` records | 40 (8 at 200, 32 at 400) |
| **action count reconciles** | ledger 7 = scorecard 7 ✔ |
| **levels reconcile** | ledger 0 = scorecard 0 ✔ |
| score reconciliation | `unavailable` — the API returns no score (INC-TA-002) |
| model calls | **5**, all at `theorize`, $6.32 |
| surprises | **8**, all empirical: 4 `render_mismatch`, 4 `replay_mismatch` |
| constraint 8 | **holds** — 1 bootstrap call + 4 covered by surprises, 0 at any forbidden beat |
| sealing | 0 bypass attempts, 0 credential-in-body, 0 guard blocks |
| sealed pile | **untouched, verified from the bytes** — the only game id anywhere in the records is `g50t-5849a774`; cut digest checked |
| Lean | never available (state space past the ceiling) |
| plan | `no_goal_declared` at close |

### The loop turned, and here is the shape of one turn

theorize (call 1, $1.33, 588s, 46,248 output tokens) → **the compiler refused**
the manual, because an `invariant` carried prose where only a `theorem` may →
theorize again (call 2, $0.87, 333s) → **all four forms generated** →
certify → **69 pixels of frame 0 belong to neither the board nor any declared
object**, and 0 of 7 transitions replay → two surprises → plan →
`no_goal_declared` → probe → **`probe_frontier` reports that no action
separates any two hypotheses**, so the probe is recorded as unrunnable with
that reason and the arm explores the least-tried legal action instead.

Then it went round again, four more times.

### The one number that measures the loop — and it does not say what it first looked like

Unexplained pixels at frame 0, across the four certify rounds:

```
69 → 68 → 69 → 69
```

Read after two rounds this looks like convergence. It is not. **The manual
oscillates**: it gains a pixel, loses it again, and settles back where it
started. Over four rewrites and $6.32 the responsibility failure is exactly
where it began.

That is the real result of this run and it is worth more than a tidier one. The
mechanism is visible in the manual itself: the desk knows *why* those pixels are
unexplained — `theorem colour_nine_collision` says colour 9 paints at least
three distinct things and this arm binds one colour to one object — so the
defect is not one the desk can fix by rewriting. Each round it re-derives the
same diagnosis, rewords the manual around it, and the count returns.

**A loop that re-theorizes against a defect its language cannot express will
cycle, not converge**, and it will spend a model call per cycle doing it. The
four rounds cost $5.00 to establish that. Two changes follow, neither of which
is in this run: the evidence gate is now quantitative, so the desk is not
called until there is materially more world to look at (`inner/loop.py`); and
`E-03` — one colour, one object — is now the top of the expressivity ledger,
because it is the thing standing between this manual and a green
responsibility check.

The number itself is the win here: constraint 2's responsibility pass produced
a real, moving quantity on a real frame, and that quantity was able to say
"you are going in circles". A framework whose checks can only say pass or fail
could not have.

### What the desk got right before certify ran

The manual carries `theorem colour_nine_collision`, in which the desk works out
that colour 9 paints at least three distinct things on this board, that this
arm binds one colour to one object, that the surplus colour-9 pixels will
therefore have no owner — and says so, explicitly, *before* certify reported
the 69. A manual that predicts its own certify failure is a better artefact
than one that passes quietly. Full text and three more like it in
`THEORIZE_LOG.md`.

### Why it stopped

Stopped from outside at a natural close-out point, with 102 actions and ~$10 of
its ceiling unspent. The binding constraint was neither: it was that one turn
costs about seventeen minutes, nearly all of it in a single `claude -p` call
that returns 46,000 output tokens. `inner/loop.py`'s evidence gate is now
quantitative (four new transitions per desk call rather than one) for exactly
this reason, but that change postdates this run and did not affect it.

Because the run was stopped rather than finishing, it never reached
`_finish()`, so `certify.json`, `plan.json` and `turns.json` were never written.
They are reconstructed in `certify_reconstructed.json` by re-running certify and
plan against the archived books and the ledger-rebuilt trace — deterministic,
zero model calls, and **labelled a reconstruction** rather than passed off as
the live report. `run.json` is likewise rebuilt and flagged.

### The confound, stated before the numbers

`INC-TA-001`: another Claude Code session ran a `baseline-arms` `bare_cc`
campaign **on this same game** for the whole of this run — its shard ledger and
this arm's ledger were both being written at `01:28Z`. Every wall-clock and
HTTP-amplification number from this run is therefore an upper bound on this
arm's own cost and not a measurement of it. It may not be compared with
`baseline-arms`' 5.07× or `arc-recon`'s 2.5–10× without that caveat. Neither
session could see the joint total; each gate counted only its own.

### What the engines said on first contact

The dispatch ran before any model call, on 6 states (RESET + one of each legal
action), and three of its results are findings in their own right:

* **The concept account went negative.** `mdl_segmenter`'s six object
  hypotheses carry `gain_bits: -5042`, `ratio 3.55` — the segmentation costs
  more than encoding the pixels raw. A0's Cart earned +2967 on the same
  accounting. On a real 64×64 frame with six states, `Theoria.md` §1.8's ticket
  of admission ("a concept earns its place by making the manual shorter") is
  not merely unmet, it is inverted.
* **One track is not an object.** `obj3` is a 50×38 blob of 1006 cells with
  `color: None` — the segmenter merged the level's structure into a single
  track. This is the degradation the background choice was documented to
  produce, and it produced it: loudly and visibly, which is what was wanted.
* **`zero_space` returned 70 "global laws" from 6 states.** They are
  numerically true and epistemically empty: with a handful of transitions
  constraining a few hundred features, the null space is nearly everything, so
  almost any vector is a "law". A0 read its two laws off 275 transitions. The
  arm now computes this explicitly — `evidence_adequacy.verdict` says `THIN`
  with the rank and the dimension — and hands the verdict to the desk with the
  laws, so a correlation cannot be mistaken for a conservation law.
* **`cegis_miner` emitted nothing.** Its precondition (exactly one `move` event
  per transition) is a claim about the world, and this world does not satisfy
  it. Recorded per track as a refusal, never worked around (D-P8-006).
