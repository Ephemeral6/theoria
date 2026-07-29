# S30 · 扫描崩了，页面只会变陈旧，不会变红

工人 W-1680 · 分支 `agent/s30-scan-crash-is-invisible` · base `580c645d` ·
UTC 2026-07-29T17:23Z 开工。零 API、零花费、封存堆零接触。

## 一句话

四件都做了；**但第三件在做的过程中推翻了这张工单的前提**——那 55 个 traceback
从来没有让扫描停下来，它们让一个探针**伪造了一个绿**。前提被推翻的部分照实写在
`monitor/CRASHES.md` 里，没有为了让工单成立而把结论掰弯；工单要的加固本身仍然
成立且已交付，因为**真**崩溃确实会静默，只是那 55 次不是。

## 交付

### 1. 失败出口（`scan.py`）

崩溃时仍写出 `state.json`（`scan_ok: false` + 异常类型 + 出事的帧 + 抛出行 +
完整 traceback + **上次成功的时刻**），并把 `index.html` 改写成红色失败页。

三个判断值得单独记：

* **出口装在 `main()` 里，不在 `build()` 里。** `verify.py:_real_run` 靠
  `build()` **抛出**把闸门判红；一个自己吞掉异常的 `build()` 会让闸门永远绿——
  同一个缺陷，只是上移一层。`test_build_still_raises_so_the_gate_still_goes_red`
  把这条钉死了，`verify.py:_fields` 里另加了一条 `scan_ok is not True` 的绊线。
* **失败页由 `render_failure()` 画，不复用 `render()`。** `render()` 直接下标九个
  成功态的键（含 `probes["conflict_scan"]`、`loop_stats[2]`），喂给它一个桩会让
  失败出口成为第二次崩溃，而那一次没有处理者。
* **失败状态不携带上一轮的任何数据。** 旧数字配新时间戳，正是本件要拆的东西。
  只保留一个事实：那些数据最后一次为真是什么时候。

写盘用 tmp + `os.replace`（`accounts.py:98` 早就为同一个理由这么写了），
`write_failure` 每一步单独 try——一个自己会抛的失败出口，交还的正是它要消灭的沉默。

### 2. 页面自己算年龄

`index.html` 里第一次有了 JavaScript（`FRESH_JS`）。它必须是烘进页面的时刻 +
浏览器的钟：这一页是 `file://` 打开的静态文件，重新 fetch 不了任何东西。
超过两个扫描周期（2 × 10 分钟 = 1200 秒，`--watch N` 时跟着变成 2N）就自己变红。

**三态不是两态**：新鲜（灰）/ 陈旧（红）/ **未知（灰，同 `--missing` 色）**。
读不出生成时刻、或时刻在未来（本机与生成机时钟不一致），都是「未知」而不是红——
把一次读取失败谎报成一次扫描失败，是同一种病换个方向犯。

`state.json` 因此多了 `scan_ok` / `generated_epoch` / `generated_at_utc` /
`stale_after_s`。`generated_at` 的老形状**一个字节没动**：`render()` 与 `app.html`
都在切 `[5:16]`，`history.jsonl` 拿它当 `ts`。
`verify.py:REQUIRED_STATE_FIELDS` 从 10 个字段加到 13 个，新字段没了就是红。

`app.html`（每 20 秒真的重新 fetch 的那一页）也改了：`render()` 开头
`if(s.scan_ok === false) return renderFailed(s)`。不改的话，一份失败的 state.json
会被它满地的 `|| []` / `?? 0` 渲染成**一屏漂亮的零**——比陈旧更坏，陈旧至少
是真发生过的数字。

### 3. 55 个 traceback 的分类 → `monitor/CRASHES.md`（被跟踪）

**一类，55 次，同一个最内层帧**：`subprocess.py:1615` 的 `_readerthread`，
`gbk` 解码 `git log --name-only --format=%h%x01%s -40` 的输出。

**工单的前提是错的，实测如下：**

| 判据 | 实测 |
|---|---|
| traceback 之后仍打印 `index.html written` | **55 / 55**（中位隔 11 行） |
| traceback 里的 `scan.py` 帧 | **0**（异常在工作线程里，传不上去） |
| 带 traceback 的 54 个周期里 `conflict_scan` 的判决 | **green 54 / risk 0** |
| 不带 traceback 的 141 个周期 | green 51 / **risk 90** |

页面从来没有变陈旧。它每一轮都被正常写出，**带着一个伪造的绿**：解码在 reader
线程里抛出 → `stdout` 变 `None` → `git()` 的 `except Exception: return ""` 吞掉 →
`probe_conflicts` 把空字符串读成「三类检查全空」→ green。一句声称三项检查都通过的话，
印在**其中一项**根本没跑成之后（只有一项——`git ls-files -u` 在索引干净时本来就返回
0 字节，那个 `""` 是真答案；对抗性复核纠正了我最初写的「两项」）。这个探针平时
64%（90/141）的周期报红，瞎掉的那 54 个周期一次没报。

窗内还有一次天然对照：**第 49 轮是这 55 次运行里唯一没崩的，也是唯一报了 `risk` 的**，
两侧第 48、50 轮都崩、都报绿。同一份代码、相邻十分钟，唯一的自变量是解码有没有崩。

解码本身早已修好（`encoding="utf-8", errors="replace"`，`05947108` → master `7f6aa876`，
比最后一次崩溃晚 6 分钟）。**没修的是它背后那句判断**，本件补上：

* 新 `git_or_none()`：拿不到答案返回 `None`——包括 `returncode != 0`，也包括
  `stdout is None` 这个 2026-07-28 的确切形状（**退出码 0、无输出、父进程里什么都没抛**，
  只抓异常的守卫会整个漏掉）；
* `git()` 保留，把失败压平成 `""`，给十几个只做**显示**的调用点；
* **四个**拿 git 结果**下判决**的调用点改用 `git_or_none`：`probe_conflicts`、
  `probe_spec_freshness`（空→`"0"`→「spec.py 一点不陈旧」）、
  `probe_append_only`（空→删除 0 行→「append-only 完好」）、
  `collect_metrics`（空→`dirty: []`→「工作树干净」）。瞎掉时返回 **`missing`**
  而非 green，detail 点名哪次调用瞎了。用 `missing` 不用 `risk`：
  没看成不等于看见了冲突。（后三个是对抗性复核找出来的，它们和那 55 次的假绿
  是同一个形状，就在同一个文件里。）

`CRASHES.md` 里每个数字都由 `classify_refresh_log.py`（本目录）重算，
输出存在 `classify_refresh_log.out`。日志被清理后脚本会说「已经没有了」并退 2，
不打印一串零。

### 4. 负样本

`monitor/tests/test_scan_failure_exit.py`（30 条）与 `monitor/tests/test_freshness_js.py`（3 条，用 node 真跑页面脚本），红与配套绿成对：
崩溃后 state 必须说自己崩了、失败页必须不含上一轮的标记字符串、
不知道上次成功时刻必须是 `None` 而不是 0、连续两次崩溃必须保住原始成功时刻、
瞎掉的探针必须不报绿、能看的探针必须仍然报绿、健康扫描必须仍然只写三个文件。

`tests/mutants.py` 加了三个变异体，全部 **RED**：
把失败出口的 `except Exception` 换成 `except ZeroDivisionError`、
让失败页把上一轮数据带过来、让 `git_or_none` 不再识别「没答案」。

## 测试

| 项 | 结果 |
|---|---|
| `python -m pytest monitor/tests` | **253 passed, 2 xfailed**（基线 220 passed / 2 xfailed，新增 33 条） |
| `bash monitor/verify.sh` | **GREEN, exit 0**；`state.json carries all 13 required fields` |
| `python monitor/tests/mutants.py` | 新增 3 个变异体全 RED（基线机制重建后，RED 只认基线之外的新失败）；2 个**先于本件就已**贴不上（见下） |
| `classify_refresh_log.py` | 复现了 CRASHES.md 的全部数字 |

## 对抗性复核（两个 subagent，任务是推翻我）

两份结论都值得记下来，因为**其中一份推翻了我自己写的修复**。

### 对着 CRASHES.md 的那一份：主结论站住，四个数字不站

「不是页面陈旧，是伪造的绿」经受住了更严的检验——复核者自己设计了更强的判据
（探针块普查 195:195:195、运行边界、孤儿 traceback、同块包含性），全部通过。
但它揪出四个错数，已逐条改正：

* **出错字节直方图加起来是 59**，而只有 55 次崩溃——算术上就不可能。已改为脚本
  复算的 55（我自己的判据脚本给的也是 55，两边独立一致）。
* **「连续 54 个周期，一轮一次」错**：窗内是 **55 次运行**，第 38 轮有两个、
  第 49 轮一个没有。
* **「其中两项没跑成」是夸大**：只有 (c) 瞎了。(b) `git ls-files -u` 在索引干净时
  本来就返回 0 字节，空字节 GBK 解码不出错，那个 `""` 是真答案。
* **position 28640 是会漂的数**，复核当天是 29000。已标注为不稳定判据。

而它还挖出一条**我漏掉、且加强了我自己论点**的证据：`history.jsonl` 在崩溃窗内有
两行（`14:24:22`、`18:12:55`）在 `refresh.log` 里没有对应运行行——**证明当时确实有
第二个进程在跑 `scan.build()`**，把我原来标为「未查明的异常」的第 3 条从猜测升格为
有据事实，并逼出一条限定：`refresh.log` 不是扫描运行的完整普查，「195 次成功运行」
应读作「195 次被记进这个日志的」。

### 对着代码的那一份：12 条，其中 1 条是我把本工单的病又犯了一遍

**最重的一条，`probe_conflicts`：git 瞎掉时，我的第一版把「已经在磁盘上找到的冲突
标记」丢掉，改报 `missing`。** 而 `_VERDICT_RANK` 里 `missing`(1) 排在 `risk`(0)
**之上**——所以那是一次**从最坏判决往上升**。检查 (a) 读的是磁盘文件，根本不依赖
git，它找到的东西不该被一次 git 失败撤销。这正是本工单要杀的形状，由本工单的修复
亲手复现。已改：`findings` 先判，瞎掉的部分**并列**报告而不是**取代**。
负样本 `test_being_blind_never_hides_a_conflict_that_was_found` 钉住了它，
另加一条断言 `_VERDICT_RANK["risk"] < _VERDICT_RANK["missing"]`，排序一旦翻转就红。

其余已修的（每条都配了负样本）：

| # | 缺陷 | 后果 |
|---|---|---|
| 2 | 失败页的 traceback 走了 `esc()`，而 `esc()` 把换行换成空格 | 整页最有用的东西被压成一段不可读的散文，`.tb` 的 `pre-wrap` 纯装饰 |
| 3 | `import spec` 在模块级 | `spec.py` 是舰队每周期都改的手写文件，**它一个语法错就死在 `main()` 之前**，失败出口根本没装上。已改成失败延迟到 `build()` 里抛 |
| 4 | 页面不自动重载 | 生产环境不带 `--watch`，所以开着的标签页**永远不会重读文件**。原版会对着一次健康的扫描显示「扫描可能已经挂了」——**同一种病反着犯，假红**。已改为陈旧时先重载一次核对文件本身，每个窗口至多一次 |
| 5 | `failure_state()` 在所有 try 之外 | `json.load` 接受裸 `NaN`，`int(nan)` 抛异常 → 失败出口自己死，什么都不写 |
| 6 | 三个 `except: pass` 下面printing着一句无条件的「页面已改写」 | 磁盘满时那句话是假的，而这份改动的论点正是「失败不许无声」 |
| 8 | 先写 `index.html` 后写 `state.json` | 只落一个时会得到「红页 + `scan_ok: true`」，而 `app.html` 只读 state → 把旧盘面当健康渲染。已改成 state 先落地（失败方向朝安全） |
| 9 | S30 之前的 state.json 有时刻没纪元 | **上线后第一次崩溃就是这个形状**：页面印出时间戳，紧接着说自己不知道时间戳 |
| 10 | 失败页的年龄 span 没有 `data-stale` | `parseInt(null)` → 红分支不可达，一个月前的成功显示成静音灰 |
| 7 | 另外三个拿 `git()` 结果下判决的调用点 | `probe_spec_freshness`（空→「一点不陈旧」的绿）、`probe_append_only`（空→「删除 0 行」）、`collect_metrics`（空→「工作树干净」）。全部同形，已改用 `git_or_none` |
| 11 | `.conflict.missing` 没有 CSS 规则 | 本件唯一新增的判决在页面上比它取代的绿还不显眼 |
| 12 | `return 1 if failed else 0` | 现在不可达，但方向是错的：将来加 `--once` 会让「崩了又恢复」报成失败 |

**还有一条是复核者对我测试的判决，我认同并已补**：全套测试**从不执行任何
JavaScript**——那些 `"setInterval" in page` 的断言只是拿 `FRESH_JS` 的源码去
grep 一个由 `FRESH_JS` 拼出来的页面，只能抓到「常量被删了」。上面第 4、10 两条
真缺陷**整个活在这个盲区里**。新增 `monitor/tests/test_freshness_js.py`：
用 node 加一个 DOM 桩**真的跑**这段脚本，覆盖新鲜/陈旧/未知/未来时钟/旧标签页重载
五种情形；没有 node 的机器上跳过而不是失败。

**以及对 `mutants.py` 本身的一条**：它没有基线。`_copy` 排除 `*.json` 和 `runs`，
临时目录也不是 git 仓库，于是有若干条测试在**任何**变异体下都失败，
`proc.returncode != 0` 因此对每一个贴得上的补丁都成立——**这个工具printing的
「RED」是不可证伪的**。已修：先跑一遍未变异的副本取基线，只有基线之外的新失败才算
「抓住」，并把基线那几条列出来点名。（本仓刚在盘面上修掉的形状，长在检查变异体的
工具自己身上。）

## 缺口（如实记账，没有降低验收线）

1. **`release/MANIFEST.jsonl` 没有重生成。** `monitor/reflex.lock` 已
   `git rm --cached` + 新建 `monitor/.gitignore`（用 `*.lock` 模式，不用路径——
   根 `.gitignore` 逐条列路径正是 `reflex.lock` 漏网的原因）。但 `release/` 不是本件的
   领地，且这不是一行改动：manifest 现在 1951 行 vs 全仓 6052 个被跟踪文件，
   重生成是 1951 → ~6051 的大改，`enumerate.py` 还会在红线未清时退 2。
   另有一条实测预警：**138 棵工作树里 123 棵带着自己那份被跟踪的 `reflex.lock`**，
   master 删掉它之后这 123 支合并时会产生 modify/delete 冲突，直接打在自动合并队列上。
   详见 `monitor/inbox/20260729T175500Z-W-1680-reflex-lock-untracked-and-two-gaps.md`。
2. **`reflex.py:79` 只按 mtime 判锁活，没改。** untrack 断掉了「checkout 造出新鲜锁」
   这个触发器，但慢周期（`run()` 默认超时 2400 秒 > 锁的 1500 秒）仍能让 reflex 判自己已死。
   `test_reflex_state_machines.py:75-88` 有一条 `strict xfail` 正记着这条，动阈值会踩到它——
   需要单独一件工单。
3. **`git()` 的 `except Exception: return ""` 仍在**（有意保留，十几个调用点只做显示）。
   风险是新写的调用点若用 `git()` 又拿它下判决，同一个形状会复发；没有机器检查拦得住。
4. **`probe_conflicts` 的 (a) 段**逐文件 `except Exception: continue`，
   读不出的文件与干净的文件仍不可区分。需要逐文件的 unreadable 计数，另一件工单的体量。
5. **进程被杀仍然不可见；导入期崩溃只堵住了最可能的那一条。**
   `import spec` 已改成失败延迟到 `build()`（对抗性复核的第 3 条），所以
   `spec.py` 语法错——舰队每周期都在改它，这是最可能的一条——现在会变成红页。
   但 `scan.py` 自己的语法错、`childio` / `board` 等其他导入的失败，以及
   taskkill / OOM / 计划任务根本没跑，仍然到不了 `main()`。
   这几类的兜底是第 2 件（页面自己算年龄）：扫描没跑起来时页面会在 20 分钟后
   自己变红。**要彻底堵住需要一个不 import `scan` 的外层启动器**，
   那会动到计划任务指向的生产入口，值得单独一件工单。
6. **`tests/mutants.py` 的两个变异体先于本件就贴不上了**（`quota.py` 代码移走了），
   实测在 master 上原文命中数即为 0。没改：那是 quota.py 主人的判断。
