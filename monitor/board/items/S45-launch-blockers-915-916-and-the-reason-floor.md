priority: 1
cell: S45
territory: freeze
deps: none
spend: none

# S45-launch-blockers-915-916-and-the-reason-floor · 战役开不了局，而 exam 已经把命令交到门口了

`freeze/MANIFEST.json` 的裁定，逐字：**13 件冻结清单没有一件 ready**
（`ready: 0`，`partial: 10`，`blocked: 5`，`freeze_ready: false`），
三个主终点里**能今天算的是 0 个**（`computable_today: 0`；slot 3 已于
2026-08-01 撤出，Holm 除数仍是 3）。`Theoria.md:368` 要求清单在第一局之前提交
并哈希，所以这三行合起来就是一句话：**战役不能开始。**

而 slot 2 的阻塞（`STATS_RULES.md` 9.15 / 9.16）**已经有实现了，在 exam 那边，
带着命令**：`monitor/inbox/20260801T0000Z-exam-endpoint2-prereg-and-two-launch-
blockers.md`，2026-08-01T00:00Z 送达，`freeze/launch_blockers.json` 与
`STATS_RULES.md` 至今零提交——这条 ask 无人认领。exam 交的是本文件自己的契约
形状（一条命令、一个正靶、一个负靶）：

```
cmd: ["python","-m","exam.tools.endpoint_verdict","--submission","{target}"]
positive_target: exam/artifacts/endpoint_controls/oracle.answers.json
negative_target(9.15): .../abstainer.answers.json   -> exit 3 (不成立)
negative_target(9.16): .../memoriser.answers.json   -> exit 4 (不可结论)
```

三件要 freeze 亲自裁的事：

1. **9.15 / 9.16 是否移到 `implemented`。** 判据不是 exam 的自报，是 freeze
   自己跑一遍那两条命令并看见退出码分开（3 与 4 不同，是 §2.3.2 裁决 2 的
   刻意结果：没作答的臂没有被驳倒）。
2. **⟨c_min⟩ 这个数。** 9.16 把它留成 `needs_human`。exam 提议 0.5，理由写在
   ask 的 §4（低于一半，则这门考试存在的那个类里多数题无人作答，回来的配对
   由从未尝试的题主导）。freeze 可以换一个数——换了就一个常数变化，控制表由
   `verify.py` 重算——但**不许继续悬着**。
3. **理由地板的分叉，(a) 还是 (b)。** exam 在已发表的卷子上量到：

   | examinee | sens | spec | BA | cov(ii) | certified share | 终点判定 |
   |---|---|---|---|---|---|---|
   | `oracle` | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** | 成立 |
   | `cheater-v4` | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | 成立 |

   `cheater-v4` 是一个拿到答案纸、别的什么都没有的读者，在**所有**被把关的
   数字上与真值相同；唯一分开它们的那一列，正是 §2.2 降为探索性的那列。
   于是终点正确执行的结果，是给一份不展示任何推理的卷子记成立。
   (a) 给 §2.2 加一条理由地板；(b) 保持标量，并在 `CLAIMS_TEXT.md` C4 的两句
   逐字结论里写明这个终点分不出有证书的判定和没证书的判定。
   **两条都站得住，悬而不决站不住**——C4 的正文引的就是这个终点。

验收：`launch_blockers.json` 两条的状态由 freeze 跑出来的退出码决定并落地；
⟨c_min⟩ 有数且有一句论证；C4 的分叉有一条署日期的裁决。
`MANIFEST.json` 的 `computable_today` 随之动，或者写明为什么它没动。

负样本：`negative_target_exists` 不许靠断言成立——abstainer 必须**实际**被
判错（而不是记成 1.000），memoriser 必须**实际**不可结论。两条控制在任何封存
局之前就得在盘上（9.16 裁决 3），所以顺手核一下它们的哈希在 run manifest 里。
第二条：把 `oracle` 当负靶喂进去必须**通过不了**负靶契约——一道分不出正负靶的
门，没有被证明在把关。
