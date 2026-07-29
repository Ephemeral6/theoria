# P-8 · Theoria 臂在线化：三臂中最后一条，当前关键路径

基准文件是 `Theoria.md`（内环五拍 1.10d、十条约束、分工三律）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`proxy/README.md` 与 `LEDGER_FORMAT.md`、`cold-start-a0/` 与 `cold-start-a2/` 的 THEORIZE_LOG（你的全部前例），然后跑一遍 proxy 与 engine-rig 的测试，绿了才开工。
分支制：从最新 master 建 `agent/p8-theoria-arm` + 独立 git worktree；完成后 push 分支，**不碰 master**（M-0 合并）。
领地：新建顶层 `theoria-arm/`。其余只读；PARTNER_SYNC 只追加。

目标：把离线已四度证活的内环（A0/A0′/A1/A2）接到真 API 上——**Theoria 臂的第一次在线对局**，对象是开发堆 `g50t-5849a774`（预检已 PASS 的局）。经 proxy 双代理走 observe→theorize→certify→probe→plan→commit；引擎全部用 engine-rig 现成件，编译用 theory-compiler；theorize 的 LLM 调用过模型代理入账（约束 8 从此有实测账单）。不追求赢——追求**回路在线转起来且账全**：哪怕只推进两三个关卡，七种意外的计数、theorize 轮数、逐回合成本曲线都要真实落账。

红线：动作预算 ≤120（含戳探），先算后花；密钥零接触（proxy 注入）；封存堆零接触；生成物不手改（约束 4）。

技巧：内环各拍可派 subagent（theorize 掌台一个、certify 独立一个、互不污染上下文）；对局主循环用循环自动推进，意外触发才回 theorize；每次 theorize 前后快照两本书（概念诞生时间线的原料）。

收工仪式：`theoria-arm/runs/<UTC>-g50t-first-contact/` 归档全部中间件 + `MANIFEST.json`（含 prompt_id: P-8, branch, base_commit, seed）；RUN_STATE.md + STATUS.md；PARTNER_SYNC 追加一段；push 分支。验收标准是合同，做不到的部分如实报 gap，不许降线。全程自主，不停下来问。
