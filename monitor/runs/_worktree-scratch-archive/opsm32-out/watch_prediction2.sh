#!/bin/sh
# OPS-M cycle 32 agent E: live check of H1.
# Predicted: ci_merge pid 2592 (started 12:28:49Z, parent reflex 6328) exits on its own
# well under its 3600s timeout; ~600s later reflex 6328 dies with NO new reflex.log line.
cd /c/Users/user/Desktop/theoria
OUT=.worktrees/opsm32-out/prediction2b.log
BEFORE=$(wc -l < monitor/reflex.log)
echo "start $(date -u +%H:%M:%SZ) reflex.log lines=$BEFORE last=$(tail -1 monitor/reflex.log | cut -c1-30)" >> $OUT
i=0
while [ $i -lt 100 ]; do
  T=$(date -u +%H:%M:%SZ)
  SNAP=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\user\Desktop\theoria\.worktrees\opsm32-out\snap.ps1' 2>/dev/null | tr -d '\r')
  LINES=$(wc -l < monitor/reflex.log)
  MLINES=$(wc -l < monitor/ci/merge.log)
  echo "$T procs=[$SNAP] reflexlog=$LINES mergelog=$MLINES" >> $OUT
  if [ "$LINES" != "$BEFORE" ]; then echo "  NEW REFLEX LINE: $(tail -1 monitor/reflex.log)" >> $OUT; BEFORE=$LINES; fi
  i=$((i+1))
  sleep 30
done
echo "done $(date -u +%H:%M:%SZ)" >> $OUT
