# verdict — sensitivity / specificity, split by class

paper `p15-verdict-a2`, positive class `unsolvable`, rubric digest `e06bdf52e6f5`

Sizes: `large_unsolvable` 4, `small_unsolvable` 5, `solvable_hard` 8

| examinee | score | sens (pooled) | spec (pooled) | sens · large_unsolvable | spec · large_unsolvable | sens · small_unsolvable | spec · small_unsolvable | sens · solvable_hard | spec · solvable_hard |
|---|---|---|---|---|---|---|---|---|---|
| `oracle` | 1.0000 | 1.000 (9/9) | 1.000 (8/8) | 1.000 (4/4) | -- | 1.000 (5/5) | -- | -- | 1.000 (8/8) |
| `null` | 0.0000 | -- (0/9) | -- (0/8) | -- (0/4) | -- | -- (0/5) | -- | -- | -- (0/8) |
| `memoriser` | 0.5882 | 1.000 (5/9) | 1.000 (5/8) | -- (0/4) | -- | 1.000 (5/5) | -- | -- | 1.000 (5/8) |
| `bluffer` | 0.2647 | 1.000 (9/9) | 0.000 (8/8) | 1.000 (4/4) | -- | 1.000 (5/5) | -- | -- | 0.000 (8/8) |
| `cheater-v4` | 0.5000 | 1.000 (9/9) | 1.000 (8/8) | 1.000 (4/4) | -- | 1.000 (5/5) | -- | -- | 1.000 (8/8) |

Each cell is `rate (answered / class size)`. **The rate alone is not a reading**: abstentions are kept out of the denominator, so an arm that abstains on everything it cannot do scores 1.000 on what is left.

`--` is an empty denominator, not a zero. Classes (i) and (ii) hold no solvable items, so specificity is undefined there; class (iii) holds no unsolvable items, so sensitivity is undefined there. An arm cannot fail a test it was never given, and writing those cells as `0.000` would say it had.

## Examinees this matrix cannot tell apart

* **`cheater-v4`, `oracle`** — every cell identical, scores 0.5000, 1.0000.

A pair of rates is not an instrument on its own. Where two examinees collide here, the thing that separates them is the score — which on this paper means the certificate half of the rubric, not the claim half.
