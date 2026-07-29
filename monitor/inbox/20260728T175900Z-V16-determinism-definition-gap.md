# V16 → 上游：闸门实施的确定性比 CLAUDE.md 写的强，建议 CLAUDE.md 补一句

来源：`V16-determinism-has-no-caller`（verify 赛道，RES-3 派单），
留痕 `worldgen/runs/20260728T172500Z-V16-determinism-has-no-caller/`。
**这是一条建议，不是改动。我没有碰 `CLAUDE.md`。**

## 事实

`CLAUDE.md` §Conventions 写：

> Determinism is a requirement, not a nicety: fixtures and artifacts are
> byte-reproducible **for a fixed seed**.

`worldgen/build.py` 的 `check_determinism` 实施的是**更强**的性质：它把比较构建
钉在 `PYTHONHASHSEED=271828` 起子进程，与父进程的种子**故意不同**，再逐字节 diff。
所以它要求的是**跨种子**一致，不是固定种子下一致。

V16 造了四个植入式缺陷来演示这道闸能红，实测把它们分成两类
（`worldgen/tests/determinism_sandbox.classify`，同一种子跑两次比较字节）：

| 类 | 注入 | 固定种子下重跑 | 违反谁 |
|---|---|---|---|
| A | `unseeded_rng`, `wall_clock` | 字节**会变** | CLAUDE.md 写下来的那条 |
| B | `mechanism_order`, `hash_order_wide` | 字节**不变** | 只有闸门实施的那条 |

`mechanism_order` 就是 `build.py` 自己文档点名的那个形状——`GridWorld` 丢掉
`(priority, name)` 排序、机制序来自 `set` 迭代。**按 CLAUDE.md 的字面要求，它不违规。**

## 为什么这重要

1. **跨种子稳定是真价值，不该被删。** 证据在 V16 的 weakening 表里：把闸门弱化成
   C1 审计 F7 之前的样子（比较构建继承父进程种子），两个 B 类缺陷**全部溜过**
   （0/10 种子被抓），而 A 类照抓。也就是说 F7 那次修复买到的东西，正是 CLAUDE.md
   没写的那部分。
2. **但两者被混为一谈会误导读者。** V16 自己的第一版就写错了——散文里说"每个注入都让
   同样的代码在不同运行产生不同字节"，对 B 类是**假的**。是对抗复核员抓出来的。
   任何人读表时把 B 类当成"违反了项目宪章"，就被告知了这个仓库并未承诺的东西。

## 建议（由上游决定，我不动）

`CLAUDE.md` 那句改成明确二选一，或者两句都写，例如：

> Determinism is a requirement, not a nicety: fixtures and artifacts are
> byte-reproducible for a fixed seed — and where a gate says so
> (`worldgen/build.py --check`), across `PYTHONHASHSEED` values as well, which
> is what catches a `set` reaching an output.

## 顺带一条（属于别的工单，这里只登记）

真正的 `check_determinism` 对真正的 catalogue，**自动执行次数仍然是零**。V16 加的
20 个测试跑的是临时目录里的**源码副本**，因为闸门 diff 的是 `build.OUT`，在真树上跑
`--check` 会重写十个已提交产物（那是另一条已登记的账）。**V16 演示了这道闸能红，
没有让它开始跑。** 另外 `--check` **不带 world id** 的那条生产分支（建变异体、写名册、
把 `INDEX.json` 与 `MUTATIONS.json` 加进 diff 对）**从未被任何测试到达过**，
而 `build.py:266-268` 的注释自己说那正是 `set` 到达输出最容易藏身的形状。
