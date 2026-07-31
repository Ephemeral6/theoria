#!/bin/sh
# Cycle 33: reflex.py pid 9944 started 14:02:01Z; scan.py pid 33764 started 14:20:01Z.
# reflex.py:361 gives scan.py timeout=600, and nothing catches TimeoutExpired.
# PREDICTION filed before observing: if scan.py is still alive at 14:30:01Z,
# reflex.py (9944) dies within seconds of that mark and reflex.log gains no line.
# FALSIFIERS: scan exits before 14:30 (no test); scan outlives 14:30 AND reflex
# survives past 14:31 (diagnosis wrong); reflex dies but writes a log line
# (it was handled after all).
OUT=monitor/runs/opsm33/reflex-watch.log
for i in $(seq 1 90); do
  T=$(date -u +%H:%M:%SZ)
  R=$(tasklist /FI "PID eq 9944" 2>/dev/null | grep -c 9944)
  S=$(tasklist /FI "PID eq 33764" 2>/dev/null | grep -c 33764)
  L=$(tail -1 monitor/reflex.log | cut -c1-20)
  echo "$T reflex=$R scan=$S reflexlog_last=$L" >> $OUT
  [ "$R" = "0" ] && echo "$T REFLEX GONE" >> $OUT && break
  sleep 20
done
echo "watch done" >> $OUT
