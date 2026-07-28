# V15 —— 抽样框：做了什么，按什么顺序，以及哪里没做到

工单：`monitor/board/claimed/V15-census-sampling-frame.RES-3.md`
分支：`agent/v15-census-sampling-frame`，从 `8e2c7e0` 起，合并了
`origin/agent/v11-negative-control-census` 与 `origin/agent/v14-standing-negative-control-probe`
（两个分支只带来 `verify-lab/`，合并在 `verify-lab/` 之外只动了 `PARTNER_SYNC.md` 一个文件）。

零 API、零网络、未读 `.env`、封存堆零接触。只写 `verify-lab/`。未 push、未碰 master。

## 时间顺序（盲判的可审计性全在这个顺序上）

1. 读工单、`CLAUDE.md`、`verify-lab/NEGATIVE_CONTROL.md`（含 V11 与 V14 两节）。
   **这一步就已经不可逆地让本会话看过了 V14 的结论，包括工单正文点名的
   `cold-start-a2/a2pipeline/engines.py`。** 记在 `BLINDING.md` 第 1 条。
2. 写 `verify-lab/frame/frame.py`（总体定义）。中途改过三次口径，每次都是收窄→放宽：
   * 第一版要求「能非零退出」——**放弃**，因为那让第一问变成成员资格，
     结构性地数不出 V11 给过 15 次的「否」。
   * 第一版分层 B 要求异常「在本文件里定义」——**放宽**为「仓库任意处定义」，
     因为前者悄悄丢掉了 `exam/leakage.py`（`LeakageError` 声明在 `exam/model.py`）。
   * 第一版 shell 只认字面 `exit <非零>`——**放宽**为也认 `set -e`，
     因为 `ablation-arm/verify.sh` 与 `monitor/verify.sh` 全文没有 `exit`。
   * 第一版把解析失败的文件 `continue` 掉——**改成收进来并标记**，
     这一改直接暴露了 `release/checklist.py` 自 `fa59795` 起就 `SyntaxError`。
   四次全部是**放宽**方向。这不是巧合：抽样框在修的错误是一次排除。
3. 写 `verify-lab/frame/reconcile.py`，算出差集 134，其中非套件 128，
   去掉探针自己那 2 个 → **126 个待判**。
4. 从本分支 HEAD 做 `git archive` 导出到 scratchpad，**删掉 `verify-lab/`**，
   得到判定员用的盲树。
5. **同一条消息里并行派出九个判定 subagent**，每人一份领地批次 + 同一份
   `BRIEF.md`（三问逐字抄自 V11 的方法节）。九份提示词里没有任何 V11 行、
   没有任何计数、没有任何「什么答案是想要的」的暗示。
6. **在九个批次全部派出之后、任何一个返回之前**，本会话读了
   `CALIBRATION.md` 的方法节（§1 的 in-scope 规则与 §2 的折叠规则），
   为的是让重算能和 V14 同协议。判定员的指令此时已经封好，读这一步影响不到他们；
   但汇总者此后的取舍是由一个看过答案的人做的 —— 所以那些取舍全部落在
   `reconcile.py` / `matrix.py` 的代码里，不在散文里。
7. 九个批次陆续返回，逐份落盘到 `partials/`，机械归并成
   `verify-lab/SUPPLEMENT_TABLE.md`（126 行，与差集逐条对上，零重复、零缺失）。
8. 跑 `matrix.py`。先复现 V14：TP/FN/FP 三格逐字相同（43 / 20 / 3），TN 差 2。
   再算补齐后的四个数。
9. 派对抗复核 subagent 打「你的总体定义是不是为了让数字好看而划的」。

## 三个结果

1. **总体是 241 个单元**（把抽样框自己的三个工具也数进去后 243），
   V11 的 127 行覆盖 44.4%，negctl 的 141 条覆盖 58.1%。
   工单说的「74 个没判过」在新定义下是 **134 个**。
2. **补齐 126 行金标准**，全部盲于探针、全部 `读码`。
   「有负控 = 否」占 61%，V11 是 28% —— 便利样本系统性地偏向已被覆盖的一侧。
3. **矩阵：FP 3 / FN 20 → FP 6 / FN 41**（strict，同协议，分母从 95 涨到 219）。
   只看探针真正枚举的 145 个单元：**FP 1 / FN 36，FNR 从 39.6% 升到 50.7%**。
   新增的假阳一个都不在探针的总体里；变糟的是假阴。
   **V14 那句「不该进闸」被加强，其论据 4 的 FNR 数字要从 32% 改到约 51%。**

外加一条 V14 的空结果现在能说话了：`cold-start-a2/a2pipeline/engines.py`
盲判为「否」、判据为 `absent`、钉子为 `absent` —— 三者一致，是 TN。
**V14 的修是对的，只是当时的分母不允许矩阵这么说。**

## 没做到的事，逐条

* **零 `实测`。** 126 行全部读码。V11 有 24 行实测，也因此撞上六个判定员共用一棵树
  互相污染产物的问题，并把教训写进了自己的报告。这一批用「不跑」换掉那个混淆，
  代价是证据强度整体弱于 V11。
* **6 个分层 C（测试套件）没判。** negctl 一个都不打分，判了不会动矩阵一格。
  声明的缺口。
* **2 个入口没法盲判**：`verify-lab/negctl/probe.py` 与 `criterion.py`。
  判它们要读它们，读它们正是盲判禁止的事。
* **汇总者不是盲的**，且在开工前就已读过 V14 的报告。见 `BLINDING.md` 第 1、2 条。
* **`cold-start-a2/a2pipeline/engines.py` 那一格是本次补齐里最弱的一格**，
  因为工单正文点了它的名，虽然那个信息没有传给判定员。
* **函数粒度没修。** 框内唯一的假阳 `worldgen/build.py` 正是粒度问题。
* **抽样框数不出「本该有一个闸而它不在」。** V11 靠人判出过两条这种
  （`battery` 没有一条命令总闸、`release/bundle.py` 不存在）；机械枚举永远给不出。

## 顺手发现、不属于本条目领地、只报不修

* **`release/checklist.py` 在 master 上解析不了。** 字符串字面量里有一个裸换行
  （`:45`），`python release/checklist.py` 直接 `SyntaxError`。自 `fa59795` 起如此。
  V11 的普查记录着实测它 `7 present, 3 withheld, 0 absent`、`exit 0` ——
  那是在这个缺陷进树之前。`negctl/criterion.py` 与 `probe.py` 都在裸 `except` 里
  吞掉解析失败，所以它悄悄离开了探针的总体。**领地：`release/`。**
* 判定员在 b1 顺手报了一条关于 `monitor/tests/mutants.py` 可能与现在的 `quota.py`
  对不上的观察，未经本会话核实，原样记在 `partials/b1-monitor.md` 的附注里。
  **领地：`monitor/`。**
