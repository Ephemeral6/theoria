# 02 · 母体 A2 解剖 — 以及一个会改变设计的发现

来源:对 `cold-start-a2/` 的只读勘查(子代理 · 标定线)。

## 1 · 头号发现:A2 的打脸不是定理驱动的

工单写"**没有证明义务就没有打脸机制**"。在**框架层面**(Theoria.md §1.4/约束 6)这是对的。
但在 **A2 的实现层面,它不成立**,必须照实登记,否则整个消融是自证。

`a2pipeline/refute.py` 的判决行:

```python
"refuted": bool(episode["final_win"]),
```

而 `episode` 来自:

```python
world = a2_world.A2World(spec)
actions = world.solve()          # 裁判自己的世界解算器
```

`refute.py` 确实打开了 `exhibit_report.json`,但只取四个键(`theorem.name`、`theorem.lean_target`、
`certify_lean.green`、`theorem.axioms`)拼一个**纯展示用**的 `claim` 块;那句
`"says": "no reachable state satisfies Goal…"` 是**硬编码的散文**,不是从定理导出的。
**没有任何一行代码比较过反例与定理。**

更要紧的:**没有任何东西触发这个回路。** `refute`/`locate`/`probe`/`repair` 是
`run_all.py` 的 `STEPS` 里无条件列出的第 7–11 步。不存在"UNSAT 欠一张证书"的看门狗。
唯一一处把义务写进代码的是 `exhibit.py:148-153` 的合取:

```python
report["exhibit_green"] = bool(
    cheap["green"]
    and plan["status"] == "UNSAT"
    and lean.get("green")
    and not lean.get("axiom_reports", [{}])[0].get("axioms", ["x"]))
```

砍掉 Lean,它退化成 `cheap["green"] and plan["status"] == "UNSAT"` ——**这恰好就是消融臂的信念状态**。

### 这对设计的后果(DESIGN.md §7 展开)

如果我只是把 `refute/locate/probe/repair` 从 STEPS 里删掉,然后宣布"消融臂修不好",
那是**手工删掉回路再报告回路不转**,评审一拳就打穿。必须换一个做法:

> **两臂共用同一条由「意外」驱动的回路开关**(`Theoria.md:233`:"回路由意外驱动……
> 有意外才回 theorize"),差异只在于**消融臂那里产生不了那个意外**。

全量臂在野外的路径是 `Theoria.md:230`:
`UNSAT → 触发证书义务(约束 6) → 定理的 depends 子句 → 定向戳探(约束 7) → 打脸 → theorize`。
A2 的 `refute.py` 用裁判的世界解算器**离线替身**演了这条路(野外没有裁判)。
消融臂两个触发器(约束 6、7)都被切掉,所以 `UNSAT → 定案`,回路无铃可响。
**回路不转是刀口的推论,不是我手动删的步骤。**

## 2 · 第二个发现:`locate.py` 在消融后**完好无损**

| 模块 | 读 .lean? | 读 plan 状态? | 读 exhibit_report? | 消融后 |
|---|---|---|---|---|
| `refute.py` | 否 | 否 | 是(4 个展示键) | 逻辑存活;`main()` 需把 4 键置 null |
| `locate.py` | 否 | 否 | 否 | **逐字节存活** |
| `probe.py` | 否 | 否 | 否 | **完好**(只有 P-02 的理由变空) |
| `repair.py` | 是(3 次 Lean) | 经 run_plan | 是 | 约 40% 存活;重证整拍消失 |

`locate.py` 只需 `theory/generated_holed/theory.py` 与 `solved_episode.jsonl`,做三查:

```python
verdicts = {"misread_board": bool(board_diffs),
            "mispredicted_step": bool(step_diffs),
            "wrong_goal_test": bool(goal_diffs)}
culprits = sorted(k for k, v in verdicts.items() if v)
```

⇒ **善意变体里,消融臂若被白送一条真实解路,它是能定位的。**
这直接反驳了我在 `00-baseline-reading.md` §6 里的先验论证(那里我说它定位不了)。照实修正。

**证明真正买到的不是"能定位",是"三选一穷尽"。** `Theoria.md:43` 的反证——
"若三处全对,这条路在模型里也走得通,与**证明了**不可能矛盾"——依赖"证明了"。
裸 UNSAT 下存在第四支:**编码/搜索坏了**,此时三查会**全绿而反例仍在**,`culprits == []`,
定位退化成"不知道"。本仓库有这个第四支的实证:**D-A2-006**——PDDL 后端接不出 teleport 的
`?p - markedcell`,于是对一份**有** teleport 规则、step 完全正确的手册返回 UNSAT。

⇒ 这条可以**构造出来测**,见 DESIGN.md §9 的 E3。

## 3 · 证明义务的真实切点(与 A0 一致)

`gen_lean_a0.py` 从不引用 `ast.laws`。DSL 里的 `theorem` / `invariant` 子句**只渲染成 markdown 散文**,
是"义务的声明",不是义务本身。真正的义务由三个调用点创造:

```python
lean = generate_lean(ast, prob, theory_py,
                     invariant_builder=builder,   # weight_invariant(region, arena, comment)
                     goal_cell=goal_cell,
                     unsolvable=unsolvable,       # <- 这个 kwarg 发出 theorem unsolvable
                     semantics=semantics)
```

调用点在 `exhibit.py:81-83` 与 `repair.py:172-174`(经 `compile_a2.compile_manual`),
外加 `certify_a2.lean(...)`。**消融就切在这三处 + 不调 `certify_a2.lean`。**

`generate_lean` 内部(gen_lean_a0.py:321-347):

```python
L.append("theorem inv_init : I s0 = true := by decide")
L.append("theorem inv_closed (s : St) (d : Dir) : I s = true → I (step s d) = true := by")
L.append("theorem inv_all (s : St) (h : Reachable s) : I s = true := by")
if unsolvable:
    L.append("theorem goal_break (s : St) : Goal s = true → I s = false := by")
    L.append("theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by")
    L.append("#print axioms unsolvable")
```

## 4 · 全量臂在 A2 上的既有数字(本臂并排坐的那一列)

**展品**(`exhibit_report.json`):

| 闸 | 结果 |
|---|---|
| certify 廉价层(游戏记录 184 帧) | **GREEN** — 14904 像素,0 异常,`pixels_unexplained 0` |
| 同一手册 vs 全扫描(248 帧) | **RED** — 44 异常,128 像素无解释,首异常 t=184 cell (6,4) |
| plan | **UNSAT**,note:"…constraint 6 forbids stopping here; a certificate is owed" |
| certify Lean | **GREEN**,`axiom_reports [{"axioms": [], "name": "unsolvable"}]` |
| 世界 | **18 步解出**,`final_win true` |

`exhibit_is_false_of_the_world: true`,`zero_space.region_size 21`,`theory.lean 64789 B`。

**控制手册**(`certify_generated.json`):cheap 248 帧 / 20088 像素 / 0 异常 / green;
lean green,目标是 `inv_all`(**不是** `unsolvable`)。
`plan_generated.json`:SAT,length 18,backend `stub-bfs`,`world_reaches_goal true`。

**回路**(`loop_ledger.json`):8 拍 8 过 0 失 0 缺。
L2 定位:`culprits ["mispredicted_step"]`,`located_at t=11`,`mover_at (6,4)`,
诊断"missing rule, not wrong rule"。
L3 戳探:设计 5、执行 4、1 条 `not_separable_in_this_world`,轨迹 184→196 帧。
L5 重证:陈旧证书 `died true`,`axioms ["sorryAx"]`,Lean 报 `decide` 反证;新定理
`pocket_unreachable` green 且 `true_of_the_world true`。
L6 解出:SAT 18 步,`execution_mismatches []`。

`repair.py` 的 green 是六项合取,**其中四项是证明义务**:
```python
report["green"] = bool(cheap["green"] and report["stale_certificate"]["died"]
                       and lean.get("green") and latch.get("green")
                       and report["scored_against_the_world"]["true_of_the_world"]
                       and plan.get("green"))
```

## 5 · 只读复用的模式(照抄 A2 对 A0 的做法)

`cold-start-a2/_bootstrap.py` 把 `engine-rig`、`theory-compiler/src`、`cold-start-a0`、`HERE`
插进 sys.path。三条纪律:

1. **包名互不遮蔽** —— A2 用 `a2world`/`a2pipeline`,绝不叫 `world`/`pipeline`。
   ⇒ 本臂用 `abl*` 前缀。
2. **只导入库函数,绝不导入 `main()`**;凡是会写回上游的入口一律在本地重写驱动。
   A2 甚至把 `recovered_region` **抄过来**而不是 import,理由是 import 会连带拖进
   `pipeline.plan_stage`(它写回 A0 的 artifacts)。
3. **钉住你读过的东西** —— `concepts.py` 有 22 条 `UPSTREAM` 清单,逐个 sha256 进
   `artifacts/upstream_pin.json`,外加 `git rev-parse HEAD`。
4. **验,别声称** —— `tools/verify_readonly.py`:哈希 258 个文件 → 跑 run_all → 再哈希 → диff。
   A2 报告的结果是 258 文件 0 改动。

⚠ **不要把 `cold-start-a2` 上 sys.path 之后去 import `a2pipeline.*`** ——
那些模块的 `ROOT` 写死在自己目录,一调就写回 `cold-start-a2/artifacts/`。
只 import `a2world.*`(世界与轨迹读写),pipeline 逻辑本地重写。

## 6 · 一条现成的判据(约束 6 的机器形式)

`cold-start-a0/certify/fd_unsat.py` —— 测试用例的 docstring 一句话点透:

> "The distinction constraint 6 turns on, and the one `fd_adapter` loses."

```python
FD_UNSOLVABLE_EXIT = 12
def is_unsat(exc) -> bool     # stub 的 "no plan exists",或 FD exit 12
# exit 13 = "我的搜索不完备且没找到" —— 故意不算 unsat
```

**exit 12(证明无解)与 exit 13(搜索放弃)的区别,就是约束 6 的整个内容。**
消融臂按定义不作这个区分——它信的是"没找到"。这给了我一个廉价而精确的度量维度。
