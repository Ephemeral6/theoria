# R4 — `needs_human` had no exit

RES-4, 2026-07-29, branch `agent/r4-ruling-path`, base `e8d95c53`.
Offline: zero API calls, $0.00, zero sealed-pile contact.

**Branched from `agent/r3-release-classifier-defaults`, not from master.** R4
builds directly on `classify()` as R3 leaves it and R3 is not merged yet. Said
here rather than left for a reader of the graph to work out.

## The finding, which came from an adversarial review of R3

R3 made the release classifier abstain instead of guessing, and `verify.sh` went
red on three files. Correct — before it, all three shipped as
`releasable-flagged` on the authority of the characters after the last dot in
their names.

The reviewer then found the thing R3 had not thought about: **`release/` has no
adjudication path at all.** Grep `checklist.py`, `bundle.py`, every document —
nothing anywhere lets a person *rule* on a `?` row. So a `?` can be removed only
by editing code, and since the rule that produces it ("bytes that do not decode
as UTF-8 are undetermined") is true of every binary figure that renders a
per-game label, the gate is red **forever** for a whole file class.

A gate that is permanently red gets switched off, and the true reds go with it.
That is the failure this item prevents. It is not a hypothetical: `check_redlines`
already carries a comment recording that its own first proposed fix was going to
be an allow-list.

## What was built

`release/RULINGS.jsonl` — append-only, one JSON object per line, all six fields
required: `path`, `sha256`, `class`, `ruled_by`, `utc`, `reason`.

Four properties, and the refusals are more of the design than the acceptance:

1. **Keyed on the content hash, not the path.** A ruling says *"I looked at
   these bytes."* Keyed on the path, the same ruling would silently carry over
   to whatever the file becomes next — a figure regenerated from different data,
   a log overwritten by a later run — and a person's signature would end up
   attached to bytes they never saw. That is this lane's standing shape: an
   assurance that outlives the thing it was about.
2. **A ruling settles a `?` and nothing else.** If it could reach a decided row
   it would be an override, and a signed override beside a classifier makes the
   classifier's answer optional — worse than the permissive defaults R3 removed,
   because it would look deliberate. This is also what makes class `D`
   structurally unreachable: `D` is decided, so no ruling ever meets it.
   `RULEABLE_CLASSES` is `("A", "B", "C")` and the loader refuses a line ruling
   `D` or `?` outright, so the property holds by two independent mechanisms.
3. **A stale ruling is reported, not dropped.** Path matches, hash does not →
   the ruling does not apply and `main()` prints `STALE RULING`, naming the old
   hash and the new one. *"Nobody has ruled on this"* and *"somebody ruled on the
   version before this one"* are different situations, and only the second is one
   signature away from resolved.
4. **The evidence is appended, never replaced.** A ruled row keeps the machine's
   original sentence and gains `-- RULED class C by <name> at <utc>: <reason>
   (the machine did not determine this; a human did, against sha256 <prefix>)`,
   plus `ruled_by` / `ruled_utc` fields. A row reading only *"ruled class C by
   X"* would hide that no parser ever opened the file, and the next reader would
   not know a signature was standing in for a measurement. For the same reason
   `main()` prints a `note` naming every ruled file **before** the distribution:
   a class-C count containing ruled rows is not the same fact as one the
   classifier reached alone.

A malformed rulings file **raises** rather than skipping the bad line. A ruling
quietly ignored is indistinguishable from one never written, and the entire
point of the file is that somebody's name is on a decision.

## Nothing is signed, and that is the deliverable

`release/RULINGS.jsonl` ships with comments and **zero rulings**.
`release/verify.sh` stays **RED**.

The work order asked for a ruling on each of the three rows *or* an argument
that they should not be ruled. The argument: a ruling is a signature, and
`monitor/CHARTER.md` routes anything requiring human identity to `needs_human`.
The agent that built the adjudication path is the last party who should sign the
rulings that turn its own gate green — that is the shape where a gate gets
cleared by whoever wants it clear, which is what this lane exists to catch.

So the *work* of the ruling is done and the *signing* is not.
`release/RULINGS_PROPOSED.md` carries, for each of the three: the machine's exact
reason for abstaining, the evidence, the ready-to-append JSON line with
`ruled_by` blank, and — deliberately — **the argument against signing it**.

## The evidence, recomputed rather than inherited

The adversarial review reported the PDF/SVG relationship. It was re-derived here
from the bytes rather than taken on trust:

| file | sha256 | bytes | ids present |
|---|---|---:|---:|
| `figures/paper/dark/figure6_bill_shape.pdf` | `ca805a75bbd858d0…` | 257,076 | 4 |
| `figures/paper/light/figure6_bill_shape.pdf` | `d4397dd8307a2647…` | 257,901 | 4 |
| `figures/paper/dark/figure6_bill_shape.svg` | `95ff2f6c760ffbf1…` | 810,872 | 4 |
| `figures/paper/dark/figure6_bill_shape.png` | `6c218b1d8b5b8ea8…` | 1,767,158 | **0** |
| `theoria-arm/…/pytest-baseline.txt` | `764359440f0d4444…` | 3,051 | 1 |

In the PDF the id is a text-drawing operator at a plot coordinate —

```
1 643.1695026034 818.6115705759 cm
BT
/F1 6.5 Tf
0 0 Td
[ (ar25-0c556536) ] TJ
ET
```

— an **axis tick label**. In the `.svg` twin, which the machine parses and
classifies **C** on its own, the same id sits in `<g id="text_41"><!--
ar25-0c556536 -->`. The `.png` twin is class **A** only because rasterising
destroyed the text: zero ids are present in its bytes at all. Same figure, three
containers, three classes — which is the incoherence that raised this item.

In the pytest log the single dev-pile id is a source constant inside captured
output (`game = "g50t-5849a774"`), and the file's entire defect is three mojibake
byte pairs; 45 non-empty lines, **none** beginning with `{`.

All ids involved are **development pile**. No red line is implicated by any of
the three; what is undetermined is a licence class.

## Two recommendations that are not changes

* **The pytest log should be repaired, not ruled.** It is three byte pairs away
  from an ordinary machine verdict, and a `?` that can be removed by fixing the
  file is better resolved that way than by a signature — the signature has to be
  re-made every time the bytes change, and the repair does not. `theoria-arm` is
  another territory's, so this is written down rather than done.
* **Ruling the PDFs from their SVG twin is provenance reasoning**, and
  `enumerate.py` permits that in exactly one place, with a comment saying so
  (`UPSTREAM_PAYLOAD_PREFIX`). Extending it is a judgement, not a derivation:
  nothing *in* the PDF proves it came from the same pipeline. A signer who does
  not accept that link should not reach for a ruling — the honest alternatives
  are to stop tracking a binary the release cannot read, or to regenerate it in
  a readable form. That argument is in `RULINGS_PROPOSED.md` beside the proposal
  it undercuts, on purpose.

## Measured end to end, then unsigned again

`verify.with-demo-rulings.txt` in this directory is a **demonstration, not a
signature**: three rulings were appended with `ruled_by:
"DEMONSTRATION-NOT-A-SIGNATURE"`, `verify.sh` was run, and the file was restored
from git. The result:

```
== every tracked file is classified
  note 3 file(s) carry a human ruling where this enumerator abstained:
-- ok
VERIFY: green
```

`verify.unsigned.txt` is the state that actually ships: **`VERIFY: RED`**, the
same three `?` rows, four of five sections green. Both are archived so the claim
"signing three lines clears it" is checkable rather than asserted.

## What an adversarial pass on this feature found, and what came of it

The tests were written by an agent told to attack the implementation, not to
document it. Four criticisms, all fair:

1. **An unreadable file could never be ruled on, and nothing said so.** A file
   `read_bytes` cannot open gets `sha256: None`, so `_apply_ruling` looks up
   `(path, None)` — which no valid ruling can key. That is the *right* answer
   (nobody can sign for bytes they were unable to read), but the row was
   indistinguishable from a ruleable one, and the next person to write a ruling
   for it would have watched it silently do nothing. **The row now says so**, in
   the evidence, and a ruling written for it anyway is reported as a miss.
2. **`stale_rulings` was silent about a ruling whose path is gone** — the same
   situation it exists for, one step further along.
3. **A typo'd path was inert and unreported.** A mistyped *hash* was caught
   (path matches, hash differs); a mistyped *path* matched nothing, was reported
   nowhere, and left the gate red for a reason nobody was told. **2 and 3 are
   now one report**: `stale_rulings` names every ruling that matched nothing and
   which of the three ways it missed. A signature that fails to land has to make
   a noise — that is the argument for a rulings file over an allow-list, and a
   silent miss gives it up.
4. **`load_rulings` called the builtin `enumerate()` from inside a module named
   `enumerate`.** It resolves today only because the module never binds its own
   name. Bound once as `_numbered`, with a test that shadows `enum.enumerate`
   and asserts the error still names the right line — the line number is the
   only thing telling an operator which line of a signed file is malformed.

**96 tests pass** in `release/tests`, from 71 at R3's delivery. Every one of the
21 the adversary wrote was measured by mutating the specific line it claims to
pin and confirming the test goes red; no mutation passed silently.

## One incident during this run, recorded because it nearly cost work

An agent measuring a negative control ran `git stash push release/enumerate.py`
in this worktree at the moment a concurrent process committed the R4 work. The
stash had nothing to save and created no entry, so the following `git stash pop`
popped an **unrelated autostash** belonging to another process, spraying conflict
markers across `monitor/` and `ablation-arm/`. The pop conflicted, so the stash
entry was retained and nothing was lost; the worktree was reset and every
remaining measurement was taken by in-place mutation instead.

The lesson is not "do not use stash". It is that **`git stash push <path>` with
no changes to save is silently a no-op, and the paired `pop` then acts on
somebody else's entry** — a two-command idiom that is safe alone and unsafe in a
tree several processes are working in. In-place mutation is the better tool for
measuring a negative control anyway: the failure is attributable to a specific
line rather than to a diff.
