# V22 — `win_tighten`: absent score vs. score below the floor

Narrative. The machine-readable half is `MANIFEST.json`; the criteria are
`PREREGISTRATION.md`, committed at `4fa378de` before any of this ran.

## What was wrong

`exam/SEALED_DRILL.md` §4. `proxy/variants.py::VariantRuntime.after` tested
`if have is None or have < needed`. A worldgen trace carries no score, so
`have` was always `None` and every `WIN` became `NOT_FINISHED` at every
`require` value. `win_tighten` was not tightening the win condition on such a
game; it was removing it. The reading itself is the safe one — the other
direction hands a scoreless game the tightened win outright — so what needed
fixing was the silence, not the direction.

## What was done

**The record splits.** `applied` now carries `reason` (`score_absent` /
`score_below`), `degenerate`, `occurrence`, and `note` on the first
absent-driven rewrite of a session. `VariantRuntime.degenerate_wins` and
`.first_degenerate` hold the session's view.

**Of refuse / warn / the bit, the bit was chosen.** Reasons in `DECISIONS.md`
D-032, in one line each: refusing inside `after()` is D-030's exact mistake —
the response is already paid for, so a refusal there destroys evidence rather
than preventing anything; a warning is not in the artefact, and the artefact is
what gets read six weeks later; the bit is in the ledger, hashes into the
chain, replays, and can be given readers.

**It was given two readers, because a bit nobody reads is decoration (D-031).**
`env_proxy` writes one `variant_degenerate` incident per session (new incident
kind, contract change C-006, classified `additive` by
`tools/contract.py`). `tools/check_variant_degeneracy.py` reads any ledger and
exits 2. `verify.py` gains rung 5, which plays a game built to trip the guard,
requires a refusal, strips the markers from that same ledger and requires a
pass.

**The negative control runs on two whole sessions, both falsified.** Raw output
in the four `evidence-*.txt` files:

| stream | markers | guard | exit |
|---|---|---|---|
| scoreless session (`score: null` throughout) | 33 | REFUSED | 2 |
| the same stream, `degenerate` stripped from 33 records | 0 | PASS | 0 |
| scoring session, floor 99, `win_tighten` fires for a real shortfall | 0 | PASS | 0 |
| the same stream, one `degenerate` forged in | 1 | REFUSED | 2 |

Rows 1–2 show the marker is what catches it: the guard reads the marker and
nothing else, and deliberately does not re-derive degeneracy from `score:
null`. Rows 3–4 show the PASS on a scoring session is a fact about the input
and not a guard that cannot fire there.

The scoreless session is a real run through both proxies against
`MockArc(scoreless=True)` — a new opt-in mode on the mock, off by default — not
a hand-built response body. The claim is about what a session leaves in a
ledger and a synthetic body cannot demonstrate that.

**Item 3: no fourth certificate form; rule R-V22 instead.** Argument in D-032.
Short version: the three frozen forms are arguments about the world, and "this
game reports no score" is a fact about the protocol; a fourth form would let a
certificate earn reason-credit for restating a property of the measuring
instrument, and would make the degenerate construction a *legitimate* exam
item. So the class is excluded instead: a `win_tighten` variant whose run
produced any degenerate rewrite does not count toward the reason score. The
enforceable half that lives on this side of the territory boundary is
`check_variant_degeneracy.py --json` reporting `exam_eligible: false` and
exiting 2, plus rung 5 keeping the detector honest. The half `proxy/` cannot
do — making `exam/`'s rubric subtract the item — is named as owed rather than
claimed.

## Two things found on the way that are not this ticket

**The mutation harness's first run was worthless and said the opposite.** It
reported 25 kills out of 25. Every one was false: the harness copied `proxy/`
into a temp tree but not `arc-recon/data/piles.json`, which `proxy/paths.py`
resolves against the repo root and `guard.py` opens on every command, so every
test errored at setup and every mutant looked killed. The fix is the file copy
plus `BASELINE` (`M00`), a no-op "mutation" that must survive; if the control
does not pass, the harness writes `harness-invalid` and refuses to report kill
counts. Recorded here rather than quietly re-run, because a clean sweep from a
harness with no control is exactly the failure this exercise exists to detect,
and it happened to the exercise itself.

**`proxy/redact.py` corrupts ledger field names after any short forced
secret.** `redact.VAULT` is process-global and never cleared; `scrub` scrubs
dictionary keys as well as values (RED-17); `register(force=True)` ignores the
length floor (RED-14). `tests/test_spend_gate.py` builds an
`EnvProxyConfig(api_key="k")`, so every ledger written later in the same pytest
process has `kind` written as `<redacted>ind`. It is why two incident
assertions here passed alone and failed in suite order. Worked around in
`_vault_without_toy_secrets` — which drops only sub-`MIN_SECRET_LEN` entries,
so every real credential stays registered — and filed as its own ticket rather
than fixed under one about `win_tighten`. RED-14's own justification ("the
operator chose a short one") is the case where this would corrupt a live
ledger.

## For Phase 4

Whether a sealed game reports a score is a **protocol** question, not a
mechanics question, and is answerable without breaking the seal. Answer it
before using `win_tighten` against a sealed game. The incident this ticket adds
is the backstop for having failed to, not a substitute for doing it.
