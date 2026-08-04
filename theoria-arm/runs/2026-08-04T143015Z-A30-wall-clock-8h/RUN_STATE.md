# A30 · RUN_STATE

Prompt: `(unset — owner instruction, 「把墙钟改成 8 小时」, 2026-08-04)` ·
branch `agent/a30-wall-clock-8h` · base `18e7d81b` · 2026-08-04.
Territory: `theoria-arm`. Run archive: `theoria-arm/runs/2026-08-04T143015Z-A30-wall-clock-8h`.

## Delivered

**1. The unattended wall clock is 8 h (was 3 h).** Why it was worth asking for:
A26 asks *given enough money, can the arm win once*, and g50t level 1 wants 78
actions. At the measured 11.2–20.7 actions/hour a 3 h ceiling tops out at 34–62,
so the money went up 4.8× while the clock did not move and the experiment could
not reach its own question — it would have recorded **"time ran out" as "money
could not win either"**.

**2. It was not a one-line change, because there were four copies.**
`inner/loop.py:69`, `harness/run.py:567`, `armtools/spend_check.py:251` and
`harness/spend.py:684` each carried their own `3 * 3600`; changing one leaves
three. `DEFAULT_WALL_CLOCK_S` now lives in `theoria-arm/harness/spend.py` and
the other three import it. The dependency direction permits this — `inner`
already imports `harness`, not the reverse — and a repo-wide grep confirmed the
constant had no external consumers before the move.

**3. A latent defect the change would otherwise have triggered, fixed with it.**
`TTL_MAX_S` was `8 * 3600` **exactly**, and the lease was
`max(TTL_MIN_S, min(TTL_MAX_S, wall_clock + TTL_MARGIN_S))`. At
`wall_clock == 8 h` the clamp eats the entire 900 s margin and returns a lease
expiring **at the same instant the run is told to stop** — while
`inner/loop.py:427` stops on `elapsed > wall_clock_s`, i.e. *after* exceeding,
so the last desk call can still be in flight against an expired lease. The
comment three lines above `TTL_MARGIN_S` already forbids exactly this: *"An
expired lease cannot be renewed, so the lease is sized to outlive the run rather
than to be rescued mid-flight."* **The comment and the constant contradicted
each other only once the wall clock reached `TTL_MAX_S`, which is why 3 h never
exposed it.** `TTL_MAX_S` is now 12 h, and the clamp is **loud**: a request that
cannot be honoured raises a named `ValueError` instead of quietly returning a
short lease. Measured at the new default: lease 29,700 s > wall clock 28,800 s.

**4. Four tests, one of which is the guard that was missing.** The existing
`test_the_lease_outlives_the_declared_wall_clock` passes `3 * 3600` as a
**literal**, so it stays green whatever the default becomes — it could not have
caught this. `test_the_lease_outlives_the_DEFAULT_wall_clock` binds to the
constant and asserts the margin survives *intact* rather than clamped. Plus the
refusal path and its twin (a wall clock that fits must still be honoured — a
refusal that fires on everything is not a check), and
`test_the_wall_clock_has_exactly_one_definition`, which asserts the agreement
rather than the value so raising the default stays a one-line change.

## Gaps — what the工单 asked for and did not get

**1. This does not make A26 conclusive, it only stops it being uninterpretable.**
78 actions at 11.2–20.7 actions/hour needs 3.8–7.0 h, so 8 h clears the median
but not the whole measured spread. If the next A26 leg still stops short, the
wall clock will no longer be the explanation — that is the whole point — but it
is not a guarantee of reaching 78.

**2. The in-flight A26b legs are unaffected.** `20260804T122546Z-A26b-g50t-a`
and `-sk48-b` were running when this landed; a running leg parsed its args at
start, so this changes the **next** launch. Their results must still be read as
3 h runs.

**3. Money follows the clock, and that is not free.** A longer ceiling means a
leg can actually spend its declared budget instead of being cut off by time.
That is what A26 is for, but the bill moves toward the cap: measured legs to
date are $4.4–$20.3, and the recomputed pool balance is +$317 against the raised
$700 ceiling.

**4. Not touched: `TTL_MIN_S`, `HEARTBEAT_WINDOW_S`,** and the per-leg dollar
caps. Only the clock and the lease sizing that depends on it.

## Verification

| | |
|---|---|
| tests | 821 tests: **817 passed, 4 failed**. Baseline at base `18e7d81b` was 813 passed / 4 failed; **+4 tests, the same 4 failures, none new**. |
| — the baseline was RED before I changed anything | The ritual said so and refused to let it be absorbed: `tests/test_arm.py::test_the_archive_stays_accountable`, `tests/test_desk_gate.py::test_a_scratch_pool_may_not_be_pointed_at_a_run_ledger`, `tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive`, `tests/test_reply_loss.py::test_the_archive_still_holds_the_thirteen_lost_replies`. All four are facts about master, carried verbatim, not fixed here. |
| sealed | **2/2 green** — 21 sealed / 4 dev, no sealed id in the 6 changed files |
| credentials | **5/5 green** — `.env` gitignored and untracked, no secret value in 13,218 tracked files |
| boundary | **RED, then green.** The guard caught a stray file `wall_clock_s` at the worktree root — see below. Removed; now **1/1 green**. |
| MANIFEST | `theoria-arm/runs/2026-08-04T143015Z-A30-wall-clock-8h/MANIFEST.json` — 8 artefacts |
| verify.sh | generated for this ticket (`theoria-arm/verify.sh`); note R2-1 also created one on an unmerged branch, so the two will meet at merge |
| sealed-pile API calls | 0. Offline throughout: no network, no model call, nothing spent. |

## Open, and deliberately not closed here

**1. A mistake of mine that only the boundary guard saw.** Writing an archive
note through a double-quoted bash argument, the backticks around an identifier
opened command substitution — and the `>` inside was a **redirect**, so bash both
ate the text *and* created an empty file named `wall_clock_s` at the worktree
root, outside the declared territory. I noticed the eaten text, because there
was a stderr line, and repaired it; I did not notice the file. The boundary
guard reported `1 stray: wall_clock_s`, 0/1 green. Removed (0 bytes, untracked).
**The lesson is sharper than "backticked identifiers vanish": the shell executes
what is inside them, and a redirect leaves an artefact somewhere nobody looks.**
Use a heredoc for any prose containing backticks, and read the boundary guard as
a real check rather than a formality — it was the only thing that saw this.

**2. `TTL_MAX_S = 12 h` is now the ceiling, and it is a deliberate number, not a
derived one.** Anything above 11 h 45 m of wall clock will be refused by name.
That refusal is the intended behaviour; raise `TTL_MAX_S` on purpose if a longer
run is ever wanted, and the new test will hold you to the margin.

**3. `armtools/spend_check.py` now imports `harness.spend` inside `main()`.** It
previously reached the pool by loading `proxy/spend_gate.py` by path and imported
no harness module. A function-level import keeps that independence at module
load while letting the projection tool follow the arm's real default — a tool
that projects a configuration nobody runs is worse than no tool.
