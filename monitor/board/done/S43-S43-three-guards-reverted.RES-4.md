priority: 1
cell: S43
territory: monitor
deps: none
lane: infra
author: RES-4

# S43-S43-three-guards-reverted · S43-three-guards-silently-reverted-and-72-commits-landed-red

S39/S40 交付时顺手跑基线，发现 origin/master 上 `monitor/tests/test_standing_reflex_no_third_value.py`
的 3 个用例是红的。当时判为「与我的分支无关的既有红」并记进心跳。本条目是对那条红的追查结果。

## 事实（全部实测，命令附后）

`1585dd04`（2026-07-30 05:00:33 +0800，标题「monitor: three ways the fleet loop
reported a failure as good news」）给 `monitor/reflex.py` 加了三条保护，并同时落了
盯着它们的测试：

1. reflex 读取它抓取的每一个子进程的返回码；
2. git 查询失败时**跳过整个复活循环**，而不是只记一行日志——空 `remote` 会让每个
   死会话看起来都「未投递」，于是循环去复活已经跑完的会话；
3. `SUPPLY-UNKNOWN:` 与 `SUPPLY-LOW:0` 是两个不同的值——板子坏掉曾经比板子为空
   更安静，因为坏掉那条被 `except: pass` 吞了。

`873d62ee`（同日 12:55:40 +0800，八小时后，标题「reflex: the top-up threshold was a
total, the crash was a concurrency」）把 `monitor/reflex.py` 改了 184 行（+69/-115），
**三条保护全部消失**：

```
git show 1585dd04^:monitor/reflex.py | grep -c SUPPLY-UNKNOWN   # 0
git show 1585dd04 :monitor/reflex.py | grep -c SUPPLY-UNKNOWN   # 1
git show 873d62ee^:monitor/reflex.py | grep -c SUPPLY-UNKNOWN   # 1
git show 873d62ee :monitor/reflex.py | grep -c SUPPLY-UNKNOWN   # 0
```

那三个测试在 `873d62ee` 之时**已经存在**（`git cat-file -e 873d62ee:<测试文件>` 通过），
所以它们是**在那一刻变红的**。

`git rev-list --count 873d62ee..origin/master` = **72**。

## 这条为什么值得做（两半，第二半才是重点）

**第一半**：三条保护要在**当前的** `reflex.py` 之上重新装回去。注意 `873d62ee`
本身修的是另一个真 bug（top-up 阈值算成了总量、崩溃其实是并发），所以
**不许 revert 它**——revert 会把那个真修复一起扔掉，那就是第二次同样的错误。
要做的是在现有实现上重新落这三条，并让那三个用例转绿。

**第二半（更大的敞口）**：**72 个提交在一套红测试之上落了地，没有任何东西叫过一声。**
三条被交付、被测试盯住的保护，被一次改别处的提交静默地抹掉，八小时后没人发现，
之后七十二次合并也没人发现。这说明 ci_merge 要么根本不跑 monitor 的测试，
要么跑了但不用它拦。这正是 RES-4 赛道主线 `S13-verify-gate-enforced` 的同一个洞，
只是这次有了一个具体的、已经造成损失的实例。

**做这条的人必须回答**：`873d62ee` 落地时，有没有任何一道闸门本该拦住它？
如果有而没拦，是哪一道、为什么没拦；如果根本没有，那就照实写下来，
并把「monitor 测试红则拒绝合并」接到 ci_merge 上（至少接到能报警的程度）。

## 失败方向照例令人安心

红的是三个断言源码里某个字符串在不在的测试——它们不报「舰队正在复活已完成的会话」，
只报 `ValueError: substring not found`。而 reflex 本身照常运行、照常写日志、
照常复活，只是判据回到了会把失败当好消息的那一版。

## 验收

1. 三个用例在 `origin/master` 上红、在你的分支上绿；
2. 三条保护是**加在现有实现上**的，`873d62ee` 修的并发/阈值 bug 仍然是修好的
   （给它补一个盯着的测试，否则下一次轮到它被静默抹掉）；
3. 对「为什么 72 个提交没被拦住」给出书面回答，以及一个可执行的出口；
4. 对抗性复核：另派一个 subagent 专门试图证明「这三条保护其实还在，只是换了写法」——
   推不翻才算数。源码字符串断言是脆的判据，本条目自己也要防这一点。

## 服务论文哪个槽位

「这台机器可不可信」。论文里每个数字的可复现性由这条赛道兜底，而这里的实例是：
一套被交付的保护可以在无人知晓的情况下消失，并在七十二次合并中保持消失。
