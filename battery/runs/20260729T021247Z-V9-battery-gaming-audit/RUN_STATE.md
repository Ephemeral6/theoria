# RUN_STATE · V9-battery-gaming-audit

`Theoria.md` Phase 2 工序 4（抗游戏审计），盲 + 预注册 + 变异体 + 对抗复核。
零 API、零网络、零模型调用、封存堆零接触。只写 `battery/`。

## 什么跑了

* **六个互不可见的盲攻击者**，各认领一组指标，工作在仓库之外的 docstring/注释
  剥除副本里（`BLINDING.md`）。之后另有**一名能看见全部材料的对抗复核员**，
  它的攻击单独记在 `attacks/a7_review.py` 并标注为**非盲**。
* **112 次攻击**，覆盖 38/38 条指标，**95 次落地**（S1∧S2∧S3 全过）。
  分数由 `battery.metrics.evaluate` 重算，贫困证书由 `check.py` 读构造函数源码判定；
  作者只能填 `claim` / `accidental` / `rationale`。
* **37/38 条指标刷得动。** 唯一没刷动的 M3 记 `undetermined`——它没有任何一条
  路径调用 `ok(...)`。
* 三道防法 D1/D2/D3 落地；37 个变异体扫过，**0 处与自己的预期不符**。

## 命令与实测输出

```
$ python -m pytest battery -q
319 passed in 3.69s
exit code 0
```

（基线 214。V9 新增 `test_v9_prereg.py` 17 项、`test_v9_defences.py` 15 项、
`test_v9_verdict_rule.py` 73 项，并改写了 `test_exploits_economy.py` 里两项
**断言缺陷存在**的旧测试。完整输出留痕在同目录 `pytest.txt`。）

```
$ python -m battery.audit.v9.run 20260729T021247Z-V9-battery-gaming-audit
battery/runs/20260729T021247Z-V9-battery-gaming-audit
```

## 预注册顺序，可证

```
$ git rev-list -1 HEAD -- battery/PREREG_V9.md
9892d23caf72436c8ce8eefaa9ef59bfc2b03cc8
$ git rev-parse HEAD
e073a8a38b8a7692a5a8c021e44309c4505f7255
$ git merge-base --is-ancestor 9892d23 e073a8a ; echo $?
0          # 0 = 预注册 commit 是结果 commit 的祖先
$ git merge-base --is-ancestor e073a8a 9892d23 ; echo $?
1          # 非 0 = 反向不成立，顺序严格
```

预注册的三条**事后修订**按其自身协议追加在 `PREREG_V9.md` 的 `## 修订` 段，
未回改正文。其中修订 1（`NOT defended` 项被折叠）是本轮预注册最实的一处失守：
整个裁决实现 `verdict.py` 根本不在预注册那个 commit 里。

## 裁决

* B14 基线主表 9 条（钉死在 `verdict.B14_BASELINE_MAIN`）→ V9 后 **0 条**。
* 被 V9 降级：`E2, E3, K11, K12, K7, M3, M6, P3, P4`（9 条）。
* `undetermined`（攻击全部拒答，且指标不会返回数字）：`M3`。
* 与 B14 基线的分歧：**9 条**。

逐指标表与对抗复核的四条判决见
[`battery/audit/v9/REPORT.md`](../../audit/v9/REPORT.md)。

## 没做的 / 撞到的

* **没有重写 `battery/artifacts/`。** 已登记的「裸跑 `run_battery` 会覆盖
  `battery/artifacts`」缺陷本轮**没有撞到**：`run.py` 只写 `battery/runs/`。
  按工单要求登记而不顺手修。
* 没有改 `GAMING_REGISTER` 的散文条目；两轮结论分文件并存，冲突留在明面上。
* 没有 push，没有碰 master、主工作树或别的 worktree。
