"""Apply one mutation at a time, run the test that should notice, restore.

A test that passes against a broken implementation is the failure mode this
leg keeps rediscovering, so every assertion added here has to be shown to
bite rather than assumed to. Each entry is (name, file, anchor, replacement,
test); the anchor must appear verbatim exactly once, and a mutation that fails
to apply prints SKIP rather than passing silently.

`test_check_ten_is_actually_wired_into_the_run` is never the target: it calls
the real `run()` over the real archive (>600 s; `armversion.scan()` alone is
136 s) and it pins the check's registered name, which none of these touch.

Run from `theoria-arm/`:  python runs/20260730T1400Z-A3-H3-SCOPE/mutate.py
"""
import io
import subprocess
import sys

VP = "armtools/verify_provenance.py"
BF = "armtools/backfill.py"
T = "tests/test_files_in_clone.py"

MUTS = [
    # -- first round: the repair itself --------------------------------------
    ("M1 manifest read from disk again", VP,
     'blob = backfill.blob_the_clone_ships(runs_root,\n'
     '                                             "%s/MANIFEST.json" % prefix)',
     'blob = open(os.path.join(runs_root, slug, "MANIFEST.json"), "rb").read()',
     T + "::test_check_ten_reads_the_manifest_out_of_the_commit"),
    # Two mutations on the anchor, one per convention. Pointing both at the
    # convention test let the first one SURVIVE: that test's green case is
    # root-relative, where the rewrite is the identity, so it cannot see a
    # broken run-relative rewrite at all. The rule `runs/*/trace.jsonl` is
    # written repo-root-relative and the manifest entry is `trace.jsonl`, so
    # only a test with both halves discriminates.
    ("M2a run-relative paths not rewritten", VP,
     'rewrite = (lambda p: p) if by_root else (lambda p: "%s/%s" % (prefix, p))',
     'rewrite = (lambda p: p)',
     T + "::test_check_ten_catches_a_dangling_reference"),
    ("M2b root-relative paths rewritten anyway", VP,
     'rewrite = (lambda p: p) if by_root else (lambda p: "%s/%s" % (prefix, p))',
     'rewrite = (lambda p: "%s/%s" % (prefix, p))',
     T + "::test_check_ten_holds_one_path_convention_per_manifest"),
    ("M4 index instead of commit", BF,
     '["git", "ls-tree", "-r", "-z", "HEAD"]',
     '["git", "ls-files", "-z"]',
     T + "::test_check_ten_asks_the_commit_not_the_disk"),
    ("M5 mixing never reported", VP,
     "if run_rel and root_rel:",
     "if False:",
     T + "::test_check_ten_holds_one_path_convention_per_manifest"),

    ("M3 scope back to every directory on the disk", VP,
     "    for slug in slugs:",
     "    slugs = [r['slug'] for r in survey]\n    for slug in slugs:",
     T + "::test_check_ten_scope_is_the_shipped_manifest_not_archive_material"),

    # -- second round: what the adversarial pass found ------------------------
    ("M7 malformed entries dropped in silence", VP,
     '                dangling.append("%s: a files[] record names no usable '
     'path (%r)"\n                                % (slug, entry))',
     '                pass',
     T + "::test_check_ten_reports_a_malformed_files_record_instead_of_crashing"),
    ("M8 gitlinks count as shipped", BF,
     'if meta.split(" ")[1:2] == ["blob"]:',
     'if True:',
     T + "::test_check_ten_does_not_count_a_gitlink_as_shipped"),
    ("M9 root-relative needs no directory component", VP,
     'root_rel = {p for p in rest\n'
     '                    if "/" in p and p in shipped} - run_rel',
     'root_rel = {p for p in rest if p in shipped} - run_rel',
     T + "::test_a_bare_top_level_filename_does_not_make_a_manifest_root_relative"),
    ("M10 the running depth guard", BF,
     "if depth < 0:",
     "if False:",
     T + "::test_check_ten_rejects_a_path_that_is_not_of_this_run"),
    ("M11 a staged rule file counts again", BF,
     '["git", "cat-file", "-e", "HEAD:%s" % source]',
     '["git", "ls-files", "--error-unmatch", "-z", "--", source]',
     T + "::test_a_staged_gitignore_does_not_explain_anything"),
]


def main():
    worst = 0
    for name, path, old, new, test in MUTS:
        src = io.open(path, encoding="utf-8", newline="").read()
        if src.count(old) != 1:
            print("SKIP %-42s -- anchor appears %d times"
                  % (name, src.count(old)))
            worst = 2
            continue
        io.open(path, "w", encoding="utf-8", newline="").write(
            src.replace(old, new, 1))
        try:
            rc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                 test], capture_output=True, text=True).returncode
        finally:
            io.open(path, "w", encoding="utf-8", newline="").write(src)
        print("%-46s -> %s" % (name, "BITES" if rc else "*** SURVIVES ***"))
        worst = max(worst, 0 if rc else 1)
    return worst


if __name__ == "__main__":
    sys.exit(main())
