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
