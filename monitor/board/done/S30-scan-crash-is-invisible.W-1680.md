priority: 1
cell: S1
territory: monitor

# S30-scan-crash-is-invisible · 扫描崩了，页面只会变陈旧，不会变红

清理审计（2026-07-29）拦下一次删除并给出了理由：`monitor/refresh.log` 不是冗余副本，
它里面有 **55 个 UnicodeDecodeError traceback**——是 `scan.py` 崩溃的**唯一存活记录**。

要害在于：**崩溃时 `state.json` 与 `index.html` 根本不写**。于是页面显示的是上一次
成功扫描的内容，看起来一切正常，只是时间戳旧了一点。**「扫描挂了」和「什么都没变」
在页面上长得一模一样**——这正是本仓 2026-07-29 编目的那一族，只不过这次它长在
仪表盘自己身上。

做四件：

1. **给 `scan.build` 加一个失败出口**：崩溃时仍然写出一份 `state.json`，
   内容是「本次扫描失败」+ 异常类型 + traceback 首行 + 上次成功的时刻。
   **页面必须能显示红色的「扫描失败」，而不是安静地显示旧数据。**
2. **页面上显示 `generated_at` 的年龄**：超过两个刷新周期就自己变红并说
   「这份数据是 N 分钟前的，扫描可能已经挂了」。渲染端不该无条件相信后端。
3. **把那 55 个 traceback 分类**：是同一个编码缺陷 55 次，还是几种？
   逐类给出成因与是否已修。`refresh.log` 是 gitignore 的，
   所以**结论要写进一个被跟踪的文件**，否则这份记录下次清理就没了。
4. **负样本**：往 scan 里注入一次必崩，断言 `state.json` 被写出且状态是失败、
   断言页面渲染出红色。没有这一条，这次修复本身也只是一份自称。

顺带（同族、便宜）：审计说 `monitor/reflex.lock` 被 `release/MANIFEST.jsonl:1376`
收录为 releasable，而 94 棵工作树各带一份含**陈旧 pid** 的副本，
而 `reflex.py:78` 认 1500 秒内的锁为活——正解是 `git rm --cached` + gitignore
+ 重生成 manifest，别直接删文件。

零 API、零封存堆接触。
