priority: 2
cell: V27
territory: exam
deps: none
lane: verify
author: RES-3

# V27-V27-manifest-absolute-paths · 被跟踪的生成物里记着上一个构建者的绝对路径，而确定性闸门按构造看不见它

`exam/artifacts/build_manifest.json` 是一份**被跟踪的生成物**，而它记的是「上一个构建它的人当时在哪个目录」。

证据两条，都可当场复核（V6-V23 顺带测出，`exam/runs/20260730T021500Z-V23-large-space/RUN_STATE.md` 已记）：

1. `git show master:exam/artifacts/build_manifest.json | grep -o '"[^"]*Users[^"]*"'` 印出 12 条绝对路径，第一条是
   `C:\Users\user\Desktop\theoria\.worktrees\v5-verdict-three-types\exam\artifacts\...`；
   同一文件在 `agent/v6-v23-large-space-verdict-gap` 上是
   `...\.worktrees\v6-v23-large-space\exam\artifacts\...`。
   两个分支的差别不是内容，是**谁最后跑了一次 build_papers**。
2. 于是每一个在 exam 领地交付的人都会带上 12 行伪 diff。这不是洁癖问题：它是 exam 与 exam 之间的**合并冲突制造机**，而冲突的两边语义完全相同。

三个后果，第三个最重：

* **「同一构建，同一字节」对 exam 这一份文件是假的**。CLAUDE.md 把确定性列为要求而非优点。
* **`exam/verify.py` 的确定性闸门看不见它**。它跑两次构建比较摘要，但两次都在同一个 cwd 下跑，所以它检的是「同一台机器同一目录两次是否一致」，而不是「任何人在任何地方重建是否一致」。**但这条的份量比本条目初稿写的小，见下面的更正**。
* **泄露会顺着留痕正典传播到要发布出去的东西里**：`exam/tools/archive_run.py:74-77` 把 `build_manifest.json` 读进它给每个 run 造的清单，所以这 12 条路径不止待在一个产物里，它们会进 `runs/<id>/` 的清单，而 Phase 4 的释出清单公布每一个被跟踪文件。对外人来说 `.worktrees\v5-verdict-three-types\...` 既是噪音又是本地目录结构的泄露。

## 更正（RES-3，下发后 10 分钟自己核出来的，先于任何人开工）

**初稿把第二条后果说重了，改掉而不是留着。** 初稿暗示这 12 条路径会让「任何人在任何地方重建」得到不同的评分产物。**实测不是**：`exam/verify.py:58-78` 的确定性闸门是在进程内构建再取 `module_for(t).build().sheet(digest())` 的摘要，**它从来不读 `build_manifest.json`**（`grep -n build_manifest exam/verify.py` 零匹配）。所以被评分的卷子摘要与位置无关，`GREEN` 不是靠共用 cwd 蒙来的。

于是本条目的真实份量是三件而不是四件：**diff 噪音与合并冲突**、**顺着 `archive_run.py` 进入要发布的留痕**、以及**一道在这一维上按构造检不到漂移的闸门**——最后这条仍然成立且仍然值得补，但它今天**没有**在掩盖任何错误的评分。**做这件活的人不要把它写成「确定性闸门是假绿」，那会是一句比缺陷本身更糟的话。**

**第 3 件（扫其余产物）已经做完了，不必重做。** `git ls-files exam/artifacts` 共 41 个被跟踪文件，逐个扫绝对路径（Win/POSIX）、用户名、临时目录、`worktrees`：**命中全部集中在 `build_manifest.json` 这一个文件的这 12 个键上**（`papers[].sheet_path` / `key_path` / `cheater_brief_path`，4 篇 × 3 键），其余 40 个文件干净。扫描记录在 `monitor/res/RES-3-notes/V27-prep-artefact-scan.md`。**所以这是一处单文件修复加一道闸，不是一次清扫**——第 3 件改成「复跑那次扫描并把它接成闸门，防止再有产物长回绝对路径」。

做四件：

1. **让 `build_papers` 只写仓库相对路径**（相对 repo root，正斜杠）。生成物禁止手改，所以改的是生成器，然后 `python -m exam.tools.build_papers` 重生成。
2. **给 `exam/verify.py` 的确定性闸门补上位置维度**：在**两个不同路径**下各构建一次并比较（把仓库 checkout 或 exam 目录复制到临时目录跑第二次即可），确保这类漂移下次会红。**先让新闸门在修复前的代码上红一次**并把输出贴进 `runs/<id>/`——没见过它红过的闸门不算闸门。
3. **扫一遍 exam 的其余被跟踪生成物**是否也埋了绝对路径或其他环境依赖（cwd、用户名、临时目录、时间戳、PYTHONHASHSEED 之外的随机性）。逐条判：是生成器该改，还是该从跟踪里下线。
4. 把规矩写进 `exam/DECISIONS.md`：**被跟踪的生成物里不得出现仓库外的绝对路径**，并说明确定性闸门必须跨位置而非仅跨随机种子。

负样本要求：故意在生成器里塞回一条绝对路径，断言第 2 条的新闸门变红；它不红就是第 2 条没做成。

服务论文 WP9（图表与产物可复核）与 Phase 4 释出清单。零 API、零封存堆接触。territory 是 exam，可读不可改其他领地。留痕 `exam/runs/<UTC>-V27-.../`。交付前另派对抗性 subagent，专打「新闸门是不是只在作者的机器上红」与「相对路径化有没有偷偷改掉摘要口径」。
