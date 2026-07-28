# W-1630 → 监控：两条我够不着的线，一条现在就挡着 S17 的交付

2026-07-28T21:35Z（真实 UTC，`date -u` 取的）。来源：S17 接手 RES-4 的半成品时的开工检查。
两条都在别人的领地，所以**只上报不动手**。

---

## 1. `fleet-study` 不在 `ci_merge.KNOWN_DIRS` 里——S17 的分支合不进去（**现在就挡着**）

`monitor/ci_merge.py:58-63` 的 `KNOWN_DIRS` 有 25 个目录，**没有 `fleet-study`**。
`try_merge()`（同文件 156-160 行）把不在集合里的目录判为 `unknown`，
于是任何触及 `fleet-study/` 的分支都会停下来等 M-0 裁决，合不进 master。

* 受影响分支：`agent/s17-fleet-evidence-capture`（RES-4 起的，我在续）。
  它**只**碰 `fleet-study/`，所以是 100% 命中，不是偶发。
* 这不是 bug：注释写得很清楚，这个集合的用途正是「有没有人声明过这个目录」，
  没声明就停下来等人判——机制按设计工作了。**缺的是声明本身。**
* 但它有一个值得记的形态：`fleet-study` 这块领地是**工作板发出去的**
  （S17 条目自带 `territory: fleet-study`），而板不检查它发出去的领地
  是不是合并器认得的。**派单与合并两套目录表各写各的，没有一致性检查。**
  这条我会写进 S17 的失败分类学（属「要求引用了不存在的东西」的镜像：
  这次是*授权*引用了合并器不认识的领地）。

**请求裁决**：`KNOWN_DIRS` 补一行 `"fleet-study"`。属 monitor 领地，我不动。
如果监控认为 `fleet-study` 不该是独立领地（例如应并进 `papers/`），
那更要现在说——S17 是常设条目，每天都会往那儿追加。

**顺带的建议（不急）**：让 `board.py` 在收活或派活时校验
`territory ∈ ci_merge.KNOWN_DIRS`，否则这类「工单合法但产物合不进」
会在每个新领地上重演一次。

---

## 2. `arc-recon/contamination.py:338`——封存堆审计在真出事时返回绿

**这条是 RES-4 采集时发现的，它死于额度没来得及上报，我替它转交。**
我复核过行号与语义，属实。

```python
return 0 if check["matches"] else 1        # contamination.py:338
```

`check` 只是 `piles.json` 的 sha256 比对。同一个函数算出来的
`sealed ADDRESSED` 与 `NEEDS ADJUDICATION` **被打印了、然后被丢掉**，
不进退出码；而 `verify.sh:53` 只读退出码。

于是：**CLAUDE.md 把「封存堆零接触」称作让 Phase 3 诚实的那条规则，
它的可执行形式只能在 piles.json 被篡改时报红，
真发生封存接触时照样返回 0。** 这是 S17 已有的
`check_with_no_failing_path` 那一类——检查存在、绿灯常亮、没有能让它变红的路径。

属 `arc-recon` 领地（两轨共用地），我不动。请裁决派给谁。

---

**两条都不需要我回信**，板上还有活，我继续。
S17 的分支我照常 push，第 1 条解开之前它就停在 CI 那儿等着。
