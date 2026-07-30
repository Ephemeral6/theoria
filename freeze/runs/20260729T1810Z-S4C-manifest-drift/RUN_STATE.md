# S4-freeze-complete · 冻结清单已经和树对不上了，而没有任何东西在看

RES-1 cycle 34，2026-07-29。领到 S4-freeze-complete 后的第一件事是查现状，
第一查就红了。

## 一、`build_manifest.py --verify` 说自己该在闸里，而它不在任何闸里

`freeze/build_manifest.py` 的 docstring 写得很清楚——它自己就是为了治
「手抄哈希表」而写的，理由是实测：某份手写草案**三十三个哈希里十九个**
在一天后就已经不对，两条判定甚至整个翻转。它给出的规矩是：

> the manifest is generated from git at a pinned commit, and `verify` fails
> if the tree it is regenerated against no longer produces it.

并且明写 `--verify` **is what belongs in a gate**。

`grep build_manifest freeze/verify.sh` → **零命中**。写好了、对的、
有 `--verify`、在自己的文档里点名说该进闸门，**没有任何闸门调它**。

这与本轮早些时候在 theoria-arm 抓到的是同一个形状（函数存在、正确、被测过、
从没被调用），也与 A16 要在花钱路径上堵的是同一个形状。**一天之内第三次。**

## 二、它确实已经漂了

`python freeze/build_manifest.py --verify` → **exit 1，DRIFT**。

重新生成后逐叶对比，13 处变化：

* **12 个内容哈希**过期（entries 4/7/8/9/10/12 下的 `paths[].sha256`）；
* `generated_from.commit` `5427a78a` → `eaeddc14`；
* `generated_from.dirty` **`true` → `false`**。

最后那条自成一件事：**清单是在一棵脏树上生成的**。脏树生成的清单无法从任何
提交复现，而「可从某个提交复现」正是这份文件存在的全部意义。它当时就不成立，
只是没人问。

## 三、修法

* 重新生成 `freeze/MANIFEST.json`（干净树，`eaeddc14`）；
* `verify.sh` 新增 **第 12 阶段**调 `build_manifest.py --verify`。

**判成硬失败，不是 NOTE**，与第 11 阶段有意不同：
第 11 阶段的 `BLOCKED` 是 NOTE，因为一条诚实地没清的 blocker 是**关于未完成套件的真陈述**；
而漂了的清单是**关于已完成套件的假陈述**，并且假在「声称得更多」的方向上。
两者该有不同的处置。

## 四、负对照（实测）

把 `MANIFEST.json` 换回漂掉的那版再跑 `verify.sh`：

```
[12] MANIFEST.json still describes this tree
  FAIL  MANIFEST.json has drifted from the tree -- regenerate and read the diff
EXIT=1
```

改回来后 `EXIT=0`，十二个阶段全绿（两条 NOTE：§9 三条 blocker 未清、以及原有那条）。

## 五、S4-freeze-complete 还剩什么

本轮做的是让清单**先变成真的**——在此之前，往上加任何一项都是往一张对不上的表上加。
工单主体（13 项逐项钉到具体路径+版本、缺的标明缺什么谁的）仍未完，
`MANIFEST_DRAFT.md` 总览表里 ⛔ 两项（5 引擎清单、12 预算表）与 ⚠ 八项照旧。
另有 `MANIFEST_DRAFT.md` 里自记的待办 **H-1**（仓库根缺全局 `.gitattributes`
`text=auto eol=lf`，导致工作树哈希跨 checkout 不可复现）也仍开着——
本轮的哈希纪律走的是 git blob 而不是工作树文件，所以不受它影响，但冻结前要选一个。
