# DRIFT-a-reset-ate-a-heartbeat-and-the-probe-reads-the-timestamp-it-forged

severity: medium (`probe_needs_human`) / low (`_self_driving`) — **deliberately not high; see §6**
dimension: 8 (监控自身漂移) + 7 (不可能变红／会假绿的检查)
cycle: 47 (OPS-A)
pinned rev: 223f78a8

**This is a DISCHARGE, not a discovery.** The core observation is published at
`monitor/audit/DRIFT-20260730T0014Z-…:133-139`, which closed with *「这条与本报告不同因，建议单独
下发」* — recommend issuing separately — and carried at `monitor/audit/state.json:61` and
`monitor/mailbox/OPS-A.md:870,:920` under the heading 欠账. Cycle 46 died before paying it. Origin
credited; §5 names what is actually new.

⚠️ **`monitor/scan.py` was rewritten by the live fleet at 2026-07-30T03:38:04Z, mid-audit**
(blob `e78d75b7` → `358a5bb0`, +47/−4, one insertion into `probe_append_only`). All three probes
below survived untouched, but **every scan.py line number shifted by +43.** Citations are pinned;
the live equivalents are given so a reader greping the working tree finds them.

| | @223f78a8 | live tree (`358a5bb0`) |
|---|---|---|
| `probe_ops_duty` getmtime | `:612` | `:655` |
| `_self_driving` def / getmtime / `>45` | `:1073` / `:1091` / `:1100` | `:1116` / `:1134` / `:1143` |
| `probe_needs_human` getmtime | `:1188` | `:1231` |
| `board_mod.heartbeat_age` call | `:1311` | `:1354` |

## claim

**A `git reset --hard` destroyed a committed heartbeat and left the reverted file wearing a fresh
mtime; three probes judge session liveness from that mtime alone; and the one of them that reaches
the human fails toward "✓ nothing to do today."**

## evidence

### 1. The written rule, stated correctly (my first draft overstated this)

`occupied()` — `standing.py:351`, the function gating whether to spend money on a launch — is often
summarised as ruling mtime out. **It does not.** It reads `getmtime` on the tracked json itself at
`git show 223f78a8:monitor/standing.py:275` and a lock mtime at `:249`. The author states the actual
rule twelve lines below the famous comment, at `:273-274`:

> `mtime 单看会被一次 merge 摸新（已实测），但那种情况下 cycle 下一跳就不再变，于是最多骗过一跳。`
> `两个都要求，才既不误杀活人、也不替死人站岗。`

So the rule is **"mtime alone is not sufficient evidence,"** not "mtime does not count." The precise
and defensible contrast:

> `occupied()` requires mtime freshness **in conjunction with** a monotone `cycle`, plus a
> first-sighting suppression at `:264-267` whose comment reads 「缺省值倒向好消息」. The three
> probes require **mtime alone** — no second signal, no suppression.

### 2. `board.py`'s "single source of truth" block is false, and points at the wrong probe

`git show 223f78a8:monitor/board.py:62-64` (`:53-55` in the older worktree copy) asserts it is the
sole origin of the threshold and that *「scan.py 的 self_driving 探针 import 这两个名字」*.

`git grep -n -E "STALE_MIN|heartbeat_evidence" 223f78a8` — widened to all files, not just `*.py`:
`monitor/board.py` (self-references), `monitor/runs/…/probe_unreachable.py:93`,
`tests/test_board_no_third_value.py`, `tests/test_standing_sweep.py`, `fleetkit/fleetkit/board.py`.
**`monitor/scan.py`: zero.** `_self_driving` has exactly one import, `import time as _t` (`:1078`),
and `:1100` is the literal `stalled = age > 45`. No `importlib`, no `getattr`, no star-import.

**The sharper form:** scan.py *does* depend on board.py — `223f78a8:monitor/scan.py:1311` is
`"idle_min": board_mod.heartbeat_age(aid)` inside `_fleet_rows`, which correctly routes through the
S28 lock-preferring wrapper. So scan.py has **one** call site that uses the shared criterion and
**three** that bypass it, and board.py's comment names the one probe that doesn't use it while
missing the one that does.

**And the block contradicts the function ten lines beneath it.** `:63-64` orders you to read mtime
and *not* the self-reported `utc`. The S28 docstring at `:74-75` says the opposite — the json is
**git-tracked**, so *「任何 merge / reset / autostash 都能把一个死会话的心跳摸活」* — and `:95`
returns the mtime branch tagged `"mtime-touchable"`. Both answer the same question and give opposite
answers. `:63` is pre-S28 doctrine left standing after S28 replaced the function underneath it; it
survives because `:65 STALE_MIN = 45` sits between them and a reader stops at the constant.

### 3. The incident: a reset ate OPS-R's heartbeat, and the repository still holds the corpse

This is not inference. The destroyed version is in the object store.

```
reflog, TZ verified by `date` → +0800, so 18:19:43+0800 = 10:19:43Z
  18:16:47+08  d659b75a  commit: OPS-R cycle 4: nothing observes the monitor…
  18:18:36+08  eae853b8  pull -q --rebase --autostash origin master
  18:19:43+08  e5f0bb40  rebase (abort): returning to refs/heads/master
  18:19:43+08  eae853b8  reset: moving to origin/master
```

* `git show d659b75a:monitor/ops-status/OPS-R.json` → **`utc 2026-07-29T10:20:00Z, cycle 4`**
* `git show eae853b8:monitor/ops-status/OPS-R.json` → **`utc 2026-07-29T05:59:00Z, cycle 3`**
* `git diff --name-status e5f0bb40 eae853b8 -- monitor/ops-status/` → **`M OPS-R.json`** (87 files
  in the reset overall)
* `git merge-base --is-ancestor d659b75a HEAD` → **exit 1**; `git log --all --oneline | grep "OPS-R
  cycle"` → 1, 2, 3. **There is no cycle 4 anywhere in the repository.**
* Today: mtime `2026-07-29T10:19:52Z`, content `utc 05:59:00Z, cycle 3`, `git status --porcelain`
  **clean**, last commit touching it `de90ba90 @ 05:58:52Z`.

**The competing explanation is dead.** OPS-R cannot have written the file at 10:19:52Z with a stale
`utc`, because the bytes on disk are byte-identical to `eae853b8`'s blob committed four hours
earlier — and OPS-R's *actual* 10:20Z write exists, in a different commit, carrying `cycle: 4`.
`reset --hard` discarded it.

**Why the mtime refresh is entailed rather than guessed** — synthetic repo outside this tree, with
the negative control doing the work:

| case | content after | mtime |
|---|---|---|
| NEG-1: `status` / `log` / `diff` / `grep` | unchanged | **unchanged** |
| **NEG-2: `reset --hard` where the file is IDENTICAL in both trees** | unchanged | **UNCHANGED** — while a sibling that *did* differ was touched |
| POS-A: file dirty, then `reset --hard` | reverts | **now** |
| POS-B: newer content committed, then `reset --hard` back | reverts | **now** |
| POS-C: `pull --rebase --autostash` with the file dirty | **preserved** | — |

NEG-2 is load-bearing: **git touches only files that actually differ.** `OPS-R.json` is in the
reset's diff, so the fresh mtime follows necessarily. POS-C also explains the reflog shape — the
autostash pull does not clobber; the abort-then-`reset --hard` did.

**Two corrections I am making against my own earlier draft.** (i) I called the 9-second gap between
the reflog entry and the mtime "causally tight." It is **consistent, not probative** — measured on a
3000-file reset the ref-update-to-write delay is +0.65 s, which does not scale to 9 s from 87 files.
The entailment in NEG-2 plus the missing `cycle: 4` is what carries this, and it carries it
completely. (ii) `d659b75a` was committed at 10:16:47Z while declaring `utc 10:20:00Z` — the
hand-typed-forward-drift defect is *also* present, **on the version that was destroyed**. Two
defects on two file versions; do not conflate them.

**Frequency, stated against me.** Of 7 live heartbeats: 4 have `mtime == utc` exactly; RES-1
(mtime 03:35:11Z vs utc 03:40:00Z) and RES-2 (03:03:58Z vs 03:22:00Z) currently have mtime **older**
than the self-report, i.e. mtime is the *conservative* number for them right now. **The dangerous
direction is observed exactly once — OPS-R, in an incident.** 112 of 1004 commits in 7 days touch
`monitor/ops-status/`, but **0 of 163 merges in the last 24 h** did: the firing path is `reset`
(~6 in the reflog), not `merge`. This is a latent defect with one documented firing, not a false
green presently on screen.

*Checked and deliberately not filed:* the same reset deleted four `RES-*.lock` files from the
worktree. They are untracked at `223f78a8` and at HEAD, ignored by `.gitignore:24` and
`monitor/.gitignore:14`, and `.gitignore:20-23` already documents that incident by name. Fixed and
filed already.

### 4. The consequence splits, and only one half matters

`_self_driving` is **recorded, rendered, and unescalatable.** `223f78a8:monitor/scan.py:2648` is the
only route from a probe into a verdict (`probed = bool(it.get("probe") and it["probe"] in
probe_results)` → `:2651 _reconcile`), and `monitor/spec.py` has exactly **5** `"probe":` bindings
(`:81, :110, :120, :135, :162`). **5 of 25 probes are gate-bound; 20 are not**, and `self_driving`
is one of the 20 — so it can never reach `_reconcile`, `verdict_overrides`, or `p1_green`.
`monitor/verify.py:79-82 REQUIRED_STATE_FIELDS` lists 13 fields and `probes` is absent.
`monitor/index.html`: zero occurrences. Consumers: the `PROBES` dict, `state.json`, `app.html`'s
**collapsed** `实况探针` fold (1 row of 25), one stdout line, and 6 tests. It *can* go red — three
`== "risk"` assertions in `tests/test_session_liveness.py` — but **the suite sets mtime by
`os.utime` fiat and never compares mtime against the `utc` field, so it is structurally blind to
this defect.**

`probe_needs_human` is the one that matters, and it is **above the fold**. `monitor/app.html`:

```
285   const nh = s.probes?.needs_human || {};
286   const restarts = nh.rows || [];
287   h += "<h2>今天需要你做的事</h2>";          <- bare <h2>, not inside any <details>
289-291  重开 ${r.id} · ${r.name} … 粘贴 <code>${r.prompt}</code>
297-299  if empty: "✓ 今天什么都不用做。会话自愈…"
303   <details class="fold">                      <- the fold starts HERE
308     <summary>实况探针…</summary>              <- self_driving lives in here
```

**The failure mode is a false all-clear, not a noisy red.** A git touch makes `age` *smaller*, which
is exactly the direction that empties `dead`; `probe_needs_human` (`223f78a8:1191-1193`) then returns
`green` / 「六个 App 会话全部在岗，无需你出手。」 and `app.html:297-299` prints **✓ 今天什么都不用做**.
The contaminated input feeds the only channel that tells the human which session to reopen and which
boot prompt to paste (`prompt: monitor/prompts/ops/<ID>.md`).

### 5. What is actually new here, since the core was already published

1. **Two more readers.** `DRIFT-…0014Z:139` named `_self_driving` only. `probe_ops_duty` (`:612`)
   and `probe_needs_human` (`:1188`) do the same thing, and the second escalates to a human.
2. **A delivered suggestion tells the fleet to lean on mtime.**
   `monitor/audit/DRIFT-20260729T2313Z` (severity high) recommends at `:102` that `age_min`
   「照常由 mtime 计算 — mtime 永远读得到」. A high-severity report's accepted advice points the
   opposite way from S28's docstring. That live conflict, not the mechanism, is the strongest reason
   this needed its own filing.
3. **S28 fixed `board.py` and walked past the three `scan.py` probes.** `board/done/S28-…:30-36`
   item 4 is `board.py:56` — *with this same OPS-R reflog evidence already in hand.* The unfiled
   thing is the gap, not the mechanism.
4. **The forensics**: the destroyed `cycle: 4` blob, and the NEG-2 control that makes the mtime
   refresh entailed.
5. **`fleetkit` ships the bug and the false comment.** `fleetkit/fleetkit/board.py:52` carries
   *「scan.py 的 self_driving 探针 import 这两个名字」* **verbatim**, in a package whose complete
   contents are `README.md`, `KNOWN_TRAPS.md`, `verify.py`, `fleetkit/{__init__,board,bus,config}.py`,
   `tests/test_fresh_repo.py` and two MANIFESTs — **no scan.py and no standing.py exist in it**.
   Its `heartbeat_age` (`:61-66`) is the **pre-S28 mtime-only version**: no lock branch, no tuple,
   and `heartbeat_evidence` has zero hits anywhere in `fleetkit/`. `README.md:3-4` presents it as the
   extracted core for reuse in other projects, and no code imports it, so nothing will ever notice
   the divergence. **The reusable artefact froze the exact defect S28 fixed, under a comment claiming
   to be its single source of truth.**
6. **`OPS-B`'s `utc` is `"2026-07-29T12:16Z"`** — no seconds, so it does not parse under the
   `%Y-%m-%dT%H:%M:%SZ` format used throughout `monitor/`.

### 6. Severity, argued down

The related prior filing is **high** because it hits `board.py`, whose `heartbeat_age` gates lane
reservation and claim sweeps. These three hit a dashboard. `probe_needs_human` is **medium** — real
consequence, bounded: not a spend gate, not a red gate, no data loss. `_self_driving` is **low**;
its one genuine defect is the fabricated receipt at `:1115`, which is a *truthfulness* defect rather
than a liveness one and is filed separately in
`DRIFT-20260730T0340Z-two-receipts-that-record-an-action-nobody-took.md`. **Do not inherit the high.**

## refusal analysis

For the three probes, the refusal that would exist is a second signal, and there is none: each
computes `age` from one `getmtime` and compares it to one constant. The second refusal I *did* find
runs the other way and narrows the finding — `occupied()`, on the money path, demands mtime **and**
a monotone cycle, which is why no launch decision is corrupted by this. The damage is confined to
what humans read.

## suggest — and this pre-empts the obvious wrong fix

**Do not just route the probes through `board.heartbeat_evidence`.** It prefers the lock but **falls
back to `getmtime` on the tracked json when no lock exists** (`223f78a8:monitor/board.py:89-95`),
and `OPS-R.lock` and `OPS-M.lock` **do not exist** right now while OPS-R is on
`probe_needs_human`'s roster. So that fix returns the identical contaminated number for the very
file this case is built on, tagged `"mtime-touchable"` and then discarded, because nothing renders
the source. Instead:

1. **Every standing session writes a lock each cycle.** OPS-A, OPS-M, OPS-B and OPS-R currently have
   no instruction to; only `prompts/ops/RES-1.md:31` does. (Carried five cycles.)
2. **Have the probes consume the `(age, source)` tuple and render the source**, so a
   `"mtime-touchable"` number is visibly weaker than a lock-derived one.
3. **Cross-check the content `utc` against the file mtime and report the DIVERGENCE** rather than
   picking a winner. This is the only check that would have caught OPS-R, because the tell was the
   261-minute gap — neither number alone was anomalous.
4. **Delete `board.py:62-64`'s claim or make it true**; and fix `fleetkit/fleetkit/board.py:52`
   before anyone reuses it.
5. Reconcile `DRIFT-20260729T2313Z:102`'s accepted recommendation with S28's docstring; today they
   contradict, and the contradiction is the reason this keeps getting rebuilt.
