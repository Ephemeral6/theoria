#!/bin/bash
# OPS-M cycle 32: watch the prediction in pass-growth.txt.
# Predicted: ci_merge pid 2592 (started 12:28:49Z) is KILLED at 13:28:49Z +-30s
# with ~13-14 of 17 branches logged and no new monitor/reflex.log line.
cd "$(dirname "$0")/../../.." || exit 1
OUT=monitor/runs/opsm32/pass-watch.log
echo "start $(date -u +%H:%M:%SZ) merge.log=$(wc -l < monitor/ci/merge.log) reflex.log=$(wc -l < monitor/reflex.log)" >> "$OUT"
END=$(( $(date +%s) + 3900 ))
while [ "$(date +%s)" -lt "$END" ]; do
  cm=$(tasklist //FI "PID eq 2592" 2>/dev/null | grep -c 2592)
  rx=$(tasklist //FI "PID eq 6328" 2>/dev/null | grep -c 6328)
  nb=$(awk '$0 >= "2026-07-30T12:34:00Z"' monitor/ci/merge.log | grep -c "FLAG\|MERGED")
  printf "%s ci_merge2592=%s reflex6328=%s branches_this_pass=%s reflexlog=%s last=%s\n" \
    "$(date -u +%H:%M:%SZ)" "$cm" "$rx" "$nb" "$(wc -l < monitor/reflex.log)" \
    "$(tail -1 monitor/ci/merge.log | cut -c1-20)" >> "$OUT"
  sleep 60
done
echo "end $(date -u +%H:%M:%SZ)" >> "$OUT"
