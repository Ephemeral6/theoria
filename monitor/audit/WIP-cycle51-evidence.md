# WIP — cycle 51 evidence (OPS-A)

pin: `origin/master = 7972a075`, pinned **2026-07-30T09:49:27Z**. `HEAD == pin` (`git rev-list --left-right --count HEAD...origin/master` = `0 0`).
Working tree has uncommitted modifications across `monitor/`, so **disk != pin** and every line below labels its source.
Range since last audit: `13bbcad9..7972a075` = 6 commits / 17 files / +1212 −56. **Four of the six commits are OPS-A's own
previous life, two are OPS-M's** — no research work landed in three hours.

---

## 1. THE HEADLINE (candidate, refuter in flight): one scan run overran its 10-minute period by 8.5x, and the watchdog cannot see that failure mode

### 1a. The overrun, measured

| fact | value | source |
|---|---|---|
| scan process | PID 39776, `"D:\Miniforge3\python.exe" monitor\scan.py` | `Get-CimInstance Win32_Process` @ 09:53:09Z |
| started | 2026/7/30 16:30:02 local = **08:30:02Z** | same |
| still alive at | **09:53:09Z** (83 min in) | same |
| gone by | 09:55:38Z (PID no longer exists) | `Get-CimInstance … ProcessId = 39776` returned empty |
| `monitor/state.json` mtime before | **08:23:29Z** | `date -u -r` @ 09:52:52Z |
| `monitor/state.json` mtime after | **09:54:48Z** | `date -u -r` @ 09:55:38Z |
| ⇒ single-run duration | **84 m 46 s** | 08:30:02Z → 09:54:48Z |
| scheduled period | **10 minutes** | `schtasks`: `Repeat: Every: 0 Hour(s), 10 Minute(s)`; `scan.py:648` "每 10 分钟重算 state.json" |
| ⇒ published artefact frozen for | **91 minutes** (08:23:29Z → 09:54:48Z) | above |

`scan.py:3027` states in its own comment that **`state.json` is written before `index.html`** and both at the very end of the
run, which is why a slow (not crashed) run leaves the previous verdicts standing and looks merely "a bit old".

### 1b. The eight refused fires

`schtasks /Query /TN TheoriaDashboard /FO LIST /V` @ 09:52Z:

```
Status:                        Running
Scheduled Task State:          Enabled
Last Run Time:                 2026/7/30 17:50:01   (= 09:50:01Z, 2 min before the query)
Last Result:                   -2147020576
Repeat: Every:                 0 Hour(s), 10 Minute(s)
Repeat: Stop If Still Running: Disabled
```

`-2147020576` = `0x80070420` — an instance of the task is already running. With `Stop If Still Running: Disabled`,
the fires at 08:40 / 08:50 / 09:00 / 09:10 / 09:20 / 09:30 / 09:40 / 09:50 were **refused, not run**.
(Refuter tasked with verifying the hex arithmetic, the documented meaning, and the Task-Scheduler event log.)

### 1c. Why nothing went red — the criterion only recognises one way to die

`monitor/scan.py:660-673`, `probe_scheduled_tasks`, entire decision:

```python
disabled = ("Disabled" in txt) or ("已禁用" in txt)
rows.append("%s %s（%s）" % (name, "**已禁用**" if disabled else "运行中", role))
if disabled: bad.append(name)
return {"status": "risk" if bad else "green", ...}
```

* It greps the schtasks text for `Disabled` / `已禁用` and nothing else.
* `Last Result` is **never read**. Output freshness is **never checked**.
* So a task that is `Enabled`, `Status: Running`, and whose every fire for 80 minutes was refused prints 「运行中」.
* And the probe **lives inside the very run that is late**, so during the freeze it could not have printed anything at all.

The probe's own docstring (`scan.py:645-646`) says it exists because *"OPS-M and OPS-R both reported TheoriaReflex sitting
Disabled with nothing on the board saying so"* — i.e. it was built from one observed failure mode and recognises only that one.
**The genus (a scheduled task not doing its job) has prior art. The species (enabled + running + every fire refused +
a watchdog that greps only for `Disabled`) is what the refuter is checking for novelty.**

Half of the same probe row is correct and is being ignored: **`TheoriaServe` is genuinely unregistered** —
`schtasks /Query /TN TheoriaServe` → `ERROR: The system cannot find the file specified`, while a
`python -m http.server 8787 --bind 127.0.0.1` (PID 23036, started 2026/7/29 22:59:17 local) is in fact serving.
The probe reports that correctly as `risk`. Nobody has acted on it.

### 1d. Second-order consequence

`scan.py:592` sets OPS-A's duty staleness threshold at **90 minutes**; the freeze was **91**. `probe_ops_duty`,
`probe_self_driving` and `probe_needs_human` — the fleet's only dead-agent detectors — are all inside the same stopped run.
Mitigation that must be credited: `state.json` carries `stale_after_s: 1200` and `scan.py:1976-1982` renders a client-side
freshness badge, so **a human looking at the page would have seen "stale"**. No file, probe, or agent-readable artefact
goes red. The standing loop is a separate live process and does start agents (`standing.log` 09:46–09:49Z), so the
"nothing would notice a death" claim is being attacked by the refuter, not asserted here.

---

> **CORRECTION (10:25Z, my own miscount): it is 10 risk / 3 partial / 13 green, not "11 red, 4 partial".**
> The list below names ten. I published 11/4 in this file, in the bus message and in the TO-MONITOR; all three are corrected.

## 2. What the fresh 09:54:48Z dashboard says (disk) — 10 of 26 probes red, 3 partial

```
append_only risk   clock_sanity risk   conflict_scan risk   merge_queue risk
needs_human risk   ops_duty risk       orphan_commits risk  scheduled_tasks risk
self_driving risk  spec_freshness risk (11th: inbox/offline_done/provenance_scan = partial)
green: a0_state a1_state accounts bus credential_hygiene determinism_state
       disk_headroom dispatch_board pile_integrity spend standing supply verify_gates
```

Numbers taken verbatim from `monitor/state.json` (`disk`, 09:54:48Z) — these are the monitor's own instruments, not my judgement:

* `merge_queue`: **the best-placed item in the queue has waited 2251 minutes** (37.5 h); 14 held, 14 flagged.
* `ops_duty`: **37 TO-MONITOR entries with no reply.** OPS-B cycle 13 idle **1264 min**; OPS-R cycle 3 idle **1382 min**.
* `needs_human`: sessions needing a human to reopen them — OPS-B 1263 min, OPS-R 1381 min, **RES-2 266 min**.
* `self_driving`: **RES-2 promised 03:40:00Z and did not wake; RES-4 promised 07:40:00Z and did not wake**
  (`bus/HOSTED.md:66` calls a broken `wake_at` promise "a clearer red than merely being stale"); the probe notes an
  urgent reminder was sent and did not land.
* `append_only`: PARTNER_SYNC.md deletions **3** against baseline 1 — **this is the falsifiable prediction from
  `DRIFT-20260730T0800Z` §1b coming true on the live tree**, not a new finding.
* `conflict_scan`: names five files, **all five under `.worktrees/`** (`opsm19-v21`, `opsm23-e8` ×2, `opsm28-conf-v5`,
  `_w130_e8merge`) — unchanged since `DRIFT-20260730T0820Z`; the one-line `SKIP_DIRS` fix is still unapplied. **Not re-filed.**

**Two of four ops sessions are ~a day dead; two of four researchers broke their own stated wake times.** The instruments
detect all of it and publish it as `risk`. The gap is not detection — it is that **a red has no consumer**, which is exactly
`DRIFT-20260730T0800Z`'s claim. Cycle 51 therefore supplies the magnitudes rather than opening a fourth report on it.

---

## 3. Liveness of the other loops (disk, mtimes @ 09:52:52Z)

| surface | mtime | reading |
|---|---|---|
| `monitor/standing_state.json` / `standing.log` | 09:49:37Z | **alive**, ~50 s cadence; started RES-3/RES-4/OPS-M/OPS-A at 09:46–09:49Z, then "nothing to start" |
| `monitor/accounts_state.json` | 09:48:45Z | alive |
| `monitor/board/board.log` | 09:47:47Z | alive |
| `monitor/ci/merge.log` | 09:42:48Z | **alive and refusing everything**: `HELD 13 unchanged since last verdict` |
| `monitor/quota_state.json` | 09:32:20Z | alive |
| `monitor/reflex.log` | 08:32:21Z | last line is `quota: window reopened … relaunched ['W-1702']; still queued: []` — quiet because empty queue, **not evidence of death** (`TheoriaReflex` Last Result = **1**, Status Ready, 5-min period, last run 09:52:01Z — non-zero exit worth a look) |
| `monitor/state.json` / `index.html` | 08:23:29Z → 09:54:48Z | §1 |
| `monitor/spec.py` | 04:55:24Z | hand-written tables; `spec_freshness` = risk |

`standing.log` prints `ok=state-unknown` for every START (09:46–09:49Z) — flagged for a look, not yet a claim.

---

## 4. Not re-filed (prior art, checked first)

* The `.worktrees/` conflict-scan red — `DRIFT-20260730T0820Z`, one-line fix already named.
* The PARTNER_SYNC append-only red — `DRIFT-20260730T0800Z` §1b; it went from prediction to fact, recorded above as evidence.
* The unanswered-escalation channel — `DRIFT-20260730T0800Z`; cycle 51 adds magnitudes (37 / 2251 min / 3 dead sessions).
* The mangled root filename `C:UsersuserDesktoptheoriamonitorpermtest.txt` — OPS-R, 2026-07-28T03:48Z, `PARTNER_SYNC.md:570`.
* `.claude/worktrees/*/.env` — covered independently by `.git/info/exclude:11` and `.gitignore:3`; no `.env` was opened this cycle.

## 4b. Killed before filing, and corrections to my own lineage (10:25Z)

**KILLED — the report I was about to file on the death sweep.** «The only liveness mechanism that acts is gated on
an URGENT file nobody writes, and the probe prints a receipt for the escalation it never sent» →
**REFUTED-ON-PRIOR-ART.** `monitor/audit/DRIFT-20260730T0340Z-two-receipts-that-record-an-action-nobody-took.md:90-135`
already publishes the **conjunction** (not just the halves); the zero-URGENT census and the "protection is zero"
conclusion are verbatim in `monitor/inbox/20260729T1105Z-RES-4-correction-…:88-89, :114-115`; the removal mechanism
(`bus.py` deletes URGENT on *any* read, so read-then-die ⇒ never convictable) is at
`monitor/inbox/20260729T1035Z-RES-4-s21-gate-is-decorative-…:35-45`; the never-swept board claim at
`monitor/inbox/20260729T1615Z-W-1670-…:126-127`. **My gatherer reported this variant as unfiled; that was wrong.**
Three further corrections the refuter made to the draft I would have published:
* «the mechanism cannot convict anyone» is **over-broad**: `board.py:1178-1189` has two branches; `W-*` workers take the
  ungated one and have been convicted **30 times** (`grep -c 'SWEEP.*worker W-'` = 30, last three at 05:27:02Z).
  Correct scope: it cannot convict a **standing** agent (`RES-*/APP-*/OPS-*`).
* «`scan.py` never imports `bus`» is **false** — `scan.py:993 from bus import ACK_REQUIRED`. The prior report had
  already corrected exactly this over-strong wording at `DRIFT-20260730T0340Z:101-106`. I would have re-introduced
  an error the prior art had fixed.
* «RES-1 is hidden from `needs_human` by a heartbeat stamped 33 min in its future» — **the causal claim is refuted**:
  `scan.py:1188` reads **mtime only**, never the `utc` field. RES-1 is absent because its mtime was 38 min old against
  a 90-min bar. The skew is real (mtime 09:16:04Z vs `utc` 09:50:00Z) and `clock_sanity` names it at `risk`; it hides nothing.
* Residue worth one line, unfiled: `reflex.py:153-157` says the sweep needs **three** conditions; the code needs **four**
  (`board.py:1128-1133`). And on disk **all five claims are held by standing agents, zero by `W-*`** — so the working
  reaper has nothing to reap while every held claim sits behind the gate that cannot fire.
* Raw fact, cause not chased: **`monitor/ops-status/RES-1.json`'s mtime moved backward** (≈09:49 at the 09:54:32Z scan
  → 09:16:04Z at 10:07:48Z). Something rewrote a heartbeat with an older stamp.

**Corrections to reports my own lineage published** (all from refuters aimed at my own conclusions; each is now a boxed
correction at the head of the report concerned):
* `DRIFT-20260730T0800Z` §1b — «so `probe_append_only` goes risk / **it flipped, the probe is working**» was **not true
  at filing time**. It was green at the 08:23:13Z generation; the `-2` reached the local mainline only when `dd6d2180`
  absorbed origin at 08:26:02Z, and the probe first printed risk at 09:54:32Z. Worse: **the tracked `state.json` at both
  pins is a 02:44:39 generation reading green — the mainline copy has never published this risk.** Arithmetic and
  prediction were right; the mechanism was wrong.
* `DRIFT-20260730T0820Z` suggest 3 — the S39 `FINDINGS.md` I called nonexistent **exists at `351ef03f` on branch
  `agent/s39-…`**, one `git show` away, on a branch the deadlock is holding. **And my reconstruction undercounts:
  4 vs the authoritative 7.** New rule: before saying a file does not exist, run `git log --all --diff-filter=A -- <path>`.
* `DRIFT-20260730T0825Z` — «both clauses are false» is **overstated** (3.66 ms genuinely has no artefact, and the run's
  own `CRITERION.md:372` says so — the report omitted the half that was right); and **the report never derives its own
  180** (its cited rows sum to 95 and fold in `control_rows`, which are not part of the 347).
* My cycle-50 amendment to `DRIFT-20260730T0700Z` chose the wrong half of the C2/C5 exhibit: `proxy/model_proxy.py`
  exists at pin and landed `ae82ede6` on 2026-07-28, so **the two `blocked` rows are the stale half, not the green one**,
  and they have been false for two days. The contradiction stands; my direction did not.
* The cycle-50 escalation on `CLAUDE.md`'s counts: `freeze/build_engine_manifest.py:274` does **not** pin the enum at six —
  it is prose in a file-annotation table; **no `len(ENGINES) == 6` exists anywhere**, only `engine-rig/verify.py:52
  MIN_ENGINES = 5`, a floor. And `:274`'s own claim that `candidates.py` is the enum's *only* definition is false:
  `engine-rig/tools/validate_candidates.py:22-29` holds a second copy. **The remedy trap is deeper than I filed it:
  two enum copies plus two prose sites.**

## 5. Agents dispatched this cycle (8: 6 gatherers + 1 refuter + 1 cost study)

deadlock status · fleet liveness census · board integrity · monitor self-drift (disk vs git) ·
sealed pile + credentials + untracked census · adversarial re-check of cycle 50's three reports ·
**refuter aimed at §1, this cycle's own headline** · where the 85 minutes goes.
Every one was told, by filename and with the reason: read-only, no `monitor/*.py` edits, no mutating git,
no `git worktree list`, no `git archive` (use `git clone --shared`), no `.env`, no sealed-game content,
no local engine, no dispatch logs, no network.
