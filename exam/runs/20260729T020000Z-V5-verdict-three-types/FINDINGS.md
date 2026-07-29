# V5 — findings, in the order they were established

Every entry carries the command that produced it. An unverified claim is not a
finding; `STATUS.md` open weakness 14 is about exactly that.

---

## F-1 — the class split can never report a pair, because the class *is* the answer

Established here, before the auditors reported, and not previously written down.

```
$ python -c "from exam.papers.verdict import build; from collections import Counter; \
             p=build(); c=Counter((i.truth['class'],i.truth['claim']) for i in p.items); \
             [print(k,c[k]) for k in sorted(c)]"
('large_unsolvable', 'unsolvable') 4
('small_unsolvable', 'unsolvable') 5
('solvable_hard',    'solvable')   8
```

The three classes partition the paper **by answer**. `small_unsolvable` and
`large_unsolvable` contain no solvable item; `solvable_hard` contains no
unsolvable one. So in `confusion_matrix.py`'s split-by-class table:

* classes (i) and (ii) have an empty specificity denominator — always `--`;
* class (iii) has an empty sensitivity denominator — always `--`.

**Every cell of the split table holds exactly one of the two numbers.** D-EX-015
records the `--` in class (i)'s specificity as a deliberate and correct choice
("an arm cannot fail a test it was never given"), which it is; what was not
noticed is that the same argument applies to all three classes, so the *pair*
never appears anywhere except pooled — and pooling is the thing D-EX-015 exists
to say destroys the distinction.

The board item's clause is 灵敏度与特异度分开报 with a stated purpose: 敢说不可解
的框架必须在可解题上闭嘴. Inside a class, that comparison is unavailable by
construction. The instrument reports the pair only at the level where it has
already been argued to be uninformative.

**A stratification that does carry both answers already exists in the truth**,
unused by the matrix:

```
('large', 'solvable')   3      ('small', 'solvable')   5
('large', 'unsolvable') 4      ('small', 'unsolvable') 5
```

`board_size_class` cross-cuts the answer. Splitting the pair on it yields a real
sensitivity **and** a real specificity in each stratum, and it splits on exactly
the distinction classes (i) and (ii) were invented to draw — whether exhaustive
search was available — while keeping a solvable control inside each stratum.
`axes()` already computes `by_board_size`, but only as an awarded/possible
fraction, never as a confusion pair; `confusion_matrix.py` does not split on it
at all.

### What is and is not new here

`confusion_matrix.render_matrix`'s footer already states the fact — "Classes (i)
and (ii) hold no solvable items, so specificity is undefined there; class (iii)
holds no unsolvable items, so sensitivity is undefined there." What was not
drawn is the consequence: **no split cell anywhere holds both numbers**, so the
pair the item asks for exists only pooled. And what was not noticed is that the
truth already carries a stratification that fixes it.

### The measurement (`probe_pair_by_stratum.py`, in this directory)

`PYTHONPATH=. python exam/runs/20260729T020000Z-V5-verdict-three-types/probe_pair_by_stratum.py`

Each entry is `(sensitivity, specificity, positive coverage, negative coverage)`.

```
oracle     score=1.0000
   by class      : large_unsolvable (1.0, None, 4/4, 0/0)  small_unsolvable (1.0, None, 5/5, 0/0)  solvable_hard (None, 1.0, 0/0, 8/8)
   by board size : large (1.0, 1.0, 4/4, 3/3)              small (1.0, 1.0, 5/5, 5/5)
null       score=0.0000
   by class      : large_unsolvable (None, None, 0/4, 0/0) small_unsolvable (None, None, 0/5, 0/0) solvable_hard (None, None, 0/0, 0/8)
   by board size : large (None, None, 0/4, 0/3)            small (None, None, 0/5, 0/5)
memoriser  score=0.5882
   by class      : large_unsolvable (None, None, 0/4, 0/0) small_unsolvable (1.0, None, 5/5, 0/0)  solvable_hard (None, 1.0, 0/0, 5/8)
   by board size : large (None, None, 0/4, 0/3)            small (1.0, 1.0, 5/5, 5/5)
bluffer    score=0.2647
   by class      : large_unsolvable (1.0, None, 4/4, 0/0)  small_unsolvable (1.0, None, 5/5, 0/0)  solvable_hard (None, 0.0, 0/0, 8/8)
   by board size : large (1.0, 0.0, 4/4, 3/3)              small (1.0, 0.0, 5/5, 5/5)
```

Two readings, and they are the argument for the change:

* **The bluffer's signature is one cell under the board-size split and two rows
  under the class split.** 敢说不可解的框架必须在可解题上闭嘴 is the pair
  `(1.0, 0.0)`, and under the board-size split it is printed twice, once per
  stratum, in a single cell each time. Under the class split a reader has to
  join `small_unsolvable`'s sensitivity to `solvable_hard`'s specificity to see
  it — across rows whose item sets are disjoint, which is the join the pooled
  rate makes and D-EX-015 says is uninformative.
* **The memoriser's emptiness is one cell too.** `large (None, None, 0/4, 0/3)`
  says in one place that this arm has answered nothing at all on a large board,
  in either direction. The class split spreads the same fact over two rows and
  prints `1.0` twice beside it.

The strata are 5 unsolvable / 5 solvable (small) and 4 unsolvable / 3 solvable
(large), so both are populated on both sides and neither rate is undefined for
an examinee that answers.

---

## F-2 — the verdict sheet leaks, through *multiplicity* rather than through any value

Raised by the leakage auditor, then **re-derived here from scratch** rather than
believed: `verify_leak_claims.py` in this directory rebuilds the paper, rebuilds
the key, and recomputes every number without reusing the auditor's code.
`STATUS.md` open weakness 14 is the reason — two of this territory's four
recorded cheater claims did not survive being scored against the key.

```
$ PYTHONPATH=. python exam/runs/.../verify_leak_claims.py
items=17  answers={'solvable': 8, 'unsolvable': 9}  majority baseline=9/17=0.5294
```

### F-2a — production's metadata check has never been run against the answer

```
label sets derived from the key : ['board_size_class', 'class', 'search_credible']
`claim` among them              : False
items whose own answer word is printed on their sheet: 17/17 (guard drops the field above 10.2)
```

`exam/papers/verdict.py` declares no `answer_labels`, so `check_paper` receives
`answer_of=None` and every label comes from `derive_label_sets`. That function
drops any field whose label text is already on the sheet — D-EX-011's third
exclusion, written for the held-out paper's deliberately-published `split` tag,
whose stated reason is "a field the sheet already publishes is a stratum, not an
answer."

The verdict item's own question reads *"Is this level solvable? Answer
`solvable` or `unsolvable`…"*. **Both words are on all 17 sheets.** So every
item counts as publishing its own label whatever its label is, the guard fires
at 17/17 against a threshold of 10.2, and `claim` is dropped. The three labels
that survive — `class`, `board_size_class`, `search_credible` — are all
referee-side strata.

This is D-EX-011's own lesson recurring one level up. There the fault was that
an optional check did not run; here the check runs, on labels that are not the
answer. The guard cannot distinguish *the sheet states this item's value* from
*the sheet prints the whole answer alphabet on every item*.

### F-2b — and widening the field list would not have caught the actual leak

```
metadata_hits AGAINST THE REAL ANSWER (never run in production): []
```

Handed the real answer, the existing checker still reports clean, because
`METADATA_FIELDS = ("points", "tags", "kind")` and all three are **constant**
across the 17 items — D-EX-011's uniform-points fix held, and the tag list is
`("verdict", "a2-family")` on every item. The auditor's token-level version of
D-EX-018 also reports clean here: the `dead`-token class is genuinely absent.

The leak is not in a bookkeeping field, and it is not a value→answer map at all.

### F-2c — the leak is `level_id` **multiplicity**

```
  level_id distinct= 9  appearing once= 7  their answers={'unsolvable': 6, 'solvable': 1}
           rule 'reused => solvable' scores 13/17 = 0.7647 (baseline 0.5294)
  grid     distinct=12  appearing once=10  their answers={'solvable': 3, 'unsolvable': 7}
           rule 'reused => solvable' scores 12/17 = 0.7059 (baseline 0.5294)
```

Seven of the nine boards appear exactly once and six of those seven are
unsolvable. A cheater needs no key and no board reasoning: *if this level_id
occurs elsewhere on the sheet, answer solvable; otherwise answer unsolvable.*
**13 of 17 against a 9 of 17 baseline.** Adding one more sheet-visible feature —
`hazards` of length exactly 1 — takes it to **14 of 17 = 0.8235**:

```
  hazards=0 -> {'solvable': 6, 'unsolvable': 7}
  hazards=1 -> {'unsolvable': 2}
  hazards=3 -> {'solvable': 2}
  combined: reuse rule, overridden by exactly one hazard: 14/17 = 0.8235
```

**Why it is there, and why it was invisible.** The module docstring argues board
identity is safe: *"The same board appears six times under different operators —
twice unsolvable, four times solvable — so board identity carries no signal
either."* Every word of that is true **of the atrium**, which is one board out of
nine. The design that makes identity carry no signal *within* a reused board is
the same design that makes *being reused* a signal: a near-twin pair needs a
board used twice, and a board built to demonstrate one construction is used once.
The docstring's conclusion is drawn from the boards the argument was written
about.

Three existing checks were structurally incapable of seeing it. `probe_hits` is
exact-string and this leak is distributional. `structural_hits` compares key
names and `level_id` is on the `SHARED_KEYS` allowlist. `positional_report` looks
only at order, id and length, and reports this sheet genuinely clean
(`order_runs 13/17`, `clustered_by_answer false`).

**Honest caveat on "key-free".** The rule's *form* needs no key, but its
*direction* — reused means solvable rather than unsolvable — is a prior a cheater
must guess; guessed the other way it scores 4/17. So 13/17 is the yield of a
correct guess about exam design, not a certainty. It is still a leak: the prior
is a good one (a false-positive trap is built by weakening the operator on a
board that already has an unsolvable item), and the feature carries the
information either way.

### The new leak class

D-EX-011 found value→answer. D-EX-018 found token→answer, inside a value that was
unique for an unrelated reason. This is **multiplicity→answer**: no value
predicts anything, and how many times a value occurs predicts a great deal. No
checker in `leakage.py` computes a bucket-size feature at all.
