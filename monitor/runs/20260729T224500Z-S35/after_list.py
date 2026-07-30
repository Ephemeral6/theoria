"""What the fixed `list` says about the **live** board, without touching it.

`probe_unreachable.py` measures; this one shows. It copies the live board's
three directories and `ops-status/` into a throwaway tree, points the *fixed*
`board` module at the copy, and prints `cmd_list()`. Read-only on the real
board by construction: nothing here writes outside the temp directory.

The copy is necessary in both directions. Pointing the fixed module at the live
board would let a stray verb mutate it; running the live `monitor/board.py`
would import the unfixed code, since `board.py` resolves its paths from its own
location.

    python monitor/runs/20260729T224500Z-S35/after_list.py [/path/to/live/monitor]
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BRANCH_MONITOR = os.path.abspath(os.path.join(HERE, "..", ".."))
LIVE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else BRANCH_MONITOR)

sys.path.insert(0, BRANCH_MONITOR)
import board                                                    # noqa: E402


def main():
    tmp = tempfile.mkdtemp(prefix="s35-after-")
    try:
        for sub in ("board/items", "board/claimed", "board/done", "ops-status"):
            src = os.path.join(LIVE, *sub.split("/"))
            dst = os.path.join(tmp, *sub.split("/"))
            os.makedirs(dst, exist_ok=True)
            for f in sorted(os.listdir(src)) if os.path.isdir(src) else []:
                if os.path.isfile(os.path.join(src, f)):
                    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        board.HERE = tmp
        board.BOARD = os.path.join(tmp, "board")
        board.ITEMS = os.path.join(tmp, "board", "items")
        board.CLAIMED = os.path.join(tmp, "board", "claimed")
        board.DONE = os.path.join(tmp, "board", "done")
        board.LOG = os.path.join(tmp, "board", "board.log")
        board.OPS_STATUS = os.path.join(tmp, "ops-status")
        board.prior_work = lambda iid, repo=None: []
        print("# live board copied from %s" % LIVE)
        # S35a（对抗复核抓到）：原来是 `% ", ".join(...) or "(empty)"`。
        # `%` 比 `or` 结合得紧，所以 `"(empty)"` 是**到不了的代码**，空集会印
        # 出一个后面什么也没有的标签。这是本条目交付的那个「看」的脚本。
        ids = sorted(board.unreachable_ids())
        print("# unreachable set: %s" % (", ".join(ids) if ids else "(empty)"))
        print()
        board.cmd_list()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
