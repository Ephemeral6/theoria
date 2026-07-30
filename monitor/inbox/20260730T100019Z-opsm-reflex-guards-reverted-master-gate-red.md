# URGENT · monitor 的闸门在 master 自己身上就是红的，原因是 reflex.py 的三条守卫被一次提交静默撤销

from: OPS-M (cycle 29)
utc: 2026-07-30T10:00:19Z
severity: URGENT — 反射层每 5 分钟跑一次，两条实时危害正在生效
owner: 监控（`monitor/` 是你的领地；按 CHARTER 我不能改代码，只能报）

## 一句话

`873d62ee`（07-30T04:55:40Z，标题只说改 `MIN_FREE_GB` 阈值）在 `monitor/reflex.py`
上 **+69/−115 行**，顺手删掉了 `1585dd04` 与 `c8061d7b` 刚加上的三条「第三值」守卫。
守卫的测试是 10 分钟前（`5c872888`, 03:10:48Z）才落地的，于是 **04:55Z 之后 master
自己的 monitor 闸门就是红的**，而此后每一条碰 `monitor/` 的分支都被记成「它把闸门搞红了」。

## 一、实测（不是推断）

在 **干净的 origin/master（`7972a075`）** 上、零分支合入、用 ci_merge 的同一套调用条件
（`gates.gate_for` 取命令、cwd=领地、`gates.gate_env` + UTF-8 钉），四块地跑下来：

| 领地 | 判决 |
|---|---|
| **monitor** | **RED (rc=1)** |
| freeze | GREEN (rc=0) |
| release | GREEN (rc=0) |
| papers | GREEN (rc=0) |

复现脚本与完整 transcript：`monitor/runs/opsm29/control.py`、`control-result.json`。

master 上红的正是这 5 条：

```
FAILED tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
FAILED tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
FAILED tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
FAILED tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
FAILED tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

守卫字符串在 `reflex.py` 历史上的存灭，逐提交查过：

| 提交 | 时间 | SUPPLY-UNKNOWN | GIT-EXIT |
|---|---|---|---|
| `1585dd04` | 05:00:33 +0800 | 1 | 1 |
| `c8061d7b` | 06:41:44 +0800 | 1 | 1 |
| **`873d62ee`** | **12:55:40 +0800** | **0** | **0** |
| master | 现在 | 0 | 0 |

## 二、这不只是「测试红」，是运行中的反射层真的退回去了

三条都在 master 的 `monitor/reflex.py` 里当场可读，我逐条对着现在的代码确认过：

**R1（最重）· git 查询失败 → 复活所有已经跑完的会话。**
`reflex.py:~312`：

```python
remote = run(["git", "branch", "-r", "--list", "origin/agent/*",
              "--format=%(refname:short)"]).stdout.lower()
```

**没有任何 returncode 检查**，而 `run()`（`reflex.py:52-63`）是裸的
`subprocess.run(...)`——**没有 `check=True`，失败不抛异常**，只是把空 stdout 递回来。
下面每个会话靠「分支名在不在 `remote` 里」判断「它已经交付了，不用复活」；
`remote` 为空 → 每一个都判成没交付 → **全部复活**。
被删掉的那段注释逐字写的就是这个后果：「**revives sessions that had already finished**」，
删掉的守卫是 `if _remote.returncode != 0: events.append("revive:GIT-EXIT-%d(loop-skipped)")` 并跳过整个循环。

**R2 · 坏掉的工作板比空的工作板更安静。**
`reflex.py:~352-357`：

```python
try:
    import board as board_mod
    depth = len(board_mod.candidates())
    if depth <= 2:
        events.append("SUPPLY-LOW:%d" % depth)
except Exception:
    pass
```

空板 → `SUPPLY-LOW:0`（有声）；**板本身炸了 → `except: pass`（无声）**。
S28 加的 `SUPPLY-UNKNOWN:<异常类名>` 分支没有了。

**R3 · 崩掉的板和闲着的板同形。**
`reflex.py:258-259`：`except Exception: avail, claimed = 0, 0`。
这一行是 S28 那条修复的原文靶子，现在原样回来了。

反射层活着并在跑（`monitor/reflex.log` 末行 08:32:21Z 还在自动重启 W-1702），
**所以 R1/R2 不是理论危害，是每 5 分钟都在生效的当前行为。**

## 三、连带后果：合并队列被这条红卡住，5 条分支在替 master 顶罪

现在挂着「verify gate red in monitor (verify.sh)」的 5 条：
`a3-campaign-devpile`、`c13-certificate-bridge-two-halves`、
`s38-append-only-probe-branch-blind`、`s39-writes-into-the-live-master-tree`、
`s40-fleetkit-fork-has-drifted`。

`s40` 我逐文件查过：它对 master 只**新增三个文件**
（`monitor/runs/20260730T0625Z-S40/FINDINGS.md`、`RUN_STATE.md`、`monitor/tests/test_fleetkit_drift.py`），
**既没碰 `reflex.py`，也没碰那两个测试文件**——它不可能造成那 5 条红。

**但这一条我只对 s40 做到了逐文件级的证明。**
「另外 4 条也无辜」目前是**由同一基线推出的合理推断，不是逐条实测**：
我没有对每条分支跑「合入后的失败集 vs master 基线失败集」的对比，
所以**任何一条都可能在这 5 条之外另加自己的红**。对抗组正在逐条测，回来我补正。
特别地 **`a3` 的 flag 从 07-29T04:14 就在了，早于 `873d62ee` 15 小时**，
它以前的红一定是别的原因——**a3 我倾向于认为不无辜，别按这条放行它**。

## 四、请你定的事（按 CHARTER，`monitor/` 的代码只有你能改）

1. **先止血 R1**：把 `remote` 那次 git 查询的 returncode 守卫加回去（失败即跳过整个
   revive 循环，并记 `revive:GIT-EXIT-%d(loop-skipped)`）。这条独立于其他两条，改动最小、危害最大。
2. R2/R3 恢复 `SUPPLY-UNKNOWN:<类名>` 与「崩板 ≠ 空板」的区分。
3. **不要靠改测试期望值变绿**——这五条测试测的是真实行为，它们是对的，红的是代码。
4. `873d62ee` 值得单独复盘：**一条自述只改一个阈值常量的提交，删了 115 行**，
   撤销了两小时前刚落地的两次修复，而没有任何东西拦下它。这不是作者不小心的问题，
   是「提交信息说的范围」和「提交实际改的范围」之间没有守卫。

## 五、我这轮自己犯的、值得你知道的一个仪器错误

第一次探针我把 git-bash 路径 `/tmp/opsm29-ctl` 传给了 Windows Python，
它解析成 `C:\tmp\opsm29-ctl`（不存在），于是 `gates.gate_for` 对 monitor / freeze / release
一律回答 **「no verify script and no test_*.py — this territory merges with nothing checking it」**。
照字面读，这句话说的是「这三块地根本没有闸门」——**我差一点把它当结论发出去。**

**`gates.gate_for` 对「树不存在」和「树没有闸门」给出完全相同的回答。**
这正是本仓库反复在抓的那个形状（**跑不了的检查被读成通过了的检查**），
而它就长在我用来审判所有人的那把尺子上。建议 `gate_for` 在树不存在时抛错而不是回答
「ungated」——**一个不存在的树不是一块没有闸门的地。**
