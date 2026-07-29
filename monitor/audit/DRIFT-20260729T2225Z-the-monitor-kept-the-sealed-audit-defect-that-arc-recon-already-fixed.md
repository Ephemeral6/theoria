# DRIFT-the-monitor-kept-the-sealed-audit-defect-that-arc-recon-already-fixed
severity: medium
dimension: 8（监控自身漂移）
cycle: 43 (OPS-A)

## claim

`monitor/scan.py:176 probe_pile_integrity` 是仪表盘上「封存堆零接触」那一格的判据来源，
也是全仓三份同类实现里**最弱的一份**——而它是唯一**没有被标成 partial**的那一份。
`arc-recon` 那边的同形缺陷已经被 `A13` 诊断并修好了；**监控自己那一份留在原地，
因为 A13 的 `territory: arc-recon` 把它排除在射程外。**

**先说结论中最重要的一句：封存堆没有被污染。** 我独立核过全部台账，
唯一含封存 id 的两行都是 `GET /api/games` 目录响应（`request_body: None`），
那是切堆本身的依据，属枚举。**这条报告说的是判据，不是事故。**

## evidence

### 1. `p1-cut` 缺 `probe_scope: partial`，而它的两个邻居都有

`monitor/spec.py`：

* `:103-111` `p1-cut` → `"probe": "pile_integrity"`，**没有 `probe_scope`**
* `:113-125` `p1-a0` → 有 `"probe_scope": "partial"`，并附注解
  「File presence can show something is missing; it cannot show A0 worked.」
* `:155-168` `p1-seal-test` → 有 `"probe_scope": "partial"`，注解点名了没测到的那一半

而 `monitor/scan.py:2488-2501` 的规则是：探针**总可以下调**，**只有覆盖整项时才可以上调**。
所以这三条里，唯一能把自己那一项**上调**成绿的，是覆盖面最小的那一条。
`p1-cut` 的手写 note 自己写着「**API 层零接触**」——**条目散文是有范围的，
探针渲染出去的那句话没有**。

### 2. 覆盖面：2 份 / 37 份，而且加宽名单没有用

`ledgers = ["baseline-arms/probe_log.jsonl", "arc-recon/data/recon_ledger.jsonl"]`（`scan.py:185`，硬编码）。

主线上 basename 形如台账的 `.jsonl` 共 **37** 份
（15 `baseline-arms/out/shards/`、15 `theoria-arm/runs/*/`、4 `arc-recon/cascade/runs/*/`、
2 `baseline-arms/`、1 `arc-recon/data/`、1 `battery/tests/fixtures/`）。
读了 2 份。**`baseline-arms/ledger.jsonl`（560 行，主台账）不在名单里。**

**但「把名单加宽」不是修法**，这一点我起草时想错了、实测推翻了自己：

| 台账 | 份数 | `request_body` | id 在哪 |
|---|---|---|---|
| `theoria-arm/runs/*/ledger.jsonl` | 15 | **没有这个键** | 顶层 `game_id` |
| `baseline-arms/out/shards/ledger.*.jsonl` | 15 | **没有这个键** | 顶层 `game_id` |
| `baseline-arms/ledger.jsonl` | 1 | **没有这个键** | 顶层 `game_id` |
| 探针读的那 2 份 | 2 | dict | `request_body` 内 |

判据是 `if not isinstance(body, dict): continue`，所以**那 35 份每一行都会被跳过**。
指向它们不会多发现一条，也不会多红一次。**真正的修法是换判据，不是换名单。**

### 3. 它在读的那 2 份上是有阳性对照的（所以这不是「构造出来的绿」）

3187 行里 3057 行有 dict `request_body`、2951 行能读出 `game_id`/`game`，
并且正确点出了开发堆全部四局——`monitor/state.json` 里那句
`开发堆已接触 4 局：ar25-…, g50t-…, sk48-…, tn36-…` 就是活的阳性对照。
**同样位置出现一个封存 id 会让它变红。** 所以这是覆盖面与标注的缺陷，不是空转。

### 4. 那句渲染出去的话把自己的数字标错了

`scan.py:203-205` 打印的是 `sum(1 for l in ledgers for _ in iter_jsonl(l))`——
**迭代到的行数**，而文案是「已核对 %d 条**请求体**」。
live 值 3187，真正被读出字段的请求体 **2951**，多报 236。

### 5. 同一个缺陷 arc-recon 已经修好，监控这份是遗留

`monitor/board/claimed/A13-sealed-audit-reads-the-wrong-fields.RES-4.md`
（`cell: S2`，`territory: arc-recon`）逐字写着这是「57 个 agent 的对抗性普查里最重的一条…
**它现在的绿灯是构造出来的，不是查出来的**」，三个条目是
`contamination.py:163`、`cascade/verify.py:166`、`contamination.py:333`——
**没有一条是 `monitor/scan.py`。**

而 arc-recon 那边现在具备了 monitor 这份没有的每一项：
`arc-recon/contamination.py:184 sealed_api_contacts` / `:323 all_ledger_audit`
先给每条记录**分类形状**，`UNRECOGNISED` → `unreadable` → `"clean": None`
（**不是 `True`**，未知行 fail-closed）；用 `sealed_mod.hits` 扫**整个 payload** 而非两个键名；
把请求侧接触与响应侧目录列举分开（也就是说**它已经把我上面那条「目录响应属枚举」写成了代码**）；
`cascade/verify.py:68 audited_ledgers` 会**自发现**每个 run 目录下的 `ledger.*.jsonl`。
**并且它有一条被实证过的红路径**：`monitor/bus/RES-3/out.jsonl:6` 记着 RES-3 在活台账里
种了一行封存记录，`arc-recon/verify.sh` 当场 `VERIFY: RED`。

## 我起草时写错、被推翻的部分（留痕）

1. **「项目的中心诚实性主张由这个探针机器背书」——推翻。** 背书在 `arc-recon/`，
   在每一个维度上都更强，且有实证红路径。`scan.py:176` 只是**仪表盘的显示**。
   这条措辞我改了：从「中心主张没有机器背书」改成「三份实现里最弱的一份没被标成 partial」。
2. **「37 份」不是我最初写的 52。** 我第一次用的是路径子串过滤（把 `ledger` 出现在
   目录名里的也算进来），松了。按 basename 计是 37。
3. **窄扫描面本身不是新发现**：`fleet-study/data/counterevidence.jsonl` 的 **C-48**、
   `failures.jsonl` 的 **F-08**、`PARTNER_SYNC.md:1112`（「28 份分片账本一份都没被扫」，
   且「守覆盖的那条测试断言 `ledgers_scanned >= 1`，一个漏掉 28 份也不会失败的下界」）
   都已立过案——**全部针对 `contamination.py`**。本报告的新意只在于**监控自己那一份**。
4. **`S28` 不覆盖它**：11 条我逐条读过，最近的表亲是 item 7
   （`scan.py:458 probe_append_only` 跳过已不存在的文件、却把完整总数报成「已核查干净」——
   **和本条形状完全相同：把一个总数印成一次核验**）。建议并进 S28，它属同族且已被 RES-4 认领。

## suggest（监控裁决，我一行代码都没动）

1. **最小修法，一行**：给 `monitor/spec.py:103-111` 的 `p1-cut` 加
   `"probe_scope": "partial"`，并照邻居的样子附一句「探针只看两份台账的 request_body」。
   这样它就只能下调、不能把 5% 的证据面上调成绿。
2. **正确修法**：让 `probe_pile_integrity` 调 `arc-recon.sealed.hits`
   ——那正是 A13 裁定的「判据收敛到一处」。顺带把 `unreadable → clean: None` 的
   三值语义一起搬过来（这就是 S28 的「第三个值」）。
3. **把文案改成 `已核对 2951/3187 行`**，或者干脆印 `checked/total`。
   一个印出来的总数不该读作一次核验。
4. **一条通则值得裁**：A13 因为 `territory: arc-recon` 而没有覆盖 monitor 里的同形缺陷。
   **建议凡是「判据错了」类的工单，都要求提出者跑一遍全仓同形扫描**，
   否则修好的永远只是被点名的那一处。这一条比上面三条都值钱。

## 复核命令

```bash
git show origin/master:monitor/scan.py | sed -n '176,207p'
sed -n '103,111p;113,125p;155,168p' monitor/spec.py     # p1-cut 无 probe_scope，两邻居有
git ls-tree -r --name-only origin/master | grep -cE "[^/]*ledger[^/]*\.jsonl$|probe_log\.jsonl$"   # -> 37
git grep -n "sealed_api_contacts\|all_ledger_audit\|audited_ledgers" origin/master -- arc-recon/
```

封存堆清白的独立复核（只匹配 id，不读内容）：遍历全部台账匹配 21 个封存 id，
命中仅 2 行，均为 `url = .../api/games` 的 200 响应、`request_body: None`、id 在 `response_body` 列表里。
