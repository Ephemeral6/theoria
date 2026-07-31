# Why these four files moved here

They were written in `monitor/res/RES-3-notes/` by three RES-3 sessions across
cycles 72–107. On 2026-07-30, cycle 107, `git log --all --oneline -- <path>`
returned **zero commits for all four**: they existed only as untracked files in
one machine's working tree, on one branch, in one worktree.

That matters because two of them are **cited by published documents**:

* the board item `V27-V27-manifest-absolute-paths` says its step-3 artefact scan
  is recorded in `monitor/res/RES-3-notes/V27-prep-artefact-scan.md`, and tells
  whoever picks the ticket up not to redo the scan;
* this run's `RUN_STATE.md` credits its opening recon to
  `monitor/res/RES-3-notes/`.

So a ticket on the board and a run document both point at evidence that is in no
commit on any ref. This is the same defect commit `98091f99` measured for
`monitor/inbox/` — 94 of the fleet's 229 proposals in no commit while documents
cited them as filed — recurring one directory over, and it is worse here because
the citation is an instruction to *skip work* on the strength of a file the
reader cannot open.

Their subject is `exam` (V2-V25, V27 and V28 are all exam tickets, and the
fourth is this run's own recon), so they are tracked here, inside the run
directory that produced most of them, covered by `MANIFEST.json` and by
`exam/tests/test_run_manifest_v23.py`. The copies under
`monitor/res/RES-3-notes/` are left in place and are now the stale ones: `monitor`
is another agent's territory this cycle, so removing them is not mine to do.
Anyone following the V27 item's citation should read the copy here.

Nothing in their content changed in the move except CRLF normalisation, which is
what `exam/.gitattributes` requires and what cycle 107 found four files had
quietly violated.
