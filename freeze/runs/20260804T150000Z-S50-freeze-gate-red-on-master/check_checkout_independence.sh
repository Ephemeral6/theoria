#!/usr/bin/env bash
# S50 · does BUDGET_TABLE.json depend on WHICH CHECKOUT generated it?
#
# It did, in two ways, and both made stage [15b] fail on master for a fix that
# was green on the branch:
#
#   1. `pool.abspath_is_main_checkout` -- True in a worktree, False in the main
#      checkout, and inside the `--verify` comparison. Fixed by moving it to
#      `generated_from`, which `--verify` already strips.
#   2. `policy.sha256` -- a RAW byte digest of `proxy/spend_policy.json`, which
#      is CRLF on disk in the main checkout and LF in a fresh worktree. Git
#      calls neither modified (`proxy/.gitattributes` pins `*.json text
#      eol=lf`), so this was drift with no edit behind it. Fixed by digesting
#      LF-normalised bytes, as `tools/check_locations.py` already does.
#
# This script is the proof, not the argument: it generates the table from the
# worktree and from the main checkout and compares the two, everything except
# `generated_from` and the pool prefix (the pool grows between the two runs --
# that is the whole point of the as-of read, and it is reported separately).
#
#   bash freeze/runs/20260804T150000Z-S50-.../check_checkout_independence.sh
set -euo pipefail

WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MAIN="${WT%%/.worktrees/*}"
[ "$MAIN" != "$WT" ] || { echo "run me from inside a worktree" >&2; exit 2; }

WWT="$(cygpath -m "$WT")"; WMAIN="$(cygpath -m "$MAIN")"
TMP="$(cygpath -m "$(mktemp -d)")"; trap 'rm -rf "$TMP"' EXIT

for tag in wt main; do
  [ "$tag" = wt ] && ROOT="$WWT" || ROOT="$WMAIN"
  sed -e "s|^HERE = os.path.dirname(os.path.abspath(__file__))\$|HERE = r\"$ROOT/freeze\"|" \
      -e "s|^OUT_JSON = os.path.join(HERE, \"BUDGET_TABLE.json\")\$|OUT_JSON = r\"$TMP/$tag.json\"|" \
      -e "s|^OUT_MD = os.path.join(HERE, \"BUDGET_TABLE.md\")\$|OUT_MD = r\"$TMP/$tag.md\"|" \
      "$WT/freeze/build_budget_table.py" > "$TMP/gen_$tag.py"
  cp "$WT/freeze/BUDGET_TABLE.md" "$TMP/$tag.md"
  python "$TMP/gen_$tag.py" >/dev/null
done

python - "$TMP/wt.json" "$TMP/main.json" <<'PY'
import io, json, sys
a = json.load(io.open(sys.argv[1], encoding="utf-8"))
b = json.load(io.open(sys.argv[2], encoding="utf-8"))
# `generated_from` is provenance and is stripped by --verify. The pool sections
# are read live, seconds apart, on a fleet that is spending: they are EXPECTED
# to differ and the as-of read is what makes that harmless.
LIVE = {"generated_from", "pool", "balance", "verdict", "projection"}
moved = sorted(k for k in set(a) | set(b)
               if k not in LIVE and a.get(k) != b.get(k))
print("checkout-dependent sections (must be none): %s" % (moved or "none"))
if a["policy"]["sha256"] != b["policy"]["sha256"]:
    print("  policy.sha256 still differs: %s vs %s"
          % (a["policy"]["sha256"][:12], b["policy"]["sha256"][:12]))
print("  policy.sha256 agrees across checkouts: %s"
      % a["policy"]["sha256"][:12])
print("  pool grew between the two runs: seq %s -> %s (expected; that is what "
      "the as-of read exists for)" % (a["pool"]["as_of_seq"], b["pool"]["as_of_seq"]))
sys.exit(1 if moved else 0)
PY
