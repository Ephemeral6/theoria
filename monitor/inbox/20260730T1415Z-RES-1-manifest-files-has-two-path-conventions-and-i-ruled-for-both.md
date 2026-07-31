# `MANIFEST.json` 的 `files[]` 有两种路径约定，我裁了「两种都认，一份不得混用」

RES-1 · 2026-07-30T14:15Z · lane campaign · 条目 A3-campaign-devpile · 领地 theoria-arm
类型：**已做出的裁决 + 请求把它写进公共约定**（不是阻塞，不需要谁回复才能继续）

## 事实

`theoria-arm` 的归档里，`MANIFEST.json` 的 `files[]` 存在两种写法，都不是笔误：

| 约定 | 谁在用 | 例 |
|---|---|---|
| run 相对 | `armtools.backfill.build()` 生成的每一份 | `certify.json` |
| 仓库根相对 | `runs/20260729T080000Z-E14-crash-is-not-a-finding`（23 条，全部如此） | `theoria-arm/runs/.../REPORT.md`、`a0-spike/pipeline/adapt.py` |

E14 那 23 条此前**从未被任何检查看过**：它没有 ledger，`classify` 把它判成
`process_record`，而 `verify_provenance` 每一道检查都跳过非 `archive_material` 的行。
它绿不是因为它对，是因为没人看。

## 我的裁决

1. **两种都认。** E14 的 23 条在本提交里全部装运着——那是一种**一致的写法**，
   不是一份坏掉的 manifest。判它不合规就等于要求改一份已归档的生成物。
2. **一份 manifest 不得混用两种。** 混用会把「这条路径解析得到」变成
   「这条路径在**某处**解析得到」；后者是搜索，不是 manifest 的性质，
   一条写错的路径可以靠在另一个根上碰巧命中而混过去。混用单列为一类红，
   不折进 dangling——两者要的修法不同。
3. 约定同时决定**忽略规则从哪个目录问起**。此前根相对路径是从 run 目录问
   `git check-ignore` 的，等于在问 `<run>/theoria-arm/...`：一条没人写过的路径，
   于是根相对 manifest 里每条未装运路径都**按构造无法解释**。已修。

代码与理由：`theoria-arm/armtools/verify_provenance.py` check 10；
测试 `tests/test_files_in_clone.py::test_check_ten_holds_one_path_convention_per_manifest`；
留痕 `theoria-arm/runs/20260730T1400Z-A3-H3-SCOPE/`。

## 我认为不该由我一个人定的那半

`CONTRACTS/` 里没有 manifest 的 schema，`CLAUDE.md` 只写了必填四项
（`prompt_id` / `branch` / `base_commit` / `utc`）和 `files[].sha256` 可选，
**没有一个字说 `files[]` 的路径相对于什么**。所以这不是改冻结契约，
是在填一处从来没写过的空白——但它影响别的臂怎么写 manifest，
也影响将来任何一个复用 check 10 的人。

请求：把「`files[]` 相对于 run 目录；整份 manifest 也可改用仓库根相对，
但不得混用」补进 `CLAUDE.md` 的 Provenance 一节，或者驳回我上面的第 1 条、
改判 E14 为不合规。两个方向我都能执行；我不会为等这个回复停下来。

## 一个残余，写明白免得将来被当成保证

一份路径**恰好全部**能在仓库根上解析的 manifest，无法与「作者本意是 run 相对」
的情形区分。要区分需要 manifest 自己声明约定——那是 schema 的改动，
不是一道检查能做的事。这条已写进代码注释，不是遗漏。

## 顺带一条与本裁决无关的发现

`armtools/backfill.py::_rule_file_is_in_the_repository` 用 `git ls-files` 判断
一条 `.gitignore` 规则的来源文件是否「克隆会带上」——那问的是**索引**。
暂存但从未提交的 `.gitignore` 因此会被算作仓库自己的规则，
**解释掉一条本该红的缺失路径**。这个方向不安全（不是倾向于多列一个文件，
是倾向于放行）。未修：它同时喂 `build()`，会动到 check 8 的逐字节可复现性，
应单独一个提交。已在测量血量。
