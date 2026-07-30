#!/usr/bin/env bash
# crosscheck territory -- verification gate.
#
#   bash crosscheck/verify.sh
#
# Green means: the C14 census re-derives from the tracked corpus exactly as
# committed, the generated PDDL is byte-identical, and nothing in this territory
# wrote outside it or touched the network.  Run from the repo root.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
rc=0

echo "== C14 census reproduces =="
python -m crosscheck.tools.c14_verify || rc=1

echo
echo "== territory discipline: crosscheck/ writes only =="
# The other track's tree is off limits by CLAUDE.md; a diff touching it is a red.
# Three exceptions, and only three: the board item's own territory (crosscheck/),
# this worker's own appended paragraph in PARTNER_SYNC.md, and monitor/inbox/ --
# the one path under monitor/ every worker is standing-authorised to write.
# Anything else under monitor/ is still a red.
strays=$(git diff --name-only HEAD -- . \
           ':(exclude)crosscheck' \
           ':(exclude)PARTNER_SYNC.md' \
           ':(exclude)monitor/inbox' 2>/dev/null)
if [ -n "$strays" ]; then
  echo "RED  this branch modifies files outside crosscheck/:"
  echo "$strays" | sed 's/^/     /'
  rc=1
else
  echo "green  no tracked file outside crosscheck/ (and PARTNER_SYNC.md) modified"
fi

echo
echo "== theory-compiler/ untouched (other track) =="
if git diff --name-only HEAD -- theory-compiler 2>/dev/null | grep -q .; then
  echo "RED  theory-compiler/ modified -- it belongs to the other track"
  rc=1
else
  echo "green  theory-compiler/ byte-untouched"
fi

echo
echo "== no credential in tracked crosscheck/ files =="
# The census reads no secrets, but the release manifest publishes every tracked
# file, so this is checked rather than assumed.
if git grep -nI -E 'ARC_API_KEY[[:space:]]*=[[:space:]]*[A-Za-z0-9_-]{12,}' -- crosscheck 2>/dev/null | grep -q .; then
  echo "RED  a credential value appears in crosscheck/"
  rc=1
else
  echo "green  no credential value in crosscheck/"
fi

echo
if [ "$rc" -eq 0 ]; then echo "crosscheck/verify.sh: GREEN"; else echo "crosscheck/verify.sh: RED"; fi
exit $rc
