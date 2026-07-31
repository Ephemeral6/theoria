# H3：那道为终结机器相关性而写的检查，自己是机器相关的

分诊表 `runs/20260730T1230Z-A3-ADVERSARIAL-TRIAGE/TRIAGE.md` 的 H3。
H1 的推荐设计 D1（check 8 不再重导 `files[]`，交给 check 10 独占）以它为前置：
判据只要还是 `os.path.exists`，D1 就只是把机器相关性从一道检查搬到另一道。

## 一、修了什么

`check 10` 问的不再是「这个文件在不在这台机器的盘上」，而是
**「这个仓库装运它吗」**——`git ls-files` 读索引，完全不看工作树内容。

| 场景 | 旧判据（`os.path.exists`） | 新判据 |
|---|---|---|
| 被跟踪 | 绿 | 绿 |
| 未跟踪、但被一条**被跟踪的** `.gitignore` 规则解释 | 绿 | 绿 |
| **在这台机器上存在、任何地方都没被跟踪** | **绿**（这就是 H3） | **红** |
| 被跟踪、但从本工作树删掉了 | **红** | **绿**（克隆里有它，盘上缺是这台机器的事） |
| 绝对路径 `C:/Windows/win.ini` | **绿**（`os.path.join` 把 run 目录整个丢掉） | 红，且判词说「not a path inside the run」 |
| `../../` 逃出 run 目录 | **绿** | 红，同上 |
| 目录而非文件 | **绿** | 红（git 不跟踪目录，自动落进「未装运」） |
| `git` 问不出来（无 git / 不在仓库里） | **绿**（文件在盘上，而那就是全部问题） | **无答案**——第三个判词，不是绿也不是「全部 dangling」 |

两个方向都要：只加「必须被跟踪」而保留「必须存在」（mutation M4）会**保留**机器相关性、
只是多加一个条件。所以「被跟踪但本地删了」必须是绿的，克隆才是基准。

形状判定用**纯字符串**，不用 `os.path.realpath`：realpath 解析符号链接要问磁盘，
于是它自己能在两台机器上给两个答案——正是本次要修的病。路径的**形状**是 manifest 的属性，
而 manifest 在每个克隆里都一样。

## 二、诚实地说清这次修的是什么，不是什么

**归档今天的判词一个字没变。** 派出去的测量 subagent 用真 `backfill.survey` /
`_ignored_paths` 逐条量了 12 个 `archive_material` run 的全部 **107 条 listed path**
（`runs/20260730T1400Z-A3-H3-SCOPE/scope.json`，脚本可重跑）：

* **「在盘上但没被跟踪、也没被规则解释」的路径：0 条。**
* 换判据后**新增 dangling：0 条**。107 条改前全过、改后全过。
* 被跟踪 103 / ignored-present 1 / ignored-absent 3；目录 0、绝对路径 0、逃逸 0。

所以 **H3 是一个真实的缺陷，但今天没有任何东西在利用它**——它是这道检查的性质缺陷
（在 fixture 里可复现、五个 mutation 全被抓），不是当前归档里的一处污点。
这条必须写在最前面：本 leg **没有**「发现 N 条悬空引用」，它把一道**在未来会说谎**的
检查改成不会。上一 leg 的教训是把近似当等式，这一条是它的孪生——**别把「修好了一道
检查」讲成「修好了归档」**。

## 三、测量顺带给出了本 leg 最实的一条：H4 有 23 条，且判据修不到

同一次测量越过了 check 10 的**作用域**去看那 32 个非 `archive_material` 的 run：
9 个有 manifest，合计 51 条 listed path，其中 **23 条是真的悬空**——
全部在 `runs/20260729T080000Z-E14-crash-is-not-a-finding` 里，
全部是**仓库根相对**的写法（`theoria-arm/runs/.../REPORT.md`、`a0-spike/pipeline/adapt.py`），
相对 run 目录一条都不存在，也没有任何规则解释它们。

它们绿只是因为**没被看**：E14 没有 ledger records、却有 MANIFEST.json，
于是 `classify()` 判它 `process_record` → `archive_material` 为假 → 每道检查都跳过。

**所以 H4 才是有咬合力的那一条，而它不在判据里、在过滤器里。**
`archive_material` 不是一个布尔表达式，是 `classify()` 每个分支上的字面量；
等价说法：有 ledger 记录、且抵达过非 loopback upstream、且 slug 不是 fixture glob。
本 leg **没动**这个过滤器：把它放宽会同时拉进 23 个 `process_record` run，
并且要先裁决 E14 那套「仓库根相对」是**第二种合法约定**还是**一份不合规的 manifest**——
那是一个判断，不是顺手改。已按严重度记入 TRIAGE 的下一步。

## 四、这些测试真的咬得住吗——mutation 有 harness、有输出文件

`mutate.py` 可重跑，输出 `mutations.json`。五个 mutation，全部被抓，
且各自被那条以它命名的测试抓：

| mutation | 抓它的测试 |
|---|---|
| M1 判据退回 `os.path.exists` | `test_check_ten_asks_the_index_not_the_disk` |
| M2 形状闸门恒真 | `test_check_ten_rejects_a_path_that_is_not_of_this_run` |
| M3 第三个判词退化成空集 | `test_check_ten_has_no_answer_rather_than_a_green_when_git_cannot_be_asked` |
| M4 要求「被跟踪**且**存在」 | `test_check_ten_asks_the_index_not_the_disk` |
| M5 检出形状错误但不判红 | `test_check_ten_rejects_a_path_that_is_not_of_this_run` |

**这个 harness 第一次跑是假的，值得写下来**：它把臂单独拷进 tmp 目录，
而臂要从仓库根 import `proxy.spend_gate`，于是五次全是
`Interrupted: 1 error during collection`——五个 `caught=True` 量的是它自己的 import 失败。
本 leg 第三次遇到「守卫通过但什么也没断言」。所以现在**先跑一次未突变的对照**，
对照不绿就整份结果作废（`control` 字段落在 `mutations.json` 里，`survivors` 单独一栏）。
判据也从「pytest 非零」收紧为「pytest 非零**且**不是 collection error」。

同一个原因也改了一条**已有**的测试：`test_check_ten_catches_a_dangling_reference`
的 fixture 只把 `certify.json` 写到盘上、没有 `git add`。新判据下它本该是红的——
也就是说那条测试里「present → 绿」的那半个断言，验的是旧缺陷。现在 fixture 真的 add。

## 五、状态

* 273+3 测试；`verify_provenance` 十项；`verify.py`——命令与结果见本目录 `MANIFEST.json` 的兄弟提交说明。
* 零 API、零花费、封存堆零接触（只读 `piles.json` 的 id 列表都没做）。
* H1 仍然开着：本 leg 只是把它的前置条件拆掉了。D1 现在可以做，但要连同 check 8 的
  名字一起改——「byte for byte」的例外必须写进检查名，不是注释。
