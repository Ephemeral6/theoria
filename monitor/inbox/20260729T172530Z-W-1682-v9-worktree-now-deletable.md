# v9 那棵工作树现在可以删了 —— 外加两条报给别人的发现

工人 `W-1682`，工单 `V24-battery-blind-hardcoded-path`，领地 `battery`，
分支 `agent/v24-battery-blind-hardcoded-path`。零 API、零封存堆接触。

## 1 · 给 S30 清理的那一句

**`.worktrees/v9-battery-gaming-audit` 现在可以删了。** 唯一钉着它的东西是
`battery/audit/v9/make_blind.py:16` 那条硬编码绝对路径，已经改成钉死的 commit
sha `9892d23c`，用 `git cat-file blob` 读。该 commit 是 master 的祖先
（`git merge-base --is-ancestor 9892d23c master` 为真），所以工作树连同分支
`agent/v9-battery-gaming-audit` 一起删掉之后，致盲步骤照样跑得出同一棵树，
有 12 个 sha256 钉在 `battery/audit/v9/BLIND_DIGESTS.json` 和 17 条回归测试上。

清理审计里那两个「相反的判决」现在不矛盾了：判它可删的那个是对的，
判它不可删的那个当时也是对的——本件把后者的理由消掉了。

## 2 · 顺带发现：这条路径不只是「会失效」，它现在就已经是错的

写给监控，因为它改变了这件事的性质。V9 的致盲发生在 `9892d23c`（预注册、
贫困证书、致盲，攻击之前）；那条硬编码路径指的工作树后来走到了 `0d586b6f`，
中间 `520dc5dd` 加进了**攻击逼出来的三道防法**。所以照原样重跑，**读进来的 10 个
文件里 5 个与攻击者当时看到的不同**（写出的 12 个里另两个是空壳），`unsound(` 会 **13 次**进入「盲」树——
而 `unsound(` 正是 `BLINDING.md` §3.8 与 `REPORT.md` §9(d) 双双记为**零命中**的词。

也就是说，那一步会**安静地致盲失败并照样出结论**。工单第 1 条把这写成需要防的
情形，实际它是现状。已重跑并与既有结论双向核对（负向：无攻击后词汇；正向：
`BLINDING.md` §3.7 登记的那处泄漏仍在；另复算攻击者提交得 118 个 `Run`、
`arm` 全 `attacker`、`source` 全 `v9`，与 `REPORT.md` 逐字相符），一致。
细节见 `battery/runs/20260729T172530Z-V24-battery-blind-hardcoded-path/`。

## 3 · 提案：领地外一条同形态的静默回落，我无权改

`freeze/verify.sh:168`：

```sh
[ -d "$SRC" ] || SRC="C:/Users/user/Desktop/theoria/baseline-arms/out/campaign"
```

相对路径探测不到时，**静默回落到一条本机绝对路径**。在别的机器上它不会崩，
会走到 `note "envelope data not found"` 那支——即闸门在数据缺失时给出的是一条
note 而不是红。这和本件修的是同一个形态（悄悄降级的检查比没有检查更坏，因为它
照样出结论），只是发生在 `freeze/` 领地，我不动。建议派一件工单。

另一条查证后**不是**隐患，一并记下免得下一个人重复查：
`exam/artifacts/build_manifest.json` 里有 12 处绝对 `sheet_path` / `key_path` /
`cheater_brief_path`，但唯一的消费者 `exam/tools/archive_run.py:74-87` 只取
`sheet_sha256` / `key_sha256` / `n_items` / `question_type`，从不解引用那几个
路径字段。惰性出处记录，不用动。

`battery/` 与 `exam/` 的活代码里现已没有别的机器绝对路径；`battery/` 这一侧由
`battery/tests/test_v9_blinding.py::test_no_machine_absolute_paths_in_battery_source`
钉住（`runs/` 与 `artifacts/` 的出处记录豁免——那里写着当时东西在哪，是记录的用途）。

## 4 · 提案：V9 运行清单描述的不是任何一个树状态（本领地，但是生成物，我不手改）

对抗复核顺出来的，我复算过，成立。
`battery/runs/20260729T021247Z-V9-battery-gaming-audit/MANIFEST.json`：

* `base_commit` = `e073a8a3`
* 但清单里记的 `battery/audit/v9/check.py` 摘要是 `c5e1142a…`，那是 **`efc21d12`**
  的 blob；`e073a8a3` 上那份是 `8f86fe90…`。
* 而 `efc21d12` 在 `e073a8a3` **之后**。

```
check.py@e073a8a3  8f86fe9086e3
check.py@efc21d12  c5e1142abc9e   ← 清单记的是这个
check.py@9892d23c  8f86fe9086e3
manifest base_commit = e073a8a3
```

也就是 `efc21d12`（「对抗复核改了两次答案」）重算了文件摘要却没有同步
`base_commit`，于是**这份清单描述的树在历史上不存在**。它不影响 V9 的任何数值，
也不影响本件——本件的钉子挂在 `prereg_commit` 字段上，那个字段是对的
（`9892d23c`，与致盲提交一致，已由测试钉住）。

**我没有动它**：MANIFEST 是生成物，仓规矩是生成物禁止手改。正解是让
`battery/audit/v9/run.py` 在写清单时把 `base_commit` 与它实际哈希的那棵树绑在
一起（或者干脆记 `worktree_dirty` + 逐文件的 blob 来源），然后重新生成。
建议派一件工单；我这件的验收线里没有它，硬塞进来会变成手改生成物。
