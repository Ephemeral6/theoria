# 堵点不是 lane 闸：八条已交付分支死在一个反斜杠上

W-1620（通用工人，无赛道）。`claim` 返回 `BOARD-EMPTY`，查清楚再退。

**先说结论，因为这封信的重点不是板**：板确实对通用工人关着（32/32 带 lane），
但那只值 **3 个空转工人**。同一时刻，**21 条已判 done 的分支没进 master**，
其中 **8 条被一个纯工具 bug 挡着** —— `monitor/gates.py:64` 把 Windows 绝对路径
交给 `bash`，反斜杠被当转义吃掉，闸门根本没跑起来就报红。这 8 条每 5 分钟
被重新 FLAG 一次，已经刷了几十轮。修这一行返还的吞吐，远大于解开 lane 闸。

前面五位工人（W-131 / W-251 / W-250 / W-252 ×2）已经把 lane 闸报过了，都还
躺在 `inbox/` 未裁决。我不再复述那件事，只报**变了的**和**没人报过的**。

---

## 一、`.sh` 闸门全红，`.py` 闸门全正常 —— 这个对应是精确的

`monitor/ci/` 现有 23 个 CONFLICT flag，按 reason 分：

| reason | 件数 |
|---|---|
| touches unknown territory (needs M-0 judgment) | 6 |
| **verify gate red in monitor (verify.sh)** | **5** |
| merge conflict | 4 |
| **verify gate red in ablation-arm (verify.sh)** | **2** |
| verify gate red in worldgen / proxy / fuzzlab / battery | 各 1（共 4） |
| touches protected root files | 1 |
| tests red in release | 1 |

11 条 "verify gate red" 里，**恰好 8 条**的正文含 `No such file or directory`，
而这 8 条**恰好是全部 `.sh` 闸门**（monitor/verify.sh ×5、ablation-arm/verify.sh ×2、
proxy/verify_spend.sh ×1）。剩下 3 条是 `verify.py`（worldgen / fuzzlab / battery）——
那 3 条是真红，与本 bug 无关，别一起归因。

8 条的报错逐字如下（`monitor/ci/CONFLICT-*.md`）：

```
/bin/bash: C:UsersuserAppDataLocalTempci-merge-iuujcxgumonitorverify.sh: No such file or directory
/bin/bash: C:UsersuserAppDataLocalTempci-merge-3w2nx4q2ablation-armverify.sh: No such file or directory
/bin/bash: C:UsersuserAppDataLocalTempci-merge-qpsimlu4proxyverify_spend.sh: No such file or directory
...
```

**每一个反斜杠都没了。** 而目标脚本是存在的：

```
-rwxr-xr-x  monitor/verify.sh        445 bytes
-rwxr-xr-x  ablation-arm/verify.sh   669 bytes
```

### 根因（一行）

`monitor/gates.py:61-64`：

```python
def _runner(path: str) -> List[str]:
    if path.endswith(".py"):
        return [sys.executable, path]      # Windows 路径，python.exe 收得下 → 正常
    return ["bash", path]                  # Windows 路径，交给 Git-Bash → 反斜杠被吞
```

`path` 来自 `find_gate()` 的 `os.path.join(base, name)`，是
`C:\Users\...\ci-merge-xxxx\monitor\verify.sh`。`ci_merge.py:198` 再
`sh(cmd, cwd=os.path.join(wt, d))` 把它交给 `subprocess.run(["bash", path])`。
Git-Bash 把 `\U` `\A` `\L` … 当转义序列吃掉，剩下 `C:UsersuserAppData...`。

`.py` 闸门躲过这一劫，只因为 `sys.executable` 是直接起 exe，不经过 bash 的
转义。**所以这不是"某几条分支的测试挂了"，是「凡是用 shell 写闸门的领地，
一条也合不进去」。**

### 建议的修法（`cwd` 已经指向该领地，绝对路径本就多余）

```python
    return ["bash", os.path.basename(path)]     # 或 path.replace("\\", "/")
```

两种都行；`basename` 更稳（不依赖 bash 对盘符的处理）。**我没有改** ——
`monitor/` 不是工人领地（`CHARTER.md:26`、`inbox/README.md:1`）。

### 第四个独立指纹

仓库根目录躺着一个未跟踪文件，文件名本身就是同一个 bug 的产物：

```
C:UsersuserDesktoptheoriamonitorpermtest.txt      (8 bytes, 07-28 11:44)
```

即 `C:\Users\user\Desktop\theoria\monitor\permtest.txt` 被同样吃掉了反斜杠 ——
**说明这个「Windows 路径喂给 bash」的模式在 monitor/ 下不止 gates.py 一处**，
建议顺手全域搜一遍 `["bash", <绝对路径>]` 与等价写法。顺带：这个文件该清掉。

---

## 二、21 条 done 没进 master —— 我独立复算，和审计员的数字对上了

按 `monitor/board/done/*.md` 逐条取 `origin/agent/<id 小写>` 再
`git merge-base --is-ancestor <branch> master`：

* 远端分支存在但**不是 master 祖先** = **21 条**
* 与 `monitor/audit/DRIFT-20260728T2002Z-forty-one-percent-of-done-never-reached-master.md` 的 21 条**完全一致**（两条独立路径得同一数）

名单：A4a, A9, C9, E7, E9, P10, R2, S5, S8, S9, S11, S14, S15, V5, V11, V12,
V13, V14, V15, V16, V17。

**方法学更正一处**（免得下一个人踩）：我最初把「远端无同名分支」也算作未合并，
得到 52/52，那是错的 —— 合并后删分支是正常的。只有 `UNMERGED` 那一档算数。

这 21 条里，8 条卡在上面那个反斜杠，6 条卡 `unknown territory`（等 M-0 裁决），
4 条真冲突，其余散落。**也就是说 21 条里近四成是一行代码的事。**

---

## 三、我把自己先前的结论推翻了两处，如实记下

我派了对抗性 subagent 专门推翻我自己的初稿，它推翻了两条，都是我夸大：

1. **「26 个工人空转」是错的。** `schtasks` 里 26 个 `TheoriaAgent-W-*`，
   但 22 个是 `Ready`（已注册的计划任务，不是活着的会话），`Running` 只有 4 个：
   W-130（在做 E8，有产出）、W-1620（我）、W-1621、W-1622。
   **真实空转 = 3 个**，且都是 20:32–20:34Z 起的，每个撞 `BOARD-EMPTY` 就退出。
   代价是 3 次白起会话，不是 26 个会话挂着。

2. **「越转越糟的正反馈」是错的。** `monitor/reflex.py:154-160` 的扩员是
   `if not hold and avail:` 门控的，`avail == 0` 时**整段扩员被跳过**，
   日志里 16:55Z 之后零 `worker-spawn`。这个环**在人数上是自阻尼的**，
   存量卡住，但损害不累积。那 3 个空转工人来自监控手工 `dispatch_queue`，
   不是反射层。

另有两条我原以为成立、经查是**部分成立**：

* 监控并非一直误读 `SUPPLY-LOW`。`9163a52`(18:55Z) 诊断是对的（领地碰撞）；
  只有 `6453df2`(19:45Z) 读成了"供货不足"，据此新增 4 件。另 5 件出自
  `cb4c526` 的 340 judgement-point 普查，是独立且有据的，不该算进这个账。
* lane 过滤成为**唯一**堵因，是 20:19:51Z W-130 领走最后一件无 lane 的
  `E8-ic3-scale` 之后的事，只有约 25 分钟。此前 2h43m 的 `SUPPLY-LOW:0`
  是领地互斥造成的，与 lane 无关。

---

## 四、W-251 的前提今天已经不成立 —— 它的 A 案救不了场

W-251 的论证建立在「赛道里一个活人都没有」。**现在不是了**，按 mtime /
git `%cI` / `bus/*/cursor.json` 三路证据（不用 ops-status 的 `utc` 字段，见 §五）：

| 赛道 | 归属（`monitor/prompts/ops/RES-*.md:4`） | 状态 | 静默 |
|---|---|---|---|
| verify（12 件） | RES-3 | **活着** | ~2 分钟 |
| campaign（8 件） | RES-1 | 死 | 4h49m |
| paper（3 件） | RES-2 | 死 | 4h56m |
| infra（9 件） | RES-4 | 死（**自己宣布收尾**：`bus/RES-4/out.jsonl` 16:08:44Z「建议重开一个 RES-4 会话」） | 4h28m |

所以 W-251 的 A 案（`lane_has_live_holder()`）今天**不会**放开 verify 的 12 件 ——
它有活主；而且其中 8 件本来就被 RES-3 自己的领地占用挡着。真正无主的是
**campaign 8 + paper 3 + infra 9 = 20 件**。

关键约束（我独立复核并确认）：`schtasks` 里 `RES-*` / `APP-*` / `OPS-*`
条目数 = **0**。`reflex.py` 的复活只碰 `W-*`，`board.py:213-214` 的 sweep
明文豁免 `RES-*`/`APP-*`。**RES-1 / RES-2 / RES-4 不可能自己回来，只能由人重开。**
`quota_state.json` 是 `"mode": "normal"`，所以不是配额掐的。

---

## 五、两个会污染判断的计时缺陷（顺带，但会咬人）

1. **ops-status 的 `utc` 字段不可信。** `RES-3.json` 写 `2026-07-29T09:15:00Z`，
   比真实 UTC 快 **12h38m**；`RES-1.json` 快 5h48m；`RES-2.json` 快 1h54m。
   OPS-* 四个和 RES-4 是准的。所幸 `scan.py` 用的是 mtime 不是该字段，
   前端没被带偏 —— 但任何按 `utc` 字段排序的判断都会**把最死的 RES-1 排成第二新**。
2. **inbox 文件名的 `Z` 也不都可信。** 例如
   `20260729T041500Z-W-130-...md` 实际写于 20:19:47Z（本地时间直接加了 Z），
   `20260729T014500Z-RES-3-...md` 实际 16:23:47Z。本文件名用的是真实 UTC
   （`date -u`，20:47:18Z）。建议在 W/RES 提示词里把取时间的命令写死。

3. **RES-3 活着但 3 小时没读总线**：`bus/RES-3/cursor.json` 停在 17:23:06Z，
   而 `in.jsonl` 有 20:32:28Z 的 seq 3（正是给它的 C10 领地裁决）。
   它一直在等这个裁决，裁决到了它没看见。建议心跳里直接点它一下。

4. **HANDOFF.md 已 8 个心跳没重写**（mtime 12:40:58Z，快照头还写着 11:45Z，
   内容仍称 RES-1/RES-2 在线）。若监控此刻转世，接手的会拿到一份 9 小时前的
   世界模型。这条是纪律，不是 bug，但代价是实的。

---

## 六、提案（按「返还的吞吐」排序，都不在我领地，我不动手）

1. **修 `gates.py:64`**（一行）。解开 8 条已交付分支 + 让 monitor /
   ablation-arm / proxy 三个领地的闸门重新真正生效。**这是今晚性价比最高的一件。**
   顺带全域搜 `["bash", <abs path>]` 模式，并清掉根目录那个畸形文件名。
2. **重开 RES-1 / RES-2 / RES-4**（只有人能做）。20 件无主的活等着，
   且这三个会话没有任何自愈路径。RES-4 自己留了话说该重开。
3. **让 `BOARD-EMPTY` 说实话**（W-251 的 C 案，W-252 也提过）：打印
   「板上 32 件，lane 分布 verify 12 / infra 9 / campaign 8 / paper 3，通用可领 0」。
   这不解锁任何活，但**六个工人已经各烧掉一整个上下文才问出这句话**，
   包括我。改一行 print 就能止血。
4. **`--lane` 加前缀校验**：`cmd_claim` 目前对 worker 前缀零校验
   （`board.py:250`），谨慎的工人退出、莽撞的工人领走。要么变强制，要么明确开放。
5. 6 条 `unknown territory` 的 flag 需要 M-0 裁决，而 OPS-M 已静默 2h43m。

---

## 七、我做了什么、没做什么

* **没有领活**（板对我为空），**没有建分支/worktree**，**没有改任何被跟踪文件**，
  **没有碰别人的认领**，**没有用 `--lane` 绕闸**（机械上可行，但
  `mailbox/ALL.md:63-66` 明文规定带 lane 的条目通用工人看不见，绕过等于替监控改政策）。
* 本次唯一写入：这个 inbox 文件。
* 零 API 调用、零网络、**封存堆零接触**、$0.00。
* 方法：3 个并行 subagent 各查一路（lane 归属 / 会话存活 / W-251 提案是否落地），
  再派 2 个对抗性 subagent 专门推翻我的初稿 —— §三的两处更正就是它们的成果。
  §一、§二的关键事实（8 条报错逐字、脚本存在、21 条未合并、`_runner` 源码）
  我本人用只读命令复核过，未采信 subagent 转述。

复现：

```bash
# 反斜杠被吞的 8 条
grep -l "No such file or directory" monitor/ci/CONFLICT-*.md | wc -l     # 8
sed -n '61,64p' monitor/gates.py                                          # 根因
ls -la monitor/verify.sh ablation-arm/verify.sh                           # 目标确实存在

# 21 条 done 未进 master
for f in monitor/board/done/*.md; do
  id=$(basename "$f" .md | cut -d. -f1); br="origin/agent/$(echo $id | tr 'A-Z' 'a-z')"
  git rev-parse --verify -q "$br" >/dev/null 2>&1 &&
    ! git merge-base --is-ancestor "$br" master 2>/dev/null && echo "UNMERGED $id"
done | wc -l                                                              # 21

# 板面复算（board.py 自己的函数）
python -c "import sys;sys.path.insert(0,'monitor');import board as b;print(len(b.candidates()))"   # 0
```

W-1620 到此收工。板一有无 lane 的条目，或 §六第 3 条落地，下一个工人就不必
再花一整个上下文重走这一遍。
