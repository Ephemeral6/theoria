# ADV-2 · adversarial review of the fleet loop half of S28

Scope: `standing.py`, `reflex.py`, `dispatch.py`, `_runner.py` and their two test
files, as changed by `1585dd04` / `fad88ca3`. Read first:
`EVIDENCE-3-standing-reflex.md`, `EVIDENCE-4-dispatch.md`, `RUN_STATE.md`.

Method: a claim counts as a defect only with an exact command and its real
output. Everything else is filed as REFUTED or marked UNCONFIRMED. Zero API
spend: no scheduled task was created, run or deleted, no session was started,
nothing under the main checkout's `dispatch-logs/` was written. Every repro runs
in `%TEMP%\s28adv\` against monkeypatched module globals, plus three read-only
queries (`schtasks /Query`, `git branch -r`, the live `registry.json`).

**13 confirmed defects.** Three of them (D1, D2, D3) are new instances of the
exact disease this item exists to remove, introduced by the fix for it; five
(D4, D5, D7, D9, D10) are siblings the sweep missed in the four files it
claims to have swept; two (D11, D12) are decorative tests.

---

## CONFIRMED DEFECTS

### D1 — `exits.json` now loses records silently instead of corrupting loudly (money-free, evidence-destroying)

`record_exit` is read-modify-write with no lock. Per-writer temp names buy
**atomicity**, not **serializability**: two sessions that read the ledger before
either writes produce a valid file in which the first writer's record does not
exist. There is no trace — `problem` stays `None`, so `_note_failure` is never
called, and `dispatch.read_exits` reports `ok=True problem=None`.

Repro (`%TEMP%\s28adv\writer.py`, wraps `load_exits` with a file barrier so both
processes have read before either replaces — no other behaviour changed):

```python
real = _runner.load_exits
def wrapped(raw):
    out = real(raw)
    open(os.path.join(d, name + ".read"), "w").close()
    while len([f for f in os.listdir(d) if f.endswith(".read")]) < 2:
        time.sleep(0.02)          # both writers have now read the ledger
    return out
_runner.load_exits = wrapped
_runner.record_exit(name, {"code": 0, "seconds": 111, "log": name + ".log"})
```

```
$ python writer.py W-AAA lab & python writer.py W-BBB lab & wait
W-BBB pid=16392 done
W-AAA pid=43380 done
=== final exits.json ===
{ "HISTORY": [...], "W-AAA": [ { "code": 0, "seconds": 111, ... } ] }
=== failure log ===
(none: both writes reported success)
```

`W-BBB`'s exit record is gone permanently. Both processes exited 0 and both
believe they recorded. This is the same outcome as the bug the commit fixed —
"62 exits silently discarded" — with a narrower window and **worse
detectability**: the old failure left a diagnosable artifact on disk, this one
leaves a healthy-looking file. Concurrent exits are not hypothetical here; they
are what produced the original corruption, and `dispatch.py:367` records
"simultaneous storms killed half a fleet once".

Fix direction: an exclusive lock (`msvcrt.locking` / a lock file with retry)
around read+write, or append-only JSONL per session (no read-modify-write at
all). Per-writer temp names cannot solve a lost update.

### D2 — the quarantine path files a *good* ledger as `.corrupt-*`, and can destroy the corrupt original it exists to preserve

Two writers that both see the damaged file each quarantine it in turn. The
second one's `os.replace(EXITS, quarantine)` moves whatever is at `exits.json`
at that moment — which is the *first writer's freshly written valid ledger*.
When both land in the same wall-clock second (the stamp is `%Y%m%dT%H%M%SZ`, a
one-second window; `standing.py:67` records four workers dying within four
seconds) the second replace overwrites the first quarantine, and the corrupt
original — "一整天的死因史比当下这一条记录值钱" — is gone.

Repro (`writer2.py`, same barrier, seed = an unsalvageable ledger):

```
############ natural stamps
--- files: exits.json  exits.json.corrupt-20260729T215750Z  exits.json.corrupt-20260729T215751Z
--- exits.json:                       { "W-BBB": [...] }        # W-AAA's record lost
--- ...corrupt-20260729T215750Z:      THE CORRUPT ORIGINAL - a day of causes of death
--- ...corrupt-20260729T215751Z:      { "W-AAA": [...] }        # a VALID ledger filed as corrupt
--- failure log:
2026-07-29T21:57:50Z W-AAA JSONDecodeError: ...; quarantined as exits.json.corrupt-...750Z
2026-07-29T21:57:51Z W-BBB JSONDecodeError: ...; quarantined as exits.json.corrupt-...751Z

############ same-second stamps (FREEZE=1)
--- files: exits.json  exits.json.corrupt-20260730T000000Z
--- exits.json:                       { "W-BBB": [...] }
--- ...corrupt-20260730T000000Z:      { "W-AAA": [...] }        # the corrupt original is GONE
--- failure log: two lines, both claiming the same filename holds their JSONDecodeError
```

Both failure-log lines are false statements about the file they moved: the
second one's `JSONDecodeError` came from a read of a file it did not quarantine.
Fix direction: quarantine name from the content hash or a `%f`/pid suffix, and
`os.link`+`unlink` or an existence check so a quarantine never overwrites.

### D3 — prefix salvage can destroy the whole ledger and leave it reading `ok=True problem=None`

`load_exits` keeps the `raw_decode` prefix and discards the tail. When the
prefix is the *short* writer's object and the tail is the history, salvage keeps
the small one, writes it back over `exits.json`, and does **not** quarantine
(deliberately — "可救时也隔离本身就是数据丢失"). The result is a healthy-looking
ledger missing almost everything, and the only trace counts *bytes*, not
records, in a log that has no reader anywhere in the repo (see D10).

```
$ python  # lab4: 48 sessions of history overlaid at offset 0 by a shorter writer
before: 1899 bytes, 49 sessions recoverable by eye
after : 147 bytes, sessions kept = ['W-new', 'W-now']
quarantine copy? NONE
trace : 2026-07-29T22:04:12Z W-now recovered valid prefix, discarded 1861 trailing bytes (...)
reader verdict on the new file:
    {'ok': True, 'problem': None}
```

One salvage converts "corrupt, and you can see it" into "clean, and 98% of the
history is unrecoverable". This answers the hypothesis directly: **yes**, a
truncated/hostile file makes the salvager write a file that then looks valid and
is missing records. Fix direction: quarantine a copy *whenever* anything is
discarded (copy, not move), and report records kept/dropped, not bytes.

### D4 — reflex's worker headcount still reads "could not measure" as "zero live workers", and that spends money

`reflex.py:231-238` is the fourth sibling of the pattern the commit fixed three
times, ~70 lines above one of the fixes:

```python
st = run_console(["schtasks", "/Query", "/TN", "TheoriaAgent-%s" % wid, "/FO", "LIST"])
if st.returncode == 0 and ("Running" in st.stdout or "正在运行" in st.stdout):
    live_workers += 1
```

A failed query (schtasks missing, RPC error, an access-denied folder) leaves
`live_workers` at 0, so `range(target - live_workers)` spawns up to
`WORKER_MAX = 7` paid sessions on top of the ones already running, and **no
event names the failed measurement**. The comment immediately below narrates the
previous incarnation of this same bug (the GBK mismatch that made
`live_workers` ≡ 0 and "补员循环每一跳都按满员上限拉人") — the encoding half was
fixed, the return-code half was not.

Repro: `reflex.main()` with `run`/`run_console`/`Popen` faked, a registry of
seven live unreaped `W-*`, and the real board (depth 2):

```
query OK      -> spawns=0 []
               log: SUPPLY-LOW:2
query FAILS   -> spawns=2 ['W-62419', 'W-62420']
               log: worker-spawn:W-62419 | worker-spawn:W-62420 | SUPPLY-LOW:2

does any event name the failed headcount query? []
```

Two extra paid workers with seven already alive, and the tick reads as healthy
refilling. With a deeper board the delta is up to 7.

### D5 — the `git branch -r` guard checks the wrong condition; the money direction is still open

The fix guards `returncode != 0`. The failure mode RUN_STATE describes is
`remote` being **empty**, and the command exits 0 with empty output whenever no
remote-tracking ref matches — no remote configured, refs never fetched or
pruned, a differently-named remote, a renamed branch prefix:

```
$ cd /tmp/gitlab && git init -q . && git commit -q --allow-empty -m x
--- case 1: no remote at all
rc=0 stdout_empty=yes
--- case 2: remote exists but refs pruned
rc=0 out=[]
```

`rc=0, remote=""` is exactly the input that makes every `"agent/%s" % slug in
remote` False, i.e. every dead session read as "never delivered" and relaunched.
The new guard does not see it, and it is indistinguishable from the legitimate
"nobody has delivered yet". Latent today only by accident — the live checkout
returns 19 refs (`git branch -r --list 'origin/agent/*' | wc -l` → 19).

Fix direction: `if _remote.returncode != 0 or not _remote.stdout.strip(): skip`.
An empty ref list is never a safe input to this loop, because the whole loop is
"who is missing from this list".

### D6 — every new alarm is buffered in one list and can be discarded wholesale; the tick then leaves no line at all

`events` is built from line 84 and flushed only at `reflex.py:381`; the `finally`
removes the lock and nothing else. Any exception after an alarm is appended
throws away the entire tick's record — including all four `*:EXIT-*` alarms this
commit added. Two reachable triggers, both repro'd:

```
### A) a crash in step 4 discards every alarm collected in steps 0c-2
mode=timeout -> main() RAISED TimeoutExpired: Command '[...ci_merge.py]' timed out after 3600 seconds
   reflex.log: (reflex.log NEVER WRITTEN)
### B) same tick, no crash -- the alarms that WOULD have been logged
mode=ok -> main() returned 0
   reflex.log: sweep:EXIT-1 | reap:EXIT-2 | worker-fail:... | SUPPLY-LOW:2
```

```
### registry.json truncated mid-write (dispatch.save_registry is not atomic)
main() RAISED JSONDecodeError: Unterminated string starting at: line 1 column 20 (char 19)
   reflex.log: (NEVER WRITTEN -- the tick left no trace)
```

The second trigger is manufactured by code in scope: `dispatch.save_registry`
(`dispatch.py:94-96`) writes `registry.json` with no temp file and no
`os.replace`, so any death mid-write leaves a truncated registry, and
`reflex.py:225` / `:271` load it unguarded. A tick that leaves no line is
strictly quieter than a tick that reports a failure as good news.

Supporting, UNCONFIRMED as to cause: the live `monitor/reflex.log` has **17 gaps
longer than 15 minutes** for a 5-minute loop (270 lines, 2026-07-28T03:16Z →
2026-07-29T21:38Z; the longest 260 min), and the last line at the time of this
review was 20 minutes old. Ticks are leaving no line; I cannot attribute which
of the paths above (or a machine sleep, or the lock branch at line 78-80, which
also returns 0 without logging) produced them.

### D7 — `standing.py` and `reflex.py` still share one temp file name per state file — the exact cause fixed in `_runner.py`

`standing.py:117` (`STATE + ".tmp"`, holds `last_launch_epoch`, i.e. the
`MIN_RELAUNCH_MIN` cooldown) and `reflex.py:71` (`LOOP + ".tmp"`, holds
`death_counts`, i.e. three-strikes). Same shape in `accounts.py:96`,
`scan.py:2846`. Two overlapping writers — and `standing.py`'s own docstring
tells a human to run `python monitor/standing.py` by hand while the 15-minute
task is registered:

```
$ python stwriter.py A st & python stwriter.py B st & wait
A: save_state returned normally
B: save_state RAISED FileNotFoundError: [WinError 2] ...: 'st\standing_state.json.tmp' -> 'st\standing_state.json'
--- standing_state.json: { "A": {...} }        # B's launch stamps lost
load_state() sees: {'A': {...}}
```

`save_state` has no `try`, and `sweep` calls it at line 400 and 417, so the
second writer dies mid-roster: the agents after it are never considered and the
`nothing to start` line is never written. The lost write is `last_launch_epoch`,
whose absence disables the relaunch cooldown — and `load_state`'s
`except Exception: pass → {}` (line 107-113) makes any corruption read as "no
state at all", which is the same swallow that `_runner.record_exit` was just
cured of. `sweep`'s own comment (lines 408-415) documents what losing this file
costs: the mechanism turned itself off for three hours while logging reassuring
lines.

### D8 — the new third value does not survive the process boundary: `dispatch.py --worker` and `standing.py` both exit 0 on failure

`via_task` now returns four values; `dispatch.main()` (`dispatch.py:329-331`)
discards it:

```
### E1: dispatch.py --worker exit code when the launch was DECLINED
main() returned 0
process exit code = 0
### E2: same, DIED-ON-ARRIVAL
process exit code = 0
### E3: standing.py exit code when nothing could be started
process exit code = 0
```

This is the same bug the commit narrates fixing in `_runner.py` ("第一版写的是
`return 127`，而 `__main__` 只调 `main()`"), left standing one file over. Only
the printed word carries the status, so any caller that checks the exit code —
including a human, and Task Scheduler's Last Result for `TheoriaStanding` —
reads a declined launch as a clean run. `_runner.py`'s guard, by contrast, is
correct: verified as a real process (see REFUTED R4).

### D9 — `via_task` still registers a pid it never measured, and the live registry proves it: 70 of 74 entries are `pid 0`, two of them "exited" while the scheduler says Running

`dispatch.py:410-421`: `real_pid = 0`, the `schtasks /Query` returncode is never
checked, no line matching means `real_pid` stays 0, and the `except: pass` hides
the rest. Nothing distinguishes "the scheduler told us pid 0" from "we did not
find out". The commit rewrote the tail of this function and left the head.

Live, read-only, right now:

```
$ python -c "...registry.json..."
entries 74 ; pid0 entries: 70
OPS-M {'pid': 0, 'task': 'TheoriaAgent-OPS-M', 'reaped': 'exited', 'via': 'task'}
OPS-A {'pid': 0, 'task': 'TheoriaAgent-OPS-A', 'reaped': 'exited', 'via': 'task'}

$ schtasks /Query /FO CSV /NH   (read-only)
"\TheoriaAgent-OPS-A", ..., "Running"
"\TheoriaAgent-OPS-M", ..., "Running"
```

Two sessions the scheduler reports as **Running** are recorded in the fleet's
registry as `reaped: "exited"` — `reap()` printed "exited on its own" for both,
because `pid_alive(0)` is now correctly False and the pid was never measured.
That is the item's own subject, live, in a file in scope. The money path is
blocked only by an accident: reflex's revive loop does reach these entries
(`OPS-*` does not match its `("M-","A-","B-","R-")` skip list), but
`dispatch.py --only OPS-M` finds no prompt because `os.listdir(PROMPTS)` is not
recursive and `OPS-M.md` lives in `prompts/ops/`, so the relaunch is a silent
no-op that also fails to increment `death_counts`.

### D10 — the ledger reader has no caller, and the dashboard still cannot see the third value

`grep -rn "read_exits\|exit_summary\|exits-write-failures" --include=*.py monitor/`
outside `dispatch.py`, `_runner.py` and `tests/` → **no consumer anywhere**. The
finding as written ("36 non-zero exits recorded and nothing in the repo reads
it") is therefore still true in production: a reader was written, a patch for
`probe_standing` was proposed in EVIDENCE-4 and correctly not applied (someone
else's file), and the delivered state has no caller.

Consequences, both verifiable by reading `scan.py:1221-1231`: `probe_standing`
still counts every `" START "` line and stays green, and it does not parse
`ok=`, so `ok=died-on-arrival(Ready)` and `ok=running` are the same thing on the
page — the new START lines simply push the "累计起过 N 次" number up faster.
`claimable = -1` likewise has no consumer outside `standing.py` (`grep -rn
claimable` → none), so its third value exists only as text in `standing.log`,
which no probe parses. The write-failure log added in D1's fix is in the same
position: a trace nobody reads.

### D11 — `test_the_new_lines_survive_a_cp936_console` is vacuous

```python
for line in src.splitlines():
    if "died-on-arrival" in line or "not on PATH" in line:
        line.encode("cp936")
```

Zero assertions if nothing matches. It PASSES against the pre-fix `dispatch.py`
and `_runner.py`, where no such line exists (row 34 of the audit below). Rename
the status string and the test stays green. Needs a `assert matched` counter.

### D12 — the headline fix of `1585dd04` has no behavioural test; its two tests are tautologies

`test_a_crashed_merger_no_longer_reads_as_a_clean_no_op` and
`test_a_successful_merge_is_unchanged` exercise `_merge_events`, a
re-implementation of `reflex.py:322-336` **inside the test file**. They import
`reflex` and never call it. Both PASS against pre-fix `reflex.py` verbatim (rows
7 and 8). The only coverage of the shipped code is a source grep for the string
`"merge:EXIT-"`. EVIDENCE-3 states "每条修复都配了阴性对照"; for finding 10 the
control is a copy of the code under test.

### D13 — the fix removed the standing cap and the 45-second stagger for any status that is not exactly `running`

`n_standing += 1` and `time.sleep(45)` now live inside `if ok == "running":`
(`standing.py:403-406`). `schtasks /Run` has already accepted the launch by
then, so a misread state — `state-unknown` (LIST output not recognised),
`died-on-arrival(gone)` from a transient `/Query` failure, or a task that has not
flipped to Running within `LAUNCH_SETTLE_S = 8` — takes both safeties off:

```
$ python sweep_probe.py     # sweep() with everything else monkeypatched
MAX_STANDING = 5, roster = ['RES-1','RES-2','RES-3','RES-4','OPS-M','OPS-A']
via_task -> running                launches=5  45s staggers=5  counted-as-started=5  cap-refusals=1
via_task -> state-unknown          launches=6  45s staggers=0  counted-as-started=0  cap-refusals=0
via_task -> died-on-arrival(Ready) launches=6  45s staggers=0  counted-as-started=0  cap-refusals=0
```

Six launches with no stagger is the configuration `standing.py:65-68` blames for
the 05:39 session limit ("六个全开正是今天 05:39 撞上 session limit 的规模，四个
工人在四秒内一起死"), and `dispatch.py:367` calls the stagger law. The old
boolean was the scheduler's receipt — which is exactly the right predicate for
"did I hand a launch over, so slow down and count it". The status read is the
right predicate for "is a researcher up". The fix replaced one with the other
instead of keeping both. Fix direction: count and stagger on `ok` (the
scheduler accepted), report health on `status`.

---

## REFUTED HYPOTHESES

**R1 — "the write is not atomic on Windows / the interleaving corruption can
still happen."** Refuted. `os.replace` is atomic here and the per-pid temp name
does remove the byte-overlay: across every two-writer run above the ledger was
always parseable JSON, never "one object plus another's tail". What replaced the
corruption is a silent lost update (D1) — a different defect, not this one.

**R2 — "a failed write leaves no trace."** Refuted. Verified with a real handle
held open on the destination:

```
ledger after the write: {"HISTORY": [{"code": 0}]}
record lost? True
failure log: 2026-07-29T21:58:22Z W-HELD PermissionError: [WinError 5] 拒绝访问。:
    '...exits.json.30676.tmp' -> '...exits.json'
leftovers: ['exits.json', 'exits.json.30676.tmp', 'fail.log']
```

Two side notes, both minor and neither a defect on its own: on Windows *any*
other open handle on `exits.json` (including `read_exits`' own
`open(p).read()`, whose handle lives for microseconds) makes `os.replace` fail
with WinError 5 and costs that one record — which the design explicitly accepts;
and the temp file is left behind on failure with nothing in the repo ever
cleaning `dispatch-logs/*.tmp`.

**R3 — "skipping the revive loop trades a loud money bug for a quiet stall."**
Refuted as posed. The skip is not silent: `revive:GIT-EXIT-%d(loop-skipped)`
reaches `reflex.log` (observed in the harness runs). It is a trace with no
machine consumer, and it can be discarded with the whole tick (D6), but "nothing
says so" is false. The real hole in that guard is D5, which is the opposite
finding: the money direction is still open.

**R4 — "`__main__` still swallows the 127."** Refuted for `_runner.py`, as a
real process:

```
$ PATH=<no claude> python rl/_runner.py Z0-adv rl/p.md rl/s.log opus
claude CLI not on PATH (shutil.which returned None)
process exit code = 127
--- session log: === runner abort Z0-adv: claude CLI not on PATH ... ===
```

`reflex.py`, `dispatch.py`, `standing.py` all use `raise SystemExit(main())`, so
the wrapper is right in all four; the loss is inside `main()` (D8).

**R5 — "the exempted memory read is the same bug."** Refuted by inspection, and
the exemption is correctly reasoned: `free_gb = 0.0` is fail-closed (fewer
workers), a failed powershell yields `int("")` → ValueError → `mem-unreadable`.
Their `test_the_memory_read_is_exempt_and_this_is_why` pins both halves.

**R6 — "salvage destroys good records in the single-writer case."** Refuted.
With one writer, unsalvageable input is quarantined byte-for-byte and a fresh
ledger is started; salvageable input keeps the prefix, appends, and reports. The
destruction cases are concurrency (D2) and prefix-vs-tail ordering (D3).

**R7 — "the new tests are decorative."** Refuted in aggregate: 26 of 34 go red
against the pre-fix sources. Two are tautologies and one is vacuous (D11, D12);
the rest discriminate. Note that 15 of the 26 go red as `AttributeError` on
monkeypatching a symbol the old code lacks — legitimate for a genuinely new API
(`read_exits` did not exist), but it means those rows test "the new API exists",
not "the old behaviour was wrong".

**R8 — "the three siblings in `reflex.py` are not actually wired up."**
Refuted: a faked tick with a crashing `board.py sweep` and a crashing `--reap`
logged `sweep:EXIT-1 | reap:EXIT-2`, and the clean tick logged neither.

**R9 — "`claimable = -1` leaks into a consumer that treats it as a count."**
Refuted: `-1` is only produced and consumed in `standing.py`, `any` is guarded
with `claimable > 0`, and the unknown branch precedes the `not any` branch. The
separate problem is that it reaches no consumer at all (D10).

**R10 — "`standing.running_tasks()` is silently returning a partial set on this
box."** Not confirmed. Its return code *is* unchecked (a failed query yields an
empty `live` set, which reads as "no standing session is running" and is the
money direction, twin of D4), but measured on this machine
`schtasks /Query /FO CSV /NH` → `returncode = 0`, 324 lines, 50 Theoria rows. A
latent hole, not a live one; filed here rather than as a defect because I have no
repro of the failure occurring.

---

## NEGATIVE-CONTROL AUDIT

Both new test files run against the four pre-fix sources
(`git show 1585dd04^:monitor/<f>.py`) in a scratch copy of `monitor/`. Control
run against the post-fix copy: **34 passed**. Against pre-fix: **22 failed, 4
errored, 8 passed**.

```
$ for f in standing reflex dispatch _runner; do git show 1585dd04^:monitor/$f.py > old/$f.py; done
$ cd old && python -m pytest tests/test_standing_reflex_no_third_value.py \
                            tests/test_dispatch_no_third_value.py -q
22 failed, 8 passed, 4 errors in 0.58s
$ cd ../new && python -m pytest <same two files> -q
34 passed in 0.40s
```

| # | test | on pre-fix code | discriminates? | note |
|---|---|---|---|---|
| 1 | crashed_board_query_is_not_reported_as_an_empty_board | FAILED (AttributeError `CLAIMABLE_UNKNOWN`) | yes | behavioural + new constant |
| 2 | the_discarded_exception_is_now_on_the_record | FAILED (AssertionError) | yes | behavioural |
| 3 | a_genuinely_empty_board_still_reads_as_zero | PASSED | n/a | intended negative control — must pass on both |
| 4 | a_board_with_work_still_reads_as_work | PASSED | n/a | intended negative control |
| 5 | the_unknown_sentinel_has_its_own_skip_reason | FAILED (ValueError, string absent) | yes | source grep |
| 6 | the_skip_reason_survives_a_cp936_console | FAILED (IndexError) | yes | source grep |
| 7 | a_crashed_merger_no_longer_reads_as_a_clean_no_op | **PASSED** | **no** | **D12: tests `_merge_events`, a copy of the code, not `reflex`** |
| 8 | a_successful_merge_is_unchanged | **PASSED** | **no** | **D12: same tautology** |
| 9 | the_real_ci_merge_has_no_deliberate_nonzero_exit | PASSED | n/a | invariant about `ci_merge.py`, predates the fix — correct as written |
| 10 | reflex_reads_the_return_code_of_every_child_it_scrapes | FAILED (AssertionError) | yes | source grep; the ONLY coverage of the ci_merge fix |
| 11 | the_memory_read_is_exempt_and_this_is_why | PASSED | n/a | documents a pre-existing exemption — correct as written |
| 12 | a_failed_git_query_skips_revival_instead_of_reviving_everyone | FAILED (ValueError) | yes | source grep; guards `returncode` only — see D5 |
| 13 | supply_unknown_is_distinct_from_supply_low_zero | FAILED (AssertionError) | yes | source grep |
| 14 | reflex_and_standing_still_import_and_compile | PASSED | n/a | smoke test, intended to pass on both |
| 15 | a_valid_ledger_reads_clean | FAILED (no `read_exits`) | yes | new API |
| 16 | a_corrupt_ledger_is_not_reported_as_an_empty_one | FAILED (no `read_exits`) | yes | new API + behaviour |
| 17 | a_missing_ledger_is_distinguishable_from_an_empty_one | FAILED (no `read_exits`) | yes | new API + the patch's own self-caught bug |
| 18 | exit_summary_counts_what_the_start_line_cannot_see | FAILED (no `exit_summary`) | yes | new API |
| 19 | a_healthy_ledger_reports_zero_deaths_not_a_false_alarm | FAILED (no `exit_summary`) | yes | new API |
| 20 | each_writer_gets_its_own_temp_file | FAILED (AssertionError: `exits.json.tmp`) | yes | behavioural, the real cause — but see D1: per-process, not per-writer |
| 21 | recoverable_corruption_is_salvaged_in_place | FAILED (no `EXITS_FAIL`) | yes | behavioural; see D3 for what it does not cover |
| 22 | unrecoverable_corruption_is_quarantined_not_overwritten | FAILED (no `EXITS_FAIL`) | yes | behavioural; single-writer only, see D2 |
| 23 | a_failed_ledger_write_stops_being_silent | FAILED (no `EXITS_FAIL`) | yes | behavioural |
| 24 | a_successful_write_leaves_no_complaint | FAILED (no `EXITS_FAIL`) | weak | negative control that cannot run on the old code |
| 25 | record_exit_still_never_takes_the_session_down | FAILED (no `EXITS_FAIL`) | weak | preserved-guarantee control; red for an irrelevant reason |
| 26 | a_missing_claude_cli_exits_127_and_is_named | FAILED (AssertionError) | yes | behavioural, verified independently as a real process |
| 27 | the_guard_uses_sys_exit_not_return | FAILED (ValueError) | yes | source grep |
| 28-31 | via_task status quartet (dies_on_arrival / running / chinese / unrecognised) | ERROR (no `LAUNCH_SETTLE_S`) | yes | behavioural; none of them covers D13 (cap + stagger) |
| 32 | a_scheduler_that_refuses_is_still_distinct | FAILED (no `LAUNCH_SETTLE_S`) | weak | old code already returned False here; red for a fixture reason |
| 33 | standing_compares_the_status_explicitly | FAILED (AssertionError) | yes | source grep; pins `if ok == "running":` |
| 34 | the_new_lines_survive_a_cp936_console | **PASSED** | **no** | **D11: vacuous, zero assertions when nothing matches** |

Two further gaps in the audit itself:

* **`tests/mutants.py` was not extended.** The repo already owns the tool that
  answers "would this suite have caught the bug" by putting each defect back
  into a scratch copy, and its docstring says exactly that. It still holds the
  same 8 pre-S28 mutants; none of the 11 S28 findings — and none of the 5
  siblings — was added. The four highest-value mutants to add:
  `tmp = EXITS + ".tmp"`, `claimable = 0`, `if ok:` in `standing.sweep`, and
  dropping the `else:` under the git guard.
* **No test covers the interaction between the new status and the two safeties
  it now gates** (D13), which is the only place this commit changed what the
  fleet *does* rather than what it *says*.

## Verification of the branch's own claims

| claim (RUN_STATE / EVIDENCE) | verdict |
|---|---|
| `-1` has no other consumer (`grep claimable`) | true, re-verified |
| `ci_merge.py` has no `sys.exit`, so the exit alarm cannot cry wolf | true, re-verified |
| `via_task`'s status separates declined / died / running | true inside the function; lost at the process boundary (D8) and at the dashboard (D10) |
| the ledger is now read | half true: readers exist, no caller exists (D10) |
| "每写者一个临时名，race 从根上消失" | overstated: the byte-overlay race is gone (R1), the lost-update race is not (D1) |
| "救不回来就隔离，别覆盖" | holds single-writer, inverts under concurrency (D2) and under prefix-vs-tail ordering (D3) |
| "每条修复都配了阴性对照" | 31/34 sound; 2 tautologies + 1 vacuous (D11, D12) |
| 全量套件绿 | true: `cd monitor && python -m pytest -q` → exit 0, ~350 passed, 2 xfailed, no F/E. None of the defects above comes from a broken tree. |

Repro scripts (outside the repo, nothing tracked was written):
`%TEMP%\s28adv\{writer.py, writer2.py, reflex_probe.py, reflex_probe2.py,
reflex_probe3.py, stwriter.py, sweep_probe.py}`, plus scratch copies
`%TEMP%\s28adv\{old,new}\` of `monitor/*.py` for the negative-control audit.
