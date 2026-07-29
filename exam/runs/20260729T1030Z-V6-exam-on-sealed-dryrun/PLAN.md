# V6 · 封存彩排 — 计划（开工即写，随进展增量修订）

条目：`V6-exam-on-sealed-dryrun`（p3，cell V4，territory `exam`，lane `verify`）
分支：`agent/v6-exam-on-sealed-dryrun`　base：`c1a60420`　UTC：2026-07-29T10:30Z
作者：RES-3

## 侦察结论（三路 subagent，已核）

彩排的多数零件**已经在盘上**，V6 不是从零建：

| 零件 | 已存在的实现 |
|---|---|
| 封存护栏 | `exam/guard.py:103` `assert_synthetic_world`，转 `battery/guard.py`；`SealedPileError`；import 零网络（实测 0.08s，拉入的网络模块为 `[]`） |
| 算子库（冻结） | `proxy/variants.py:34` `LEGAL_OPERATORS = ("forbid_action","remap_action","step_limit","observation_loss","win_tighten")`，`Variant` 构造即校验 |
| 构造性依据登记 | `Variant.justification` 少于 40 字符即拒（`proxy/variants.py:68-73`）；`exam/papers/verdict.py:464` `_emit_spec` 双哈希（对象 + 文件字节） |
| 真值隔离 | `exam/model.py:108/112` `Item.sheet_side` / `key_side`；`Paper.sheet()` 结构上拿不到 truth |
| 三类灵敏度/特异度 | `exam/grading/confusion_matrix.py:55` `per_class_confusion`，已按 `small_unsolvable` / `large_unsolvable` / `solvable_hard` 分列，D-EX-015 |
| 归档 | `exam/tools/archive_run.py` → `runs/<id>/MANIFEST.json` |

**所以 V6 的价值不在重建这些，重建等于把已有的东西再抄一遍。**

## V6 真正要回答的问题

现行 verdict 卷面**全部建在 `a2` 上**（`exam/papers/verdict.py:80` `WORLD_ID = "a2"`）——
一个作者从第一天就完全理解的手搭世界。**这不是 Phase 4 的处境。** Phase 4 的处境是：
一局你没研究过的游戏，主表跑完之后才允许研究，然后用冻结算子库构造带依据的变体。

拿 worldgen 的 20 个世界当假封存局，能问出 a2 问不出的两个问题：

**Q1（主问题）· 构造性依据说的话，和穷举真值一致吗？**
真封存局上没有神谕——"由构造即知不可解"是唯一的真值来源，**且永远无法核对**。
worldgen 世界有 `worldgen/core/solvability.py:144 report()` 的穷举判定，
所以**彩排是这套程序唯一一次能被证伪的机会**。若某个变体的构造性依据说"不可解"
而穷举说"可解"，那是程序缺陷，正是彩排该抓的东西。

**Q2 · 冻结算子库真的与游戏无关吗？**
`LEGAL_OPERATORS` 是按"包裹合法集"选的，宣称适用于任何托管游戏。
把它套到一个不是为它设计的世界上，是对这条宣称的第一次真实检验。
`worldgen/core/world.py:27-33` 已经写明 `forbid_action` 与 exam 的同名算子
"same semantics ... which is what makes the two comparable"——即桥是有意留的，但只留了一根。

## 做法

1. **包裹层，不改世界**（Theoria.md §Phase 1 变体注入层：「不重写游戏，在代理上做确定性改写」）。
   实现 `WrappedWorld`：拦命令（`forbid_action` / `remap_action`）、记步数（`step_limit`）、
   判触败（`observation_loss`）、收紧胜利判定（`win_tighten`）。**不碰 `GridWorld`。**
2. **穷举神谕**：在包裹后的状态空间（含步数与"已触败"位）上做 BFS，得到该变体的真解/不可解。
3. **每个变体随附构造性依据**，走 `proxy.variants.Variant` 校验并落 `variant_specs/`，双哈希入账。
4. **对照 Q1**：构造性宣称 vs 穷举真值，逐条报，**不一致就是发现，不是失败**。
5. **护栏在彩排中真开火**：喂 `piles.sealed_pile[0]` 全名与短名，断言 `SealedPileError`；
   护栏未开火则整个彩排判红（不是跳过、不是警告）。
   封存 id **运行时从 `piles.json` 读**，绝不写进任何被跟踪文件。
6. **真值隔离**：sheet / key 分两文件，泄漏探针走 `exam/leakage.py`。
7. **判卷 + 三类灵敏度/特异度**：复用 `per_class_confusion`。
8. **归档**：`runs/<id>/MANIFEST.json`，含 `piles` 摘要与 `passive` 零花费块。

## 红线（写在开工仪式里，不是跑完再说）

* **零 API、零网络**：全程包在 `exam.guard.no_network()` 内；
  绝不 import `arc-recon/precheck.py`（它经 `client.py` 拉入 `urllib.request` 与 `load_api_key()`）。
* **零封存接触**：只用 `worldgen/out/worlds/INDEX.json` 里的 20 个世界；封存 id 只作为**被拒的输入**出现。
* 产物 LF；MANIFEST 的哈希按 LF 算（前世在这上面付过一次账）。

## 已知的、不由 V6 承担的红

* `leakage.check_paper` 今天在 20/20 worldgen 卷上都 raise（V7 §1，未修）——
  成因是 `heldout_worldgen` 不在 `exam/papers/__init__.py:34` 的 `BUILDERS` 里。
  V6 若端到端跑 `check_paper` 会因为不属于自己的原因变红。**处理：本卷自带探针并自查，
  不改 `BUILDERS`；把这条作为已知缺口写进 SEALED_DRILL.md，不静默绕过。**
* `exam/papers/verdict.py::_emit_spec` 有并发写 `variant_specs/` 的缺陷（已 xfail 钉住）。
  **处理：本彩排写自己的 spec 目录，不与 verdict 卷共享路径。**
