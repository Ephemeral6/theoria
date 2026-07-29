# ============================================================================
# READY TO PASTE into freeze/verify.sh, immediately after stage [12] and before
# the "# ---- verdict" block.  RES-1 does the wiring; this subagent did not edit
# verify.sh, because another subagent is working the same worktree.
#
# Disposition: the `--verify` call is a HARD FAILURE; the outstanding ⛔ is a
# NOTE.  Both halves, and the reason for the split, are stage [12]'s own
# distinction applied one item further:
#
#   an uncleared blocker is a TRUE statement about unfinished work   -> NOTE
#   a drifted manifest is a FALSE statement about finished work      -> FAIL
#
# So: "item 5's eight engines carry no version string" is true, honestly
# recorded, and must not stop the script (the kit is a complete draft, not a
# ready freeze).  "ENGINE_MANIFEST.md pins hashes that are not in the tree" is
# a false statement in the direction of claiming more, and is the same defect
# class stage [12] exists for.
# STAGE NUMBER: [15].  As of this run, [13] and [14] are already taken by the
# ⟨n⟩ / residuals work in flight in this same worktree, so renumber if the
# stages shift again before RES-1 wires this in.
#
# ONE MORE COORDINATION POINT, and it is not optional if [14] stays as it is.
# `freeze/residuals.py`'s `DOCS` list is the four drafts only.  If RES-1 adds
# ENGINE_MANIFEST.md to it, `ANY_MARK` will see the `⛔ 缺 5-b` line and demand
# a `RESIDUALS.json` entry for code `5-b`.  That code is DELIBERATELY the one
# `MANIFEST_DRAFT.md` §5 already declares -- same gap, one code -- and the
# manifest's line starts with `> ` so `DECL` (which anchors on `**⛔` at line
# start) reads it as a reference, not a second declaration.  Suggested entry if
# one is needed:  owner `engine-rig`, landing
# `engine-rig/engines/<pkg>/__init__.py`, kind `fix_code`, clears_when "a
# version string exists for all 8 packages and build_engine_manifest.py stops
# printing ⛔ in the 版本串 column".
# ============================================================================
echo "[15] ENGINE_MANIFEST.md still describes this tree (freeze item 5)"

# Item 5 是 13 项里唯一一项在 P-22 起草时**完全没有落点**的（`MANIFEST_DRAFT.md`
# §5 的 ⛔ 5-a）。`freeze/ENGINE_MANIFEST.md` 是那个落点，`--verify` 是它的门。
if [ ! -s "$HERE/ENGINE_MANIFEST.md" ]; then
  bad "freeze/ENGINE_MANIFEST.md missing or empty -- freeze item 5 has no landing spot again"
else
  em_out="$(python "$HERE/build_engine_manifest.py" --verify 2>&1)"
  if [ $? -eq 0 ]; then
    ok "build_engine_manifest.py --verify: $(printf '%s' "$em_out" | tail -1)"
  else
    bad "ENGINE_MANIFEST.md has drifted from the tree -- regenerate and read the diff"
    printf '%s\n' "$em_out" | sed 's/^/        /'
  fi

  # Three disclosures that `--verify` alone cannot protect, because the
  # generator is the single source of BOTH sides of that comparison: drop a
  # disclosure from `build_engine_manifest.py`, regenerate, and --verify is
  # green again while the manifest says less than it did.  So these are read off
  # the PUBLISHED file, independently of the generator.
  n_eng="$(grep -cE '^\| [0-9] \| `engine-rig/engines/' "$HERE/ENGINE_MANIFEST.md" 2>/dev/null || echo 0)"
  if [ "$n_eng" -eq 8 ]; then
    ok "the roster is 8 packages (CLAUDE.md's 'six' is the frozen enum, not the roster)"
  else
    bad "ENGINE_MANIFEST.md lists $n_eng engine packages, not 8 -- the enum-vs-roster confusion is back"
  fi

  # D-018: two packages declare another package's name, so a consumer keyed on
  # `ENGINE` silently merges 8 rows into 6.  A manifest that stops saying so is
  # a manifest whose own key looks arbitrary.
  if grep -q 'ENGINE = "fd_adapter"' "$HERE/ENGINE_MANIFEST.md" \
     && grep -q 'ENGINE = "lp_potential"' "$HERE/ENGINE_MANIFEST.md" \
     && grep -q 'deadlock_carver' "$HERE/ENGINE_MANIFEST.md" \
     && grep -q 'ic3_pdr' "$HERE/ENGINE_MANIFEST.md"; then
    ok "the D-018 enum collision is still disclosed (deadlock_carver->fd_adapter, ic3_pdr->lp_potential)"
  else
    bad "ENGINE_MANIFEST.md no longer discloses the D-018 enum collision -- keying on the package path then looks arbitrary"
  fi

  # The ⛔ itself.  A NOTE, not a failure -- see the header.
  if grep -q '⛔ 缺 5-b' "$HERE/ENGINE_MANIFEST.md"; then
    note "freeze item 5: 8/8 engines carry no version string (⛔ 5-b, engine-rig track) -- item 5 is recorded, not cleared"
  else
    # Silence here is not good news: either the gap was closed (then the
    # sentinel should be replaced by the versions) or the disclosure was
    # deleted.  Only one of those is progress, and this stage cannot tell them
    # apart, so it refuses to guess.
    bad "ENGINE_MANIFEST.md no longer carries the '⛔ 缺 5-b' version gap -- if the versions now exist, say so; if they do not, the gap may not be silent"
  fi
fi
echo
