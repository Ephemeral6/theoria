# A17 · provenance 扫描读哪个引用集合：先量到，再定

接 `runs/20260730T0855Z-A17-MEASUREMENT/`（原始测量，第一节已被撤回）
与 `runs/20260730T1200Z-A17-THE-STASH-WAS-INNOCENT/`（订正）。
那两份留下的问题是同一个：**该读什么，还没定；能不能真咬人，还没构造出来。**
本文件答这两个。

零 API、零花费、封存堆零接触。**本仓库里没有建任何 tag、branch、stash，
也没有删任何引用**；唯一造引用的地方是临时目录里 `git init` 出来的一次性仓库。
`python -m armtools.backfill --all` **全程未执行**。

复现：`python runs/20260731T1050Z-A17/probe_ref_set_bite.py`
（全部只读，除临时仓库外不写盘），产物 `measurement.json`。

---

## 一 先量：四种触发方式，三种成功

`runs/20260730T0855Z-A17-MEASUREMENT/` §4 拒绝在本仓库建 tag 来构造触发，
理由是对的（别人正在这里测 provenance），代价是问题悬着。
在 `git init` + 裸仓当 origin 的一次性真仓库里做，两个顾虑都没有。

固定装置：`master` 上 `base -- mainline`；离线两个提交
`unique`（arm 状态别处没有）与 `duplicate`（arm 状态与 `mainline` 相同），
造完把 `side` 分支删掉，于是这两个提交任何引用都不可达。

| 触发 | `--all` | 仅 `HEAD` | 结论 |
|---|---|---|---|
| **T1** 在 `unique` 上打注解 tag | `no_match` → **`matched`** | `no_match` | 成功 |
| **T2** 在 `duplicate` 上打注解 tag | `matched` → **`ambiguous`** | `matched` | 成功 |
| **T3** 同一提交，改用普通 branch | **`matched`** | `no_match` | 成功 |
| **T4** 在 HEAD 已可达的提交上打 tag | 不动 | 不动 | 反向对照，符合预期 |

**所以「构造不出来」这个可能的结论不成立：三种都构造出来了，各一条命令。**
T3 是本节最值钱的一条：**这件事从来不只关于 tag，是关于引用**。
任何人建一个分支、推一条远程分支，效果与 tag 完全一样。
条目标题写的是 tag，真正的面比 tag 宽。

## 二 咬到什么：`commits` 列表进了归档清单，而 check 8 是逐字节比

这一步是本轮真正的新发现，前两份都没量。

`backfill.provenance` 把 `locate()` 的**整个**回答——含 `commits` **列表**——
原样抄进 `MANIFEST.json`（`backfill.py:395`）。
而 `verify_provenance` 的 check 8 是「re-deriving every manifest reproduces it
**byte for byte**」。

于是：往某个 hash 的分组里多塞一个提交，会怎样？
不建任何引用也能量——把一张多一个提交的 table 交给 `backfill.build`，
比渲染出来的字节：

> **8 份归档清单中，8 份字节改变。**（全部带 `matched`/`ambiguous` 裁决的清单，
> 逐份验过 `matches_disk_today: True`，即改前与盘上一致。）

**所以引用集合变动不是诊断里的一处摆动，是 check 8 在一整片没人碰过的归档上翻红。**
这就是「归档产物依赖一个没有被声明为契约的外部东西」的具体价钱。

顺带一个尺度感：`20260728T025503Z-g50t-e08-fixed` 的 `commits` 有 **380** 条。
不是因为那份 run 特别，而是因为绝大多数提交根本不碰 `theoria-arm/*.py`，
于是携带父提交的 arm 子树。今天 HEAD 不在那个分组里（arm 之后被改过），
所以这个分组是封口的；能把它撑大的只有**指向旧提交的新引用**——
正好就是本条目问的那件事。

## 三 判定该读什么

`scan(refs)` 原先只接受**一个** token（整串当一个参数传给 `rev-list`），
所以任何多引用方案都要先放宽签名。已放宽（字符串仍等价于一个 token，
既有调用一个不变），然后才谈选择。

本仓库今天的实测（`measurement.json` → `today.shape`）：

| 读集 | 提交 | arm version |
|---|---|---|
| `--all` | 1425 | 68 |
| `--branches --remotes HEAD` | 1418 | **68** |
| 仅 `HEAD` | 1394 | 66 |

`--all` 多出来的 7 个提交，逐个点名（`rev-list A --not B` 直接问，不做减法）：
`refs/stash` 3 个 + `refs/original/refs/heads/agent/a3-campaign-devpile` 4 个。
非 heads/tags/remotes 的引用本仓库总共就这两条。
**这 7 个提交贡献的 arm version 是 0**（68 = 68）。

> 顺带订正一条：`runs/20260730T1200Z-...` 说「266 个工作树的 detached HEAD」
> 也是扫描输入的主体。本轮实测 `--all` 减去 branches/remotes/tags/HEAD
> **恰好等于** stash 3 + refs/original 4 = 7，工作树的 detached HEAD 一个都不在里面。
> 结论方向没变（refs/original 是主体、stash 是边角），但工作树那一项不成立。

四个候选，每个答错在什么情况下：

* **仅 `HEAD`** — 排除掉 tag、别人的分支、stash、一切。答错在：
  实测**丢掉 2 个只存在于其它分支上的 arm version**。一次记录了其中之一的 run
  会被告知「executed against a working tree that was never committed in that
  state」——那是一句关于诚实性的指控，不该由「谁今天站在哪个分支上」决定。
  **否决，理由是量到的，不是口味。**
* **`origin/master` 第一父链** — 最可复现（任何克隆算出同一答案），
  但 2026-07-30 已量到它把 `20260729T004020Z-leg01` 从 `ambiguous/4`
  打成 `no_match/0`：**在分支合并之前，它指控每一次尚未落地的 run**。
  归档是在战役**进行中**写的，所以这不是边角情形，是常态。**否决。**
* **清单自记的显式引用集合** — 可复现且不受别人影响，代价是清单要加一个新字段，
  于是自带一次 17 份归档的迁移。**这轮不做**，理由见下。
* **`--branches --remotes HEAD`（选定）** — 见下。

### 选定：`DEFAULT_REFS = ("--branches", "--remotes", "HEAD")`

写成模块常量，因为这正是重点：以前的输入是 `--all`，
即「这台机器上 `refs/` 下此刻恰好有什么」——不是任何人声明过的东西，
也不是任何人控制得住的东西。

* `--branches`：主体。
* `--remotes`：一个新克隆一条本地分支都没有，只有 `origin/*`；
  少了它，克隆里每一条裁决都会变成 `no_match`。
* `HEAD`：脚下这棵树。正常状态下它是 `--branches` 的子集
  （实测 `rev-list HEAD --not --branches --remotes` = 0），
  留着是为了 detached 工作树里刚做的 run 仍然锚得住。
* **`--tags` 有意不在里面**——那正是条目点名的风险（任何人打个 tag 就改了扫描输入）。
  实测：本仓库**没有任何提交是只经由 tag 可达的**（`rev-list --tags --not
  --branches --remotes HEAD` = 0），所以排除 tag 今天**一个提交都不减**。

「今天」这个词在上一句里承重，所以不能靠它长期为真：`scan()` 每次**顺手再量一遍**，
把 `excluded["--tags"]` 放进返回值。哪天它不是 0 了，读者立刻看得见
支撑 `DEFAULT_REFS` 的那段论证已经过期。用 `rev-list --count A --not B` 直接问，
不用两个总数相减——**相减正是 2026-07-30 那次归因错误的成因**
（`runs/20260730T1200Z-...` §3 的判据：能直接问就直接问）。

### 这个改法**没有**修好什么，照实说

答案仍然是仓库分支集合的函数：同事推一条够到旧 arm 状态的分支，它照样动。
要让答案变成常量，需要每份清单记下自己是在哪个引用集合下推导的——
新字段，因而是 17 份归档的迁移。**本轮有意不做**，因为这个改法之所以被选中，
部分正是**它一份清单都不用重写**；迁移是另一个决定，该带自己的机械守卫。

## 四 归档清单：一份都没重写

* `today.rows`：17 份清单在 `--all` / `HEAD` / `--branches --remotes HEAD`
  三个读集下裁决**逐份完全相同**。
* 换默认值后 `python -m armtools.verify_provenance` = **10/10**，
  check 8「byte for byte」仍绿。
* `git status` 下 `runs/*/MANIFEST.json` 无改动。
* `python -m armtools.backfill --all` 未执行。

**这条修法不需要动任何归档清单**——条目里希望的那个结果，此处明确写出来。

## 五 测试：真 git 仓库，且带反向对照

`theoria-arm/tests/test_armversion_read_set.py`，12 条。
每一条涉及引用的都建**真**仓库（`git init` + 裸仓当 origin + 真提交 + 真 tag）：
`scan()` 就是三个 `git` 子进程，套一层假 git 只能测到那层假壳。

反向对照是这个文件的重点。写一个排除 tag 的读集、再只测「tag 被排除了」，
在 `scan()` 被改坏成返回空的时候**同样会绿**。所以两个方向都测：

* 在读集已经够得到的提交上打真 tag，答案必须**逐字节不动**
  （连 `commits` 的顺序都比）；
* 指向不可达提交的 **branch** 必须**被看见**——否则这个改法是用假的
  `no_match` 指控换来的稳定；
* 指向不可达提交的 **tag** 必须**被排除**，且**排除计数器必须察觉到它**
  （0 → 1）；两半都断言，因为「tag 被排除了」只有在证明了它本来会被算进去
  的旁边才有意义。

## 六 交付前在新工作树里复跑

条目要求「在一棵不含未跟踪产物的新工作树里复跑闸门」，
理由是「今天正是这条差别把一条 24 小时的红藏了起来：check 8 在造出产物的机器上绿、
在 `ci_merge` 建的克隆里红」。结果记在本目录的 `gates.txt`。
