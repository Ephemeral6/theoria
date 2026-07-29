# V19 的病灶换了个词，规模是它的七倍：`deferred` 与 `unreachable` 都不进闸

RES-3 / verify 赛道，V19-unverified-is-not-true 的**登记不改**项。
由 V19 的对抗复核员发现（F5），本实现员**独立重数过**，数字逐条对上。
**一个字节都没改**——这一条不该由 V19 顺手修，理由在最后一节。

放在 `worldgen/runs/20260728T230307Z-V19-unverified-is-not-true/` 下等你上板。

---

## 事实

V19 修的是：`invariants_all_hold` 用 `.get("holds", True)` 把**未验证**写成**成立**，
35 份 ground truth 里 13 份中招。

`core/reversibility.py:251-273` 里有同一件事，换了两个词：

```python
if measured is None:
    verdict = "unreachable"          # the rule can never fire in this world
elif isinstance(stated, bool):
    verdict = "agrees" if stated == measured["re_witnessable"] else "DISAGREES"
else:
    verdict = "deferred"
```

**只有 `DISAGREES` 进 `claim_disagreements`**，而 `claim_disagreements` 是 build 闸
（`build.py` 的 `GATES`）。`deferred` 和 `unreachable` 两类**都不进任何闸，也不进任何布尔**。

独立实测（`out/worlds/*/ground_truth.json` 全量，35 个世界）：

| verdict | 条数 | 占比 | 进闸？ |
|---|---|---|---|
| `agrees` | 128 | 58.7% | — |
| `deferred` | 53 | 24.3% | **否** |
| `unreachable` | 37 | 17.0% | **否** |
| `DISAGREES` | 0 | 0% | 是 |
| **合计** | **218** | | |

* **218 条已发布主张里 90 条（41.3%）从未被核对过。**
* **35/35 个世界至少各有一条。** 不是长尾，是全体。
* 全仓 `claim_disagreements` 是**空的**——闸从来没有响过，因为能让它响的那一类是空的。

最常见的几条：

| 规则 | verdict | 出现次数 |
|---|---|---|
| `walk` | `deferred` | **35（全部世界）** |
| `door_mirrors_net` | `unreachable` | 12 |
| `blocked_portal_exit` | `unreachable` | 10 |
| `push` | `deferred` | 9 |
| `blocked_toggle_would_shut_door` | `unreachable` | 8 |
| `advance_cycler` | `deferred` | 6 |

`walk` 的 `reversible` 写的是散文
（`"conditional — reversible on open floor, not across a one-way edge"`），
`isinstance(stated, bool)` 为假，于是**每一个世界**里最基本的那条规则都记 `deferred`。
**这就是 `check: None`，换了个词。**

## 两处文档目前是乐观读法，都没更新

* `core/truth.py:23`（V19 改后仍在）——「**the reversibility stamp is measured**」。
  measured 的是 `max_witnesses`，**不是那条主张**；41% 的主张没有被对照过。
* `README.md:118` 同样的读法。

一个读这两句的人会以为 reversibility 那一栏是核对过的。V19 那 13 个世界的教训正是：
**人读的那份诚实、机器读的那个撒谎**，是可以查出来的；而这里是**两份都乐观**。

## 建议的做法（不是我来做）

和 V19 同形，但**要害在第 2 条**：

1. `deferred` 与 `unreachable` 各自成类并发布，别混进 `agrees` 的补集；
2. **`unreachable` 与 `deferred` 不是一回事，别合并**——
   `unreachable` 说「这条规则在这个世界里根本不会触发」，`truth.py` 的
   `rule_correspondence` 已经有一整套 `cascade` / `clause` 豁免在处理同一件事，
   两处口径必须先对齐再谈上闸，否则会和 `declared_never_fires` 打架；
   `deferred` 说「主张是散文，没法和布尔比」——那是 V19 里
   `latch_monotone` 那一类，**多半可以像 V19 那样真的验起来**
   （`walk` 的「open floor 可逆、one-way edge 不可逆」是可判定的）；
3. 上闸之前先量一遍：把 `deferred` 真验起来之后，还剩多少 `unreachable`。
   V19 的经验是这个数会大幅塌缩——13 个世界的红，验完只剩 0。

## 为什么 V19 不顺手修

三条，第一条是硬的：

1. **会让 V19 的验收线没人复核得动。** 90 条主张跨 35 个世界、6 个 mechanism，
   动它等于重写 reversibility 那一层；V19 的复核员做了 80 个变异体才把 V19 这一件钉住，
   把七倍大的一件塞进同一次交付，等于让验收线变成一件没人核过的事。
   这正是 RES-3 当初在 V16 里发现 V19 却**没有顺手改**的同一条理由，那次的判断被采纳了。
2. **口径要先对齐**（上面第 2 条）：`unreachable` 与 `rule_correspondence` 的
   `cascade` / `clause` 豁免是同一件事的两套说法，谁豁免谁得先定，不是实现细节。
3. **它跨出 V19 的领地判断**：`reversibility.json` 是 `exam/` 与 battery 读的，
   改类目要那边接受。

## 附带一条同形的，一起登记

`truth.py` 的 `rule_correspondence` 里，**37 条规则靠 `cascade: True` / `clause: True`
自我豁免**「declared_never_fires」这道闸。豁免是规则自己声明的、没有独立核对——
一条错标 `cascade` 的规则就此永久免检。和上面的 `unreachable` 是同一个口径问题，
建议并案。

---

RES-3 / V19。零 API、零网络、封存堆零接触。
数字复算：`worldgen/runs/20260728T230307Z-V19-unverified-is-not-true/`。
