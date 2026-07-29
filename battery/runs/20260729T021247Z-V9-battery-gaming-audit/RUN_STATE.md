# RUN_STATE · V9-battery-gaming-audit

`Theoria.md` Phase 2 工序 4（抗游戏审计），盲 + 预注册 + 变异体重跑。
零 API、零网络、零模型调用、封存堆零接触。只写 `battery/`。

## 什么跑了

* 六个**互不可见**的盲攻击者，各认领一组指标，工作在仓库之外的
  docstring/注释剥除副本里（`BLINDING.md`）。
* **105 次攻击**，覆盖 38/38 条指标；每次攻击的分数由 `battery.metrics.evaluate`
  重算，贫困证书由 `battery/audit/v9/check.py` 读构造函数源码判定。作者只能填
  `claim` / `accidental` / `rationale`，任何影响裁决的字段都是导出的。
* **91 次落地**（S1∧S2∧S3 全过）。**37/38 条指标刷得动**；唯一没刷动的
  M3 是个 stub。
* 三道防法 D1/D2/D3 落地；37 个变异体扫过，**0 处与自己的预期不符**。

## 命令与实测输出

```
$ python -m pytest battery -q
245 passed in 3.68s
exit code 0
```

（基线是 214 passed；V9 新增 `test_v9_prereg.py` 16 项、`test_v9_defences.py`
15 项，并改写了 `test_exploits_economy.py` 里两项**断言缺陷存在**的旧测试。）

```
$ python -m battery.audit.v9.run 20260729T021247Z-V9-battery-gaming-audit
battery/runs/20260729T021247Z-V9-battery-gaming-audit
```

## 预注册顺序，可证

```
$ git rev-list -1 HEAD -- battery/PREREG_V9.md
9892d23caf72436c8ce8eefaa9ef59bfc2b03cc8
$ git rev-parse HEAD
520dc5dda90eefd93c6c2afbe2b03db5b0745e49
$ git merge-base --is-ancestor 9892d23 520dc5d ; echo $?
0          # 0 = 预注册 commit 是结果 commit 的祖先
$ git merge-base --is-ancestor 520dc5d 9892d23 ; echo $?
1          # 非 0 = 反向不成立，顺序是严格的
```

## 裁决

* B14 主表 9 条 → V9 后 **2 条**：`E1, M3`。
* 被 V9 降级的 8 条：`E2, E3, K11, K12, K7, M6, P3, P4`。
* 与 B14 的层级分歧：**8 条**（全部是 main → reference）。

详见 [`battery/audit/v9/REPORT.md`](../../audit/v9/REPORT.md)。
判据见 [`battery/PREREG_V9.md`](../../PREREG_V9.md)，逐条数据见 `v9_gaming_audit.json`。

## 没做的 / 撞到的

* **没有重写 `battery/artifacts/`。** 已登记的「裸跑 `run_battery` 会覆盖
  `battery/artifacts`」缺陷本轮**没有撞到**：`run.py` 只写 `battery/runs/`。
  按工单要求登记而不顺手修。
* 没有改 `GAMING_REGISTER` 的散文条目；两轮的结论分文件并存，冲突留在明面上。
* 没有 push，没有碰 master，没有碰主工作树或别的 worktree。
