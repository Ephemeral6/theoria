# A3 · H3/H4 —— 判据从索引走到提交，作用域从 archive_material 走到「本提交装运的 manifest」

RES-1 · cycle 51 · 2026-07-30 · 离线（零 API、零花费、封存堆零接触）

## 我接手时磁盘上是什么样

上一世（cycle 50）死在半路：`armtools/` 两个文件改完没提交，`tests/` 一个字没动。
`python -m pytest -q` 停在 **272 passed / 5 failed**，五条全在
`tests/test_files_in_clone.py`，全是「实现改了、测试还在断言旧语义」。

这一条本身值得记下来：**未提交的半成品在磁盘上和已完成的工作长得一模一样**，
分辨它们的唯一办法是跑测试，不是读 diff。心跳里那句「H1 定型本轮已落盘」
是真的，「H3 已修」也是真的——但「已修」不含「测试还认得它」。

## 三处实质修正

### 1. 索引不是提交（`paths_the_clone_ships`）

上一世从 `os.path.exists` 改到 `git ls-files`，方向对，落点差一格：
`ls-files` 读**索引**，而 `git add` 过、从未提交的路径在索引里读成「已装运」，
可没有任何克隆有它的副本。这不是理论缺口——本仓库的约定就是
`git commit <paths>`（CLAUDE.md 禁止根目录 `git add -A`），
而那恰恰是**把暂存路径留在提交之外**的操作。

改成 `git ls-tree -r --name-only -z HEAD`。工作树完全不参与。

代价是明确的：一个 run 的产物在它的提交存在之前不算装运。这笔代价由
**调用方的作用域**付（见 2），不由这个函数付。

### 2. 一半的修复读起来像整个（`blob_the_clone_ships`）

改完 1 之后，check 10 仍然是：问 git 哪些路径被本提交装运，
**然后从磁盘上读那份路径清单**。manifest 提交过一次、之后本地编辑过，
这台机器校验的是本地那份，克隆校验的是另一份文档——正是 H3 开出来的那个缺陷，
落在第一次修复没有覆盖的那个输入上。

新增 `blob_the_clone_ships(any_dir_in_repo, repo_rel_path)`：`git show HEAD:<path>`。
现在「工作树完全不参与」这句话在 check 10 上是真的，而不是在它的两个输入里
真了一个。

对应测试 `test_check_ten_reads_the_manifest_out_of_the_commit` 两个方向都钉：
本地未提交的编辑不改变判词；同一处编辑提交之后改变判词（否则「不读磁盘」
可以由「什么都不读」满足）。

### 3. 忽略规则要从写路径的那个目录问起

上一世新加的「两种路径约定」分支有一个按构造成立的错误：
`_ignored_paths` 用它拿到的目录当 `git check-ignore` 的 cwd，
而根相对 manifest 的未解析路径是拿着 `theoria-arm/...` 从 **run 目录**问的——
那是在问 `<run>/theoria-arm/...`，一条没人写过、也没有任何规则匹配的路径。
于是根相对 manifest 里每一条未装运路径都**无法被解释**，是一条没有可行修复的红。

`anchor = top if by_root else run_dir`。

顺带把「混用两种约定」那条改成报完即 `continue`：它是自己一类的故障，
不该再被重复计一遍 dangling。

### 一个我写大了又收回的说法

我一度在代码注释里写：把约定固定到「每份 manifest 一种」堵住了
「run 相对的 manifest 借仓库根的同名文件蒙混过关」。**这是假的**，我逐路径重算过：
只要有任何一条路径按 run 相对解析成功，混用分支就已经把它拦下了；
run_rel 为空时，「按根相对读」本来就是唯一合理的读法。新旧代码在这一点上
行为完全相同。注释已改成它实际做的事，并且把真正堵不上的那条写进代码里：
**一份路径恰好全部能在根上解析的 manifest，无法与作者本意是 run 相对的情形区分**——
那需要 manifest 自己声明约定，是 schema 的改动，不是检查能做的事。

## 作用域（H4）

check 10 此前继承了「只看 archive_material」的过滤器，而这让它的名字成了谎话：
`20260729T080000Z-E14-crash-is-not-a-finding` 有 23 条在 run 目录下解析不到的路径，
它绿是因为没有 ledger，`classify` 把它判成 `process_record`，于是**每一道检查**都跳过它。

换成「本提交装运了这份 MANIFEST.json 吗」：

| | runs | listed paths |
|---|---|---|
| 换之前 | 12 | 107 |
| 换之后 | 35 | 161 |

这个过滤器同时是 1 的代价的付款方：在飞的 run（manifest 未提交）对这道检查不可见，
而这是正确的而不只是方便的——只有克隆的读者也看不见它。

## 验证

* `python -m pytest -q tests/test_files_in_clone.py` → 19 passed。
* **五条变异全部咬住**（`mutate.py`，逐条改实现、跑对应测试、还原）：
  manifest 改回从磁盘读 / anchor 恒为 run 目录 / 去掉作用域过滤 / `ls-tree` 换回
  `ls-files` / 混用分支永不触发。没有一条幸存。
* `python -m armtools.verify_provenance` → 10 checks，全绿；check 10 的
  detail 现在自报口径：`35 manifests this commit ships, 161 listed paths`。

一个 fixture 上的坑，记下来因为它差点把最关键的那条断言变成同义反复：
`_commit` 最初写成 `git add <paths>` + `git commit`（无 pathspec），
那会把**整个索引**提交进去——包括
`test_check_ten_asks_the_commit_not_the_disk` 故意留在暂存区、
永不提交的那个 `staged.json`。唯一区分「索引」与「提交」的断言会因此恒真。
`commit ... -- <paths>` 修掉；`--allow-empty` 与 pathspec 可以同用，实测过。

## 还没做

* **H1 / D1**（check 8 不再重导 `files[]`，交给 check 10 独占）：H3 是它的前置，
  前置现在成立了。
* `_rule_file_is_in_the_repository` 仍然问 `git ls-files`——**同一个缺陷、隔一个函数**：
  暂存但从未提交的 `.gitignore` 会被算作「仓库自己的规则」。方向上失败得安全
  （倾向于**列出**产物）不适用于这里：它会解释掉一条本该红的缺失路径。
  没有在本轮一并改，因为它同时喂 `build()`，会动到 check 8 的逐字节可复现性，
  应当单独一个提交、单独一次对抗复核。
