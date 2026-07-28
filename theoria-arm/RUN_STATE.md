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

## `20260728T012311Z-g50t-first-contact` — the first online contact

**Purpose.** P-8: connect the inner loop, proved four times offline
(`a0-spike`, `cold-start-a0`, A1, `cold-start-a2`), to a real environment
through the double proxy. The goal is not to win — it is that the loop turns
online and the books balance.

**Settings.** `g50t-5849a774`, 120 successful actions, 3000 HTTP commands,
`claude-opus-5` at the desk, $20 ceiling, 9000s wall clock, no variant.

**Status: see `runs/20260728T012311Z-g50t-first-contact/MANIFEST.json`.** The
section below is filled from that file when the run closes; until then
`RUN_STATE.json` in the run directory is the live counter.

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
