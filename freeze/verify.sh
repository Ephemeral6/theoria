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
"MANIFEST_DRAFT.md|含封存堆 21 局 / 14,121 基线动作|budget arithmetic: how many games get RUN, kept as the UPPER BOUND. Not the statistical denominator. RES-1 recommends running 19; monitor confirms the budget line (RECONCILE ruling 2, PENDING_FIVE 4.2.1)."
"STATS_RULES.md|封存堆有 21 局，但|(a) states the sealed pile size in order to say the denominator is NOT it."
"STATS_RULES.md|sealed n=21 只作描述|(a) the tier definition itself -- sealed is descriptive-only by construction."
"STATS_RULES.md|也不需要 21 局封存游戏来确证|(a) the sealed pile as a resource ('you need not spend the pile to show this'), not a denominator."
"STATS_RULES.md|sealed 层 n=21 只作描述|(a) same tier definition, stated again in 1.2 where the three tiers are set out."
"STATS_RULES.md|达成 14 在 n=21 下的 CI 下界是|(a) recomputation of P-22's OLD table, quoted to show it was wrong at its own n."
"STATS_RULES.md|必修一把分母从 21 改成 19|(a) the correction's own record of what it changed."
"STATS_RULES.md|是 n=21 下的值（21/3 = 7|(a) the superseded integer threshold, kept so the change is auditable."
"STATS_RULES.md|原条款作废|(a) names the SUPERSEDED ⟨m⟩ source (sealed_pile) in order to record what was wrong and why. The operative rule is the line above it and draws from claim_set; stage 9 enforces that."
"CLAIMS_TEXT.md|不是封存堆的 21|(a) names 21 in order to reject it as the denominator."
"PENDING_FIVE.md|\`sealed_pile\` 21 = 25 自洽|(a) the pile cut's own arithmetic, 4 + 21 = 25 public games."
"PENDING_FIVE.md|封存堆 21 局，官方基线动作合计|budget denominator = games run; carries the caveat immediately below it."
"PENDING_FIVE.md|这个 21 是「要跑多少局」|(a) the caveat that distinguishes games-run from the statistical denominator."
"PENDING_FIVE.md|跑满 21 局、只在 19 局上主张|(a) same caveat, spelling out that the two counts need not be equal."
"PENDING_FIVE.md|上表按 21 局算|(a) same caveat, stating the direction of the resulting bias."
"PENDING_FIVE.md|原条款的抽取源是|(a) same superseded ⟨m⟩ source, recorded so the correction is auditable. The operative rule two lines above draws from claim_set; stage 9 enforces that."
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

# ---------------------------- 9. the ⟨m⟩ exam subset is drawn from the 19
# Stage 8 catches a *denominator* that reads 21.  This stage catches something
# stage 8 cannot see: a pre-registered SELECTION RULE whose source list is the
# sealed 21.  That rule was in both drafts (RECONCILE N-2) and it did not merely
# risk picking a quarantined game -- under its own ordering it picked ft09 at
# m>=5 and ls20 at m>=9, deterministically.  A result on either is uninterpretable
# in both directions ("never seen" is false for them), so a rule that can select
# one is a defect in the rule.
#
# WHAT THIS ENFORCES, and why each half is here:
#   1. the rule, EXECUTED: for every legal m the prefix must avoid `quarantined`.
#   2. a NEGATIVE CONTROL: the superseded sealed-pile rule must still be shown to
#      select them.  Without it, check 1 could pass by testing nothing.
#   3. the prose: every line carrying the draw clause `取前 ⟨m⟩ 局` must name
#      `claim_set` and must not mention sealed or 21 -- so putting the rule back
#      on the sealed pile turns this red, in either file.
#   4. the bound: every `m ≤ N` in the two files must read 19.
#   5. the ORDER TABLE printed in STATS_RULES.md is recomputed and compared row
#      by row, so the published list cannot drift from the rule that made it.
echo "[9] the ⟨m⟩ exam-subset rule draws from the claim-set 19, never the sealed 21"
CS="$HERE/../arc-recon/data/claim_set.json"
PL="$HERE/../arc-recon/data/piles.json"
if [ ! -s "$CS" ] || [ ! -s "$PL" ]; then
  bad "claim_set.json / piles.json not readable from the freeze kit ($CS)"
else
  m_out="$(python - "$CS" "$PL" "$S" "$P" <<'PY' 2>&1
import json, re, sys

# The drafts are Chinese and the draw clause itself contains ⟨m⟩, so this
# script's own diagnostics are not ASCII.  On Windows the default stdout
# codec is gbk and every message below would die on U+27E8 -- which would
# have shown up as "stage 9 did not run cleanly", i.e. a red gate for an
# encoding reason rather than a content one.  Pin UTF-8.
sys.stdout.reconfigure(encoding="utf-8")

cs_path, pl_path, s_path, p_path = sys.argv[1:5]
cs = json.load(open(cs_path, encoding="utf-8"))
pl = json.load(open(pl_path, encoding="utf-8"))

claim = cs["claim_set"]
quar = set(cs["quarantined"])
sens = set(cs.get("retained_with_sensitivity_analysis", []))

# THE RULE, executable: claim_set, sorted by game_id code point, first m.
order = sorted(claim)

# 1. the guarantee, checked at every legal m rather than argued
hits = [m for m in range(1, len(order) + 1) if set(order[:m]) & quar]
if hits:
    print("FAIL the rule selects a quarantined game at m=%s" % hits[:3])
elif len(order) != 19 or set(order) != set(claim) or (set(order) & quar):
    print("FAIL claim_set changed shape: |claim|=%d overlap=%s"
          % (len(order), sorted(set(order) & quar)))
else:
    print("PASS rule selects no quarantined game at any m in 1..19 (quarantined: %s)"
          % ", ".join(sorted(quar)))

# 2. negative control -- the superseded rule must still be shown to be wrong
sealed = sorted(pl["sealed_pile"])
pos = {g: sealed.index(g) + 1 for g in sorted(quar) if g in sealed}
if len(pos) == len(quar) and pos:
    print("PASS negative control holds: the old sealed-pile rule selects %s"
          % ", ".join("%s at m>=%d" % (g, i) for g, i in sorted(pos.items(), key=lambda kv: kv[1])))
else:
    print("FAIL negative control broke: quarantined games missing from sealed_pile (%r) "
          "-- this stage would then be testing nothing" % pos)

# 3. the prose: the draw clause must name its source, in both files
DRAW = "取前 ⟨m⟩ 局"          # 取前 ⟨m⟩ 局
for name, path in (("STATS_RULES.md", s_path), ("PENDING_FIVE.md", p_path)):
    text = open(path, encoding="utf-8").read()
    lines = [l.strip() for l in text.split("\n") if DRAW in l]
    if not lines:
        print("FAIL %s: the ⟨m⟩ draw clause is gone -- the rule must stay stated verbatim" % name)
        continue
    clean = True
    for l in lines:
        if "claim_set" not in l:
            print("FAIL %s: draw clause does not name claim_set: %s" % (name, l)); clean = False
        if "sealed" in l or "21" in l:
            print("FAIL %s: draw clause is back on the sealed pile: %s" % (name, l)); clean = False
    if clean:
        print("PASS %s: %d draw clause(s), every one sourced from claim_set" % (name, len(lines)))

# 4. the bound
bounds = set()
for name, path in (("STATS_RULES.md", s_path), ("PENDING_FIVE.md", p_path)):
    text = open(path, encoding="utf-8").read()
    for n in re.findall(r"m\s*[≤<=]+\s*(\d+)", text):
        bounds.add((name, n))
wrong = sorted(b for b in bounds if b[1] != "19")
if wrong:
    print("FAIL the ⟨m⟩ bound is not 19: %s" % wrong)
elif bounds:
    print("PASS the ⟨m⟩ bound reads m ≤ 19 in %d place(s)" % len(bounds))
else:
    print("FAIL no ⟨m⟩ bound is stated in either file")

# 5. the published order table vs the rule that produced it
stats = open(s_path, encoding="utf-8").read()
blk = re.search(r"M-ORDER:BEGIN(.*?)M-ORDER:END", stats, re.S)
if not blk:
    print("FAIL STATS_RULES.md: the generated ⟨m⟩ order block (M-ORDER) is missing")
else:
    got = re.findall(r"^\s*>?\s*(\d+)\s+([0-9a-z]{4}-[0-9a-f]{8})\s*$", blk.group(1), re.M)
    want = [(str(i + 1), g) for i, g in enumerate(order)]
    if got == want:
        print("PASS the published order table matches the rule, all %d rows" % len(want))
    else:
        diff = next((i for i in range(max(len(got), len(want)))
                     if got[i:i + 1] != want[i:i + 1]), None)
        print("FAIL order table drifted from the rule: doc has %d rows, rule has %d, "
              "first difference at row %s (doc=%s rule=%s)"
              % (len(got), len(want), None if diff is None else diff + 1,
                 got[diff:diff + 1], want[diff:diff + 1]))

# 6. the exposure skew of the prefix is a property of the rule, so it is
#    recomputed rather than trusted -- the disclosure must not go stale.
want_s = "M-EXPOSURE: prefix5=%d/5 prefix10=%d/10" % (
    sum(1 for g in order[:5] if g in sens), sum(1 for g in order[:10] if g in sens))
if want_s in stats:
    print("PASS prefix exposure disclosure is present and current (%s)" % want_s)
else:
    print("FAIL STATS_RULES.md must carry the sentinel '%s' -- recomputed from the rule" % want_s)
PY
)"
  while IFS= read -r line; do
    case "$line" in
      "PASS "*) ok "${line#PASS }" ;;
      "FAIL "*) bad "${line#FAIL }" ;;
      "") ;;
      *) bad "stage 9 did not run cleanly: $line" ;;
    esac
  done <<EOF
$m_out
EOF
fi
echo

# ------------- 10. the U3 axiom criterion: one rule, stated the same in both
# RECONCILE N-4.  `STATS_RULES.md` §1.2 judges U3 criterion (b) by the G1
# axiom WHITELIST; `CLAIMS_TEXT.md`'s C1 verbatim text said 空公理集 (empty
# axiom set).  Both files claim to be the verbatim text of the SAME endpoint,
# and they were incompatible: judge by the whitelist, publish by the empty set,
# and the published sentence is false -- while wording rule 1 ("a claim may
# come only from CLAIMS_TEXT.md") is broken in the direction nobody notices.
#
# Stage 9 guards a pre-registered SELECTION rule.  This stage guards a
# pre-registered ACCEPTANCE criterion against the same failure mode: two
# copies of one rule drifting apart.
#
# WHAT THIS ENFORCES:
#   1. neither verbatim block in C1 states the superseded empty-axiom-set
#      criterion (the amendment record above them may quote it -- that is
#      prose, not a claim, and is deliberately out of scope);
#   2. the 成立版 block names the whitelist in full -- all three allowed
#      axioms AND both never-allowed ones, so it cannot be relaxed by
#      quietly dropping `sorryAx` from the published sentence;
#   3. STATS_RULES.md §1.2 still carries the same five names, so the two
#      files cannot drift by one side forgetting the list;
#   4. §9.2 (non-triviality check) and §9.14 (U3 has no implementation) are
#      typed 开跑前置条件, not needs_impl.  This is the price of item 2:
#      criterion (b) was relaxed, so criterion (c) is now the ONLY thing
#      standing between a vacuous theorem and a counted U3 -- and a vacuous
#      theorem is the case (b) scores most cleanly, since it uses the fewest
#      axioms.  Relaxing (b) without hardening (c) leaves the endpoint easier
#      to game than before the amendment;
#   5. a NEGATIVE CONTROL: checks 1-2 are re-run against a mutated copy that
#      restores the old wording, and must go red on it.  Without this the
#      stage could pass by matching nothing.
echo "[10] U3 criterion (b): CLAIMS_TEXT.md and STATS_RULES.md state one rule"
g1_out="$(python - "$C" "$S" <<'PY' 2>&1
import re, sys
sys.stdout.reconfigure(encoding="utf-8")

c_path, s_path = sys.argv[1:3]
claims = open(c_path, encoding="utf-8").read()
stats  = open(s_path, encoding="utf-8").read()

ALLOWED  = ["propext", "Quot.sound"]
REFUSED  = ["Classical.choice", "sorryAx", "ofReduceBool"]
SUPERSEDED = ["公理集为空", "空公理集", "公理集非空", "不报告任何公理"]

# Every axiom name allowed to appear ANYWHERE in the frozen drafts.  A name
# outside this set is a whitelist that grew -- see check 3b.  `Classical.em`
# is here because the counterexample that justifies excluding Classical.choice
# is stated in the drafts.
KNOWN_AXIOMS = set(ALLOWED) | set(REFUSED) | {"Lean.ofReduceBool", "Classical.em"}

# A "claim" section is `## C<n> · …`; C1 is the one that carries U3.
def c1_section(text):
    m = re.search(r"^## C1 [·・].*?(?=^## C[0-9]|\Z)", text, re.M | re.S)
    return m.group(0) if m else None

def verbatim_blocks(text):
    """Every '（逐字）' quote block inside C1, keyed by its heading.

    Scoped to C1 rather than to the file: `re.search` on a bare heading
    pattern takes the FIRST match anywhere, so a claim inserted above C1
    would silently redirect this audit.  Keyed by whatever heading is
    actually there rather than by a fixed pair of names, because C2 already
    sets the precedent that a claim may publish a third outcome
    (`结局三 · B-2`) -- a third outcome under C1 carrying a different
    acceptance criterion must be audited, not ignored.
    """
    sec = c1_section(text)
    if sec is None:
        return None
    out = {}
    for m in re.finditer(r"^### ([^\n]*?（逐字）)[ \t]*$(.*?)(?=^###|\Z)", sec, re.M | re.S):
        out[m.group(1).strip().replace("（逐字）", "")] = "\n".join(
            l for l in m.group(2).split("\n") if l.lstrip().startswith(">"))
    return out

def audit(text, label):
    """Returns a list of complaints.  Empty list == the criterion is aligned."""
    bad = []
    blocks = verbatim_blocks(text)
    if blocks is None:
        return ["%s: C1's section could not be located -- the audit has no subject" % label]
    for name in ("成立版", "不成立版"):
        if name not in blocks:
            bad.append("%s: C1 has no %s（逐字）block" % (label, name))
    for name, block in blocks.items():
        for s in SUPERSEDED:
            if s in block:
                bad.append("%s: C1 %s states the superseded criterion %r"
                           % (label, name, s))
        # A published sentence may not point somewhere else for the rule it
        # is supposed to BE.  Without this, C1 can keep its pinned wording
        # byte-for-byte and append "the operative whitelist is §1.9" -- the
        # rule moves out of range of every check below and the claim text
        # says so out loud.
        # Narrow on purpose: 成立版 legitimately says "两层分歧时以弱者为准",
        # which is a rule it STATES.  What is refused is delegating the
        # ACCEPTANCE CRITERION -- the whitelist, the axioms, criterion (b) --
        # to somewhere this stage does not read.
        for pointer in re.findall(r"(白名单|判据|公理)[^\n]{0,24}(为准|仅为历史|另见)", block):
            bad.append("%s: C1 %s delegates its own acceptance criterion elsewhere "
                       "(%s…%s) -- a verbatim claim must state the rule, not cite it"
                       % (label, name, pointer[0], pointer[1]))
    extra = [n for n in blocks if n not in ("成立版", "不成立版")]
    if extra:
        bad.append("%s: C1 carries an unaudited extra verbatim outcome %s -- "
                   "a third outcome may not smuggle a different criterion"
                   % (label, sorted(extra)))
    hold = blocks.get("成立版", "")
    for a in ALLOWED + REFUSED:
        if a not in hold:
            bad.append("%s: C1 成立版 does not name %r from the G1 whitelist" % (label, a))
    return bad

# 1 + 2 -- the live file
live = audit(claims, "CLAIMS_TEXT.md")
for b in live:
    print("FAIL " + b)
if not live:
    print("PASS C1's two verbatim blocks state the G1 whitelist, not the empty axiom set")

# 3 -- the other copy of the same rule.  Scoped to the whitelist TABLE, not to
#      §1.2 at large: the surrounding prose argues about these axioms and names
#      every one of them in passing, so a substring search over the section
#      stays green even after the operative table is gutted.  The disposition
#      each axiom receives is what has to match, so that is what is read.
# SCOPE NOTE.  An earlier form of this check read only §1.2 and only column 2
# of rows containing 放行.  An adversarial pass demonstrated four green
# bypasses against exactly those qualifiers: drop the backticks, put the
# supplement in the reason column, put it in a new section (§1.9), or label
# the row 接受 instead of 放行.  So the scan is now file-wide and shape-free:
# the four frozen drafts may not mention ANY axiom name outside the known
# set, wherever it appears and however it is dressed.  Disposition is still
# read off the table, because that is where disposition lives.
# Any code-ish identifier, not just dotted or camel ones: the bypass that got
# through the first form of this check was a plain snake_case `axiom
# theoria_step_sound`, which no name-shape heuristic was going to catch.  So
# the rule is inverted -- on a disposition row, EVERY identifier must be one
# we already know, and the vocabulary of things that legitimately appear there
# is small enough to enumerate.
AXIOM_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_.]{2,}")
NOT_AN_AXIOM = {
    "Lean", "lean", "sorry", "native_decide", "decide", "rfl", "print",
    "axioms", "propext", "Prop", "noncomputable", "theorem", "axiom",
    "STATS_RULES", "CLAIMS_TEXT", "PENDING_FIVE", "MANIFEST_DRAFT",
}
sec = re.search(r"### 1\.2(.*?)(?=^## |\Z)", stats, re.M | re.S)
if not sec:
    print("FAIL STATS_RULES.md: §1.2 not found -- criterion (b) has no home")
else:
    rows = [l for l in sec.group(1).split("\n")
            if ("放行" in l or "接受" in l) and l.count("|") >= 3]
    passes = [l for l in rows if "永不放行" not in l and "不放行" not in l]
    refuses = [l for l in rows if "永不放行" in l or "不放行" in l]
    drift = []
    for a in ALLOWED:
        if not any(a in l for l in passes):
            drift.append("%s is no longer on the 放行 row" % a)
    for a in REFUSED:
        if any(a in l for l in passes):
            drift.append("%s has been moved onto the 放行 row" % a)
    # The whitelist is CLOSED.  The prose promises that adding an axiom after
    # the freeze is an incident; this is the executable half of that promise,
    # and it is stated over the whole file so that "somewhere else" is not a
    # place a supplement can live.
    for name, path in (("STATS_RULES.md", s_path), ("CLAIMS_TEXT.md", c_path)):
        # Every line that talks about the whitelist, anywhere in the file and
        # under any of its labels -- so "put it in another section", "put it
        # in another column", "drop the backticks" and "call the row 接受"
        # all land inside the scan instead of outside it.
        lines = [l for l in open(path, encoding="utf-8").read().split("\n")
                 if re.search(r"放行|接受|whitelist", l) and l.count("|") >= 3]
        unknown = {n for l in lines for n in AXIOM_TOKEN.findall(l)
                   if n not in KNOWN_AXIOMS and n not in NOT_AN_AXIOM
                   and not re.search(r"\.(md|py|json|jsonl|sh|lean)$", n)}
        if unknown:
            drift.append("%s names axiom(s) outside the frozen whitelist: %s "
                         "(adding one is an incident, not an edit)"
                         % (name, ", ".join(sorted(unknown))))
    if drift:
        print("FAIL STATS_RULES.md §1.2 whitelist table drifted: %s" % "; ".join(drift))
    else:
        print("PASS the whitelist is closed: 放行 = %s, and no axiom outside the "
              "frozen set is named anywhere in the two files" % ", ".join(ALLOWED))

# 4 -- the price of the relaxation
for row, what in (("9.2", "non-triviality check (criterion c)"),
                  ("9.14", "U3 has no implementation")):
    line = next((l for l in stats.split("\n")
                 if l.startswith("| %s |" % row)), None)
    # A substring test cannot tell a promotion from its own retraction: a row
    # reading `~~开跑前置条件~~ -> needs_impl（降级）` contains the substring.
    # Demonstrated green against the first form of this check, so the marks of
    # retraction are read too.
    # `needs_impl` alone is not a mark of retraction -- 9.2's row names it in
    # order to record what it was PROMOTED from.  The direction is what is
    # read: strikethrough, 降级, 暂缓, 豁免.
    retracted = [m for m in ("~~", "降级", "暂缓", "豁免")
                 if line and m in line]
    if line is None:
        print("FAIL STATS_RULES.md §9: row %s is gone -- %s was a launch blocker" % (row, what))
    elif "开跑前置条件" not in line:
        print("FAIL STATS_RULES.md §%s downgraded: %s is no longer a launch blocker"
              % (row, what))
    elif retracted:
        print("FAIL STATS_RULES.md §%s carries 开跑前置条件 alongside marks of its own "
              "retraction (%s) -- %s"
              % (row, ", ".join(retracted), what))
    else:
        print("PASS §%s is a launch blocker (%s)" % (row, what))

# 5 -- negative control: put the old wording back, the audit must catch it
mutant = claims.replace(
    "> `#print axioms` 只报告预注册白名单内公理（`propext` / `Quot.sound`；\n"
    "> `Classical.choice`、`sorryAx` 与 `Lean.ofReduceBool` 均不放行）"
    "且通过非平凡性检查的定理，",
    "> 公理集为空且通过非平凡性检查的定理，")
if mutant == claims:
    print("FAIL negative control could not be built: the 成立版 whitelist sentence "
          "is not where this stage expects it -- the check may be scanning nothing")
elif not audit(mutant, "mutant"):
    print("FAIL negative control did not fire: restoring 空公理集 in C1 still passes "
          "-- this stage is testing nothing")
else:
    print("PASS negative control fires: restoring 空公理集 in C1 turns this stage red")
PY
)"
while IFS= read -r line; do
  case "$line" in
    "PASS "*) ok "${line#PASS }" ;;
    "FAIL "*) bad "${line#FAIL }" ;;
    "") ;;
    *) bad "stage 10 did not run cleanly: $line" ;;
  esac
done <<EOF
$g1_out
EOF
echo

# ------- 11. the launch blockers have an executable gate, and it is honest
#
# Stage 10 keeps §9's launch-blocker rows from being edited away.  It cannot
# tell whether anything implements them -- that is what launch_gate.py is for.
#
# The split of dispositions here is deliberate and is the whole point of the
# stage.  The gate's VERDICT is a note: it is red today, correctly, because
# 9.2/9.11/9.14 are outstanding, and this script must keep exiting 0 while ⛔
# items stand (see its header).  The gate's SELFTEST is a hard failure: if the
# gate cannot demonstrate it would say "clear" when a blocker is genuinely
# cleared, and "blocked" for each known way of faking one, then the executable
# half of §9 does not exist and the draft is not complete.
echo "[11] the §9 launch blockers have an executable gate"

# Python writes to a pipe in the locale encoding; the rest of this script is
# UTF-8, so pin it or the row subjects come back as mojibake.
export PYTHONIOENCODING=utf-8

st_out="$(python "$HERE/launch_gate.py" --selftest 2>&1)"
if [ $? -eq 0 ]; then
  ok "launch_gate.py --selftest: $(printf '%s' "$st_out" | tail -1 | tr -d ' ') cases, both directions"
else
  bad "launch_gate.py --selftest is red -- the gate cannot be trusted either way"
  printf '%s\n' "$st_out" | sed 's/^/        /'
fi

gate_json="$(python "$HERE/launch_gate.py" --json 2>&1)"
gate_rc=$?
if [ "$gate_rc" -eq 2 ]; then
  bad "launch_gate.py cannot evaluate itself (exit 2) -- §9 is unreadable to it"
  printf '%s\n' "$gate_json" | sed 's/^/        /'
elif [ "$gate_rc" -eq 0 ]; then
  ok "launch gate is CLEAR -- every §9 launch blocker is implemented"
else
  n_blocked="$(printf '%s' "$gate_json" | python -c \
    'import json,sys; d=json.load(sys.stdin); print(sum(1 for b in d["blockers"] if not b["cleared"]))' \
    2>/dev/null || echo "?")"
  note "launch gate is BLOCKED: $n_blocked §9 launch blocker(s) outstanding -- the sealed campaign must not spend yet (this is a note, not a failure: the draft is complete, the kit is not ready)"
  printf '%s' "$gate_json" | python -c \
    'import json,sys
for b in json.load(sys.stdin)["blockers"]:
    if not b["cleared"]:
        print("        §%-5s %s" % (b["row"], b["subject"]))' 2>/dev/null
fi
echo

echo "[12] MANIFEST.json still describes this tree"

# `build_manifest.py`'s own docstring says "--verify is what belongs in a gate",
# and until this stage existed it was in no gate at all: the generator was
# correct, tested, and never invoked, so the one file whose entire job is to say
# "these exact bytes are what the campaign ran against" was free to drift.
# It had. Twelve of its content hashes were stale and `generated_from.dirty` was
# `true` -- a manifest generated from a dirty tree cannot be reproduced from any
# commit, which is the property it exists to provide.
#
# This is a hard failure, not a note. Stage [11]'s BLOCKED is a note because a
# blocker that is honestly outstanding is a true statement about an unfinished
# kit. A drifted manifest is a *false* statement about a finished one, and it is
# false in the direction of claiming more.
bm_out="$(python "$HERE/build_manifest.py" --verify 2>&1)"
if [ $? -eq 0 ]; then
  ok "build_manifest.py --verify: the hash table matches the tree it pins"
else
  bad "MANIFEST.json has drifted from the tree -- regenerate and read the diff"
  printf '%s\n' "$bm_out" | sed 's/^/        /'
fi
echo

echo "[13] cell yield vs <n>, and the floors are sealed (STATS_RULES.md 5.7)"

# 5.7's first version was wrong, and the way it was wrong is why this stage is
# shaped like this.  It took 47/48 for an "infrastructure death rate", compounded
# it, and concluded <n> buys nothing -- but that 47/48 was the hit rate of an
# abort constant that D-016 has since deleted from the code, and a second tracked
# measurement (0/9, post-fix) was sitting in the same tree unread.  Same-day
# adversarial review refuted it; the section now states the conditional and names
# what is still undefined ("this cell yielded an observation").
#
# So the gate checks two things the prose cannot:
#   * both directions of the conclusion -- if the optimistic measurement stops
#     clearing the floor, or the pessimistic one starts clearing it, 5.7's
#     premise moved and the stage goes red to force a rewrite;
#   * that the PRE-REGISTERED floors have not been edited.  The first version
#     claimed FLOORS and EXPECTED were sealed together; that claim was false --
#     verify() hardcoded 14, so moving the floor to 10 stayed green and printed
#     10/19's threshold under the 14/19 label.  The floors now carry a digest.
nf_out="$(python "$HERE/n_feasibility.py" --verify 2>&1)"
if [ $? -eq 0 ]; then
  ok "n_feasibility.py --verify: 5.7's thresholds recompute, both measurements land where the section says, floors seal intact"
else
  bad "5.7's arithmetic, its premise, or the pre-registered floors moved"
  printf '%s\n' "$nf_out" | sed 's/^/        /'
fi

# Negative control, aimed at the exact hole the adversarial round demonstrated:
# move the pre-registered claim-tier floor from 14 to 10 and require a red.  The
# old negative control perturbed a prose-vs-arithmetic constant instead, which is
# why it could not see a floor being edited.
nf_tmp="$(mktemp -d)"
sed 's/"claim-14\/19": (14, CLAIM_CELLS)/"claim-14\/19": (10, CLAIM_CELLS)/' \
    "$HERE/n_feasibility.py" > "$nf_tmp/n_feasibility.py"
if python "$nf_tmp/n_feasibility.py" --verify >/dev/null 2>&1; then
  bad "negative control did not fire: the pre-registered floor 14 -> 10 stayed green"
else
  ok "negative control fires: editing the pre-registered floor 14 -> 10 turns this stage red"
fi
rm -rf "$nf_tmp"
echo

echo "[14] every gap in the kit names who fixes it, where, and how it clears"

# The board item's own criterion for "committable" is: each of the thirteen is
# either pinned to a path + version, or explicitly marked 缺，由谁在哪补.  Stages
# 1/2/12 enforce the first half.  This is the second half, and it was the half
# nothing checked: the kit stated its gaps well and almost never said who owned
# one, so a gap could ride to the freeze commit as a known issue with no owner.
#
# residuals.py refuses four things: a gap declared without a code (untrackable),
# one code declared twice (「it is fixed」 then has two answers), an entry with no
# owner / no landing path / no executable clearing condition, and any
# disagreement with launch_blockers.json about which gaps block the launch.
res_out="$(python "$HERE/residuals.py" --verify 2>&1)"
if [ $? -eq 0 ]; then
  ok "residuals.py --verify: every gap carries an owner, a landing path and a clearing condition"
else
  bad "a gap in the kit has no owner, no landing path, or a duplicated code"
  printf '%s\n' "$res_out" | sed 's/^/        /'
fi
echo

# ============================================================================
# READY TO PASTE into freeze/verify.sh.  RES-1 does the wiring; this subagent
# did not edit verify.sh -- several subagents share this worktree.
#
# STAGE NUMBER: [16].  [13], [14] and [15] are taken (⟨n⟩ feasibility,
# residuals, ENGINE_MANIFEST).  Paste after [15] and before the verdict block.
# Requires $C, $S, ok/bad/note -- all already defined in verify.sh.
#
# WHAT IT IS.  Stage [10] guards ONE criterion of ONE endpoint: U3's axiom
# criterion (b), which once said 空公理集 in CLAIMS_TEXT.md while STATS_RULES.md
# had already moved to the G1 whitelist -- adjudicate by the whitelist, publish
# by the empty set.  This stage generalises that to the whole surface the same
# failure mode lives on: `Theoria.md:373` limits the campaign to THREE primary
# endpoints and `Theoria.md:379` adjudicates verbatim against the pre-registered
# text, so for each of the three there must be ONE ENDPOINT, ONE WORDING.
#
# HOW IT READS.  Two probe kinds, and the distinction matters:
#
#   IDENT   a canonical string that must appear in BOTH files.  Compared with
#           ASCII spaces stripped, because the two files already differ by
#           `/ 2` vs `/2` on the BA formula and that is not a divergence.
#           This is the "defining sentence and pass line appear identically"
#           half of the check.
#   SCOPED  an obligation that both files must STATE, in wordings that cannot
#           be identical because one side carries ⟨…⟩ placeholders.  Each probe
#           names a scope per file (a section, or the whole file) and a pattern
#           per file.  Three outcomes, and all three are reported differently:
#           both -> pass; one -> "only <file> states it"; neither -> "neither
#           file states it", which is the more dangerous case and the one stage
#           [8] structurally cannot see (it detects a 21 that is PRESENT, never
#           a 19 that is ABSENT -- its positive check at verify.sh:344-350 is
#           file-wide and is satisfied by §1's denominators no matter what §2
#           says).
#
# DISPOSITION AS WIRED (RES-1, 2026-07-29, E-WORDING).  The stage was authored
# RED against the drafts as they stood, reporting 11 hard divergences.  All 11
# were then fixed in both files -- see
# freeze/runs/20260729T2040Z-S4-freeze-complete/RUN_STATE.md for the ruling
# behind each -- and three probes were CORRECTED rather than satisfied, because
# the wording they demanded would have been false:
#
#   E2/unit, E2/tier, E2/mpairs  endpoint 2 does not inherit §0's 19/12.  The
#       exam runs on ⟨m⟩ games only, so the probe now requires ⟨m⟩ / ⟨m_clean⟩
#       in both files.  Writing "clean 层 12" into §2 would have satisfied the
#       original probe with a false statement.
#   E3/ablstatus  the original fired on the mere presence of `needs_human` in
#       §3.2.  A residual ⟨δ⟩ may honestly still be open; what may NOT happen is
#       the published sentence RESTING on the ablation quantity.  Rewritten to
#       test that instead.
#
# It is GREEN as wired: 27 probes, 0 hard, 0 soft, both negative controls firing.
# A green here is a narrow claim -- see WHAT IT CANNOT DO below.  The historical
# measurement, for the record:
#
#     27 probes -> 14 pass, 11 hard FAIL, 1 soft NOTE, 1 cross-ref NOTE,
#     2 negative controls both firing.
#
# The 11 reds, and where each is argued:
#     E1/nontriv    D7   非平凡 defined only in STATS_RULES.md
#     E2/unit       D1   endpoint 2 has no denominator in either file
#     E2/tier       D1   endpoint 2 has no clean-tier replication in either
#     E2/agg        D6   全局合计 only in STATS_RULES.md
#     E2/marks      D8   confusion() named only in STATS_RULES.md
#     E2/mpairs     D2   the pairing count is ⟨m⟩ and neither file says so
#     E3/thin       D12  thin only in STATS_RULES.md
#     */sign        D3   the sign-test fallback only in STATS_RULES.md
#     */inconc      D9   the mandated inconclusive text exists nowhere
#     E3/ablstatus  D4   `theoria − 消融臂` is claim-bearing in one, exploratory
#                        in the other
#     E3/nonzero    B.3-1  非零 is an adjective carrying a claim
#
# That is the audit's finding, not a bug in the stage -- the ranked list and a
# one-sentence proposed fix for each is in
# freeze/runs/20260729T2040Z-S4-freeze-complete/endpoints/WORDING_AUDIT.md.
# RES-1 decides whether to land it red as `bad` (the drift is a FALSE statement
# about a frozen rule, which is stage [10]'s own reason for being a hard
# failure) or to soften some rows first.  The probe table carries a `sev`
# column for exactly that: move a row from "hard" to "soft" and it becomes a
# NOTE, with no other edit.
#
# WHAT IT CANNOT DO.  It reads whether a rule is STATED in both places, never
# whether the rule is right, and never whether the code computes it.  Three of
# the four worst findings in WORDING_AUDIT.md are invisible to it for exactly
# that reason (弃权计错 is stated in STATS_RULES.md and contradicted by
# exam/grading/mark.py; the specificity floor has no total order once _rate
# returns None; the BA scalar cannot separate `memoriser` from ground truth).
# Those need a rule/implementation gate, not a wording gate.  A `memoriser`
# probe is included below as the cheapest available proxy: the drafts name
# `bluffer` as the mandatory negative control and never name the arm that
# actually beats this endpoint.
# ============================================================================
echo "[16] one endpoint, one wording: the three primary endpoints agree across the two files"
ep_out="$(python - "$C" "$S" <<'PY' 2>&1
import re, sys
sys.stdout.reconfigure(encoding="utf-8")

c_path, s_path = sys.argv[1:3]
CLAIMS = open(c_path, encoding="utf-8").read()
STATS  = open(s_path, encoding="utf-8").read()

# One wording means one wording up to whitespace.  Nothing else is normalised:
# a different character is a different rule.
def norm(t):
    return re.sub(r"[ \t ]+", "", t)

def section(text, start, end):
    m = re.search(start + r".*?(?=" + end + r"|\Z)", text, re.M | re.S)
    return m.group(0) if m else None

# --- IDENT: the same string, in both files ---------------------------------
#   (id, endpoint, what it is, canonical string)
IDENT = [
    ("E1/test",   "E1", "the test (single-sample proportion)",      "单样本比率"),
    ("E1/ci",     "E1", "the interval",                            "Clopper–Pearson"),
    ("E1/floor",  "E1", "the recommended pass line 14/19",         "14/19"),
    ("E1/hard",   "E1", "the claim-tier hard floor",               "硬下限10"),
    ("E1/hardc",  "E1", "the clean-tier hard floor",               "硬下限7"),
    ("E2/scalar", "E2", "the scalar",       "平衡准确率BA=(灵敏度+特异度)/2"),
    ("E2/floor",  "E2", "the pass-line symbol",                    "⟨S_min⟩"),
    ("E2/veto",   "E2", "the floor being a one-vote veto",         "一票否决"),
    ("E3/arms",   "E3", "the pinned comparison arms",              "theoria−bare_cc"),
    ("E3/dir",    "E3", "the pre-registered direction",  "theoria>schema≈bare_cc"),
    ("E3/test",   "E3", "the test",                                "Wilcoxon符号秩"),
    ("*/holm",    "*",  "the multiplicity correction",             "Holm"),
]

# --- SCOPED: both files must state it, in their own words ------------------
#   (id, endpoint, what, sev, (s_scope, s_pat), (c_scope, c_pat), consequence)
# Scopes: "S1"/"S2"/"S3" = STATS_RULES §1/§2/§3; "C1"/"C2"/"C4" = the claim
# sections; "*" = the whole file.  Patterns are matched against NORMALISED text.
SCOPED = [
    ("E1/unit",  "E1", "the analysis unit / denominator", "hard",
     ("S1", r"达成局数/\*\*19\*\*"), ("C1", r"⟨X_obs/19⟩"),
     "a rate with no stated denominator can be published over any n"),
    ("E1/tier",  "E1", "the clean-tier replication", "hard",
     ("S1", r"clean层12|干净层n=12"), ("C1", r"clean层12"),
     "§1.2 requires every confirmatory statistic twice, weaker of the two wins"),
    ("E1/nontriv", "E1", "what 非平凡 (criterion c) actually requires", "hard",
     ("S1", r"两个可表示状态|每个目标态都被排除"),
     ("C1", r"两个可表示状态|每个目标态都被排除"),
     "§9.2: after (b) was relaxed to the whitelist, (c) is the only gate left -- "
     "stage [10] guards (b) in both directions and nothing guards (c)"),
    ("E2/unit",  "E2", "the analysis unit / denominator", "hard",
     ("S2", r"⟨m⟩局"), ("C4", r"⟨m⟩局"),
     "C4 is 主骨 and named no n at all; the sealed 21 reading was available in "
     "the published sentence, and stage [8] cannot see an ABSENT 19.  The unit "
     "is the ⟨m⟩ exam games -- a prefix of the claim-tier 19, never the 21"),
    ("E2/tier",  "E2", "the clean-tier replication", "hard",
     ("S2", r"⟨m_clean⟩"), ("C4", r"⟨m_clean⟩"),
     "the clean replication for THIS endpoint runs on the clean games among "
     "the ⟨m⟩, whose count is ⟨m_clean⟩ and is NOT 12: the exam takes the front "
     "prefix of the codepoint order, where clean games are scarce -- 2 at m=5, "
     "4 at m=10, 5 at m=12, 6 at m=13, 7 at m=14 (recomputed from claim_set.json)"),
    ("E2/agg",   "E2", "how the specificity floor is aggregated", "hard",
     ("*", r"全局合计"), ("*", r"全局合计"),
     "macro vs micro specificity are different numbers, and this floor is a "
     "one-vote veto"),
    ("E2/marks", "E2", "which half of `exam` supplies the marks", "hard",
     ("*", r"confusion"), ("*", r"confusion"),
     "`exam` also has a total score, which C4 itself quotes (bluffer 0.265)"),
    ("E2/abst",  "E2", "that abstentions count as wrong", "hard",
     ("*", r"弃权计错"), ("*", r"弃权计错"),
     "§2.3's seal on 只答有把握的题 is this clause and nothing else"),
    ("E2/mpairs","E2", "that the pairing count is ⟨m⟩, not 19", "hard",
     ("S2", r"配对数[^\n]{0,8}⟨m⟩对"), ("C4", r"配对数[^\n]{0,8}⟨m⟩对"),
     "§4.1's 19/3 and §4.1.0's 12/3 thresholds are computed on the wrong n"),
    ("E2/memo",  "E2", "`memoriser` as a mandatory negative control", "soft",
     ("*", r"memoriser"), ("*", r"memoriser"),
     "the drafts pin `bluffer`, which the specificity floor already kills; "
     "`memoriser` scores BA = 1.000 on this endpoint (exam/DECISIONS.md D-EX-015)"),
    ("E3/unit",  "E3", "the analysis unit / denominator", "hard",
     ("S3", r"跨claim层19"), ("C2", r"claim层19局上"), ""),
    ("E3/tier",  "E3", "the clean-tier replication", "hard",
     ("S3", r"clean层12"), ("C2", r"clean层12"), ""),
    ("E3/thin",  "E3", "the `thin` disposition", "hard",
     ("*", r"thin"), ("*", r"thin"),
     "C2 成立版 reports a median 在 claim 层 19 局上, but the test runs on "
     "19 minus thin minus void"),
    ("*/sign",   "*",  "the sign-test fallback", "hard",
     ("*", r"符号检验"), ("*", r"符号检验"),
     "§4.1 switches to the sign test when ties exceed 1/3; every verbatim block "
     "says `Wilcoxon 符号秩 p` -- adjudicate by one test, publish another"),
    ("*/inconc", "*",  "the inconclusive outcome", "hard",
     ("*", r"不可结论"), ("*", r"不可结论"),
     "§4.1.0 mandates a verbatim inconclusive text and forbids using either "
     "outcome version; CLAIMS_TEXT.md has no third block and its mechanical "
     "procedure has two branches"),
]

def audit(claims, stats):
    """-> (failed_ids, messages).  Messages are (level, text)."""
    NC, NS = norm(claims), norm(stats)
    scopes = {
        "S1": section(stats,  r"^## 1\. 主终点一", r"^## 2\."),
        "S2": section(stats,  r"^## 2\. 主终点二", r"^## 3\."),
        "S3": section(stats,  r"^## 3\. 主终点三", r"^## 4\."),
        "C1": section(claims, r"^## C1 [·・]",     r"^## C2 [·・]"),
        "C2": section(claims, r"^## C2 [·・]",     r"^## C3 [·・]"),
        "C4": section(claims, r"^## C4 [·・]",     r"^## C5 [·・]"),
    }
    failed, msgs = set(), []
    # A missing section is not a pass -- it is an audit with no subject.
    for k, v in scopes.items():
        if v is None:
            failed.add("scope/" + k)
            msgs.append(("FAIL", "section %s could not be located -- this stage "
                                 "would be scanning nothing" % k))
    def text_of(which, side):
        if which == "*":
            return NS if side == "S" else NC
        sec = scopes.get(which)
        return norm(sec) if sec else ""

    for pid, ep, what, canon in IDENT:
        in_s, in_c = norm(canon) in NS, norm(canon) in NC
        if in_s and in_c:
            continue
        failed.add(pid)
        where = "CLAIMS_TEXT.md" if in_s else ("STATS_RULES.md" if in_c else "neither file")
        if in_s or in_c:
            msgs.append(("FAIL", "%s %s: %r is in one file but not %s -- one endpoint, "
                                 "two wordings" % (ep, what, canon, where)))
        else:
            msgs.append(("FAIL", "%s %s: %r is in neither file -- the frozen wording "
                                 "is gone from both copies" % (ep, what, canon)))

    for pid, ep, what, sev, (ss, sp), (cs, cp), why in SCOPED:
        in_s = bool(re.search(sp, text_of(ss, "S")))
        in_c = bool(re.search(cp, text_of(cs, "C")))
        if in_s and in_c:
            continue
        failed.add(pid)
        tail = (" -- " + why) if why else ""
        if in_s and not in_c:
            msgs.append((sev, "%s %s: stated in STATS_RULES.md (%s) but NOT in "
                              "CLAIMS_TEXT.md (%s)%s" % (ep, what, ss, cs, tail)))
        elif in_c and not in_s:
            msgs.append((sev, "%s %s: stated in CLAIMS_TEXT.md (%s) but NOT in "
                              "STATS_RULES.md (%s)%s" % (ep, what, cs, ss, tail)))
        else:
            msgs.append((sev, "%s %s: stated in NEITHER file (%s / %s)%s"
                              % (ep, what, ss, cs, tail)))

    # Bespoke 1: one quantity may not carry two statuses.  `theoria − 消融臂` is
    # needs_human/exploratory in §3.2 and a load-bearing conjunct of C2's
    # 成立版.  If it is claim-bearing there, the family is 4, not 3.
    c2 = scopes.get("C2") or ""
    hold = ""
    m = re.search(r"^### 成立版（逐字）[ \t]*$(.*?)(?=^###|\Z)", c2, re.M | re.S)
    if m:
        hold = "\n".join(l for l in m.group(1).split("\n") if l.lstrip().startswith(">"))
    else:
        failed.add("E3/holdblock")
        msgs.append(("FAIL", "E3 C2 has no 成立版（逐字）block -- the ablation-status "
                             "check has no subject"))
    s3 = scopes.get("S3") or ""
    # The rule is NOT "§3.2 must stop saying needs_human" -- a residual ⟨δ⟩ may
    # honestly still be open.  The rule is that the ablation quantity may not be
    # LOAD-BEARING in the published sentence: if it appears in the hold block at
    # all, that block must mark it exploratory / non-evidential, AND §3.2 must
    # have ruled its status.  Otherwise it is a FOURTH primary endpoint
    # (Theoria.md:373 says three) or a verbatim claim resting on an untested one.
    if "消融臂" in hold and not re.search(r"探索性|不构成", hold):
        failed.add("E3/ablstatus")
        msgs.append(("FAIL", "E3 `theoria − 消融臂` appears in C2's 成立版 without being "
                             "marked 探索性 / 不构成……证据 -- the verbatim claim rests on "
                             "it, making it a FOURTH primary endpoint (Theoria.md:373 "
                             "says three) or a claim no test backs"))
    if "消融臂" in hold and not re.search(r"探索性", s3):
        failed.add("E3/ablstatus")
        msgs.append(("FAIL", "E3 `theoria − 消融臂` is reported in C2's 成立版 but "
                             "STATS_RULES.md §3.2 never rules its status -- one quantity "
                             "carrying two statuses is the drift this stage exists for"))
    # Bespoke 2: 非零 is an adjective where the same file already ruled that a
    # threshold must be a test (CLAIMS_TEXT.md's own B-2 note).
    if re.search(r"非零", hold) and not re.search(r"非零[^\n]{0,40}(p ?=|α|检验)", hold):
        failed.add("E3/nonzero")
        msgs.append(("FAIL", "E3 C2 成立版 conditions the claim on the ablation difference "
                             "being 非零 with no test, no α and no direction -- the same "
                             "file rules two sections later that 「更高」是一个检验，"
                             "不是一个形容词"))
    # Bespoke 3: the cross-reference for endpoint 2's paired test.
    s2 = scopes.get("S2") or ""
    if re.search(r"跨局做配对检验（§3）", norm(s2)):
        msgs.append(("NOTE", "E2 STATS_RULES.md §2.2 sends the reader to §3 for the paired "
                             "test; §3 is endpoint THREE and the tests are in §4"))
    return failed, msgs

base_failed, base_msgs = audit(CLAIMS, STATS)
for level, text in base_msgs:
    print(("FAIL " if level in ("FAIL", "hard") else "NOTE ") + text)

for ep, label in (("E1", "U3 attainment rate"),
                  ("E2", "adjudication-question accuracy"),
                  ("E3", "front-loading index paired difference")):
    if not any(f.startswith(ep + "/") for f in base_failed):
        print("PASS %s (%s): defining sentence, scalar, unit, test, direction and "
              "pass line agree across both files" % (ep, label))

# --- negative control ------------------------------------------------------
# Without this the stage could pass by matching nothing.  Two mutations, one
# per probe kind, each targeting a probe that passes TODAY -- so the control
# stays meaningful while the 13 known divergences are still open.
NEG = [
    ("E2/scalar", "the BA formula in C4",
     "(灵敏度 + 特异度)/2", "(灵敏度 + 特异度)/3"),
    ("E1/unit", "the U3 denominator in C1's 成立版",
     "⟨X_obs/19⟩", "⟨X_obs/21⟩"),
]
for pid, what, old, new in NEG:
    if pid in base_failed:
        print("FAIL negative control for %s is vacuous: that probe is ALREADY red, "
              "so mutating it proves nothing -- pick a probe that passes" % pid)
        continue
    mutant = CLAIMS.replace(old, new)
    if mutant == CLAIMS:
        print("FAIL negative control could not be built: %r is not in CLAIMS_TEXT.md "
              "where this stage expects it (%s) -- the probe may be scanning nothing"
              % (old, what))
        continue
    mut_failed, _ = audit(mutant, STATS)
    if pid in mut_failed:
        print("PASS negative control fires: mutating %s (%s -> %s) turns probe %s red"
              % (what, old, new, pid))
    else:
        print("FAIL negative control did not fire: mutating %s still passes probe %s "
              "-- that probe is testing nothing" % (what, pid))

hard = sum(1 for lvl, _ in base_msgs if lvl in ("FAIL", "hard"))
soft = sum(1 for lvl, _ in base_msgs if lvl == "soft")
print("NOTE one-endpoint-one-wording: %d hard divergence(s), %d soft, out of %d probes "
      "(see endpoints/WORDING_AUDIT.md for the ranked list and the proposed fixes)"
      % (hard, soft, len(IDENT) + len(SCOPED)))
PY
)"
while IFS= read -r line; do
  case "$line" in
    "PASS "*) ok   "${line#PASS }" ;;
    "FAIL "*) bad  "${line#FAIL }" ;;
    "NOTE "*) note "${line#NOTE }" ;;
    "") ;;
    *) bad "stage 16 did not run cleanly: $line" ;;
  esac
done <<EOF
$ep_out
EOF
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
