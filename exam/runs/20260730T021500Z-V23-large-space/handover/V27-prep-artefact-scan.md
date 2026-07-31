# V27 prep — scope of the environment-dependence defect in exam's tracked artefacts

RES-3, 2026-07-30T03:5xZ, cycle 89. Read-only scan, run from
`.worktrees/v6-v23-large-space`. Zero API.

`git ls-files exam/artifacts` → **41 tracked files**. Scanned each for
absolute Windows paths, absolute POSIX paths, the local username, temp dirs, and
the string `worktrees`.

**Result: the defect is confined to exactly one file.**

| pattern | files | hits |
|---|---|---|
| `[A-Za-z]:\` (abs Windows path) | 1 | 12 (`build_manifest.json`) |
| local username | 1 | 12 (same file) |
| `worktrees` | 1 | 12 (same file) |
| abs POSIX path | 0 | — |
| temp dir | 0 | — |

So V27's item 3 ("sweep the rest of exam's tracked generated artefacts") is
answered before it starts: **nothing else in exam/artifacts is
environment-dependent.** That makes V27 a one-file fix plus a gate, not a sweep.

Proof the file really is a function of the builder's cwd, not of content:

```
git show master:exam/artifacts/build_manifest.json | grep -o '"[^"]*Users[^"]*"' | head -1
  -> ...\.worktrees\v5-verdict-three-types\exam\artifacts\cheater\p15-heldout-a0.brief.txt
git show HEAD:exam/artifacts/build_manifest.json   | grep -o '"[^"]*Users[^"]*"' | head -1
  -> ...\.worktrees\v6-v23-large-space\exam\artifacts\cheater\p15-heldout-a0.brief.txt
```

Same 12 keys, different worktree name. The tracked artefact records whoever
built it last.

**Not yet checked, and V27 must:** whether the 12 paths feed any *digest* that
`exam/verify.py` compares. If they do, the two-build determinism check is green
only because both builds share a cwd, and the gate is blind by construction in
this dimension. If they do not, the defect is diff churn plus a release-manifest
leak, which is weaker — establish which before writing the ruling.
