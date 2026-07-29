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

## 4. 上一轮为什么不算盲

`battery/audit/exploits/*.py` 与 `battery/audit/gaming.py` 在同一棵树里，且
`gaming.py` 的每一条 `GAMING_REGISTER` 都写着 `how_to_game` 与 `defence`。
写 exploit 的会话读得到它。所以 B14 的 38 个 exploit 至少有一部分是
**按登记簿的提示去实现**的，而不是独立发现的。这不否定它们的价值——一个被提示
后仍然实现得出来的攻击仍然是真攻击——但它没法回答「登记簿没写到的攻击面有多大」。
V9 就是去量那一块。
