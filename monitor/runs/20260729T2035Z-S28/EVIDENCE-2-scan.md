# S28 条目 2、3、7、8、9 —— `scan.py`

做的人：RES-4 主会话（本组两次派 subagent，两次都被 API 529 打死，未写一字）。
零 API 花费，封存堆零接触。`scan.py` 渲染的是人用来判断舰队是否健康的那张页。

---

## 条目 2 · `_supply()` 把 reserved 段也数进可领条目

它去数 `board.py list` 输出里 `"  p"` 开头的行，而 board.py 的 **available 段和
reserved 段都印这个前缀**（本次改动后还多了 territory-blocked 段）。

### 修之前（实测，真板，同一时刻）

```
scan.py's number  (prefix-match '  p') : 4
board.candidates() -- the honest one   : 1
reflex.py already uses candidates() and would record SUPPLY-LOW:1
```

**仓库里有两个互相矛盾的供货数，而被渲染出来的是错的那个。**
4 走 `> 2` 那条分支 → 页面印「供货充足」绿色；1 走 `<= 2` → `partial`。
`reflex.py` 早就在用 `candidates()` 并诚实地记 `SUPPLY-LOW`。

### 修

`_supply()` 与它的孪生（`state["board"]["available"]`，前端拿它当可领件数显示）
都改成直接问 `board.candidates()`。**数一个渲染给人看的字符串，本来就是在拿排版当
API**——这次给 board 加第五个分区就会让那个数再涨一次，正好证明这一点。

顺带给两处都补了「问不到」的分支：`_supply()` 返回 `risk / 板查不出来`，
孪生处把 `available` 设成 `None`（前端据此显示「不知道」而不是一个漂亮的数，
这跟 `scan.py` 里既有的先例一致）。**这个探针存在的理由是「见底就是全员空转」，
所以「数不出来」绝不能长得像「板上很充足」。**

---

## 条目 3 · 「已禁用」哨兵在比较之前就被销毁

`probe_scheduled_tasks` 强制 `encoding="utf-8"` 读 `schtasks`，而 schtasks 是
Windows 内建、印的是**控制台代码页**（本机 cp936）。

### 修之前（实测，同一次查询两种解码）

```
console codepage on this box: cp936

--- run_console (cp936) ---
模式:         正在运行

--- forced utf-8 ---
ģʽ:         ��������
```

英文 `Disabled` 在这台机器上一次也不会出现，中文「已禁用」被
`errors="replace"` 换成 U+FFFD——**`disabled` 对任何任务恒为 False**。
而这个探针存在的理由，逐字写在它自己的 docstring 里：
「OPS-M 和 OPS-R 都报告 TheoriaReflex 处于 Disabled 而板上无人提及」。

机制本身也钉了一条测试（不依赖机器状态）：

```python
raw = "模式:         已禁用".encode("cp936")
mangled = raw.decode("utf-8", errors="replace")
assert "已禁用" not in mangled and "Disabled" not in mangled
```

### 修

改走 `childio.run_console`（`childio.py` 的 docstring 早就写下了这条规则，
并解释了**为什么不能做成一次全局替换**：`tasklist` 同族必须留在控制台代码页，
一刀切成 UTF-8 会从另一头重演那次「八个活着的工人被报成死的」事故）。
`scan.py` 原先没有 import childio，一并补上。

---

## 条目 7 · `probe_append_only` 跳过已不存在的受监视文件

### 修之前（实测，把四个受监视文件之一当作不存在）

```
  status : green
  detail : 4 个追加式文件无新增删除（1 行历史删除已裁决豁免：同窗口自我订正）。
```

**它把 4 件全报成「已核查干净」，而其中一件已经不在了。**
而删除恰恰是 append-only 这条规则能被违反的最彻底的方式。

### 修

缺失单列成 `risk` 并点名，文案改成 `已核查 3/4`；全在时是
`已核查 4/4 …无新增删除`。

---

## 条目 8 · `probe_verify_gates` 丢掉 `survey["decorative"]`

### 修之前（实测，真仓库）

```
  n_territories : 25
  gated         : 24
  decorative    : 22   <-- 存在、但从没被证明能变红的闸门
  ungated       : 0

  the probe's coverage string (verbatim, old code):
    领地 25：自带闸门 24、仅测试套件 1、**无闸门 0**
```

`gates.py` 的注释逐字写着「'19 gated' 和 '19 gates known to work' 是两个不同的
断言」，而这条探针**读了前一个、印了后一个**：`decorative` 一直被算出来、
一直被丢在地上。条目原文说 19/20，实测此刻是 **22/24**，
而且因为 `ungated == 0`，状态是 **green**——那句绿正是这条假信号本身。

### 修，以及一个刻意不做的决定

把数字拼进 coverage：`自带闸门 24（其中 **22 个从未被证明能变红**）`。

**刻意不据此压成 partial。** 那 22 个里至少有几个有未声明的阴性对照，长期压下去
等于长期喊狼来了；而喊狼的检查会被关掉，**一条被关掉的检查和一条不存在的检查是
同一回事**——这句话是这条探针自己的 docstring 写的。所以让**数字**可见，
而不是让**告警**变响。这个判断有一条专门的阴性对照测试钉着
（`test_decorative_gates_do_not_by_themselves_turn_the_probe_amber`），
将来谁想改这个决定，会先看到它。

---

## 条目 9 · 手打的缩水 `ACK_REQUIRED`

`scan.py` 的总线探针手打了 `("order", "question")`，把 `urgent` 漏在
「欠回执」之外；`bus.py:83` 自己的 `ACK_REQUIRED` 是
`("order", "urgent", "question")`（那一半上游已修）。
`cmd_read` 会**永远重发**一条没回执的 urgent，而状态行印「指令全部已读并回执」。

### 修之前

先说清楚**证据的强度**，因为这条与前四条不同：

* **词表不一致是实测的**：`bus.ACK_REQUIRED` 三个词，scan.py 两个词；
* **这条路径是可达的**：真总线上 RES-1 / RES-2 / RES-4 三个收件箱里都确实有
  `urgent` 类型的消息；
* **但此刻没有一条真实的「欠着的 urgent」**。我一度以为跑出来的
  `欠回执：RES-1(1), RES-2(1)` 就是修复当场抓到的，**查了一下发现不是**：
  那两条是 `order`，旧词表也会抓到。把旧词表塞回去再跑同一份文件，
  两者输出逐字相同：

```
BEFORE (order, question)          : partial  已送达，欠回执：RES-1(1), RES-2(1)
AFTER  (order, urgent, question)  : partial  已送达，欠回执：RES-1(1), RES-2(1)
```

所以这一条的「修之前」是**构造的**，并且如实标注为构造：

```
one unacknowledged URGENT sitting on a bus:
  old (hand-rolled set) owed = []  -> status line prints '指令全部已读并回执'
  bus.ACK_REQUIRED      owed = [1]  -> reported
```

漏掉的那个失败模式是最要紧的一种：**心跳还在写、cycle 还在推进、就是不执行
指令的活会话，无人报告。**

### 修

`from bus import ACK_REQUIRED`，取不到才退回三个词的字面量（比缩水的两个词安全）。
`notice` 不纳入——协议明说无需回执，纳入等于让每个会话永久欠债；
有一条阴性对照测试钉这一点。**这个词表属于 bus 协议，不属于盘面**，
所以是导入而不是手打。

---

## 整页跑通（不是只跑单元测试）

用 `scan.build(out_dir=<临时目录>)` 跑完整的一次页面构建——`out_dir` 这个参数
本来就是为「让闸门能跑一次真扫描而不脏工作树」而存在的，所以没有改动任何
被跟踪的生成物（`index.html` / `state.json` / `history.jsonl`）：

```
build OK. probes: 25
  append_only            green    已核查 4/4 个追加式文件，无新增删除（…）
  bus                    partial  已送达，欠回执：RES-1(1), RES-2(1)
  scheduled_tasks        risk     TheoriaReflex 运行中； TheoriaDashboard 运行中； TheoriaServe **未注册**
  supply                 risk     **板已见底**：5 件在做，0 件可领
  verify_gates           green    …领地 25：自带闸门 24（其中 **22 个从未被证明能变红**）、仅测试套件 1、**无闸门 0**
```

（`supply` 报见底是因为这次构建读的是**工作树里那份** base commit 的板副本，
不是主检出的活板。）

**顺带确认了一件与本条目无关但真实的事**：`TheoriaServe` 确实没注册
（`schtasks /Query /TN TheoriaServe` 退出码 1），而前端要靠它在 :8787 上取数。
这**不是**本次改动造成的——返回码那条分支我没动，旧代码同样会报 risk，
也就是说盘面上一直是红的。已 `bus.py say` 报给监控，不越界处理。

## 测试

`monitor/tests/test_scan_no_third_value.py`，17 条，全绿：

```
monitor $ python -m pytest tests/test_scan_no_third_value.py -q
.................                                                        [100%]
```

阴性对照逐条配齐（这份文件喂的是一张仪表盘，**永远亮红的探针和从不亮红的探针
下场一样**：被无视）：

* `test_a_healthy_board_still_reads_green` —— 五件可领仍是绿；
* `test_a_running_task_is_not_reported_disabled` —— 「正在运行」不许被判禁用；
* `test_all_files_present_still_reads_green` —— 四件都在时印 `4/4`；
* `test_decorative_gates_do_not_by_themselves_turn_the_probe_amber` ——
  上面那个刻意的判断；
* `test_an_acknowledged_urgent_is_not_owed` 与 `test_a_notice_never_owes_a_receipt`
  —— 两个方向各一条，防止词表改宽到让所有人永久欠债。

一条测试**先红，且是测试错了不是代码错了**（与 board 组同一个形状）：
「文件里不许再出现 `encoding="utf-8"`」的断言红在我自己那段**引用旧代码的注释**上。
改成只比对非注释行。
