# r3/r4：红是它们自己的，不是 master 的；而且 r4 已经把 r3 整个吞了

utc: 2026-07-30T03:55:36Z
from: OPS-M (cycle 25)
status: **已过对抗复核，并被实质性修正——先读文末的「八、对抗复核修正」再读正文。**
正文第一至七节保留原样（不是掩饰，是让修正看得见）：机械结论站得住，
但**我给它的框架（「r3 的回归」）是错的**，而且**我漏了一半的影响面**。

## 一、我自己的假设被推翻了，这条先说

我 cycle 20 起反复怀疑、cycle 25 开机又写进 TO-MONITOR 的那条假设是：

> r3 与 r4 的红逐字相同、点的是同样三个文件，**所以红属于 master 自己**，
> 两条分支都被挂在不属于它们的红上。

**这条是错的，已被对照实验否掉。** 我当时把它写成假设而不是发现（"成不成立由命令说，
不由我说"），所以不需要撤回一个结论——但需要在这里把答案记清楚，因为我连着几轮
都在往"这些分支被冤枉了"的方向使劲，而这一次事实是反的：**r3/r4 是凭自己的本事红的。**

`release/verify.sh` 一共五个 stage，四棵树各跑全部五个（cycle 20 我只跑过五步里的一步
还管它叫"决定性一步"，那条裁决后来被推翻，这次不重犯）：

| stage | 干净 master `50e10617` | flag 记的旧 base `5439d07f` | master+r3 `211fcfb8` | master+r4 `4f8e8eb2` |
|---|---|---|---|---|
| 1 红线负控 | ok | ok | ok | ok |
| 2 红线清 + 每个文件真被读过 | ok | ok | ok | ok |
| 3 每个被跟踪文件都被归类 | **ok** | **ok** | **FAILED** | **FAILED** |
| 4 无检查项依赖未归类文件 | ok | ok | ok | ok |
| 5 S23 前后存档可复现 | ok | ok | ok | ok |
| **总判** | **绿** | **绿** | **红** | **红** |

`?`（undetermined → needs_human）这一类的计数：干净 master **0**，旧 base **0**，
r3 **3**，r4 **3**。**旧 base 也是绿的**——这一格特别值钱，它同时排掉了"红是 master
后来引入的"这个逃生出口。

## 二、机制（函数级隔离，不是读代码读出来的）

`release/check_redlines.py:250-258`（r3 的版本），`json_shaped()`：

```python
if rel.endswith(JSON_SUFFIXES):
    return True, rel.endswith(".jsonl")
try:
    text = blob.decode("utf-8-sig")
except UnicodeDecodeError:
    # `check_sealed` only reaches here for a file that already matched a
    # sealed id in its raw bytes, so ... this is not a stray binary.
    return True, True
```

那段注释的辩护是**对着 `check_sealed` 这个调用点写的**——在那里，"已经匹配到一个
封存 id"是前置条件，所以"不是野生二进制文件"成立。**r3 把 `json_shaped` 又接进了
`enumerate.classify`**，而后者对**每一个**被跟踪文件都跑一遍，没有任何 id 匹配前置。
前置条件在新调用点不成立，于是解不出的字节 → `structured=True` → 跳过 class-C 散文分支
→ 进 `_records_pairing` → 解码再失败 → 落进 `?`。

同一批字节、不同的代码、不同的判决，函数级实测：

```
MASTER  classify figures/paper/dark/figure6_bill_shape.pdf -> C
R3      classify figures/paper/dark/figure6_bill_shape.pdf -> ?
```

**这正是 r3 自己命名所指的那个缺陷（"守卫只进了两个读者里的一个"），被 r3 在上一层
原样复制了一遍。** 另：r3 的代码注释显示作者**知道**这三行，是有意让它们停在 `?` 的，
只改了措辞。所以这个红在 r3 那边是**故意的**，不是事故。

## 三、三个文件都比两条分支老，且其中一个根本不是二进制

| 文件 | 何时进树 | 经谁 | 真是二进制吗 |
|---|---|---|---|
| `figures/paper/dark/figure6_bill_shape.pdf` | `4720937f` 07-28 22:41 | `p10-figures-into-paper` | **是**（`%PDF-1.4`，647691 B） |
| `figures/paper/light/figure6_bill_shape.pdf` | 同上 | 同上 | **是**（648516 B） |
| `theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt` | `31556e0c` 07-29 07:42 | A3 战役提交 | **否，是真文本** |

三个全部**早于** r3 的第一个提交（07-29 约 16:00Z）。**文件是 master 的，判决是 r3 的。**

那个 `.txt` 值得单独说：3051 字节 / 53 行，**零个 NUL 字节**，只有 **6 个非 ASCII 字节**，
构成 3 对 GBK；`0xa1 0xec` 在 cp936 里是 `§`，还原出来是 `# LEDGER_FORMAT.md §1: ...`。
**这是本机 cp936 控制台代码页的产物，不是泄漏，也不是二进制**——一个带编码回退的读者
会正常解码并扫描它。拿 utf-8 去读 PDF 是范畴错误这条我原来说对了，但对这个 `.txt` 说错了：
它不是二进制，它是被 Windows 控制台掺了三个 GBK 字符的文本。

**顺带一条我认为值得单独立项的**：master 现在把这两个 PDF 判成 class C，证据句是
"ids used as constants, guards or narrative"——**这句话对一个 PDF 是假的**（那四个
开发堆 id 是压缩流里的字节子串巧合）。所以 master 的 C 和 r3 的 `?` **哪个更对并不显然**：
r3 的弃权可以说比 master 那句假证据更诚实。这是设计判断，在合并裁判之上，我不裁。

## 四、r4 把 r3 整个吞了——这条有直接的操作后果

```
$ git merge-base --is-ancestor e8d95c53 b5507b1f  ->  YES
```

**r4 = r3 的五个提交 + 另外三个。** 不是重复，不是兄弟，是严格嵌套。
`git diff e8d95c53 b5507b1f` 只碰 10 个文件（r4 独有），而 r3 是 504 个。

r4 是 r3 的续集，专门补上 r3 缺的那个出口："needs_human 没有出口，所以闸门永远红"。
它加 `release/RULINGS.jsonl` + `RULINGS_PROPOSED.md` + `tests/test_rulings.py`，
`load_rulings` 要求六个字段、**按内容 sha256 而不是路径**做键（签名不能漂移到没人看过的
字节上）、拒绝 class `D`、遇到畸形行直接拒绝而不是跳过。这几条设计我认为是对的。

**而 r4 现在红，是因为它的 `RULINGS.jsonl` 里一条真裁决都没有**（只有注释头）。
**它是 by design 地红着等一个人类签名。**

**操作后果两条**：
1. **合 r4 就等于合 r3。没有任何理由单独合 r3。**
2. **单独放行 r3 是有害的**——那会把"弃权"落地而把它的出口留在门外，
   于是 `needs_human` 又变成一个没有出口的坑。

## 五、没有不重新归类就能变绿的路（硬停已生效）

stage 3 的失败条件字面就是 `count(?) > 0`。所以让它变绿**按构造**就必须把这三个文件
移出 `? / needs_human`。所有候选路径都在做这件事：教 `json_shaped` 认二进制 → PDF 回到
class C（master 的答案）；给 `.txt` 加编码回退 → 也回到 C；走 r4 的 ruling 路径 → 一条
签了名的人类裁决把 `?` 行搬进 A/B/C。

**按硬停，我没有做任何修改，也没有实现任何修法。** 这三个文件的许可处置是人类的活。

**而合并裁判这边的结论是：这里不欠任何修法。** r3/r4 对着绿的 master 红是它们自己的回归，
**它们没有被挂在别人的红上**。我之前几轮反复暗示它们可能被冤枉了，这一条到此为止。

## 六、需要你的（没变，但理由现在精确了）

`r3` / `r4` 的许可证签名需要人类身份。**现在可以说得更准**：需要的不是"放行两条分支"，
是**对三个具体文件的许可判断**，而 r4 已经把接收这个判断的机器造好了
（`RULINGS.jsonl`，按内容 sha256 键，六字段必填）。所以这件事的形状是：
**人类签三条 ruling → r4 自己变绿 → 合 r4（r3 随之进去）。** r3 单独合是有害的。

## 七、还没定的

- 一个字节上撞到开发堆 id 的 PDF，正确的许可类到底是 A/B/C 还是一个新的二进制类——许可判断，不归我。
- master 那句对二进制为假的 class-C 证据句，是否值得单独立一项。
- `monitor/gates.py` 到底用什么参数调 `verify.sh`（上一跑明确列为未确定）——**对抗组正在钻这个洞**，
  因为整个对照实验的效力都压在"队列跑的树和我手跑的树是同一棵"上面。

## 产物

四个工作树留在原地供复核（都在仓库内、已 gitignore，**未提交、未推送**）：
`.worktrees/opsm25-release`（干净 master）、`opsm25-base`（旧 base）、
`opsm25-r3merge`（`211fcfb8`）、`opsm25-r4merge`（`4f8e8eb2`）。两次合并都零冲突。
零 API 花费、零网络、未读任何封存材料；密钥只以闸门自己的掩码形式 `7171...05dd (len 36)` 出现过。

---

# 八、对抗复核修正（2026-07-30T04:17:55Z）

对抗组沿六条线打，**推翻了一条框架性的、两条事实性的，并且把影响面从 3 个文件扩到 11 个。**

## 8.1 最重的一条：「r3 的回归」是错的描述，照它办会恢复一个假绿

**影响面是 11 个既有文件，不是 3 个。** master → +r3 的完整类别 diff：
**3 个 C→`?`**，**外加 8 个 C→B**。

* C = `derived-statistics → releasable-flagged`（可释出，带标记）
* B = `api-derived-compilation → **needs-written-permission**`（需要书面许可）

**r3 改的是 8 个文件的已发布许可处置，而 stage 3 对此完全沉默**——
因为它唯一的失败条件是 `count(?) > 0`。
**更糟**：已提交的 `release/MANIFEST.jsonl` 对其中 4 个仍然记着 `C releasable-flagged`，
**于是 r3 让上架清单与它自己的分类器互相矛盾，而闸门没有任何一级抓得到这件事。**
（B 从 61→69 **全部**是重新归类；新增的 19 个文件贡献 A:9、C:10、**B:0**。）

## 8.2 第二重：干净 master 的绿，是靠断言一件它从没检查过的事换来的

master 对两个 PDF 的证据句是：

> `names ARC game(s) ar25-…, g50t-…, sk48-…, tn36-… in source or prose;
> ids used as constants, guards or narrative carry no environment payload`

**这是对两个没有任何解析器打开过的二进制 PDF 做出的、正面的「可释出」声称**，
而且 "in source or prose" 对它们字面为假。

**r3 的改动恰恰是给了仪器说「我读不了这个」的能力。**
**这条红不是 r3 放进树里的缺陷，是 r3 让它显形的缺陷。**
在这里 `git revert` 买到的绿，是靠恢复那句假声称买的。

我正文第三节末尾已经把这句假证据记为「值得单独立项」，**但我把它写成了附带观察，
它其实是这件事的中心**。这是我这轮第二次把中心当成边角（另一次是 s11 的例子选择）。

## 8.3 三条事实性更正

| 我写的 | 实际 |
|---|---|
| 对照基线「干净 master `50e10617`」 | **`3d59d0a6`**（队列真正合并的基线，快两个提交）。对抗组在真基线上重跑全部三棵树：**?=0 / 3 / 3，exit 0/1/1，结论不变**，但**我的对照提交号是错的** |
| 三个文件「都早于两条分支」 | **对两个 PDF 为假**：最后触碰它们的 `a5f597dd` 在 master 上，**不被任何一条分支包含**。结论（文件是 master 的）成立，**理由不成立** |
| 「没有不重新归类就能变绿的路」（第五节） | 字面为真，**但对 r4 是误导性的重言式**：r4 自己的存档 `release/runs/20260729T1835Z-R4/verify.with-demo-rulings.txt` 结尾是 `VERIFY: green`。**在 r4 上通往绿不需要任何代码改动，只需要 `RULINGS.jsonl` 里三行签了名的裁决。** 我那句话会招来错的补救 |

## 8.4 队列的调用方式：我列为「未确定」的那个洞已经堵上

对抗组读了 `ci_merge.py:513-522` 与 `gates._runner`：队列**一次只合一条分支**、
`--no-ff`、在 `%TEMP%` 工作树里，闸门 `cwd=<wt>/release`、`PYTHONPATH=<wt>`、
`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、**无额外参数、无 MODE 覆盖**。
**队列不堆叠分支，也不用别的方式调闸门。**
且 `MODE` 无关紧要：`generate` 与 `verify` 在三棵树上给出**相同的类别计数与相同的退出码**。
cp936/`PYTHONUTF8` 假说也**死了**：每次读取都是 `open(path,"rb")` + 显式 `decode("utf-8-sig")`。

## 8.5 一条我没问、而它替我问了的释出问题（结果干净）

那个 `.txt` 里唯一像 game id 的 token 是 **`g50t-5849a774`（开发堆）**，
**21 个封存 id 一个都没出现。无事故。**
（`'§'.encode('gbk').hex()` = `a1ec`，还原出三处 `# LEDGER_FORMAT.md §…` 注释。
小瑕疵：r3 的注释说该文件「45 行」，实为 53 行。）

## 8.6 修正后的处置建议

1. **不要 revert，不要「教分类器认二进制」当作修法**——那是 8.2 说的买假绿。
2. **r4 的正确补救是三行签名，不是改代码**（8.3）。r3 单独合仍然有害，这条没变。
3. **新增一条我原来没提的、而且我认为最该先做**：
   **8 个 C→B 的重新归类没有任何闸门在看**，而它改的是「需不需要书面许可」。
   请给「分类器判决 vs 已提交 MANIFEST.jsonl」加一条对账闸门——
   否则下一次许可处置被悄悄改动时，仍然没有任何东西会说话。
4. master 那句对二进制为假的 class-C 证据句，**请单独立项**（不再是「值得考虑」）。

## 8.7 对抗组自己报的一条过程错误（值得照抄的习惯）

它第一批全闸门跑与攻击线 4 的临时补丁**撞了车**，在 r3 上产出一个假的 stage-1 失败。
**它自己发现、还原文件、重跑，并明确指出哪一份记录作废（`gate-adv-r3.txt`）。**
上面引的数字全部来自干净重跑（`gate2-*`）。

## 8.8 仍未确定

* 那 8 个 C→B 的移动**实质上对不对**（r3 声称 `theoria-arm/runs/20260728T235841Z-leg01/run.json`
  是「一份字面的 ARC scorecard 响应」——**载荷问题没人裁**）。
* r3 的 docstring 说有**十一**个文件进 B，在真基线上只有 **8** 个到达 B。差额未解。
* 两个 PDF 是否真的内嵌 environment payload（没有解压流）。
* `verify.sh` stage 5 **即使在绿的干净 master 上也会弄脏两个被跟踪文件**
  （`release/runs/20260728T234923Z-S23/{before,after}/contamination.planted.txt`）。
  `ci_merge` 把这记为「一个闸门弄脏了工作树」**但不阻断**。没追。
