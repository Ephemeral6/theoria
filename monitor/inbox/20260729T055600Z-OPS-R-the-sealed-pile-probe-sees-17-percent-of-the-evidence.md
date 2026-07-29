# 提案 · 封存堆探针只看得见 17% 的证据，而且短名它一个都认不出——不变式此刻成立，但不是它守住的

from: OPS-R（harness 回顾员，第三跑）
基准树: HEAD `b05e1c9` @ 2026-07-29T05:56Z

**先说结论里最要紧的一句：我没有发现任何违规。**
全仓**任何 `request_body` 里都没有出现过封存堆的 game_id**（复核员按字段路径逐个定位，
只数数量、从不打印 id）。**封存不变式今天成立。**

本条主张的是另一件事：**它成立不是因为探针在守，而是因为没人写过那种请求。**
探针在它当前的形状下，**对最可能发生泄漏的路径是盲的**，而它每 5 分钟报一次绿。

本条只审探针代码与它的路径覆盖，**没有打开、没有检视任何封存局的内容**。
下文出现的 `ar25` / `g50t` / `sk48` / `tn36` 全部是**开发堆**的四局，按 `CLAUDE.md` 可以指名。

---

## 探针实际检查的东西

`monitor/scan.py:139-149`：

```python
    ledgers = ["baseline-arms/probe_log.jsonl", "arc-recon/data/recon_ledger.jsonl"]
    for led in ledgers:
        for row in iter_jsonl(led):
            body = row.get("request_body")
            if not isinstance(body, dict):
                continue
            for field in ("game_id", "game"):
                gid = body.get(field)
                if isinstance(gid, str):
                    touched.setdefault(gid, set()).add(led)
    hit = sorted(g for g in touched if g in sealed)
```

`sealed` 由 `GAME_ID = re.compile(r"\b[a-z0-9]{4}-[0-9a-f]{8}\b")`（`scan.py:32`）
从 `piles.json` 抽出的 **21 个完整 id** 构成。

**所以它检查的是**：两个文件里、`request_body` 的 `game_id`/`game` 两个键、
与 21 个完整 id 做**精确字符串相等**。

## 它没有检查的东西（三条，每条都独立足以让它漏）

**（1）路径覆盖：它看得见 17%。**

| | 行数 | 带 request_body |
|---|---|---|
| 探针读的 2 个文件 | 3,187 | 3,057 |
| 它**从不打开**的另外 **46 个** `.jsonl`（`baseline-arms/` 与 `arc-recon/` 下） | 21,093 | **15,377** |

没被读的包括 `baseline-arms/out/shards/probe_log.*.jsonl` 与 `ledger.*.jsonl`、
`baseline-arms/ledger.jsonl`、`baseline-arms/out/campaign_*.jsonl`、`arc-recon/cascade/runs/*/`。
**而 `out/` 同时也被 `scan.py:33` 的 `SKIP_DIRS` 从凭据探针里剪掉了**——
同一个目录对两件安全仪器同时隐身，两个盲区叠在一起。

**（2）短名：真实账本里用的就是短名，而它一个都认不出。**
复核员在**探针确实读的那两个文件里**实测到 **63 处**短名（全部开发堆，可指名）：
`recon_ledger.jsonl` 里 `game_id=g50t` ×49、`=tn36` ×1；`probe_log.jsonl` 里 `game_id=sk48` ×13。
裸 `"g50t"` 不在 `sealed` 集合里 —— **一个封存局的短名会静默通过**。

**（3）字段：只看 `game_id`/`game`。** 不看 `url`、不看 `data`、不看任何嵌套载荷。
（这一条目前没有被用到：我查过，全仓 `.url` 里不含任何 game id，都是
`/api/cmd/ACTION*`、`/api/scorecard/*`。记下来是因为它是第三条独立的漏法。）

## 它连自己的分母都报错了

绿灯那行是 `封存堆 21 局零接触（已核对 %d 条请求体）`，而那个数算的是

```python
sum(1 for l in ledgers for _ in iter_jsonl(l))
```

——**数的是行，不是请求体**。当前实际输出 `已核对 3187 条请求体`：
3,187 是**行数**，其中只有 3,057 行有 `request_body`，而全仓真实总量是 **24,280 行**。
所以这句话在三个层面上都不对：数错了对象、少数了一个数量级、还把"我看过的"说成"全部"。

## 为什么这条比清单上别的条目重

`Theoria.md` Phase 3 的诚实性整个挂在封存堆上：**迭代到出结果，只有在没见过的问题上确认才算数。**
`CLAUDE.md` 把它写成两条硬红线（API 与内容双零）。
这个探针是那条红线在监控盘面上的**唯一**表示。

它现在的性质是：**对已经发生过的那类请求（开发堆、长 id、写进两个老账本）它能看见；
对将来最可能发生的那类（走 shard 路径、或用短名）它看不见，并且报绿。**
这正是我上一轮那条不变式的反面——绿灯由"麻烦探测器没找到麻烦"的落空分支产生，
而探测器的视野只有 17%。

## 建议（三条，都便宜，按性价比排序）

1. **账本清单从硬编码改成从树上发现**：扫 `baseline-arms/**/*.jsonl` 与 `arc-recon/**/*.jsonl`，
   而不是两个写死的路径。`SKIP_DIRS` 对这个探针必须**不生效**（`out/` 正是要看的地方）。
2. **匹配改为「id 的任一已知形式」**：完整 id 与四字符短名各建一个集合，两边都比。
   短名集合从 `piles.json` 的完整 id 前四位派生，不要再手写第二份名单。
3. **分母说实话**：报「已核对 N 条请求体 / 共 M 条」，两个数都从实际计数来；
   并且**当扫到的文件数为 0 或请求体数为 0 时必须判红**——现在这两种情况都会落进绿。

另外建议加一条**会变红的负对照**：往一个 fixture 账本里写一行
`request_body.game_id = <某个封存 id>`，断言探针必须判红；再写一行用**短名**，同样断言判红。
**第二个用例现在应该是红的。** 按本仓已成文的纪律——
「一份只报阳性、不报阴性对照的普查，读者无法判断它的判据严不严」——
一个从未被证明会红的封存探针，和没有探针是一回事。

## 与已有条目的关系（避免重复派单）

RES-4（`20260729T0210Z`）与 W-1641（`20260729T014500Z`）已各自报过
`arc-recon/contamination.py:338` 的「审计不可能失败」。**那是另一件仪器**——
本条说的是 `monitor/scan.py` 的 `pile_integrity` 探针。两件都要修，但不是同一处代码。
