# S23-unreadable-is-not-clean · run state

Worker `W-1642`, branch `agent/s23-unreadable-is-not-clean`, base `bac8282`.
Written as the work happened.

## Step 0 — a takeover, which is why there are two run directories

This item had been claimed before. `.worktrees/s23-unreadable-is-not-clean/`
already existed, on `29f41ea`, with uncommitted work by `W-1631` and an earlier
run directory `20260728T212958Z-S23/`. That work is preserved verbatim as commit
`c516409` before anything was built on it, so the takeover is auditable.

It was **not** a working state, and one part of it was worse than incomplete:

| left behind | state |
|---|---|
| `read_bytes` / `read_json_records` / `json_shaped` in `check_redlines.py` | sound, and kept |
| `check_credential` / `check_sealed` widened to a three-value return | done |
| `main()` and the body of `check_sealed` | never updated — the module raised `ValueError: too many values to unpack` on every invocation |
| `_records_pairing_sealed_with_payload` callers | still `if bad:` on what is now a tuple, which is always truthy |
| `json_shaped` | defined, never called |
| `arc-recon/contamination.py` | **a 28-line docstring describing a `gate()` function that was never written**, and `main()` still ending `return 0 if check["matches"] else 1` |
| `release/tests/` | a `conftest.py` and no tests |
| `runs/…212958Z-S23/before/` | three green captures on a clean tree |

The docstring is the part worth recording. It described the fix in the present
tense — including a `scan_surface_self_discovered` field — beside code that did
none of it. That is the same failure as the bug being fixed, one level up: a
claim of a check that does not exist. It was rewritten to match what the code
now actually does, and `gate()` was written.

W-1631's `before/` captures were correct about one thing this run agrees with
and builds on: **the defect is latent, not firing.** Every tracked file in this
repository currently decodes, so three green captures on a clean tree are three
green captures. Only a planted negative sample shows anything, which is what
`replicate.py` below does.

## Step 1 — the census, before touching anything

Three parallel subagents: one census of the fail-open shape across `release/`
and `arc-recon/`, one map of `contamination.py`'s verdict surfaces, one map of
the existing test surface. Findings that changed the plan:

* The two named sites were **not the only two**. `enumerate.py:258-266` had the
  same disease twice, and worse: `continue` on an unhashable file removed the
  row from a manifest whose docstring promises one row per tracked file, and
  `blob = b""` classified an unreadable file **A / releasable** on the evidence
  string "no ARC game id appears in this file" — a positive claim about bytes
  nobody read.
* `checklist.py:140` tested only `("B", "D")`, so class `?` / `needs_human` fell
  through to **PRESENT**. Latent, because the enumerator could not yet emit `?`
  for an unreadable file — *fixing enumerate.py makes it live*, so it could not
  be left.
* `release` was one of four **UNGATED** territories in `monitor/gates.py`. The
  territory holding the credential and sealed-pile red lines had no gate of its
  own, and `ci_merge.py` had been merging it with nothing checking it.
* `contamination.py`'s most severe possible finding — a sealed game ADDRESSED in
  a ledger — exited 0. So did a **missing** ledger, which read as
  `0 calls, sealed ADDRESSED: NONE`, and a **missing** contamination log, which
  produced a full clean claim set over 21 games from a file that is not there.

## Step 2 — the fix

Converged on the conservative half, as the work order requires, and made both
files reference one implementation rather than two:

* `read_bytes` → `(blob, None)` or `(None, reason)`, never `(b"", reason)`.
* `read_json_records` → `(records, None)` or `(None, reason)`, never
  `([], reason)`. Records are materialised eagerly, so a malformed line 5000 no
  longer discards a violation found at line 1.
* `json_shaped` decides JSON-ness from the name **and** the bytes, so a
  frame-bearing stream named `.log` is parsed instead of being assumed innocent.
* `enumerate.py` calls those same functions; `test_both_scripts_read_through_the_same_decision`
  asserts the sharing, because that is the property that decays silently.
* `contamination.gate()` — one function behind both the printed table and the
  exit code. Five conditions, three of them about not having looked.

**One thing deliberately not done.** `needs_human` exits `2` from
`check_redlines.main` where a violation exits `1`. It is not a softer verdict —
it blocks `enumerate.py` from writing a manifest exactly as hard — but a caller
can now distinguish "we found something" from "we could not look" without
parsing prose, which is the distinction `return []` erased.

**One thing deliberately kept green.** `quarantined` and
`retained_with_sensitivity_analysis` are non-empty on this tree today and must
not turn the gate red: they are settled disclosures, the system working. A gate
that fires on honesty is a gate somebody switches off.
`test_a_quarantined_game_does_not_turn_the_gate_red` pins that.

## Step 3 — the negative samples

Both halves have negative **and** positive controls; a gate that has never been
seen to go red proves nothing, and one that goes red at everything proves less.

`release/tests/test_unreadable_is_not_clean.py` (27 tests) builds a throwaway
git repository under `tmp_path` for each case, so the real `git ls-files` path
is exercised rather than a hand-supplied list. Nothing undecodable is planted in
this repository: the alternative is committing undecodable bytes into a tree
whose entire purpose is to be published, and `MANIFEST.jsonl` would carry it
forever.

The two ways a file goes unread are not the same way, and the tests separate
them — `read_bytes` opens `"rb"`, so it never sees a decode error. An
*undecodable* file only reaches a verdict through `read_json_records`, and only
for a file that also names a sealed game. That is exactly line 207's path, and
exactly the file where the confusion is most expensive.

`arc-recon/test_contamination_gate.py` (20 tests) replays the real contamination
log into `tmp_path` and appends one planted row, so a plant is judged against the
real register rather than a universe built to contain it. Nothing writes to
`arc-recon/data/`; `main()` is called without `--json`.

## Step 4 — before and after, on the same input

`replicate.py` in this directory. For each scenario it obtains **the pre-fix copy
of the module** via `git show bac8282:<path>`, writes it beside its real sibling
(both modules resolve `REPO_ROOT`/`DATA_DIR` from `__file__`, so a
temp-directory copy would take a different branch), and runs old and new over
identical planted input. The ref is a hash and not `master` for a reason given
in Step 7.

| check | planted input | before | after |
|---|---|---|---|
| `check_redlines.main --mode verify` | a `.jsonl` naming a sealed game with invalid UTF-8, plus a tracked file deleted from the working tree | **exit 0**, "Both red lines clear. A release manifest may be generated from this tree." | **exit 2**, two NEEDS HUMAN lines naming both files |
| `contamination.main` | the real log plus one record with `claims: "quarantined"` (a typo, in no settled bucket), and a `DATA_DIR` with no ledger in it | **exit 0** | **exit 1**, GATE: RED on two conditions |

The `before` capture of `contamination` is the one to read: it **prints**
`NEEDS ADJUDICATION (excluded from 'clean'): bp35-0a0ad940` and then exits 0 on
the same page. The human reading the table was told; the machine holding the
gate was not.

`replicate.py` asserts the before/after verdicts rather than only recording
them, and `release/verify.sh` runs it — a claim about what old code did decays
into a story if nothing re-checks it.

## Step 5 — the gate

`release/verify.sh`, new. Negative controls run **first**: every other step in it
reports that nothing is wrong, and a check that has never failed cannot
distinguish "nothing is wrong" from "nothing is being checked". `monitor/gates.py`
now reports 9 verify-gated territories and 4 ungated, down from 5.

Two entry points changed exit behaviour, which anything scripting them will see:

* `check_redlines.py` gained exit `2`.
* `checklist.py` returns 1 when any item is UNDETERMINED (0 on this tree).

`release/CHECKLIST.md` is unchanged on this tree — the tally line gained an
`undetermined` field, and it is regenerated only by an explicit non-dry run.

## Step 6 — the adversarial pass, which turned over nine things

A subagent was given the finished branch and asked to **refute** it, not to
review it. It could not refute the headline claim, and it checked that the hard
way: it mutated the source four ways — `read_json_records` back to `([], reason)`,
`read_bytes` back to `(b"", reason)` with the old `len(paths)` note and
suffix-only sniffing, `status_of` back to no `?` branch, and `gate()` stripped
back to the piles hash — and confirmed each mutation kills the tests that claim
it. It also confirmed no caller elsewhere in the repository breaks on the
widened three-value returns.

It then turned over **nine defects, five of them introduced by this branch.**
All are fixed, and the two worst are worth writing down because both are this
work order's own disease reappearing inside its own fix:

* **`size: None` crashed the very refusal this branch added.** `build()` emitted
  it for an unreadable file; both consumers sum that field; `checklist.report`
  died on a `TypeError` *before* it could return UNDETERMINED. So the branch
  replaced a wrong answer with a traceback. The test that covered the verdict
  hand-built a row shape `build()` never produces — **a negative control aimed
  slightly to the left of the thing it was guarding**, which is why 18 green
  tests could not see it. The test now drives the real row through both readers.
* **`enumerate.main` printed the `?` count and returned 0**, while
  `release/verify.sh` asserted the opposite in a comment I had written two hours
  earlier. Reachable without any unreadable file at all: an unparseable `.json`
  naming a *dev-pile* id is invisible to `check_sealed`, which scans only sealed
  ids, so nothing upstream aborts.

Three more of mine: `checklist` inspected only rows some pattern matched, so an
unclassified file no item covers left it green; `json_shaped`'s first-byte test
was defeated by a UTF-8 BOM or one comment line; and `CHECKLIST.md` was left
stale by the tally field I added, so the generator no longer matched its own
artefact.

Three pre-existing, same disease: an unrecognised `level` fails open through
`order.get(level, 0)` → `never_audited` (the module fixed this exact shape once
for `claims`, and it survived in the field beside it); `--json` wrote
`claim_set.json` *before* the gate ran, so `verify.sh`'s own step overwrote the
tracked artefact with a reassuring fabrication and only then returned 1; and both
red lines are UTF-8 byte searches, so a UTF-16 file opens, counts as scanned, and
can never match — which this branch made worse before better by adding an
explicit "N of N scanned" claim on top of it.

And two of my assertions could not fail: `scan_surface_self_discovered is False`
read back a literal, and `enum.redlines is redlines` holds because the import is
at module scope. Both now assert what they were standing in for.

**The lesson worth keeping.** Every one of the five I introduced was in the
*downstream* of the fix, not the fix. The readers were right the first time; what
was wrong was what happened to their new third answer once it left them. A change
that adds a verdict has to be chased to every consumer of that verdict, and
"tests pass" does not do the chasing — three of the five were covered by tests
that were aimed just beside them.

## Gaps — stated, not hidden

1. **`arc-recon/tools/ledger_invariants.py` has the same disease and was not
   fixed here.** `_load_secret` catches bare `Exception` and returns `None`, so
   tier 2 — the only check that compares against the live key — does not run,
   while `scan()` still computes `"clean": True` and `main()` returns 0. It is
   out of this work order's scope; reported to monitor rather than changed
   unasked.
2. **`contamination.py`'s scan surface is still hand-written.** `OTHER_LEDGERS`
   names two files and the repository holds more ledger-shaped files than that.
   Not made self-discovering — a separate work order — but promoted from a prose
   caveat to `gate()["scan_surface_self_discovered"] = False`, printed on every
   green run. It does **not** turn the gate red: a permanently red gate is one
   nobody looks at.
3. **`verify-lab/negctl/tests/test_probe.py:320`** swallows
   `(OSError, SyntaxError, UnicodeDecodeError)` while walking the real tree, in
   the negative-control territory's own tests. Probably harmless, not mine to
   judge, reported.
4. **`checklist.py` had never parsed** — line 45 held a literal newline inside a
   string. Fixed here, because leaving a `SyntaxError` in a file this change
   edits is indefensible; but it means `release/CHECKLIST.md` was generated by
   some earlier working copy and nobody has run that script since.
5. The credential half of `check_redlines` still reports **per-file** skips only
   as `needs_human`; it does not distinguish a file that is unreadable from one
   that is absent from the working tree. Both block, so nothing passes wrongly.
6. **`release/verify.sh` step 4 quotes a manifest step 3 did not produce.**
   `checklist.py` reads whatever `release/MANIFEST.jsonl` is on disk, while
   `enumerate.py --dry-run` writes nothing, so the checklist step can be
   answering about an older tree. The composite still catches a newly unreadable
   file — step 3 exits non-zero first — but the two steps are not looking at the
   same thing, and the step's own title implies they are.
7. **`piles.json` is read by an unguarded `open` in three files**
   (`check_redlines`, `enumerate`, `contamination`), and `checklist.load()`
   parses `MANIFEST.jsonl` bare. The cut file being unreadable is arguably the
   most consequential instance of this item's subject in the repository, and all
   of them answer it with a traceback. Left alone on purpose: a traceback exits
   non-zero and is therefore not the defect class here — "could not check"
   reported as "clean" — but it is the obvious next work order.
8. `main()` in `contamination.py` computes `claim_set()` for the table and
   `gate()` recomputes it. They agree because the files are read twice with no
   write in between, so "the table and the exit code cannot disagree" is true by
   recomputation rather than by construction.

## Step 7 — a second reviewer, on a different question

The adversarial pass above asked "is this broken". A second subagent was asked
the different question "was the work order actually satisfied", requirement by
requirement. It graded two of four **PARTIALLY MET** and found seven gaps the
delivery had not admitted. The important ones:

* **`replicate.py` had a fuse in it.** `BASE_REF` defaulted to `master`. The
  moment this branch lands, `git show master:release/check_redlines.py` returns
  the *fixed* file, "before" stops reporting clean, the assertion fires, and
  `release/verify.sh` — which runs this script on every green run — is
  permanently RED for a reason that has nothing to do with the tree. Worse, the
  captures were written *before* the assertion, so the first post-merge run
  would have overwritten `before/*.txt` with after-content on its way to
  failing: the gate destroying the archive it exists to protect. Now pinned to
  the hash `bac8282`, and unexpected output goes to `unexpected/` while the
  archive is left alone. Both halves are demonstrated by running the script with
  `S23_BASE_REF=HEAD`.
* **The reader I unified had split again inside `contamination.py`.**
  `register_coverage()` and `entries()` were two loops over the same file in the
  same module, each with its own `open`, its own exception tuple and its own
  idea of a usable line — the exact arrangement this work order forbids,
  reintroduced by the fix for it. One read now, two views of the result.
* **`release/verify.sh` ran the credential red line in the one mode that can
  skip itself and still exit 0.** It passed `--mode verify` unconditionally, so
  on any checkout without a credential the new release gate reported green
  having not run half of what it gates — this work order's own sentence, turned
  on its own gate. The mode is now chosen by asking `load_api_key()` whether it
  returns, and the fallback is announced in five loud lines rather than
  inferred. (The first version of that probe tested `[ -f ../.env ]`, which is
  wrong inside a worktree — `client.py` resolves the main checkout's `.env`, so
  the probe failed on the one machine where the key is definitely present and
  silently chose the lenient mode. Same shape again, three levels down.)
* **`MANIFEST.json` was stale**: written mid-run, and three later commits changed
  files it hashed. **And its zero-contact sentence was false as worded** — the
  archived captures do contain sealed ids, because they are the stdout of checks
  whose job is to name the ids they keep out. That is a mention and not
  material, so the constraint held; the claim did not. Both corrected, and the
  code/output distinction is now drawn explicitly rather than elided.
* **Requirement 4 had a `before/` with no `after/`** for the full-tree run. The
  pre-fix full-tree capture in the earlier run directory was taken at a
  different base over 2817 files and is comparable to nothing now. `replicate.py`
  gained a third scenario that runs *both* versions over the real tree in one
  run: both exit 0 over the same 3069 files, which is the other half of the
  claim — the stricter check does not redden a healthy tree.

Two of its findings I did not act on, deliberately:

* `piles.json` is read by an unguarded `open` in three files, and
  `checklist.load()` parses `MANIFEST.jsonl` bare. These raise rather than
  returning a verdict — a traceback is a loud non-zero exit, which is not the
  defect class this item is about ("no finding" reported as clean). Worth doing,
  not worth doing under this item's name.
* `verify.sh` step 4 grades `checklist.py` against whatever `MANIFEST.jsonl` is
  on disk, while step 3 runs `enumerate.py --dry-run` and writes nothing. The
  composite still catches a newly unreadable file, because step 3 exits non-zero
  first — but the checklist step is quoting a manifest that may predate the tree.
  Recorded as gap 6 below rather than papered over.

## Ledger

* Zero API calls. Zero sealed-pile contact. Sealed ids are read from
  `piles.json` at runtime and are not hardcoded in any source or test added
  here; they **do** appear in the archived run captures, which are the verbatim
  stdout of checks whose job is to name them. Mention, not material — see
  `MANIFEST.json`'s `sealed_pile_contact` block, which states this precisely
  after an earlier version of it stated something simpler and untrue.
* `bash release/verify.sh` → VERIFY: green (5 steps, `--mode generate`).
* `bash arc-recon/verify.sh` → VERIFY: green.
* `cd arc-recon && python -m pytest -q` → 131 passed.
* `cd release && python -m pytest -q` → 27 passed.
