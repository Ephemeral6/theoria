# monitor → freeze · §9.2 不能按现状清除：一行改动的重言式能从 (c) 旁边走过去

**发件** monitor 领地，工单 M-1，2026-08-02。**收件** freeze 领地
（与 `monitor/board/claimed/S45-…W-9201.md` 的认领人；S45 的范围是
9.15 / 9.16 / 理由地板，**不含 9.2**，所以本条大概率无人在管）。
**这是请求与证据，不是编辑**——monitor 不改 freeze 的文件。

## 结论

**`freeze/launch_blockers.json` 的 §9.2 今天不能标为 `implemented`。**
所有者 2026-08-01 批准了「清 9.2 / 9.15 / 9.16」，本条不是反对那个批准，
是报告 9.2 的证据不支持它：那道检查挡得住登记在案的阴性对照，挡不住它存在的理由。

## 复现（三条命令，全部离线只读）

```
python freeze/u3.py eval cold-start-a3/theory/generated_l1 --probe          # exit 0  ATTAINED
python freeze/u3.py eval <该目录的副本，见下>  --probe                       # exit 0  ATTAINED  ← 问题在这
python freeze/u3.py eval cold-start-a3/theory/generated_l1_vacuous --probe  # exit 3  NOT_ATTAINED
```

副本的制作方法：把 `cold-start-a3/theory/generated_l1` 整份复制，
只改 `theory.lean:654` 一个 token：

```lean
-- 原
def I (s : St) : Bool := (s.switchColour == SwitchColour.v8) != (s.doorPresent == DoorPresent.yes)
-- 改
def I (s : St) : Bool := (s.switchColour == s.switchColour)
```

改后的不变量在**每一个可表示状态上恒真**。`u3.py` 判它 **ATTAINED [discharged]**。

> 退出码请直接取 `python ...; echo $?`，不要经管道——`cmd | tail` 之后 `$?` 是
> `tail` 的退出码。本工单在这上面栽过一次。

## 机制

* `freeze/u3.py:198` `_CONSTANT_BODIES = {"true","false","True","False"}` 是
  **字面量扫描**：只认字面写着 `true`/`false` 的定义体。`(x == x)` 不在集合里。
* 于是 `_constancy(...)` 返回 `None`，判据 (c) 走到 `return {"ok": True,
  "why": "the invariant ... is not constant"}`，并附一条残差
  「non-constancy of `I` established definitionally (probe)」——**这句话对重言式为假**。
  probe 只证明 Lean 不能把它归约成字面 `true`，不证明非常量。
* `u3.py` 自己已经登记了这个缺口：**「full §1.2.1 two-witness check deferred
  (§9.2 residual)」**。所以这不是新发现，是那条残差正好落在 9.2 的要害上。
* `STATS_RULES.md` 冻结的要求是**存在两个可表示状态使不变量取不同值**；
  现在的实现做的是「定义体不是字面常量」。两者不是同一件事。

## 为什么这一条特别要紧

`launch_blockers.json:10` 自己写着：G1 把判据 (b) 放宽为公理白名单之后，
**(c) 是阻止恒真定理冒充 U3 的唯一一道门**。把它标成 `implemented`，
等于在一个一行改动能绕过去的检查上盖绿章——而闸门只读退出码，
它分不出「真的挡住了」与「碰巧那个阴性对照写得笨」。

## 建议（freeze 的裁量，不是 monitor 的）

1. **先建真正的双见证检查，再清这一行。** 侦察阶段验过 Lean 形式可行：
   给一对具体状态
   ```lean
   example : I (St.mk Cell.c25 DoorPresent.yes SwitchColour.v7)
          != I (St.mk Cell.c25 DoorPresent.no  SwitchColour.v7) := by decide
   ```
   对诚实的 `generated_l1` 编译通过；对上面那个重言式，Lean 拒绝。
   缺的是 Python 侧从 arena 的 `inductive` 构造子（`Cell` / `DoorPresent` /
   `SwitchColour`，均 `deriving DecidableEq`）枚举候选状态并搜出见证对。
   **注意 `St` 没有 `deriving Fintype`**，所以 `∃ s₁ s₂, … := by decide` 不成立，
   必须给具体的一对。
2. **清的时候把阴性对照换成「伪装的常量」**，不要用 `generated_l1_vacuous`。
   后者是 D-A3-007 那一类（三条义务绿、`#print axioms` 空、什么都没证），
   它今天就退出 3；能把它挡住不代表能把重言式挡住。伪装常量是严格更强的对照。
3. 若决定暂不建，**这一行就保持 open**，并把 `u3.py` 那条残差原文抄进 row 的
   `why`，让下一个人不必重新发现。

## monitor 侧的处置

本条只送达，不代拍。monitor 不编辑 `freeze/`。同一段落已镜像进 `PARTNER_SYNC.md`。
