# Adversarial review — V6-V22-wintighten-absent-vs-below

Reviewer: adversarial pass, read-only against the source under review.
Base: `9bc8c8806840a1b0942df6dbb17bd5e5e999ed5e`.
HEAD when the review started: `463bf1f1`. HEAD when it finished: `71d23d57`.

**The worktree was being written while it was being reviewed.** Four commits
(`bf9e8fae`, `a92215d6`, `9c424693`, `71d23d57`) landed between 21:19 and 21:23
local, during this pass. I hashed every `proxy/` file at the start and again at
the end: `variants.py`, `tools/check_variant_degeneracy.py`, `env_proxy.py`,
`verify.py` and `tests/test_variant_degeneracy.py` are **byte-identical**
across that window, so every finding below is against code that did not move.
What moved was the run directory (see F6).

Everything below was run offline. No network, no `.env`, no key read, no file
outside this run directory written. Probe scripts were written to the session
scratchpad, not into the repo; mutations were applied to temp copies.

---

## F1 — HIGH. The incident consumer can be lost entirely, under exactly the concurrency its own design invokes

**What I did.** Read `env_proxy._note_degeneracy` and noticed it tests
`runtime.degenerate_wins != 1` — a read of a *shared mutable counter at notify
time*, not a value captured at rewrite time. `after()` takes no lock and
`VariantRuntime` has none. `env_proxy` serves on a `ThreadingHTTPServer` with
`daemon_threads = True` (`env_proxy.py:532,536`), and `runtime_for` hands the
same `VariantRuntime` to every command for a given `game_id`. So I drove the
real `_Handler._note_degeneracy` with the real `VariantRuntime` through two
interleavings:

* serial — `after()`, notify, `after()`, notify;
* interleaved — `after()`, `after()`, notify, notify (two commands for the same
  game in flight, both responses rewritten before either handler reaches its
  notify).

**What I observed.**

```
serial interleaving                          -> incidents: ['variant_degenerate']
interleaved (A,B rewrite; then both notify)  -> incidents: []
degenerate_wins = 2 | first_degenerate recorded = True
VERDICT: INCIDENT LOST
```

Both notifiers read the counter at 2, both take the `!= 1` early return, and
**no incident is written at all** — while 33 degenerate rewrites go into the
ledger and `first_degenerate` sits populated and unread.

**Does it refute a claim?** Yes, two.

D-032 and `RUN_STATE.md` both say "`env_proxy` records one `variant_degenerate`
incident per session". It records *at most* one; under interleaving, zero.

Worse, the mitigation is aimed at the wrong half of the race. The
`state.degeneracy_reported` set defends against the incident firing *twice*,
and the new test
`test_the_incident_is_written_once_even_if_the_edge_is_seen_twice` pins that
direction — its docstring explicitly cites "two commands for the same game can
be in flight at once (`ThreadingHTTPServer`)" as the justification. That
docstring is correct about the hazard and then pins the benign half of it. The
harmful half — the incident vanishing — has no test and no defence. A duplicate
incident is noise; a missing one is the silence this whole ticket exists to
remove.

This is not fatal to the change: `check_variant_degeneracy.py` reads per-record
markers and still refuses such a run, so the defect is recoverable from the
ledger. But the second consumer, the one advertised as living "in the live
path, not only by a tool someone has to remember to run", is the one that can
go quiet.

The fix is small — have `after()` report whether *this* call was the first
degenerate rewrite (it already knows: `self.degenerate_wins == 1` inside the
branch), and let `_note_degeneracy` act on that return value rather than
re-reading the counter — but it is not in this change.

---

## F2 — HIGH. The guard fails open, silently, on exactly the ledger corruption this change documents

**What I did.** `RUN_STATE.md` and `_vault_without_toy_secrets`' docstring
disclose a `redact.py` defect: `VAULT` is process-global, `Vault.scrub` scrubs
dictionary **keys** as well as values (RED-17), and `register(force=True)`
bypasses `MIN_SECRET_LEN` (RED-14), so a short forced secret rewrites ledger
field names — `kind` becomes `<redacted>ind`. The disclosure stops at "a
genuinely short live key would corrupt field names in a real ledger the same
way." It does not ask what happens when the corrupted field is one the **new
guard** reads.

`ledger.py:237` confirms every record goes through `VAULT.scrub()` on its way
to disk. So I took one real `env_step` record in the exact shape `env_proxy`
writes, scrubbed it under a series of short forced secrets, and put the result
in front of `scan_records`.

**What I observed.**

```
unscrubbed            -> REFUSED

secret='k'   verdict=REFUSED  applied keys now: ['degenerate', 'effect', 'occurrence', 'op', ...]
secret='ate' verdict=PASS     applied keys now: ['degener<redacted>', 'effect', ...]
secret='app' verdict=PASS     applied keys now: []
secret='ari' verdict=PASS     applied keys now: <no `variant` key>
secret='op'  verdict=PASS     applied keys now: ['<redacted>', 'degenerate', ...]
```

Any short forced secret that is a substring of `variant`, `applied`, `op` or
`degenerate` turns a stream full of degenerate rewrites into `PASS`, exit 0,
with no diagnostic whatsoever.

**Does it refute a claim?** It refutes the change's implicit claim to have
removed a silent collapse. It reproduces the *same failure shape* one layer up:
a condition that should be loud, collapsing into an outcome indistinguishable
from "nothing happened". D-032 argues at length that a warning is the wrong
answer because "the failure mode is a variant claim read six weeks later from a
ledger" — and the guard that replaces the warning has a mode in which the
ledger it reads six weeks later cannot be distinguished from a clean one.

Two honest caveats. First, this requires a sub-12-character credential
registered with `force=True`; with the one the suite actually registers (`"k"`)
the guard is unaffected, which is why nothing here is red today. Second, the
underlying defect is genuinely pre-existing and genuinely not this ticket's to
fix.

But the workaround's honesty is incomplete in a way that matters. It is honest
that the defect exists and honest about the mechanism. It is silent on the fact
that the defect **fails the new guard open**, and installing the workaround in
the fixture guarantees the suite can never notice. The right disposition is one
sentence in `RUN_STATE.md` and a note on the filed ticket saying the V22 guard
is downstream of it — not a code change under this ticket.

---

## F3 — MEDIUM. The guard cannot tell "nothing degenerate happened" from "I saw nothing"

**What I did.** `scan_file` silently `continue`s past any line that will not
parse, defended by this comment:

> "Not this tool's complaint to make: validate_ledger.py owns unreadable lines.
> Skipping one here cannot hide a degenerate rewrite that a readable line would
> have shown."

I fed the tool three streams: one intact with a marker; one where the marked
line is truncated mid-JSON (what a killed writer leaves); one with no variant
records at all.

**What I observed.**

```
intact (marker present)   -> REFUSED (2 records, 1 degenerate rewrite(s))   exit 2
marked line TRUNCATED     -> PASS    (1 records, 0 degenerate rewrite(s))   exit 0
no variant records at all -> PASS    (1 records, 0 degenerate rewrite(s))   exit 0
```

The last two are byte-identical. The report has `records` (all records, variant
or not) and `findings`, and nothing that says how many variant records were
walked or how many lines were skipped.

**Does it refute a claim?** Yes — the comment quoted above. It is a tautology
dressed as a safety property: of course a skipped line cannot hide what "a
readable line would have shown", because the skipped line is precisely the one
that would have shown it. The sentence reads as an argument that skipping is
safe, and it is not one. Prose the code does not support.

A `variant_records` count and a `skipped_lines` count in the report would close
both this and half of F2, and would cost about four lines.

---

## F4 — MEDIUM. Rung 5's stripper is asymmetric with the guard it exists to test

**What I did.** Compared the guard's unwrapper with the two places that strip
markers. `_applied_records` **recurses** through `{"op":"multiple"}` — and
there is a test pinning that (`test_the_guard_sees_a_marker_nested_under_multiple`,
with a deliberately doubly-nested record). But both strippers are top-level
only:

* `verify.py:481` — `applied = (record.get("variant") or {}).get("applied")`,
  then `applied.pop("degenerate", None)` if it is a dict;
* `test_stripping_the_marker_lets_the_scoreless_session_through` — the same
  shape.

**What I observed.** Harmless today: `PLAY_SCORELESS` and the test fixture both
declare a single `win_tighten` operator, so no `applied` record is ever nested
and my rung-5 baseline run stripped all 13 markers cleanly. But `env_proxy.py:408`
nests as soon as an outbound rewrite and an inbound one fire on the same
command, and `variants.after()` nests when `observation_loss` and `win_tighten`
both fire.

**Does it refute a claim?** No — it is a latent fragility, not a false claim.
Add a second operator to rung 5's variant and the stripper leaves a nested
marker behind, the guard (correctly) still refuses, and rung 5 fails with *"with
the marker removed the guard still refused — it is not the marker that catches
this"*. That message would be false, and it points at the guard rather than at
the stripper. The guard was written to recurse and given a test for it; the two
strippers that mirror it were not. Reusing `_applied_records` in both would
remove the asymmetry.

---

## F5 — MEDIUM. P4's "the whole suite" was quietly reinterpreted as three test files

**What I did.** Compared `PREREGISTRATION.md` P4 — "At least 15 distinct source
mutations, spread over all three files that carry the new behaviour … **each run
against the whole suite**" — against `mutants.py`:

```python
TESTS = ["-m", "pytest", "proxy/tests/test_variant_degeneracy.py",
         "proxy/tests/test_variants.py", "proxy/tests/test_e2e.py", "-q",
         "-x", "--no-header"]
```

**What I observed.** Three files, not the suite. Nothing in `RUN_STATE.md`,
`MANIFEST.json` or `mutants.py` calls this deviation out; `mutants.py`'s
docstring discusses the mutant *surface* at length and says nothing about the
test surface being narrowed.

**Does it refute a claim?** It is a criterion not met as written, and not
flagged. In fairness the deviation runs in the *conservative* direction — a
smaller test set makes mutants **harder** to kill, so the 24 kills are if
anything understated, and I confirmed five of them independently. So this
weakens the pre-registration's discipline rather than the result. P4's other
clauses (≥15 mutants: 25; all three files: 14 / 7 / 3 plus 1 on the mock; a
deliberate expected survivor: M14; survivors reported not dropped: M17/M24 were
reported) are met.

One side effect worth naming: the narrowed set excludes `test_spend_gate.py`,
which is the file that pollutes the vault — so the mutation harness never
exercises the redaction interaction that F2 is about, in either direction.

---

## F6 — MEDIUM (provenance). At the commit I was handed, the committed mutation matrix was the known-false one and `MANIFEST.json` did not exist

**What I did.** Checked the pre-registration's own integrity claims first.
`git merge-base --is-ancestor 4fa378de HEAD` → **yes**; `git log -- PREREGISTRATION.md`
shows exactly one commit, so it was never amended after the fact. That part is
clean and I could not break it.

Then I read the artifacts at the then-HEAD `463bf1f1`.

**What I observed.** At `463bf1f1`, the committed `mutants.json` said
`"killed": 25, "mutants": 25`, had **no `control` key**, and listed M14 — the
mutant declared in the same file as "EXPECTED TO SURVIVE" — with
`"verdict": "killed"`. That is the false first run, the one `RUN_STATE.md`
correctly describes as worthless, committed as the result. `MANIFEST.json` was
absent, while `PREREGISTRATION.md:9` says "base_commit at pre-registration:
recorded in `MANIFEST.json` as `base_commit`" and `RUN_STATE.md:3` says "The
machine-readable half is `MANIFEST.json`" — both pointing at a file that did not
exist. `CLAUDE.md` makes that file mandatory for every run.

Between 21:19 and 21:23, while this review was in progress, the author landed
`bf9e8fae` (the two survivor-killing tests), `a92215d6` (rung-5 red evidence),
`9c424693` (`MANIFEST.json`, the corrected matrix, `pytest.txt`) and `71d23d57`.
At `71d23d57` the matrix reads `killed 24 / 25`, control `SURVIVED`, sole
survivor M14 — which is the honest result — and `MANIFEST.json` exists with
`base_commit`, `prompt_id`, `branch`, `utc`, `preregistration_is_ancestor_of_head`,
and a `mutation.note` that states the first run's falseness in the machine-readable
record and not only in the narrative.

**Does it refute a claim?** Not at HEAD. Both defects were self-corrected. I
record it because the review was commissioned against a tree in which the
headline artifact contradicted the narrative, and because a reviewer arriving at
`463bf1f1` — or a merge gate reading it — would have been handed 25/25.

---

## F7 — LOW. Of the "two readers", only one changes an outcome

**What I did.** P2 sets the bar at "a non-zero exit code, a refused verdict, or
a record that a gate reads". Grepped every consumer of `variant_degenerate` and
of `event == "incident"`.

**What I observed.** The guard clears P2 outright: `main()` returns 2, and M18
(`return 0` instead) and M21 (verdict hard-coded `PASS`) are both killed by
behavioural assertions I reproduced myself.

The incident does not. Outside `tests/`, the only other reader of any incident
is `tools/triage_credential_incidents.py`, which filters
`kind == "credential_in_body"`. `validate_ledger.py` has no incident logic at
all. Nothing gates on it. M22 (delete the `_note_degeneracy` call) *is* killed —
so something would notice if it stopped being written — but the something is the
test suite, not an outcome.

**Does it refute a claim?** Not P2, which only needs one qualifying consumer.
It qualifies D-032's framing: "A bit with no reader is decoration, so it has two
readers." True of the bit; the two readers are not peers. One exits non-zero;
the other appends a record whose only reader is the suite that asserts it was
appended. That is a reasonable design — an incident is *for* a human reading the
ledger later, which is D-032's stated failure mode — but "two readers" invites a
stronger inference than the wiring supports, and F1 shows the weaker of the two
is also the one that can silently not fire.

---

## F8 — LOW/MEDIUM. On axis (c): the adjudication is *not* evasive, but its "executable half" is never pointed at a real ledger

**What I did.** The brief asks whether R-V22 is prose wearing a JSON key. I
took the question in two parts: is the *reasoning* evasive, and is the
*enforcement* real.

**What I observed, on the reasoning.** It is not evasive, and it is the
strongest part of the change. D-032 refuses the fourth certificate form on a
substantive argument, explicitly *not* on the territory boundary: the three
frozen forms are arguments about the world (board, alphabet, reachability),
whereas "this game reports no score" is a fact about the **protocol**, learned by
looking rather than by arguing. Adding a form would let a certificate earn
reason-credit for restating a property of the measuring instrument, and — the
sharper half — would make the degenerate construction *legitimate*, handing the
library's one non-game-agnostic operator a certificate that makes it look
game-agnostic. It then does the thing that was actually required: converts the
0.95 ceiling from an unexplained calibration gap into a named exclusion rule,
and names the `exam/`-side line it cannot write as **owed** rather than claiming
it. I have no criticism of this reasoning.

**What I observed, on the enforcement.** `check_variant_degeneracy` is invoked
from exactly three places: `verify.py` rung 5, `tests/test_variant_degeneracy.py`,
and `README.md` as a command a human types. Nothing in `runner.py`, no campaign
path, and no CI step runs it over `proxy/var/ledger.jsonl` or over any run
artifact. Rung 5 runs the guard **only against a ledger rung 5 itself fabricates
seconds earlier**.

So the accurate statement is: the *detector* is CI-enforced (`monitor/`'s merge
gate runs a territory's `verify.py`, and rung 5 is inside it, so the guard
cannot rot unnoticed), but the *rule* is not applied to any production run by
anything. R-V22 fires on a real campaign only if a human remembers to type the
command.

**Does it refute a claim?** It refutes a sentence. D-032 says the `exam_eligible:
false` report and the exit 2 mean "the fact reaches a grader in a form that
costs something to ignore". The fact reaches a grader only if someone runs the
tool; nothing obliges anyone to. "Costs something to ignore" describes a gate,
and this is a command.

Is that enough? Given the constraint, **yes, but it should be said plainly
rather than in that phrasing.** `exam/` is genuinely another territory and the
repository's one-territory-one-owner rule is exactly the thing that keeps two
concurrent sessions from colliding — crossing it would be the worse error, and
`PARTNER_SYNC.md` records a previous session refusing the same trade for the
same reason. The proxy-side rule is boundary-respecting and not an excuse. But
there is a third option that was available and is not taken: `proxy/` could run
the guard over the ledger a run just produced, inside `runner.py` or at
run-close, and record the refusal in the run's own record. That is entirely
inside this territory and would make R-V22 fire without anyone remembering
anything. Its absence is the gap; the territory boundary does not explain it.

---

## What I could not break

Stated as findings, not padding: I attacked each of these and failed.

* **P1 is solid.** An absent-score record and a shortfall record differ in
  `reason`, `degenerate` **and** `score`, and cannot be made equal by any input:
  the two branches are mutually exclusive on `have is None` and write disjoint
  constants. M01–M06 (collapse the split, pin the bit true, pin it false, swap
  the reasons, drop the bit) are all killed by behavioural assertions.
* **The conservative direction is intact and pinned.** M09 — the dangerous
  inverse, letting an absent score *pass* a tightened win — is killed.
* **Rung 5 is not a rung that passes no matter what.** I built four temp copies
  and broke it four independent ways, none of which the author's own
  `rung5_red.py` covers in full: guard never refuses → RED; guard always refuses
  → RED (the strip-and-pass arm catches it); the `degenerate` marker never
  written → RED; the scoreless world quietly starts scoring → RED. Unmodified →
  green. It cannot be green by construction.
* **The mutation control M00 is real, not a rubber stamp.** It replaces an
  anchor with itself, so it exercises `build_tree` and the identical test
  command in the identical tree the mutants get, and `run_one`'s
  `count != 1` check means a control that failed to apply would be reported
  rather than skipped. I re-ran it: SURVIVED, 22.3 s (a full green run) against
  ~1 s for each kill, which is the signature of `-x` stopping early — consistent
  with real kills rather than collection errors. `main()` refuses to print kill
  counts at all if the control fails.
* **The kills are genuine.** I applied M01, M17, M18, M21 and M24 myself in temp
  copies. Every failure is a named behavioural assertion inside
  `test_variant_degeneracy.py` — `assert 'score_absent' == 'score_below'`,
  `assert 'REFUSED' == 'PASS'`, a duplicated incident in a list — not an import
  error, not a collection error, not a missing fixture. This is the failure the
  first harness run had, and it is not present in the second.
* **The two behavioural survivors were genuinely fixed.** Before the author
  committed them, I ran the harness against the working tree and confirmed M17
  (guard flags any operator carrying the key) and M24 (once-per-session guard
  removed) are now **killed** by the two tests added for them. Both new tests
  say in their docstrings that they exist because a mutant survived. That is the
  honest handling P4 asked for.
* **The scoreless session is genuinely scoreless end-to-end, not hand-fed.**
  `MockArc(scoreless=True)` → `World` → `Session.body()` returns
  `"score": None if self.scoreless else self.levels_completed`; the test drives
  `run_game` through both proxies over real loopback HTTP and reads back a
  127-record ledger with 33 marked rewrites. And the fixture itself is pinned:
  M25 (the scoreless world quietly starts scoring) is killed.
* **P3b is real — the guard reads the marker and only the marker.** I read the
  source: `scan_records` branches on `applied.get("degenerate") is not True` and
  never looks at `score`. Stripping the marker yields PASS in the unit test, in
  the evidence file, and in my own rung-5 baseline (13 markers removed → exit 0).
  There is no second signal it could be catching.
* **P3d is real.** Forging a single marker into the scoring stream flips it to
  REFUSED with exactly one finding, so the scoring session's PASS is a fact
  about the input rather than about a guard that cannot fire there. Both halves
  of the negative control are present, which was the thing the brief was most
  suspicious of.
* **The nesting attack fails.** I tried to hide a marker under
  `{"op":"multiple"}`; `_applied_records` recurses to arbitrary depth and there
  is already a test with a doubly-nested record. (The *strippers* do not
  recurse — F4 — but the guard does.)
* **`_vault_without_toy_secrets` is an honest workaround, in scope.** It drops
  only sub-`MIN_SECRET_LEN` entries, restores the list in a `finally`, touches
  no code under test, and is disclosed in `RUN_STATE.md` with the mechanism
  named and the ticket filed separately. It does not hide any V22 defect — I
  checked what fails without it, and it is `record["kind"]` on the incident
  assertions, exactly as described. What it does not say is F2.
* **The pre-registration is genuine.** `4fa378de` is an ancestor of HEAD, it is
  the first commit on the branch, and `git log` on the file shows it was never
  touched again. No criterion was edited after results existed. P4 was deviated
  from in implementation (F5), not rewritten.
* **P6 holds.** `python -m pytest proxy -q` → exit 0 (341 passed at my run,
  343 after the two tests were added), and no pre-existing test file was edited:
  the diff touches only new files plus source, with `test_variants.py` and every
  other existing test untouched.

## Axes with nothing on them

Asked to say so explicitly rather than pad: **on axis (b) I found no way to make
the negative control itself unsound.** Both kinds of session are really
falsified, in both directions, on real end-to-end runs, and the mutation harness
that backs it has a real control and real kills. F2 and F3 are ways to defeat
the *guard*, not defects in the negative control's construction.

The three headline items are, in my judgement, delivered: the split is real
(F-none), the negative control is real (F-none), and the certificate adjudication
is substantive rather than evasive (F8, first half). The findings that matter are
F1 — the loud consumer has a silent failure mode, and the test written to defend
it defends the wrong half — and F2 — the guard has a documented, filed, unfixed
upstream defect that turns it green.
