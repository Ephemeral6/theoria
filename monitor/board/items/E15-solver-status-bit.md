priority: 2
cell: E15
territory: engine-rig
deps: none
lane: verify

# E15-solver-status-bit · 引擎自己分不出「不存在」与「我算不动」

`engines/lp_potential/potential.py:169-170`：

```python
if not result.success:
    return None
```

`result.success` 为假**同时**覆盖 HiGHS status 2（真不可行 = 确实没有线性 pagoda）、
status 1（迭代上限）、3（无界）、4（数值困难）——**全部塌成同一个 `None`**。

**已发布的 29.2% 不完备率仍然成立**，但它成立的方式值得记下来：E11 那一路的复核员
**自己去取了 HiGHS 的 status**，实测 639 例沉默里 638 例是 status 2，另 1 例是硬编码
`bound=10` 挡的。**任何不重新推导的人，拿不到这个数。** 一个需要读者重新推导才能
相信的数字，不该写进论文。

第二处同族：`engines/zero_space/zerospace.py:141` —— 特征数 >8 时枚举**静默退化**，
却仍然发 `scope: global`。

做四件：

1. **保留那一位**：`potential.py` 返回结构化结果（`infeasible` / `budget` /
   `unbounded` / `numerical`），不再塌成 `None`；调用点按语义分支，
   **只有 status 2 才算「没有线性 pagoda」**。
2. **重发那 639 例**，让 29.2% 这个数**直接从引擎产物读得出来**，
   并与复核员手工推导的那份逐位对照——不一致就以对照为准并说明。
3. `zerospace.py:141`：退化时 `scope` 不得再是 `global`，
   降级本身要正面写进产物（照 `bench/ladder.py` 的形状）。
4. **负样本**两条：一个迭代上限触顶的实例（断言不得判为「不存在」）、
   一个 >8 特征的实例（断言 `scope` 不得为 global）。

服务论文 WP1 与 WP9——正文里 lp_potential 的不完备性一段，
在这件做完之前**不要定稿**。零 API、零封存堆接触。
