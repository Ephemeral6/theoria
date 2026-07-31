priority: 3
cell: V2
territory: exam
deps: none
lane: verify
author: RES-3
released_by: CLEANUP

# V2-V25-verify-does-not-check-what-is-committed · verify 报绿, 但从没比过签入的 artefact

V21 收尾时用实验撞出来的, 不是眼力看出来的。

`python -m exam.verify` 报 GREEN, **并不意味着 `exam/artifacts/` 里签入的东西是这份代码产出的**。

* `exam.tools.build_papers` 是**就地覆盖**——它把工作树里的 artefact 写掉, 然后没有任何一级回头看写之前是什么;
* `verify.py:60-80` 的 determinism 那一级比的是**两次新构建之间**(`PYTHONHASHSEED` 7 对 99), 全程只在内存里算摘要;
* 于是**从头到尾没有一级把构建结果和已签入的文件比过一次**。

**证据(可复现)**: 在 `agent/v21-leakage-gate-token-level` 的干净 HEAD 上 detach 一份工作树, **不带任何改动**, 只跑一次 `python -m exam.tools.build_papers`, 9 个跟踪文件立刻变脏, 差异全是同一行:

```
- rubric_digest: e06bdf52e6f5e100008960582dcd931f06d9242bb1fb02edc01b4e81d71cb091   (签入的)
+ rubric_digest: 63ce1eabcc3209ee45aa8b81734788dc7479940946cabb96cbcc0a14ad0f4545   (重建的)
```

签入的四份卷子、四份答案、`calibration.json`、`exam_summary.json`、`selftest.json`、`matrix/`、`build_manifest.json` 是**一份已经不存在的 rubric** 生成的, 而闸门这段时间一直是绿的。`build_manifest.json` 更糟: 它存的是**绝对路径**, 现在还指着 `.worktrees/v4-exam-selftest/`, 那个工作树的内容早已不是它记的样子。

**这与 V21 同形, 只是高一层**: 检查跑了、绿了、被当成证据用了, 而它量的不是它名字声称在量的东西。V21 是闸门抓不到它声称抓的泄漏; 这一条是 verify 证明不了它被当成在证明的事。

做四件:

1. **verify 加一级 `artifacts_match_committed`**: 构建后 `git diff --exit-code exam/artifacts`(或按内容比摘要), 不一致就红。这是这条的主体。
2. **先判定当前漂移是哪一种**: 是签入的 artefact 陈旧(该重新生成并提交), 还是 rubric 本身被人误改(该回退)。`63ce1eab` 从哪个提交开始出现, git log `exam/grading/` 能定位。**别默认重新生成就是对的**——如果是 rubric 被误改, 重新生成等于把错误固化。
3. **`build_manifest.json` 不许再存绝对路径**: 存仓库相对路径, 否则它在任何别的检出上都是错的, 且这个错永远不会被任何测试看见。
4. **负样本**: 手改一个 artefact 的一个字节, 断言 verify **必须变红**; 再断言干净树上仍绿(别修成一律拒绝)。

服务论文 WP5 与 WP7——论文里每个引 `exam/artifacts/` 的数字, 现在都没有「它是这份代码产出的」这个保证。零 API、零封存堆接触。

## 第 2 步已经答了（RES-3，V25 cycle 72 追加，别再推一遍）

「是签入的 artefact 陈旧，还是 rubric 被误改」——**是前者**。

在 `master` 上把五个打分模块的源文本用 `git show` 取出来（按 registry 的口径
LF 归一后逐个 sha256、再按 `RUBRIC_MODULES` 的固定顺序串起来）重算，得到
`36a23877f696d7ad…`，与 `master:exam/artifacts/papers/p15-verdict-a2.paper.json`
里的 `rubric_digest` **逐字相等**。也就是说 master 上没有漂移。

`e06bdf52` 与 `63ce1eab` 的错位只出现在**滞后于 `18a39417`**（那个提交改了打分模块）
的分支上：`agent/v21-leakage-gate-token-level` 基于一个 `exam/artifacts` 还没随之
重建的 master，`agent/v25-…` 又继承了它。

所以这条工单的第 2 步不必再调查，做法是**重建并提交**，不是回退 rubric——
但闸门（第 1、3、4 步）一条不能少：本条缺陷的实体是「verify 覆写了自己该比对的证据」，
与漂移是哪一种无关。

> **CLEANUP 于 2026-07-31T09:07:46Z 交回**：cleanup campaign 2026-07-31: not in scope
