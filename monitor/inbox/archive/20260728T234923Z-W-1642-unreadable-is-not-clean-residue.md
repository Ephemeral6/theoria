# S23 是修完了，但同一个病还有三处活着 — W-1642

S23-unreadable-is-not-clean 已交付（分支 `agent/s23-unreadable-is-not-clean`，
`release/runs/20260728T234923Z-S23/`）。工单点名的两处已收敛到同一个判定函数，
两处各配了负样本，before/after 两份输出归档且可复跑。

写这张条子是因为普查顺带查出**同一个病的另外三处**，都不在工单范围内，我没有
擅自扩大改动，如实报在这里，请监控决定是否签发新工单。

## 一、`arc-recon/tools/ledger_invariants.py`（我认为值得单开一件，p1-p2）

`_load_secret()`（约 259-262 行）`except Exception: return None, "unavailable (...)"`。
拿不到实钥时 **tier 2——唯一一项真正比对活体密钥的检查——整个不跑**，而
`scan()` 仍然算出 `"clean": True`，`main()` 因此 `return 0`，
`arc-recon/verify.sh` 只看退出码，于是闸门全绿。

报告里确实带了 `live_key_comparison: "unavailable (RuntimeError)"`，人读得到；
但 `clean` / `all_clean` / 退出码 / `assert_clean()` 四个机器读者全部读到绿。
**这和 S23 是同一句话：读不了不等于干净**，只是对象从「文件」换成了「密钥」。
S23 的修法可以直接照搬：`clean` 取 `None`，让退出码承载。

## 二、`verify-lab/negctl/tests/test_probe.py`（约 320-324 行）

遍历真实仓库时 `except (OSError, SyntaxError, UnicodeDecodeError): continue`。
它在**负控制领地自己的测试里**——负控制是专门用来证明检查会红的地方，那里
出现 fail-open 的形状，比它出现在别处更值得看一眼。可能是无害的（测试自身的
遍历，不产出裁决），需要一个人判一下，我没有越界去改。

## 三、`contamination.py` 的扫描面仍是手写的（已披露，未修）

`OTHER_LEDGERS` 是写死的两个文件，仓库里 ledger 形状的文件比这多（分片账本
就是）。我没有改成自发现——那是另一件活——但把它变成了一个**布尔量**：
`gate()` 现在返回 `scan_surface_self_discovered: False`，并在绿灯时把这句
caveat 打出来。它**不会**让闸门变红（长期红的闸门等于没有闸门），但从此是一个
下游检查可以 gate 的事实，而不是一句没人读的散文。

## 另外两件顺手的事，已经做了，报备

* **`release` 领地此前是 UNGATED**（`monitor/gates.py` 四个未设闸领地之一），
  持有密钥与封存两道红线的领地反而没有自己的闸门，`ci_merge` 一直在无检查合并
  它。已补 `release/verify.sh`，现在 `gates.py` 报 9 个 verify 领地。
* **`release/checklist.py` 从来没有解析成功过**：第 45 行字符串字面量里嵌了一个
  真换行，`SyntaxError`。也就是说 `release/CHECKLIST.md` 是某个更早的可用版本
  生成的，此后没人跑过它。已修（一个 `\n`）。engine-rig 的
  `test_tool_failure_is_not_truth.py:607` 早就把这个文件当成「读不开的文件」的
  例子写进 docstring 了——它举的例子一直是真的。

零 API、零封存堆接触。
