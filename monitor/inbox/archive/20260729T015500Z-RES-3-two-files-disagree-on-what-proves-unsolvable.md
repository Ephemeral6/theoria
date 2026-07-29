# 跨轨：两个文件对「FD 退出码 12 是不是证明」判得相反，偏在不安全的方向

RES-3 / verify 赛道 / 工单 E11-engine-crosscheck-deep 的第六路（可达图裁决死锁与不可解主张）。
零 API、零网络、封存堆零接触、$0.00。

**这一条跨轨**，而且落在 `cold-start-a0/`——按 `CLAUDE.md`，那是 theory-compiler 轨道的目录，
**engine-rig 轨道不许动**。所以这是登记，不是动手；我一个字节都没改，也不打算改。
转给该轨道或监控裁决。

## 先说这一路的主结果，因为它是正面的

独立可达图（自写 BFS，不调用被裁决的任何一方）裁决了 **50 条**主张：
36 条 `deadlock_carver` 死锁定理（**含 `ring` / `open4` 这 18 条 recheck 从没验过的**）、
peg4/peg5 五张不可解证书、`probe_frontier` 的 p_side、A0/no-button/worldgen 四个世界。
**50 条全部成立，0 条被推翻。** 两个负控独立复否成功。
三套编码（STRIPS / C4 Lean / 复核员自写）在 open4far 上 112 动作、3352 可达态、
210/14 覆盖、最优 11 步**逐位吻合**。a2 那条已知假定理被独立重推翻，
断点定位到 `teleport_down` 单条边，距离 18 与既有 refutation 记录一致。

**定理本身是干净的。** 唯一的矛盾不在任何一条定理里，在**「怎么算证明了不可解」这条判定规则**上。

## 矛盾（我逐行复核过，两边原文如下）

`engine-rig/engines/fd_adapter/backends.py`：

```
FD_TRANSLATE_UNSOLVABLE      = 10
FD_SEARCH_UNSOLVABLE         = 11
FD_SEARCH_UNSOLVED_INCOMPLETE = 12
```

并且它的注释（同文件 :79-82、:253）说得很细：**经验上，一个被独立证明不可解的实例
退出 12 而不是 11**，所以 **12 同时覆盖两种情形**，因此它额外要求
「在 optimal 档、且 FD 报告状态空间已穷尽」才认。

`cold-start-a0/certify/fd_unsat.py`：

```
# 12 only.  13 means "my search was incomplete and I found nothing"
FD_UNSOLVABLE_EXIT = 12
...
return bool(match) and int(match.group(1)) == FD_UNSOLVABLE_EXIT
```

它的文档写「12 `SEARCH_UNSOLVABLE` — proved, not merely unfound — 13
`SEARCH_UNSOLVED_INCOMPLETE`」——**整体错开一位**，并且 `is_unsat`
**只匹配异常字符串里的数字，不看档位、不看日志**。

## 为什么这条值得现在记下来

1. **偏在不安全的方向**：按 a0 的规则，「我放弃了」会被上报成「我证明了无解」——
   **正是该模块自己声明要防的"裸 UNSAT"**。
2. **两边测试各自全绿**：a0 的测试把那个映射**写进了断言**，所以它的测试证明的是
   "代码符合它自己写错的那份理解"。**只有交叉才看得见。**
3. **仓库自带的实测件站 engine-rig 这边**：`engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`
   是对真实 FD 构建跑出来的。
4. **目前没爆，因为 pipeline 走 stub**——已装弹未击发。
   这也意味着**修它现在是便宜的**：还没有任何结论建立在它上面。

## 我建议的措辞，供裁决者参考

这不是「a0 写错了」那么简单：FD 上游 `driver/returncodes.py` 的字面定义与
**实测行为**本身就不一致（这正是 engine-rig 那段注释存在的原因）。
所以更准确的说法是：**两边都读了同一个模糊的上游事实，engine-rig 补了实测与额外条件，
a0 没补**。修法不是改一个常量，是把「什么算证明」这条判定**收敛到一处**，
并且**带一个负控**——构造一次 FD 放弃（而非证明）的运行，断言 `is_unsat` 必须为假。

## 这一路未判的，已列明不掩饰

exam 的 9 题、proxy 的 3 条（需联网，**没碰**）、a3-l2-oneway。

完整报告：分支 `agent/e11-engine-crosscheck-deep` 的
`engine-rig-crosscheck/partials/deadlock-via-reachability.md`，含共享依赖清单。
