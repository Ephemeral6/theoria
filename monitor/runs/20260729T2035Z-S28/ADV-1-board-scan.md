# ADV-1 · 对抗性复核：`board.py` 与 `scan.py`

Adversarial review of `1585dd04^..fad88ca3` restricted to `monitor/board.py`,
`monitor/scan.py`, `monitor/tests/test_board_no_third_value.py` and
`monitor/tests/test_scan_no_third_value.py`. Read-only: no source file, board
file or tracked artefact was modified. Every reproduction below is an actual
command with its actual output.

Method note for the negative-control audit: a throwaway detached worktree was
created at `1585dd04^` (`5a997ef8`), the two new test files copied in, both
suites run, and the worktree removed (`git worktree remove --force`). Nothing
was committed anywhere.

**Verdict in one line: the six fixes in scope all hold in the direction they
claim, but eight defects of the *same family* survive inside the functions the
commit touched, and one of the six fixes has no behavioural negative control.**

---

## CONFIRMED DEFECTS

### D1 · `meta()` was fixed for six keys and left broken for `deps` and `released_by`

`board.py:128` now uses `[^\S\n]*` for the six single-token keys. Two lines
below, `board.py:139` and `board.py:143` still use the cross-line `\s*`:

```python
m = re.search(r"^%s:\s*(.+)$" % RELEASED_BY, head, re.M)
m = re.search(r"^deps:\s*(.+)$", head, re.M)
```

An **empty `deps:`** therefore still borrows the next line — and the borrowed
value becomes a dependency that can never be satisfied, so the item is
unclaimable forever and the board explains it with a sentence that is not true.

```
$ cd monitor && python -           # item file: "…\nterritory: t1\ndeps:\nlane: infra\n\n# X-1\n"
A) empty `deps:` (next line is `lane: infra`)
   deps   = ['lane: infra']
   lane   = 'infra'
B) empty `released_by:`
   released_by = 'lane: infra' -> workers {'lane:', 'infra'}
C) cmd_list() on a board holding only that one item:
=== available (通用工人可领 0) ===
=== blocked ===
  X-1                          waits on lane: infra
   candidates() = 0
```

Note the interaction with the new fifth partition: `withheld_items()` skips
dep-blocked items on purpose ("`blocked` 那段已经报过了"), so the new partition
is silent about it too. The only report a human gets is `waits on lane: infra`,
a dependency that does not exist.

The shipped test (`test_an_empty_metadata_field_does_not_borrow_the_next_line`)
covers `lane` only. Fix: use `[^\S\n]*` — or better `[ \t]*` (see D4) — in all
four regexes.

Direction: work is withheld and the stated cause is fabricated. `_supply()`
does go red (0 candidates), so it is not silently green — but "no third value"
is exactly what this is: an unfilled field and a filled one encode to the same
thing.

### D2 · `build()` still scrapes the layout it just denounced, and still ignores the child's exit code

`scan.py:2692-2710`. The commit replaced `available` with `len(candidates())`
and left, in the same dict literal, `"blocked": bl.count("waits on")` and
`"listing": bl.strip()` — both derived from `bl`, which is
`_sp.run([...board.py, "list"]).stdout` with **no `returncode` check**, four
lines away from the fix. `git_or_none()` exists in this very file for exactly
this reason and is not used here.

Real end-to-end reproduction (temp copy of `monitor/`, one malformed item file,
the expression from `build()` verbatim):

```
returncode          : 1
stderr last line    : ValueError: invalid literal for int() with base 10: 'high'
bl                  : ''
state["board"]["blocked"] = 0
state["board"]["listing"] = ''
```

A board that cannot be listed reads as **zero blocked items**. Partial
mitigation, found and confirmed: `monitor/verify.py:208` fails the gate when
`board.listing` is empty, so a *total* crash is caught by the gate (not by the
page). Nothing catches a child that dies **after** printing — the documented
`UnicodeEncodeError`-while-printing failure of this repo's own history:

```
rc = 1
bl = '=== blocked ===\n  A-1   waits on B-2\n  C-3   waits on D-4\n'
blocked count from a child that died mid-print: 2 (true answer unknown: the child stopped)
```

Direction: reassuring. `blocked` under-counts, `listing` truncates, and
`_supply()` stays green because it no longer reads the child at all.

### D3 · `_bus_probe()`: one agent that never read its inbox suppresses **every** owed receipt

`scan.py:1046-1051`. The `if never:` early return predates this commit and was
not touched, but it defeats the fix that finding 9 is about: the whole point was
"an unacknowledged `urgent` must not be silent".

```
$ cd monitor && python -   # RES-4: unacked urgent; RES-3: has in.jsonl, no cursor.json
status: partial
detail: 总线已上线；**1 个会话还没读过**（RES-3）——它们下个循环读到指令后即被托管。
RES-4 mentioned at all?  False
```

The new test `test_an_unacknowledged_urgent_is_owed` cannot see this: its
fixture builds a bus containing exactly one agent, so `never` is always empty.
The live bus happens not to be in this state right now (all eight agents have a
`cursor.json`), so the masking is latent, not active.

Direction: reassuring, and it silences precisely the signal the commit added.

### D4 · The `meta()` regex still swallows five characters that are line breaks everywhere else

`[^\S\n]` excludes `\n` only. Python's `str.splitlines()` — and most editors —
treat eight more characters as line terminators, and `\S` excludes all of them,
so `[^\S\n]` happily eats them and the empty field borrows the next line again:

```
VT U+000B    empty lane parses as '#'    (str.splitlines sees 6 lines)
FF U+000C    empty lane parses as '#'    (str.splitlines sees 6 lines)
NEL U+0085   empty lane parses as '#'    (str.splitlines sees 6 lines)
LS U+2028    empty lane parses as '#'    (str.splitlines sees 6 lines)
PS U+2029    empty lane parses as '#'    (str.splitlines sees 6 lines)
```

(`U+001C`–`U+001E` behave the same at the regex level.) Severity is low — a
board item would have to contain one of these bytes, which paste-from-web can
produce for `U+2028`/`U+0085` — but the airtight form costs one character:
`[ \t]*`.

### D5 · `_ack_required()`'s silent fallback is indistinguishable from a successful import, including to its own test

`scan.py:990-999`:

```python
    except Exception:
        return ("order", "urgent", "question")
```

Nothing is logged, nothing is reported, and the literal is byte-identical to
`bus.ACK_REQUIRED` today — so `test_the_ack_vocabulary_comes_from_the_bus`
passes whether the import worked or silently failed:

```
(b) _ack_required() with the import broken -> ('order', 'urgent', 'question')
    == bus.ACK_REQUIRED ? True
    test_the_ack_vocabulary_comes_from_the_bus would still PASS: True
```

This is the item's own disease one level up: "I read the protocol" and "I
guessed the protocol" encode to the same value, with no third one. It becomes a
real under-report the day `bus.ACK_REQUIRED` grows a fourth kind *and* the
import breaks. `_ACK_REQUIRED` is also frozen at scan-import time
(`scan.py:999`), so a later change to `bus.py` inside a live process is not seen.

### D6 · `state["board"]["available"]` has no consumer, so the twin fix's stated motivation is false

The code comment (`scan.py:2703`) and `EVIDENCE-2-scan.md` both say the
frontend renders this number ("前端拿这个数当可领件数显示" / "前端据此显示
「不知道」"). Repo-wide search finds exactly one occurrence, the assignment:

```
$ grep -rn "\"available\"|'available'|\.available" --include=*.html --include=*.js --include=*.py .
monitor/scan.py:2706:        "available": _available,
```

`monitor/app.html` never mentions `board` (only a `pre.boardpre` CSS rule), and
`render()` writes `index.html` *before* `state["board"]` is assigned, so the
static page cannot show it either. `monitor/verify.py:208` checks
`board.listing` and **not** `board.available`, so `_available = None` is checked
by nobody. The fix is inert; the field that *is* consumed (`listing`) and the
one that feeds the gate's shape check are the ones left unguarded (D2).

### D7 · `claimed` is still two independent computations, and they drift on the documented duplicate-claim incident

`_supply()` reports `len(board_mod.claimed_map())` (a dict keyed by item id, so
duplicates collapse); `build()` reports `len(os.listdir(cd))` (raw file count).

```
files in claimed/                       : 3     # E8-ic3-scale.RES-1.md, E8-ic3-scale.W-1671.md, S4-freeze.RES-1.md
_supply()'s number  len(claimed_map())   : 2
page's number      len(os.listdir(cd))  : 3
live board right now:
   listdir = 5  claimed_map = 5
```

Two claim files for one id is not hypothetical — `board.py`'s own docstring
records `E8-ic3-scale` being re-claimed four times. This is the *same* class of
defect the commit fixed for `available` and did not fix for its neighbour in the
same dict.

### D8 · `_bus_probe()` imported the bus's vocabulary but kept a hand-rolled owed-rule, and now calls unread messages "已送达"

`scan.py:1042-1043` computes `pend` over **all** of `in.jsonl`.
`bus.py:118`'s own rule is `if r["seq"] <= last and r["kind"] in ACK_REQUIRED`
— only messages the agent has actually read can be owed.

```
(a) unread urgent, cursor=0 -> partial | 已送达，欠回执：RES-4(1)
    bus.py's own owed rule: ['if r["seq"] <= last and r["kind"] in ACK_REQUIRED']
```

A message the agent has never read is reported as *delivered and unacknowledged*.
Direction: over-report (alarming, not reassuring) — but the second hand-rolled
copy of a bus rule is still there, which was the stated reason for importing
`ACK_REQUIRED` in the first place.

### D9 · Finding 3 (schtasks codepage) has no behavioural negative control

Both probe-level tests for this fix (`test_a_disabled_task_is_detected_in_both_languages`,
`test_a_running_task_is_not_reported_disabled`) fail on the pre-fix code with
`AttributeError: module 'scan' has no attribute 'childio'` — i.e. they fail
because the new symbol is absent, not because the old code got the answer
wrong. What remains for this fix is a source-text grep and
`test_forcing_utf8_would_still_destroy_the_sentinel`, which asserts a property
of Python's codecs and touches no product code at all (it passes unchanged on
the pre-fix tree).

A behavioural control was constructible and was not written. Run against the
**pre-fix** `scan.py`, with the bytes `schtasks` really emits decoded the way
the old code decoded them:

```
$ cd .worktrees/s28-adv-oldcode/monitor && python -
OLD code, task genuinely Disabled -> green
detail: TheoriaReflex 运行中（reap / quota / 自动合并）；
```

The bug was real (this confirms the evidence file). The negative control for it
is not.

### D10 · `test_all_files_present_still_reads_green` cannot fail in the state its positive twin constructs

```python
assert r["status"] in ("green", "risk")
if r["status"] == "green":
    assert "4/4" in r["detail"]
```

`risk` is the exact status the fix introduces for a missing watched file, so on
any checkout where one of the four is absent this "NEGATIVE CONTROL" passes
without evaluating a single wording assertion:

```
live probe_append_only: green | 已核查 4/4 个追加式文件，无新增删除（…）
with one file absent  : risk
test_all_files_present_still_reads_green would PASS on that state: True
   -- and it never reaches its `4/4` assertion
```

It works today only because this checkout has all four files. A monkeypatched
`exists()` returning True would have made it unconditional.

---

## REFUTED HYPOTHESES

**A · the `meta()` regex fix can still be made to swallow the next line.**
Refuted for every realistic input tried. Old vs new, same fixtures:

```
empty + blank + title (LF)     new=None         old='#'
empty + CRLF                   new=None         old='#'
empty + trailing tab + CRLF    new=None         old='#'
empty at EOF no newline        new=None         old=None
colon then EOL no space        new=None         old='#'
indented field                 new=None         old=None
empty + NBSP + token           new='#'          old='#'      (same line — not a borrow)
```

CRLF is safe because `\r` is `\s`, so `(\S+)` cannot match it. Trailing
whitespace, tabs, a field at EOF with no newline, and `lane:` with no space are
all safe. NBSP does yield `'#'`, but the token is on the *same* physical line,
so this is "someone wrote `#`", not "the parser borrowed a line". The only
survivors are the five line-terminator characters in D4.

**B · the `available` count and the printed list are still two computations that can drift.**
Refuted inside `board.py`. All three partitions in `cmd_list` count and iterate
the *same* object:

* `print(... % len(generic))` then `for ... in generic` (`board.py:369-371`);
* `... % len(reserved)` then `for ... in sorted(reserved)` (`board.py:384-386`);
* `... % len(hidden)` then `for ... in hidden` (`board.py:405-407`).

No construction makes a header disagree with the lines under it. `_supply()` and
`build()` both call `board.candidates()`, the same function the `available`
partition prints, so the "two contradicting supply numbers" really is gone.
Double reporting between `blocked` and `territory-blocked` is also genuinely
prevented (`withheld_items` skips items with pending deps, and
`test_a_dependency_blocked_item_is_not_double_reported` passes on the pre-fix
tree as a proper control). What *did* survive is the sibling fields, not the
count: D2 (`blocked`) and D7 (`claimed`).

**C · remaining `except: pass` / unread returncode in the touched functions.**
Swept; the following are clean:

* `probe_append_only` — every git call goes through `git_or_none()` and an
  unanswered call returns `status: "missing"`. Failure direction alarming. Holds.
* `probe_scheduled_tasks` — `out.returncode != 0` is checked and produces
  `**未注册**` + `risk`. If `schtasks` itself is absent, `subprocess` raises
  through the unguarded probe comprehension (`scan.py:2595`) and takes the whole
  build down, which `main()`'s failure exit turns into a red page. Alarming. Holds.
* `_supply()` — `except Exception as exc` reports `risk / 板查不出来` with the
  exception type and text. Holds; verified by
  `test_a_board_that_cannot_be_queried_is_not_called_healthy`.
* `probe_verify_gates` — a missing `survey["decorative"]` key would raise, again
  taking the build down loudly. Alarming. Holds.

Remaining silent handlers in touched functions, with direction:
`_ack_required` (`scan.py:995-996`, silent, → D5); `build`'s
`except Exception: _available = None` (`scan.py:2703`, silent, no reason
recorded, no consumer → D6); `_bus_probe`'s `except Exception: pass` on a
corrupt `cursor.json` (`scan.py:1024-1025`, silent, but the effect is
`last = 0` → everything looks pending → over-report, alarming; it also silently
omits the agent from `seen_ok`, so the green line's "N 个会话在线" undercounts).

**E · the two narrowed assertions removed the thing worth testing.**
Refuted for both.

`test_the_claim_rename_catches_only_the_expected_race` — the 900-char window
after `os.rename(src, dst)`, comments stripped, is 8 lines and contains the
handler under test:

```
os.rename(src, dst)                # atomic: first one wins
        except FileNotFoundError:
            continue
        note("CLAIM %s by %s" % (iid, worker))
        …
```

Both assertions (`except FileNotFoundError:` present, `except OSError:` absent)
still bite, and this test fails on the pre-fix tree. Narrowing to non-comment
lines removed nothing.

`test_scheduled_tasks_are_read_with_the_console_codepage` — the window still
contains `childio.run_console([...])` and the full `disabled` computation, so
`'encoding="utf-8"' not in body` remains load-bearing. One cosmetic remark, not
a defect: the 2200-char window over-reaches by 12 lines into
`probe_spec_freshness`, so a future legitimate `encoding="utf-8"` on a *git*
call there would turn this test red for an unrelated reason. That direction is
false-red, i.e. safe.

**Not a defect, recorded as a judgement call.** `probe_verify_gates` stays
`green` with 22 of 24 gates never shown able to go red, and
`test_decorative_gates_do_not_by_themselves_turn_the_probe_amber` pins that
green in place. This is in tension with the item's own thesis, is argued
explicitly in the code and in `EVIDENCE-2`, and the number does now reach the
page. I found no repro that makes the choice wrong, only the observation that
the test now blocks the stricter reading as well as the sloppier one.

---

## NEGATIVE-CONTROL AUDIT

All 32 tests pass on the fixed tree (`python -m pytest
tests/test_board_no_third_value.py tests/test_scan_no_third_value.py -q` → 32
passed). Run against `1585dd04^` (`5a997ef8`) with the same two files: **26
failed, 9 passed** across both suites (11/15 board, 12/17 scan… see below; two
files were run together for the final tally: 26 failed).

`fails on old?` = **yes** means the test would have caught the defect.
**API-only** means it fails with `AttributeError` because a new symbol does not
exist yet — a weak control: it proves the symbol is new, not that the old
answer was wrong. **no (control)** is the correct result for a test whose job is
to pin preserved behaviour.

| test | fails on old code? | note |
|---|---|---|
| board · test_a_territory_blocked_item_is_no_longer_invisible | yes | partition absent from old output |
| board · test_nothing_withheld_prints_no_new_partition | yes (incidental) | labelled NEG CTRL; fails on old for an unrelated reason — the fixture's empty `lane:` parses as `#` there, so READY-1 is not available |
| board · test_an_item_on_an_ownerless_lane_is_also_surfaced | yes | `assert 'ORPHAN-1' in '=== available (0) ==='` |
| board · test_a_dependency_blocked_item_is_not_double_reported | no (control) | correct |
| board · test_an_unexplained_exclusion_says_so_instead_of_hiding | yes | |
| board · test_the_new_partition_survives_a_cp936_console | no | vacuous on old code (no new partition to encode); bites only on new code |
| board · test_the_lock_is_preferred_over_the_tracked_file | yes — API-only | `no attribute 'heartbeat_evidence'`. Behaviourally verified by hand: old `heartbeat_age` returns **0 minutes** for a lock 200 minutes old with a git-touched json, so the underlying claim is true |
| board · test_a_missing_lock_says_the_number_is_touchable | yes — API-only | same |
| board · test_never_started_is_still_none | yes — API-only | labelled NEG CTRL, but the contract it protects (`heartbeat_age → None`) is unchanged, so a real control here should have *passed* on old code |
| board · test_a_live_session_reads_fresh | no (control) | correct |
| board · test_stale_lanes_now_rests_on_the_untouchable_signal | yes | behavioural, no new API — **the load-bearing control for finding 4** |
| board · test_a_locked_file_no_longer_becomes_board_empty | yes | `DID NOT RAISE PermissionError` |
| board · test_the_claim_rename_catches_only_the_expected_race | yes | source assertion |
| board · test_an_empty_metadata_field_does_not_borrow_the_next_line | yes | old parses `lane` as `'deps:'` |
| scan · test_supply_asks_the_board_instead_of_reading_its_layout | yes | old detail: `板上尚剩 2 件可领` with `candidates()` monkeypatched to 1 |
| scan · test_supply_does_not_scrape_the_list_output | yes | source assertion |
| scan · test_a_board_that_cannot_be_queried_is_not_called_healthy | yes | old: `partial`, new: `risk` |
| scan · test_a_healthy_board_still_reads_green | yes | labelled NEG CTRL but behaviourally different on old code (`partial` vs `green`) |
| scan · test_scheduled_tasks_are_read_with_the_console_codepage | yes | source assertion |
| scan · test_a_disabled_task_is_detected_in_both_languages | yes — API-only | `no attribute 'childio'` → see D9 |
| scan · test_a_running_task_is_not_reported_disabled | yes — API-only | same |
| scan · test_forcing_utf8_would_still_destroy_the_sentinel | no | asserts a property of Python's codecs; touches no product code |
| scan · test_a_deleted_append_only_file_is_a_risk | yes | old: `green`, new: `risk` |
| scan · test_all_files_present_still_reads_green | yes (wording) | passes vacuously whenever a watched file is absent → D10 |
| scan · test_the_gate_count_admits_how_many_were_never_proven | yes | `the decorative count must reach the page` |
| scan · test_decorative_gates_do_not_by_themselves_turn_the_probe_amber | no (control) | correct |
| scan · test_the_ack_vocabulary_comes_from_the_bus | yes — API-only | `no attribute '_ACK_REQUIRED'`; and it cannot detect the fallback → D5 |
| scan · test_an_unacknowledged_urgent_is_owed | yes | old: `green`, new: `partial` — behavioural control for finding 9 |
| scan · test_an_acknowledged_urgent_is_not_owed | no (control) | correct |
| scan · test_a_notice_never_owes_a_receipt | no (control) | correct |
| scan · test_every_new_probe_line_survives_a_cp936_console | no | vacuous on old code: the strings it looks for do not exist there, so the loop body never runs |

Per-fix summary of the claim "每条修复都配阴性对照":

| fix | has a test that fails pre-fix? | behavioural (not API-only / not source-grep)? |
|---|---|---|
| 1 territory-blocked partition | yes | yes |
| 2 `_supply` asks the board | yes | yes |
| 3 schtasks codepage | yes | **no** → D9 |
| 4 heartbeat lock vs tracked mtime | yes | yes (`test_stale_lanes_now_rests_on_the_untouchable_signal`) |
| 5 claim rename catches only FileNotFoundError | yes | yes |
| 7 append-only missing file | yes | yes |
| 8 decorative gate count | yes | yes |
| 9 ACK vocabulary from the bus | yes | yes (`test_an_unacknowledged_urgent_is_owed`) |
| extra: `meta()` empty field | yes | yes (for `lane` only — `deps`/`released_by` uncovered → D1) |
