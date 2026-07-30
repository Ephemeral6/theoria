# DRIFT-two-published-certifications-that-cannot-fail

severity: low-to-medium（A 条 low、B 条 low-medium；不合并成一个更高的数）
dimension: 7（不可能变红的检查）为主，兼 3（证据漂移）与 5（流程漂移）
audit range: pin `origin/master=3d59d0a6`（钉于 2026-07-30T04:00:52Z）；
两条都是 `monitor/audit/state.json:47` 带过来的欠账，本轮才过复核
status: 已过对抗复核。**复核部分推翻了我，两处都记在下面**：A 条的「模式」描述是错的，
A 条的后果被一组真正的正样本挡住；B 条我记的「缓解情节」是**假的**，删掉它反而加重责任。

## claim

两件被published出去的「已核实」，各自靠一个**不可能变红的东西**支撑：

* **A**：五处测试断言 `report["probe_hits"] == 0`，而那个字段在 `exam/leakage.py:1078-1085`
  **是字面常量 `0`**——断言的是 `0 == 0`。一份被跟踪的论文评审据此记了 **CONFIRMED**。
* **B**：六个被跟踪的文件里有七处引用指向三个 **从未进入 git** 的 `monitor/inbox/` 提案。
  发布清单只发布被跟踪的文件，所以这三处引用在**每一份 clone 里都指向空**——
  而全仓**没有任何检查器会去解析一处引用是否可解析**。

## evidence · A —— 五处断言断的是一个字面常量

### A1 五处站点，pin 上逐字复现（`git show 3d59d0a6:<path>`）

| file:line | 文本 | 所在测试名 |
|---|---|---|
| `exam/tests/test_adaptation.py:164-165` | `assert report["probe_hits"] == 0` / `... == 0` | `test_the_sheet_does_not_carry_its_own_answers`（:161） |
| `exam/tests/test_core.py:113` | `assert report["probe_hits"] == 0 and report["structural_hits"] == 0` | `test_clean_paper_passes_and_reports_its_evidence`（:110） |
| `exam/tests/test_handover.py:125-126` | 同上一对 | `test_sheet_is_leakage_clean`（:123） |
| `exam/tests/test_heldout.py:188-189` | 同 | `test_leakage_check_passes`（:185） |
| `exam/tests/test_verdict.py:309-310` | 同 | `test_leakage_is_clean`（:305） |

### A2 为什么空转，以及负样本

`exam/leakage.py:1078-1085` 里 `"probe_hits": 0` 与 `"structural_hits": 0` **是字面常量**，
而 `check_paper` 一旦有命中就在 `:1064-1076` **`raise error`**。
**能走到那条断言，本身就已经证明什么都没触发。** 断言之后不增加任何信息。

在 `%TEMP%` 的 `git archive 3d59d0a6` 副本上做了两个负样本（基线：五条目标测试全绿）：

* **变异 A（把字段与事实解耦）**：压掉 `if findings:` 的 raise、保留真实计算出的 findings，
  再构造一篇**真有** probe 泄漏和 structural 泄漏的卷子：

  ```
  真实计算出的 findings : [{"item_id":"leaky-01","check":"probe","hits":["r3c4"]},
                          {"item_id":"leaky-01","check":"structural","keys":["secret_target"]}]
  report['probe_hits']     : 0
  report['structural_hits']: 0
  ```
  **五处站点的三种写法全部在一篇带两条真实泄漏的卷子上通过。**
* **变异 B（把两个检查瞎掉）**：`probe_hits()` 与 `structural_hits()` 无条件返回 `[]`
  → **五条目标测试仍然全绿**。空转，两次独立确认。

### A3 复核推翻我的两处

1. **`== structural_hits` 这个模式根本不存在。** 在 pin 上
   `git grep 'probe_hits.*== *structural_hits'` 与 `'== report\["structural_hits"'` **命中 0**。
   真实的一对是 `== 0` / `== 0`。**我上一轮对模式的描述是错的**，实质不变。
2. **泄漏引擎并没有失去覆盖，所以后果被挡住。** 变异 B 铺到全部 10 个碰泄漏的测试文件上：
   **334 passed / 3 failed**（基线 337 passed）。变红的三条是真正的正样本，
   而且就在同一个文件里：`exam/tests/test_core.py:76`
   `test_leak_probe_fires_on_a_planted_answer`、`:85`
   `test_structural_check_catches_an_unprobed_leak`、`:96`
   `test_short_probes_are_refused_rather_than_checked`。
   **所以不存在「泄漏可能逃逸」的风险。** 缺陷是五条死断言在**误述被核实过的东西**。
   严重度因此按 **low** 报，不按 medium。

### A4 那份评审的 CONFIRMED：我把归因写错了，而真相更难看

`papers/phase1-workshop/runs/20260728T173000Z-P12-paper-multi-review/review-c-repro.md:413`：

> `| 44 | 0 probe hits, 0 structural hits | ibid. | **CONFIRMED** — probe_hits: 0 和 structural_hits: 0 在四篇上都成立 |`

那个 `ibid.` 指向的是 `exam/artifacts/leakage.json`（第 42 行，`:411`），
**不是**那五条测试断言。所以我上一轮写的「评审是靠这五条断言 CONFIRMED 的」**不对**。
**但结论只是换了载体**：`exam/tools/build_papers.py:84` 把 `check_paper` 的 report **原样**
存成 `"leakage"`，所以产物里的 `probe_hits: 0` 就是同一个字面常量。
**那位评审核实的是「0 等于 0」**——同样的空转，而且发生在一份**published的论文评审**里，
这是比测试更坏的载体。

### A5 既有项：无

pin 上 `git grep` 五个 `file:line` 串**没有任何被跟踪文件提到它们**；
`monitor/` 下没有任何文件提到 `probe_hits`；没有 DRIFT 立案过。
`exam/STATUS.md:1084-1099` 讲了这条**通则**并只点名 `test_handover_auto.py` 那一对
（「就在它**上面三行**的那两条一样的」），结尾写着：
> 「**修好一处『不可能失败的检查』并不会修好它旁边的那些，而『我已经修了一处』这份满足感正是让你停止查找的东西。**」
**它没有点名这五个文件。** 作者立了通则、没做普查——所以这不是自述限制，是漏项。

**踩到的坑，记下来**：`exam/STATUS.md` 在 pin 与 `223f78a8` 上都是 **1121 行**，
而在本地 `HEAD=b5998e5d` 上只有 **590 行**。照工作树读会以为 `:1084-1099` 这个锚点是坏的。
**用 pin 读。**（这是本轮第三次踩 LIVE-vs-TRACKED。）

## evidence · B —— 七处引用，指向三个从未进 git 的文件

### B1 三个文件在当前 pin 上仍未被跟踪

| 路径（均在 `monitor/inbox/`） | pin 上被跟踪 | 盘上存在 | `git log -1 3d59d0a6 -- <path>` |
|---|---|---|---|
| `20260729T231500Z-RES-2-negative-sample-shadowed-by-prose.md` | **否** | 是 | 空（从未提交） |
| `20260729T233000Z-RES-2-a-new-gate-silently-retires-the-old-one.md` | **否** | 是 | 空 |
| `20260730T0315Z-RES-2-a-line-anchor-into-a-growing-log-is-wrong-when-committed.md` | **否** | 是 | 空 |

第四个（`20260730T0210Z-RES-4-e18-needs-a-reassignment-decision.md`）**是**被跟踪的，经 `91898d8d`。

### B2 七处引用、**六个**文件（订正我自己）

`PARTNER_SYNC.md:1609`／`:1613`／`:1637`；
`papers/runs/20260729T224939Z-S34/MANIFEST.json:31`；
`papers/runs/20260729T224939Z-S34/RUN_STATE.md:70` 与 `:119`；
`papers/runs/20260730T031500Z-P22/MANIFEST.json:22`。
**订正**：其中两处是**同一个** `RUN_STATE.md` 的两行，不是我上一轮写的「两个 RUN_STATE.md」。
**七处位置、六个文件。**

### B3 规则确实先写下来了

`91898d8d`「S35: the paragraph cited an inbox proposal that was never tracked」，
`git merge-base --is-ancestor 91898d8d 3d59d0a6` → **true**，提交信息原文：
> 「…the file was only ever written into the live working tree -- untracked, while 121 of its
> neighbours are tracked. **Merging the paragraph without it would publish a citation to a file
> that is not in the repository.**」

规则 10:26 落地，而第 6、7 处引用**在那之后**才进来。

### B4 后果：一半成立，一半塌掉

**发布这一半成立。** `release/enumerate.py:98-102`：
```python
def _tracked() -> list[str]:
    out = subprocess.run(["git", "-C", REPO_ROOT, "ls-files"], ...).stdout
```
`git ls-files` 是**唯一**的枚举来源，没有 `os.walk`。未被跟踪的文件进不了
`release/MANIFEST.jsonl`；而 `PARTNER_SYNC.md` 与那两份 `MANIFEST.json`／`RUN_STATE.md`
**都会被发布**。所以这三处引用在每一份 clone 里都指向空。

**闸门这一半塌掉：没有任何东西会去解析它们，现在没有，将来也没有。**
`papers/phase1-workshop/verify_paper.py` 是唯一解析散文路径的，作用域是
`SECTIONS = HERE / "sections"`（`:149`），根目录的 `PARTNER_SYNC.md` 与 `papers/runs/**` 都在域外；
而它自己的 docstring（`:98-100`）还承认「候选集是工作树、不是 commit……用 `git ls-files` 才对」,
所以**即便在域内，一个未被跟踪但盘上存在的文件也会判绿**。
`figures/check_figure_citations.py` 只管 `papers/` 下的图版；
`fleet-study/verify.py:226-279` 只管 `fleet-study/data/*.jsonl` 的 `evidence` 数组，用工作树 `.exists()`；
`monitor/gates.py:163-177` 每个闸门只查一条声明路径的 `os.path.isfile`。
**全仓每一处存在性检查都是基于工作树的。**
**实测危害：published散文里三处无法解析的引用；没有任何闸门会为此变红，这个增量里不会，以后也不会。**

### B5 我记的缓解情节是**假的**，删掉它加重而非减轻责任

我上一轮写「monitor/inbox 是监控的领地，RES-2 不越界就提交不了，所以这是舰队协议缺口」。
**pin 上 `monitor/inbox/README.md` 只有一句：**
> 「提案箱。**执行会话唯一可写的 monitor/ 路径**。一事一文件，命名 `<UTC>-<from>-<slug>.md`。
> 提案不是指令；监控逐条裁决后移入 archive/。」

`monitor/CHARTER.md:22-28` 那张表的「仅 monitor/」是限制**监控自己**，并不排除别人，
表里也没有 `inbox/` 这一行；`CHARTER.md:32`／`:43`／`:55` 全在叫非监控会话往 inbox 投提案；
`monitor/mailbox/PROTOCOL.md:3` 把 inbox 定义为**向上通道**。
**并且 RES-2 自己有六个已被跟踪的先例**（如
`monitor/inbox/20260729T024500Z-RES-2-pile-digest-three-hashes.md`）。
**所以这不是协议缺口。我那句缓解必须删掉。**

**唯一活下来的缓解**：pin 上 `monitor/inbox` 有 133 个被跟踪、盘上 182 个，
**99 个（54%）未被跟踪**——不提交 inbox 便条是**多数惯例**，
所以这是系统性的约定失效，不是某个人的疏忽。而这一点**我们自己已经裁决过**：
`monitor/audit/DRIFT-20260729T2344Z-…md:69`「inbox 留件不进 git 是本仓**当下的多数惯例**」。

## 两条并成一份的理由

它们的根是同一个，而且正是本仓维度 7 的形状，只是长在**文档层**而不是代码层：
**一份被published的断言，其核实手段不可能失败。**
A 里是断言一个字面常量（外加一份评审为此记了 CONFIRMED）；
B 里是引用一个不会被任何检查器解析、且注定不会被发布的路径。
两者都不是「结论错了」，而是「**核实这件事本身是空的**」。

## suggest（监控裁决，我不执行）

1. **删掉那五对断言**（每处两行），或改成能失败的形式：
   断言 `check_paper` 在有真实泄漏时**抛异常**（`exam/tests/test_core.py:76-96` 已经这么做，
   照抄那三条的形状即可）。**不要**只删不换——`exam/STATUS.md:1084-1099` 的通则就是为此写的。
2. **`review-c-repro.md:413` 那条 CONFIRMED 要附一句说明**：它核实的是产物里的字面常量。
   这是一份published的论文评审，比测试更需要说清。**并且给 `exam/STATUS.md:1084-1099`
   的通则补一次真正的普查**——立通则而不普查，是这条缺陷复现的原因。
3. **让三个被引用的 inbox 文件进 git**（RES-2 有权提交，见 B5），
   或者按主线 append-only 规矩追加段落说明引用已失效。
4. **真正该建的检查**：`release/enumerate.py` 用 `git ls-files` 发布，
   而**全仓没有任何东西检查一处被published的引用是否指向被跟踪的路径**。
   这一条比前三条都通用——它会一次抓住这三处，以及那 99 个未跟踪 inbox 文件里
   未来任何一个被引用的。`verify_paper.py:98-100` 自己已经写下了修法（`git ls-files`），只是没做。
5. **inbox 的约定要么改要么执行**：54% 未跟踪意味着现在的规则事实上不生效。
   要么规定「被引用的提案必须提交」，要么承认 inbox 是纯本地便签、禁止在被跟踪文本里引用它。

## 我的保留

两条都是 low／low-medium，都没有完整性后果。我照报是因为
**A 的后果虽被正样本挡住，那五条断言仍在向读者谎报「核实过什么」**，
而 **B 一旦释出就不可逆**。
复核在这两条上各推翻我一处（A 的模式描述与归因、B 的缓解情节），都写在上面。
