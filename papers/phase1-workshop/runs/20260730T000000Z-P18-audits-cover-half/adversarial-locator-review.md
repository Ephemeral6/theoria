# Adversarial review — `locator_findings()` and its wiring

Target: the uncommitted working-tree change to `papers/phase1-workshop/verify_paper.py`
on `agent/p18-audits-cover-half-the-paper` (worktree
`.worktrees/p18-audits-cover-half-the-paper`). Reviewed 2026-07-30.

Nothing in the tree was edited by this review. Every reproduction below drives the
module in memory (`import verify_paper as V`) against a scratch sections directory
or a monkeypatched copy of a ruling table, so `git diff` is untouched.

## Baseline

```
cd papers/phase1-workshop && python verify_paper.py
  -> verify_paper: FAIL (1/7) -- E UNCITED
     415 claim blocks scanned across 12 body sections: 1 uncited, 9 ruled, 0 stale rulings
     UNCITED   08_exam.md:154 -- quantities [1] ...

cd papers/phase1-workshop && python -m pytest -q
  -> 244 passed, 1 xfailed
```

Note on concurrency: another session (RES-3) was writing this worktree *during*
this review. `verify_paper.py` was modified at 11:36 UTC and
`test_locator_gate.py` (11 tests, the negative control the brief said was missing)
appeared at 11:39 UTC. The pytest count was 233 passed / 1 xfailed before that file
landed and 244 / 1 after. Every finding below was re-confirmed against the file as
it stands after those edits.

`locator_findings()` currently reports **nothing** on either shipped table: all
nine `ADJUDICATED_UNCITED` entries and all four `ADJUDICATED_BARE` entries print as
`ruled`. Only 4 of 9 and 1 of 4 respectively even produce a parsed locator:

| table | key | parsed locator | paths named |
|---|---|---|---|
| UNCITED | `01_intro.md` | none | 1 |
| UNCITED | `03_a0.md` | `(2, line, back)` | 1 |
| UNCITED | `07_battery.md` δ | none | 2 |
| UNCITED | `07_battery.md` bill shape | `(1, block, back)` | 2 |
| UNCITED | `08_exam.md` 0.000 | `(2, block, back)` | 2 |
| UNCITED | `10_adjudication.md` 340/48 | `(1, block, back)` | 5 |
| UNCITED | `07_battery.md` moved twice | `(2, block, fwd)` | 2 |
| UNCITED | `09_preflight.md` | none | 0 |
| UNCITED | `10_adjudication.md` disputed | none | 0 |
| BARE | `02_framework.md` `playbook.dsl` | `(4, line, back)` | 2 |
| BARE | others (3) | none | — |

So the mechanism is live on 5 of 13 rulings. That is not itself a defect, but it
bounds how much the green means.

---

## Item 5 first: does it catch the thing it was written for?

**Yes, but by the weaker of its two branches.** Re-introducing the withdrawn
`08_exam.md` §8.4 entry verbatim:

```python
import verify_paper as V
key = ("08_exam.md", "**n = 1 per handover tier**, on a saturated")
V.ADJUDICATED_UNCITED[key] = (
    "Restates the sample size of the handover result cited one block above "
    "(one report per tier, both named there). This bullet list is the "
    "section's statement of what the exam does not establish.")
print(V.locator_findings(V.ADJUDICATED_UNCITED))
print(V.check_uncited()[0])
```

```
LOCATOR   08_exam.md → '**n = 1 per handover tier**, on a saturated' says the evidence is
          1 block above and names no artefact to look for there. ...
check_uncited ok = False
415 claim blocks scanned ...: 1 uncited, 9 ruled, 1 stale rulings
```

It fires on the *"names no artefact"* branch, not on the distance branch. If the
same false ruling had named the reports it claims are there, it would be caught by
the distance branch too (verified: variant A below). So the regression is covered
in both shapes. `test_locator_gate.py` — added concurrently — now encodes both.

---

## Defects

Nine, listed by severity. All reproduce against the file as it currently stands.

### D1 — HIGH. `any(p in body for p in named)` clears a false locator on any incidental path

**What.** `_ruling_paths()` harvests *every* backticked token in the whole
justification that has a `/` or an artefact suffix — including paths the ruling
names as a **contrast**, and including paths named inside the new
`(Corrected 2026-07-30: ...)` notes, which by construction describe what is at the
**wrong** location. `locator_findings()` then accepts the ruling if **any** of them
is in the target block.

**Reproduction.** One word changed in a ruling that ships today. The `08_exam.md`
"0.000" justification names two things: the handover reports (the evidence) and
`Theoria.md` (which its own correction note identifies as the only citation in the
block *one* above — i.e. the wrong block). Change "two blocks above" to "one block
above" and the locator becomes exactly the falsehood the note says was there:

```python
import verify_paper as V
k = ("08_exam.md", "the 0.000 that could be computed from two")
mut = V.ADJUDICATED_UNCITED[k].replace("cited two blocks above", "cited one block above")
print(V.locator_findings({k: mut}))   # -> []   PASSES
```

Block 13 (one above) contains `Theoria.md`; neither report is in it. The check
passes. The correction note that was written to document the bug is the thing that
now conceals it.

**Why it matters.** This is the exact failure class the mechanism exists for, and
it is reachable by a one-word edit to a shipped entry. The more careful a ruling's
prose is — the more it cites contrasts and records its own history — the more decoy
paths it supplies.

**Fix (described, not landed).** Restrict `named` to paths in the locator's own
clause, e.g. the backticked tokens between the locator match and the next sentence
boundary, and require **all** of them (or at least one path drawn from that clause
only). Failing that, exclude anything after the literal `(Corrected`. Do not use
`any()` over the whole justification.

### D2 — MEDIUM. The origin block is chosen by a different rule than the block that gets silenced

**What.** `locator_findings()` measures from the **first block whose text contains
the anchor**, including headings and non-quantitative prose. `scan_uncited()`
silences the first block that contains the anchor **and has a quantity**. When
those differ, the locator is validated against a block that is not the one the
ruling exempts.

**Reproduction** (scratch section `90_t.md`):

```
## 4 The main table moved twice          <- block 0, locator's origin

The gaming audit is recorded in `battery/artifacts/gaming_audit.json`.   <- block 1

The main table moved twice, from 19 -> 6 and then 6 -> 9, per the audit. <- block 2, the block actually silenced

Trailing prose with nothing in it.       <- block 3
```

ruling: `"Summarising the moves the block one block below states and cites
\`battery/artifacts/gaming_audit.json\`."`

```
locator_findings -> []               PASSES
scan_uncited hits -> {key: 1}, silenced block index 2
```

One block below the silenced block is "Trailing prose", which cites nothing. The
locator is false about the block it exempts and true only about the heading.

**Live today?** No — checked all nine UNCITED anchors; each one's first matching
block is also the quantitative one. It is latent, and `07_battery.md`'s "and the
main table moved twice" is a heading anchor, i.e. one line of body text away from
triggering it.

**Fix.** Resolve the origin with the same predicate `scan_uncited()` uses: first
block containing the anchor **that has quantities**, falling back to first match.

### D3 — MEDIUM. Artefact matching is naked substring, so a bare filename matches any file with that basename

**What.** `p in body`. `_ruling_paths()` admits bare filenames (anything ending in
an artefact suffix), and the paper's dominant citation idiom *is* the bare filename.

**Reproduction.**

```
Unrelated block citing `engine-rig/STATUS.md`.

The claim block with 42 in it.
```
ruling: `"The exam's status file is one block above -- \`STATUS.md\`."` → **PASSES**.
The ruling means `exam/STATUS.md`; the block carries a different repository's file.

Same shape with a directory prefix: ruling names `runs/survey/`, block carries
`runs/survey/unrelated.json` → **PASSES**.

**Fix.** Match on the block's *citation tokens* (reuse `CITE_TOKEN` /
`_split_siblings`) and compare whole tokens, not substrings of the raw text.

### D4 — MEDIUM. Unparsed phrasings are a silent pass, and the vocabulary is narrow

**What.** `if loc is None: continue`. The mechanism is opt-in by phrasing. These
all disable it while reading as locators to a human:

| phrasing | parsed? |
|---|---|
| `cited in the previous block` | no → PASSES |
| `cited in the immediately preceding block` | no → PASSES |
| `cited just above` | no → PASSES |
| `cited immediately above` | no → PASSES |

Reproduced with a block that demonstrably does not carry the named artefact; all
four return `[]`.

This is inherent to a prose-parsing check and the new table docstring does state
the convention. It is recorded because "the ruling stated a distance and we did not
check it" and "the ruling stated no distance" are indistinguishable in the output —
nothing prints when a locator fails to parse, so a reader cannot tell which rulings
were actually examined. **Fix (cheap):** print a one-line `unchecked` note for
every ruling whose justification contains `above|below|up|down|earlier|later` but
whose locator did not parse.

### D5 — MEDIUM/HIGH false positive. Check E measures a `lines` locator from the block's first line, not from the anchor

**What.** On the check-E path `anchor_line` is the *block start* (`blocks[k][0]`).
A writer counting lines counts from the sentence they are ruling on. For any anchor
that is not on the block's first line the two disagree by the anchor's offset within
the block.

**Reproduction.**

```
L1  Preamble paragraph that cites `runs/x/evidence.json` and is the evidence.
L2
L3  Line one of the ruled block.
L4  Line two of it.
L5  Line three of it.
L6  Line four of it.
L7  The anchor sentence with 42 in it lives on line 7 of the file.
```
ruling: `"The evidence is six lines above -- \`runs/x/evidence.json\`."`
The locator is **true** — six lines above L7 is L1, the evidence. Result:

```
LOCATOR  90_t.md → 'The anchor sentence with 42 in it lives' says 6 lines above,
         which is off the end of the section.
```

A true ruling is dropped and its block reports UNCITED. Worse, the message is
wrong about why: the section has seven lines, nothing is off its end; L3−6 = −3 is.

**Live today?** `03_a0.md`'s `(2, line, back)` ruling passes, and the table's new
convention retires line locators. But nothing *enforces* that convention, and a
check-E ruling written "four lines above" today gets a wrong verdict.

**Fix.** Either resolve check-E line locators from the anchor's own line (find the
anchor's line inside the block rather than using the block start), or reject the
`line` unit on the check-E path outright with an explicit
`"state the distance in blocks"` finding — which is what the table docstring
already asks for.

### D6 — MEDIUM false positive. A merged block's line span is understated, so line locators skip over it

**What.** `_target_block()` computes `end = ln + len(body.splitlines()) - 1`.
`_emit()` merges a table/list/quote chunk into the prose chunk above it *without*
the blank line between them, and `_blocks()` also drops heading and fenced lines.
So `end` understates the true span by at least one line per merge, and blocks are
non-contiguous in the line coordinate.

**Reproduction.**

```
L1  The anchor block with 42 in it, ruled here.
L2
L3  Preamble citing `runs/x/evidence.json`:      <-.
L4                                                 |  one merged block,
L5  | a | b |                                      |  real span L3..L7,
L6  |---|---|                                      |  computed end = L6
L7  | 1 | 2 |                                    <-'
L8
L9  Trailing block.
```
ruling: `"The evidence is six lines below -- \`runs/x/evidence.json\`."` — true:
L1+6 = L7, the last row of the evidence block. Result:

```
LOCATOR  ... says the evidence is 6 lines below, but the block there (L9) carries
         none of runs/x/evidence.json. Nearest block offsets carrying it: [1]
```

The forward fallback (`ln > line and fallback is None`) jumps past the block the
line is genuinely inside. The backward fallback happens to absorb the same error,
which is why this only bites in the `below` direction.

**Fix.** Have `_blocks()` return a true `(start, end)` span, or compute `end` as
the start of the next block minus one.

### D7 — MEDIUM false negative. On the check-F path `anchor_line` can come from a line `_blocks()` deliberately excludes

**What.** The `anchor_is_token` branch scans **raw** `text.splitlines()` for the
first line containing the token, while `i` comes from a search over `_blocks()`.
Code fences, headings and blank lines are absent from `_blocks()` but present in
the raw scan, and the raw scan matches the token as a bare substring — including
inside a longer path and inside prose. The two origins can therefore land in
different places, and the `line` unit uses the raw one.

**Reproduction.**

```
L1  Evidence paragraph citing `runs/x/evidence.json`.
L2
L3  ```
L4  cat playbook.dsl                  <- first raw occurrence; not in any block
L5  ```
L6
L7  Unrelated middle paragraph, cites nothing.
L8
L9  A sentence citing `playbook.dsl` bare.    <- the citation check F is ruling
```
ruling: `"Names the form. The instance is two lines up -- \`runs/x/evidence.json\`."`
with `anchor_is_token=True` → **PASSES**. Two lines up from the actual citation
(L9) is L7, which cites nothing; the check measured from L4 instead.

**Fix.** Restrict the raw line scan to lines that fall inside `blocks[i]`, and
prefer a backticked occurrence of the token over a bare one.

### D8 — LOW/MEDIUM false positive. Only the first locator in a justification is parsed

`RULING_LOCATOR.search()` takes the leftmost match. A justification that mentions a
position in passing before stating its evidence gets the wrong one.

```
ruling: "Discussed in the block above, and the artefact itself is two blocks above
         (`runs/x/evidence.json`)."
```
against a section where the evidence is two blocks above → **FLAGGED**, reporting
"1 block above". The docstring already records one near-miss of this family ("the
frozen-baseline paragraph below"), so the hazard is known; `search` rather than
`finditer` is the residue. **Fix.** Check every match, and pass if any resolves.

### D9 — LOW/MEDIUM. Check F double-reports a bad-locator ruling, with a false reason

`check_uncited()` was given `if key in invalid: continue` before the STALE loop.
`check_bare()` was not — its final loop is an unguarded `for key in stale:`.

```python
V.ADJUDICATED_BARE[("02_framework.md", "THEORIZE_LOG.md")] = (
  "Names the kind of file each arm keeps; the instance is one block above -- "
  "`cold-start-a0/THEORIZE_LOG.md`.")
V.check_bare()
```
```
LOCATOR   02_framework.md 'THEORIZE_LOG.md' says the evidence is 1 block above, but ...
93 bare-filename citations: 1 ambiguous, 3 ruled, 1 stale rulings, ...
STALE     02_framework.md `THEORIZE_LOG.md` is ruled and no longer appears.  <- FALSE
```

The token appears once; the ruling was dropped for a false locator, not because it
matched nothing. The STALE line asserts the opposite. (Pre-existing for `BROAD`
keys; the change adds a third source to the same unguarded loop.)

**Fix.** Add the same `if key in invalid: continue` guard to `check_bare()`'s STALE
loop — and, since `BROAD` has the same problem there, guard on `hits.get(key)` as
check E now does.

### D10 — LOW. The "N ruled, M stale rulings" summary double-counts

`stale` is a list, appended to by the LOCATOR, BROAD, ANCHOR and FENCE paths with
no de-duplication, and the summary computes `len(TABLE) - len(stale)` and
`len(stale)`. One ruling can be counted twice.

```python
V.ADJUDICATED_UNCITED[("08_exam.md", "no real result")] = (
    "Cited one block above -- `exam/artifacts/leakage.json`.")
V.check_uncited()
```
```
LOCATOR   08_exam.md 'no real result' ...
ANCHOR    08_exam.md 'no real result' is 14 characters ...
415 claim blocks scanned ...: 1 uncited, 8 ruled, 2 stale rulings
```

The table has ten entries and exactly one bad ruling. The line says 8 ruled (should
be 9) and 2 stale rulings (should be 1). `FENCE` also injects synthetic
`(section, "unbalanced fence")` keys into `stale`, which are not rulings at all.
Both the BROAD+ANCHOR overlap and the FENCE injection pre-date this change; LOCATOR
is a new third contributor. **Fix.** Make `stale` a `set` (or de-duplicate before
the summary) and count FENCE separately.

### D11 — cosmetic, recorded not argued

* `where` is rendered from the parsed numbers, so `"the block above"` prints back
  as `"1 block above"` and `"four lines up"` as `"4 lines above"`. A reader
  grepping the section for the ruling's own words will not find them.
* `n = 0` is accepted (`"0 blocks above"` resolves to the ruled block itself, so a
  ruling can cite itself and pass). Reproduced.
* `locator_findings()` does not honour `EXEMPT_SECTIONS`, so a ruling on
  `00_abstract.md` is locator-checked although its block is never scanned.
* `if not path.exists(): continue` — a ruling naming a section that does not exist
  is a silent pass here (the STALE rule does own it, so this is defensible).

---

## What the concurrent test file covers

`test_locator_gate.py` (11 tests, all passing) covers: wrong-block, names-nothing,
off-the-end, a true locator, no locator, `the block above` == 1, stale anchor,
missing section, and — importantly — that an invalid ruling does not silence its
block, plus a parametrised sweep asserting every shipped ruling states a true
locator. None of D1–D11 is covered: there is no test for a decoy path, for origin
divergence, for substring matching, for the `line` unit on either path, for the
merged-block span, or for the double-report and double-count in the wiring.

## Verdict

**Nine real defects: one high, five medium, three low.** The mechanism is a genuine
improvement over nothing — it is sound on both shipped tables today, it catches both
shapes of the failure it was written for, it correctly drops the ruling before the
scan rather than merely printing, and it turns `E UNCITED` truthfully red.

But it does not do what its docstring says. `"nothing did: ... `_blocks()` can check
every one of them"` overstates a check that is live on 5 of 13 rulings, that clears
a false locator on any incidental path in the justification (D1), and that measures
from a different origin than the one it is validating (D2, D7).

**Safe to commit as an improvement, not as a guarantee**, provided:

1. D1 is fixed before the entry lands — it is small, and it is reachable by a
   one-word edit to a ruling that ships in this same diff.
2. D9 is fixed (one line: the guard check E already has).
3. The `line` unit is either fixed (D5, D6) or rejected outright on the check-E
   path, which is what the table's own new convention asks for anyway.
4. The docstrings on `locator_findings()` and `ADJUDICATED_UNCITED` are cut back to
   what the code does: it checks locators of a specific shape, and a ruling that
   phrases its locator differently is not checked at all — and says so in the output
   (D4).

D2, D3, D8, D10, D11 can be follow-ups; none of them is live on the current table.
