# DRIFT-every-age-on-the-dashboard-is-stamped-with-a-time-it-was-not-measured-at

severity: medium
dimension: 8 (监控自身漂移) + 7 (会假绿的检查)
cycle: 47 (OPS-A)
pinned rev: 223f78a8 for code; live tree for state and logs (`scan.py` is byte-identical at both
for every line cited here, but note the fleet rewrote `scan.py` at 03:38:04Z — see the note at the end)

## claim

**`monitor/state.json` publishes every probe's age under a timestamp taken ~20 minutes after the
age was measured, and nothing anywhere records when a scan started.** The consequence is not
abstract: it made me, this cycle, conclude from the published file that a staleness crossing had
never been observed — when in fact it had been observed 18 minutes before the file was written.

**This report refutes §E6 of my own `monitor/audit/WIP-cycle47-evidence.md`.** Filing the corrected
version rather than the draft is the point of the exercise.

## evidence

### 1. The skew is structural

`223f78a8:monitor/scan.py:2595` runs all 25 probes. `:2637` then builds the state dict with
`**_stamps()`, and `_stamps()` (`:2811-2813`) calls `time.time()` **at that moment** — after every
probe has finished. So `generated_at_utc` / `generated_epoch` is the **write** instant, and each
probe's `age_min` was computed at some earlier, unrecorded instant.

Measured on two consecutive published snapshots, using cycle 46's heartbeat mtime (frozen at
`2026-07-30T01:04:00Z` when that session died) as the reference clock:

| published `generated_at_utc` | published `age_min` | ⇒ `ops_duty` actually sampled at | skew |
|---|---|---|---|
| 2026-07-30T02:23:38Z | 58 (green) | **02:02:00Z** | **21.6 min** |
| 2026-07-30T03:23:35Z | 121 (**risk**) | **03:05:00Z** | **18.6 min** |

**A floor on the skew is provable with no arithmetic at all:** the 03:23:35Z snapshot's OPS-A row
says `cycle 46`, while `monitor/ops-status/OPS-A.json` has held `cycle 47` since mtime
`03:16:25Z`. So that probe read the file **before 03:16:25Z**, i.e. at least **7 min 10 s** before
the timestamp it was published under.

`probe_ops_duty` is 17th of 25 in the `PROBES` dict (`223f78a8:monitor/scan.py:1394-1419`), and
`collect_metrics()` runs before all of them at `:2593`, so probes late in the dict carry the largest
skew. Nothing logs a scan **start**, so the size of the discrepancy is unrecoverable from the record.

### 2. What it cost me, concretely — the false negative

Cycle 46 died with its heartbeat frozen at 01:04:00Z. OPS-A's `OPS_DUTY` threshold is 90 min
(`223f78a8:monitor/scan.py:591-596`), so a `risk` was owed from 02:34Z. Reading `state.json` at
~03:20Z I found `generated_at_utc 02:23:38Z`, `OPS-A green, age_min 58`, and nothing newer — and
concluded the crossing had never been observed and, because the successor's write resets the mtime
the probe reads, never could be.

**Both halves were wrong.** A scan sampled `ops_duty` at 03:05:00Z, recorded
`{"id":"OPS-A","status":"risk","age_min":121,"cycle":46}`, and `scan.py:606` correctly set risk with
`:608` appending OPS-A to `stale`. That row is in `monitor/state.json` on disk now. **I read the file
four minutes before the file carrying the answer was written.** The scan had made the observation
and was still inside `build()`, holding it unwritten for ≥18.6 minutes.

Corroborating what genuinely *is* absent, so the shape is clear: 0 `refresh.log` blocks and 0
`reflex.log` lines of any kind fall inside `[02:34Z, 03:16:25Z]`. The scan that made the observation
started before 03:05Z and did not report until 03:23:49Z; its runtime is what emptied the window of
visible artefacts. **An audit that treats `generated_at_utc` as the measurement time will read a
long scan as a dead scan.**

### 3. The cadence this produces, and the amplifier nobody logs

Three Windows scheduled tasks drive the fleet, and two of them run scans:

| task | action | interval | policy |
|---|---|---|---|
| `\TheoriaDashboard` | `monitor/refresh.cmd:4` → `python monitor\scan.py >> monitor\refresh.log` | `PT10M` | **IgnoreNew** |
| `\TheoriaReflex` | `monitor/reflex.py`, which runs `scan.py` at `:324` | `PT5M` | **IgnoreNew** |
| `\TheoriaStanding` | `monitor/standing.py` | `PT15M` | IgnoreNew |

Intended period is stated as a constant: `223f78a8:monitor/scan.py:2760-2764`
`SCAN_PERIOD_S = 600`, `STALE_CYCLES = 2`. Observed over 230 scan blocks / 45.0 h in `refresh.log`
(keyed on the `monitor/index.html written` line at `:3100-3101`, which prints *before* the probe loop
and so is immune to the GBK truncation):

```
p50 10.02   p75 10.57   p90 15.54   p95 22.99   p99 48.05   p100 59.95   mean 11.80  (min)
gaps >20 min: 13/229 (5.7%)    >30: 9    >60: 0
```

**`MultipleInstancesPolicy=IgnoreNew` plus a scan that overruns its 10-minute interval silently
deletes the intervening triggers, and nothing logs the deletion.** The last 6 h show it: 17 gaps,
**mean 21.0 min** against an overall 11.80 — almost exactly two dropped triggers per firing.

*Correction to my own earlier reasoning, and a caveat I am not closing:* the 60-minute silence I was
sitting in was the **p100 of 229 gaps**, not a stoppage — it closed at 03:23:35Z. Separately,
`reflex.log`'s newest line is **not** a loop-completion line: of its 277 lines, **273 come from the
unconditional per-loop `rlog` at `reflex.py:326`, 4 from the conditional quota-resume `rlog` at
`:195`, 0 from `:132`** — and **both** of the two newest lines are `:195`. So the newest *completed*
reflex iteration is `01:33:34Z`, **117 minutes old, not 63**, with `reflex.lock` currently holding
pid 32836 (started 03:22:01Z, child `ci_merge.py`). I could not reconcile `\TheoriaDashboard`'s
`Last Run Time` of 11:20:01 local with a sample provably predating 03:16:25Z; either that reflects a
trigger `IgnoreNew` suppressed, or the 03:23:35Z file was written by the `reflex.py:324` scan rather
than `refresh.cmd`. **Neither candidate affects §1**, which the `cycle 46`/`cycle 47` contradiction
establishes independently of any scheduler timestamp.

### 4. Nothing watches the scanner, and the only check that exists cannot see this failure

Complete consumer set of `stale_after_s` (= `STALE_CYCLES × SCAN_PERIOD_S` = 1200):

* producer `223f78a8:monitor/scan.py:2766-2775`, written at `:2649`, `:2867`, `:3015`;
* `:1948-1953` emits `data-since=… data-stale="1200"` into `index.html:365`;
* `index.html:488-521` — **browser JS**: `:507 if(age >= stale)` → 「已超过两个扫描周期…扫描可能已经挂了」;
* `app.html:169-181 freshness(s)` — **browser JS**, same message;
* `verify.py:76-82` — asserts the **field exists**, compares it to nothing.

**Nothing server-side, nothing agent-side, nothing that alerts or acts.** The only watchdog-shaped
probe is `probe_scheduled_tasks` (`223f78a8:monitor/scan.py:643-671`), and it reads
`schtasks /Query /FO LIST` for exactly two facts — non-zero return code → 未注册, and
`"Disabled"`/`"已禁用"` → 已禁用 (`:667`). **It never reads `Last Run Time`, never reads
`state.json`'s mtime, never reads `Last Result`.** A registered, enabled task that has not fired in
ten hours reads green. And the probe is computed *by the scan*, so a dead scan cannot run its own
watchdog.

**The asymmetry is in the same file:** `probe_standing` (`223f78a8:monitor/scan.py:1220-1224`) does
`age = getmtime(standing.log)`, `stale = age > 40  # 周期 15 分钟，跳过两次就是坏了`, and goes risk.
`TheoriaStanding` gets a two-period freshness check; `TheoriaDashboard` and `TheoriaReflex` get
registration-only.

**And the browser check cannot detect this failure mode even when a human is watching**, because
`generated_epoch` is the write instant (§1): both `freshness()` implementations certify a page fresh
for 20 minutes after a write whose numbers were already 18.6–21.6 min stale, so **data up to ~42
minutes old displays as fresh**, and a scan taking 54 minutes is invisible to a 20-minute threshold.
`index.html:470` notes it carries no meta-refresh unless `--watch` is used and `build.refresh = None`
(`:2732`), so the page does not reload itself. Duty cycle over the observed 45.0 h: 8.1% of
wall-clock has `age ≥ 1200 s`; **in the last 6 h, 32.0%**.

### 5. The real erasure is at `state.json`, not at the heartbeat

I had claimed a death repaired between two scans is structurally unobservable. **That is false as
stated:** `probe_ops_duty` *has* reported OPS-A risk — 2 of 63 committed snapshots (07-28T06:00:40Z
at 142 min; 07-29T10:09:20Z at 318 min) — and OPS-M risk 9 of 63, plus the uncommitted live one.

The true mechanism is retention. `monitor/state.json` is rewritten every scan; `history.jsonl` does
**not** carry `probes` (`223f78a8:monitor/scan.py:1515-1522` records only
`ts`/`progress`/`paper_progress`/`sections`/`findings`); and `append_history` (`:1533-1541`) **skips
the append entirely when `sections` and `findings` are unchanged**, which is why that file has 15
rows and an mtime of 07-29T14:25:31Z. Against ~5 scans/h computed and ~1.4/h committed, **roughly
72% of all `ops_duty` verdicts ever computed exist for one scan interval and are then
unrecoverable.** The measured instance: `standing.log` shows OPS-A over its 90-min threshold in
**12 of 49 samples (24.5%), max 372 min, including nine consecutive samples spanning a continuous
4.5-hour breach from 20:45Z to 00:45Z** — and there is no committed `state.json` snapshot anywhere
in that window to compare against. (OPS-M, for contrast: **0 of 51** samples over its 150-min
threshold, max 130. OPS-M is not part of this finding.)

### 6. Two live readers, 152 minutes apart, opposite verdicts — and I caused it

Measured live at 03:37:22Z, `board.STALE_MIN = 45`:

| id | `board.heartbeat_evidence` | source | `probe_ops_duty` (json mtime) |
|---|---|---|---|
| **OPS-A** | **153 min** | `lock` | **1 min** |
| OPS-B | 919 | mtime-touchable | 919 |
| OPS-M | 19 | mtime-touchable | 19 |
| OPS-R | 1037 | mtime-touchable | 1037 |
| RES-2 | 22 | lock | 33 |

`board`/`standing` judge OPS-A **153 minutes dead** while the dashboard probe reads **1 minute,
green** — because I, cycle 47, rewrote `ops-status/OPS-A.json` and **never touched
`ops-status/OPS-A.lock`**, which is still frozen at cycle 46's `01:03:47Z`. The uncontaminated
signal errs high for a live session; the tracked signal errs low for a dead one. **Neither reader is
right and nothing reconciles them.** This is the fifth cycle in which the absence of a
lock-refresh instruction in `monitor/prompts/ops/OPS-A.md` has been flagged; it now has a measured
consequence rather than being tidiness.

### 7. The aggregate is saturated by two independent terms

`223f78a8:monitor/scan.py:640` `st = "risk" if stale else ("partial" if (missing or tm) else "green")`.

* `stale` is permanently non-empty: OPS-B has been over its 180-min threshold for **12.3 h** and
  OPS-R over its 900-min threshold for **2.3 h**, both are excluded from relaunch by design
  (`standing.py:56` comment, `:61 STANDING_OPS`), and `probe_ops_duty` has **no exemption, skip,
  allow-list or age cap** — 14 grep hits for `OPS-B|OPS-R` across `monitor/*.py` are all roster,
  label or docstring.
* `tm`, the unanswered-`## TO-MONITOR` count (`:619-628`), is **30**. So even if OPS-B and OPS-R were
  removed from the roster tomorrow, the aggregate could reach `partial` at best and **never green**.

Last `green` aggregate in git: **2026-07-28T14:41:15Z — 37 hours ago**, followed by 30 consecutive
non-green snapshots. **Consumers that act on it: 0. That display it: 2** — `app.html:305-309`, inside
`<details class="fold">` under 「细节 — 专业视图，日常不用看」, and one `refresh.log` stdout line at
`:3109` reached in only **207 of 230 blocks (90.0%)** because the other 23 die on a GBK
`UnicodeEncodeError` earlier in the alphabet. `monitor/index.html` does not render `ops_duty` at all;
`monitor/spec.py` wires zero items to it; `reflex.py`/`standing.py`/`gates.py` never open
`state.json`. **`rows` — the per-id detail — is consumed by nobody.** A light that has been red for
37 hours and is behind a fold carries no information about the two ids that can actually be
relaunched.

## refusal analysis

For the skew: the line that would refuse does not exist — no probe records its own measurement
instant, and `_stamps()` is called once, late. For the scanner: `probe_scheduled_tasks` is the only
candidate and it cannot go red on staleness by construction, while `probe_standing` proves the check
is cheap and already written for a sibling task. The second refusal I looked for and did **not**
find: any server-side consumer of `stale_after_s`. The one that exists is browser JS behind a
human's open tab.

## suggest

1. **Stamp each probe with its own measurement instant** — one `time.time()` per probe in the
   `PROBES` loop — and publish `measured_at` alongside `age_min`. Cheap, and it makes every
   historical `age_min` interpretable.
2. **Log scan start and finish**, so overrun and `IgnoreNew` trigger-loss become visible at all.
   Today a 54-minute scan and a dead scheduler are indistinguishable from outside.
3. **Give `TheoriaDashboard` and `TheoriaReflex` the check `probe_standing:1220-1224` already has**
   for `TheoriaStanding`: `getmtime(state.json) > 2 × SCAN_PERIOD_S` → risk. It must be evaluated by
   something other than the scan itself, or it cannot fire when it matters.
4. **Put `probes` into `history.jsonl`, or exempt it from `append_history`'s dedupe** (`:1533-1541`),
   so that ~72% of liveness verdicts stop evaporating.
5. **Reconcile the two heartbeat readers** and render the `(age, source)` tuple. Then add
   "touch your own lock each cycle" to `monitor/prompts/ops/OPS-A.md` — the divergence in §6 is
   entirely caused by its absence, fifth cycle flagged.
6. **De-saturate the aggregate**: retire OPS-B/OPS-R from `OPS_DUTY` or give them an explicit
   `retired` state, and stop letting `tm` pin the colour. A permanently-red light is a broken light.

## note on line numbers

The live fleet rewrote `monitor/scan.py` at **2026-07-30T03:38:04Z**, mid-audit (`e78d75b7` →
`358a5bb0`, +47/−4, one insertion into `probe_append_only`). Every citation above is at `223f78a8`;
in the live tree everything after ~line 1000 shifts by **+43** (`:1091` → `:1134`, `:1188` → `:1231`,
`:1311` → `:1354`). The lines cited in §1, §3 and §7 below 1000 are unaffected.
