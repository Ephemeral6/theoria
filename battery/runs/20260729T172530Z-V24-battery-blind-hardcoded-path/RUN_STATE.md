# V24 · 致盲步骤指向一棵随时会被清掉的工作树

工人 `W-1682`，领地 `battery`，分支 `agent/v24-battery-blind-hardcoded-path`，
base `580c645d`。**零 API 调用，零封存堆接触**（全部操作是 `git cat-file` 与本地
`ast`；未读、未跑、未提及任何封存局）。

## 结论先写

工单说这条硬编码路径「随时会被清掉」。是的，但那是小的一半。**大的一半是：
照着它重跑，现在就已经得到错的树了。**

致盲发生在 `9892d23c`（「pre-registration, poverty certificate, blinding —
before any attack」，07-29 09:52:28 +0800）。硬编码路径指的工作树
`.worktrees/v9-battery-gaming-audit` 现在停在 `0d586b6f`，中间隔着 `520dc5dd`
（「105 blind attacks, 37 of 38 metrics gamed, **three defences**」）。也就是说，
那四个 metric 模块是**因为攻击才被改的**，而重跑会把改完的版本发给攻击者。

实测：**从该提交读进来的 10 个文件里 5 个不同**（`COPY` 的 8 个加 `check.py`、
`attack.py`；写出的 12 个里另两个是空壳包，不从源头读，所以分母是 10 不是 12），
`unsound(` 会 **13 次**进入「盲」树。
而 `unsound(` 正是 `BLINDING.md` §3 第 8 条与 `REPORT.md` §9(d) 双双记为
**零命中**的词之一。这不是「路径可能失效」，是「这一步会安静地致盲失败、
并照样跑完出结论」——正是工单第 1 条点名的那种坏法，只是它不是假设，是现状。

## 三件事

### 1 · `SRC` → `BLIND_REF`，钉死完整 sha，失败大声报错

`battery/audit/v9/make_blind.py`：

* `BLIND_REF = "9892d23c…"`，**完整 40 位 sha，不是分支名**。分支名可读性更好，
  但它只是把同一个漂移推迟一层——这正是本件要避免的错误，写进了 `D-B-023`。
* 文件用 `git cat-file blob <sha>:<path>` 读，不用 `git show`：前者绕过 smudge /
  eol 过滤，字节不受本机 `core.autocrlf` 影响。
* `BlindingError` + 退出码 2，覆盖：ref 解析不到、ref 下缺文件、不在 git 工作树里、
  git 不可执行。**不回落到工作树，不回落到任何默认目录，没有 best-effort 模式。**
  `--out` 目录在失败时保持为空（有测试钉住）。
* `9892d23c` 是 master 的祖先，所以工作树与分支都删掉之后它照样解析得到——
  这才是把「可以删了」交给 S30 的前提。
* 新增 `--digests`（只算摘要不落盘）与 `BLIND_MANIFEST.json`（落盘时记 ref /
  commit / python / 每文件 sha256）。

`BLIND_REF` 必须等于 V9 运行清单里的 `prereg_commit` 字段，由测试钉住：常量与
出处记录不能各自漂移。

**对工单的一处收窄，明说。** 工单第 1 条许可「分支名**或**提交 sha」，我只取 sha。
查证的理由：分支 `agent/v9-battery-gaming-audit` **不在 origin 上**
（`git ls-remote --refs origin` 零命中；`git branch -r --contains 9892d23c` 则
列出 `origin/master`），所以新克隆解析不了那个名字，而 `9892d23c` 一定在。
再加上该分支 tip 已漂移，分支名只是把同一个漂移推迟一层——工单第 2 条要的
「重跑并与既有结论一致」在分支名下不可满足。收窄是为了满足第 2 条，不是嫌第 1 条麻烦。

### 2 · 重跑致盲，与既有结论双向核对 —— 一致

盲树从未提交、也没有任何清单记过它的摘要（V9 MANIFEST 的 24 条里根本没有
`make_blind.py`），所以没有字节可比。可比的是**记在案的关于这棵树的断言**，
两个方向都比了（`rescan_blind.py`，结果 `rescan_blind.json`）：

| 方向 | 依据 | 结果 |
|---|---|---|
| 负向：盲树不含攻击后词汇 | `BLINDING.md` §3.8 / `REPORT.md` §9(d) 记为零命中 | **clean**：`unsound(`、`V9-P*`、`D1/D2/D3`、tier 词汇、`gaming.py`、`GAMING_REGISTER`、`how_to_game`、`a0-spike`、`bare_cc` 全部 0 命中 |
| 正向：登记在案的那处泄漏仍在 | `BLINDING.md` §3.7 | **在**：`39960` ×1、`3 adversarial gaps` ×1，都在 K2 的 `thin()` 串里 |
| 攻击者提交面 | `REPORT.md` §9(d) | **118 个 `Run`**、`arm` 全为 `attacker`、`source` 全为 `v9`、`game_id`/`campaign`/`pile`/`model` 一个都没被赋值——与报告记的数字逐字相符 |
| 确定性 | — | 两次重建逐字节相同 |

正向那一条是特意留的：**只查「有没有新泄漏」，一棵空树也能过**。一次丢掉了已知
泄漏的重建，同样不是攻击者当时看到的那棵树。

一处自纠：初稿的扫描把 `campaign` 列进盲树禁词，于是 `model.py` 报红。查下来
`model.py` 里的 `campaign` 是 `Run` 数据类的**字段名**（`campaign: Optional[str]
= None`，解释它的注释已被剥掉）。`REPORT.md` §9(d) 说的是攻击者**构造的 Run 没有
填**这些字段，不是字段名不可见——攻击者看不见字段就没法构造 Run。两个断言说的是
两个对象，扫描已拆成两段（scan A 查盲树，scan B 查提交），不再混。

顺手做掉了 `BLINDING.md` 第 7 条要求下一轮做的事：按「字符串里有没有数字」扫一遍
留存的字面量，而不是按记忆。除已登记的 K2 那条外只捞出一条值得登记的：`P1` 的
`definition=` 里写着 "development pile and A0 only"，已补记为 `BLINDING.md`
§3 第 9 条。`economy.py` 的 `90%` / `25%` 是定义里的阈值常量，属于定义本身。

### 3 · 绝对路径普查

`battery/`：**活代码里只有 `make_blind.py:16` 这一处**，已修。其余命中全在
`battery/runs/` 与 `battery/artifacts/` 的出处记录（`capability_spectrum.json` 的
`"root"` 字段、旧 MANIFEST、RUN_STATE 叙述里转录的命令）——出处记录里写着当时
东西在哪，这正是出处记录的用途，不动。现由
`tests/test_v9_blinding.py::test_no_machine_absolute_paths_in_battery_source`
钉住：`battery/` 下活代码（排除 `runs/`、`artifacts/`）再出现盘符路径就红。

`exam/`：**活代码零命中**。`exam/artifacts/build_manifest.json` 里有 12 处绝对
`sheet_path` / `key_path` / `cheater_brief_path`，看着像隐患，**查过了不是**：
唯一的消费者 `exam/tools/archive_run.py:74-87` 只取 `sheet_sha256` /
`key_sha256` / `n_items` / `question_type`，从不解引用那几个路径字段。是惰性记录。
（这条是查证过的，不是照抄扫描结果——扫描把它标成了「潜在隐患」。）

领地外，只报不动，已进 inbox：`freeze/verify.sh:168`
`[ -d "$SRC" ] || SRC="C:/Users/user/Desktop/theoria/baseline-arms/out/campaign"`
——一条机器专属的**静默回落**，和本件修的是同一个形态。

## 测试

```
python -m pytest battery/tests/test_v9_blinding.py -q      17 passed
python -m pytest battery/ -q                               352 passed   (V24 前 335)
python battery/verify.py                                   exit 0，四级全绿
python battery/runs/<this>/rescan_blind.py                 exit 0
```

`verify.py` 第 3 级报 104 个 run（主树是 112）：本工作树没有那些按设计不跟踪的
输入（`baseline-arms/out/shards`、schema traces），`verify.py` 自己把这条写成
note 而不是红，见其 docstring。

## gap（如实写，不降验收线）

1. **重跑复现的是代码树，不是攻击者拿到的全部。** `BLINDING.md` §1 列的每人一份
   `TARGETS.md` 与 `ATTACKER_BRIEF.md` 是手写的，`make_blind.py` 从来不生成它们，
   仓库里也没留。所以「攻击者看到的全部」里有两份 Markdown 无法复现，只有代码树
   可以。这一条无法靠本件补上——材料不存在。
2. **盲仍然是程序性的，不是强制的**（`BLINDING.md` §3 第 4 条），本件没有改变
   这一点，也不试图改变。
3. `ast.unparse` 的输出与 Python 版本有关，`BLIND_DIGESTS.json` 因此记了
   `"python": "3.13"`；换大版本重跑摘要可能不同，测试的失败信息会先指向这一点。
4. **V9 的结论本身没有被本件重新裁决过，也不需要**：盲树不在任何自动代码路径上
   （全仓 `v9-blind|make_blind` 只有 5 处命中，全是散文或脚本自身），攻击模块
   `a1..a6` import 的是真的 `battery.model`。所以本件不改变任何既有数值——
   它改变的是「这一步下次还跑不跑得对」。
