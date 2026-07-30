# OPS-M cycle 22 — r3 / r4: my "the red is master's own" hypothesis is refuted. The red is correct, deliberate, and waiting on a signature only a human can give.

utc: 2026-07-30T00:20:11Z   (read from `date -u`, not typed)
author: OPS-M
re: `monitor/ci/CONFLICT-origin_agent_r3-release-classifier-defaults.md` (10 attempts),
    `monitor/ci/CONFLICT-origin_agent_r4-ruling-path.md` (8 attempts)
disposition: **needs human** (a licence signature), plus **one genuine referee-level
    trade-off for you to decide**. Nothing here is mine to land.

## I was wrong, and the control experiment is what says so

I hypothesised — twice, in cycles 20 and 22 — that r3's and r4's shared red belonged to
**master**, on the grounds that three files fail to classify with `UnicodeDecodeError`
and that reading a PDF as UTF-8 is a category error rather than a leak.

**The mechanism was right. The ownership was exactly backwards.**

Clean `origin/master` (`6f4b5e32`), release gate, all five steps of `release/verify.sh`
run separately — because my retraction earlier today was for calling one of five steps a
verdict:

| # | step | master |
|---|---|---|
| 1 | red-line negative controls (`pytest -q`) | ok (32 passed) |
| 2 | red lines clear, every tracked file read | ok — 0 credential, 0 sealed-pile, 0 unreadable over 6281 files |
| 3 | every tracked file is classified | **ok — A 5946 / B 62 / C 272 / D 1, no `?` class at all** |
| 4 | no checklist item rests on an unclassified file | ok — 0 undetermined |
| 5 | S23 before/after archive reproduces | ok |

`VERIFY: green`, exit 0 — and also green with `PYTHONPATH` unset, so the known
`gates.run()` env defect is not implicated here. **Master never abstains on those three
files.** It classifies all three as **C, releasable-flagged, on the authority of the file
extension** — which is precisely the permissive default that r3 was opened to remove.

So the red appears *only* once r3's classifier lands, and it is r3's deliberate and
correct outcome: a classifier that used to guess from the extension now abstains when the
bytes do not decode. **The three `?` files are the permissive default being caught in the
act.** My hypothesis had it as a defect in master; it is a defect master was hiding.

The `UnicodeDecodeError` details confirm exactly as I described them — byte 10 = `0xac` in
`figures/paper/{dark,light}/figure6_bill_shape.pdf`, byte 1805 = `0xa1` in
`theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt` — and my
reading that this is not a leak is confirmed from the artifacts: every ARC id involved is
**development pile**, the PDF ids are axis tick labels (`[ (ar25-0c556536) ] TJ` at a plot
coordinate), the log's id is a source constant in captured output. What is undetermined is
a **licence class, B versus C** — not a red line.

## The two flags are one finding: r4 *contains* r3

```
$ git merge-base --is-ancestor origin/agent/r3-release-classifier-defaults \
                              origin/agent/r4-ruling-path   → YES
```
r4's own `RUN_STATE.md` says so in its third line: *"Branched from
`agent/r3-release-classifier-defaults`, not from master."* Merging r3-then-r4 produces a
tree **byte-identical** to r4 alone (`git diff --stat` between the two trees is empty),
with the same red. **They do not interact, they nest.** Landing order: r3 then r4, or r4
alone, which subsumes r3. No order produces green.

That also means the board has been carrying these as two independent NEEDS-HUMAN items
for five hours when they are one decision.

## Why there is nothing for the author to fix

R4 built the adjudication path — `release/RULINGS.jsonl`, content-hash keyed, `?`-only,
stale rulings reported — and then **deliberately shipped it with zero rulings**, on the
stated ground that a ruling is a *signature*, and `monitor/CHARTER.md` routes human
identity to `needs_human` rather than to the agent whose own gate would thereby go green.
`release/runs/20260729T1835Z-R4/verify.with-demo-rulings.txt` archives the proof that
three signed lines clear it, and `RULINGS_PROPOSED.md` carries the argument *against*
signing beside each proposal.

**So the branch is complete and its red is by design.** Sending it back to its author
would be sending it back to someone who already did the right thing and documented why.
The routing worked; what is missing is a human acting on it. It has now cost 18 gate runs
across the two flags.

## Two things I measured so you can decide rather than guess

**1. Landing only ever withholds more. It never ships more.** Comparing master's
classifier against r3's and r4's over the 6281 files common to both trees, **11 files
move, all strictly away from shipped**: 3 × `C → ?` (releasable-flagged → needs_human —
the two PDFs and the pytest log) and 8 × `C → B` (releasable-flagged →
needs-written-permission: `proxy/runs/p9-shell-harden/scores_ar25_lifted.json`,
`proxy/tests/fixtures/scorecard_corpus.json`, and six `theoria-arm/runs/*/run.json` or
`MANIFEST.json`). **Zero files move toward shipped** — no `B→A`, no `B→C`, no `D→*`, no
`?→*`. r3 and r4 have identical effect on existing files; r4 differs only by its own 27
new artifacts (12 A, 15 C).

So landing does **not** trip the hard stop I set, and it strictly tightens the release.
The eight `C → B` moves are the more interesting half and nobody asked for them: eight
files that master would ship on a flagged basis need written permission once the
extension-guess is gone.

**2. The cost of landing is real and it is yours to weigh.** `release`'s gate goes **red
on master permanently**, which will hold every future branch that touches `release/`.
Blast radius is limited to `release/`: `ci_merge` runs a territory's gate only when that
territory is in `touched_dirs`, and the only references to `release/MANIFEST.jsonl`
outside `release/` (`figures/check_figure_citations.py`, three `engine-rig` files) are
docstring prose, not functional reads.

**The trade-off, stated plainly:** land it and the release is honest but `release/` is
gated shut until three lines are signed. Leave it and master keeps shipping three files
on an extension guess, while two branches re-run a ~3-minute gate every time master moves
— `verify gate red` is not in `TRANSIENT_REASONS`, and `should_hold` releases the hold
whenever the base moves, so **this recurs indefinitely; it does not converge.**

## HARD STOP observed

The smallest forward fix is three appended lines in `release/RULINGS.jsonl`. Its exact
delta, from R4's own archived demo: **3 files move from `?`/needs_human to C/releasable-
flagged — i.e. from needs_human to shipped.** That is my hard stop verbatim: a licence
signature over ARC-derived material is not a merge decision. **Not applied.**

Two alternatives were identified and also not touched, because each trips the same stop or
belongs to another territory: repairing the three mojibake byte pairs in the pytest log
(moves it toward shipped, and `theoria-arm` is not mine), and untracking or regenerating
the two PDFs in a readable form (changes what the release contains; `figures/`' call).

No `BUNDLE` and no `MANIFEST` were regenerated. The class census was taken in-process via
`enumerate.build(enumerate._tracked())` — the same entry point r3's own `snapshot.py`
uses, precisely so the distribution can be computed without writing `MANIFEST.jsonl`.

## Recommendation

1. **Treat r3+r4 as one item, not two**, and route it to the user for a signature — this
   is the `needs_human` path CHARTER already describes, and R4 built the mechanism for it.
2. If the signature is not coming soon, **decide explicitly whether to park the two
   branches** rather than let them re-run the gate every time master moves. The retries
   are not free and they carry no new information.
3. The **eight `C → B` moves** deserve a look independently of r3/r4's fate: they say
   master is currently shipping eight files on a guess. That is true today, on master,
   whether or not these branches ever land.

## Unmeasured, stated as such

* Whether master's release gate is green at the flags' literal recorded base `794e5b46`.
  The control ran at current `origin/master` `6f4b5e32`; the relevant trees were shown
  byte-identical between the two (`git diff --stat 794e5b46 origin/master -- release
  figures theoria-arm` is empty), but no worktree was built at `794e5b46` itself.
* Whether any *other* territory's gate changes verdict once r3/r4 land. Cross-territory
  references to `release/MANIFEST.jsonl` were checked and are prose only, but no other
  territory's gate was run.
