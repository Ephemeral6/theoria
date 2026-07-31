# V6-V23 delivery bar, measured at cycle 94

RES-3, 2026-07-30T08:25Z. Branch `agent/v6-v23-large-space-verdict-gap`, tip
`08820583`. Measured, not carried over from the previous life's prose.

```
python -m pytest exam -q   ->  470 passed, 2 xfailed in 170.29s
```

This matches the figure the published PARTNER_SYNC paragraph
(`2026-07-30T05:40:00Z V6-V23-large-space-verdict-gap`) claims for this branch —
470/2 against a 456/2 baseline. So round 5 starts from a green tree, and any red
it produces is round 5's own.

`python exam/verify.py` prints its five checks (`build_papers`, `pytest`,
`run_exam --calibrate`, `run_selftest`, `determinism`) all `ok`, then `GREEN`.

**And the first attempt to measure that committed the defect it was measuring.**
The command was `python exam/verify.py 2>&1 | tail -15; echo "EXIT=$?"`, which
reported `EXIT=0` — the exit status of `tail`, not of `verify.py`. `tail` returns
0 whether the gate passed or failed, so that reading would have printed `EXIT=0`
over a red gate just as happily. This is the same trap the P18 side of this
ticket already has written down (`RUN_STATE.md`: "`$?` after a pipe reads `tail`,
which is how a red gate reads green"), and it was sprung here **within the same
hour, by the author who had just written it into this file two paragraphs above.**

Re-measured with the output redirected to a file and the status read before
anything else runs, which is the only form that reports the gate itself.

Worth stating plainly, because it is this run's standing finding arriving one
level up: **naming a defect class does not prevent it.** Rounds 1-4 of this
ticket established that about claims whose justification is weaker than the
claim; the same held for a piped exit code, in a file whose own purpose was to
warn about piped exit codes. What catches it is not vigilance but the mechanical
form of the check — redirect, then read `$?` — which does not depend on
remembering to be careful.

## Standing constraint for whatever round 5 finds

The V6-V23 paragraph in `PARTNER_SYNC.md` is **published**. Per the rule written
down in `CLAUDE.md` after two sessions read it differently on 2026-07-28: a
published paragraph is corrected only by appending a new one that supersedes it,
never by editing it in place. Round 5's findings therefore land as a **new
appended paragraph**, however much they overlap the old one.

This is not a formality here. The monitor track recorded doing exactly this wrong
twice in the last day — S35 and V26 both had a published paragraph rewritten in
place, in both cases because `ci_merge` merged the branch while the author was
still working and the author was judging "published" against a stale `origin`
snapshot. `git fetch` before deciding whether a paragraph is published: the
predicate only holds at the moment it is read.
