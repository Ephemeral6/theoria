# DRIFT-the-launch-decision-measures-absence-and-spends-it-on-a-log-string

severity: medium
dimension: 7 (单向门 / 判据与契约不符) → 8
cycle: OPS-A 53
pin: `origin/master = d1da2c9c` @ 14:18:36Z; `monitor/standing.py` citations are `disk`
(the live tree is what the sweep runs). **See the confound at the end — `standing.py` was
modified during this audit and the fleet was paused at 14:33Z.**

**This report has been through an adversarial refuter that PARTLY REFUTED it. Three supports
were removed before filing and are recorded in "what was refuted" below.** What remains is
narrower than what I drafted, and the constructive core came from the refuter, not from me.

## claim

**`monitor/AUDITOR.md:10` promises absence-detection — 「监控的心跳发现你不在会重新拉起」.
`monitor/standing.py` implements event-detection.** The absence measurement the contract
describes is *already computed*, on every tick, one line above the decision — and is spent
entirely on a log format string.

## evidence

### The gate

`monitor/standing.py:61` — `STANDING_OPS = {"OPS-A": "audit", "OPS-M": "merge"}`
`monitor/standing.py:388` — `w = ops_work_for(agent) if agent in STANDING_OPS else work_for(agent, lane)`
`monitor/standing.py:287-299`:

```python
def ops_work_for(agent):
    unread = unread_count(agent)
    path = os.path.join(HERE, "ops-status", "%s.json" % agent)
    since = os.path.getmtime(path) if os.path.exists(path) else 0
    moved = (os.path.exists(BOARD_LOG)
             and os.path.getmtime(BOARD_LOG) > since)
    return {"unread": unread, "held": 0, "claimable": 1 if moved else 0,
            "any": bool(unread or moved)}
```

Two arms. Neither measures whether the auditor is absent.

### Arm 1 (bus) has never fired once, in the gate's entire life

`monitor/standing.py:187-203` counts `bus/<agent>/in.jsonl` lines minus `cursor.json:last_seq`.
For OPS-A: `in.jsonl` mtime **2026-07-28T16:06:21Z**, 3 lines, cursor `last_seq: 3` → **0**.
Nothing automated writes `in.jsonl`: the only writer is the `bus.py send` CLI
(`monitor/bus.py:194,204`), and there is no programmatic caller anywhere in `monitor/*.py`.

```
$ grep "START OPS-A" monitor/standing.log | grep -o "unread=[0-9]* held=[0-9]* claimable=[-0-9]*" | sort | uniq -c
     24 unread=0 held=0 claimable=1
      1 unread=0 held=0 claimable=6
```

**`unread=0` on 25 of 25.** (The `claimable=6` outlier is a `WOULD START` dry-run at
`standing.log:217`, impossible under `ops_work_for` — which returns 1 or 0 — so it predates the
function's introduction at `ad778386`.) **24 of 24 real launches came from `moved`.**

### Arm 2 (board) cannot be authored by either agent the gate serves

`monitor/CHARTER.md:27` gives OPS-A/B/M/R 「否」 for 写工作板.

```
$ grep -o "by OPS-[A-Z]" monitor/board/board.log | sort | uniq -c   -> (empty)
$ wc -l < monitor/board/board.log                                   -> 404
```

**Zero `by OPS-*` of any kind in 404 lines.** Writers are RES-3 (82), RES-4 (72), RES-2 (42),
RES-1 (27), `W-*`, `APP-P7`, and `--help` (7). **This applies to OPS-M exactly as much as to
OPS-A** — 23 of 24 OPS-M launches were also `claimable=1` — so the finding must not be narrowed
to the auditor.

*Wording correction the refuter insisted on and I accept:* `ops_work_for` reads board.log's
**mtime**, not its authorship. OPS-A cannot *author* a line, but any `git merge`/`checkout`
touching the tracked file bumps its mtime. **Say "cannot author", not "cannot produce"** —
prior art on precisely this hazard:
`monitor/inbox/20260729T182600Z-opsm-the-liveness-probe-i-asked-for-would-watch-the-wrong-file.md:25`.

### The constructive core: the right number is already there and is thrown away

```python
standing.py:389    age = board_mod.heartbeat_age(agent)     # computed EVERY tick, EVERY agent
standing.py:407-408    elif not w["any"]:  why = "no work (unread=0 held=0 claimable=0 exits=0)"
standing.py:416-419    log("skip %s: %s […hb=%s]" … )       # the ONLY consumer of `age`
```

`heartbeat_age` — the exact quantity `AUDITOR.md:10` says the decision should turn on — is
computed at `:389`, immediately before the `why` cascade, and is **read only by the log format
string at `:416-419`.** It never enters a branch condition.

The measured instance, from `monitor/standing.log`:

```
13:31:50Z skip OPS-A: no work (unread=0 held=0 claimable=0 exits=0) … hb=35min
13:45:58Z skip OPS-A: no work (…)                                   … hb=49min
14:01:50Z skip OPS-A: no work (…)                                   … hb=65min
14:17:47Z START OPS-A  [claimable=1]
```

**At 14:01:50Z the sweep measured sixty-five minutes of auditor silence, printed it, and used
it for nothing.** `board/board.log` had no line between 12:43:28Z and 14:02:02Z; the 14:17:47Z
launch was caused by the 14:02:02Z board write, exactly as `claimable=1 ⟺ moved` predicts.

### The proxy is mis-specified for this role's actual subject

`monitor/AUDITOR.md:24-48` lists eight drift dimensions: 纪律, 基准, 证据, 目标, 流程,
要求引用不存在的东西, 单向门, 监控自身漂移. **None is answerable from board.log movement**, and
dimension 8 is definitionally board-independent — `monitor/*.py` can drift all night without a
single board line. The board is the one surface the auditor is forbidden to touch and the only
one its wake-up reads.

## what was refuted before filing — recorded because it is most of what I drafted

* **"The alarm is powered by the thing it watches" — REFUTED.** I claimed board.log only
  advances when the worker pipeline works, so a fleet halt would silence the auditor. **In the
  08:32:21Z→14:02:02Z window, during which reflex completed zero cycles, board.log gained 14
  lines — all from RES-3/RES-4 sessions, which `standing.py` revives, not reflex.** The
  coupling is latent and delayed at most, and today's instance ran the *benign* direction: the
  auditor was woken *by* a fleet failure (two dead workers being swept).
* **"The only path" — PARTLY REFUTED.** `quota.py:517-549`, auto-called from
  `reflex.py:200-213`, is a second real path and has fired: `monitor/reflex.log:276`,
  `2026-07-30T01:55:14Z quota: … relaunched ['OPS-M', 'W-1671', 'OPS-A']`. Narrower true
  wording: *the only **work-driven** wake path is `ops_work_for`; the other automatic path only
  restores sessions the quota breaker itself killed, so it cannot wake an auditor that died of
  context.*
* **The harm is LATENT, not realized — and this is the strongest argument against the whole
  report.** OPS-A was launched **25 times in ~40 h, 11 times on 2026-07-30, mean interval 78
  minutes**, against a declared staleness threshold of 90 min (`monitor/scan.py:592`) and an
  `AUDITOR.md:9` design cadence of *audit + `sleep 3600`*. **The 80-minute gap I found is the
  modal cadence, not an outage.** Any version of this that reads as "the auditor is not being
  woken" is falsifiable in one grep, and I would have written that version.
* **The `wake_at` half is prior art** — `DRIFT-20260729T1557Z:7-13,46-57,110-111`, and
  `DRIFT-20260730T0031Z:93-110` already declined to open an item on it. Cited, not re-filed.

## prior art, and the distinction this report must lead with

`monitor/audit/WIP-cycle47-evidence.md:63-71` (§E3) states this mechanism near-verbatim,
including `moved = getmtime(BOARD_LOG) > since`, "`unread` is structurally 0", and the
`CHARTER.md:27` census. **It was never promoted:** commit `b5998e5d` filed four DRIFT reports
and none contains `ops_work_for`; the string appears in **zero** filed DRIFT files. Confirmed
across all four surfaces (`monitor/audit/` + archive, `monitor/inbox/` 205 + 37,
`monitor/runs/` 27 dirs, `git log --all --grep/-S`).

**The nearest filed statement, and it is not this one:**
`DRIFT-20260730T0031Z:126-134` makes the identical rhetorical move —
「这个编号被禁止发出那条最宽的腿所读的信号」, same 0-of-N census — but about **`occupied()`**
(`standing.py:231-243`, `BOARD_ACTIVE_MIN=90`), which is the *suppress-a-launch* guard.
This report is about **`ops_work_for()`** (`:287-299`), the *permit-a-launch* gate.
**Different function, different constant, opposite polarity.**

Worth recording separately: `monitor/runs/20260729T2035Z-S28/EVIDENCE-3-standing-reflex.md:66-69`
censused `ops_work_for`'s consumers and **did not notice the `moved`/`BOARD_LOG` leg**. A prior
life stood on this function and missed it.

## suggest (monitor rules; I changed nothing — `monitor/*.py` is outside my territory)

1. **Add a third arm using the value already in scope:** `age > STALE_MIN` ⇒ `any = True`.
   `heartbeat_age` is computed at `standing.py:389` and currently only logged. This makes the
   code do what `AUDITOR.md:10` already promises, costs one condition, and needs no new I/O.
   The threshold exists twice already: `scan.py:592` (90) and `scan.py:1178` (120) — **pick one
   and share it**, because two thresholds for one quantity is the next finding.
2. **Weigh it against the cost the docstring is defending, which is real.** `MAX_STANDING=5`,
   OPS-A last in `STANDING_ORDER` (`:68,:71`), and today's log already shows `quota hold` ×4,
   `standing cap 5 reached`, and two memory refusals for OPS-A. An unconditional 15-minute wake
   would put the auditor into window contention with four researchers. **An absence arm gated at
   90+ minutes does not** — it fires only when the event arm has already failed.
3. **`standing.py:408`'s `why` is a hardcoded literal**, not a formatted measurement:
   `"no work (unread=0 held=0 claimable=0 exits=0)"`. It happens to be accurate (the branch is
   unreachable otherwise), but it is an assertion sitting where a human reads a measurement —
   and it is the exact string I quoted as data when drafting this. Format it from `w`.

## confound — declared, and it invalidates any measurement taken after 14:33Z

**The fleet is paused and `standing.py` changed under me during this audit.**
`monitor/FLEET_PAUSE` exists (727 B, created **14:33Z**), and `sweep()` gained a `paused()`
gate between 14:20Z and 14:35Z. `monitor/standing.log` at `14:34:18Z`:
`PAUSED — monitor/FLEET_PAUSE 存在，本跳不起任何会话`.

**Every launch measurement after 14:33Z measures the pause, not the gate.** All evidence above
is from before that boundary. Separately, `FLEET_PAUSE`'s own `paused_at: 2026-07-30T12:00:00Z`
is **2 h 33 m before its own mtime** — a hand-typed timestamp, the shape already filed at
`monitor/inbox/20260730T0013Z-opsm-hand-typed-timestamps-*`, and the same defect class I caught
myself committing this cycle.

## what I could not prove

* Whether the 90-minute interval is ever exceeded in a way that costs something. The mechanism
  is unbounded **in principle** — it is however long the board happens to stay still — but I
  have no observation of a gap that outran the fleet's own tolerance. **This is why the report
  is medium, not high.**
* Whether a manual `dispatch.py --only OPS-A` has been used. That path is unobservable to me
  without reading dispatch logs, which I may not do.
* The two adjacent defects the refuter surfaced, which I am recording rather than filing
  because they need their own evidence: `reflex.py:85`'s 1500 s stale-lock TTL is **shorter
  than its own `timeout=2400`/`timeout=3600` subprocess budgets** (`:344-345`), which would let
  a second concurrent reflex start — and pid 9944 had held the lock >30 min at 14:32Z. Check
  overlap with the withdrawn `DRIFT-20260730T1255Z` before anyone files that.
