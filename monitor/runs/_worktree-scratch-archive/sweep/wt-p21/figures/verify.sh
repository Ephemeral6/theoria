#!/usr/bin/env bash
# figures/verify.sh -- the P-21 stop gate.
#
# Determinism is a requirement in this repository, not a nicety, so it gets an
# executable form rather than a promise:
#
#   1. build everything into scratch tree A
#   2. build everything again into scratch tree B
#   3. diff A against B -- ANY difference fails
#   4. recompute the data-source hash manifest and diff it against the
#      committed figures/SOURCES.sha256 -- a source that moved under the
#      figures fails
#   5. check every declared artefact exists: 5 figures x 2 themes x 2 formats
#      = 20 images, plus 5 CSVs
#
# Exits non-zero on the first failing gate, naming the offending path.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PYTHON="${PYTHON:-python}"
SCRATCH="$HERE/.verify"
FAILED=0

say()  { printf '%s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; FAILED=1; }
step() { printf '\n== %s ==\n' "$*"; }

trap 'rm -rf "$SCRATCH"' EXIT
rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"

# ---------------------------------------------------------------------------
step "0. required data sources present"
# ---------------------------------------------------------------------------
if ! "$PYTHON" -c "
import sys; sys.path.insert(0, '.')
import sources
missing = sources.check_required()
if missing:
    for m in missing: print(m)
    sys.exit(1)
"; then
    fail "required data sources missing (listed above)"
    exit 1
fi
say "ok"

# ---------------------------------------------------------------------------
step "1. build pass A"
# ---------------------------------------------------------------------------
if ! FIGURES_OUT="$SCRATCH/A/out" FIGURES_CSV="$SCRATCH/A/csv" FIGURES_SHA="$SCRATCH/A/SOURCES.sha256" \
        "$PYTHON" build_all.py > "$SCRATCH/A.log" 2>&1; then
    cat "$SCRATCH/A.log" >&2
    fail "build pass A did not complete"
    exit 1
fi
say "ok  ($(grep -c '  img  ' "$SCRATCH/A.log") images)"

# ---------------------------------------------------------------------------
step "2. build pass B"
# ---------------------------------------------------------------------------
if ! FIGURES_OUT="$SCRATCH/B/out" FIGURES_CSV="$SCRATCH/B/csv" FIGURES_SHA="$SCRATCH/B/SOURCES.sha256" \
        "$PYTHON" build_all.py > "$SCRATCH/B.log" 2>&1; then
    cat "$SCRATCH/B.log" >&2
    fail "build pass B did not complete"
    exit 1
fi
say "ok  ($(grep -c '  img  ' "$SCRATCH/B.log") images)"

# ---------------------------------------------------------------------------
step "3. A vs B, byte for byte"
# ---------------------------------------------------------------------------
# The two trees are built at different wall-clock times into different
# directories. Any surviving difference is non-determinism in a figure script.
for leaf in csv out SOURCES.sha256; do
    if [ -e "$SCRATCH/A/$leaf" ] || [ -e "$SCRATCH/B/$leaf" ]; then
        if ! diff -r "$SCRATCH/A/$leaf" "$SCRATCH/B/$leaf" > "$SCRATCH/diff.$(basename "$leaf").txt" 2>&1; then
            fail "pass A and pass B differ under '$leaf':"
            sed 's/^/    /' "$SCRATCH/diff.$(basename "$leaf").txt" | head -40 >&2
        fi
    fi
done
[ "$FAILED" -eq 0 ] && say "ok  (csv, out, SOURCES.sha256 all identical)"

# ---------------------------------------------------------------------------
step "4. data-source hashes match the committed manifest"
# ---------------------------------------------------------------------------
COMMITTED="$HERE/SOURCES.sha256"
if [ ! -f "$COMMITTED" ]; then
    fail "figures/SOURCES.sha256 is not committed; run build_all.py and commit it"
else
    if ! diff -u "$COMMITTED" "$SCRATCH/A/SOURCES.sha256" > "$SCRATCH/diff.sources.txt" 2>&1; then
        fail "a data source changed under the figures:"
        sed 's/^/    /' "$SCRATCH/diff.sources.txt" | head -40 >&2
    else
        say "ok  ($(grep -c '^[0-9a-fA-F]' "$COMMITTED") sources hashed)"
    fi
fi

# ---------------------------------------------------------------------------
step "5. every declared artefact exists"
# ---------------------------------------------------------------------------
mapfile -t FIGS < <("$PYTHON" build_all.py --list)
if [ "${#FIGS[@]}" -eq 0 ]; then
    fail "build_all.py --list returned nothing"
else
    EXPECTED=0
    for name in "${FIGS[@]}"; do
        for th in light dark; do
            for fmt in svg png; do
                EXPECTED=$((EXPECTED + 1))
                p="$SCRATCH/A/out/$th/$name.$fmt"
                [ -s "$p" ] || fail "missing or empty artefact: out/$th/$name.$fmt"
            done
        done
        c="$SCRATCH/A/csv/$name.csv"
        [ -s "$c" ] || fail "missing or empty CSV: csv/$name.csv"
    done
    say "checked ${#FIGS[@]} figures -> $EXPECTED images + ${#FIGS[@]} CSVs"
fi

# ---------------------------------------------------------------------------
step "6. the committed tree matches a fresh build"
# ---------------------------------------------------------------------------
# Gate 3 proves the pipeline is deterministic. This one proves what is
# committed is what the pipeline currently produces -- otherwise a stale
# figure could sit in the repo behind a green determinism check.
for leaf in csv out; do
    if [ ! -d "$HERE/$leaf" ]; then
        fail "figures/$leaf is not present; run build_all.py and commit it"
    elif ! diff -r "$HERE/$leaf" "$SCRATCH/A/$leaf" > "$SCRATCH/diff.committed.$leaf.txt" 2>&1; then
        fail "committed figures/$leaf differs from a fresh build:"
        sed 's/^/    /' "$SCRATCH/diff.committed.$leaf.txt" | head -40 >&2
    fi
done
[ "$FAILED" -eq 0 ] && say "ok"

# ---------------------------------------------------------------------------
printf '\n'
if [ "$FAILED" -eq 0 ]; then
    say "VERIFY: green. Two builds byte-identical, sources unchanged, all artefacts present."
    exit 0
fi
say "VERIFY: red."
exit 1
