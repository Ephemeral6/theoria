# DRIFT-manifest-has-no-canonical-form

severity: low
dimension: 流程漂移（留痕规则只规定了 MANIFEST 的**内容**，没规定文件名与格式，检查器只认其中一种）

evidence: 审计基准 `HEAD=7c55c09`。

- 工单侧的措辞：`monitor/prompts/B-1-browser-ops.md:25`「runs/ 补 MANIFEST（prompt_id: B-1, branch, base_commit）」、`P-18:15`「RUN_STATE + MANIFEST(prompt_id: P-18)」、`A2-crosscheck.md:14`、`C1-worldgen.md:14`、`E1-property-fuzz.md:13` 同形。**十来份工单反复要 MANIFEST，没有一份说它叫什么、是什么格式。**
- 树上因此长出两种：
  - `arc-recon/runs/P-11/MANIFEST.json`、`battery/runs/P-14/MANIFEST.json`
  - `engine-rig/runs/p13-fd-real/MANIFEST.md`（外加 `TOOLCHAIN_MANIFEST.md` / `dividend.json` / `DIVIDEND.md`）
  - `theory-compiler/runs/P-10/` — **只有 `RUN_STATE.md`，没有任何 MANIFEST**。
- 检查器只认一种：`monitor/scan.py:307` 是 `os.path.exists(os.path.join(runs_dir, d, "MANIFEST.json"))`。于是 `monitor/state.json` 的 `provenance_scan` 报「engine-rig：1 个 run，MANIFEST 0/1」——engine-rig 那份留痕其实是全仓最厚的一份（工具链 URL / 版本 / 大小 / sha256 / 构建命令逐项在 `TOOLCHAIN_MANIFEST.md`），只是名字不叫 `.json`。
- 同一个探针另报：`baseline-arms`、`cold-start-a0`、`cold-start-a2`、`a0-spike` 尚无 `runs/` 档案；`proxy` 同样没有。这一条监控自己已在册（`provenance_scan.detail`），此处只作为同因证据列出，不另开报告。

claim: 留痕规则有内容要求、无形式要求，结果是三种落法（`.json` / `.md` / 没有）都同时存在，而唯一的自动检查只认 `.json`——它现在既漏报（P-10 没 MANIFEST 却混在「MANIFEST 0/1」里看不出与 engine-rig 的区别），又误报（engine-rig 有厚留痕被判 0）。`Theoria.md` Phase 4 要靠 runs/ 档案回溯每一个数字；到那时才发现格式不齐，是回溯不动的。

suggest:
1. 定一条正典（建议 `runs/<id>/MANIFEST.json`，必填 `prompt_id` / `branch` / `base_commit` / `utc`，可选 `files[].sha256`），写进 `CLAUDE.md` 的 Conventions 一段，让它对两轨道同时生效；人读的叙述留在 `RUN_STATE.md`，不与 MANIFEST 争位。
2. `monitor/scan.py:307` 改成先找 `MANIFEST.json`、找不到再认 `MANIFEST.md` 并在 detail 里标 `(md)`，让「格式不正典」与「根本没留痕」在盘面上分得开——现在这两件长得一样。
3. 存量三笔按正典补齐：`engine-rig/runs/p13-fd-real`（有内容，补一份 `.json` 索引即可）、`theory-compiler/runs/P-10`（真缺）、`arc-recon` / `battery` 已合规。`P-12` 工单里已有的「历史产物补建 runs/ 与 MANIFEST（`retro:` 前缀）」是现成的口径，直接沿用。
