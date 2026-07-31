#!/bin/sh
# OPS-M cycle 31: record agent 5's falsifiable prediction as it fires.
# Predicted: ci_merge pid 2220 killed at 12:19:10Z; reflex pid 42104 exits with NO new
# reflex.log line; fresh reflex ~12:22:0x.
OUT=.worktrees/opsm31-out/prediction-check.log
BEFORE=$(wc -l < monitor/reflex.log)
echo "start $(date -u +%H:%M:%SZ) reflex.log lines=$BEFORE last=$(tail -1 monitor/reflex.log | cut -c1-20)" >> $OUT
i=0
while [ $i -lt 70 ]; do
  T=$(date -u +%H:%M:%SZ)
  P2220=$(powershell.exe -NoProfile -Command "if (Get-Process -Id 2220 -ErrorAction SilentlyContinue) {'alive'} else {'GONE'}" 2>/dev/null | tr -d '\r')
  P42104=$(powershell.exe -NoProfile -Command "if (Get-Process -Id 42104 -ErrorAction SilentlyContinue) {'alive'} else {'GONE'}" 2>/dev/null | tr -d '\r')
  NEW=$(powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {\$_.CommandLine -like '*reflex.py*'} | ForEach-Object {\$_.ProcessId}) -join ','" 2>/dev/null | tr -d '\r')
  LINES=$(wc -l < monitor/reflex.log)
  echo "$T ci_merge2220=$P2220 reflex42104=$P42104 reflex_pids=[$NEW] reflexlog_lines=$LINES" >> $OUT
  if [ "$LINES" != "$BEFORE" ]; then echo "  NEW REFLEX LINE: $(tail -1 monitor/reflex.log)" >> $OUT; BEFORE=$LINES; fi
  i=$((i+1))
  sleep 30
done
echo "done $(date -u +%H:%M:%SZ)" >> $OUT
