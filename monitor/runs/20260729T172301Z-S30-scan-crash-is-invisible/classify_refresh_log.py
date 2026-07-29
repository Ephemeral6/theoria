"""Reproduce every number in `monitor/CRASHES.md` from `monitor/refresh.log`.

    python monitor/runs/20260729T172301Z-S30-scan-crash-is-invisible/classify_refresh_log.py

`refresh.log` is gitignored and will not survive the next cleanup, which is the
whole reason CRASHES.md exists. This script is the bridge: while the log is
still on disk, anyone can re-derive the classification instead of taking the
write-up's word for it. When the log is gone the script says so and exits 2
rather than printing zeros -- a missing input is not a clean result.

The log is mixed-encoding: scan.py's own stdout is cp936, the tracebacks are
ASCII. Decoding UTF-8 with `errors="replace"` keeps the ASCII exact and turns
the Chinese into U+FFFD, which is fine because every judgement below is made on
ASCII markers.
"""

import bisect
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
#: Defaults to the `monitor/` this script sits under. `refresh.log` is
#: gitignored, so inside a worktree there is none -- pass the main checkout's
#: path as argv[1] instead of concluding the log never existed.
LOG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..",
                                                         "refresh.log")

TB = "Traceback (most recent call last)"
WRITTEN = "index.html written"


def main():
    if not os.path.exists(LOG):
        print("refresh.log is gone -- the classification in monitor/CRASHES.md "
              "can no longer be re-derived from it. That was the predicted end "
              "state, not a failure of this script.")
        return 2

    raw = open(LOG, "rb").read()
    lines = raw.decode("utf-8", errors="replace").splitlines()

    tb = [i for i, l in enumerate(lines) if l.startswith(TB)]
    wr = [i for i, l in enumerate(lines) if WRITTEN in l]
    exc = [l for l in lines
           if re.match(r"^[A-Za-z_][A-Za-z_.]*(Error|Exception):", l)]

    print("bytes                        %d" % len(raw))
    print("lines                        %d" % len(lines))
    print("tracebacks                   %d" % len(tb))
    print("successful runs logged       %d" % len(wr))
    print("exception types              %s"
          % Counter(l.split(":")[0] for l in exc).most_common())
    print("frames in subprocess reader  %d"
          % sum(1 for l in lines if "_readerthread" in l))
    print("frames mentioning scan.py    %d"
          % sum(1 for l in lines if "scan.py" in l and l.strip().startswith("File")))

    followed = sum(1 for i in tb if bisect.bisect_right(wr, i) < len(wr))
    gaps = [wr[bisect.bisect_right(wr, i)] - i
            for i in tb if bisect.bisect_right(wr, i) < len(wr)]
    print("tracebacks followed by a written line   %d / %d"
          % (followed, len(tb)))
    print("  lines from traceback to that line     median %d, max %d"
          % (sorted(gaps)[len(gaps) // 2], max(gaps)))

    # The probe rows are printed after the run line, so the first conflict_scan
    # row at a higher index than a traceback belongs to that traceback's cycle.
    cs = [i for i, l in enumerate(lines) if re.search(r"conflict_scan\s+\w+", l)]
    verdict = lambda i: re.search(r"conflict_scan\s+(\w+)", lines[i]).group(1)
    crashed = set()
    for i in tb:
        j = bisect.bisect_right(cs, i)
        if j < len(cs):
            crashed.add(cs[j])
    print("conflict_scan, cycles WITH a traceback  %s"
          % Counter(verdict(i) for i in sorted(crashed)).most_common())
    print("conflict_scan, cycles WITHOUT           %s"
          % Counter(verdict(i) for i in cs if i not in crashed).most_common())

    bad = Counter()
    for l in lines:
        m = re.search(r"can't decode byte (0x[0-9a-f]+) in position (\d+)", l)
        if m:
            bad[m.group(1)] += 1
    print("offending bytes              %s" % sorted(bad.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
