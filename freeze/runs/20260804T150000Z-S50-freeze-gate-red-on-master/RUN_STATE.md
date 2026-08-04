# S50 · the freeze gate was red on master, and two of its three reds were not about the tree

**Worker** W-9209 · **territory** `freeze` (plus the two `tools/` files the item
explicitly authorised) · **branch** `agent/s50-freeze-gate-red-on-master` ·
**base** `18e7d81b` · **UTC** 2026-08-04.

## What was red, and what it was actually red about

`bash freeze/verify.sh` on master: **3 failing stages**, blocking `ci_merge`
for every freeze-touching branch — s45 had already been ruled "no new failure,
not its fault, blocked by master". After this ticket: **82 PASS, 0 FAIL**,
stable over three consecutive runs.

Regenerating the artefacts, which is what the item prescribed, would have
cleared **one** of the three. The other two were red for reasons that had
nothing to do with the tree, and the report of that is the substance of this
run:

| stage | the item's diagnosis | what it actually was |
|---|---|---|
| [12] MANIFEST | drift from the tree | correct — regenerate, 13 attributed drifts |
| [15b] BUDGET_TABLE | "the balance really moved, regenerate" | correct **and insufficient**: two of the compared inputs were not facts about the tree at all |
| [18] locations | new runs need dated exemptions | correct — 11 signed — but the run half of that gate had no negative control |

---

## [12] · MANIFEST.json regenerated — every drift, and the fact behind it

The manifest was last committed at `263c5ff4`, recording commit `e8345aff`;
**71 commits** sit between that and `18e7d81b`. With `freeze/BUDGET_TABLE.json`
pinned at HEAD the drift is exactly **13 hash lines**, every one a tracked-blob
change (the manifest hashes tracked paths from `git show HEAD:<path>`, not from
disk):

| # | drifted path | what changed | landed by |
|---|---|---|---|
| 1 | `theoria-arm/inner` | 14 → 17 files: `+scoreboard.py`, `+economy.py`, `+anchor.py` | `ce2a3a8e` (A27), `b5fa23f0` (A25), `cd748188` |
| 2 | `theoria-arm/harness` | A18 self-scoring + ledger flag; A25; A27; R1b census pins | `8ec111fb`, `b5fa23f0`, `ce2a3a8e`, `33c449c1` |
| 3 | `theoria-arm/armtools` | 15 → 19 files: `+action_economy.py`, `+desk_yield.py`, `+goal_forensics.py`, `+replyloss.py` | `b5fa23f0`, `151fdf5a`, `20ebfd9e` |
| 4 | `theory-compiler/.../generators` | "r2-2 was never a grammar hole: the compiler lied about it" | `5ee845ee` |
| 5 | `baseline-arms/harness/bare_cc.py` | A19 — the ARC credential leaves the bare_cc arm process | `db33f983` |
| 6 | `theoria-arm/inner/probe.py` | stale-anchor fix (97.7% of commands) | `cd748188` |
| 7–10 | `battery/metrics`, `battery/audit`, `battery/run_battery.py`, `battery/BATTERY_V1.md` | S46 — "an axis that cannot be rebuilt is a measurement that was not taken" (+ S46 step 0 archive move for BATTERY_V1.md) | `1efc8dbf`, `7befaef7` |
| 11 | `theoria-arm/harness/budget.py` | A27 | `ce2a3a8e` |
| 12 | `baseline-arms/STATUS.md` | A19 + the A19 follow-up (GAP-5 split sha) | `db33f983`, `86d0f7bb` |
| 13 | `baseline-arms/DECISIONS.md` | A19 | `db33f983` |

**Nothing unattributable.** But two corrections to the item's framing, both
worth recording because the next reader will otherwise repeat the search:

* **The item's cause (i) — register #13/#14 — is not in the manifest at HEAD.**
  The money rulings reach `MANIFEST.json` only through
  `freeze/BUDGET_TABLE.json`. #13's own cost clause ("freeze/MANIFEST 第 12 项
  不得在超支状态下报 ready") was *already satisfied* by the committed manifest.
  So the money drift is strictly downstream of [15b], which is the ordering the
  work actually had to follow.
* **The item's cause (ii) — new tracked run directories — is absent.** The
  manifest hashes only four run-ish paths and none of them changed; the new
  `theoria-arm/runs/*` directories are not in the manifest at all. That claim
  belongs to stage [18], not [12].

### The v0.4 hole, which the item asked to adjudicate

W-9204's inbox note
(`20260802T085557Z-...-freeze-manifest-will-not-hash-dsl-grammar-v0-4.md`) is
**correct in every particular**, independently verified:
`CONTRACTS/dsl_grammar_v0.4.md` is tracked (added by `21e62d3d`), item 2's
`paths` at `build_manifest.py:78-98` is a hand-written list naming only
v0.1/v0.2/v0.3, the module contains no glob, and `build()` only ever walked
declared paths — `absent` records declared-but-missing and never
present-but-undeclared. **Zero occurrences** of v0.4 in the committed manifest,
exit code 0, no warning. It failed **open**, which for a document whose job is
"these exact bytes are what the campaign ran against" is the one direction it
must not fail in. The file it omitted carries the **refusal of GAP R2-2**, a
contract clause.

Fixed, and the class closed for that item — but **not with a glob**. A glob over
`CONTRACTS/dsl_grammar_v*.md` would admit a future v0.5 into the freeze list
with nobody ruling on it, and this module's own docstring says a judgement is
exactly the thing that must not be regenerated. Instead item 2 gains a `family`
regex, `build()` records tracked-but-undeclared siblings as `unlisted`, and
`verdict.unlisted_paths` publishes them. Because `--verify` compares a
regeneration against the committed file, a v0.5 landing is **drift with a
filename in it** rather than silence. Four controls in `--selftest` (now 12/12),
including the one that matters: the regex is shown to match all four real
grammar files, so an empty `unlisted` means *declared*, not *unmatched*.

**Gap left open, deliberately, and filed rather than done:** only item 2
declares a family. Every other single-file path in `ITEMS`/`EXTRA` is still
fail-open on its siblings, and the audit is worse than the v0.4 instance —
**7 of 10 tracked `CONTRACTS/` files are unhashed**, including
`candidates_schema.md`, which `CLAUDE.md` calls "the only candidates contract in
force"; and `proxy/spend_policy.json`, `monitor/spec.py` and
`monitor/money.json` are unhashed although item 12 *is* the money item. Adding a
file to the freeze list is a ruling about what the release publishes. S50's
warrant was to make the gate honest, not to widen what it covers. Filed as its
own board item.

---

## [15b] · the balance did move — and regeneration could never have made this green

The item is right that the balance moved and right that the fix is regeneration
to match the ledgers, not adjusting numbers. Both were done. But the stage had
been red **continuously since at least 2026-08-01**, and it would have gone red
again within minutes of any regeneration, because two of its compared inputs
were not facts about the tree.

### (a) The citation anchors — re-anchored by hand, which is the mechanism working

`CITED_LINES[0]`/`[1]` asserted the literal strings `"usd_ceiling": 214.9` and
`"action_ceiling": 24000` on lines 4 and 5 of `proxy/spend_policy.json`. Those
lines now read `700.0` and `40000`, changed by **`c42f5ad4`** (2026-08-02) —
the only commit ever to touch either value — through `spend_policy.json`'s own
`raising_it` clause, registered as `monitor/spec.py` p3-gate-exception **#15**
on the owner's instruction 額度限制全部放开. Line 6 still matches, so the
file's shape did not shift under the anchor; only the values moved.

**Regeneration alone could not clear this**: `check_citations()` reads a Python
constant, so a regenerated JSON would faithfully record `"state": "drifted"` and
`main()` would still return 1. The two tuples had to be edited by a human — and
that is exactly what the mechanism is for. The prose now carries the
distinction the re-anchor would otherwise have erased: **$214.90 was a
measurement** ($50 G1 + $164.90 stop-loss = INC-BA-003's worst-case combined
exposure); **$700.00 is a budget**, with no such derivation — the policy file's
own provenance says "It is a budget, not a bound". Crossing $214.90 means that
bound stops being a bound. §A-1 of `BUDGET_TABLE.md` now says so in a
superseding box, and §B records that **B = $60 was ruled under the old ceiling
and did not scale with it**.

### (b) The pool is untracked, live, and a fleet is appending to it

Measured during this ticket: `proxy/var/spend_gate.jsonl` went
**17592 → 17662 → 17677 → 17745 → 17768 → 17868 → 17946 → 17963 lines** in one
session, as the A26b legs spent. Every regeneration was stale before the gate
could run. `ci_merge` reads only the exit code, so nobody could distinguish
"red because somebody hand-edited the table" from "red because a leg spent
forty cents" — which is precisely the discrimination this stage exists to make.
**A gate whose steady state is red is not a strict gate; it is an unread one.**

The category error is the fix: a frozen artefact cannot pin live untracked
state *and* be reproducible. `build_manifest.py` already refuses that error in
the other direction ("an untracked input to a freeze manifest is itself a
finding"). So `--verify` now recomputes the pool **as of the `as_of_seq` the
committed table states**, and digests exactly those records.

What got **stricter**:

* `prefix_sha256` digests the included records, so **editing or deleting any
  historical line is caught**. The old whole-file `sha256` could not do this on
  a growing file — a retroactive edit hid inside a red that was already there
  for an innocent reason. Tamper-evidence went up, not down.
* A pool that **shrank** past `as_of_seq` fails: the prefix stops reproducing.
* Every tracked input — the policy, the citations, the arm ledgers, the price
  table — is still recomputed live and compared exactly. Nothing there was
  relaxed.

What it stops failing on: the pool having **grown**. That is not dropped.
Every run, green or red, now prints the as-of seq, the live seq, the record
delta and **the dollars spent since**. `--verify --frozen` restores the
all-or-nothing behaviour and is what the freeze itself must run — at the freeze
moment "the balance moved" *is* the invalidating event. Today 0 of 13
freeze-list items are ready, so there is no freeze for it to guard yet; wiring
it into the freeze ritual is filed as its own board item.

Six controls in `--self-test`, written against a synthetic pool whose bytes are
known. The one that kills the tautology is #5: *an uncapped read of a grown
pool must still differ from the reference*. Without it, controls 1–4 are
equally satisfied by a `prefix_sha256` that ignores its input entirely — which
is the shape of the defect M-1's inbox note reported for `u3.py`'s criterion (c)
(`_CONSTANT_BODIES` is a literal-token scan, so `(x == x)` passes a check whose
stated criterion is "not constant"). That note is about §9.2, a different gate,
and this ticket does not touch it; it is cited here because it is the reason
control #5 exists.

### (c) `policy.sha256` was a fact about which checkout ran the generator

Found while chasing a `sections that moved: policy` on a file nobody had
touched. `proxy/spend_policy.json` is **CRLF on disk in the main checkout and
LF in a fresh worktree**. `git status` calls neither modified, because
`proxy/.gitattributes` pins `*.json text eol=lf` and git compares the
normalised form — so the main checkout's copy is the stale one and the
worktree's is what every other checkout will produce. The raw-byte digest
therefore returned two values for one file.

`sha256_file` now digests LF-normalised bytes, which is what
`tools/check_locations.py:sha256` already concluded and documents for the same
reason. And `pool.abspath_is_main_checkout` — True in a worktree, False in the
main checkout, and *inside the compared object* — moved to `generated_from`,
next to `commit`/`branch`/`dirty`, which `--verify` already strips. Nothing is
lost: the guarantee it stood for ("these numbers came from the one true pool")
is enforced better by `prefix_sha256`, since a worktree-local pool produces a
different digest and reddens the gate, whereas the boolean only ever described
the search.

`check_checkout_independence.sh` in this directory is the proof rather than the
argument: it generates from both checkouts and asserts no checkout-dependent
section survives. Result: **none**, `policy.sha256` agrees.

> **Spun out as a finding for `proxy/`, not fixed here.** `proxy/spend_gate.py`
> stamps every `run_start` with its own `policy_sha256` over **raw** bytes. The
> live pool right now contains **two different `policy_sha256` values for the
> same policy content** — `d722c615…` (2 records, launched from the CRLF main
> checkout) and `2f22ba45…` (4 records, from a correct checkout). A later audit
> asking "which runs drew on the widened pool?" gets the wrong answer. Reported
> to `proxy/` by inbox note.

### The other finding: `programme_measured_usd` double-counts $129.03

`build()` claims "each dollar counted once … tracked-ledger totals plus the
pool campaigns that have no tracked ledger", but the implementation excludes
only three hard-coded `phase3-*` campaign names. Every `theoria-arm:` pool
campaign whose run directory *also* has a tracked `ledger.jsonl` is added
twice. Measured 2026-08-04: **$129.0326 across 10 campaigns**, which is
**byte-identical to `monitor/money.json`'s
`allocations.dev_pile_B.measured_usd`** — the money single-source-of-truth and
this file agree on the overlap, and this file then adds it twice.

It is **pre-existing** (the committed table double-counted $54.85; it grew by
exactly the $74.18 of ledgers that `445c647e`/`d10788f7` landed, because
landing a ledger converts a correctly-pool-only campaign into a double-counted
one). It **overstates** spend and understates headroom, so it is conservative
and did not manufacture the verdict flip. **Not fixed here**: correcting it
changes what a published money figure means by $129, which is an adjudication
and not a regeneration. Disclosed in the module docstring and filed.

---

## [18] · eleven dated exemptions, and the control the run half never had

All 11 violations are `run` scope; **zero** are `artefact` scope. Every one
landed 2026-08-01, on branches that merged at or after `aa2e2cc1` — the last
allowlist pass, also 2026-08-01 — which is why none was ever signed for. Each
entry names its landing commit and why the path cannot be scrubbed. The three
irreducible sources:

* **`ledger_abspath`** (`theoria-arm/harness/spend.py:160`) is absolute **by
  design**: `assert_one_true_pool` refuses any gate whose value differs, so
  ~50 worktrees cannot become ~50 pools each carrying the full ceiling, and
  `theoria-arm/tests/test_desk_gate.py:516` asserts `.worktrees` is absent from
  it. Relativising it would break the money single-truth mechanism.
* **`traceback`** fields are verbatim CPython output captured at
  `theoria-arm/world/adapt.py:53`, and they are embedded unchanged inside the
  `desk/call-*.md` prompts the model was actually shown. Editing them would
  claim the model saw text it did not.
* **captured console transcripts** (`GATES.txt`, `verify_out.txt`,
  `env_proxy.log`) — the checker's own guidance rules out rewriting these:
  "Deleting the pattern from a captured log is not one of the options: it
  falsifies a third party's output."

Two things the signatures disclose rather than paper over:

* **7 of the 23 files in `R1b-g50t-a` are a false positive.** The `posix home
  path` pattern fires on the playbook comment `#   up/home/undo from that
  cell.` — `up`, `home`, `undo` are ARC action names. The count 23 is what the
  checker sees today, not a claim that 23 files name a machine, and the
  exemption says so. Narrowing the regex is **not** done here: the pattern is
  load-bearing (5 genuine MSYS-style `/c/Users/user/…` findings that the
  Windows pattern misses), and a change to counts across other territories'
  runs is not this ticket's call. Filed.
* **`exam/u3_census.py:511` is still writing absolute paths.** `census.json`
  carries `root.as_posix()`, the one field `census()` does not pass through
  `u3.sanitize_paths`. New censuses will reproduce this. The two exemptions say
  explicitly that they cover the landed measurement only and are not a licence
  for the next one. Reported to `exam/`. Same for
  `theoria-arm/inner/transfer.py:223` (`source_books_dir`), which is cheaply
  relativisable.

### The negative control the run half never had

The item pointed at M-1's report of a one-token tautology and asked whether it
touches this gate. It does — not the same code, but the same shape, and worse:

Setting `RUN_PATTERN_NAMES = frozenset()` in memory — **deleting the run
detector outright** — turned **every test in `tools/tests/` green, including the
two that were red at the time**. A mutation that removes half the gate should
not repair its test suite. The cause: `test_an_unlisted_run_directory_is_red`
and `test_a_listed_run_directory_that_grew_is_red` hand-fabricate the finding
tuple and feed it to `adjudicate()`, testing the bookkeeping and never the
predicate; and `_hits()` defaults to `scope="artefact"`, so `_patterns("run")`
— a different frozenset carrying 1966 of the 1982 findings — was exercised by
nothing. The file's own docstring demands "before the gate is trusted, it must
have been *seen red*", honoured for artefacts and silently not for runs.

Two tests added, one against **real bytes**
(`445c647e:theoria-arm/runs/…R1b-sk48-b/run.json`, whose `ledger_abspath` is
absolute by design and so is a stable specimen), one asserting the run pattern
set is non-empty (it does not skip when the blob is unreachable). **Verified:
the mutant now fails both.** Before: `19 passed`. With the mutant:
`2 failed, 17 passed`.

**Not done, and filed with evidence**: a run exemption's `reason` is never
read, never validated, and may be **absent entirely** — an entry with no
`reason` key, an empty one, `"dated": "yes"`, or `"files": 999999` all pass the
schema test and turn the gate green. The artefact side enforces
`len(reason) > 40`; the run side asserts nothing. Mirroring the assertion would
immediately red **69 existing entries** whose reason is the 28-character
`"write-once provenance record"`. That is arguably the right outcome and it is
certainly not S50's unilateral call. Also latent: `run_dir()` truncates to the
first segment under `runs/`, so one entry for the grouping directory
`theoria-arm/runs/_rounds` would swallow every round ever placed under it —
untracked today, and `theoria-arm/runs/_rounds/20260802T122531Z-A26/` is
sitting in the main checkout's working tree right now.

---

## Verification

```
bash freeze/verify.sh          82 PASS, 0 FAIL   (run three times, green each time)
python freeze/build_manifest.py --selftest       12/12
python freeze/build_budget_table.py --self-test  all controls PASS (6 new)
python tools/check_locations.py                  clean
python -m pytest tools/tests -q                  19 passed
bash .../check_checkout_independence.sh          no checkout-dependent sections
mutant RUN_PATTERN_NAMES=frozenset()             2 failed, 17 passed  (was: all green)
```

Zero API spend. Entirely offline. Sealed pile untouched: no game id was read,
named or reasoned about, and nothing in this ticket goes near
`environment_files/` or the swarm runner.

## What the next person should know

1. **Regenerate `freeze/BUDGET_TABLE.json` from any checkout now** — that was
   not true this morning. If it ever again reports `sections that moved:
   policy` for a file nobody edited, suspect a raw-byte digest and CRLF before
   suspecting an edit.
2. **`[15b]` green does not mean the balance is current.** It means the table
   is a truthful record up to its stated `as_of_seq`. The delta is printed on
   every run; read it.
3. **The freeze itself must run `--verify --frozen`.** Nothing calls it yet.
