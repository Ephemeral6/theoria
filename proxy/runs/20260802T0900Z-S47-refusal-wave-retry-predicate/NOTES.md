# S47 — running notes

Written as the work happens. The disk is the memory; a session's context is not.

| | |
|---|---|
| prompt_id | `S47-refusal-wave-retry-predicate` |
| branch | `agent/s47-refusal-wave-retry-predicate` |
| base commit | `1e5b3f00dfb40fcc73f582a5de2390d1d3466844` |
| worker | `W-9203` |
| started | `2026-08-02T09:00:45Z` |
| spend | **$0.00** — offline throughout, zero API calls, zero sockets outside loopback tests |

## Baseline before anything changed

`cd proxy && python -m pytest` → **497 passed** in 128s, at `1e5b3f00`.

## The ask, restated

`proxy/forward.py:27-30` asserts that a non-429 4xx is the upstream telling the
truth, so it is never retried. For one response that premise is false: `400` +
`error: SERVER_ERROR` + `message: "game <id> not found"` is the upstream's own
transient, and the byte-identical retry succeeds. Because `forward()` will not
retry it, the retry happens one layer up in `theoria-arm/harness/arc.py`, where
each attempt is a fresh request through the proxy and therefore a fresh
`env_step` row — 570 outbound rows bought 72 actions across the four
2026-07-31 legs.

Item 1 of `monitor/inbox/20260801T0400Z-theoria-arm-to-proxy-refusal-wave.md`
only. Items 2 (`step_idx` numbers attempts) and 3 (a closed recording gap) are
explicitly out of scope and are not touched.

## Design decision taken up front

`forward.py`'s first docstring line is "Nothing here knows about ARC or about
model providers." A predicate that matches an ARC game id inside a JSON body
would end that. So the layering is kept: `forward()` gains a keyword-only,
defaulted **caller-supplied** body predicate, and the ARC knowledge — the
`SERVER_ERROR` name, the anchored `game <id> not found` regex, the id-identity
check — lives in `env_proxy.py`, which is the ARC-shaped half. `model_proxy`
passes nothing and is byte-for-byte unchanged.

Recorded as `D-S47-001`.

## What landed, in order

1. `forward.py` — keyword-only `retry_body: Optional[RetryBody] = None`, consulted
   only for `status >= 400` that `RETRY_STATUSES` already declined. An attempt it
   authorises is marked `body_retry` in `attempt_log`.
2. `env_proxy.py` — `ARC_TRANSIENT_ERROR`, `ARC_GAME_NOT_FOUND`,
   `game_not_found_retry(game_id)`; threaded through `_forward` and supplied by
   `_command` only. `_meta` (scorecard, game list) passes nothing.
3. `tests/test_forward_retry_predicate.py` — 25 tests, plus 14 for the replay.
   Suite **497 → 536**, green. Mutation-measured: 7 of the 25 fail if `forward()`
   is made to ignore `retry_body`; the rest are negative controls, which pass on
   master by design and are required by the acceptance line.
4. `DECISIONS.md` `D-S47-001`; `CONTRACT_CHANGES.md` `C-009`; `LEDGER_FORMAT.md`
   `http` row names `body_retry`; `README.md` layout table gains `forward.py`,
   which had never been listed.
5. `monitor/inbox/20260802T0930Z-W-9203-proxy-to-theoria-arm-s47-landed-retry-is-now-nested.md`

## A hazard the tests found, not the design

The first draft consulted the predicate on **every** terminal status, including
the `200` that ends a successful retry. `test_the_predicate_is_asked_about_
nothing_but_declined_errors` installs a predicate that answers `True`
unconditionally and caught it: `forward()` would have discarded a response the
pool had already paid for and gone to buy another one. Hence the `>= 400` floor,
which also keeps a refused redirect out of the hook's reach (RED-01).

Worth stating because the design review would not have caught it. The test was
written to pin "the hook can widen, never narrow"; the upper bound was the half
nobody was looking at.

## The measurement

`python -m proxy.tools.refusal_replay --verify` over the four legs, at
`max_attempts=5`, offline: **570 → 149 `env_step` rows (73.9% fewer), sockets
570 → 570, `actions_agree` true before and after on all four legs**, verdict
PASS, all four invariants held. Archived as `refusal_replay.json`.

149 rather than the idealised 76, because the replay models `forward()`'s
*bounded* loop: 73 of the 149 rows exist because the 5-attempt budget ran out
while the predicate still wanted to retry, and the arm then retries. Pooled row
count by budget: 1→570, 2→303, 3→219, 4→170, **5→149**, 6→134, 8→112, 10→104,
16→83.

`python -m proxy.tools.contract --fingerprint` is byte-identical on this branch
and on master (`sha256:574a3dbf…`), which is the empirical form of C-009's claim
that §4's detector cannot see this change.

## Three bugs in my own verify script, found by running it

Worth recording, because all three would have produced a *green* gate that
proved less than it claimed if they had failed in the other direction:

1. The network check grepped for `requests\.` over the source and matched the
   docstring phrase "outbound requests." — a gate that cries wolf at its own
   prose is one people learn to ignore. Replaced with an `ast` walk over the
   module's actual imports.
2. The territory check diffed against `master`, and master **advanced** while
   this ticket was being written (`1e5b3f00` → `9e478dd8`, C15 and V30 landing
   in `theory-compiler/`). It reported another cell's landed work as this
   branch's strays. Now diffs the merge base, which is the question actually
   being asked.
3. `refusal_replay.json` embeds the `--leg` paths it was invoked with, so the
   first archived copy did not reproduce under the script's own canonical
   invocation. Regenerated from the repository root; the byte-comparison in the
   gate now passes and pins the invocation as part of the artefact.
4. **The credential red line was a no-op, and it printed a pass.** `.env` lives
   at the *main* checkout's root and is gitignored, so a worktree has none; the
   check found no file, printed "nothing to leak into a file", and went green —
   passing precisely because it could not find the thing it guards. It now
   resolves the main checkout through `git rev-parse --git-common-dir`, and
   **fails when it finds no secret**, because "I found no secret" and "no secret
   leaked" are different sentences and only one is evidence. It now loads 1
   secret and scans 13,086 tracked files: zero hits.

**The fourth is a rediscovery, not a new class, and the correction is to say so.**
`release/verify.sh:60-68` had already met this exact shape and written it up —
"a check that skipped itself while reporting on the skip" — and had already
landed the right answer: ask `arc-recon/client.load_api_key()` whether a key is
*reachable*, rather than asking the filesystem whether a file is *beside you*.
This check now does that too, which is also what `CLAUDE.md` instructs ("prefer
the shared reader over parsing `.env` yourself") and which additionally covers a
key supplied through the environment rather than a file.

A grep over every `verify*` script in the repo found **no other instance** of the
`exists(".env")`-then-skip shape, so no inbox note went out: the claim "every
worker's gate has this hole" was mine to check before making, and it is not
true.

## Gates

`cd proxy && python -m pytest` → **518 passed** (baseline 497 + 21 new).

`bash verify_contract.sh` → **9 of 9 contract steps ok**, including "canon.describe()
still matches proxy/canon_contract.json" and "the fingerprint an importing track
pins is printable". That is the empirical form of C-009's claim that §4's
detector cannot see this change: the pin did not move, so the ledger row *is*
the announcement.

Its tenth step, "the whole proxy suite", is **red — and red on master too**, for
a reason that has nothing to do with S47. That step runs `python -m pytest proxy
-q` from the repo root, where the repo-root `tools/` package shadows
`proxy/tools`, so `tests/test_audit_delivery.py`'s `from tools import
audit_delivery` fails at collection. Reproduced identically at `1e5b3f00` in the
main checkout before touching anything. It is `proxy` territory and it is a real
defect, but it is a different one with a different cause; left for a ticket that
owns it rather than folded in here. `cd proxy && python -m pytest` — the
invocation `pytest.ini` is written for, and the one `verify.py` rung 1 uses — is
green.

## The gap this does not close, stated before anyone asks

The retry is now **nested**. `theoria-arm/harness/arc.py:_retryable` still
retries a `400`-not-found up to 40 times, and each is now up to 5 attempts inside
the proxy. On the transient this is close to cost-neutral — the arm only
re-enters on a non-200, so the same requests happen, regrouped. On a
**permanently** failing id the worst case goes from 40 sockets to 200.

The pool ceiling is unaffected (`permit.check()` before every socket, the
reservation's action cap unchanged); the rate of approach to a run's own cap is
up to 5× on that path. `arc.py` is `theoria-arm`'s file. Recommendation filed to
`monitor/inbox/`, not acted on.
