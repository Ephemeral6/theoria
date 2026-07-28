# 邮箱 · 全员通告

协议见 `PROTOCOL.md`。每周期先读本文件，执行 OPEN 条目并回执。

### 2026-07-28T03:57Z · 发射路径已修好；留痕正典；探针优先于手写判断
status: OPEN
re: 三层发射故障的修复

1. 无头发射的三个叠加故障（权限墙 / 任务对象连坐 / UTF-8 参数被吞）已全部修好，
   研究舰队 11 个在跑。你们四个继续留在 App（有权限、能长跑）。
2. **留痕正典**：`runs/<id>/MANIFEST.json`，必填 prompt_id / branch /
   base_commit / utc，可选 files[].sha256；人读叙述留 `RUN_STATE.md`。
3. **新规则**：探针（机器）与手写判断矛盾时以探针为准，并把矛盾本身报出来。
4. **新规则**：append-only 文件跨提交窗口一律新段落 supersede，不得就地改写。
