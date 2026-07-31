# RUN_STATE — V5-battery-freeze (W-252)

**工单**：`V5-battery-freeze`，领地 `battery`，分支 `agent/v5-battery-freeze`，
base commit `7df12a3`。

## 交付

`battery/BATTERY_V1.md` —— `Theoria.md:368` 冻结清单十三项里第 8 项
（指标电池 v1：定义与代码、逐指标方向预测）的第一次提交。四件必需内容全部落地：

| 工单要求 | 落点 |
|---|---|
| 定义 | §1，38 条指标逐条列出 id / 族 / direction / tier / 工序 1 判决 / 预注册状态 |
| 计算代码指纹（逐文件 sha256） | §2，四个 fenced 块：code 28 / docs 3 / freeze 3 / prereg 1 |
| 逐指标方向预测（快照哈希入册） | §3，`PREDICTIONS.md` 全文哈希 + 前缀哈希两道 |
| 抗游戏审计结论（哪些降为参考项、为什么） | §4，主表 9 / 参考 29，三条子句的规则全写出 |

另加三件工单没点名、但 `Theoria.md:330` 与 `:327` 要求的：**工序 1（区分力）与
工序 3（去冗余）的结论也一并冻**（§5），以及**闸门与负样本**（§8.1）。

新增代码：

* `battery/freeze.py` —— 冻结记录的解析与核验。LF 归一 sha256（口径取自
  `proxy/scoring/__init__.py:64`）；`unlisted_code()` 把「成员资格」本身也冻住，
  防第 39 条指标从冻结外面计算已发布的数。
* `battery/verify.py` —— 本领地此前**没有 verify 闸**，只能退化成裸 pytest
  （`monitor/gates.py`）。现在有了：先查冻结，再跑测试。
* `battery/tests/test_freeze.py` —— 12 个测试，其中 6 个是**负样本**：就地改指标 /
  加未登记的指标模块 / 事后改写预测（等长改写，只有前缀哈希抓得住）/ 冻结后追加预测 /
  截断预注册 / 删除冻结文件。没被见过报警的闸门等于注释。

## 结果

```
$ python -m battery.verify
ok    freeze: 28 code + 3 docs + 3 freeze files and the pre-registration all match BATTERY_V1.md
ok    tests: 226 passed in 1.03s
VERIFY PASS
```

基线 214 passed → 226 passed（+12，全部是新增的冻结测试）。**没有改动任何既有
指标代码**，因此没有任何已发布的数字发生变化。

## 两个必须随交付一起读的结论

**其一：这份记录冻的是一台尚未被证明能分开任何已知差异的仪器。** 在
`Theoria.md` 指定的梯度（CC vs Schema）上，38 条指标的工序 1 判决是
8 underpowered / 23 no-data / 7 not-ranked / **0 通过**。功效上限是硬的：双侧符号
检验需 6 局非平局配对，试点只有 4 局。写进 §0.2 并置顶，因为它决定了本电池所有数字
该怎么被引用。

**其二：三个 Phase 4 主终点里，电池只拥有一个。** 前载指数 = `E2` 在电池内；
U3 达成率与判决题准确率不在（分别在 U 阶梯打分器与考卷轨道）。所以**冻结本电池不等于
冻结了 Phase 4 的三个主终点**，冻结清单还需要别的项来盖这两个（记为 W-J）。

## 有意不冻的东西

输入与产物**只记录、不作闸门**（§6）。理由写在文件里：电池是被动仪器，Phase 4 的
全部意义就是把它指向它从未读过的输入；拿输入哈希当闸门，第一次回算封存堆就会按构造
失败。代价如实登记为 W-F：本冻结钉住了仪器，没有钉住读数。

## 登记在案的既有缺陷（继承，不就地修）

`BATTERY_V1.md` §7 列了十条 W-A…W-J。其中三条是本次新查出来的，此前没有写在任何
地方：

* **W-C**：`METRICS.md` 自相矛盾，共 10 条指标 —— tier 列由实跑攻击渲染，下方散文块
  由散文登记渲染。最难看的是 K10：散文写 *"it is why this metric stays in the main
  table"*，同一份文件把它列在 Reference 里。
* **W-D**：`Exploit.defended` 对 P4/K12/E2 已过期（三道防御都实现了，字段仍是
  `False`，只有 `succeeded` 翻了）。本记录因此不发布该字段。
* **W-E**：`REPORT_V2.md:204-205` 的工序 4 数字是 v2.1 之前的，三个都不对
  （38/37/13，实测 39/35/10）。

三条都**不在本次就地修**：修它们要动 `docs.py` / `gaming.py` / 报告，而那按定义
就是 `BATTERY_V2` 的事。冻结记录的职责是如实继承并指出来。

## 复核

结论性产出按扇出纪律派了两个对抗性 subagent 复核，各带一个视角：

1. **打机制** —— 目标是「改一个已发布的数而让 `python -m battery.verify` 仍然通过」。
2. **打文档** —— 目标是逐条推翻 §0–§9 的事实主张、引文与 file:line 出处。

复核结论与据此所做的修正，见下面的「复核回执」。

---

## 复核回执

**两个对抗性 subagent 都成功了。交付前的版本有六个可打穿的洞和十五处事实缺陷。**
下面逐条记，因为这是这份冻结最该被信任的部分：负样本不是想出来的，是先被打穿、
后被补上的。

### 复核一（打机制）：六次「改了已发布的数而闸门仍报绿」

| # | 攻击 | 现在被什么挡住 |
|---|---|---|
| S1 | 直接改 `artifacts/capability_spectrum.json` 里 K1 的值（0.987→0.500） | 新增 `readings` 桶：逐份记录、漂移**报告**、仍 exit 0（产物是读数，拿它当闸门会让 Phase 4 按构造失败） |
| S2 | 改 `validation_material.json` 再跑 `battery.docs`，`METRICS.md` 的「Never validated」从 21 变 7 | `METRICS.md` 与 `audit/REDUNDANCY.md` 进 `docs` 桶，**被 gated** |
| S3 | 加 `tests/conftest.py` 重绑 `docs.render`，手改 `METRICS.md` 主表成 12 条 | 走查改成**遍历每一个文件**，不再跳过 `tests/`；整个测试目录进 `suite` 桶 |
| S4 | 改 `pytest.ini` 加一行 `addopts` 把会反对的测试 deselect 掉 | `pytest.ini` 进 `code` 桶；`verify.py` 把 `deselected` 与「通过数 < 200」判失败 |
| S5 | 在 `freeze:code` 块里**重复一行**摘要，字典序位置正常，last-wins 静默改指 | 解析器对重复路径、重复同名块、重复 `prefix-bytes` 一律抛错 |
| S7 | 把一局从封存堆挪进开发堆、重写 `piles.json` 自己的 `sha256` 字段（自指，`guard` 照单全收） | 规范摘要 `3feca53e…` 钉进 `freeze.py` 的 `CUT_DIGEST`，作为**契约**核验（不是读数） |

**S6 是唯一没能在领地内部关上的**：把 `freeze.py` 的 `check()` 改成永远返回空列表，
冻结那一道必然报绿——它是用攻击者自己那份代码在进程内跑的。目前只被
`test_freeze.py` 的负样本集体失败抓住。**如实写进 §8.2 作为边界**，并给出唯一正解：
把 `freeze.py` 的摘要记到它管不着的地方（`monitor/gates.py` 配置或释出清单），
由外部先核一次。本记录不声称能防住改了 `freeze.py` 的人。

另修一个易读性 bug：`verify.py` 在 Windows 控制台（cp936）打印非 GBK 字符时会抛
`UnicodeEncodeError`，操作者看到 traceback 而不是失败原因。它 fail-closed，但看不懂。

### 复核二（打文档）：十五处事实缺陷，全部已改

按会不会误导论文评审排序，三处最严重的：

1. **`separates` 根本不是代码会发出的判决**（通过的那种叫 `discriminating`），而且
   `underpowered` 分支排在前面 —— 4 局配对下最小可达 p = 0.125 > 0.05，所以
   `discriminating` **在这批材料上按构造不可达**。原稿把它写成「38 条都测了、都没
   过」，那是把一个功效上限说成了一个发现。已重写 §0.2，并补上
   `PREDICTIONS.md:385-387` —— 这件事在回算之前就预注册了。结论不变，因果说对了。
2. **U3 达成率不是「在 `proxy/scoring/` 里」，而是全仓没有任何实现。**
   `proxy/scoring/` 是 ARC scorecard 的读取器，`proxy/` 下不出现 `U3` 这个串。
   W-J 因此更锋利：那个主终点不是「被别的清单项盖住了」，而是**任何清单项都盖不住
   它**。给监控的 inbox 已按更正后的说法写。
3. **E2 走到主表的实际代码路径，和 `REPORT_V2.md` 讲的故事不是同一条。**
   `collect()` 在两个 exploit 都不提议降级时按 claim 文本**字典序**破平，返回了那个
   **已经打不中**的长度攻击，于是走「攻击没打中 → main」；0.993 那条集中攻击从未被
   咨询，而 `gaming_audit.json` 里**根本不出现 0.993 这个数**。两条路径同给 `main`，
   所以 tier 没错——但引用出处必须写 `REPORT_V2.md`，不能写产物。登记为 **W-K**，
   不就地修（改 `collect()` 会重算 tier，那是 `BATTERY_V2` 的事）。

其余十二处已逐条改掉：`discrimination.json` 摘要打错一位（现由 `readings` 块机器
生成，不再手抄）；`.gitattributes` 的收录理由说反了（归一哈希已经覆盖 CRLF，它是保守
不是必需，如实标为唯一不满足收录判据的条目）；§6.3 引了一句**并不存在**的原话
（真话在 `audit/stats.py:3-4`）；`Theoria.md:328` 的引文把 ASCII 引号改成了「」；
K11 没有自己的 v2 行、v2 逐条行只有 18 条；`MEDIUM_EFFECT` 只有两个具名副本、
第三处是标签用的裸字面量；主表 9 条的 19→6→9 里 exploit 数当时是 38 现在 39；
「`METRICS.md` 逐字引用」实为转述；四处行号漂移（`Card` 在 `:66`、
`proxy/scoring` 引文在 `:71`、`gaming.py:383-384`、`test_docs.py` 还断言了
`Seal declaration`）；§6.1 的 `piles.json` 摘要是文件摘要、与人人引用的规范摘要
`3feca53e…` 不是一个东西，已加一句区分；§5.2 的
「38 → 32 簇、淘汰 5」差 1，原因是代表**按族**留（跨族簇 `[K6,X1,X4]` 留了两个代表，
33 个代表落在 32 个簇上），已写清展开。

**通过复核而未改的**：§1.1 整张 38 行表（族 / 方向 / tier / 工序 1 判决 / 降级列
逐格与实跑代码零不符）、append-only 的四次提交 127/113/149/119=508 零删除（含
`git log --follow` 无改名）、11 条 `[seen]` / 27 条盲、工序 4 的
9/29/39/35/17/10、W-C 的那 10 条、W-E 的 38/37/13→39/35/10、W-G、W-H 的 21 条、
以及 E2 警告原句逐字无误。

### 最终

```
$ python -m battery.verify
ok    freeze: 29 code + 3 docs + 16 suite + 2 freeze files, the pre-registration and the pile cut all match BATTERY_V1.md
ok    tests: 237 passed in 1.59s
ok    readings: 7 artefacts match the values recorded at freeze time
VERIFY PASS
```

`git status --porcelain` 只有五个新增路径，**没有一个既有 battery 文件被修改** ——
这就是「本次没有动过任何已发布的数」的可核验形式。
