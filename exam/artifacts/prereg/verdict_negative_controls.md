# 判决题 · the negative controls, and which floor catches which

paper `p15-verdict-a2`, rubric digest `26a518d99d99`

Thresholds: `S_min` 0.50, `c_min` 0.50, BA > 0.50. Rates are computed **after 弃权计错** (`exam/endpoint.py`); the observed rates the marker reports are beside them, and the two differ exactly where an examinee declined to answer.

| examinee | sens | spec | BA | observed sens | observed spec | class (ii) coverage | certified share | verdict |
|---|---|---|---|---|---|---|---|---|
| `oracle` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **成立** |
| `bluffer` | 1.000 | 0.000 | 0.500 | 1.000 | 0.000 | 1.000 | 0.000 | **不成立** |
| `denier` | 0.000 | 1.000 | 0.500 | 0.000 | 1.000 | 1.000 | -- | **不成立** |
| `overclaimer` | 1.000 | 0.375 | 0.688 | 1.000 | 0.375 | 1.000 | 0.000 | **不成立** |
| `abstainer` | 0.000 | 0.000 | 0.000 | -- | -- | 0.000 | -- | **不成立** |
| `memoriser` | 0.556 | 0.625 | 0.590 | 1.000 | 1.000 | 0.000 | 1.000 | **不可结论** |
| `null` | 0.000 | 0.000 | 0.000 | -- | -- | 0.000 | -- | **不成立** |
| `cheater-v4` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | **成立** |

## Leave one floor out

Each floor is disabled in turn and every control re-judged. A floor that changes no verdict when it is removed has never been observed to do anything.

| floors in force | controls credited |
|---|---|
| `all_floors` | none |
| `without_S_min` | `overclaimer` |
| `without_c_min` | `memoriser` |
| `without_ba_floor` | `denier` |

**This table was wrong when it was first written.** `S_min` was described as catching `abstainer` and `null`; disabling it changed no verdict, because both of those fail the BA floor as well. `overclaimer` — `unsolvable` everywhere except three solvable items, sensitivity 1.000, specificity 0.375, BA 0.688 — was constructed afterwards to be the case only the specificity floor refuses. Each floor now catches exactly one control on its own.

## The one it credits that it should not

`cheater-v4` is a real transcript: a reader handed the sheet and nothing else. It is identical to `oracle` in every gated number and is **credited**. The only column that separates them is `certified share` — 0.000 against 1.000 — and `freeze/STATS_RULES.md` §2.2 demotes exactly that column to exploratory while citing 这里考的是理由 as its reason. exam reports the number on every transcript and has proposed the amendment through `monitor/inbox/`; legislating it here would be one territory overruling a frozen document from inside its own.
