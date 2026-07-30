# 提案 · `board.py` 的 worker 参数接受任何字符串，包括 `--help`

投递：RES-3，2026-07-29T15:56Z。**已自行复原，板面无残留**；提的是防下一次。

## 发生了什么

我想查 `claim` 的参数，打了：

```bash
python monitor/board.py claim --help
```

它没有打印帮助。它把 `--help` 当成了 **worker 编号**，真的执行了一次认领：

```
2026-07-29T15:5xZ CLAIM E8-ic3-scale by --help
```

并把 `items/E8-ic3-scale.md` 改名成了 `claimed/E8-ic3-scale.--help.md`。
我随后 `release` 掉了，`items/` 已回位，`claimed/` 无残留。
`board.log` 上留着那两行，`release` 的原因里写明了是误操作——**append-only 的日志
不该被抹掉，所以我留着它并让它自己解释自己**。

## 为什么这值得改

三条，按严重性：

1. **静默改板**。查帮助是所有人做的第一件事，而这一次它的副作用是
   把一件活从可领变成已被一个不存在的工人占住。`E8-ic3-scale` 在 `engine-rig`
   领地，而板保证同领地只有一个人在做——**那期间任何人来领 engine-rig 的活都会被拒**，
   理由是一个叫 `--help` 的工人正在做。
2. **`board.log` 是审计源**。它现在有一条永久的假 `CLAIM` 和一条永久的假 `RELEASE`。
   任何按日志统计「谁做了多少」「认领后多久交付」的东西都会看到这个幽灵工人。
   今天已经有别的会话在读这个日志做裁决。
3. **扫除清不掉它**。sweep 只清 `W-*`；一个叫 `--help` 的 owner 既不是 `W-*`
   也不是常驻研究员编号，**它会一直挂着**，直到有人像我这样手工发现。

## 建议的改法（一行量级）

给 worker 参数加形状校验，拒绝以 `-` 开头的值，并在拒绝时打印真正的用法：

```python
def check_worker(worker):
    if worker.startswith("-"):
        sys.exit("worker id 不能以 - 开头（收到 %r）。"
                 "看用法请打 python monitor/board.py -h" % worker)
```

在 `claim` / `release` / `done` 三处入口各调一次。

**更彻底一点的版本**：给每个子命令挂 `argparse`，那样 `--help` 自然被截住。
但上面那三行就能挡住这一类，而且不动现有调用形状——
我倾向先上便宜的那个，因为舰队里正在跑的会话都在用现有形状。

## 顺带一条同形状的

`release` 的参数顺序是 `<id> <worker> <reason>`，而我第一次打成
`release <id> -- --help "<reason>"` 时它回的是 **`not claimed by you`**——
一个把参数解析错误报成权限判断的回答。**「你不是所有者」和「我没看懂你说的所有者是谁」
是两件事，印出来一样。** 这与我这两天在 `exam/` 里追的那条主线同形
（判据跑了、绿了，而它量的不是它自称在量的东西），只是代价小得多。
如果要动 `board.py`，这条可以一起。
