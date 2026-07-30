import subprocess, sys, io

VP = "armtools/verify_provenance.py"
BF = "armtools/backfill.py"

MUTS = [
 ("M1 manifest read from disk again", VP,
  'blob = backfill.blob_the_clone_ships(runs_root,\n                                             "%s/MANIFEST.json" % prefix)',
  'blob = open(os.path.join(run_dir, "MANIFEST.json"), "rb").read()',
  "tests/test_files_in_clone.py::test_check_ten_reads_the_manifest_out_of_the_commit"),
 ("M2 anchor always the run dir", VP,
  "anchor = top if by_root else run_dir",
  "anchor = run_dir",
  "tests/test_files_in_clone.py::test_check_ten_holds_one_path_convention_per_manifest"),
 ("M3 scope filter removed", VP,
  '        if "%s/MANIFEST.json" % prefix not in shipped:\n            continue',
  '        if False:\n            continue',
  "tests/test_files_in_clone.py::test_check_ten_scope_is_the_shipped_manifest_not_archive_material"),
 ("M4 index instead of commit", BF,
  '["git", "ls-tree", "-r", "--name-only", "-z",\n                               "HEAD"]',
  '["git", "ls-files", "-z"]',
  "tests/test_files_in_clone.py::test_check_ten_asks_the_commit_not_the_disk"),
 ("M5 mixing never reported", VP,
  "if run_rel and root_rel:",
  "if False:",
  "tests/test_files_in_clone.py::test_check_ten_holds_one_path_convention_per_manifest"),
]

for name, path, old, new, test in MUTS:
    src = io.open(path, encoding="utf-8", newline="").read()
    if old not in src:
        print("SKIP %-40s -- anchor text not found" % name); continue
    io.open(path, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    try:
        rc = subprocess.run([sys.executable, "-m", "pytest", "-q", test],
                            capture_output=True, text=True).returncode
    finally:
        io.open(path, "w", encoding="utf-8", newline="").write(src)
    print("%-40s -> %s" % (name, "BITES (test failed)" if rc else "*** SURVIVES ***"))
