# What this package was scanned for

A handover package is supposed to be everything its reader gets. The build scans every file in it for the four ways a working session leaks into a document it produced:

1. **a path out of the bundle** — a reference to a directory or file that is not here;
2. **a run id** — a timestamp naming one execution nobody kept;
3. **an artefact that is not here** — a log, a ledger, a status file;
4. **conversational deixis** — "as we discussed", "see above".

Those four and no more. It does **not** try to catch every prose mention of something that lives elsewhere: a generated file's own docstring may name the pipeline that produced it, and a source comment may name a component you do not have. Neither gives you a reference you need to follow — but do not read a clean scan as a promise that no sentence in here mentions anything outside it.

Two files are excluded from the scan and it matters that you know which: `MANIFEST.json`, which records on purpose where these files came from in the repository that produced them, and `SEAL.md` — this file — which quotes what the scan found and would otherwise report itself. Nothing else is excluded.

## Result

- **blocking findings: 0.** A blocking finding is a hit in text that carries meaning — a rule, a law, a rendered sentence. The build refuses to write a package with any.
- **citations: 9.** A citation is a hit inside a source comment: the author's record of *why* a clause was adjudicated the way it was. Those files are not here and you do not need them — no clause depends on one. The comments are handed over unedited because a package that rewrote the deliverable would be handing over a document nobody shipped.

## The citations, in full

| file | line | kind |
|---|---|---|
| `manual/MANUAL.dsl` | 4 | path_out_of_bundle |
| `manual/MANUAL.dsl` | 8 | path_out_of_bundle |
| `manual/MANUAL.dsl` | 8 | artefact_not_here |
| `manual/MANUAL.dsl` | 9 | path_out_of_bundle |
| `manual/MANUAL.dsl` | 51 | path_out_of_bundle |
| `manual/MANUAL.dsl` | 64 | path_out_of_bundle |
| `manual/MANUAL.dsl` | 64 | run_id |
| `manual/MANUAL.dsl` | 88 | artefact_not_here |
| `manual/MANUAL.dsl` | 131 | artefact_not_here |
