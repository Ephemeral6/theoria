# B-1 · 浏览器操作员：CLI 解决不了的三件事（claude-in-chrome）

你是浏览器操作员会话，工具是 **claude-in-chrome**（用户的真 Chrome，含登录态；用户已授权）。第一步先探测 chrome MCP 工具是否可用：不可用就把这一事实写进 `browser-ops/RUN_STATE.md`、提交、退出——不要用别的方式硬凑。
基准文件 `Theoria.md`；读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`baseline-arms/INCIDENTS.md` 的 INC-BA-001（**你这类任务上一次就是在这里出的事故，全文读完再动**）。
分支制：`agent/b1-browser-ops` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `browser-ops/`。

## 红线（先于任务）

- **封存堆内容红线**：19+2 局封存 game_id（见 `arc-recon/data/piles.json`，白名单是开发堆 4 局）。任何页面若开始描述具体游戏机制，立即停读、记录 URL、换路。下载类任务只按**文件名白名单**取文件，不读页面正文介绍。
- 登录、验证码、付款、新开账号 → 停下记录，那是人类的（汇总在 RUN_STATE 的 `needs_human` 一节）。
- 每个页面访问记录：URL、时间、取了什么、有没有看到不该看的（如实登记，INC-BA-001 的诚实先例）。

## 三件任务

1. **Schema 路 A artifacts 获取**（此前 CLI 下载守卫 fail-closed 卡住）：定位 Schema 上游释出的轨迹 artifacts 托管处，只下载属于开发堆 4 局（ar25-0c556536 / g50t-5849a774 / sk48-d8078629 / tn36-ef4dde99）的文件，来源 URL + sha256 入 `browser-ops/runs/`。任何汇总页/README 用「文件名匹配」策略，不通读。
2. **ARC 官方条款核查**（P-11 的遗留）：three.arcprize.org 及官方文档里查三点——速率限制/动作配额的官方口径、帧数据缓存与再释出的许可条款、API key 的使用范围。逐条摘录原文 + URL 落 `browser-ops/TERMS.md`。
3. **账户侧核查**（用户 Chrome 若有 arcprize 登录态）：只读地看账户/scorecard 面板有没有配额余量、key 权限范围的显示；截图存 runs/。没有登录态就记录并跳过，不要尝试登录。

## 留痕（比收工更重要）

你是一次性会话：上下文会蒸发，磁盘才是记忆。**边跑边落盘，不许攒到最后**——开工第一件事建 `browser-ops/runs/<UTC>-b1/`，此后每完成一小步（一次探测、一个页面、一个下载、一次判断）立即增量写入该目录；工作到一半崩掉时，磁盘上必须已经有能让下一个会话无缝接手的全部中间产物。凡只存在于你上下文里的信息，视同不存在。

## 收工

`browser-ops/RUN_STATE.md`（三件各自结果 + needs_human 清单）+ runs/ 补 MANIFEST（prompt_id: B-1, branch, base_commit）+ PARTNER_SYNC 追加 + push 分支。全程自主，不停下来问（needs_human 是记录不是提问）。
