# P12 — why four legs and ~$35 completed zero levels

Offline throughout. No key, no network, no model call, no ARC action, zero
sealed-pile contact. The four legs under diagnosis are read-only inputs.

## What the legs actually did

| leg | actions | of which probes | committed | $ | levels |
|---|---|---|---|---|---|
| `20260731T1240Z-A3-level2-carried` | 5 | 0 | 0 | 0.00 | 0 |
| `20260731T1310Z-A3-level2-carried-r2` | 13 | 8 | 0 | 9.56 | 0 |
| `20260731T1430Z-A3-level2-carried-r3` | 33 | 28 | 0 | 13.44 | 0 |
| `20260731T1500Z-A3-sk48-carried-l1` | 21 | 16 | 0 | 12.25 | 0 |

Every leg ended `spend_gate_tripped` on `RESERVATION_USD_CAP`, not on the action
budget: r3 stopped with 267 of 300 actions unspent.

## Three mechanisms, in the order they matter

**1. The arm never tried to win.** `runs/…-r3/plan.json` holds 29 records and
all 29 read `status: "no_goal_declared"` — "the manual states no winning
condition, so `is_goal` is `False` everywhere". `inner/loop.py:_main_loop` only
calls `_commit` when `plan_report["status"] == "sat"`, so `commit` was never
entered on any leg. Every action spent was an opening-sweep action or a probe.
`inner/plan.py:surprises_from` fired only on `search_timeout`, so across 22 desk
calls costing $35.25 the model was never told that its playbook declares no goal.
The carried manual even contains a theorem named
`the_goal_section_is_empty_on_purpose` — the desk decided this deliberately and
nothing in the loop ever argued back.

**2. Every probe was measured wrong.** In r3, 28 of 28 resolved probes came back
`survived: []` — the observed grid hash matched no hypothesis: not the manual,
not any of its 14–22 single-rule ablations, not even `inert` ("nothing happens").
A posterior over an empty set is not a posterior. Pooled over all four legs,
52 resolved probes claimed **43.167 bits** by design and realised **2.714** —
6.3%. 47 of the 52 (90.4%) were vacuous. The design's `entropy_bits` measures
disagreement *among the hypotheses*; nothing measured what the answer eliminated.

**3. Nothing noticed the arm was going in circles.** `…-l1/trace.jsonl` shows
the last fourteen actions alternating ACTION4/ACTION3 and repeatedly returning to
states already visited (15 distinct states in 22 steps). In r3, P-25 and P-27
are byte-identical designs, as are P-26 and P-28 — four actions, two questions.
Pooled: 56 designed probes, **38 distinct experiments**.

Cost shape, from `desk_log.json`: r3's 8 calls averaged 49,448 output tokens and
41,298 cache-creation tokens with `cache_read_input_tokens: 0` on every single
call. Output tokens are roughly 80% of the bill, and the desk rewrites the whole
of `theory.dsl` each time (33k → 51k chars over the leg). The 4-turn cadence is
`MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4` against one probe per turn — the shape of
the entire run was set by a constant, not by evidence.

## What changed

* `inner/probe.py` — `information_gain_bits()` (realised bits, uniform prior,
  vacuous case returns 0.0 and says so rather than `log2(n/0)`); `fingerprint()`
  (action + every hypothesis's prediction = the identity of an experiment);
  result rows gain `information_gain_bits`, `expected_bits`, `n_survivors`,
  `frontier_vacuous`, `vacuous_streak`; design rows gain `fingerprint` and
  `repeat_of`; the vacuous verdict stops saying only "THE MANUAL WAS WRONG".
* `inner/plan.py` — `no_goal_declared` fires `heuristic_miss` (computational
  family → `playbook.dsl`, which is where the goal is missing). No eighth
  surprise kind: `Theoria.md` 1.10(d) fixes the seven. Fired once per playbook
  revision, not once per turn.
* `inner/loop.py` — three refusals before an action is spent on a probe:
  `MAX_VACUOUS_PROBES_IN_A_ROW = 3`, a repeat of an experiment already asked,
  and `MAX_PROBES_BETWEEN_THEORIZE = 4`. Each is written to `probes.jsonl` as an
  `unrunnable` row and falls through to least-tried-action exploration. Both
  counters are re-armed by a theorize round. The `probe_refutation` payload sent
  to the desk drops the table of 16–24 opaque grid hashes and carries the shape
  instead.

## The measurement

`replay_live_probes.py` replays the four legs' own `probes.jsonl` through the new
code — same world responses, same order. Result in `probe_replay.json`:
**31 of 52 probes kept, 21 refused (16 repeats, 5 vacuous-streak)**, a 40%
reduction in probe actions, all of them redirected to least-tried exploration.

## Honest gap: the specified mock campaign cannot see any of this

`python -m harness.campaign --mock --pool <tmp>/pool.jsonl --out-dir <tmp>/out`
produces **byte-identical results before and after this change** — one leg of 41
steps, 0 probes, all seven surprise counts 0, 0 theorize rounds, then three
carry failures. `mock_campaign_before.json` / `mock_campaign_after.json` are both
archived here.

That is not a null result, it is a blind instrument. `--mock` implies
`offline=True`; offline skips theorize; no theorize means no `theory.dsl`; no
manual means `books.load_predictor()` returns an error; and `_probe_or_explore`
with `namespace=None` never designs a probe and never reaches `plan`. **No
pre-flight this arm owns can exercise the probe, plan or commit beats.** Every
one of today's three failure modes was unreachable offline, which is why $35
bought the discovery. Closing that is the next item and is out of this ticket's
scope; a mock leg seeded with a carried manual gets closer, but the mock world
(8×8, 2 dynamic cells, 2 distinct states) is too small for the carried g50t
manual to compile against — `ParseError: Line 130: Expected 'goal' statement`.

## Gates

`python -m pytest -q` — **2 failed, 479 passed in 862.41s**. All 33 new tests
pass. Both failures reproduce **identically on an untouched worktree of
master**, cut and checked separately for this report:

* `tests/test_arm.py::test_the_archive_stays_accountable` and
  `python -m armtools.verify_provenance` check 8 — `drifted: [the four
  2026-07-31 legs]`. The drifting field is `env_proxy.log`'s sha256 in each
  leg's `MANIFEST.json`. The live runs wrote that log with platform line
  endings and the manifest hashed it as written; `theoria-arm/.gitattributes`
  pins `* text eol=lf`, so git stores it normalised and **any fresh clone or
  worktree gets bytes the manifest can never reproduce**. Measured: the
  manifest and the main tree agree (`050499536a38`, 440 bytes for r3); a clean
  master worktree and this branch's worktree agree with each other and not with
  the manifest (`4bb01cad2a62`, 436 bytes). Nothing in this branch touches any
  file under a leg directory. Not fixed here: the certain repair is to
  re-derive four archived legs' manifests, which is a deliberate act on another
  ticket's artefacts, not a side effect of a probe-economics branch — and master
  moved from `73760dc8` to `21a724ed` while this ran.
* `tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive` —
  `claude-opus-5: the recorded rate $0.0030474/s is below the worst rate in the
  archive, $0.0042222/s`. `harness/spend.py:OBSERVED_USD_PER_SECOND` has not
  kept up with the legs that landed on 2026-07-31. Untouched by this branch and
  failing the same way on master.

`python verify.py` — `theoria-arm: RED (1 problem(s))`, and the one problem is
the pytest step above. Its other two steps pass: `[2/3] one real run — the whole
arm, offline against proxy/mock … ok, game g50t-5849a774, budget 6 actions, no
key, no network`, and `[3/3] artefact self-check`.

`python -m armtools.verify_provenance` — 9 of 10 PASS, the tenth as above.
Notably PASS: *no sealed-pile game appears anywhere in the archive*, and *runs/
contains no test or smoke fixture* (the seven mock leg directories this ticket
produced were deleted rather than left behind).

## Other gaps, stated and not fixed

* **`cache_read_input_tokens` is 0 on 21 of 22 live desk calls.** The prompt is
  rebuilt each call and grows monotonically (35k → 47k tokens), so every call
  pays the 1h cache-write premium and no call ever reads the cache. Roughly 20%
  of the bill. Fixing it means restructuring the theorize prompt so the stable
  prefix comes first, which is a change to `inner/theorize.py` whose effect
  cannot be verified without spending — deliberately not attempted.
* **The desk rewrites both books in full every call** (~48k output tokens,
  ~80% of the bill). A diff-shaped protocol is the obvious lever and is a much
  larger change than "cheap and certain".
* **`_roll_forward` is a pure simulation that is never re-anchored** to the
  observed frame, so every probe's pre-state is the manual's opinion of where
  the world is. Whether that is a defect depends on `certify`'s replay claim
  (which reported `29/29 transitions replay exactly` on the same leg where every
  probe was refuted). Those two claims are in tension and one of them is
  measuring something other than what its name says. Not resolved here — it
  needs a controlled world to settle, and guessing would be worse than saying so.
* **The three new constants (3, 4, 4) are judgement, not measurement.** They are
  bounds on waste, chosen so the observed pathologies would have been caught
  early; no run has yet shown what the optimal values are.
