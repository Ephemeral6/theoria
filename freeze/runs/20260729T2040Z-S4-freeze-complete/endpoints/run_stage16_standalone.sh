#!/usr/bin/env bash
# Test harness for verify_sh_stage16.snippet.sh -- defines exactly what
# verify.sh defines around a stage, and nothing else, so the snippet can be
# exercised without touching verify.sh.
#
#   bash freeze/runs/20260729T2040Z-S4-freeze-complete/endpoints/run_stage16_standalone.sh
#
# Exit 0 always; read the PASS/FAIL/NOTE lines.
set -u
HERE_SNIP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERE="$(cd "$HERE_SNIP/../../.." && pwd)"     # -> freeze/
FAIL=0; WARN=0
red()  { printf '\033[31m%s\033[0m\n' "$*"; }
grn()  { printf '\033[32m%s\033[0m\n' "$*"; }
ylw()  { printf '\033[33m%s\033[0m\n' "$*"; }
ok()   { grn "  PASS  $*"; }
bad()  { red "  FAIL  $*"; FAIL=$((FAIL+1)); }
note() { ylw "  NOTE  $*"; WARN=$((WARN+1)); }
S="$HERE/STATS_RULES.md"
C="$HERE/CLAIMS_TEXT.md"
. "$HERE_SNIP/verify_sh_stage16.snippet.sh"
echo "standalone summary: FAIL=$FAIL NOTE=$WARN"
