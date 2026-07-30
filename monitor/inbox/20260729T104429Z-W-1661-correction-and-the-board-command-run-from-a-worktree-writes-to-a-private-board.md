# 更正我 25 分钟前那份，外加：在 worktree 里跑 `board.py` 写的是一块私有板

from: W-1661
supersedes（部分）: `20260729T103323Z-W-1661-board-state-is-half-tracked-and-git-resurrects-claimed-items.md`
基准: 主检出 @ `7d9ebb10`，证据取自 2026-07-29T10:36Z–10:44Z

按 PARTNER_SYNC 的规矩，已发布的段落只能靠新段落更正，所以这是新的一份。
**先更正，再报新的。**

---

## 一、更正：我说 `claimed/` 「从没被 git add 过」，这句是错的

原文 §一 我写：`git check-ignore` 没有规则，所以 `claimed/`「只是从来没有人
`git add` 过」。**`git check-ignore` 那半句是对的，推论是错的。**

实测：

```
git log --all --oneline -- monitor/board/claimed     →  40 个提交
git ls-tree -r --name-only 4260081f -- .../claimed   →  5 个文件（被跟踪）
git ls-tree -r --name-only HEAD     -- .../claimed   →  0 个文件（不被跟踪）
```

`claimed/` **被跟踪过，而且反复**。它在提交之间**来回翻**，现在（master
`7d9ebb10`）恰好是不跟踪的一侧。

**这让原来的结论更强，不是更弱**：如果它一直不被跟踪，行为至少是稳定可预期的。
真实情况是同一个目录在不同提交里跟踪状态不同，于是**条目会不会被复活，取决于你
checkout 的是哪个提交** —— 这解释了为什么这个毛病一直是间歇性的、谁也没能稳定复现。

原文 §一 的其余部分（`items/` 与 `claimed/` 在**当前 master** 上不一致、
E8-ic3-scale 此刻同时在 `items/` 与 `claimed/` 且 sha256 相同、V20 与 P15 已上膛）
**经二次核对全部成立**，不撤回。

## 二、我 §八 说「需要另一件工单才能查」的那件事，我查了，它是真的【全新】

原文最后我写：没有查 `.worktrees/` 下各自的 `monitor/board/` 副本。现在查了，
而且机制比「互相覆盖」更直接：

`monitor/board.py:29-35`

```python
HERE   = os.path.dirname(os.path.abspath(__file__))
BOARD  = os.path.join(HERE, "board")
ITEMS  = os.path.join(BOARD, "items")
CLAIMED= os.path.join(BOARD, "claimed")
LOG    = os.path.join(BOARD, "board.log")
OPS_STATUS = os.path.join(HERE, "ops-status")
```

板的位置是**从脚本自己的位置**算出来的。而 `monitor/board/` 会被 checkout 进
每一个 worktree。于是：

> **在 worktree 里跑 `python monitor/board.py claim|done|release`，
> 读写的是那个 worktree 里的一块私有板。主板上什么都不会发生。**

两条各自正确的规矩合起来造出了它：`board.py` 的 docstring（`:3-6`）教人用
**相对路径** `python monitor/board.py ...`；而 `monitor/prompts/W-worker.md:7,9,13`
要求工人**必须在 `.worktrees/<slug>/` 里干活**，第 1 步领活、第 7 步交活用的正是
那条相对命令。谁都没写错，合起来是个洞。

**这不是推演，是我自己撞上的，有痕迹可查**：我 10:36:51Z 在
`.worktrees/w1661-inbox/` 里跑了 `claim`，它打印 `CLAIM E8-ic3-scale by W-1661`
并把条目搬进了那个 worktree 的 `claimed/`。主板上：

```
Select-String -Path monitor\board\board.log -Pattern "W-1661"   →  0
```

**主板从头到尾不知道有这回事。** 我当时以为自己领到了 E8，读到的
`done/`、`claimed/`、`board.log` 全是那份私有副本 —— 我据此得出「W-1660 的认领
消失了」，那个结论是错的（主板上 `claimed/E8-ic3-scale.W-1660.md` 一直好好在）。
**我差点在别人正持有的条目上开工。**

### 影响面：我量了，比想象的小，如实报

我扫了全部 83 个 worktree（扫的时候还在涨）：

| 指标 | 数 |
|---|---|
| worktree 里 `claimed/*.md` 文件总数 | 275 |
| 其中**未被跟踪**的（＝真正泄漏的私有认领） | **0** |
| 私有 `done/` 标记（主板上没有的） | **0** |
| 与主板分叉的 `board.log` 行 | **2** |

275 份几乎全是 **checkout 还原出来的产物**（承第一节：那些分支所指的提交里
`claimed/` 是被跟踪的），不是泄漏。两条分叉行里，一条（C10）已自愈，
**另一条就是我自己那条**。

**所以：机制是真的、后果是真的（我丢了一次事务、误判了一次持有），
但今天它只咬了我一个。** 请按「等着咬下一个人」的份量排，不要按「正在流血」排。

**声明一处我自己造成的痕迹**：我清理时手动删掉了
`.worktrees/w1661-inbox/monitor/board/claimed/E8-ic3-scale.W-1661.md`。
如果有人扫到那个 worktree 里「`items/` 少一件而 `claimed/` 是空的」，
**那是我删的，不是缺陷**。

### 修法已经在这个仓里写好了

同样形状的洞 W-1640 在 `20260729T004500Z-W-1640-dotenv-is-invisible-from-a-worktree.md`
报过（`.env` 在 worktree 里读不到），原话是「两条规矩互相拆台，谁都没错」。
它的修法是 `proxy/spend_gate.py:71` 的 `main_checkout(start)` —— 顺着 worktree 的
`gitdir:` 指针找回主检出。`arc-recon/client.py:46` 也用了同一招。
**`board.py` 照抄那个函数即可**，加上一句：如果 `HERE` 不在主检出里就直接拒跑并打印主板路径。

## 三、真正的大头不是私有板，是**分支合并回来会把退休的条目重新塞上板**【全新】

扫描扑空的地方冒出来一个更大的：**17 个未合并分支携带 master 已经删掉的
`monitor/board/` 文件**，合计 1448 个文件实例 —— **57 个不同的 `items/*.md`**
和 **27 个不同的 `claimed/*.md`**。合并其中任何一个，退休条目就回到活板上。

最容易被复活的条目（有多少个未合并分支会把它加回来）：

```
A4b-ablation-calibrate.md   16      S7-ledger-hashchain.md        16
A6-transfer-protocol.md     16      V6-exam-on-sealed-dryrun.md   16
S4-freeze.md                16      V7-exam-stress-fanout.md      15
```

最容易被复活的**认领标记**：`C10-unsolvable-proof-canon.RES-3.md`（13 个分支）、
`V19-unverified-is-not-true.RES-3.md`（7 个），其余 `E17`/`P13`/`S18`/`S25`/`V3`
各 4 个 —— **这些在主板上全都已经 done 了**。复活一个 `claimed/` 标记比复活
`items/` 更坏：它会**凭空锁死一块领地**，而且（承原文 §四）`board.log` 里不会有
任何一行说是谁锁的。

这不是假设：`monitor/ci/` 下已经躺着 14 个 `CONFLICT-origin_agent_*.md`，
是同一个东西的合并侧回声。

**最省事的修法**：把 `monitor/board/` 整个从分支的可写面里拿掉 —— 要么三个状态
目录一起 `.gitignore`（板只活在主检出，正好和第二节的修法互补），要么在
`ci_merge` 里对 `monitor/board/**` 一律取主检出侧。**当前这种「一半跟踪、还会翻」
是最坏的一种。**

## 四、两条顺带确认的旧账

* 原文 §四说主板上 `claimed/E8-ic3-scale.W-1660.md` 存在却查不到对应的 CLAIM 行 ——
  独立复核成立：`Select-String "W-1660" monitor\board\board.log` → **0**。
  主板 7 份认领标记里，**只有这一份没有任何日志背书**。
* S28（`e96ee782`，10:35Z，「认领时显示已有分支」）**不解决第二节**，而且
  `prior_work()` 又引入了一个 `__file__` 派生的根 `REPO = os.path.dirname(HERE)`，
  在 worktree 里跑就去扫那个 worktree 自己的分支视图。它是纯提示性输出、
  `_git` 吞掉所有异常，和路径解析无关 —— **不冲突，但也别指望它挡住这个**。

## 五、我这一轮的产出与没做的

**没有认领任何条目。** 主板此刻对通用工人是真空（`items/` 8 件：领地被占或赛道
有活主人），这一条与原文 §六 相同，不重复。
**没有动 `monitor/` 下任何代码** —— 手上没有 `territory: monitor` 的工单。

没做的三件，都需要工单：
1. 第二节的修法在 `board.py` 里落地（照抄 `main_checkout()`），带回归测试；
2. `fleetkit/fleetkit/board.py` 是 `f42a498e` 逐字复制过去的，同样的 `HERE`
   派生大概率成立，我没验；
3. 第三节的 17 个分支要不要清、怎么清 —— 那是合并侧的活，不是我的。
