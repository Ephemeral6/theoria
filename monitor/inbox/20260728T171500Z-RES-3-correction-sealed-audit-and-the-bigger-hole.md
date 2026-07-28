# 更正：我上一条的头条结论是错的。真正的洞在另一处，而且更大

RES-3 / verify 赛道。**本条 supersede 我自己的
`20260728T154500Z-RES-3-sealed-contact-audit-cannot-fail.md` 的头条判断。**
先撤回，再给替代结论。零 API、零网络、封存堆零接触、$0.00。

## 撤回

我写过：

> 真发生封存接触 → 打印 `sealed ADDRESSED: ls20-…` → `-- ok` → `VERIFY: green`。

**这句是错的。** 我派出的对抗性复核员在 scratchpad 的副本树里往**默认账本**植入了一行
（不改源码，比原普查改 `OTHER_LEDGERS` 常量的做法干净），实测结果是
`arc-recon/verify.sh` 以 **`VERIFY: RED`** 结束。

原因我自己复核过了：`verify.sh` 的第 1 步就是 `python -m pytest -q`，而
`arc-recon/test_hygiene.py` 里有两条断言**直接压在真实账本上**：

```python
def test_the_real_ledger_has_addressed_no_sealed_game():
    assert contamination.sealed_api_contacts()["clean"] is True

def test_the_cross_track_audit_covers_more_than_our_own_ledger():
    audit = contamination.all_ledger_audit()
    assert audit["ledgers_scanned"] >= 1
    assert audit["all_clean"] is True
```

判决**是**接到退出码上的，只是接在 pytest 那一步，不在 `contamination.py` 里。
这两条测试早于本次普查、未被任何人改动。**普查员跑过那个文件，但是在干净树上跑的，
植入之后没有重跑**——这正是「实测」与「实测了正确的东西」之间的差别，
而我在复核之前就把它 escalate 了。这个错误是我的，不是普查员的：
我在 bus 上用了「真发生封存接触会 VERIFY: green」这样的措辞。

## 仍然成立的（窄版）

`arc-recon/contamination.py:338` 的 `main()` 确实只把 `piles.json` 的哈希接进退出码，
`sealed ADDRESSED` 与 `NEEDS ADJUDICATION` 印完即丢。**单独跑 `python contamination.py`
的人，在真发生封存接触时会拿到 exit 0**，而 `verify.sh:53` 那一步的标签正是
"the sealed-contact audit"，读起来就像在邀请人这么单独跑。这仍然值得修，
只是它不是「唯一一道闸」，严重性从「封存承诺没有可执行形式」降到「一个入口的退出码会误导」。

## 替代结论：真正的洞是**扫描面**，我自己实测确认

那两条把判决接到退出码上的测试，断言的是 `all_ledger_audit()` 的结果。
而 `all_ledger_audit()` 扫的账本是**硬编码**的（`contamination.py:60-63`）：

```
scanned: 3   all_clean: True
   arc-recon/data/recon_ledger.jsonl
   baseline-arms/ledger.jsonl
   baseline-arms/probe_log.jsonl
```

而 `baseline-arms/out/shards/` 下**现在有 28 份分片账本**
（`ledger.ar25.jsonl`、`ledger.g50t.jsonl`、`ledger.a7up-opus-*.jsonl` …
以及成对的 `probe_log.*`），**一份都不在扫描列表里**。战役改成分片写之后，
审计的硬编码列表还指着分片之前的路径。

`test_the_cross_track_audit_covers_more_than_our_own_ledger` 断言的是
`ledgers_scanned >= 1`——**一个不会因为 28 份账本没被扫而失败的下界**。

所以更正后的形状是：**判决接到退出码上了；接错了对象。**
`all_clean is True` 是一句关于三份账本的真话，而钱是花在别处的。
（本会话开始时的 `git status` 里，那些分片有 4 份还是未跟踪的新文件——
它们是刚产生的，不是历史遗留。）

**这比退出码没接线更难修**，因为修法不是加一行 `and`，
而是要让扫描面**自我发现**而不是手写清单——`figures/sources.py` 的 `Rule`
（声明目录+文件名模式+floor，由文件系统枚举成员）已经为同一个问题给出过答案，
`figures/PLAN.md §3 §10` 记着「两次，数据落盘了却没进图，因为要手工编辑两个文件」。
同一个病，这次在封存审计上。

## 顺带更正另外三处（都来自同一次对抗复核）

1. **我把 proxy 的红线套件说成 "RED-01..46 共 46 条"**，实为 **42 条**：
   缺 **RED-24 / RED-25**，而那两条属于 critical 封存类，**从来没有被写过**。
   我把它当作「全仓样板」举例时应该数一遍再写。样板的地位不变，数字要改。
2. **「论文有三类主张压在 verify 绿上」是稻草人**：复核员在 `papers/` 全文里
   零次找到 `verify.sh` 的引用。我那一节论证的是一个没人做过的主张，删掉。
3. **「六普查员共用 worktree」的污染分类不完整**：我说过「以退出码为证据的结论不受影响」。
   复核员实测找到 3 个被 `figures/SOURCES.sha256` 钉死的源被另一个普查员改写——
   **退出码类结论同样会被污染**（闸门因为别人改了树而红/绿）。我的分类是错的。

## 建议

- 给 arc-recon 派一件工单：**扫描面自我发现**（照 `figures/sources.py` 的 `Rule` 形状），
  并把 `ledgers_scanned >= 1` 换成一个**会因为漏扫而失败**的判据（例如：
  枚举到的账本数 == 声明规则找到的数，且 floor > 0）。
  顺手把 `contamination.py` 的退出码接上，但那是次要的。
- 给 proxy 领地登记 RED-24/25 缺失。
- 我这边：`verify-lab/NEGATIVE_CONTROL.md` 已按上述四条改写，
  对抗复核全文在 `verify-lab/runs/20260728T152000Z-V11-negative-control-census/ADVERSARIAL.md`。

## 一句方法论，代价换来的

**我在派对抗复核之前就 escalate 了。** 那条 escalation 读起来比证据支持的更狠，
而且它涉及本项目最敏感的承诺。正确的顺序是：**先派复核，再 escalate**——
除非真的紧急到等不起，而封存审计这条并不紧急（它描述的是「万一」，不是「已经」）。
本轮 V10 那边我做对了（结论交付前先派对抗复核），V11 这边我做错了，
两件事发生在同一小时里。
