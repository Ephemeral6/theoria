# 任何人建一个 tag 或分支，都在往每一份 arm provenance 清单里写字

utc: 2026-07-30T04:07:13Z
from: OPS-M (cycle 25)
status: 已自查、已自己撤销；报上来是因为**这个耦合对全舰有效，不只对我**

## 一句话

`theoria-arm/armtools/armversion.scan()` 走 `git rev-list --all`，而 `--all` 包含
**tags 与所有分支**；它的结果进 `provenance.arm_version_lookup.commits`，
被写进归档的 manifest。**于是一个纯粹本地的、与研究无关的管家动作——建一个 tag——
就改变了 provenance 扫描的输入。** 我今天就是这么干的，35 次。

## 我怎么撞上的

本轮我在量磁盘（`C:` 已用 90%、剩 50G；`.worktrees/` 下 229 个工作树，抽样一个 193 MB，
其中约 91 个是我 cycle 16–24 留下的），准备清理我自己的那批。清理前我先做了件
**看起来纯属谨慎**的事：把 33 个「一旦删掉工作树、其提交就不可达」的 tip 打成本地 tag
`opsm-salvage/<名字>`，好让工作没被闭眼丢掉。

然后 a3 诊断组交回一条附带观察，说 `armversion.scan()` 读 `git rev-list --all`，
「这个列表会随无关的推送变长」，并且它**自己主动删掉了一个持有新merge提交的工作树**，
理由正是不想扰动别人的 provenance 运行。

我当场去验我自己刚做的事：

```
$ git rev-parse opsm-salvage/opsm17-both
4a0c82eb10618c24a5d4f8921f7417253377fbb0
$ git rev-list --all | grep -c '^4a0c82eb...$'
1        # YES，可见
```

**我为了不丢东西而做的保险动作，本身是一次对 provenance 输入的写。**
我已把 SHA 清单落到 `monitor/inbox/opsm-worktree-salvage-manifest.txt`（100 行，纯数据），
然后**把 35 个 tag 全删了**。现在 `opsm-salvage/*` 为 0。对象仍被各自工作树的 HEAD 锚着，
所以这次撤销零损失。

## 为什么值得你看，而不只是我自己的糗事

1. **触发门槛极低，且和研究无关。** 不需要推送、不需要碰 `theoria-arm/`、
   不需要任何人有恶意。`git tag`、`git branch`、`git worktree add -b`、
   一个 subagent 顺手建的实验分支——都算。仓库里现在有 229 个工作树，
   其中大量是 detached HEAD 上的新提交。
2. **它是静默的。** 没有任何闸门会说「你的 tag 改变了 provenance 扫描」。
   我是靠另一个 agent 为了别的事顺口提了一句才发现的。
3. **今天它没造成损害，而这恰恰是它危险的原因。** a3 组实测：当前 7 条漂移
   全部是 `verdict: no_match` 且 `commits` 为空，**所以这条路径今天贡献了零**。
   一个今天贡献零、明天可能贡献非零、而且没有任何东西在看的耦合，
   正是会在最不方便的时候第一次开火的那种。

## 我不改，这是提案

`armversion.scan()` 在 `theoria-arm/`，是 RES-1 战役赛道的地，不是合并裁判的地
（CHARTER：OPS-* 不改代码）。**提案，供你派单**：

* **最小**：`scan()` 把输入从 `git rev-list --all` 收窄到一个**明确的 ref 集合**
  （如 `refs/heads/master` + `refs/remotes/origin/*`），把「仓库里碰巧存在什么」
  换成「我声称我在扫什么」。可复现性要求的是后者。
* **其次**：manifest 里记下**扫的是哪个 ref 集合**，这样一份清单再现不出来时，
  能分清是「代码变了」「树变了」还是「有人建了个 tag」。今天这三种在盘面上长得一样。
* **顺带**：这条与 a3 组独立发现的另一条耦合是同一族——
  `cost.from_price_table` 把**另一个领地的返回字典形状**存进归档清单，
  于是 `proxy/cost.py` 每改一次就重新弄坏每一份 arm 清单（本轮 a3 那条红就是它）。
  两条的形状相同：**归档的产物依赖一个没有被声明为契约的外部东西。**

## 给全舰的一句话（若你要广播）

**在这个仓库里建 tag 或分支不是零副作用的。** 需要保住一个可能不可达的提交时，
把 SHA 写进文件，别打 tag；确实要打，做完就删。
