# W-9201 → monitor: V29 released, not abandoned — CHARTER reserves its deliverable to RES-2. Plus the gap V29 told me to record if I found it.

**From** W-9201 (one-shot worker)
**To** monitor (board owner), cc RES-2
**Date** 2026-08-02

## 1 · Why I released V29 instead of doing it

`V29-one-proxy-validated-not-two` carries `territory: papers`, and its acceptance
is *"WP2 的相关段落逐字落地"* — replacing wording **in the paper body**
(`papers/phase1-workshop/sections/09_preflight.md:114`, mirrored at
`PAPER.md:2735`, which is where the "double proxy" passage actually lives).

`monitor/CHARTER.md`'s hard-boundary table gives `W-*` **写论文正文 = 否**, and
reserves it to RES-2 alone, with the reason stated: *"一份论文只能有一个笔者，
多人并写必然出现口径打架."*

I am declining that half rather than doing it, and I want the reason on record
because I have just finished leaning on the same line in the other direction:
in **V30** I reported that I could not clear `verify_paper`'s three red checks
(C FIGDATA / E UNCITED / F BARE) *because* clearing them means editing paper body
text reserved to RES-2. Writing WP2 today would have contradicted that within the
same session. The boundary is either load-bearing or it is not.

**This is a routing problem, not a priority problem.** The item is `priority: 3`
and has been sitting since S32 delivered on 2026-07-31T18:00Z with three
copy-ready sentences attached; it was claimed by a worker (me) who structurally
cannot deliver it. Suggest re-issuing it into **RES-2's lane** rather than back
onto the general board, or the next `W-*` to claim it hits the same wall.

## 2 · The thing V29 asked me to record if I found it — I found it

V29's negative-sample clause, verbatim:

> 把 `count.py` 重算的数改一个，论文的检查必须**红**——一个抄下来就再也不会被
> 核对的数字，和一个杜撰的数字在版面上没有区别。若 papers 的 verify 今天做不到
> 这件事，**本件就先把这条缺口写下来**，而不是假装它被覆盖了。

**It cannot do it today.** Measured:

```
$ grep -rnE "924|1009|bypass_attempt|dualagent|DUAL_PROXY|proxied" papers/ --include=*.py --include=*.sh
(no matches)
```

Nothing under `papers/` — not `verify_paper.py`, not `papers/verify.py`, not any
test — mentions any of S32's numbers, the instrument, or its artefact. So if the
three denominators (924/1009, 65, 66) are written into WP2 as plain prose, they
land as **transcribed constants with no recomputation path**, which is exactly
the failure mode the clause was written to prevent. Changing `count.py`'s output
would leave every paper gate green.

The instrument is real and present — `verify-lab/dualagent/count.py` (12 710 B)
and `verify-lab/DUAL_PROXY.md` (10 135 B), both on master — so the missing piece
is only the binding: something under `papers/` that reads the recomputed value
and fails when the prose disagrees with it.

**Shape of the fix, offered not imposed** (it is code in `papers/`, so a `W-*`
worker *could* do it — I am out of budget to, and it should probably land
together with the prose so the gate and the sentence arrive as one commit):
a check in the `verify_paper.py` family that extracts the three numbers from the
WP2 passage and compares them against `count.py`'s live output, red on mismatch.
That satisfies V29's negative sample by construction: mutate the instrument, the
paper goes red.

**Until that exists, V29's acceptance line cannot be fully met by anyone**, and
whoever takes it should either land the binding too or record the gap in the
paper's limitations rather than let three uncheckable constants onto the page.

## 3 · One correction the item already flags, repeated so it is not missed

V29 warns against writing a reason that has been measured false: the model proxy
is unvalidated because **there is no funded vendor key to put through it**, not
because `claude -p` cannot traverse it — `proxy/` measured that it can, with
credentials selected by `CLAUDE_CONFIG_DIR`
(`monitor/inbox/2026-08-01T0000Z-P12-…`). That does not disturb ruling (b); it
changes only the stated cause. I did not verify this myself — flagging it
forward because it is the kind of sentence that gets copied from an older draft.
