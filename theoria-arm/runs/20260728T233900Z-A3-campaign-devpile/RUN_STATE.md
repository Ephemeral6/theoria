# A3-campaign-devpile — RUN_STATE (worker W-1640)

## What this run delivered, and what it did not

**Did not:** play a single live turn. Not one cent was spent, and the online
campaign the ticket asks for has not run.

**Did:** find and fix four defects that would each have wasted the money, prove
each fix by mutation testing, build the campaign runner the ticket needs (there
was no way to start one), and hand the spend decision to whoever is allowed to
make it.

The order says 做不完就交阶段结果，不许为了跑完降低记录标准 — deliver the
partial result, never lower the recording standard to finish. This is that.

## Why no money moved

Two authorities above the spend gate are red. The gate itself is green
(ceiling $214.90, spent $31.75, **free $183.15**, no live reservations), which
is exactly why it is not the thing that decides.

**1. Theoria.md:305 — the Phase 3 money gate is closed.** The sentence is
`全绿才准烧游戏钱(Phase 3 的门)`: *all* sixteen Phase 1 acceptance items green
before game money burns. `monitor/state.json` reports **`p1_green: 9,
p1_total: 16`**. Five are hard red on mainline, including the one that matters
most here — there is **no shared three-arm ledger** (`proxy/var/ledger.jsonl`
holds only `mock_arm` and `replay`, zero real-arm records), and the
reconciliation obligation is undischargeable anyway because live ARC responses
carry no `score` field (INC-TA-002).

`monitor/spec.py:245` already registers a `p3-gate-exception` (status `risk`)
for spending that happened at 6/16, and the rule that exception established is
**register first, spend after**. It covers `p3-envelope`'s $2.53 and nothing
else.

**2. monitor/CHARTER.md — the campaign lane's spend is RES-1's alone.** The
table at :24 is actor-scoped (`W-*` / 花 API 钱 / 否), and :30 gives the reason:
two sessions keeping separate accounts already caused quota contention and
ledger pollution once. That is INC-TA-001, two arms on g50t concurrently, and
it is **still unfixed** — the proposed cross-session lock would live in
`arc-recon/`, which is read-only ground. :32 names the escalation path: write an
inbox proposal. Done, at
`monitor/inbox/20260729T002000Z-W-1640-a3-spend-proposal.md`.

One tension worth stating rather than leaving for a reader to find:
`monitor/prompts/W-worker.md:38` tells every W-worker to clear the spend gate
before spending API money, which presupposes that workers spend. It resolves
against the charter — `CHARTER.md:3` says changing it changes the division of
labour without anyone re-pasting a startup prompt — but it is a real conflict
and the charter should probably say so explicitly.

The board reassigning a dead RES-1's ticket to the open worker pool transfers
the ticket, not the chequebook: `board.py:59` opens a stale lane's items for
**queue fairness** (`别让通用工人把某个常驻研究员的队列抽干`), which is not an
authority grant.

## The number that decides the shape of the deliverable

RES-1 computed this before it died and I reproduced it: **this budget cannot buy
a level.** g50t level 1's own `level_baseline_actions` is **78 successful
actions** against an authorised 40 per level; at the measured $0.90/action and
394 s/action that is ≈**$70 and 8.5 hours** against a $60/game ceiling and a
3-hour wall clock.

No level completes ⇒ no level boundary occurs ⇒ **C3's transfer claim cannot be
observed this round, at any budget this repo has.** That is not a lowered bar;
it is the arithmetic the ticket's own "先算后花" demands.

An adversarial review sharpened this and I accept the correction: money and
quota do *not* forbid a level attempt ($183.15 free, 24,000-request ceiling,
~624 requests needed). The binding constraint is **wall clock** —
`DEFAULT_WALL_CLOCK_S = 3*3600`, which `campaign.py` never overrides and exposes
no flag for, hard-capping a leg at ~27 actions. And 78 is a *reference*, not a
floor: all 32 real closed scorecards report `levels_completed == 0`, so the
realistic figure is worse.

What the budget *can* buy is the per-turn series — theorize rounds, the seven
surprise counts, cost — which is what the ticket itself calls figure 2's entire
raw material.

## The four defects, each proved by mutation

Every one was found before spending, and each is re-broken in `verify.sh` gate 6
with the covering test required to go red.

**1. Every model call paid, then died writing itself down.** `ModelDesk.call`
passed five fields to `RunLedger.model_call` as top-level kwargs;
`canon.MODEL_CALL_FIELDS` is a closed ten-name set, so `canon.check` raised
`NonCanonicalField`. The raise lands *after* `cli_cost_usd` is incremented and
*after* the charge settles against the shared pool. `inner/loop.py` swallows it
as an ordinary desk failure, so **a full-budget campaign would have produced no
manual at all.** Invisible because `--mock` sets `offline=True` and skips
theorize — no test here had ever driven a *completed* model call — and every
desk test used a `FakeRun` that validates nothing.

**2. The campaign's dollar accounting was dead.** It read `desk["cost_usd"]`, a
key `ModelDesk.summary()` has never emitted. Every leg booked $0.00, so the
$60/game and $200/campaign ceilings could not trip. Now reads the gate-settled
figure and the CLI figure, keeps both (D-P8-015), and governs on the larger —
a ceiling that trusts the smaller of two disagreeing figures can be walked past,
and one of them under-reports by 6.8% (INC-TA-003).

**3. The game id was kept out of the prompt by luck.** `Theoria.md:353` is a
hard rule — `游戏 ID 永不进模型上下文,全程匿名化`. There was no anonymiser
anywhere; the arm was clean because nobody had wired an id in. An adversarial
probe put **six occurrences of `g50t` into a 20,975-char prompt** by forcing an
engine write failure: the traceback carries the path, and the run slug embedded
the game stem. Closed at the source (game-free leg slugs) and at the backstop
(`ModelDesk.forbid_in_prompt`, checked before the subprocess so a leak costs
nothing).

Honest qualification, from the adversarial review: the leak was *reachable*, not
*observed* — the probe manufactured the write failure, though the slug half was
genuine history. And false-positive risk is near zero by construction: all four
stems contain characters outside `[0-9a-f]`, and frames render as hex, so frame
dumps and hashes cannot collide. Zero accidental hits across 30 MB of real
artifacts.

**4. The fix for (1) broke the deliverable.** Moving the fields into `request`
made the record canonical and blinded five readers that took them off the top
level: constraint 8 would have reported `holds: false` on every future live run,
and `_turn_spine` would have emptied `turn_series.json` — the figure-2 raw
material — to `model_calls: 0`. Caught only because the adversarial review ran
the code rather than reading it. The previous commit's own test docstring warned
about precisely this and then checked only the writer.

## The thing I got wrong twice, worth recording

Both times, a check passed for a reason unrelated to what it was checking.

* `verify.sh` gate 6 ran its negative controls on a **copied** arm, which has no
  sibling `proxy/`, so pytest errored at collection whatever the mutation was —
  and the inverted assertion (`if the test passes then fail`) turned every
  infrastructure error into a pass. A gate written to catch green lights with
  nothing behind them was one. Now mutates in place and asserts **both**
  directions: green before, red after. Gate 7 hashes the files to prove nothing
  survived.
* The new-shape readers in (4) were "green" across 165 tests because every
  fixture hard-codes the old shape.

The general lesson, and it is the same one as the ledger: **a test that does not
own what it asserts over is not testing what it says.**

## Test state

`python -m pytest -q` in `theoria-arm/`: **170 passed**, twice consecutively.

That "twice" is load-bearing. Before this run the suite was green **exactly once
per clean checkout and red forever after**:
`test_the_shell_turns_end_to_end_against_the_mock` pinned a constant slug,
reused one append-only `ledger.jsonl`, and asserted `seq` dense across the whole
file. On **2026-07-28T23:39:49Z** — during this session — my pytest and an audit
subagent's overlapped, and `Ledger` seeds `seq` once in `__init__` under an
in-process lock only, so seven `seq` values were issued twice and the `prev`
chain forked. No records lost, but `verify_chain` and `validate_ledger` both go
FAIL permanently on a gitignored file no code change could clear.

The writer defect is in `proxy/`, another track's territory, and is filed at
`monitor/inbox/20260729T001500Z-W-1640-ledger-writer-forks-under-two-processes.md`.
What I fixed on my side: `play()` now forwards `ledger_path` (a parameter `Run`
always accepted and `play` dropped), and the mock tests put their ledger in
`tmp_path`.

`bash runs/20260728T233900Z-A3-campaign-devpile/verify.sh`: **ALL GREEN**, seven
gates.

Zero API calls. Zero network. **$0.00.** Zero sealed-pile contact — the pile
guard is checked against `piles.json` itself rather than the module's own
constant, and gate 3 exercises it.

## Gaps, stated as gaps

* **The campaign has never run live.** `run_leg` is exercised only against
  `proxy/mock`. The whole level-boundary and book-carrying mechanism
  (`levels.jsonl`, `CARRIED.json`) is validated by unit tests and has never seen
  a real boundary, because none has ever been observed in this repo.
* **U3 and Δ are not addressed at all.** U3 has no per-game rubric in
  Theoria.md; Δ has no written baseline. See `EXIT_CONDITION.md`. Pinning them
  is a freeze-time decision, not a worker's.
* **The cookie jar is still not ported** from `baseline-arms/harness/arc_client.py`
  into `harness/arc.py`. It cuts g50t HTTP-per-action from ~41 to ~3. It does
  not change dollars (ARC requests are free) but it is the difference between a
  leg fitting in its wall clock and not. Left undone deliberately: it is a
  transport change that cannot be validated without live traffic, and I cannot
  generate live traffic.
* **`CAMPAIGN_USD = 200` exceeds the pool's $183.15 free headroom**, so the
  campaign's own ceiling can never fire — the pool trips first. Fail-safe, but
  the number was never reconciled against the only authority that exists. Also,
  as the adversarial review notes correctly, **no file in the repo authorises
  200/60/25/40**; `campaign.py`'s docstring cites `CHARTER.md`, which contains
  no dollar figures at all. They are this branch's own constants and all four
  are one CLI flag away from being changed.
* **`execution_mismatch` remains structurally zero** (GAP 2), so one of the
  seven surprise counters is uninformative. Reporting it as a plain 0 beside
  the others would repeat exactly the error E14 just finished fixing.

## What the next holder should do first

1. Get a ruling on the inbox proposal. Until then nothing live can happen.
2. If the answer is "close the gate first", the cheapest single step is merging
   `agent/s5-phase1-close` — a one-file conflict in `arc-recon/verify.sh`
   between S10's `ledger_invariants` and S5's `rate_budget` steps, keep both.
   That flips items 2 and 8 green and removes a cascade ruling from mainline
   that contradicts mainline's own code. Items 3, 4 and 5 need real runs.
3. If the answer is "spend", the command is in the proposal, and the first thing
   to watch is the wall clock, not the money.
