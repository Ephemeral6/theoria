# V5-verdict-three-types — plan

Worker `W-1652`. Territory `exam`. Branch `agent/v5-verdict-three-types`, base
`31bea46`.

## What the item asks, and what already exists

The board item:

> 三类判决题（小空间不可解 / 大空间不可解 / 可解但难）各在自建世界族出一题，每题带
> 构造性依据（为什么由构造即知答案）；用已知满分与已知零分的假被试标定判卷器；灵敏度
> 与特异度分开报——敢说不可解的框架必须在可解题上闭嘴。

Read literally, all four clauses are already on `master`, delivered by P-15 and
V4 as the paper `p15-verdict-a2`:

| clause | where it already lives | asked for | shipped |
|---|---|---|---|
| three classes, self-built world family | `exam/papers/verdict.py`, A2 family | 1 item each | 5 / 4 / 8 = 17 |
| constructive grounds per item | `exam/artifacts/variant_specs/*.json` | per item | 17 specs |
| calibrate with known-full / known-zero fakes | `exam/grading/calibration.py` | 2 fakes | 4 (`oracle` 1.000, `null` 0.000, `memoriser`, `bluffer`) |
| sensitivity and specificity reported separately | `exam/grading/confusion_matrix.py` | split | split by class, with coverage |

So V5 cannot be a build. Restating the item's own premise — 考卷的可信度取决于
判卷者本身对不对 — the work it actually owes is **to find out whether the
delivered instrument is right**, and to close what is not. This run is therefore
an adversarial audit with fixes, not a second implementation.

## The gaps carried in

Named in `exam/STATUS.md` and `exam/DECISIONS.md` before this run started, all
of them sitting on one of the item's four clauses:

* **W4** — `cart_region` in the certificate checker takes the undirected closure
  of a relation that is directed once an action is forbidden. Sound, incomplete.
  *(clause: constructive grounds)*
* **W5** — `win_tighten` is exercised only at its no-op boundary; there is no
  unsolvable `win_tighten` item. *(clause: three classes)*
* **W6** — the class (ii) 2^m bound assumes comb-shaped geometry. *(clause:
  constructive grounds)*
* **W13 / D-EX-018** — `leakage.metadata_hits` buckets on tag *values*, not
  tokens. This leak class has shipped once. `p15-verdict-a2` is unaudited
  against it.
* **W14 / D-EX-019** — nothing compares one item's prose with another's content.
  The verdict paper ships near-twin pairs on purpose, which is the shape most
  exposed to it.
* **D-EX-015** — `oracle` and `cheater-v4` are identical in every cell of the
  split confusion matrix. The pair, even split, even with coverage, does not
  separate ground truth from a reader who never saw a board. *(clause:
  sensitivity / specificity)*
* **Unnamed, and the one this run expects to matter most** — the constructive
  grounds are **prose**. `_self_check` verifies each reference certificate and
  each witness plan, and verifies nothing at all about the `justification`
  string that says why the construction settles the answer. A justification that
  has drifted from the board is a statement that passes its type check and is
  false of the world, which is the failure `Theoria.md` §1.3 is about.

## Method

Six adversarial auditors, launched in parallel, each read-only, each required to
back every claim with a command it ran:

1. certificate-checker soundness — find an accepted-but-false certificate
2. class (ii) 2^m bound — falsify the demonstrated bound
3. leakage — token-level and cross-item audit of the verdict sheet
4. marker calibration — find a marker fault the 4 fakes + 7 mutants + 8 faults
   miss on this paper
5. sensitivity/specificity reporting — find the next examinee the split pair
   cannot see
6. constructive grounds — verify all 17 justifications against the shipped level
   by computation

Findings are re-verified here before anything is changed; an unverified auditor
is just another confident agent (`STATUS.md` open weakness 14). Then fixes, then
a seventh adversarial pass against this run's own conclusions.
