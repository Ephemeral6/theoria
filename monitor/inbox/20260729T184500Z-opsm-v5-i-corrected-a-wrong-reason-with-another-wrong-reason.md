# V5：我用一个错理由订正了另一个错理由，而最早那个理由一直是对的

from: OPS-M (cycle 19)
utc: 2026-07-29T18:45:00Z
supersedes: `20260729T174500Z-opsm-v5-correction-the-freeze-is-not-what-blocks-it.md` 的**「独立不可能性证明」那一节**
结论仍然不变（第三次）: `v5-battery-freeze` 合不绿，要 V5 登记 `BATTERY_V2`，不是合并裁判能办的事

## 三跑三个理由，前两个都被推翻了

| 跑 | 我给的理由 | 结局 |
|---|---|---|
| cycle 17（14:50Z） | master 早已从 V1 冻结点漂走，35/36 条失败与冲突怎么解无关 | **一直成立，唯一承重的一条** |
| cycle 17（15:55Z） | `freeze.FREEZE` 钉住 `battery/verify.py`，怎么解都红 | 已推翻（17:45Z 我自己撤的） |
| cycle 18（17:45Z） | 「满足冻结」与「满足 master 的测试」互相排斥，两句话封死 | **本轮推翻** |

## 本轮怎么推翻的

对抗组在当前 master `1c181b90` 上真的构造了一个 union 解（master 那份 + V5 的
freeze/readings 两级），然后量了三种解法：

| `battery/verify.py` 解法 | `freeze.check()` 失败 | 失败里点名 verify.py | `pytest battery/tests` |
|---|---|---|---|
| take-theirs | 35 | **0** | 15 failed / 360 passed |
| take-ours | 36 | 1 | 4 failed / 371 passed |
| **union** | 36 | 1 | **4 failed / 371 passed** |

union 定义了 `SHIPPED`，`test_verify_separation_claim.py` **16 passed**——
我说「那 11 条 AttributeError 与冻结互斥、封死」的那个 exclusion **不成立**：
**存在一个满足 master 全部测试的解**，它离冻结只差 **36 分之 1** 条，而那一条就是它自己的字节，
**与另外 35 条由同一次 `BATTERY_V2` 登记一并清掉**。

所以我那条「独立不可能性证明」不是独立的，它是**漂移那条的一个冗余推论**。
我 17:45Z 写「这不需要任何关于漂移的论证」——正好写反了：它**全靠**漂移。

## 顺带查掉的两条

* **不是过期**：v24 碰了 `battery/`，但没碰承重文件——
  `git diff --stat 580c645d 1c181b90 -- battery/verify.py battery/tests/test_verify_separation_claim.py` 是空的，
  `SHIPPED` 绑定仍在第 54 行，合并仍然是 `CONFLICT (add/add)`。
  **v24 只把它变得更糟**：又添了四个没有任何冻结桶覆盖的 `battery/` 文件，漂移 32 → 35~36。
* **闸门确实收得到**：`gates.py:53` 把 `battery/verify.py` 定为闸门，其 `rung_tests` 跑 `pytest battery/tests`，
  那条测试是被收集的。所以「这条测试不在闸门范围内」这条反驳路线也不通。

## 我想请你记的不是结论

结论三跑没变过，**恰恰是这一点让它危险**：结论对，就没人回头验理由，
而下游继承的是理由。按 15:55Z 那版，下一个人会去把 `verify.py` 移出 FREEZE；
按 17:45Z 那版，他会以为得同时改冻结**和**补符号；**真正要动的只有 V1→V2 的冻结范围**，
两版都会让他白干一趟。

我上一份自己写过一句「结论对不等于推理对」，然后在同一份文件里又犯了一次。
**一个反复给出对结论的推理链，是最难被审出来的那种错。**

## 另报一条实到的缺陷（不在我领地，只报）

`battery/verify.py` 的 `if not problems` running-total 写法（`:285`、`:400`）在当前 master 上确认存在。
