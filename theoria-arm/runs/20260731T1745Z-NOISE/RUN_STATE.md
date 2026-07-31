# RUN_STATE — 20260731T1745Z-NOISE

## What was asked

Before any Phase-3 round can be believed, measure the noise floor: how far apart
do two identical legs land when nothing changed? `Theoria.md:336` forbids
deciding on one leg's difference, and that rule is unusable without a variance
envelope.

## What happened, in order

1. Ran the documented rehearsal (`python -m harness.campaign --mock --pool …
   --out-dir …`) once, to see what it does. It ran for five seconds, played one
   leg, and then failed legs 2 and 3 with `FileNotFoundError: no theory.dsl
   carried in from …/books`.

2. Traced why. `--mock` without `--desk` sets `offline=True`;
   `inner/loop.py:856` skips theorize entirely; no manual is written; the carry
   into leg 2 correctly refuses an empty manual; three zero-progress legs end
   the campaign before games 2–4 are ever reached. Everything downstream of the
   desk — the seven surprise counts, theorize rounds, certify rounds, engine
   dispatches, desk calls — is unreachable in that mode. Measuring only it
   would have produced a table of confident zeros about machinery the campaign
   never ran.

3. Built `armtools/noise_floor.py` with two modes. `cli` repeats the documented
   command as a subprocess. `stub-desk` runs the same `Campaign` in-process
   with `ModelDesk._invoke` replaced by a canned envelope whose reply is a real
   archived desk answer replayed — `runs/20260731T1430Z-A3-level2-carried-r3`'s
   two books, wrapped in the `=== THEORY === / === PLAYBOOK === / === LOG ===`
   blocks `inner/theorize.py:BLOCK` parses. That holds the desk exactly constant
   while the engines, the compilers, certify, plan, probe and the replay checker
   all run for real.

   Chose in-process patching over putting a fake `claude.cmd` on PATH. The PATH
   route has one failure mode — the shim not being found first — whose
   consequence is a live model call. The in-process route cannot reach a
   subprocess at all.

4. Wired the negative control. `install_stub_desk(None)` installs a `claude_bin`
   that raises and nothing else, and `--negative-control` runs a whole leg under
   it. The first draft reported `refused: false`: the guard *had* fired, but
   `inner/loop.py` catches a raising desk and files it under `desk_failures`
   rather than letting it escape, so nothing about it reached `campaign.json`.
   Fixed the control to look where the evidence actually is. This is the reason
   the control exists.

5. Ran 12 repetitions of each mode, read the columns, swept the leg directories
   out of `runs/`, and diffed the artefacts. All twenty-one columns: spread 0.
   The variation audit found the interesting thing — `curves.json` differs
   between repetitions in the *turn* a surprise is filed under.

6. Chased it to `armtools/archive.py:491–497`: surprises join to turns by
   wall-clock containment, `Surprise.ts` is truncated to the second, turn edges
   are millisecond ledger stamps, so any turn shorter than a second is a coin
   toss. The reduction counts this
   (`join.surprises_within_1s_of_a_turn_boundary`) and calls the join `exact`
   in the same object. Checked the live archive: the largest live leg carrying
   a `turn_series.json` reports 22 of 39 surprises ambiguous and
   `join_confidence: "exact"`. Checked the next hop:
   `armtools/curves.py:257` carries `join_confidence` into `curves.json` and
   drops the ambiguity count, and `curves.json` is what the figure pipeline
   reads.

7. Ran a second, independent set of 12+12 to see whether the placement effect
   replicates. It does: off-mode fraction 0.25 then 0.3125, max displacement 2
   rows in both, every leg ordinal affected. The two sets' *columns* are
   identical to the count.

## Deliverables

* `NOISE_FLOOR.md` — the measurement, the rule, the gaps.
* `noise-cli.json`, `noise-stub-desk.json` — set 2, with the placement histogram.
* `noise-cli-set1.json`, `noise-stub-desk-set1.json` — set 1.
* `negative_control.json` — the guard refusing.
* `MANIFEST.json` — provenance, per-file sha256, and the code files' sha256.
* `../../armtools/noise_floor.py` — the reusable instrument.
* `../../tests/test_noise_floor.py` — 9 tests, including the audit's own
  negative control (a normaliser that hid everything would make every
  repetition look identical forever).

## Cost

$0.00. No ARC contact, no model call, no network. The only pool touched was a
scratch spend-gate ledger in a temp directory. 48 campaigns, about 7 minutes of
wall clock in total including both sets.

## Not done

Nothing was fixed. The surprise→turn join is reported, not repaired: the change
would move numbers in every archived `curves.json` and that is a decision with a
downstream blast radius, not a patch to slip into a measurement run.

`Campaign` still has no `--runs-root`, so the next rehearsal will fill the
tracked archive again; this run's instrument sweeps only after itself.
