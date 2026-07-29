# ============================================================================
# READY TO PASTE into freeze/verify.sh, after stage [14] and before the
# "# ------------------------------------------------------------------ verdict"
# block.  RES-1 owns the wiring; this subagent did not edit verify.sh -- several
# subagents share this worktree.
#
# STAGE NUMBER: [15].  [13] = n_feasibility, [14] = residuals, and
# endpoints/verify_sh_stage16.snippet.sh already reserves [16] for the
# one-endpoint-one-wording audit.  Requires $HERE, ok, bad, note -- all already
# defined in verify.sh.  Nothing else is introduced.
#
# ---------------------------------------------------------------------------
# WHAT IT GUARDS, AND WHY
# ---------------------------------------------------------------------------
# Stage [12] exists because build_manifest.py's own docstring said "--verify is
# what belongs in a gate" and it was in no gate at all: the generator was
# correct, tested and never invoked, so MANIFEST.json was free to drift -- and
# it had, by twelve stale hashes.
#
# `freeze/build_engine_manifest.py` (freeze item 5) and
# `freeze/build_budget_table.py` (freeze item 12) each carry the same `--verify`
# mode, each says so in its own docstring in the same words, and as of this
# writing verify.sh mentions NEITHER file anywhere.  Two gates built and left
# unwired.  So `ENGINE_MANIFEST.md`, `BUDGET_TABLE.md` and `BUDGET_TABLE.json`
# had exactly the freedom to drift from their generators that stage [12] takes
# away from `MANIFEST.json`, and for the budget table the drift is worse than
# stale: its totals are sums over append-only ledgers, so the moment a run
# spends, a stale table overstates the remaining headroom -- the direction that
# authorises a campaign which cannot finish.
#
# The disposition is stage [12]'s, unchanged: a drifted generated artefact is a
# FALSE statement about finished work, in the direction of claiming more, so it
# is a hard failure and not a note.
#
# ---------------------------------------------------------------------------
# WHAT THIS STAGE CANNOT SEE -- read this before trusting a green
# ---------------------------------------------------------------------------
#  * The generator is the single source of BOTH sides of each comparison.
#    Delete a caveat from build_engine_manifest.py's ROSTER, regenerate, and
#    --verify is green again while the manifest says strictly less than it did.
#    Neither half of this stage can see that.  The three published-file greps in
#    item05/verify_sh_stage15.snippet.sh (roster is 8 packages, the D-018 enum
#    collision is still disclosed, the ⛔ 5-b version gap is still stated) are
#    the counterweight and are NOT reproduced here -- keep them, do not choose
#    between the two snippets.
#  * The budget table's `pool` half reads `proxy/var/spend_gate.jsonl`, which is
#    gitignored and grows with every proxied call.  A red from 15b therefore
#    does not distinguish "somebody hand-edited the table" from "the balance
#    moved since it was last regenerated"; only reading the printed section list
#    does.  That is by design (the generator's docstring calls a moved balance
#    "the one event that must invalidate a frozen budget table"), but it means
#    15b goes red on its own after any spend, with no edit anywhere.
#  * Neither half checks that the numbers are RIGHT, only that they still
#    recompute.  A citation that has drifted is caught (15b prints CITATION
#    DRIFT); a citation that was wrong when it was written is not.
#  * Cost: ~20 s.  Three `build_engine_manifest.py` runs (~5.5 s each: the
#    check, plus two for the control) and one `build_budget_table.py` run
#    (~8 s).  Both are read-only in --verify mode; neither writes to the tree.
#
# ---------------------------------------------------------------------------
# EXPECTED DISPOSITION ON FIRST PASTE: 15a GREEN, 15b RED.
# ---------------------------------------------------------------------------
# Measured in this worktree, HEAD 3b0dd342, 2026-07-30.  verify.sh is GREEN
# today (DRAFT COMPLETE, 0 failures, 2 notes); pasting this stage as written
# flips it to DRAFT INCOMPLETE on one failure.  The three causes of 15b's red,
# all recorded in endpoints/stage15-evidence.txt, are:
#   1. the pool moved: 11,874 -> 12,154 lines, 5,190 -> 5,296 actions.  $0.00 of
#      new money, but the action headroom really did shrink, and the table still
#      publishes the old figure.
#   2. the generated block in BUDGET_TABLE.md is stale for the same reason.
#   3. CITATION DRIFT on freeze/STATS_RULES.md:777 and :791 -- STATS_RULES.md
#      has been edited under build_budget_table.py's CITED_LINES and the two
#      line numbers now point at the wrong lines ("0.78" moved 777 -> 770,
#      "0.513" moved 791 -> 805).  That one is a genuine defect in the tree and
#      is not fixed by regenerating.
# 1 and 2 clear by `python freeze/build_budget_table.py`; 3 needs the two line
# numbers in CITED_LINES corrected first, or it comes straight back.
# ============================================================================
echo "[15] the other two generated artefacts still describe their sources"

# --- 15a · ENGINE_MANIFEST.md (freeze item 5) -------------------------------
em_out="$(python "$HERE/build_engine_manifest.py" --verify 2>&1)"
if [ $? -eq 0 ]; then
  ok "build_engine_manifest.py --verify: ENGINE_MANIFEST.md still pins the tree it describes"
else
  bad "ENGINE_MANIFEST.md has drifted from the tree -- regenerate and read the diff"
  printf '%s\n' "$em_out" | sed 's/^/        /'
fi

# Negative control for 15a, in stage [13]'s pattern: mutate a COPY outside the
# repo and require a red.  It cannot be stage [13]'s mechanism verbatim, because
# n_feasibility.py is pure arithmetic with no paths, while this generator pins
# HERE/REPO to its own __file__ and shells out to git in REPO -- drop a bare copy
# in $TMPDIR and it dies for want of a repository, which would make a red prove
# nothing.  So the copy keeps HERE pointing at the real freeze/ (REPO, sys.path
# and every git call stay correct) and only the ARTEFACT path is redirected.  The
# two `python -c os.getcwd()` lines exist because a sed replacement string is not
# path-mangled by MSYS: on Git Bash $HERE is /c/... and Python cannot open that.
#
# The unmutated copy is run FIRST and must reproduce the green above.  Without
# that, a botched sed would break the copy, the mutated run would exit non-zero
# for the wrong reason, and the control would report "fires" while testing
# nothing.
em_tmp="$(mktemp -d)"
em_here="$(cd "$HERE" && python -c 'import os; print(os.getcwd().replace(os.sep, "/"))')"
em_dest="$(cd "$em_tmp" && python -c 'import os; print(os.getcwd().replace(os.sep, "/"))')"
sed -e "s|^HERE = os.path.dirname(os.path.abspath(__file__))\$|HERE = r\"$em_here\"|" \
    -e "s|^OUT = os.path.join(HERE, \"ENGINE_MANIFEST.md\")\$|OUT = r\"$em_dest/ENGINE_MANIFEST.md\"|" \
    "$HERE/build_engine_manifest.py" > "$em_tmp/build_engine_manifest.py"
cp "$HERE/ENGINE_MANIFEST.md" "$em_tmp/ENGINE_MANIFEST.md"
if python "$em_tmp/build_engine_manifest.py" --verify >/dev/null 2>&1; then
  sed 's|^tree [0-9a-f]*  engine-rig/engines$|tree 0000000000000000000000000000000000000000  engine-rig/engines|' \
      "$HERE/ENGINE_MANIFEST.md" > "$em_tmp/ENGINE_MANIFEST.md"
  if python "$em_tmp/build_engine_manifest.py" --verify >/dev/null 2>&1; then
    bad "negative control did not fire: zeroing the engine-rig/engines tree hash in a copy stayed green"
  else
    ok "negative control fires: zeroing one pinned hash in a copy of ENGINE_MANIFEST.md turns this stage red"
  fi
else
  note "negative control not run: the relocated copy does not reproduce 15a's own verdict, so a red from it would prove nothing about the real manifest"
fi
rm -rf "$em_tmp"

# --- 15b · BUDGET_TABLE.{json,md} (freeze item 12) --------------------------
bt_out="$(python "$HERE/build_budget_table.py" --verify 2>&1)"
if [ $? -eq 0 ]; then
  ok "build_budget_table.py --verify: BUDGET_TABLE.{json,md} still recompute from the ledgers"
else
  bad "BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff"
  printf '%s\n' "$bt_out" | sed 's/^/        /'
fi

# No negative control on 15b, and this is a real gap rather than an oversight.
# The relocation mechanism does work on it (verified: the relocated copy prints
# byte-identical output to the in-place run, and mutating a clean section of the
# copied JSON -- unit_prices, 0.0435 -> 0.9999 -- adds `unit_prices` to the
# printed "sections that moved" list).  What cannot be built today is a control
# read off the EXIT CODE, because 15b is already red for the three reasons in
# the header: a control that requires non-zero from an already-non-zero check
# passes no matter what it mutates, and reporting that as "the control fires"
# would be a false statement about a test that ran on nothing.  Promote this
# note to a real control -- same shape as 15a's -- once 15b is green.
note "15b has no negative control: it is red today, and a control that requires a red from an already-red check proves nothing (evidence: endpoints/stage15-evidence.txt)"
echo
