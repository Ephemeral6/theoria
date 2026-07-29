## 8 · The exam — four papers, one sat, and a check that did nothing

The battery of §7 reads capability off trajectories that already exist. The exam
asks the complementary question: hand a subject a sheet and mark it. This section
reports the instrument, the one paper that has actually been sat, and — at
greater length, because it is the more useful result — the ways the instrument
was caught not working.

### 8.1 Four papers

`exam/model.py` freezes four question types. They are not four framings of one
question; each asks something a different failure would break.

| type | asks | items | points | implementation |
|---|---|---|---|---|
| **held-out** | given a (state, action) the evidence never contained, produce the exact next frame | 80 | 80 | `exam/papers/heldout.py` |
| **handover** | read a manual (and, at tier 2, a playbook) and answer about a world you have not seen | 29 | 46 | `exam/papers/handover.py` |
| **adaptation** | one rule has changed; detect it, describe it, bound the collateral, repair the manual | 60 | 144 | `exam/papers/adaptation.py` |
| **verdict** | is this configuration solvable, and why | 17 | 34 | `exam/papers/verdict.py` |

Two design choices are load-bearing. The held-out paper carries a **replay
control** drawn from the evidence set with identical class quotas, so the
`replay`/`heldout` tag itself carries no answer information. And the verdict
paper is one type spanning three item classes — 5 small unsolvable, 4 large
unsolvable, 8 solvable-hard (`exam/artifacts/leakage.json`) — not three separate
papers.

Marking is deliberately dumb. `exam/grading/mark.py` looks each item's rubric up
by id and hands it exactly `(answer, truth, item)`; a rubric never learns who it
is marking, because "a rubric that can see who it is marking is a rubric that can
flatter". Partial credit differs by type and is stated rather than assumed:
held-out and handover are all-or-nothing, adaptation is the only type with graded
fractions, and verdict splits each item half for the answer and half for the
reason — where a machine-checked certificate earns the full reason half, a
credible exhaustive search earns 40 % of it, and an *invalid* certificate
short-circuits to zero with no fallback.

The held-out rubric's refusal of per-cell credit is worth quoting, because it is
the kind of scoring choice that silently manufactures a result
(`exam/grading/rubrics_heldout.py`):

> on a 7x7 A0 board a typical transition changes two cells, so an examinee that
> returns the input frame unchanged already scores 47/49 = 96 % under a
> cells-correct rubric

**Sensitivity and specificity are computed by one function or not at all.**
`mark.py`'s `confusion()` returns both, each `None` when its denominator is empty,
with abstentions excluded from both and reported separately. The docstring gives
the reason, and it is the framework's own:

> a framework that answers "unsolvable" to everything has perfect sensitivity and
> is worthless. Both numbers, always, or neither.

### 8.2 The marker is calibrated; three of the four papers have never been sat

Before any real submission is marked, four synthetic subjects sit every paper —
an **oracle**, a **null**, a **memoriser** and a **bluffer** — against bands
registered in advance (`exam/grading/calibration.py`). `assert_calibrated()`
raises rather than warns, because "an uncalibrated marker's output is not a
low-confidence result, it is not a result".

It calibrates. The oracle scores exactly 1.000 and the null exactly 0.000 on all
four papers (`exam/artifacts/calibration.json`), and the interesting numbers are
the middle two, which catch things a band cannot express:

* the held-out **memoriser** scores 1.00 on the replay half and 0.15 on the
  held-out half — a gap of 0.85 — and on the over-sampled `blocked_crossing`
  class it goes 5/5 to 0/5;
* the verdict **bluffer** posts sensitivity 1.0 with specificity 0.0, which is
  exactly the degenerate strategy the paired metric exists to expose;
* the adaptation **memoriser** trips a `silently_wrong` counter twice.

One pre-registered band failed on first contact — the held-out bluffer scored
0.45 against a band ending at 0.35 — and it was **replaced rather than widened**,
by two mix-invariant checks, with the original reasoning preserved verbatim in
the code (`exam/DECISIONS.md` D-EX-010).

**Only one paper has been sat by a real subject.** Two fresh subagent readers,
given a bundle and a sheet and nothing else, each scored 46.0/46.0 on the
handover paper (`exam/artifacts/reports/p15-handover-a0.reader-tier{1,2}.report.json`).
Held-out, adaptation and verdict have never been answered by anything but the
four fakes; no answers or reports exist for them in the tree.

And the handover result is weaker than a perfect score sounds. The exam's own
status file says so before anyone else can:

> **The second number is not a measurement.** Both tiers hit the ceiling, so the
> paper had no room left to show a difference. A zero delta from a saturated
> sheet is uninformative about the value of the playbook, and reporting it as
> "the playbook is worth nothing" would be wrong.

> **Worse, the exam measures the wrong side of the pre-registered prediction.**
> `Theoria.md` 1.11 predicts that the manual-only reader *catches up*, and that
> the difference shows up as 多付的搜索成本 — a **cost**, not an accuracy.

The exam has no cost instrument, so the quantity the framework actually predicts
was not measured. We report the tier difference as **unmeasured**: the artefacts
record `tier2_minus_tier1: null`, and the 0.000 that could be computed from two
saturated scores is arithmetic, not an observation.

### 8.3 Leak protection, and the check that silently did nothing

The sheet and the key are separate objects by construction — `Item.paper` and
`Item.truth` are distinct fields, and `Paper.sheet()` is built from a method that
never receives a truth. On top of that, `exam/leakage.py` attacks each sheet five
ways: declared answer probes, structural key-disjointness, positional
independence, metadata independence, and an adversarial "cheater" subagent given
the sheet alone. `check_paper()` raises before the sheet is written, so a leaking
build fails closed. The archiver ships `key_sha256` and copies no truth file at
all, because an archive that ships the keys beside the sheets rebuilds the leak
inside the archive.

The static checks come back clean: **1,790 declared probes across the four
papers, 0 probe hits, 0 structural hits** (`exam/artifacts/leakage.json`).

That number is worth almost nothing on its own, and the directory says why.

**Two real leaks shipped, and the cheater found both.** The verdict paper's
`points` field encoded the answer — 3.0 for solvable, 2.0 for unsolvable — which
yielded **17 of 17 claims with no board reasoning at all**, measured rather than
estimated. And the held-out paper's world description published the dynamics in
prose, taking a reader from 47.5 % to essentially full marks. Both are fixed
(uniform point values; a world block that no longer states dynamics); both yields
were confirmed against the answer key before anything was changed
(`exam/DECISIONS.md` D-EX-011).

The reason the static checks missed them is the most transferable thing in this
section:

> `answer_labels` was an *optional* hook on each paper module. No module
> implemented it. So `check_paper` received `answer_of=None` and checks 3 and 4
> **silently did nothing on all four papers**. An optional check is a check that
> does not run, and it fails in the direction that looks like success.

The repair added label derivation from the key, and it did not fully close the
hole: `leakage.json` records `label_sets_checked: []` for the handover and
adaptation papers, so the positional and metadata checks still run on nothing for
two of the four. The directory's own reading is the one we adopt — "the static
checks are necessary and cheap, and the adversarial reader is the one that found
the leaks".

Both guards are tested by being made to fire, which is the only way to know a
guard exists: `exam/tests/test_core.py` opens with "a leak checker that cannot be
made to fire is not a leak checker", and includes a test pinning the exact
point-value leak that shipped. A separate module, `exam/guard.py`, handles two
different jobs — a network tripwire that replaces `socket.socket` for the
duration of a build, and a pile guard that reads the cut itself rather than a
copy and refuses any sealed game, any unregistered id, and a missing id. It is
honest about its own scope: "Not a sandbox — a process determined to get out can
get out. It is a tripwire for the accident that actually happens."

### 8.4 What the exam does not establish

* **Three of four papers have no real result.** Held-out, adaptation and verdict
  exist as machinery and as calibration runs. Nothing has sat them.
* **n = 1 per handover tier**, on a saturated sheet. Nothing here supports a
  variance claim about fresh readers, and nothing here prices a playbook.
* **No cross-type total should be quoted.** The four papers were built by four
  separate agents and their rubric weights are not calibrated against each other.
* **The calibration bands are outside the rubric digest.** The digest hashes the
  rubric modules' source text and travels onto every sheet and report; the bands
  live elsewhere, so a quiet widening there would not surface as a mismatch. One
  band has already been changed once — recorded, and correctly — which is exactly
  why the hole matters. Closing it is not done.
* **The cheater's numbers are prose, not artefacts.** The brief prompts are
  digested in the run manifest but the directory holding them is gitignored, and
  no cheater response or transcript is archived. We report those figures as
  findings the exam reports, not as results a reader can re-derive here.
* **Two cheater agents, four sheets, one pass** — and none of them has seen the
  fixed sheets. In the directory's own words: *the leaks that remain are the ones
  nobody has looked for yet.*

The exam's sharpest sentence is about itself, and it generalises past this
paper:

> An exam is two instruments in a trenchcoat: a question-setter and a marker.
> The question-setter can be checked by reading it. The marker cannot — a marking
> bug produces a plausible number, and a plausible number is indistinguishable
> from a result.

### 8.5 One thing the exam found in what it was examining

Building the handover bundle, and then independently both readers, caught a
defect in the artefact under examination: `a0-spike/theory/theory.dsl` ships
`invariant box_row_parity (Box.pos.row) mod 2 = 1` marked `[status: proven]`.
What the push rule conserves is the **parity** of the coordinate; the value `1`
is a fact about the particular board the evidence came from. The manual therefore
ships, marked proven, a sentence that is false on most boards of its own world —
including several on the exam sheet.

The bundles keep it verbatim and nothing was repaired, on the grounds that
repairing a deliverable in order to examine it would be examining a document
nobody shipped.
