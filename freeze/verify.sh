#!/usr/bin/env bash
# freeze/verify.sh -- P-22 stop-hook.
#
# The single condition this script enforces:
#
#     Theoria.md:368's 13-item freeze list has, for every item, either a
#     landing spot on the tree or an explicit annotation saying what is
#     missing.  Not one of the 13 may be silently absent.
#
# It also checks the three companion drafts are structurally complete
# (5 pending items each classified; C1-C5 each carrying BOTH outcomes;
# the three primary endpoints and the <n> ruling each present), and
# re-runs the <n> arithmetic so the number in STATS_RULES.md cannot rot.
#
# This verifies the DRAFT is complete.  It does NOT verify the freeze is
# ready -- items marked MISSING are honestly recorded failures, and the
# script reports them loudly while still passing, because "drafted" and
# "ready to freeze" are different states.  Readiness is the human's call.
#
# Usage:  bash freeze/verify.sh          (from the repo root or anywhere)
# Exit:   0 = draft complete   1 = draft incomplete

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAIL=0
WARN=0

red()  { printf '\033[31m%s\033[0m\n' "$*"; }
grn()  { printf '\033[32m%s\033[0m\n' "$*"; }
ylw()  { printf '\033[33m%s\033[0m\n' "$*"; }

ok()   { grn "  PASS  $*"; }
bad()  { red "  FAIL  $*"; FAIL=$((FAIL+1)); }
note() { ylw "  NOTE  $*"; WARN=$((WARN+1)); }

echo "=============================================================="
echo " freeze/verify.sh -- P-22 freeze-kit completeness check"
echo "=============================================================="
echo

# ---------------------------------------------------------------- 0. files
echo "[0] the four drafts exist"
for f in MANIFEST_DRAFT.md STATS_RULES.md CLAIMS_TEXT.md PENDING_FIVE.md; do
  if [ -s "$HERE/$f" ]; then ok "$f"; else bad "$f missing or empty"; fi
done
echo

M="$HERE/MANIFEST_DRAFT.md"
S="$HERE/STATS_RULES.md"
C="$HERE/CLAIMS_TEXT.md"
P="$HERE/PENDING_FIVE.md"

# ------------------------------------------------- 1. the 13 items, by name
# The names are quoted verbatim from Theoria.md:368, in its order.
echo "[1] Theoria.md:368 -- all 13 items have a section in MANIFEST_DRAFT.md"
ITEMS=(
  "内环代码"
  "DSL 语法版本"
  "生成器"
  "提示词"
  "引擎清单与版本"
  "戳探策略"
  "规划器配置"
  "指标电池 v1"
  "变体算子库"
  "统计裁决规则"
  "claim 逐字文本与双结局"
  "预算表"
  "每格重复数"
)
if [ ${#ITEMS[@]} -ne 13 ]; then
  bad "the checklist itself does not have 13 entries (${#ITEMS[@]})"
fi

n=0
for item in "${ITEMS[@]}"; do
  n=$((n+1))
  # a numbered "## <n>. ..." heading must exist AND mention the item name
  hdr="$(grep -n "^## ${n}\. " "$M" 2>/dev/null | head -1)"
  if [ -z "$hdr" ]; then
    bad "item ${n} (${item}): no '## ${n}.' section in MANIFEST_DRAFT.md"
    continue
  fi
  if ! printf '%s' "$hdr" | grep -q "$item"; then
    bad "item ${n}: section heading does not name '${item}' -> $hdr"
    continue
  fi
  # every item must carry a status marker: landed, caveated, or missing
  if printf '%s' "$hdr" | grep -qE '✅|⚠|⛔'; then
    ok "item ${n} ${item}"
  else
    bad "item ${n} (${item}): section has no status marker (✅/⚠/⛔)"
  fi
done
echo

# ------------------------------------------ 2. the overview table has 13 rows
echo "[2] MANIFEST_DRAFT.md overview table has exactly 13 numbered rows"
rows="$(grep -cE '^\| [0-9]+ \| ' "$M" 2>/dev/null || echo 0)"
if [ "$rows" -eq 13 ]; then ok "13 rows"; else bad "expected 13 rows, found $rows"; fi
echo

# --------------------------------------------- 3. nothing silently unresolved
echo "[3] no item is silently absent (every ⛔ is spelled out in prose)"
gaps="$(grep -cE '⛔' "$M" 2>/dev/null || echo 0)"
if [ "$gaps" -gt 0 ]; then
  note "$gaps blocking gap(s) recorded -- draft is complete, freeze is NOT ready"
  grep -nE '^\| [0-9]+ \|.*⛔|^## [0-9]+\..*⛔' "$M" | sed 's/^/        /'
else
  ok "no blocking gaps recorded"
fi
echo

# -------------------------------------------------- 4. STATS_RULES structure
echo "[4] STATS_RULES.md -- three primary endpoints + the <n> ruling"
for pat in "^## 1\. 主终点一" "^## 2\. 主终点二" "^## 3\. 主终点三" "^## 5\. ⟨n⟩"; do
  if grep -qE "$pat" "$S"; then ok "${pat}"; else bad "missing section: ${pat}"; fi
done
if grep -q '⟨n⟩ = 2' "$S"; then ok "<n> is ruled (n = 2)"; else bad "<n> not ruled"; fi
# the anti-gaming audit the ticket asked for
if grep -q '这条能被怎么钻' "$S"; then
  k="$(grep -c '这条能被怎么钻' "$S")"
  ok "anti-gaming audit present (${k} sections)"
else
  bad "no anti-gaming audit ('这条能被怎么钻') in STATS_RULES.md"
fi
echo

# ------------------------------------------------ 5. CLAIMS: C1-C5, both ways
echo "[5] CLAIMS_TEXT.md -- C1..C5 each carry BOTH outcomes"
for c in C1 C2 C3 C4 C5; do
  # slice the section for this claim and require both verbatim outcome blocks
  body="$(awk -v c="$c" '
      $0 ~ "^## "c" ·" {on=1; next}
      on && /^## C[0-9] ·/ {on=0}
      on' "$C")"
  if [ -z "$body" ]; then bad "$c: no section"; continue; fi
  yes="$(printf '%s' "$body" | grep -c '### 成立版')"
  no="$(printf  '%s' "$body" | grep -c '### 不成立版')"
  if [ "$yes" -ge 1 ] && [ "$no" -ge 1 ]; then
    ok "$c has both outcomes"
  else
    bad "$c: 成立版=$yes 不成立版=$no (need >=1 of each)"
  fi
done
echo

# ------------------------------------------- 6. PENDING_FIVE: 5, each classed
echo "[6] PENDING_FIVE.md -- all five items present and classified"
i=0
for h in "一" "二" "三" "四" "五"; do
  i=$((i+1))
  hdr="$(grep -n "^## ${h} · " "$P" 2>/dev/null | head -1)"
  if [ -z "$hdr" ]; then bad "pending item ${i} (${h}) missing"; continue; fi
  if printf '%s' "$hdr" | grep -qE '✅|⚠|🔴'; then
    ok "pending ${h}"
  else
    bad "pending ${h}: no classification (✅/⚠/🔴)"
  fi
done
if grep -q 'needs_human' "$P"; then ok "needs_human items are marked"; else bad "no needs_human marks"; fi
echo

# ----------------------------------------- 7. the <n> arithmetic still holds
echo "[7] re-run the <n> evidence (the number in STATS_RULES.md §5 must not rot)"
SRC="$HERE/../../baseline-arms/out/campaign"
[ -d "$SRC" ] || SRC="C:/Users/user/Desktop/theoria/baseline-arms/out/campaign"
if [ ! -d "$SRC" ]; then
  note "envelope data not found at $SRC -- cannot re-verify <n>"
  note "this is itself the finding recorded as MANIFEST_DRAFT.md gap 13-a"
else
  out="$(python - "$SRC" <<'PY' 2>&1
import json, glob, math, statistics as st, sys
src = sys.argv[1]
files = sorted(glob.glob(src + "/campaign_*.json"))
if not files:
    print("NODATA"); raise SystemExit
eps = [e for f in files for e in json.load(open(f, encoding="utf-8"))["episodes"]]
ratios, dead = [], 0
for f in files:
    d = json.load(open(f, encoding="utf-8"))["episodes"]
    ok = [e["actions_ok"] for e in d]
    if len(ok) < 2: continue
    m, sd = st.mean(ok), st.stdev(ok)
    p = m / (10.0 + m)
    ratios.append(sd / math.sqrt(10 * p / (1 - p) ** 2))
dead = sum(1 for e in eps if e["outcome"] in
           {"api_unusable", "model_error", "harness_error", "no_reset_window"})
lv = sum(1 for e in eps if e["levels_completed"] > 0)

# Provenance, not just arithmetic. STATS_RULES.md 5.2 first described this
# batch as a later, cleaner envelope re-run; it is in fact the S1 campaign that
# was the contention source in INC-BA-003, started 109s BEFORE the envelope.
# The arithmetic below is unchanged by that -- which is the whole problem: this
# stage stayed green while measuring something other than what the prose said
# it was measuring. So the identity of the data is now asserted too, and a
# batch that stops matching the description turns this stage red rather than
# silently re-blessing the old conclusion.
docs = [json.load(open(f, encoding="utf-8")) for f in files]
scen = {d.get("scenario") for d in docs}
started = {d.get("started") for d in docs}
status = {d.get("status") for d in docs}
prov = "OK"
if scen != {"S1 baseline-parity"}:
    prov = "SCENARIO:%s" % ("|".join(sorted(str(s) for s in scen)))
elif len(started) != 1:
    prov = "STARTED-SPLIT:%d" % len(started)
elif sorted(started)[0] >= "2026-07-27T18:21:25Z":
    prov = "NOT-BEFORE-ENVELOPE:%s" % sorted(started)[0]
elif status != {"episode_limit_hit"}:
    prov = "STATUS:%s" % ("|".join(sorted(str(s) for s in status)))
print("%d %.3f %.3f %d %s" % (len(eps), st.mean(ratios), dead / len(eps), lv, prov))
PY
)"
  if [ "$out" = "NODATA" ] || [ -z "$out" ]; then
    note "envelope present but unreadable"
  else
    set -- $out
    N="$1"; RATIO="$2"; DEATH="$3"; WINS="$4"; PROV="$5"
    echo "        episodes=$N  negbinom obs/pred=$RATIO  infra-death=$DEATH  U3-wins=$WINS"
    echo "        provenance=$PROV"
    # Identity before arithmetic: 5.2's reading of these numbers depends on
    # this batch being the S1 contention source, not a clean envelope re-run.
    case "$PROV" in
      OK) ok "provenance matches STATS_RULES.md 5.2 (S1 baseline-parity, pre-envelope, episode_limit_hit)" ;;
      NOT-BEFORE-ENVELOPE:*) bad "this batch no longer predates the envelope ($PROV) -- 5.2's contention finding must be redone" ;;
      SCENARIO:*) bad "scenario is not S1 baseline-parity ($PROV) -- 5.2 describes a different dataset" ;;
      STARTED-SPLIT:*) bad "the four games no longer share one start ($PROV) -- they are not one campaign, so 5.3's leave-one-out may be live again" ;;
      STATUS:*) bad "status is not episode_limit_hit ($PROV) -- '12 consecutive episodes, not 12 repeats' may no longer hold" ;;
      *) bad "unrecognised provenance verdict: $PROV" ;;
    esac
    # the ruling rests on these three; if any moves, STATS_RULES.md §5 must be redone
    awk -v r="$RATIO" 'BEGIN{exit !(r > 0.80 && r < 1.25)}' \
      && ok "variance still explained by the abort rule (obs/pred=$RATIO)" \
      || bad "obs/pred=$RATIO left [0.80,1.25] -- redo STATS_RULES.md §5.2"
    awk -v d="$DEATH" 'BEGIN{exit !(d > 0.5)}' \
      && ok "infrastructure mortality still high ($DEATH) -- n=2 argument holds" \
      || note "mortality dropped to $DEATH -- the n=2 argument may need restating"
    [ "$WINS" -eq 0 ] \
      && ok "endpoint floor effect intact (0 episodes reached a level)" \
      || note "$WINS episode(s) now reach a level -- §5.2 finding one must be redone"
  fi
fi
echo

# ------------------------------------------------------------------ verdict
echo "=============================================================="
if [ "$FAIL" -eq 0 ]; then
  grn " DRAFT COMPLETE -- all 13 items landed or annotated; $WARN note(s)"
  echo
  echo " This does NOT mean the kit is ready to freeze.  See the ⛔ items"
  echo " in MANIFEST_DRAFT.md and the needs_human rows in PENDING_FIVE.md."
  echo " Freezing is a human action."
  echo "=============================================================="
  exit 0
else
  red " DRAFT INCOMPLETE -- $FAIL check(s) failed"
  echo "=============================================================="
  exit 1
fi
