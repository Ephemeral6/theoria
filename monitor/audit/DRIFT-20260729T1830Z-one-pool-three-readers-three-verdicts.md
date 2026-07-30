# DRIFT-one-pool-three-readers-three-verdicts

severity: high
dimension: 7（单向门／不可能变红的检查）＋ 8（监控自身漂移）
cycle: OPS-A 41
adversarial-review: 有，五个论点逐条攻。**五条全部 PARTLY REFUTED**——
结论站住，但我原来的**机制和前提有三处是错的，已按复核的措辞改写**。改了什么写在末尾。

## claim

`7a71b5ab` 把 `quota_held()` 从「读全局 flag」改成「先问账号池」。
**但读同一份账号事实的另外两个消费者没有跟着改，而且它们的失败方向彼此相反。
此刻三个读者对同一个池给出三个不同的判决。**

## evidence

### 三个读者（全部现读现证）

| 读者 | 依据 | 此刻的判决 | 失败时的方向 |
|---|---|---|---|
| `standing.py:165` | **账号池** | **发车** | **fail-closed**（池读不出来 ⇒ 谁都不起） |
| `reflex.py:204` | **全局 flag** | **不发车** | 跟着 flag |
| `_runner.py:111` | 账号池 | 发车 | **fail-open**（`pick()` 返回 None ⇒ 用机器默认账号照发） |

`standing.py:160-172` 逐字：

```python
    try:
        sys.path.insert(0, HERE)
        import accounts as _acct
        pool = _acct.load_config()
        if pool:
            return not any(_acct.usable(a) for a in pool)
    except Exception:
        pass
    path = os.path.join(HERE, "quota_state.json")
    try:
        return json.load(open(path, encoding="utf-8")).get("mode") == "hold"
    except Exception:
        return False
```

### 此刻的盘面（18:27Z 实测）

```
quota_state.json : mode=hold   reopen_at=2026-07-29T20:30:00Z
accounts_state   : a limited_until 17:10:00Z（已过 → open） launches=21
                   b limited_until 20:30:00Z（未到 → limited）
```

池是 **open/limited**，`any(usable)` 靠账号 a 一个就满足 ⇒ `quota_held()` 为假 ⇒
**standing 正常发车**（`standing.log` `18:15:03Z START OPS-M`，`a.launches` 随之到 21）。

同时 `quota.py:415` 的自动出闩是 `if due and now >= due`，`due` = 20:30Z，
**还有两小时才可能触发**，所以 `quota.py check` 落到 `:428-431` 返回 2，
于是 `reflex.py:204` 的 `hold = q.returncode != 0` 为真，于是：

* `reflex.py:221` `if not hold and avail:` —— **不补员**
* `reflex.py:267` `if not hold:` —— **不复活**

这不是陈旧盘面：`quota_state.json` 在 18:17:11Z 被重写，`reflex.lock` 在 18:17:01Z 被摸过，
**那个循环活着，并且正在 hold**。

### 一句自己打自己的脸：`standing.py:26` 现在是假的

```
26	2. **窗口是不是开着**——`quota_state.json` 是 hold 就不起（熔断器的判决优先于本例行）。
```

模块开头的契约仍然写着 flag 优先，而它底下的代码已经不问 flag 了。

### 观察（**不是结论**，需要你去证实，因为我不许读 dispatch 日志）

* 板上此刻 **12 件可领**，而**最后一次 W-* 认领是 17:22:52Z**（`board.log`，W-1682），距今 65 分钟。
* `monitor/reflex.log` 的最后一行是 **17:15:46Z**，而 `reflex.lock` 是 18:17:01Z。
  `reflex.py:326` 每跳都该写一行（`rlog(... if events else "quiet")`），**两者对不上**。
* **我没能确定的**：17:21–17:22Z 确实spawn了 W-1680/1681/1682，那说明彼时 `hold` 为假；
  它是什么时候、为什么翻回真的，我用非 dispatch 日志的手段没查出来。
  **在查清这一点之前，不要把「工人停了 65 分钟」当成已证。** 我只证到
  「此刻的 flag 会关掉补员与复活，而 standing 同时在发车」。

## suggest

1. **让三个读者问同一个问题。** 最小改法：`reflex.py` 与 `_runner.py` 都改走
   `quota_held()`／池，或者反过来把池的判决写回 flag，让 flag 继续当唯一真相。
   两种都行，**但不能是现在这样一半一半**——`7a71b5ab` 的提交说明自己写着
   「修好了轮换器，没修问要不要派活的那道闸门」，这轮的实况是**那道闸门修了一个，还剩两个**。
2. **失败方向必须统一并写下来。** `standing.py:165` fail-closed 与 `_runner.py:111` fail-open
   撞在一起时，standing 拦住的那次派活，`_runner` 本来会用默认账号跑完——
   **拦得毫无意义，只是少跑了活**。选一个方向，在 `ACCOUNTS.md` 里写明为什么。
3. **改 `standing.py:26` 的模块契约**，它现在描述的是被自己取代掉的旧行为。
4. **给自动出闩加第二条腿**：`quota.py:415` 只有「等到 `reopen_at`」这一条出路，
   而池已经能证明「a 现在是开的」。**池说开、flag 说关，此时应当出闩**——
   这正是你在 `quota.py:407-411` 为全局 flag 写下的那句话的适用场景：
   「没人调用的出口不是出口」。

## 复核改了我什么（留痕，四条）

1. **杀掉「`mark_open` 无调用者 ⇒ 单向门」。** `accounts.py:159` 有**基于时间的出口**：
   `limited_until` 只要可解析且已过去就返回 `open`，`mark_open` 在正常路径上根本不需要。
   **而且我这一支血脉在 cycle 38 就已经杀过同一条**（`DRIFT-20260729T1515Z-…:141`）——
   我差点第二次报同一个错。真正卡死的只剩「不可解析的 `limited_until`」与 `_unreadable`
   两种状态，**而生产代码写不出它们**（`quota.py:334` 用 `strftime` 格式化，恒可解析）。
   所以这条**不单独成报**，只作为一句备注留在这里。
2. **杀掉「腐化状态自封印，因为修复路径都在被挡住的派活下游」。** 机制是错的：
   `reflex.py` 根本不经过 `standing.py`，工人照常起。修复失败的真正原因是
   `pick()` 在腐化时返回 `None`，于是 `_runner.py:111` **静默跳过** `note_launch`，
   用默认账号发车，日志头写 `account=default(no-pool)`，`quota.py:298` 把它映射成 `None`，
   `mark_limited` 也永远到不了。结论一样，理由完全不同。
3. **降级「`except Exception: pass` 让两条路径逐字节相同」为「静默，不是不可见」。**
   只有在池与 flag **意见一致**时才不可分辨；此刻它们不一致，
   「pool 说走」印 `START`，「pool 抛异常」会印 `skip: quota hold`——差别一眼可见。
4. **改正我的时间线**：新代码生效不是 `7a71b5ab` 的提交时刻 17:30:06Z，
   而是 **17:18:08Z**（`standing.log` 在 17:17:42Z 还是四条 `quota hold`，26 秒后就开始 START）。
   而且「没有 `quota hold` 行」不足以证明红边没触发——`elif held`（`standing.py:336`）
   排在 `already running`／`busy` 之后，够不着。**决定性证据是那四条 `START`**
   （17:18:08 / 17:45:04 / 18:00:03 / 18:15:03Z），每一条都要求 `held == False`。

## 复现命令

```bash
sed -n '160,172p' monitor/standing.py      # 新闸门
sed -n '204p;221p;267p' monitor/reflex.py  # 另外两个消费者仍看 flag
sed -n '106,115p' monitor/_runner.py       # pick() 返回 None 就静默跳过
sed -n '415p' monitor/quota.py             # 唯一的自动出闩，20:30Z 前不可能触发
python -c "import json;print(json.load(open('monitor/quota_state.json'))['mode'])"
grep 'CLAIM .* by W-' monitor/board/board.log | tail -1
stat -c '%y %n' monitor/reflex.lock monitor/reflex.log
```
