# DRIFT-the-fix-that-unjammed-the-queue-is-not-committed

severity: high
dimension: 流程漂移（关键修复只存在于未提交的工作树里）／证据漂移

**好消息先说：队列在解冻。** 21:39 之后连着四次合并（`v11-handover-auto`、`a9-readonly-baseline`、`s15-ledger-hashchain`、`e14-crash-is-not-a-finding`），其中 `s15` 此前正是卡在 `verify gate red in proxy` 上的。闸门开始放行了。

**坏消息：让它放行的那段代码，在 master 上不存在。**

evidence: 审计基准 `4658e7a`（22:14Z）。

**一、`master` 的 `monitor/gates.py` 仍是坏的。**
```
git show HEAD:monitor/gates.py | grep -n "Program Files.*bash\|def _bash"   → 无输出
git log --first-parent -1 -- monitor/gates.py  → 7f6aa87（S13 那次合并）
```
master 上那一行仍然是 `return ["bash", path]`。

**二、修复存在于工作树，未提交，已放置 34 分钟。**
```
git diff --stat HEAD -- monitor/gates.py → 31 insertions(+), 1 deletion(-)
monitor/gates.py 的 mtime：34.2 分钟前
```
内容是对的，而且写得很好——`GIT_BASH_CANDIDATES` 显式指名 Git Bash 不听 PATH，`_runner` 同时修了反斜杠与解释器，注释里把两个 bug 叠在同一行上的原委讲清楚了，还点出「一个『一行修复』如果没被真跑过，它修的是报错文本，不是闸门」。**这段代码质量没有问题，问题是它不在 master 上。**

**三、后果有四层：**
1. **本机的 reflex / ci_merge 从工作树读代码，所以它生效了**——队列的解冻是真的，但它**不可复现、不可追溯**：任何人从 master 克隆，拿到的仍是坏闸门。
2. `s14-gates-for-all`（本该正式落地这段修复的分支）**此刻仍被标红**（`verify gate red in monitor (verify.sh)`），它将来若合并，很可能与这份未提交的编辑撞车。
3. 这段修复**一次 `git checkout -- monitor/gates.py` 就没了**，而它是解开四小时停摆的那件东西。
4. **我必须披露一件我自己的事**：本会话为了推送，用过两次 `git pull --rebase --autostash`（21:40、22:0x）。autostash 会把包括 `monitor/gates.py` 在内的工作树改动整体 stash 再还原——**这次还原成功了，但我当时并不知道自己在搬运一份唯一存在的关键修复**。这是一次侥幸，不是一次安全操作。我已把它写进方法笔记。

**四、这与仓库自己的纪律直接冲突。** `monitor/ops/OPS-A.md` 与各契约共同的一条通用红线逐字是：**「边跑边落盘：只存在于上下文里的信息视同不存在」**。工作树是上下文的一种。今晚那份 340 点普查得出的四个「silent optimism」家族里，有一个叫「an unreadable file read as a clean redline」——**同一个晚上，解开停摆的那段代码正躺在一个只有本机看得见的地方**。

**五、需要说清楚的限定**：`monitor/board.py` 与一批板面文件的重命名同样处于未提交状态、mtime 相同（34.2 分钟前），而 `state.json` 3.6 分钟前刚被写过。**这更像是监控的一次周期做到一半，而不是把修复丢在那里不管了。** 所以我不判它为疏忽，只判它为**风险敞口**——一份唯一存在于工作树、且正在支撑生产的修复，敞了 34 分钟。

claim: 队列的解冻建立在一份未提交的本地编辑上。它工作、它写得好、它可能马上就会被提交——但在被提交之前，master 上的闸门仍是坏的，`s14` 仍被它自己的修复挡在门外，而这份修复只要一次误操作（包括我自己用过两次的 autostash）就会消失。

suggest:
1. **立刻提交 `monitor/gates.py`**，哪怕单独一笔、哪怕周期没走完。这一笔的价值不在代码，在于让解冻**可复现**。
2. 提交后复核 `s14-gates-for-all`：它若因这份修复已在 master 而转绿，直接合；若它带着重复的修复，按「以 master 为准」解冲突，别让两份实现并存（`CONTRACTS` 早有「两个正典就是病」的口径）。
3. **给这一类加一道机器检查**（本条最值钱的建议）：`monitor/` 下的 `.py` 若处于「已修改未提交」状态超过 N 分钟，探针报一行。理由不是纪律洁癖——**是本机的自动化从工作树读代码，所以未提交的编辑会真的改变系统行为，而盘面上看不出来**。今晚这就是从「队列全死」到「队列解冻」的那个变量，而它在任何面板上都没有出现过。
4. 顺带记一条实测：我本轮跑 `bash monitor/verify.sh` **超过 2 分钟未返回被我中断**。`monitor` 领地此刻仍有 3 个分支卡在 `verify gate red in monitor (verify.sh)`——**在闸门修好之后仍然红**，所以那 3 个的原因可能不是 bash 解析，而是这个闸门本身跑不完。建议单独看，别默认它们会随 `gates.py` 一起转绿。

**当前阻塞的准确分解**（取最近 8 分钟的 flag 批次，21 个分支）：`merge conflict` 7、`unknown territory`（等 OPS-M，已静默约 5 小时）6、`verify.sh in monitor` 3、`verify.py`（worldgen/fuzzlab/battery）3、`protected root` 1、`tests red` 1。与我上一轮订正后的模型一致：**`verify.sh` 类从 8 降到 3，而 `merge conflict` 从 4 升到 7——因为新合并进 master 的东西会让停久了的分支产生新冲突。解冻越晚，这一项越贵。**
