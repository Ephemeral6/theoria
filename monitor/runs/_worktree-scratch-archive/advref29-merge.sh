set -u
W=C:/Users/user/Desktop/theoria/.worktrees/advref29-m
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1
for b in a3-campaign-devpile c13-certificate-bridge-two-halves s38-append-only-probe-branch-blind s39-writes-into-the-live-master-tree s40-fleetkit-fork-has-drifted; do
  cd "$W"
  git merge --abort 2>/dev/null
  git reset --hard 7972a075 -q
  git clean -xdfq -e .venv 2>/dev/null
  echo "================ BRANCH $b"
  git merge --no-edit -q origin/agent/$b > /tmp/mrg-$b.txt 2>&1
  echo "MERGE_RC=$?"
  tail -5 /tmp/mrg-$b.txt
  git status --porcelain | grep -c "^UU\|^AA" || true
  bash monitor/verify.sh > /tmp/gate-$b.txt 2>&1
  echo "GATE_RC=$?"
  grep -E "^FAILED |^RED: |^GREEN|^== " /tmp/gate-$b.txt | sort | uniq -c | sed 's/^/    /'
done
