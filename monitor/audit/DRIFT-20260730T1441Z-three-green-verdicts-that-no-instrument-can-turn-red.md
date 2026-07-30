# DRIFT-three-green-verdicts-that-no-instrument-can-turn-red

severity: high
dimension: 8 (监控自身漂移) → 7 (单向门 / 不可能变红的检查)
cycle: OPS-A 53
pin: `origin/master = d1da2c9c` @ 2026-07-30T14:18:36Z (HEAD moved to `ea4f6af6` mid-cycle;
`monitor/scan.py` and `monitor/spec.py` are byte-identical across the gap, so every claim
below holds at both). Live measurements labelled `disk`.

## claim

**Three separate green verdicts are being published right now, and in each case there is no
negative sample anywhere in the tree that could have made them red.** They are not three
mistakes; they are one shape — a verdict whose evidence base structurally excludes the failure
it is supposed to detect. One of them was caught misreporting a live, ongoing failure in the act.

## evidence

### 1. `probe_scheduled_tasks` reports a failing task as healthy — caught in the act

`monitor/scan.py:665-666` (pin == disk):

```python
out = childio.run_console(["schtasks", "/Query", "/TN", name,
                           "/FO", "LIST"])
```

**No `/V`.** The entire health test is `monitor/scan.py:671`:

```python
disabled = ("Disabled" in txt) or ("已禁用" in txt)
```

Running the probe's exact command returns **six fields** — `Folder`, `HostName`, `TaskName`,
`Next Run Time`, `Status`, `Logon Mode`. **`Last Result` is not among them. Neither is
`Scheduled Task State`.** So the one criterion can only ever match the `Status` line, which
reports *instance* state, not enablement: the variable named `disabled` is checking the wrong
field even for its own stated purpose.

With `/V`, the same task at the same moment:

```
Scheduled Task State:  Enabled
Repeat: Every:         0 Hour(s), 5 Minute(s)
Last Result:           -2147020576        (0x800710E0 — a failure HRESULT)
```

And independently of `schtasks`: `monitor/reflex.log` had not been written for **356 minutes
against a 5-minute period — 71× the period**. The probe published **`TheoriaReflex 运行中`**.

Both previously-suggested negative samples are still absent at pin and disk: the string
`Last Result` appears nowhere in `monitor/scan.py`; the probe never calls `getmtime` and never
opens `reflex.log`. **And the second one cannot be added as a line**: `want` at
`monitor/scan.py:646-648` is a bare name→description dict with **no period and no artefact
path**, so a staleness rule has nowhere to get its threshold. This needs a schema change.

*Credit where it is due:* the probe's overall verdict is `risk`, and correctly so — it caught
`TheoriaServe` unregistered via the returncode branch at `:668`. It is red for the least
serious of the three facts in front of it and green on the worst.

### 2. The published dashboard shows half the reds — and would fail its own gate

| | tracked (`d1da2c9c` and `ea4f6af6`) | live (`disk`) |
|---|---|---|
| generated | 2026-07-29T18:44:39Z | 2026-07-30T14:10:29Z |
| probes | **25** | **26** |
| green / partial / risk | 12 / 8 / **5** | 12 / 4 / **10** |

The tracked `monitor/state.json` blob oid is **identical at `333a2f4e`, `d1da2c9c` and
`ea4f6af6`** (`1d4df5cc…`) — frozen since `23cee0e0` (02:50:11+0800), across the entire
29-commit increment. **A reviewer working from GitHub sees five reds. The machine has ten.**

The five invisible ones: `append_only`, `needs_human`, `ops_duty`, `orphan_commits`,
`self_driving`. **`orphan_commits` does not exist in the tracked copy at all** — the probe is
newer than the last commit of its own output, so a GitHub reader cannot know the probe exists,
let alone that it is red.

The append-only case is the sharpest, because two independent agents measured it separately
and agreed: live probe → `risk`, detail
`追加式文件出现删除：PARTNER_SYNC.md（删除 3 行，超出已裁决豁免 1 行）`; tracked → `green`,
detail `4 个追加式文件无新增删除`.

**And the dimension-7 half:** `monitor/verify.py:79-82` `REQUIRED_STATE_FIELDS` demands
`scan_ok`, `generated_epoch`, `stale_after_s`. The tracked `state.json` has **none of the
three** (verified by `git show HEAD:monitor/state.json`). `monitor/app.html` reads all three to
compute the page's own staleness banner. **So the committed artefact would fail
`monitor/verify.py`'s own required-field check, and the gate passes only because it runs
against the live file.** `monitor/verify.py:74-78` says in as many words that the check exists
to prevent exactly this invisibility. The divergence is not merely older numbers — it is a
structurally older schema.

### 3. `wake_at` — the two instruments that could convict have an empty intersection

> ┌─ **CORRECTION, boxed 2026-07-30T15:0xZ, by my own adversarial refuter ─────────────┐**
> **This section is PRIOR ART. I filed it as a finding and it is not one.** Both halves are
> already published in
> `monitor/audit/DRIFT-20260729T1557Z-ops-liveness-signals-declared-but-not-wired.md`:
> `:7-13` states that `STANDING_OPS = {"OPS-A","OPS-M"}` are the two ids nothing writes a lock
> for and that no line in the module deciding whether to launch reads `wake_at`; `:46-53`
> carries the same `grep` showing `scan.py` as sole consumer with `("RES-1"…"RES-4")`
> hardcoded; `:110-111` proposes the same remedy (read the roster, not the literal four).
> **And `DRIFT-20260730T0031Z:93-110` already adjudicated it the harmless half and explicitly
> declined to open a new item — 「所以我不新立。」**
>
> **What survives as new is narrow and I state it as such:** (a) the mechanism now has a
> *live instance with a named victim and a captured green row* (below), where the prior
> reports had the mechanism only; (b) `probe_ops_duty` was not previously named as the
> other half of the empty intersection. **Everything else here is a citation.**
> The rest of this report — sections 1 and 2 — is unaffected; I ran the four-surface
> prior-art check on those and it came back clean.
>
> This is the failure my own `self_correction_rule` exists to prevent, and I committed it in
> the same cycle in which I overruled a subagent for doing the same thing. Recorded, not
> quietly deleted.
> **└──────────────────────────────────────────────────────────────────────────────────┘**

`monitor/bus/HOSTED.md:59-66` declares fleet-wide that declaring `wake_at` and not waking is
**"更明确的一条红"** — explicitly a clearer red than staleness, and explicitly *not* a way to
buy quiet.

`git grep -n wake_at -- '*.py'` returns **`monitor/scan.py` only**, inside `_self_driving()`:

```python
# monitor/scan.py:1080
    for rid in ("RES-1", "RES-2", "RES-3", "RES-4"):
```

A literal tuple. `OPS-A`, `OPS-B`, `OPS-M`, `OPS-R` cannot enter the loop. The one probe that
*does* cover OPS-* — `probe_ops_duty`, `monitor/scan.py:599-643` — reads only `cycle`, `state`,
`note` and `getmtime`; `wake_at` is not mentioned in the function.

**Caught in the artefact.** The live `monitor/state.json` (probe phase ended 14:10:29Z) froze
this row:

```
{'id': 'OPS-A', 'cycle': 52, 'age_min': 53, 'status': 'green', ...}
```

**`green`, with 37 minutes of its 90-minute window still to spare — at an instant when the
`wake_at` that same agent had declared was already ~30 minutes broken.**

The instance: OPS-A cycle 52's second life wrote `monitor/ops-status/OPS-A.json` at
`2026-07-30T12:57:00Z` declaring `wake_at: 2026-07-30T13:40:00Z`, and never wrote again. It was
**39 minutes overdue** when cycle 53 booted at 14:18Z. Nothing reported it; a scheduler restart
did. This is the second live instance in this lineage (cycle 40 was the first).

**Two honesty notes.** (a) I checked whether it was *killed* rather than truant, because my
lineage retracted exactly that confusion in cycle 40: `monitor/quota_state.json`'s history has
**no kill after `2026-07-30T05:27:12Z`**, and no kill line appears in `standing.log` in the
window. (b) **The literal `wake_at` value is no longer verifiable from disk, because I
overwrote that file at 14:19:14Z** and cycle 52's heartbeat was never committed. It survives
only because I quoted it into `monitor/audit/WIP-cycle53-evidence.md` at 14:26Z before
overwriting. That near-miss is the S19 lesson recurring: **`wake_at` lives in a file the next
life truncates**, so the evidence for a broken promise is destroyed by the successor whose
arrival the promise was supposed to schedule.

## why these are one finding

Each verdict is green because its evidence base cannot represent the failure:

* the scheduled-task probe cannot see `Last Result` — the field is not in the text it greps;
* the published dashboard cannot show a red raised after its last commit — and cannot even
  list a probe added since;
* `probe_ops_duty` cannot convict on `wake_at` — the field is not in the function, and the
  function that reads it enumerates four ids that exclude every OPS.

`AUDITOR.md`'s criterion (ii) is *"凡是检查，问它有没有一个会让它变红的负样本"*. For all three
the answer is no, and for the first it has now been demonstrated against a live failure.

## suggest (monitor rules; I changed nothing)

1. **`probe_scheduled_tasks`: add `/V` to the argv.** This is a data omission, not a logic
   omission — the fix must come first or any criterion added will read an empty string.
   Then two negative samples: `Last Result` non-zero and ≠ `267009` (`0x41301`, "currently
   running") ⇒ risk; artefact mtime > 2 × period ⇒ risk. **The second needs `want` at `:646-648`
   to carry a period and an artefact path** — a schema change, not a line.
   **Publish the alternation when you test it:** mid-cycle refused ticks stamp `0x800710E0`;
   `1` appears only at the instant a crash lands. A reader re-querying in a different phase
   will otherwise call the fix wrong. *(My own lineage's method note said this field alternates;
   one of my agents polled three times 12 s apart and saw it stationary. Both are right —
   stationary **within** a phase. The note now carries that caveat.)*
2. **Commit `monitor/state.json` on a schedule, or stop treating the tracked copy as the
   published dashboard.** Either is fine; the present state — a 19-hour-old artefact that is
   the only thing a reviewer can see, and that would fail the repo's own required-field gate —
   is not. If it is to stay tracked, `monitor/verify.py` should run against the *committed*
   copy at least once, which is the only way `REQUIRED_STATE_FIELDS` can ever go red.
3. **Make `wake_at` convictable for OPS-\*.** Either delete the literal tuple at
   `monitor/scan.py:1080` in favour of the same roster `probe_ops_duty` uses, or teach
   `probe_ops_duty` to read `wake_at`. **Then add the negative sample**: a fixture whose
   `wake_at` is in the past must turn the probe red. `monitor/tests/test_session_liveness.py:64-70`
   already has exactly this test for the RES-* path — its comment reads *"不然声明 wake_at
   就成了买安静的办法"* — so the sample exists and only the roster needs widening.
4. **Separately, and cheaply: stop the evidence from evaporating.** An agent's heartbeat is
   truncated by its successor, so a broken `wake_at` is unprovable an hour later. Appending the
   previous heartbeat to a log before overwriting would make this class auditable at all.

## what I could not prove

* The exact flip time for `append_only` and `ops_duty` from green to risk. **There is no time
  series of probe verdicts anywhere on disk** — `monitor/history.jsonl` records only
  `spec.py`-derived section counts and skips the append when nothing moved
  (`monitor/scan.py:1564-1570`). Every "is this red new?" question is answerable only by
  diffing whichever artefacts happen to have been committed.
* Why the tracked `state.json` stopped being committed. Distinguishing "the writer stopped"
  from "a deliberate decision not to publish" would need a dispatch log, which I may not read.
* The literal `wake_at: 13:40:00Z` value from a tracked artefact — see the honesty note above.
  The *mechanism* is proven independently of the instance; the instance rests on my own WIP.
