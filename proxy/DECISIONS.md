# `/proxy/` — design calls and their reasons

## D-001 · The format document was written before any code

`LEDGER_FORMAT.md` is normative and dated ahead of `ledger.py`. The ticket
asked for it in that order and the order matters: the ledger is the shared
surface for three arms and the Phase 2 metric battery, and a format that
emerges from one implementation encodes that implementation's accidents. Where
the two ever disagree, the document is right and the code is a bug.

## D-002 · Two event shapes, and auxiliaries kept out of them

`env_step` and `model_call` stay exactly two shapes. Everything else the
proxies observe — scorecard traffic, the game list, guard refusals, incidents —
goes to `run_start` / `run_end` / `env_meta` / `guard_block` / `incident` under
the same envelope. The battery reads two shapes without branching, which is the
whole point of a shared format; the alternative was optional fields on
`env_step` that mean "this is not really a step".

`baseline-arms/harness/ledger.py` reached the same conclusion independently
(its D-003) and sent diagnostics to a separate file. v1.0 keeps them in the
same file but under distinct `event` values, so a single stream stays ordered
by `seq` — ordering that a second file would lose.

## D-003 · A refusal is a record, not an absence

A command the guard denies, or a variant declines to forward, is written as a
full `env_step` with `frames: null` and `guard.decision: "deny"`. Recording
only what succeeded would make "the arm never tried" and "the arm tried and was
stopped" indistinguishable in the ledger — and the second is exactly the
evidence a sealing claim rests on.

## D-004 · No dollar figure is ever written to the ledger

`model_call` carries the provider's `usage` verbatim plus a `pricing_ref`
naming a hashed price table. Cost is computed on demand by `cost.py`. An
append-only file that recorded dollars would be wrong the day a price changed
and could not be corrected; with the conversion outside, a price change
re-prices history instead of contradicting it. `RunLedger.model_call` raises if
a caller passes `cost` or `cost_usd`, so this cannot be eroded by convenience.

## D-005 · Usage is copied through, never reshaped

Whatever keys the provider emits are the keys in the ledger. No renaming, no
summing, no normalising across providers. A normalised usage block is a
derived quantity wearing a recorded quantity's clothes, and the derivation
would be invisible at read time. The one exception is documented and narrow:
for a streamed response the proxy merges the `message_start` and
`message_delta` usage objects, which is a merge of the provider's own keys.

## D-006 · The guard is at the proxy, and it fails closed

The sealed-pile rule was previously enforced by every caller checking. Here an
arm's only route to the environment refuses before the upstream socket opens,
and the arm has no credential with which to go elsewhere — so the cut is
enforced by construction.

Three sub-calls:

* **The data source is `arc-recon/data/piles.json` itself**, not a copy. A copy
  is a second thing to keep in sync, and the failure mode of that drift is
  silently playing a sealed game.
* **Integrity is verified on load** against the digest the cut recorded. A
  silently edited cut raises instead of quietly widening what is reachable.
* **An id in neither pile is denied by default.** The cut covers the 25 public
  games; anything outside it is not something Phase 1 authorised. Widening
  should be a deliberate, recorded act rather than a shrug.

The guard reads the *whole* request for game ids — path, query and every string
in the body — not just `body["game_id"]`. A guard that only checked the field
it expected would be a guard by convention again.

## D-007 · The variant library is limited to what a wrapper can actually do

`forbid_action`, `remap_action`, `step_limit`, `observation_loss`,
`win_tighten` — and `Variant.load` rejects anything else rather than accepting
it and failing later. The environment is hosted; a wrapper cannot change server
internal dynamics, so an operator outside this set would be a claim we could
not honour. The set is small and sufficient: forbidding the only action that
crosses a gap, or declaring a loss on the only cell a path must traverse,
constructs unsolvability that follows from the construction.

**Every spec must carry a constructive justification**, and the loader enforces
it. An exam needs ground truth and ground truth comes from construction, not
from running the variant and seeing what happened. The shipped set is
deliberately three unsolvable plus one solvable: with only unsolvable questions,
"I failed" and "it was impossible" score identically.

## D-008 · `observation_loss` reads the last frame of a command

One command can return several frames. The predicate is evaluated against the
last one — the observation the arm actually acts from. Evaluating it against
intermediate frames would make a variant's behaviour depend on animation
timing, which is exactly the kind of hidden dependency that makes a truth claim
unfalsifiable. The consequence is a real obligation on the spec author, and
`v003`'s justification discharges it explicitly: it argues that neither
declared cell is ever a transient position.

## D-009 · Level boundaries are derived but recorded

`level` and `level_boundary` break the otherwise clean recorded/derived split
(D-004). Two reasons: `level` is not an API field so it must be derived from
score jumps at all, and the derivation needs the live step sequence, which the
proxy has and a later reader would have to reconstruct. The rule that makes
this safe is that a derived-and-recorded field must be recomputable from the
same file — and `reconcile.py` recomputes both and fails if they disagree.

## D-010 · The replay opens its own probe scorecard

A prefix replay is real traffic: it consumes actions and would add to a
scorecard. It therefore opens a separate card marked as a probe, and runs under
its own `run_id` with `arm: "replay"`. Otherwise re-running a game would
silently change the score the reconciler is checking against — the measurement
would alter the thing measured.

## D-011 · The mock world is a fixture, and its solver is too

The stand-in provider is a breadth-first search, not a language model. A
stochastic decider would make the end-to-end run unreproducible, and replay
would fail for reasons that have nothing to do with the harness. Calling it a
model would be the dishonest version; it is a fixture that produces a
deterministic action from a frame.

The mock's transition rule lives in one function (`arc_mock.slide`) that both
the world and the solver import. Two copies would eventually disagree, and the
disagreement would present as the environment being non-deterministic.

The world **requires the credential**: every gameplay route answers 401 without
a valid `X-API-Key`. That is what makes the seal test a proof rather than an
assertion — `tests/test_seal.py` sends the byte-identical request twice, once
directly (401) and once through the proxy (200), and the only difference is the
injected key.

## D-012 · Streaming is buffered before it is answered

The model proxy reads a streamed response to completion, extracts usage and the
assembled message, records both, then hands the original bytes to the arm. The
recording obligation is absolute and incremental delivery is not needed by
anything in Phase 1, so the simple thing wins. It is a real limitation and it
is in the README, not buried here: an arm that renders tokens as they arrive
will see them arrive at once.

## D-013 · An arm that can see a credential refuses to start

`arm_mock.assert_sealed()` raises if any known credential variable is set in
the arm's environment. A run in which the arm *could* have gone around the
proxies demonstrates nothing about a run in which it didn't, so the arm-side
half of the sealing property is checked at startup rather than assumed. The
proxy-side half is separate: an arm that sends a credential header has it
stripped, and a `bypass_attempt` incident is recorded.

## D-014 · Everything a test asserts, it also proves can fail

The replay and reconciliation tests each have a companion that forges the
ledger and asserts the check goes red. A check that has never been observed to
fail is not evidence that anything passed.
