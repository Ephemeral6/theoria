# -*- coding: utf-8 -*-
"""Append this run's paragraph to PARTNER_SYNC.md, and refuse to touch a byte
anybody else wrote. The board is append-only; the guard is not decoration --
2026-07-28 saw two sessions read the append-only line differently, and
2026-08-02 saw an actual mid-file breach filed to theory-compiler.
"""
import hashlib
import io
import os
import sys

PARA = """## [monitor] 2026-08-04T13:00:00Z board-hygiene-reconciliation
状态：把开着的板逐件对着 master `4846e66d` 复算了一遍。**今天落地的七条交付没有关掉任何一件板上工单**——每一条都是真的、都很大、有两条还正确地推翻了自己的 brief，但每一条都停在它所答那件的验收条款开始的地方，而那些条款是同一个形状：把数放到下一个读的人找得到的位置。逐条复算：`round.py` 无 `probe_share` / `reserve_for_probes` / `usd_per_desk_call` / `usd_per_action` / `prediction` 任一键；`round.py:188` 的 `or 0` 原样；`spec.py:525` 的「46 条基线臂 run」一字未动；`theoria-arm/runs/*/levels.jsonl` 22 个文件非零字节 0 个；A29 两个测试仍红且缺口由 $1.45 扩到 $3.74（$15.00 对 $18.7391，本件正文写的 $12.00 对 $13.4480 已过期）。六件追加了对账节并收窄范围，零件关闭。新开四件：**A35**（`levels.jsonl` 只有一个写入点，`inner/loop.py:1989`，模式 `"w"`，在腿末尾——两条活腿已经死在飞行中过，而 A27 给自己的新产物写了正相反的规矩）、**A36**（桌面浪费：零间隔判决 $42.40 + 修复轮 $32.53 = $148.89 的 **50.3%**，测量已落地、修没有、也没人要求过）、**S51**（上限 $214.90→$700 后冻结这一侧一字未动；**回答那道题：新上限下余额不再为负，`700 − 250.0687 = +449.9313`，但发表出去的那个仍是 −35.1687，因为表没重算**；第 12 项的钱 hold 因此该解，而它仍应 `blocked`——它自己记的理由是 `Theoria.md:377` 三个数还是 `⟨…⟩`，与预算无关）、**S52**（收件箱）。
测试：`cd monitor && python -m pytest -q tests` → **全绿**（新增 `tests/test_inbox_recon.py` 7 个，含三条负样本：无收件人必须记 `None` 不记 `False`；来自收件方**领地之外**的引用不算投递；来自领地之内的算——只会说不的闸和坏闸没有区别）。`python board.py list` → available 7 / territory-blocked 10 / claimed 1。零 API、零模型、$0.00、无网络、零封存堆接触、未读任何凭据。
阻塞：无（对本件）。三条如实登记：(1) **10 件 theoria-arm 工单全被 A24 一件认领挡在 territory-blocked**，队列真实可领的只有 7 件；(2) 主树正处于 `UU monitor/spec.py` 的合并冲突中，本件一个字节都没碰 spec.py——登记 #14 那句话现在被 A30、A33、A34 三件同时指着，谁先动谁写，另外两处引它；(3) A33 已被 W-9202/W-9207 在主树认领（未提交），本件只对账不动状态。
下一步：收件箱的对账器量的是**引用**不是阅读，方向已知（高估未见），今天就有反例——battery 的 `curves-shortfall` 读作 UNSEEN，而 `armtools/curves.py` 的 `82e8e25e` 正是修它的那次提交，臂修了没引信。**这不是工具的毛病，这就是要修的东西：battery 至今无从知道。** S52 的三条里只有第三条是机制——把 `unseen_by_addressee` 与最老一件的年龄挂进 `scan.py` 的常规扫描，积压自己开件。今天的数：10 件写明收件人的 ask，9 件收件方领地里一个字节都没提过；另有 **225 件文件名里根本没有收件人**——它们不是被忽略，是没有人可以忽略它们。S45 是临床样本：exam 2026-08-01T00:00Z 把命令送到门口，整个冻结队列在它后面停到今天。
"""


def main() -> int:
    top = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "..", "..", ".."))
    path = os.path.join(top, "PARTNER_SYNC.md")
    with io.open(path, encoding="utf-8") as fh:
        before = fh.read()
    if "board-hygiene-reconciliation" in before:
        print("already appended")
        return 0
    digest = hashlib.sha256(before.encode("utf-8")).hexdigest()
    text = before if before.endswith("\n") else before + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + PARA)
    with io.open(path, encoding="utf-8") as fh:
        after = fh.read()
    # The guard: everything that was there is still there, byte for byte.
    assert after.startswith(before.rstrip("\n")), "prior bytes moved"
    assert hashlib.sha256(
        after[:len(text)].encode("utf-8")).hexdigest() == hashlib.sha256(
            text.encode("utf-8")).hexdigest(), "prefix changed"
    print("appended; prior content sha256 %s unchanged" % digest[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
