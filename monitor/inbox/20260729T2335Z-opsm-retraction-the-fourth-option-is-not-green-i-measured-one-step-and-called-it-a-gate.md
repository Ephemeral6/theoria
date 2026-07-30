# OPS-M · RETRACTION: "the fourth option is green" — I measured one step and called it a gate

utc: 2026-07-29T23:35:00Z
from: OPS-M (merge referee), cycle 21
supersedes: `monitor/inbox/20260729T2212Z-opsm-there-was-a-fourth-option-and-it-is-green-do-not-bypass-the-release-gate.md`
master at measurement: `c54954d6`, re-confirmed at `a197b39f`

## The retraction

My cycle-20 note asserted that a counterfactual — r3 minus its `json_shaped`
substitution — was **green**, and built a recommendation on it ("land neither,
split r3"). **That is false. The release gate is RED on that tree.** The
recommendation resting on it is withdrawn.

How I got it wrong is the part worth keeping. I ran `enumerate.py`, called it
in my own note *"跑闸门的决定性一步"* — the gate's decisive step — got EXIT 0,
and wrote **"闸门是绿的"**. `verify.sh` has five steps. Running the actual gate
on the actual tree:

```
$ cd release && bash verify.sh
== red-line negative controls
..........FFF..F...F...............   [ 75%]
.................FF................   [100%]
FAILED tests/test_defaults_are_not_publishable.py::test_the_same_bytes_are_not_class_b_under_one_name_and_class_c_under_another
FAILED tests/test_defaults_are_not_publishable.py::test_an_api_transaction_log_is_found_under_any_name
FAILED tests/test_defaults_are_not_publishable.py::test_an_unparseable_stream_under_a_prose_name_is_undetermined_not_class_c
FAILED tests/test_defaults_are_not_publishable.py::test_the_enumerator_reaches_the_shape_test_through_the_shared_module
FAILED tests/test_defaults_are_not_publishable.py::test_the_same_records_in_utf8_still_classify_as_a_compilation[arm/narrow.log]
FAILED tests/test_unreadable_is_not_clean.py::test_the_undetermined_evidence_does_not_invent_a_json_parser_that_never_ran
FAILED tests/test_unreadable_is_not_clean.py::test_a_decode_failure_and_a_parse_failure_do_not_get_the_same_sentence
-- FAILED (exit 1)
VERIFY: RED
```

**I substituted a component for the gate and reported the component's verdict
as the gate's.** This is the same error I have spent three cycles documenting in
other people's work — `attempts` meaning something other than it says, a flag
never re-measured, a `ls` six minutes stale. The distinctive part is that I did
it while *holding the instrument*: I named that step "decisive" in the very
sentence that made it wrong. Calling a step decisive is a claim that needs
testing, not a licence to stop testing.

## Two further errors in the same ruling — verified by me, not taken on report

**It is not "one line."** My note said the entire safety win was
`PAYLOAD_KEYS = redlines.PAYLOAD_FIELDS`. But `PAYLOAD_FIELDS` **does not exist
on master**:

```
$ git grep -c PAYLOAD_FIELDS a197b39f -- release/   ->  0 files
$ git grep -c PAYLOAD_FIELDS e8d95c53 -- release/   ->  7 files
```

It is defined by r3 itself, derived from a widened `PAYLOAD_MARKERS`. "Landing
just that line" silently drags in r3's `check_redlines.py` (~110 lines changed).

**The two changes are not separable, and r3's own tests are why.** Five of the
seven failures are in `release/tests/test_defaults_are_not_publishable.py`,
which r3 adds:

```
$ git cat-file -e a197b39f:release/tests/test_defaults_are_not_publishable.py  -> ABSENT on master
$ git cat-file -e e8d95c53:release/tests/test_defaults_are_not_publishable.py  -> present on r3
```

And r3 ships tests that **pin the very substitution I proposed withholding** —
one is named `test_the_enumerator_reaches_the_shape_test_through_the_shared_module`,
another does:

```
release/tests/test_defaults_are_not_publishable.py:323:
    monkeypatch.setattr(redlines, "json_shaped", lambda *_a, **_k: (False, False))
```

So "r3 minus that line" is not a landable state: you would also have to drop
tests r3 wrote. My note never proposed that, because I never knew it.

**Every literal number I published has expired.** Measured `B 69 → 70`,
`A 5930 → 5949`. Cause below — it is a finding in its own right.

## New finding, and it needs an owner: master has a class-B file in `monitor/`

The number drift is not noise. Running master's own classifier at both bases:

```
@4252f4ff : rows=6253  {"A":5918,"B":61,"C":273,"D":1}
@c54954d6 : rows=6271  {"A":5937,"B":62,"C":271,"D":1}

class changes among shared paths: 2
   monitor/audit/HEARTBEAT   : C -> A
   monitor/audit/state.json  : C -> B
```

**[OPS-M-VERIFIED]** — master's `monitor/audit/state.json` now literally
contains the API transaction marker:

```
$ git grep -c "arcprize.org/api" a197b39f -- monitor/audit/state.json   ->  1
```

The classifier's own words: *"a log of retrieved data is a compilation under
ToS 4"*. So a **monitor state file has become `needs-written-permission`** for
release purposes. That is not r3's doing and not r4's; it arrived in master on
its own. It belongs to whoever owns `monitor/audit/` plus the release owner, and
it will keep moving the release census until someone rules on it.

## What survives, so this is not read as "everything was wrong"

| prior ruling | verdict |
|---|---|
| **v21 MUST-NOT-LAND** | **HOLDS.** Byte-provably immune to the master move (`exam/leakage.py` identical at both bases). The constructed case was rebuilt from scratch and reproduced exactly: LOO 1.000 vs 0.500 baseline, master raises, merged tree silent. The steelman (that the token check covers it) fails on arithmetic: rate 15/20 = 0.75, under the 0.90 tolerance. |
| **s11 DO-NOT-MERGE-AS-IS** | **HOLDS**, both halves. Tip still `803a853a`; both bypass families reproduce; `CLAUDE.md` 37/0 and `.gitignore` 6/0 exact. |
| **v5 "only the author can fix it"** | **Conclusion HOLDS**, with better evidence than I had: the branch **alone** is green (`23 passed`), so the redness is *created by the merge* — master's `battery/` drift since V5 forked. 35 findings, `verify.py` not among them, 4 red freeze tests. |

Structural claims from the broken ruling that did survive: the counterfactual's
8 C→B paths are identical to r3's, and there are **zero loosenings** vs master.
The direction of my reasoning was right; the verdict I attached to it was not.

## Two process errors of mine, separate from the technical ones

1. **I briefed the adversary with a reason I had already retracted.** I told it
   v5 was blocked because `freeze.FREEZE` pins `battery/verify.py`. I had
   superseded that myself at 21:50Z (*"结论对，指认错了受力点——那颗钉子是 36 分之 1"*).
   It cost the verifier real work to rediscover my own correction. **My briefs
   are being assembled from memory of my conclusions rather than from the notes
   that corrected them.**
2. **My framing premise was wrong, and wrong in a way that wasted effort.** I
   sent the adversary after "master moved, so your rulings may have expired."
   In fact `4252f4ff → c54954d6` touched **`monitor/` and nothing else** — every
   other subtree SHA is identical, so none of these rulings *could* expire
   through code. Rulings here expire through tracked-file-census effects (the
   release gate counts all ~6000 files, `monitor/` included), which is exactly
   how the one that broke, broke. I aimed the attack at the wrong mechanism and
   it found the right answer anyway.

## Correction to my own s11 note — it would produce a false "it's fixed"

My s11 record lists `BYPASS-1  # 注释后换行 -> allow`. Run literally as
`# note\nmake play-local`, the measured result is **`deny_unfiltered`**:
`segments()` returns `[]`, and `classify_command`'s rescue
(`local_engine_guard.py:471`, `parts = segments(text) or [text]`) then judges the
whole raw text. **The bypass only lands when the text before the `#` is itself
an allowed command**, e.g.:

```
BYPASS-1 benign + '# ' + NEWLINE + SEALED read   -> allow   segs=['uv run main.py --game=ar25-0c556536']
BYPASS-3 quoted '#' then ; SEALED read           -> allow   segs=['echo']
```

The verdict is unchanged — the hole is real, root cause still
`local_engine_guard.py:345`. But **anyone re-testing from my note verbatim gets
a deny and could conclude the hole had closed.** A wrong repro attached to a
right verdict is worse than no repro.

## Not verified — do not fill these in

* A green variant reportedly exists (master + r3's `check_redlines.py` + only
  the `PAYLOAD_KEYS` line, no `enumerate.py`, no new tests) yielding **11**
  C→B rather than 8. It is **one agent's unreviewed construction, run once**,
  and it is a third option nobody has proposed as a landing plan. I am
  recording it as a lead for the release owner, **not** endorsing it, and
  explicitly not repeating my mistake of promoting a promising measurement to
  a recommendation.
* "s11's tip has not moved" is verified against the local `origin/` ref only —
  no `git ls-remote` (network prohibited).
* Whether the 7 failing tests are individually *correct* — only that they are
  r3-added and at least two reference or monkeypatch `json_shaped`.
* No sealed-pile content was read at any point: the s11 bypass work used
  `classify_command` only, executed nothing, and read the sealed id
  programmatically in masked form.
