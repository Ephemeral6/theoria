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
# EXPECTED DISPOSITION ON FIRST PASTE: this stage is RED today.  Measured on
# STATS_RULES.md @ 2026-07-30 04:49 and CLAIMS_TEXT.md @ 2026-07-29 22:25:
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
     ("S2", r"跨claim层19|19对|配对数"), ("C4", r"19|claim层"),
     "C4 is 主骨 and names no n at all; the sealed 21 reading is available in the "
     "published sentence, and stage [8] cannot see an ABSENT 19"),
    ("E2/tier",  "E2", "the clean-tier replication", "hard",
     ("S2", r"clean层12"), ("C4", r"clean层12"),
     "and the exam runs on the front prefix of the codepoint order, where the "
     "clean games are scarce: 2 at m=5, 4 at m=10, 7 only at m=14"),
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
     ("*", r"⟨m⟩对|配对数[^\n]{0,12}⟨m⟩"), ("*", r"⟨m⟩对|配对数[^\n]{0,12}⟨m⟩"),
     "§0 declares 19/12 globally; the exam can only ever have ⟨m⟩ pairs, and "
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
    if "消融臂" in hold and re.search(r"needs_human", s3):
        failed.add("E3/ablstatus")
        msgs.append(("FAIL", "E3 `theoria − 消融臂`: C2's 成立版 makes it a conjunct of "
                             "the claim while STATS_RULES.md §3.2 still types it "
                             "needs_human/exploratory -- either it is a FOURTH primary "
                             "endpoint (Theoria.md:373 says three) or the verbatim claim "
                             "rests on a quantity no test backs"))
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
