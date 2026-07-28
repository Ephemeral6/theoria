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
#   9. every publication artefact exists: one per paper figure x 2 themes x 3
#      formats, plus the index and one caption each
#  10. the publication SVG is byte-identical to the screen SVG of the same
#      plate -- "the paper shows the figure the pipeline built", checked
#  11. the index's digests match the files on disk, and the paper numbering is
#      1..N with no gaps
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
        FIGURES_PAPER="$SCRATCH/A/paper" "$PYTHON" build_all.py > "$SCRATCH/A.log" 2>&1; then
    cat "$SCRATCH/A.log" >&2
    fail "build pass A did not complete"
    exit 1
fi
say "ok  ($(grep -c '  img  ' "$SCRATCH/A.log") images)"

# ---------------------------------------------------------------------------
step "2. build pass B"
# ---------------------------------------------------------------------------
if ! FIGURES_OUT="$SCRATCH/B/out" FIGURES_CSV="$SCRATCH/B/csv" FIGURES_SHA="$SCRATCH/B/SOURCES.sha256" \
        FIGURES_PAPER="$SCRATCH/B/paper" "$PYTHON" build_all.py > "$SCRATCH/B.log" 2>&1; then
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
for leaf in csv out paper SOURCES.sha256; do
    if [ -e "$SCRATCH/A/$leaf" ] || [ -e "$SCRATCH/B/$leaf" ]; then
        if ! diff -r "$SCRATCH/A/$leaf" "$SCRATCH/B/$leaf" > "$SCRATCH/diff.$(basename "$leaf").txt" 2>&1; then
            fail "pass A and pass B differ under '$leaf':"
            sed 's/^/    /' "$SCRATCH/diff.$(basename "$leaf").txt" | head -40 >&2
        fi
    fi
done
[ "$FAILED" -eq 0 ] && say "ok  (csv, out, paper, SOURCES.sha256 all identical)"

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
for leaf in csv out paper; do
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
step "9. every publication artefact exists"
# ---------------------------------------------------------------------------
# The expected roster is written as LITERALS here, not read from paper_map.py.
# That is the house rule this pipeline learned the hard way (PLAN.md section 10):
# a probe that takes its expectations from the module it audits can only prove
# that module self-consistent, and P8's coverage probe stayed green over the
# exact defect it was written for by doing precisely this. Deleting a figure
# from paper_map.py must turn this gate red, not shrink it.
PAPER_FIGS=(
    "figure1_concept_timeline"
    "figure2_a0_vs_a0prime"
    "figure3_a2_repair_loop"
    "figure4_a3_transfer"
    "figure5_capability_spectrum"
    "figure6_bill_shape"
)
PUB_N=0
for name in "${PAPER_FIGS[@]}"; do
    for th in light dark; do
        for fmt in pdf png svg; do
            PUB_N=$((PUB_N + 1))
            p="$SCRATCH/A/paper/$th/$name.$fmt"
            [ -s "$p" ] || fail "missing or empty publication artefact: paper/$th/$name.$fmt"
        done
    done
done
for n in 1 2 3 4 5 6; do
    [ -s "$SCRATCH/A/paper/captions/figure$n.md" ] || fail "missing caption: paper/captions/figure$n.md"
done
[ -s "$SCRATCH/A/paper/INDEX.md" ]   || fail "missing paper/INDEX.md"
[ -s "$SCRATCH/A/paper/index.json" ] || fail "missing paper/index.json"
say "checked ${#PAPER_FIGS[@]} paper figures -> $PUB_N artefacts + 6 captions + index"

# ---------------------------------------------------------------------------
step "10. the paper's SVG is the plate the pipeline built"
# ---------------------------------------------------------------------------
# Both profiles are written from the same in-memory Figure, so the vector output
# must be identical byte for byte. Checking it is what makes that claim worth
# anything: if the two ever diverge, the paper is showing something the CSV
# audit layer does not describe. The pairing is spelled out rather than derived,
# for the same reason as gate 9.
check_pair() {  # <pipeline-slug> <paper-slug>
    for th in light dark; do
        a="$SCRATCH/A/out/$th/$1.svg"
        b="$SCRATCH/A/paper/$th/$2.svg"
        if ! cmp -s "$a" "$b"; then
            fail "paper/$th/$2.svg differs from out/$th/$1.svg -- the two profiles have diverged"
        fi
    done
}
check_pair fig06_concept_timeline     figure1_concept_timeline
check_pair fig07_a0_vs_a0prime        figure2_a0_vs_a0prime
check_pair fig05_a2_repair_loop       figure3_a2_repair_loop
check_pair fig04_a3_transfer          figure4_a3_transfer
check_pair fig03_capability_spectrum  figure5_capability_spectrum
check_pair fig02_bill_shape           figure6_bill_shape
[ "$FAILED" -eq 0 ] && say "ok  (6 plates x 2 themes, screen SVG == paper SVG)"

# ---------------------------------------------------------------------------
step "11. the index's digests match the files on disk"
# ---------------------------------------------------------------------------
# An index is a promise about bytes. This recomputes every digest it claims --
# for the data sources, the CSVs and the artefacts -- against the tree that build
# actually wrote, independently of paper_index.py's own hashing. (A *committed*
# index that someone hand-edited is caught one gate earlier, by gate 6's diff
# against a fresh build; this gate is about the fresh build being self-true.)
#
# It also checks the paper numbering is 1..N contiguous with N = 6 stated as a
# literal: "Figure 5" with no Figure 4 is a broken document, and it is exactly
# the state a careless edit to paper_map.py leaves. Shown failing: deleting
# Figure 6 from the registry turns gates 9, 10 and 11 red -- separately -- rather
# than shrinking any of them.
if ! "$PYTHON" - "$SCRATCH/A" <<'PY' > "$SCRATCH/index.txt" 2>&1; then
import hashlib, json, os, sys

scratch = sys.argv[1]
repo = os.path.dirname(os.getcwd())  # verify.sh cd's to figures/; repo is its parent
index = json.load(open(os.path.join(scratch, "paper", "index.json"), encoding="utf-8"))

def digest(abs_path):
    h = hashlib.sha256()
    with open(abs_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def resolve(canonical):
    """A canonical 'figures/...' path, in the scratch tree this build wrote."""
    rest = canonical.split("/", 1)[1]
    top = rest.split("/", 1)[0]
    if top in ("paper", "out", "csv"):
        return os.path.join(scratch, *rest.split("/"))
    return os.path.join(repo, *canonical.split("/"))

bad = []
numbers = []
for rec in index["figures"]:
    numbers.append(rec["number"])
    checked = [("csv", rec["csv"]["path"], rec["csv"]["sha256"])]
    for art in rec["artifacts"] + rec["screen_artifacts"]:
        checked.append(("artifact", art["path"], art["sha256"]))
    for src in rec["sources"]:
        checked.append(("source", src["path"], src["sha256"]))
    for kind, path, claimed in checked:
        abs_path = resolve(path) if path.startswith("figures/") else os.path.join(repo, *path.split("/"))
        if claimed is None:
            if os.path.isfile(abs_path):
                bad.append(f"{rec['cite']}: {kind} {path} recorded ABSENT but is on disk")
            continue
        if not os.path.isfile(abs_path):
            bad.append(f"{rec['cite']}: {kind} {path} claimed sha256 but is not on disk")
            continue
        actual = digest(abs_path)
        if actual != claimed:
            bad.append(f"{rec['cite']}: {kind} {path}\n    index {claimed}\n    disk  {actual}")

if sorted(numbers) != list(range(1, len(numbers) + 1)):
    bad.append(f"paper figure numbers are not 1..{len(numbers)} contiguous: {sorted(numbers)}")
if len(numbers) != 6:
    bad.append(f"expected 6 paper figures, index declares {len(numbers)}")

for line in bad:
    print(line)
print(f"checked {len(index['figures'])} figures")
sys.exit(1 if bad else 0)
PY
    fail "the paper index disagrees with the tree:"
    sed 's/^/    /' "$SCRATCH/index.txt" | head -20 >&2
else
    say "ok  ($(tail -n 1 "$SCRATCH/index.txt"), every digest recomputed)"
fi

# ---------------------------------------------------------------------------
printf '\n'
if [ "$FAILED" -eq 0 ]; then
    say "VERIFY: green. Two builds byte-identical, sources unchanged, all artefacts present."
    exit 0
fi
say "VERIFY: red."
exit 1
