#!/usr/bin/env bash
# figures/verify.sh -- the figure-pipeline stop gate (P-21, extended by P4).
#
# Determinism is a requirement in this repository, not a nicety, so it gets an
# executable form rather than a promise:
#
#   0. every required data source is present
#   1. build everything into scratch tree A
#   2. build everything again into scratch tree B
#   3. diff A against B -- ANY difference fails
#   4. recompute the data-source hash manifest and diff it against the
#      committed figures/SOURCES.sha256 -- a source that moved under the
#      figures fails
#   5. check every declared artefact exists: N figures x 2 themes x 2 formats
#      images, plus N CSVs. N is read from build_all.py --list, so adding a
#      figure does not mean editing this script.
#   6. the committed tree matches a fresh build -- a stale committed figure
#      cannot hide behind a green determinism check
#   7. no figure script reads a path that sources.py does not declare
#   8. everything on disk that the figures are supposed to draw is reaching
#      them -- and the probe that says so is shown failing on the tree it was
#      written for
#   9. the cross-arm cost claim reconciles, four independent ways
#  10. every figure the pipeline builds is accounted for on the far end: cited
#      in the paper, or declared uncited with a reason. The figure set comes
#      from build_all.FIGURES, so a plate added tomorrow is checked tomorrow --
#      the paper's own parity gate maps exactly three figures and cannot.
#
# Runs every gate and reports all failures, rather than stopping at the first,
# except where a later gate cannot mean anything without an earlier one.

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
step "7. no figure reads an undeclared path"
# ---------------------------------------------------------------------------
# sources.py exists so that every input a figure touches lands in
# SOURCES.sha256. A bare open() in a figure script is an unhashed read: the
# figure would keep building green while its input drifted underneath it.
#
# Parsed, not grepped. The first version of this gate was a regex over the
# source text and its first finding was the phrase "never ``open()``" inside a
# docstring -- a gate whose failures are mostly false is a gate people learn to
# ignore. `ast` sees calls and not prose.
if ! "$PYTHON" -c "
import ast, pathlib, sys

BANNED_NAMES = {'open'}
BANNED_ATTRS = {
    ('os', 'walk'), ('os', 'listdir'), ('os', 'scandir'), ('os', 'remove'),
    ('shutil', 'copy'), ('glob', 'glob'), ('glob', 'iglob'),
}
# theme.save/write_csv own every write under figures/out and figures/csv, and
# they are the only place a path is opened on purpose.
hits = []
for path in sorted(pathlib.Path('.').glob('fig*.py')):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id in BANNED_NAMES:
            hits.append((path.name, node.lineno, f.id))
        elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            if (f.value.id, f.attr) in BANNED_ATTRS:
                hits.append((path.name, node.lineno, f'{f.value.id}.{f.attr}'))
for name, line, what in hits:
    print(f'{name}:{line}: calls {what}()')
sys.exit(1 if hits else 0)
" > "$SCRATCH/undeclared.txt" 2>&1; then
    fail "a figure script reaches the filesystem directly; declare it in sources.py instead:"
    sed 's/^/    /' "$SCRATCH/undeclared.txt" | head -10 >&2
else
    say "ok  (every read goes through sources.py)"
fi

# ---------------------------------------------------------------------------
step "8. coverage: everything on disk reaches the figure"
# ---------------------------------------------------------------------------
# Gates 1-7 are all satisfied by a figure that quietly omits data. P8 found two
# such omissions in a tree that was green on every one of them: two tracked
# roll-ups the figure never read, and a fourth theoria run directory nobody had
# added to the tuple. check_coverage.py walks the tree itself and asks whether
# what is on disk reached the picture.
#
# The self-test runs FIRST and is not optional. It reconstructs the pre-P8 tree
# and requires the probe to fail on it; a coverage probe that cannot be shown
# failing is a green light with nothing behind it.
if ! "$PYTHON" check_coverage.py --self-test > "$SCRATCH/coverage.selftest.txt" 2>&1; then
    fail "the coverage probe's negative control did not fire:"
    sed 's/^/    /' "$SCRATCH/coverage.selftest.txt" | head -20 >&2
else
    say "ok  (negative control fires)"
fi
if ! "$PYTHON" check_coverage.py > "$SCRATCH/coverage.txt" 2>&1; then
    fail "data on disk is not reaching the figures:"
    sed 's/^/    /' "$SCRATCH/coverage.txt" | head -20 >&2
else
    say "ok  ($(tail -n 2 "$SCRATCH/coverage.txt" | tr '\n' ' ' | sed 's/  */ /g'))"
fi

# ---------------------------------------------------------------------------
say "== 9. the cross-arm cost claim reconciles, and the check is shown refusing =="
# ---------------------------------------------------------------------------
# `cost x actions`, over the same declared sources fig02 reads, computed four
# independent ways. The negative control runs FIRST: a reconciliation that has
# never been seen to refuse cannot be read as agreement.
if "$PYTHON" reconcile_cost.py --selftest > "$SCRATCH/reconcile.selftest.txt" 2>&1; then
    say "ok  (negative control fires: planted cost and action mismatches both refused)"
else
    fail "the reconciliation's negative control did not fire:"
    sed 's/^/    /' "$SCRATCH/reconcile.selftest.txt" | head -20 >&2
fi
if "$PYTHON" reconcile_cost.py > "$SCRATCH/reconcile.txt" 2>&1; then
    say "ok  ($(grep -E '^ +(AGREE|UNCORROBORATED|DISAGREE)' "$SCRATCH/reconcile.txt" | tr -s ' ' | paste -sd' ' -))"
    grep -E "^  KNOWN DEFECT|^  STALE DECLARATION" "$SCRATCH/reconcile.txt" | sed "s/^/    /" || true
else
    fail "the arms do not agree on what a run cost or what it accomplished:"
    sed 's/^/    /' "$SCRATCH/reconcile.txt" | head -20 >&2
fi

# ---------------------------------------------------------------------------
say ""
say "== 10. every figure reaches a reader, and the check is shown refusing =="
# ---------------------------------------------------------------------------
# Gates 1-9 all pass for a plate that is built, hashed, published and read by
# nobody. The figure set is taken from build_all.FIGURES rather than a copy of
# it, so this gate grows with the pipeline instead of ageing beside it.
#
# The negative control runs FIRST and is not optional, for the same reason gate
# 8's does -- and with a sharper one here, because the gate this replaces was
# green for its whole life *because* it could not see three of the six figures.
if "$PYTHON" check_figure_citations.py --self-test > "$SCRATCH/citations.selftest.txt" 2>&1; then
    say "ok  (negative control fires: an undeclared, uncited new figure fails by name)"
else
    fail "the citation gate's negative control did not fire:"
    sed 's/^/    /' "$SCRATCH/citations.selftest.txt" | head -20 >&2
fi
if "$PYTHON" check_figure_citations.py > "$SCRATCH/citations.txt" 2>&1; then
    say "ok  ($(tail -n 2 "$SCRATCH/citations.txt" | tr '\n' ' ' | sed 's/  */ /g'))"
    grep -E "^  DECLARED" "$SCRATCH/citations.txt" | sed 's/^/    /' || true
else
    fail "a figure this pipeline builds is cited nowhere and declared nowhere:"
    sed 's/^/    /' "$SCRATCH/citations.txt" | head -20 >&2
fi

# ---------------------------------------------------------------------------
printf '\n'
if [ "$FAILED" -eq 0 ]; then
    say "VERIFY: green. Two builds byte-identical, sources unchanged, all artefacts present."
    exit 0
fi
say "VERIFY: red."
exit 1
