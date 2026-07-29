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

# ------------------------------- 8. the 19-vs-21 correction must not grow back
# `freeze/tiers.py --verify` guards two .py files against a hardcoded `N = 21`.
# It cannot see prose -- and prose is where the wrong denominator actually
# lived: after the code was fixed on 2026-07-29, twenty lines across the four
# drafts still read 21, including the analysis-unit table, the Clopper-Pearson
# calibration table, and a "分母恒 21" sitting six sections away from a "/19".
# This stage is the missing half of that gate (RECONCILE N-1).
#
# WHAT IS DETECTED: `21` in the shapes a *count of analysis units* takes --
#   X/21 and 21/X fractions, `21 局`, `21 对`, `21 格`, `n=21`, `恒 21`,
#   a sentence pairing 分母 with 21, `封存堆 21`, `sealed ... 21`, `m ≤ 21`.
# Hashes (`5f21d674…`), line refs (`:121-123`), timestamps (`18:21:25Z`),
# `0.021` and `$1.2184` are not counts and are deliberately not matched.
#
# WHAT IS ALLOWED: an explicit allowlist, keyed on the TEXT of the line rather
# than its number (numbers move; these files grow every session).  Every entry
# says why that particular 21 is correct or why it is knowingly still open.
# Anything else fails.  If you are about to add an entry to make this green,
# read the reason column of the neighbours first -- "21" is right only when the
# sentence is about the sealed pile as an object, never when it is a
# denominator.
#
# SCOPE: the four frozen drafts only.  RECONCILE.md is a worklist that quotes
# the wrong numbers on purpose, and the *.s4draft.md files are the untouched
# porting source -- scanning either would make the stage red for being honest.
echo "[8] 19-vs-21: no frozen draft uses 21 as an analysis-unit count"

# NOTE on the regex: no negated bracket may contain a multibyte character here.
# grep runs byte-oriented, so `[^。]` becomes "not one of the three bytes of 。",
# and E3/80 are bytes that 「 」 ， are all built from -- `分母[^。]*21` silently
# stopped matching at the first quote mark.  Bounded `.{0,60}` instead: a byte
# window, no character classes, no locale surprises.
DETECT='/21([^0-9]|$)|21/[0-9]|21 ?(局|对|格|个)|[nN] ?= ?21|恒 ?21|分母.{0,60}21|21.{0,60}分母|封存堆的? ?21|sealed.{0,20}21|[≤<] ?21'

# file | substring that must appear in the line | why this 21 is legitimate
ALLOW=(
"MANIFEST_DRAFT.md|含封存堆 21 局 / 14,121 基线动作|budget arithmetic: how many games get RUN. Not the statistical denominator. Open, see PENDING_FIVE 4.2."
"STATS_RULES.md|封存堆有 21 局，但|(a) states the sealed pile size in order to say the denominator is NOT it."
"STATS_RULES.md|sealed n=21 只作描述|(a) the tier definition itself -- sealed is descriptive-only by construction."
"STATS_RULES.md|也不需要 21 局封存游戏来确证|(a) the sealed pile as a resource ('you need not spend the pile to show this'), not a denominator."
"STATS_RULES.md|sealed 层 n=21 只作描述|(a) same tier definition, stated again in 1.2 where the three tiers are set out."
"STATS_RULES.md|达成 14 在 n=21 下的 CI 下界是|(a) recomputation of P-22's OLD table, quoted to show it was wrong at its own n."
"STATS_RULES.md|必修一把分母从 21 改成 19|(a) the correction's own record of what it changed."
"STATS_RULES.md|是 n=21 下的值（21/3 = 7|(a) the superseded integer threshold, kept so the change is auditable."
"STATS_RULES.md|按 \`piles.json\` 里 sealed 21 局的|OPEN, RECONCILE N-2: the ⟨m⟩ exam-subset rule still selects from the sealed 21 and so can select a quarantined game. Known wrong, tracked, NOT fixed here."
"CLAIMS_TEXT.md|不是封存堆的 21|(a) names 21 in order to reject it as the denominator."
"PENDING_FIVE.md|\`sealed_pile\` 21 = 25 自洽|(a) the pile cut's own arithmetic, 4 + 21 = 25 public games."
"PENDING_FIVE.md|封存堆 21 局，官方基线动作合计|budget denominator = games run; carries the caveat immediately below it."
"PENDING_FIVE.md|这个 21 是「要跑多少局」|(a) the caveat that distinguishes games-run from the statistical denominator."
"PENDING_FIVE.md|跑满 21 局、只在 19 局上主张|(a) same caveat, spelling out that the two counts need not be equal."
"PENDING_FIVE.md|上表按 21 局算|(a) same caveat, stating the direction of the resulting bias."
"PENDING_FIVE.md|约束是 m ≤ 21|OPEN, RECONCILE N-2: same ⟨m⟩ bound. Must become 19 when N-2 is done."
)

hits="$(cd "$HERE" && grep -nE "$DETECT" \
        MANIFEST_DRAFT.md STATS_RULES.md CLAIMS_TEXT.md PENDING_FIVE.md 2>/dev/null)"
used=""
n21=0
if [ -n "$hits" ]; then
  while IFS= read -r hit; do
    [ -z "$hit" ] && continue
    hfile="${hit%%:*}"; rest="${hit#*:}"
    hline="${rest%%:*}"; htext="${rest#*:}"
    allowed=0
    idx=0
    for entry in "${ALLOW[@]}"; do
      idx=$((idx+1))
      afile="${entry%%|*}"; tail="${entry#*|}"; apat="${tail%%|*}"
      [ "$afile" = "$hfile" ] || continue
      case "$htext" in
        *"$apat"*) allowed=1; used="$used $idx"; break ;;
      esac
    done
    if [ "$allowed" -eq 0 ]; then
      bad "$hfile:$hline uses 21 as a count -- the claim set is 19 (F-11). Line: $htext"
      n21=$((n21+1))
    fi
  done <<EOF
$hits
EOF
fi
[ "$n21" -eq 0 ] && ok "no unexplained 21 in the four drafts (${#ALLOW[@]} allowlisted, each with a reason)"

# A stale allowlist entry is a silent hole: it stops covering anything and
# nobody notices.  Report the ones that matched nothing.
idx=0
for entry in "${ALLOW[@]}"; do
  idx=$((idx+1))
  case " $used " in
    *" $idx "*) ;;
    *) afile="${entry%%|*}"; tail="${entry#*|}"; apat="${tail%%|*}"
       note "allowlist entry ${idx} matched nothing and can be deleted: $afile -- $apat" ;;
  esac
done

# The other direction: the corrected numbers must actually be present.  A file
# with no 21 and no 19 would pass the check above while saying nothing.
for want in "19" "12"; do
  if grep -q "claim 层 ${want}\|n = ${want}\|n=${want}\|/${want}" "$S"; then
    ok "STATS_RULES.md still carries the n=${want} tier"
  else
    bad "STATS_RULES.md no longer mentions the n=${want} tier -- the correction is gone"
  fi
done

# And the code-side half of the same gate, so both halves fail together.
if python "$HERE/tiers.py" --verify >/dev/null 2>&1; then
  ok "freeze/tiers.py --verify (claim set still 21/19/12, no script hardcodes it)"
else
  bad "freeze/tiers.py --verify failed -- run it for the reason"
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
