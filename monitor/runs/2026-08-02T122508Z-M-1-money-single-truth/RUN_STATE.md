# M-1 · RUN_STATE

Prompt: `(unset — owner instruction, 「第二三件都批准」, 2026-08-02)` · branch
`agent/m-1-money-single-truth` · base `d10788f` · 2026-08-02.
Territory: `monitor`. Run archive: `monitor/runs/2026-08-02T122508Z-M-1-money-single-truth`.

## Delivered

**1. `monitor/money.json` — the single source for amounts.** Amounts are
hand-written once, here. The pool ceiling stays a **pointer** to
`proxy/spend_policy.json` and is never copied — copying it is how a fourth
truth gets made, and three already existed (dashboard green on a $200
envelope; freeze on a $214.90 ceiling already $250.07 spent; the gate on
$92.99 remaining). Register entries carry `covers` (campaign substrings +
`from_utc`), which is what makes *"which entry authorised this leg"* a
question a program can answer rather than a sentence someone typed.

**2. `monitor/INCIDENTS.md` — the territory had no incident book.** Prefix
`INC-MON-` (grep across the repo: previously 0 occurrences), chosen not to
collide with `INC-00n` / `INC-AR-0nn` / `INC-BA-0nn` / `INC-TA-0nn`.

* **`INC-MON-001` — B = $60 was spent to $129.0326 (215%) and the dashboard was
  green throughout.** Recomputed from `proxy/var/spend_gate.jsonl` (17,329
  rows): dev pile $129.0326 over 37 campaigns; per game g50t $71.4784, sk48
  $57.5542, ar25 $0.00; pool $160.9480. G1 $50 crossed at ledger line
  **16157** (`2026-07-31T23:54:45.969Z`, mid `R1-g50t-a`, 49.78684 → 51.509416);
  B $60 crossed at line **16346** (`2026-08-01T00:48:42.766Z`, mid
  `R1b-sk48-b`, 59.086316 → 62.448327). The load-bearing half is *why nothing
  fired*: `scan.py:_spend_watch()` hard-coded `ENVELOPE = 200.0`, summed the
  whole ledger with no `kind` and no campaign filter, called the result
  「开发堆战役包」, and reddened only below $40. **B was never a quantity that
  instrument could express** — not one missed reading, a structural blindness.
* **`INC-MON-002` — two live entries both numbered `#12`.** Not a typography
  problem: `20260731T1500Z-A3-sk48-carried-l1` ($12.2517) carries
  `prompt_id: "A3-campaign-level2"` (register **#10**'s name), but #10 declares
  a **g50t** leg and its settlement $9.5569 reproduces exactly and only from
  the two g50t campaigns. The entry that actually covers it is the batch #12,
  which landed **11.4 s** before that leg's reserve (`spend_gate.jsonl:15032`,
  `15:06:28.568Z`, `usd_cap 19.0`). **So which entry keeps the number decides
  whether a paid leg has any authorisation at all.**

**3. The register, corrected in `monitor/spec.py`.** `:522` renumbered
`#12 → #14` **in place**, following `baseline-arms/INCIDENTS.md:7-13`: the
externally-cited entry keeps the number (`PARTNER_SYNC.md:1898` and
`monitor/runs/20260731T155302Z-P1READJ/RUN_STATE.md:18` both predate
`af138a0d` and both point at the batch entry), paragraphs are never reordered,
and the collision is recorded rather than tidied away. Settlement heading
retitled. R1b's breach restated accurately. `#13`'s figures corrected as
superseded. New **`#15`** registers R2 / R2b, which had no entry at all —
**recorded honestly as after-the-fact, not back-dated into compliance**.
Rendered ids are now unique and gap-free (3..15); order is deliberately not
ascending, because renumbering in place forbids reordering.

**4. `_spend_watch()` rewritten.** Reads `money.json`, compares per allocation,
reports the pool separately against `spend_policy.json`'s own ceiling. Measured
output today: `risk` — `dev_pile_B：额度 $60.00，已花 $129.03，剩 $-69.03 →
已超支`. Three values never collapse to two: unreadable `money.json` → `unknown`,
absent ledger → `partial`, never a default that reads healthy.

**5. `monitor/tests/test_money_register.py` — 9 tests.** Nothing in
`monitor/tests` (39 files) previously matched `spend_gate` / `gate-exception` /
`登记簿`; a register no test can redden is decoration.
`test_register_ids_are_unique_and_have_no_gap` is the assertion that would have
caught `INC-MON-002` the day it landed, and it has a manufactured-red twin.
**Breaches are checked by set equality, not by "must not breach"** — B is
already over, so "must not breach" would be red forever and a permanently red
gate becomes furniture. A new undeclared breach fails; a declared breach that
has silently vanished also fails. Writing a breach down is the only route back
to green, which is the discipline.

**6. Two cross-territory notes, no direct edits.**
`monitor/inbox/20260802T1240Z-…-9-2-cannot-be-cleared-…` (to `freeze`) and
`…T1245Z-…-three-money-records-to-correct.md` (to `theoria-arm`).

## Gaps — what the工单 asked for and did not get

**1. The overrun is recorded, not undone.** $129.0326 is spent. Fixing the
instrument is not fixing the spend, and `INC-MON-001` does not close because
the dashboard now tells the truth.

**2. Three things need a human and are not decided here.**
(a) **B = $60 per campaign or per game?** `A3-campaign-devpile.RES-1.md:54` and
`freeze/BUDGET_TABLE.md` read per-campaign ($129.0326 = 215%);
`loop_state.json` and `theoria-arm/harness/campaign.py` read per-game (g50t
over, sk48 under). Breached under both, so the verdict is unchanged — but blame
and remaining headroom differ and `money.json` can hold only one.
(b) **Confirm the #12 renumbering direction**, since it decides the sk48 leg's
authorisation.
(c) **Does `#13` (「不管预算，全额推进」) suspend `#14`'s $15/$30 and `#12`'s
$75/2500?** `#13` declares no number of its own, and R2b then ran at $39.0392 —
the largest round on record with no envelope. Until this is answered the
register cannot settle R2b.

**3. Three fixes belong to `theoria-arm` and were requested, not made:** the
mis-attributed MANIFEST `prompt_id`; whether `armtools/round.py` should refuse
a `--ceiling` above the registered per-leg figure (`round.py:126` defaults to
15.0 and was overridden with 25 on R1b/R2/R2b, opening reserves to `usd_cap`
$29.00 — that is the whole breach, and it is in the dollar axis only); and
`harness/campaign.py`'s constants reading a different source from `money.json`.

**4. `freeze/BUDGET_TABLE.json` is stale and was not touched** — freeze's file.
`python freeze/build_budget_table.py --verify` reports `THE BALANCE MOVED`
today. Noted in the PARTNER_SYNC paragraph.

## Verification

| | |
|---|---|
| tests | `python -m pytest monitor/tests -q` → **534 passed, 2 xfailed, exit 0**. Baseline at base `d10788f` was 525 passed / 2 xfailed; +9 tests, still green. |
| the territory's standing gate | `monitor/verify.sh` / `verify.py` **already existed and were deliberately not regenerated** — `verify-gate gen` overwrites a standing `verify.sh`, which would have destroyed this territory's own gate. The three red-line guards were invoked directly instead. |
| sealed pile | **raw run RED, then allowed with disclosure.** 3 files hit (`monitor/spec.py`, `monitor/state.json`, `monitor/index.html`) carrying `dc22-fdcac232`, `ft09-0d8bbf25`, `ls20-9607627b`. The guard is **file-level, not hunk-level**, so touching `spec.py` for an unrelated renumbering makes it scan the whole file. Established rather than assumed: `git show <base>:monitor/spec.py` already contains them; **my diff's added lines contain zero sealed ids** (`git diff -U0 \| grep ^+ \| grep -c` → 0); none of the six files I created contains one; `state.json`/`index.html` are regenerated copies of that same pre-existing text. The two lines are contamination **registration** (`spec.py:739` records which sealed games' mechanics were read before the stop-reading rule; `:1011` records that `dc22` is sealed and both CLAUDE.md and Theoria.md forbid it) — exactly the exception the guard's own message names. Re-run with `--allow` on those three paths → **2/2 green**. |
| sealed-pile API calls | 0. Offline throughout: no network, no model call, nothing spent. |
| credentials | **5/5 green** — `.env` gitignored and untracked, no secret value in 13,093 tracked files. |
| boundary | **1/1 green** — nothing changed outside `monitor/`; `PARTNER_SYNC.md` appended, never edited. |
| MANIFEST | `monitor/runs/2026-08-02T122508Z-M-1-money-single-truth/MANIFEST.json` |
| the territory's standing gate, after merging master | **GREEN, exit 0** on the fourth run — but it reddened twice first, at **different stages each time**, and both reproduce green standalone: run 2 `real run` (`board.py list failed`, empty stderr; standalone returncode 0, 187 lines), run 3 `tests` (3 × `test_orphan_commits` failing at `git push` inside a temp repo; standalone 10/10 pass). Non-zero exit with empty stderr is the Windows `0xC0000142` spawn signature, and `verify.py`'s own docstring records that its 460 s budget was measured under six concurrent pytest. Load-dependent flakiness, not this change — **but a gate that reddens somewhere different on every run is worth someone's attention.** |
| PARTNER_SYNC append-only | **guard RED, and the cause is not this branch.** It reports `diverges at line 1821 -- existing text was modified`. Three-way against base `d10788f7`: `origin/master` first-diff-idx **1820**; this branch's pre-merge commit `f32ad2d5` first-diff-idx **None** (base is a clean byte-prefix — M-1's own paragraph is a pure append); post-merge HEAD inherits 1820. Cause: the `theory-compiler` paragraph `c15-unnameable-cell-verdict` was inserted **mid-file**, between the `阻塞:` and `下一步:` lines of the published 2026-07-31 `gen-pddl-repaired` paragraph — splitting it, so the older entry now has no `下一步` line and the newer appears to have two. **Not fixed here**: moving the orphaned line back is itself editing existing text, and the board's rule is that a published paragraph is corrected only by appending one that supersedes it. Filed to `theory-compiler` via `monitor/inbox/20260802T1330Z-…`. Same rule, same recurrence as `monitor/audit/DRIFT-20260729T0236Z-…`. |

## Open, and deliberately not closed here

**1. `monitor/state.json` and `index.html` were regenerated on purpose.** They
carry **two and one** further copies of the register string respectively; had
`spec.py` been committed without re-running `scan.py`, the dashboard would have
gone on publishing the duplicate-`#12` register — the exact drift this ticket
exists to remove. `_spend_watch` now honours `THEORIA_SPEND_LEDGER` so a
worktree regeneration reads the real ledger instead of downgrading a genuinely
red cell to 「尚未产生记录」.

**2. Two numbers of mine were wrong until I ran them, both kept here because
the shapes recur.**
(a) **Charge basis.** I first quoted the pool as $160.9480 (all rows) while B
was spend-only. Reconciled: `spend` $160.7917 + `price_correction` $0.1563 =
$160.9480; `reserve` and `release` each sum to exactly 0 and double-count if
included. The basis is now declared in `money.json` and in `scan.py`'s comment
**because both figures had already been quoted inside this one ticket**. B is
identical under either basis.
(b) **My coverage model was wrong and the new test caught it.** `_covered()`
ignored `#12`'s `covers.from_utc`, so legs paid on 2026-07-29 fell inside an
envelope that landed 2026-07-31T15:06:17Z, manufacturing breaches that never
happened. The same run surfaced that **the ledger mixes pytest-fixture reserves
with real ones** (`pytest-*`, `_probe-*`: $0 charged but real `usd_cap` rows),
so a money check that does not exclude them audits test doubles. Both are
handled and documented in the test rather than filtered silently.

**3. `action_cap 5616` is NOT a breach, and the guard against re-deriving that
misreading is a test.** The pool counts outbound ARC HTTP requests, not
scorecard actions: `36 + ceil(300 × 9.3 × 2.0) = 5616` is exactly what 300
declared actions converts to, and `#10`/`#11` settled compliant carrying the
same 5616. Dividing 5616 by 300 to get "18.7×" divides two units. That
misreading reached a draft of this ticket;
`test_action_cap_is_read_in_outbound_units_not_actions` exists to stop it
coming back.

**4. R2 spent $0.0000 and both its legs exited 0.** Both `reset_failed` on
`RESET did not return 200 after 40 attempts` — 0 actions, 0 desk calls, 0
levels. This is not the first time in this repo that exit 0 has accompanied
nothing being achieved. Judge health by artefacts, not by exit codes.

**5. The fleet is not running.** The scan run for this ticket reports
`TheoriaReflex` and `TheoriaDashboard` **disabled**, `reflex_heartbeat` last
completed 3,528 minutes ago, and all standing researchers 「疑似停下等人」.
Nothing here restarts them; a Windows scheduled task needs a human at the
console.

**6. A duplicate session exists on adjacent work.**
`monitor/board/claimed/S45-…W-9201.md` claims the freeze-side blockers
(9.15 / 9.16 / the reason floor) and `A23-…W-9202.md` claims the anchor-drift
work already delivered as `agent/r2-1-roll-forward-drift`. A sibling `F-1`
worktree for the freeze half of this instruction was created and then **stood
down and deleted** (0 commits, clean) once that claim was found. Same-ticket
double-working is happening on this board.
