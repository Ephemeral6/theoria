priority: 1
cell: A35
territory: baseline-arms
deps: none

# A35-baseline-archive-not-worktree-reproducible · 归档在新 worktree 首跑必红，闸门因此给整个领地造假红

A19（2026-08-01）验明并写在案、2026-08-04 由 ci_merge 应验的病：
**主检出 559/0 全绿，闸门的一次性 worktree 里同一套件必红**——于是
merge 闸给 baseline-arms 制造 BASE RED，a33 等一切触本领地的分支被冤枉
挡下。两个成因，都在本领地：

1. **runs/ 归档不可跨 worktree 复现**：committed 的 runs/MANIFEST.json
   哈希是在主检出上算的，那里的 tracked 文件带 CRLF 落盘（如
   out/pilot_g50t_sonnet_rerun.json：28 个 CRLF、811 字节），新 worktree
   检出得到 LF（783 字节）——test_archive_runs.py 3 个测试首跑必红，
   然后因 archive_runs.build() **重写 ~21 个 tracked 文件**而"自愈"。
   修法方向（择一或组合，写明理由）：manifest 哈希前按 LF 规范化；或
   .gitattributes 钉 LF（engine-rig 先例——「core.autocrlf 不许腐蚀
   字节」是仓库明文纪律）；且**测试套件不许重写 tracked 文件**——
   把 build() 的输出改到临时目录比对，别动树。
2. **test_schema_column.py 的 skip 守卫看容器不看载荷**：schema_traces/
   目录存在而载荷（gitignored）不在时，3 个测试在该 skip 的地方 fail。
   守卫改为 key 在载荷上（resolve_root 已文档化 THEORIA_SCHEMA_TRACES
   为逃生口；monitor 侧 gates.py 已在闸门环境里代设，但守卫本身该修）。

验收：在一个**全新** worktree 里首跑 `python -m pytest` 全绿（不靠自愈、
不靠环境变量）；跑完 `git status` 干净（套件不再重写 tracked 文件）；
主检出照旧绿。零花费。绿了之后 ci_merge 对本领地的 BASE RED 假警自动
消失，a33 放行（monitor 盯）。
