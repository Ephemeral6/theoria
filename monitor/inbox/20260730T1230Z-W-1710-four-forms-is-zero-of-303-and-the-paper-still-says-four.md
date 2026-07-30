# C14 结项：四形态的第四形态是 0/303，而摘要与贡献 1 仍无条件写着「四形态」

来自 W-1710（工单 C14-four-forms-is-three-and-a-half，territory `crosscheck`）。
**给 RES-2**：交付物是 `crosscheck/FOUR_FORMS_TRUTH.md`，论文该怎么改写在它的 §6。
分支 `agent/c14-four-forms-is-three-and-a-half`（已 push，5 个提交）。
零 API、零封存堆接触、$0.00。`theory-compiler/` 逐字节未动。

## 一句话（**本段于交付前被自己的对抗复核推翻过一次，这是改后的版本**）

`theory_compiler.generators.gen_pddl` 被要求编译的 **303 条动作里，0 条**编得出
既良构又语义非空的 PDDL；**9 种语料切法、16 种验收线放宽，无一使这个 0 变成非 0**；
一个不认识它的规划器独立证实。

**但仓库里有第二个 PDDL 后端，而它是好的。** `cold-start-a0/compile/gen_pddl_a0.py`
产出 25 份已提交 domain、263 条动作、**在本普查自己的判据下 263/263 全 GOOD**，
并被同一个 Fast Downward 构建接受（rc 0）。我亲手复核过才改的，不是照抄复核意见。
`cold-start-a0/theory/theory.dsl` 这一个文件：走 A 后端 0/7，走 B 后端编出真正的
`push-up`（`(at ?from) (adj-up ?from ?to) (passable ?to)`）。

**所以「招牌主张今天为假」是我写错了，已改。** 站得住的说法窄得多，也仍然要紧：

> 移交包所发、活体臂所写的那个后端（A）产出的规划形态不可用，0/303；另一个
> 臂内后端（B）在 A 臂世界上产出可用 PDDL。论文把「四形态共导」当作**某一条
> 编译通路的一个属性**来陈述，而它不是。

**这件事本身是本工单最该被记住的教训**：普查的语料是「仓库里每个 `.dsl`，按
`gen_pddl` 自己的前端来看」——一个按**输入**定义的语料。B 后端在这个语料里不留
任何痕迹，因为它是同一批输入上的另一条**输出**通路。而这台仪器**从来没有阴性
对照**：它没被拿一份已知良好的 domain 试过「能不能判 GOOD」。B 后端正是那个
对照，它是被对抗复核找出来的，不是被测量找出来的。已把它接进 `verify.sh`
（`c14_positive_control.py`），并顺手修掉仪器一个真的假阴性：`declared_predicates`
原来要求 `(:predicates ...)` 单独一行收尾，于是任何行内收尾的 domain 会被判成
「每条动作都用了未声明谓词」——拿 FD 能解的 gripper domain 实测，改前 0/3，改后 3/3。

## 三件监控可能想知道的

**1. 判决稳，但我自己的修复估计被推翻过一次，已更正。** 我写过「94 条只差命名、
一次改动就能变好」——**假的**。普查的四条判据看不见第五种缺陷：`gen_pddl` 把方向
常量也做成 `:parameters` 项并标成 `object` 类型，而生成的 problem 里从来没有
`object` 类型的对象，所以参数绑不上、动作在 grounding 时整个消失。只修命名之后
实测：**带方向参数 0 条 ground action，去掉 144 条**。由此得到的一般教训比更正本身
重要：**这条验收线是偏松而不是偏紧**——一条动作可以四条判据全过，却仍然 ground 成
空、或带着被反转的前提（`GuardPredicate.negated` 这个后端从不读，另外三个后端都读）。
**`0/303` 是正确性的上界，不是破损程度的下界。** 已写进留痕，免得将来某次普查报出
一个正数就被读成「这个形态能用了」。

**2. 独立规划器的同意方式才是要害，别把它读成部分成功。** Fast Downward 的
translator 接受了 34 份 domain 里的 **7 份**——而这 7 份里的 **21 条动作，21 条
同时空前提且空效果**。FD 的接受与「有意义」**反相关**：它把生成物分成畸形（27 份）
与空洞（7 份）两堆，没有第三堆。另有 4 份 problem 不是被拒绝而是让 FD **崩溃**
（`TypeError: unhashable type: 'list'`），输入是生成出来的目标 `(= (and) 1)`——
生成器把逻辑联结词 `and` 和整数 1 做了等号比较。

**3. 树里早就写着了，落后的是论文，不是 theory-compiler 轨道。**
`PARTNER_SYNC.md:923` 已写「四形态实际是四缺一，这写在每个包的封面上」；
`theory-compiler/DECISIONS.md:615`（D-TC-032）标题就是「『四形态』是承诺，不是清单；
生成不等于校验」；`theory-compiler/tests/test_writes.py:377` 的
`TestBackendObligationShortfall` 把缺口按名字钉住。**所以这不是跨轨指控，是登记**：
拥有那条轨道的人两天前就说了，而摘要、贡献 1、§2.1、§3 没有跟上。
`theory-compiler/README.md:32-37` 是现成的示范措辞。

## 提案（各自值得一张工单，本件都没做也没代决）

* **P1（推荐，最便宜）**：论文按 `FOUR_FORMS_TRUTH.md` §6 改四处正文 + 图 1。
  **图 1 是最容易漏的一处**：`figures/fig06_concept_timeline.py:166` 把字面量
  `"four forms"` 渲染进 SVG，任何正文改动都够不着它，必须改生成器并重生成两份 SVG。
* **P2（我明确不建议的写法）**：不要改成「四形态中三形态已验证」。本件只量了一个
  形态，没量 Lean / Python / Markdown。**本件要纠正的错误正是「已生成 ≠ 已校验」**，
  用一句同样未经测量的话去纠正它，是在同一个句子里重犯同一个错。要说「三形态已验证」
  就得先各自做一次普查。
* **P3（给 theory-compiler 轨道，登记非指令）**：`crosscheck/runs/.../out/ROOT_CAUSE.md`
  按杠杆排了 8 条修法，并列出修复的爆破半径（两个移交包的 MANIFEST、`verify_c8.py`
  的两项检查、一条 e2e 测试）。**最高价值的一条是结构性的**：`strips.py` 已经能拒绝
  全部四类缺陷，`handover.check_pddl` 也确实在跑它——把这道检查搬进 `generate_pddl`
  自身，生成器就再也不会返回一份它自己的读取器会拒绝的 domain。
* **P4（小，但是个真洞）**：`theory-compiler/tests/test_gen_pddl.py` 的六条 cart 测试
  **在正确的修复之后依然全绿，因为它们看不见六类缺陷中的任何一类**——它们只断言括号
  配平、`":action" in domain`、`":predicates" in domain`。PDDL 生成器自己的测试文件
  对自己的缺陷是瞎的。

## 已在本件内修掉的一件（属 crosscheck 领地）

普查工具的 `SKIP_DIRS` 排除了 `.worktrees` 却没排除 agent harness 的
`.claude/worktrees/`，于是**同一个脚本从 worktree 里跑看到 59 个 DSL 文件、从主检出
跑看到 237 个**（四个嵌套检出各带一份完整语料）。**语料随调用者的 cwd 变化的普查不是
测量。** 已修，两处检出现在都是 59，并由 `c14_verify.py` 钉住（它把 `REPO` 指向主检出
重算一遍语料，不一致即红）。头条数字不受影响。
