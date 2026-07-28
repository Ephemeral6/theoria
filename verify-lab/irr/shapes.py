"""Named pairs of rows that describe the same shape and got different cells.

With zero inter-judge overlap (`overlap.py`), the 253 published rows carry no
reliability coefficient. They do carry something weaker and still worth having:
pairs of rows whose *evidence cells describe the same situation* and whose
verdicts differ. Three of the four pairs below are inside a single batch, so they
are not even inter-judge disagreement -- they are one judge using the cell two
ways within one sitting.

This is not a statistic and must not be quoted as one: the pairing is a
judgement, mine, and a hostile reader should re-read the four cells and decide
whether the shapes really match. The script exists so that the quoted evidence is
pulled from the tables rather than transcribed by hand.

    python verify-lab/irr/shapes.py
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import rows as rowsmod  # noqa: E402

#: (shape, [(census, path-or-entry-substring), ...], what it costs)
PAIRS = [
    (
        "控制只读源码，从不执行被判文件",
        [("V15", "monitor/ci_merge.py"), ("V15", "monitor/reflex.py")],
        "同一批 b1。`ci_merge.py` 的测试是对源码字符串 grep，判 `否`；"
        "`reflex.py` 的测试是 AST 解析加断言、同样从不执行 `reflex.main()`，判 `部分`。",
    ),
    (
        "控制打的是同功能的第二份实现",
        [("V15", "cold-start-a2/a2pipeline/engines.py"),
         ("V15", "monitor/scan.py"),
         ("V15", "worldgen/generate.py")],
        "b5 在自己的附注里写下规则「打的是别处…按判据一律不算，故判 `否`」；"
        "b1 与 b9 对同一形状判 `部分`。规则被独立写下过，只是没被写进判据。",
    ),
    (
        "文件内有一条拒绝路径被演示过，其余若干条没有",
        [("V15", "theory-compiler/src/theory_compiler/parser/theory_parser.py"),
         ("V15", "theory-compiler/src/theory_compiler/strips_encoding.py")],
        "同一批 b3。`theory_parser.py` 明写「`SemanticsError` 的 7 处 raise 全树无任何断言」"
        "仍判 `是`；`strips_encoding.py` 明写「负控只有一处且只打到构造器」判 `部分`。",
    ),
    (
        "预注册变异体存在且可执行，但没有断言绑定它的结果",
        [("V15", "cold-start-a3/a3pipeline/run_l1.py"),
         ("V11", "run_arm.py --twice")],
        "V15 判 `部分`（「可执行的预注册变体，但没有任何断言绑定它的结果」）；"
        "V11 对同一形状也判 `部分`（「算半个演示」）。**这一对是一致的**，"
        "登在这里是因为一个只列不一致的清单会骗人。",
    ),
]


def find(census: str, needle: str) -> List[Dict[str, object]]:
    return [r for r in rowsmod.corpus()
            if r["census"] == census
            and (needle in str(r["entry"]) or needle in " ".join(str(p) for p in r["paths"]))]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.parse_args(argv)
    for shape, members, note in PAIRS:
        print("== %s" % shape)
        for census, needle in members:
            hits = find(census, needle)
            if not hits:
                print("   [%s] %s -- NOT FOUND" % (census, needle))
                continue
            for row in hits:
                print("   [%s %s] %-58s 有负控=%s"
                      % (census, row["judge"], needle, row["has_negctl"]))
        print(textwrap.fill(note, 78, initial_indent="   ", subsequent_indent="   "))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
