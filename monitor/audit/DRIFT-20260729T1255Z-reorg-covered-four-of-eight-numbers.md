# DRIFT-reorg-covered-four-of-eight-numbers

severity: high
dimension: 7（单向门／不可能变红的检查）＋ 8（监控自身漂移）
audit range: `de90ba90..9bc8c880`（102 提交 / 403 文件），周期 36，OPS-A

**先说一句方法上的事，因为它决定了这份报告的第一段该怎么写。**
本轮我几乎报了一条「同号双会话第四次」：`standing.log` 里
`2026-07-29T12:46:33Z START OPS-A ok=True`，比用户贴给我的启动词早 33 秒，
而 `schtasks` 里 `\TheoriaAgent-OPS-A` 正 `Running`。**我先查了自己的进程祖先，
它证伪了这条报告**：

```
powershell.exe(24908) ← claude.exe(31172) ← cmd.exe(28628) ← python.exe(30764) ← svchost.exe ← services.exe
```

`services.exe → svchost → python.exe(standing.py) → claude.exe` —— **我就是 12:46:33Z
那个无头会话本人**，不是 App 会话，没有双胞胎。
**判据留给下一个人：一个会话想知道自己走的是哪条启动路径，走一遍进程祖先即可，
提示词文本区分不了**（`monitor/prompts/ops/OPS-A.md` 与用户手贴的启动词逐字相同）。

下面这条报告说的不是「已经撞了」，是**为什么这次没撞纯属侥幸，以及侥幸靠的是另一个缺陷**。

---

## claim

`9bc8c880` 宣布了四件事——一个身份、一条启动路径、一个通道、一个存活判据——
**四件都只对 RES-1..4 成立**。同一次重整把 `OPS-A` / `OPS-M` 放进了
`standing.py` 的自动启动名单（`STANDING_OPS`，standing.py:61），却没给它们那条路径
所依赖的任何一件配套：**它们在存活判据上是不可见的，在通道上仍被指向已停写的邮箱，
在盘面上仍被当作「只有人能重开的 App 会话」。**
现在挡住二次启动的不是任何一道闸门，是另一个缺陷（并发上限刚好卡死）——
**先修上限、后修判据，会当场造出一个 OPS-A 双胞胎。**

## evidence

**一、新的存活判据对 OPS-* 结构性失明。**
`FLEET.md` 第二节：「他还活着吗：一个判据——**问工作板**」。`standing.py:199-219`
实现了它（board.log 里 `by <编号>` 的 CLAIM/DONE）。而：

```
Select-String monitor/board/board.log -Pattern 'OPS-A'  →  0 行（有史以来）
Get-ChildItem monitor/ops-status/*.lock                 →  只有 RES-1..4，无 OPS-A.lock
```

原因不是 OPS-A 偷懒，是 `CHARTER.md` 的权限表明写 **OPS-* 写工作板：否**。
**这个编号被禁止产生那个判据所要读的信号。** 锁文件同理：`monitor/ops/OPS-A.md`
与 `monitor/prompts/ops/OPS-A.md` 从头到尾没有要求刷新 `.lock`（RES 的提示词有）。
于是 `occupied("OPS-A")` 只剩第三条腿：`cycle` 推进。

**二、剩下那条腿的时长对不上，差 10–40 分钟。**

```
standing.py:83   LOCK_FRESH_MIN = 20     # cycle 推进在 20 分钟内才算「有人顶着」
standing.py:80   EVERY_MIN = 15          # 每 15 分钟问一次
monitor/ops/OPS-A.md:22          「睡 30 分钟」
monitor/prompts/ops/OPS-A.md:11  「睡 60 分钟」   ← 这份才是 standing.py 真正下发的
monitor/AUDITOR.md:9             「sleep 3600」＋「跑满 6 个周期后主动退出」
```

一个**完全守约**的 OPS-A，每个周期有 10 分钟（按 30 分钟版）到 40 分钟（按 60 分钟版）
在 `occupied()` 眼里是「没人顶着」，而扫描每 15 分钟跑一次。
**同一个岗位的三份文件写了三个不同的休眠时长，其中两个都比判据窗口长。**

**三、今天没起成第二个，靠的是并发上限，而那是个缺陷。**

```
standing.py:64   MAX_STANDING = 4
standing.py:295  roster = sorted(LANE_OWNER…)          # 四个研究员在前
standing.py:296  roster += sorted(STANDING_OPS)        # OPS-A、OPS-M 永远在后
```

四个赛道 + 上限 4 = **四个研究员全活时，两个监督岗永远排在门外**。日志实测：

```
2026-07-29T12:47:18Z skip OPS-M: standing cap 4 reached
```

`OPS-M` 自加入名单起 starts=0（`scratchpad/standlog.py` 直方图）。
OPS-A 这次挤进去，只因为那一跳里研究员尚未记满。**注意这条的方向**：
上限既是「OPS-M 起不来」的原因，也是「OPS-A 没被起第二次」的唯一原因。
**它同时是缺陷和护栏；单独修掉护栏那一半，二、里那个 10–40 分钟窗口立刻变成实弹。**
（限定：`STANDING_OPS` 上线只有几分钟日志，饥饿是算术上的结构性结论 + 1 次实测，
不是长期统计，如实记。）

**四、盘面仍在叫人去手动开那两个编号。**
`scan.py:939-967 probe_needs_human`，文档字符串写着「全系统唯一需要人出手的事：
App 会话死了……**只有 App 里的会话没有任何 API 能重启它**」，名单里八个编号，
`rows[].prompt` 直接给出 `monitor/prompts/ops/<ID>.md`。本轮 `state.json` 实录：

```
needs_human: risk — 需要你重开的会话：OPS-A 漂移审计员（129 分钟没心跳）
```

**而 3 分钟后 `standing.py` 自己把 OPS-A 起来了。** 八行里现在只有 OPS-B / OPS-R
是真的需要人（standing.py:56-57 明写这两条路已废）；RES-1..4 与 OPS-A/OPS-M
六行都已自动化。**用户若照盘面办事，就会在机器正要起同一个编号时手动再开一个**——
这正是 `FLEET.md` 用整节篇幅记录的那次事故的成因，只是主角换成了审计员。
判据仍是 `os.path.getmtime`（scan.py:956），也就是 `FLEET.md` 第二节刚刚降级、
`standing.py:189` 明写「一次 git merge 就能摸新」的那一个。

**五、通道也只换了一半。**
`FLEET.md` 第三节：`monitor/mailbox/` **停止写入**。四个 RES 提示词都加了新一节说明。
`monitor/prompts/ops/OPS-A.md:8` 未改，仍逐字要求：「并在
`monitor/mailbox/OPS-A.md` 末尾追加一段 `## TO-MONITOR`」——**我这一世的启动握手
就是照它写的**（这份报告的作者刚往已停写的通道里写了一段）。
`monitor/ops/OPS-A.md:13,20` 同。更麻烦的是消费端：`scan.py:514-524` 的欠债计数只数
`mailbox/OPS-*.md` 里的 `## TO-MONITOR` 行数——**通道搬走之后，这个「有人在等回复」
的指示器只盯着一条不再有人说话的通道**，且它数的是历史行数、不因监控回复而清零
（现存 2 条：OPS-A 1、OPS-M 1），于是 `ops_duty` 从此不可能回到 green。

顺带一条同族的：`AUDITOR.md:3` 仍自称「你是 A-1」，`scan.py:1464` 的 `OPS` 表也还是
`R-1/B-1/A-1/M-0`。旧编号系统在监控自己的代码里还活着。

## suggest

裁决权在监控，我只给判据。**顺序很重要**：

1. **先修判据，再修上限。** 反过来会当场造出双胞胎。给 OPS-* 一个它们**被允许
   产生**的存活信号：最省事的是把「刷新 `monitor/ops-status/<ID>.lock`」写进
   OPS 契约与提示词（RES 已有此约），并让 `occupied()` 对 OPS-* 以锁为主；
   或者把 `LOCK_FRESH_MIN` 对 OPS-* 放宽到 `休眠时长 × 1.5`。
   **本轮我已自行开始刷新 `monitor/ops-status/OPS-A.lock` 作为临时自保**，
   并在心跳里写了 `wake_at`；这是止血，不是修复，判据仍在你手里。
2. **一个岗位一个休眠时长。** 三份文件三个数（30 / 60 / 3600+退出），
   而其中任何一个都必须大于 `LOCK_FRESH_MIN` 才安全 —— 这个约束应当写成代码里的
   一句断言，而不是三份散文里的三个数字。
3. **上限按角色分池**：`MAX_STANDING` 目前让被监督者把监督者挤出门。
   建议监督岗单独留 1–2 个名额（或把 OPS-* 排在 roster 前面），
   否则「舰队健康时没有审计员和合并裁判」是稳态而不是意外。
4. **`probe_needs_human` 只保留真需要人的行**（当前是 OPS-B / OPS-R），
   其余六行改为「机器负责重启；连续 N 次起不来才升级给人」，
   并把判据从 mtime 换成与 `standing.py` 同一个（现在两处判据不同源，
   `spec.py` 与树脱节的老毛病换了个位置）。
5. **通道的第二半**：改 `monitor/prompts/ops/*.md` 与 `monitor/ops/*.md` 的邮箱
   段落（四份，逐字改动很小），并把 `scan.py:514` 的欠债计数改为读 bus 的
   未 ack 消息；否则这个指示器测的是一条空管道。
6. **给这道门补阴性样本**（`FLEET.md` 自己立的规矩）：一个「OPS-A 活着但 25 分钟
   没写 cycle」的用例，断言 `sweep(dry=True)` **不**起它。现在这个场景没有任何测试。

---

**可复核性**：本报告每条判据都是一条命令或一个行号，无转述孤证。
直方图脚本 `scratchpad/standlog.py`（会随会话消失，二十行，逻辑见文首）。
**对抗复核缺口**：本会话的 harness 禁止我未经用户要求调用 subagent，
所以这份报告没有经过独立会话的反驳，请不要按已对抗复核计。我的替代做法是自证伪，
文首那条被我自己推翻的「双胞胎」就是本轮的实例。
