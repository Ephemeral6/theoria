# BLINDING.md — 攻击者看得见什么，看不见什么（V9）

工单纪律第 1 条：攻击者**不该拿到**「这个指标设计时想防什么」的说明；给它指标的
**定义与计算代码**，不要给设计意图、不要给已知弱点清单。否则测的是「照着提示找
答案」。

本文件写明我怎么挡的、以及**哪些没挡住**。写在攻击开始之前，与 `PREREG_V9.md`
同一个 commit。

## 1. 攻击者拿到的树

六个攻击者，**每人一份独立副本**（互相不可见，互不知道对方存在、也不知道自己
只分到全部指标的一部分），落在仓库之外：

```
<scratchpad>/v9-blind/{a1..a6}/
  battery/__init__.py
  battery/model.py
  battery/metrics/{__init__,economy,epistemic,exploration,mechanism,planning}.py
  battery/audit/__init__.py            (空壳)
  battery/audit/v9/__init__.py         (空壳)
  battery/audit/v9/check.py            (贫困证书检查器)
  battery/audit/v9/attack.py           (提交用的数据类)
  TARGETS.md                           (只有阈值表，没有理由)
  ATTACKER_BRIEF.md                    (协议 + 它自己那几条指标)
```

**这些 .py 全部经过 `ast.unparse` 往返，docstring 与注释一律剥掉。** 剥法见
`<scratchpad>/make_blind.py`。留下的是计算本身与 `definition=` 字符串——也就是
工单允许给的「定义与计算代码」。

## 2. 挡住了什么

| 泄漏面 | 处理 |
|---|---|
| `battery/audit/gaming.py`（散文登记簿：逐条写着「怎么刷它」「防法」「已知弱点」） | **不给**。这是本轮最大的泄漏面——上一轮的攻击者是看得见它的。 |
| `battery/audit/exploits/`（38 个已实现的攻击） | **不给**。 |
| `METRICS.md` / `STATUS.md` / `DECISIONS.md` / `PREDICTIONS.md` / `REPORT_V0..V2.md` / `audit/REDUNDANCY.md` / `README.md` | **不给**。已知弱点清单基本都在这几份里。 |
| `battery/artifacts/`、`battery/runs/`、`battery/tests/` | **不给**。真实数值与「测了什么」都会提示形状。 |
| `PARTNER_SYNC.md`、`monitor/inbox/`、`CLAUDE.md`、`Theoria.md` | **不给**（整个仓库都不在攻击者的树里，不是 `git rm`，是根本没复制）。 |
| 所有 docstring / `#` 注释 | 机械剥除。`model.py` 的 docstring 里原本逐条解释了每个字段是为了防什么（例如 `won` 能力位的整段理由），这是最隐蔽的一条泄漏，剥除后消失。 |
| 七条会泄漏意图的**运行期 reason 字符串** | 改写成中性短句。原文如 `won`：「path efficiency has no floor —— a run that gives up on step one scores better than any solve」——等于把攻击方案直接写给攻击者。改写只动人读的文字，不动 `status` 与 `value`。逐条列在 `make_blind.py` 的 `NEUTRALISE`。 |
| 「哪些在主表、哪些已是参考项」 | **不给**。攻击者不知道自己攻的是主表还是参考层，因此不会在主表上更用力。 |
| 攻击者之间 | 各自独立目录、独立会话、不交叉。工单指定「独立攻击比协同攻击更能暴露判据形状」。 |
| 汇总者的方向性预测（`PREREG_V9.md` §4） | **不给**。里面点名了 K12、M3、K7、P4。 |

## 3. 没挡住的（诚实清单）

1. **`definition=` 字符串本身带一点意图。** 七条指标的定义里写着
   "A diagnostic, not a ranking" / "the confound P1 and P2 are most exposed to"
   / "Support for X1/X4" 之类。它们是**注册表里的定义**，是工单明确允许给的东西，
   删掉就等于不告诉攻击者这条指标是什么。留着，并在此登记：`E1 E6 K7 M6 P5 X5`
   的「诊断项」身份、以及 `P5` 与 `P1/P2` 的关系，攻击者看得见。
2. **`needs` 元组是防御的地图。** `P4` 的 `needs` 里明摆着 `solve_attempt` 与
   `won` 两个闸。攻击者由此知道有闸，只是不知道为什么装。这个泄漏**删不掉**——
   闸就在计算路径上。
3. **`thin()` 的判据是防御。** 例如 E2/E3 的 `MIN_TURNS_FOR_SHAPE`、X3 的八条
   转移下限。同上，属于代码本身。
4. **盲是程序性的，不是强制的。** 攻击者是同一台机器上的子会话，文件系统对它们
   是通的；我只能在简报里写死「不许读本目录以外的任何东西，读了整份结果作废」，
   并要求每人自报一句。**这不是隔离，是纪律。** 复核时的可检验痕迹只有一条：
   攻击理由里若出现只有仓库里才有的专名（`Schema` 臂、`bare_cc`、`a0-spike`、
   具体局数），就是读过外面。我在对抗复核里把这条查一遍并记结果。
5. **我（汇总者）不盲。** 我读过 `gaming.py` 与既有 exploits，然后才写的预注册。
   预注册 §4 的五条预测因此是**有先验的预测**，不是盲预测——它们只用来检验我自己
   的判断，不能当独立证据。这一点写在预注册里，也写在这里。
6. **`check.py` 的白名单本身提示了「摆数据是允许的」。** 这会把攻击者推向
   「构造退化 Run」这一类攻击，可能压低了别的攻击形态的多样性（例如需要计算的
   攻击）。代价是自愿付的：不付这个代价就没法机械地区分「刷」和「真干活」。

7. **（对抗复核补记）`thin()` 的字符串里有具体数值，而我漏登记了。**
   K2 的 `thin()` 原文逐字包含 `39960` 与「3 adversarial gaps」——A0 与 a0-spike
   两个真实抽样框的大小。它不在 `make_blind.NEUTRALISE` 名单上，随剥除后的树进了
   攻击者手里，`a5` 的两个 K2 攻击直接用了这两个字面量。**它给的是这条指标的
   真实材料规模，属于第 3 条（`thin()` 判据是防御）的延伸，但我当时只想到判据、
   没想到判据里嵌着数据。** 攻击本身不依赖它（1/1 同样得 1.0），所以结论不受影响；
   登记在此，下一轮的剥除名单要按「字符串里有没有数字」扫一遍，而不是按我记得哪几条。
8. **（对抗复核补记）盲化经全量比对未被攻破。** 复核比对了仓库专名、层级词汇、
   汇总者预测词汇、防法名与产物数值：tier 知识、其它攻击者的存在、`V9-P*`、
   `D1/D2/D3`、`unsound(` **全部零命中**；118 个构造的 `Run` 一律
   `arm="attacker"` / `source="v9"`，无 `game_id`、`campaign`、`pile`、`model`。
   另有一处 `held_out_frame` 自由文本写了「sealed pile」字样，是装饰性文字、
   零优势，登记不追。

9. **（V24 补记）`P1` 的 `definition=` 里点名了开发堆与 A0。** 原文是
   「…needs ground truth, so **development pile and A0 only**」。它属于第 1 条
   （`definition=` 字符串本身带一点意图）那一类，是工单允许给的东西，但第 1 条
   当时只逐条列了「诊断项身份」与「P5 与 P1/P2 的关系」，没列这一条，所以补记。
   泄漏的是 P1 真值的**来源范围**，不是任何一局的内容；攻击者没有用到它。
   这一条是第 7 条要求的那次扫描找出来的——按「字符串里有没有数字」扫，而不是
   按我记得哪几条：`1.0 is optimal` 里的数字把整句捞了出来。扫描本身连同
   逐条结果落在 `runs/20260729T172530Z-V24-battery-blind-hardcoded-path/`，
   除本条外没有新增泄漏面（`economy.py` 的 `90%` / `25%` 是定义里的阈值常量，
   属于定义本身）。

## 3a. 致盲的源从哪里来（V24 起）

前述一切都以「重跑 `make_blind.py` 能得到攻击者当时看到的那棵树」为前提，而在
V24 之前这个前提是假的。`make_blind.py:16` 写的是一条本机绝对路径，指向工作树
`.worktrees/v9-battery-gaming-audit`；**工作树的 HEAD 会往前走**。致盲发生在
`9892d23c`（预注册、贫困证书、致盲，攻击之前），而该分支后来推进到 `0d586b6f`，
中间 `520dc5dd` 加进了攻击逼出来的三道防法。于是照着那条路径重跑，**从源头读进来的
10 个文件（`COPY` 的 8 个加 `check.py`、`attack.py`）里有 5 个**与当时不同——
写出的 12 个里另两个是空壳包，不从源头读，所以分母是 10 不是 12。
`unsound(` 会出现 13 次进入「盲」树，而它正是 §3 第 8 条记为**零命中**的词之一。
也就是说，那一步会安静地重建出一棵把答案写给攻击者的树，并照样跑完出结论。

现在 `SRC` 换成 `BLIND_REF`，钉死在 `9892d23c` 这个**完整 sha**，文件用
`git cat-file blob` 从该提交读出。

**这里对工单做了一处收窄，明说：** 工单第 1 条许可「分支名**或**提交 sha」，
这里只取 sha。理由是查过的：分支 `agent/v9-battery-gaming-audit`
**根本不在 origin 上**（`git ls-remote --refs origin` 零命中），所以新克隆解析
不了这个名字；而 `9892d23c` 在 `origin/master` 上，新克隆一定有它，`git gc` 也
剪不掉。加上该分支的 tip 已经漂移，用分支名只会把同一个漂移推迟一层——工单第 2 条
「重跑并确认与既有结论一致」在分支名下根本不可满足。
解析不到 ref、ref 下缺文件、不在 git 工作树里，一律抛 `BlindingError` 并以退出码
2 结束，**不回落到工作树、不回落到任何默认目录**。`BLIND_REF` 与 V9 运行清单里
`prereg_commit` 字段相等这件事由测试钉住，二者不能各自漂移。

盲树的 12 个 sha256 记在 `audit/v9/BLIND_DIGESTS.json`（此前没有任何清单记过
盲树的摘要），回归测试见 `tests/test_v9_blinding.py`。

## 4. 上一轮为什么不算盲

`battery/audit/exploits/*.py` 与 `battery/audit/gaming.py` 在同一棵树里，且
`gaming.py` 的每一条 `GAMING_REGISTER` 都写着 `how_to_game` 与 `defence`。
写 exploit 的会话读得到它。所以 B14 的 38 个 exploit 至少有一部分是
**按登记簿的提示去实现**的，而不是独立发现的。这不否定它们的价值——一个被提示
后仍然实现得出来的攻击仍然是真攻击——但它没法回答「登记簿没写到的攻击面有多大」。
V9 就是去量那一块。
