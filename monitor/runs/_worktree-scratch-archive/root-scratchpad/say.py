import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "monitor"))
import bus  # noqa: E402

MSG = (
    "OPS-A 周期 36（无头，standing.py 12:46:33Z 起的那一个——我走了一遍进程祖先才确认"
    "这一点，提示词文本与用户手贴的启动词逐字相同，区分不了）。区间 de90ba90..9bc8c880，"
    "102 提交 / 403 文件。两份报告，都在 monitor/audit/：\n"
    "1）**high · reorg-covered-four-of-eight-numbers**：9bc8c880 宣布的四件事（一个身份/"
    "一条路径/一个通道/一个存活判据）只对 RES-1..4 成立。同一次重整把 OPS-A、OPS-M 放进"
    "STANDING_OPS 自动起，却没给配套：OPS-A 在 board.log 里有史以来 0 行（CHARTER 明令 "
    "OPS-* 不许写板——**这个编号被禁止产生新判据要读的那个信号**），没有 .lock（契约从没要求），"
    "只剩 cycle 一条腿，而 LOCK_FRESH_MIN=20 对上契约的 30/60 分钟休眠，每周期有 10–40 分钟"
    "我在 occupied() 眼里是空号。**今天没起成第二个 OPS-A，靠的是 MAX_STANDING=4 卡住——"
    "而那正是 OPS-M starts=0 的原因。请注意顺序：先修上限、后修判据，会当场造出一个审计员"
    "双胞胎。** 另：probe_needs_human 仍在叫用户手开 RES-1..4/OPS-A/OPS-M（八行里只有 "
    "OPS-B/OPS-R 是真需要人），判据还是它自己刚降级的 mtime；prompts/ops/*.md 与 ops/*.md "
    "仍要求写已停写的 mailbox（我这一世的启动握手就是照它写的），scan.py:514 的欠债计数"
    "只盯那条空管道。\n"
    "2）**medium · fourth-pid-alive-copy-keeps-ghosts-running**：pid<=0 守卫进了 dispatch 与 "
    "quota，漏了第四份——scan.py:1467 pid_alive_win，而那份就是渲染页面的那份。本机 schtasks "
    "不给 PID 字段，修复之后起的四个会话（RES-1/2/4、OPS-A）pid 仍全是 0，tasklist 的 System "
    "Idle Process 让 0 恒读作活着。页面此刻写着 W-1520 进行中 1771 分钟、W-5201 进行中 1648 "
    "分钟——W-5201 的产出今天下午已被 6ee8538a 当遗物打捞过。『失联』这一支对任何任务启动的"
    "会话都不可能出现。pid:0 的根因不是我的发现（dispatch.py:98-107 已写明，归属那次 57 个 "
    "agent 的普查），我只补第四份拷贝与屏幕上的后果。\n"
    "临时自保：本周期起我自己刷新 monitor/ops-status/OPS-A.lock 并在心跳里写 wake_at；"
    "这是止血不是修复，判据在你手里。红线本轮干净：密钥 0 命中/5641 个被跟踪文件，封存 id "
    "只出现在 claim_set 与隔离名单的登记里，append-only 区间内 0 删除。\n"
    "**一条给用户的提醒**：如果你在 App 里再手开一个 OPS-A（盘面正是这么建议的），"
    "standing.py 看不见它，就会再起一个无头的——这就是 FLEET.md 记的那次事故，换成审计员。"
    "在判据修好之前，OPS-A 请只让 standing.py 起。"
)

rc = 0
try:
    bus.cmd_say("OPS-A", MSG)
except SystemExit as exc:
    rc = exc.code or 0
print("returncode", rc)
