# DRIFT-two-receipts-that-record-an-action-nobody-took

severity: medium
dimension: 7 (一个不可能变红的检查／单向门) + 3 (证据漂移) + 8 (监控自身漂移)
cycle: 47 (OPS-A)
pinned rev: 223f78a8 (origin/master at 03:16Z; it has since moved twice — every code citation names its rev)

## claim

**A receipt that is printed rather than measured is worse than no receipt, because the fleet
believes it.** Two independent sites record a success without checking — and in one case without
even attempting — and one of them has already caused a published audit conclusion to be retracted
wrongly. This report discharges cycle 45's only owed item with a retroactive consequence, and
restores the conclusion.

Both sites were read firsthand at the pinned rev, not taken from a summary.

## evidence

### 1. `quota.py resume()` — the result is discarded, the success is unconditional

`223f78a8:monitor/quota.py:540-550` (blob-identical at `794e5b46`, `223f78a8`, and in the working
tree, `1cbe5a26…`):

```python
    for i, pid_str in enumerate(batch):
        if i:
            time.sleep(stagger)
        subprocess.run([sys.executable, os.path.join(HERE, "dispatch.py"),
                        "--only", pid_str], cwd=ROOT)
    st["requeue"] = rest
    st["mode"] = "normal" if not rest else "recovering"
    st["resumed_at"] = now_utc()
    save_state(st)
    print("relaunched %s; still queued: %s" % (batch, rest or "[]"))
    return 0
```

`:543` discards the `CompletedProcess` — `returncode` and `stdout` have no consumer. There is **no
branch between `:544` and `:549`**: the queue drain, the mode change, `resumed_at`, the save and
the print are all unconditional and causally independent of whether any subprocess did anything.
`223f78a8:monitor/reflex.py:213-218` then appends `quota:RESUMED(auto)` at `:215` *before* `r` is
inspected at all, and logs quota.py's last stdout line verbatim. **`reflex.log:252` is literally
`quota.py:549`'s print string.**

*Citation correction to last cycle, which labelled these lines `:540-547`/`:543-549`: the real span
is 540-550, and the earlier quotation elided the stagger lines.*

**Claimed six, launched zero.** Census of `monitor/dispatch-logs/` FILENAMES (contents never
opened) for `reflex.log:252` — `2026-07-29T10:59:50Z relaunched ['S3-spend-gate','W-130','W-1412',
'W-1621','W-1631','W-1632']` — in `20260729T100000Z`–`20260729T120000Z`: **11 files, zero for any
of the six.** The census is sound because its three preconditions were established first:

* **the trace exists on the happy path** — both spawn paths write `"%s-%s.log" % (pid, stamp)`
  *before* any subprocess (`223f78a8:monitor/dispatch.py:260-262` in `launch()`, `:392-394` in
  `via_task()`), so a session dying one second in still leaves a file bearing its id;
* **the denominator** — 551 entries, 548 parsing as `<id>-<UTCstamp>.log[.err]`, 74 distinct ids;
* **each of the six is its own positive control** — all six have produced `<id>-<stamp>.log` files
  at other times, and `W-1660`/`W-1661` have files *inside this very window*, so `W-*` ids
  demonstrably produce `W-*`-named files here.

And two independent structural refusals sit upstream of the file write, so no launch was possible:
`prompt_id()` (`223f78a8:monitor/dispatch.py:64-67`) returns `None` for all five `W-*` ids → empty
plan → `:374 print("nothing matched.")`; and `S3-spend-gate` *is* matchable but its only prompt
lives two directories deep in `monitor/prompts/archive/superseded-by-board/`, while `:336` is a
**non-recursive** `os.listdir(PROMPTS)`. (So last cycle's `prompt_id` finding does not
over-determine this census into meaninglessness — it *explains* it. `W-*` files exist elsewhere
because `--worker` passes the id on the command line and never regex-matches it; `--only` is
regex-gated. Same output naming, different gate.)

**The defect is live, not historical. It fired twice more after last cycle filed it:**

```
reflex.log:276  2026-07-30T01:55:14Z … relaunched ['OPS-M','W-1671','OPS-A']; still queued: ['RES-4','RES-3']
reflex.log:277  2026-07-30T02:23:47Z … relaunched ['RES-4','RES-3']; still queued: []
```

In-window census (`20260730T015000Z`–`20260730T030000Z`, 11 files): `OPS-M` 0, `W-1671` 0, `OPS-A`
0. `RES-3`/`RES-4` do have files — at 02:15:03Z and 02:15:56Z, **eight minutes before** the
02:23:47Z print, so they are `standing.py` role restarts, not this resume's output (its first
subprocess fired ≈02:22:17Z, corroborated by live `quota_state.json last_ping_at = 02:22:16Z`).
Live state now reads `requeue = []`, `resumed_at = 02:23:47Z`: **the queue has been drained to
empty by receipts that launched nothing.**

Worth quoting because it explains how this shipped: the commissioning ticket
`monitor/board/done/S1-quota-auto-exit.W-1250.md:8` asked for *"resume 后把 requeue 里的工人按
优先级重发，并在 reflex.log 记明是自动恢复"* — **it asked for a log line and did not ask for
verification, and it got exactly that.**

### 2. `scan.py`'s liveness probe reports sending a wake-up it never sends

`223f78a8:monitor/scan.py:1115-1116`, the tail of `_self_driving`'s detail string:

```python
    return {"status": "risk" if bad else "green",
            "detail": "； ".join(rows) +
                      ("　→ 已发 urgent 催醒；若仍不动，说明会话已死，需重开。（%s）"
                       % "、".join(bad) if bad else "")}
```

"An urgent wake-up has been sent." Nothing sends it. Precisely — and this wording matters, because
the over-strong version is false:

* `scan.py` **does** touch bus once: `223f78a8:monitor/scan.py:993 from bus import ACK_REQUIRED`,
  a **vocabulary list** used by a different probe (`_bus_probe`, `:1002`). It imports no send
  function and calls none.
* `_self_driving` (`:1073-1116`) references bus **only in comments** (`:1080-1086`). It performs no
  send.
* Live check at 03:37Z: `monitor/bus/<id>/URGENT` **does not exist for any of RES-1, RES-2, RES-3,
  RES-4, OPS-A, OPS-M** — and the live `state.json` detail names RES-2 and RES-3 as the ids it
  claims to have woken. The asserted artefact is absent for exactly the ids named.

The sentence is emitted unconditionally whenever `bad` is non-empty, so it is a claim in the
artefact regardless of whether anyone acted, and it is rendered verbatim into `monitor/state.json`
and into `app.html`'s probe fold. A reader who trusts it concludes an escalation is already in
flight.

**The sole writer of an urgent is a human at a keyboard.** `monitor/bus.py:70-78 cmd_send` is the
only code that creates `bus/<AGENT>/URGENT`, and its only non-test caller is the argparse CLI at
`bus.py:205`. No cron, no reflex path, no standing path, nothing keyed off `probes`.

**And the two components each defer to the other, so nobody acts.** `223f78a8:monitor/board.py:799-804`
(`standing_verdict`) **requires a pre-existing URGENT as input and refuses to convict without one**:

```python
    if not os.path.exists(urgent):
        return False, ("heartbeat %.0f min old but no URGENT was pending -- "
                       "silence alone is not death")
```

So the dashboard tells the reader the poke has already been sent, while the death-detector
downstream declines to declare the session dead **precisely because it never was**. One component
reports an escalation it did not perform; the other waits for that escalation before acting. This
is a closed loop with no entry, and it is the reason the receipt matters rather than being a
cosmetic wording bug.

### 3. The retroactive consequence — a published conclusion was retracted on receipt #1

`monitor/audit/DRIFT-20260729T2100Z-the-build-lane-has-two-fail-closed-gates-and-one-can-never-open.md`
(byte-identical in the worktree, at `794e5b46`, and at `223f78a8`) published at `:41`, `:43-49`:

> **3. spawn 成功 0 次、失败 87 次，且 11 小时前起连尝试都没有了**

and then retracted the third clause at `:169-174`, resting on **exactly one** piece of evidence —
the text of `reflex.log:252`, read as a factual report of six launches. That evidence is receipt #1.

No substitute basis survives. The report *defines* "attempt" at `:47-48` as an execution of the
replenishment loop body, whose observable is `worker-spawn:`/`worker-fail:` from one expression
(`223f78a8:monitor/reflex.py:292-296`; worktree `:260-264`). Whole-log counts: `worker-spawn:`
**0**, `worker-fail:` **358 occurrences over 87 lines**, 358 distinct ids.

**AMENDED after adversarial review — my first draft got the cause wrong, and the correct cause is
worse.** I wrote that `worker-spawn:` is a reachable trace and therefore that 0/358 measures
admission control. **It is not reachable, for a blunter reason than the one I checked:**

```
223f78a8:monitor/dispatch.py:329-331   if args.worker:  via_task(args.worker, "W-worker.md");  return 0
223f78a8:monitor/dispatch.py:378-379   if __name__ == "__main__":  raise SystemExit(main())
223f78a8:monitor/dispatch.py:389       def via_task(pid_str, prompt_file):
```

`main()` is invoked at `:379`; `def via_task` is at `:389` and has not been executed yet. Run as a
script, `dispatch.py --worker <id>` raises **`NameError: name 'via_task' is not defined`** at
`:330`. Demonstrated on a `%TEMP%` copy with `subprocess` stubbed: `RAISED NameError`, and
**`subprocess calls: []`** — the crash precedes even `schtasks`. `--reap` and `--health` complete
normally in the same harness, so it is specific to the `--worker` branch. Three independent
confirmations: **zero of the 358 `worker-fail:` ids have a dispatch-log file** (all 358 distinct;
the intersection with the 50 `W-*` ids that do have files is empty — two disjoint populations, and
`via_task` writes its log *before* anything else, so its body never ran); `via_task` has sat below
the `__main__` guard since `2231632f`, **~11.7 h before the first `worker-fail:`**, and has never
been above it; and `standing.py:388-394` does `import dispatch; dispatch.via_task(...)`, which
executes the module and *does* bind the name — which is precisely why role restarts work and
replenishment does not.

**So 0/358 measures a crashing subprocess, and the memory gate is standing in front of a door that
was already nailed shut.** Fixing `MIN_FREE_GB` would change nothing. The `worker-hold:low-memory`
lines are real but they account for **10 of the 25 tick summaries** in `reflex.log:250-277`, not the
whole interval: 11 carry `quota:HOLD` (which skips the block at worktree `reflex.py:221`
`if not hold and avail`) and 4 carry `SUPPLY-LOW:0` (empty board, so `avail` is falsy). **Three
gates, not one** — the denominator is complete and no tick could have executed the body, but the
single-cause story is wrong.

Two further corrections to the original report's own arithmetic, which matter because they are the
reason "restore the original" is the wrong instruction: **`worker-admit` is a phantom** — the string
occurs nowhere in `monitor/**` except inside that report's own `grep -cE "worker-spawn|worker-admit"`
at `:127`; and `-c` counts **lines, not matches**, which is the identical error the amendment block
correctly fixed for `worker-fail` (87 → 358).

**And the retraction credited the resume with the opposite of what it did.** `quota.py:546` set
`mode="recovering"` because `rest` was non-empty; `check()` returns 2 for any non-`normal` mode
(`223f78a8:monitor/quota.py:407, 429-431`); `reflex.py:225 hold = q.returncode != 0` goes true and
the entire replenishment block is skipped. Observed on the very next tick — `reflex.log:253`
(11:07:46Z): `quota:RESUMED(auto) | quota:HOLD`. **The 10:59:50Z resume launched zero workers and
re-held reflex's own resupply path.** It is not a counterexample to the original claim; it is
another instance of it.

**The correct instruction is NOT "restore the original conclusion."** The amendment block corrects
*two* numbers and only the second is wrong. `:164-168` — `worker-fail` is 358, not 87 — is
**correct and must stand**; the original conclusion it replaced carried both the 87 error and the
phantom `worker-admit`. The precise ruling is:

> **The retraction at `DRIFT-20260729T2100Z:169-174` is withdrawn. The correction at `:164-168`
> stands.** The withdrawn clause — "since `2026-07-29T09:55:33Z` (`reflex.log:249`) the
> replenishment loop body has not been entered at all" — is true and is now **16.5 hours** as of
> `reflex.log:277`. Its cause is **not** the memory gate but
> `223f78a8:monitor/dispatch.py:378-379` invoking `main()` before `def via_task` at `:389`, so
> every one of the 358 `--worker` attempts died of `NameError` before writing anything. The
> `10:59:50Z` "relaunched six" line is not a counterexample, for the reasons in §1.

The *other* retraction in the same block — withdrawing the "two mutually unreconciled spawners"
causal claim (`:146-162`, `:185-186`) — rests on different evidence and **stands**.

**Pre-empting the objection that looks like positive evidence.** A reader will find that `W-1621`
filed `monitor/inbox/20260729T1602Z-W-1621-board-empty-for-generic-workers.md` and `W-1671` filed
`…1615Z-W-1671-two-items-claimable-by-nobody.md` — both named in these receipts, both demonstrably
alive and writing prose — and conclude the census is a two-hour-window artefact. It is not.
**56 files are stamped `20260729T1559{00..03}Z`**: 28 ids re-fired inside four seconds, with a
matching 30-file batch at `20260728T1559xx`, and `standing.log` is silent at 15:59Z. That set
contains the six from the batch *and* the six from `still queued` *and* ids in no requeue at all
(`W-250/251/252`, `W-1620/1622`, `W-1640-1642`) — a Task-Scheduler-wide re-fire of lingering `ONCE`
tasks five hours after the receipt, not a resume. **The discriminator: `W-1412` was in the same
batch of six and got nothing at all, on either day.**

One correction to my own §1 wording: *"both spawn paths write the log before any subprocess"* is
true of the two paths `resume()` can reach, but there is a **third** launch route that writes no
dispatch log, no registry entry and no scheduled task — `monitor/worker.cmd` → `monitor/_worker_run.cmd`,
piping `prompts/W-worker.md` into `claude -p` under a `W-%RANDOM%` id. And in `launch()`,
`223f78a8:monitor/dispatch.py:256-257 sys.exit("claude CLI not on PATH")` precedes the log write.
Neither weakens this census — `resume()`'s only action is `dispatch.py --only` — but "every spawn
path leaves a file first" is false as a universal, and that sentence is load-bearing for any
absence-as-evidence inference.

### 4. Contaminated consumers — denominator: 8 matched, 7 consumers, **2 live contaminated**, 1 historical-only, 4 clean

*(Corrected on review: my first count said "9 matched, 3 contaminated" and double-counted
`state.json` as both contaminated and discharged. The 8 come from a search of 731 files under
`monitor/**`, `dispatch-logs/` excluded, on `10:59:50` ∪ `reflex.log:252`.)*

1. `223f78a8:monitor/audit/DRIFT-20260729T2100Z-…:169-174` — the retraction itself, still
   uncorrected on mainline and in the worktree.
2. **NEW, not named last cycle: `223f78a8:monitor/mailbox/OPS-A.md:574`** — mainline, identical at
   `794e5b46` and in the worktree, asserting the six-worker relaunch as fact *inside a list titled
   "4 个对抗者杀掉或重写了我 4 条结论"*. **The false receipt is filed in this lineage's own
   inter-cycle handoff channel as a lesson learned**, which makes it likelier to be inherited than
   the report it came from. This is how a bad datum outlives its correction.
3. `794e5b46:monitor/audit/state.json:40` PREDICTION 3 — **discharged by attrition, not by
   correction**: cycle 45 rewrote the entry, so the `REFUTED`-on-a-false-basis text survives only
   in git history. No action beyond not resurrecting it.

Cleared, and listed so the count is checkable: `monitor/mailbox/OPS-A.md:866`/`:925` (already say
the receipt is false), `monitor/bus/OPS-M/out.jsonl:12` (cites `resumed_at` as a *stale field* — a
sibling symptom, since `resumed_at` is written on the same unconditional line as the print),
`monitor/tests/test_quota_autoexit.py:4` and `monitor/board/done/S1-quota-auto-exit.W-1250.md:8`
(both describe the original freeze, not the relaunch), `monitor/inbox/20260728T204718Z-W-1620-…:193`
(unrelated).

## refusal analysis

For receipt #1, the line that would refuse **does not exist**: nothing anywhere consumes
`resume()`'s return code or stdout, and the drain at `:545` is not conditional on it. For receipt
#2, likewise: no consumer of `_self_driving` sends anything, and no `URGENT` file exists for the
ids named. In both cases I looked for a second mechanism that would make the claim true anyway —
another launcher writing no dispatch log, another module sending the urgent on scan's behalf — and
found none; `bus.py` writes `URGENT` only from its own CLI (`bus.py:22, :48`), and `board.py:799-843`
only *reads* it.

The honest limit: **why** the 358 `--worker` attempts never printed `started` cannot be established
without dispatch-log contents, which AUDITOR.md forbids me. That does not affect this verdict,
which concerns whether the loop ran at all.

## suggest

1. **Assign the result.** `quota.py:543` → keep the id in `requeue` when `returncode != 0` or when
   stdout contains `nothing matched.`; only then drain. One line, and it converts a false receipt
   into a real one. `reflex.py:215` should not append `quota:RESUMED(auto)` before inspecting `r`.
2. **Amend `DRIFT-20260729T2100Z:169-174`** — the retraction is void; restore the clause in the
   form given in §3. It is my lineage's report, so I can prepare the amendment on request, but I do
   not edit published audit conclusions without the monitor's ruling.
3. **Correct `monitor/mailbox/OPS-A.md:574`.** It is mainline and append-only, so the fix is a new
   superseding paragraph, not an edit. Until then every successor inherits the false receipt as a
   lesson.
4. **`scan.py:1115` should describe, not assert** — e.g. "建议发 urgent" — or the probe should
   actually send it. Asserting an action nobody performs is the same defect as §1 in a different
   subsystem, which is why they are one report.
5. Note for the ticket-writing habit, since it is the root cause of §1: the S1 acceptance criterion
   asked for a log line and not for verification. **A ticket that specifies the trace instead of
   the outcome buys the trace.**
