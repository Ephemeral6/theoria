# 提案 · `cold-start-a0/certify/replay.py` 的 relpath 破坏字节确定性

- 提出者：RES-1
- UTC：2026-07-28T21:20:00Z
- 发现于：bus #2（ablation-arm 只读闸门修复，分支 `agent/bus2-ablation-readonly`）
- 归属赛道：theory-compiler（**不是我的领地，所以只提案不动手**）

## 事实

`cold-start-a0/certify/replay.py:103` 记录

```python
"theory": os.path.relpath(theory_py)
```

`relpath` 没有 `start=`，所以这个字段是相对**调用进程的 cwd**，而不是相对任何固定的根。

后果是同一份产物按「谁重生成的」写出不同的字节：

| 重生成方式 | cwd | 记进 `run_report.json` 的值 |
|---|---|---|
| `bash verify.sh` | 仓库根 | `ablation-arm\artifacts\...` |
| `python run_arm.py`（臂内） | `ablation-arm/` | `artifacts\...` |

我在修 bus #2 时重生成了消融臂的产物，好几个 `run_report.json` 因此出现一行 diff —— 内容没变，只有这个字段跟着 cwd 翻脸。

## 为什么值得管

CLAUDE.md 把确定性写成硬要求而非好习惯：「fixtures and artifacts are
byte-reproducible for a fixed seed」。这条洞让「重生成后字节相同」变成一句
**取决于你从哪个目录敲命令**的话。它不会让任何测试变红——正因如此才该记下来：
它只会在有人比对两次重生成的产物时冒出来，而那正是确定性断言唯一被使用的场合。

顺带，它也污染 diff 噪音：每次换个位置重生成，一批产物就诈一次尸。

## 建议

改成显式的根，与仓库里别处的写法一致：

```python
"theory": os.path.relpath(theory_py, start=REPO).replace(os.sep, "/")
```

（`replace(os.sep, "/")` 一并加上：Windows 写 `\`、POSIX 写 `/`，同样是跨机器的字节
差异。`ablation-arm/ablcore/pin.py:59` 已经是这个写法，可以照抄。）

改完需要重生成一次受影响的产物，并确认两种 cwd 下重生成的字节一致——
这条是修复的验收条件，不是可选项。

## 我没做什么

没有改那个文件，也没有改任何 `cold-start-a0/` 下的东西：CLAUDE.md
写明 `/cold-start-a0/` 是 theory-compiler 赛道的，engine-rig 不得进入。
请监控转给该赛道，或下发成一件工作板条目。
