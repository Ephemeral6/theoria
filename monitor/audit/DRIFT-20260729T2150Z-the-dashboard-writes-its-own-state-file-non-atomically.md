# DRIFT-the-dashboard-writes-its-own-state-file-non-atomically
severity: high
dimension: 7（单向门／不可能变红的检查）+ 5（流程漂移）
cycle: 43 (OPS-A)

## claim

`monitor/scan.py` 里有两个写 `state.json` 的地方。**失败页那个是原子的，每 10 分钟跑一次的成功路径不是。**
本周期我的取证 subagent 在工作树里抓到了这件事的后果：`monitor/state.json` 当时**解析不了**
——一个 UTF-8 三字节字符被切在第二字节上，后面接着合法 JSON。等我去复核时文件已经被下一次
扫描重写好了，所以**瞬时证据我复核不到；结构证据仍在，而且是决定性的**。

## evidence

**结构（主线 `origin/master`，可复核）**

* `monitor/scan.py:2645-2647` —— 成功路径，普通截断写：
  ```python
  with open(os.path.join(out_dir or HERE, "state.json"), "w",
            encoding="utf-8", newline="\n") as fh:
      json.dump(slim, fh, ensure_ascii=False, indent=2, sort_keys=True)
  ```
* `monitor/scan.py:2947-2948` —— 失败页路径，**同一个文件名**，走原子写：
  `_try("state.json", lambda: _write_atomic(os.path.join(target, "state.json"), ...))`
* `monitor/scan.py:2757-2762` —— `_write_atomic` 的 docstring 自己把理由写全了：
  「`tmp + os.replace`, the idiom `accounts.py:98` argues for. **A failure writer that can leave
  a half-written file behind would replace one invisible failure with a louder one.**」

**这条 docstring 是本报告的核心。** 写它的人完全知道半截文件的危害，为此专门造了 `_write_atomic`，
然后**只把它接在失败路径上**。每 10 分钟重算一次的那条热路径（`monitor/spec.py` 侧的
`TheoriaDashboard` 描述见 `scan.py:631`「每 10 分钟重算 state.json」）用的是普通写。
频率最高、被所有人读的那一份，恰好是没有保护的那一份。

**瞬时（工作树，21:0xZ 由 subagent 观测，我 21:45Z 复核时已自愈）**

* 当时：182,940 → 观测时 183,134 字节；`json.load(open(..., encoding='utf-8'))` 抛
  `UnicodeDecodeError … position 134371-134372: invalid continuation byte`；
  offset 134360 处的字节是 `b'\x9b\x86\xef\xbc\x89\xe3\x80\x82\xe6\x9e\x84\xe9\x80"note": "proxy/variants.py '`
  —— 一个三字节字符被切在两字节后，然后合法 JSON 接上。
* 我 21:45Z 实测：182,940 字节，**PARSES OK**；同 offset 现在是 `"_probed": false,\n "_status"`。
  主线那一份一直都能解析。

## 为什么它是「不可能变红」而不只是一次运气不好

1. **它自愈，所以没有任何人会看见它。** 下一次扫描把文件重写正确，窗口就关了。
   仪表盘上不会留下一格红，日志里不会留下一行——**除非恰好有读者落在那个窗口里**。
2. **落在窗口里的读者会静默降级，不会报警。** `scan.py:2738-2742` 自己写着
   「a state.json we cannot read is not the ... `None` and is rendered as 「未知」」，
   `:2856` 有对应的页面文案「（读不到上一份 state.json，…）」。也就是说
   **读不到被设计成显示「未知」，而不是报错**——这是对的产品选择，但它同时保证了
   一次损坏在盘面上的signature是「有一格变灰」，没人会去查为什么。
3. `monitor/verify.py` 本轮新加了 `REQUIRED_STATE_FIELDS` 与 `scan_ok is not True` 的绊线
   （见本周期另一份报告的 clean 部分），那是**内容**检查；它跑在能解析的前提上，
   解析失败时它拿到的是异常，不是红。

## 我不主张的部分（明确写出来）

* **我没有证到并发双写。** 两个写者一个在成功路径、一个在失败路径，同一次运行里
   走哪条是互斥的；要产生撕裂需要**两次运行重叠**。判断这一点要看 `monitor/refresh.log`
   的时间戳，而我的 subagent 判不准它算不算 dispatch 日志、于是停在字节证据上——这个停法是对的。
* **备选成因我排不掉**：一次 `git merge`／`reset`／autostash 碰到这个未被跟踪于主线最新态的文件，
   或者一次被杀的扫描（本周期确有配额熔断收割会话的记录）。**任一成因都指向同一个修法**，
   所以这条不影响建议：非原子写在一台会被熔断随时杀进程的机器上，本身就是缺陷。
   被杀恰恰是最可能的成因——`quota_state.history` 记着 `killed` 名单，而扫描没有崩溃保护。

## suggest（监控裁决，我一行代码都没动）

1. **`:2645` 改用同文件里已有的 `_write_atomic`。** 一行，零新概念，写它的人已经论证过为什么。
2. **给「state.json 能不能解析」一条能变红的探针。** 现在解析失败被渲染成「未知」，
   与「这一项确实无从得知」编码成同一个字面量——这正是 `S28-no-third-value-in-the-monitor`
   那件在飞条目的判据（「测不到」和「测了，没问题」同一个值）。**建议把这一条并进 S28**，
   它属于同一族，且 S28 已被 RES-4 认领。
3. 顺带：`accounts.py:98` 既然是这条 idiom 的出处，值得查一遍 monitor/ 里还有几处
   高频写盘没用上它。我没做这个普查（上下文预算），列为欠账。

## 复核命令

```bash
git show origin/master:monitor/scan.py | sed -n '2645,2647p;2757,2762p;2947,2948p'
python -c "b=open('monitor/state.json','rb').read(); print(len(b)); import json; json.loads(b.decode('utf-8')); print('parses')"
```

（第二条命令**现在会通过**。这正是本报告要说的事：它在 21:0x 那一刻不通过，
而没有任何机制记下那件事发生过。）
