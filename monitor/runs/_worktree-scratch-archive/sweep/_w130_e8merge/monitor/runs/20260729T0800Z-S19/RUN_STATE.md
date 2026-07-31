# S19 — telling "asleep" from "closed", and not losing orders at the seam

Two failures with one shape: something that had stopped looked exactly like
something that was fine, and the instrument had no power to separate them.

## Part 1 — `wake_at`

A sleeping App session and a closed one produce the identical signature: a
heartbeat file that stops moving. A timestamp cannot tell them apart, because
both are "no writes since T". OPS-R slept twelve hours and was read as dropped;
a session was nearly reopened for nothing.

A session that intends to be silent for more than 45 minutes now declares when
it will be back, in the heartbeat:

```json
{"id": "RES-4", "cycle": 12, "state": "idle",
 "wake_at": "2026-07-29T08:30:00Z", "note": "sleep 900 后回到第 0 步"}
```

`_self_driving` now splits three ways instead of two. Before `wake_at`, silence
is **scheduled** and reports nothing. After `wake_at` with the heartbeat still
stale, it reports **"说好 08:30 醒，没醒"** — which is both louder and more
precise than "a bit old", because it is the session failing an appointment it
set itself.

**It is deliberately not a way to buy quiet.** Omitting `wake_at` keeps the old
45-minute staleness rule, and declaring one and overrunning it is a sharper red
than never declaring one. A test holds each of those, because the obvious way to
get this wrong is to let any `wake_at` suppress the alarm.

Contracts updated so the field is actually written: `monitor/res/RES-{1..4}.md`
and `monitor/bus/HOSTED.md`.

### The bug found next door

`_self_driving` decided its verdict by searching the *display strings* for
`"疑似停下"`. A researcher with no heartbeat file at all appended `"未启动"` and
`continue`d — no row contained the magic substring, so the probe returned
**green**. Never started and running well were the same colour. The verdict now
comes from a list of failing ids, not from grepping its own output. This is the
same family S26 is about, one directory over.

## Part 2 — instructions lost at the session boundary

`bus.py read` advanced the cursor past everything it printed. So an instruction
read by a session that then died — context exhausted, quota, closed tab — was
already behind the cursor when its successor started. It was never refused and
never answered; it stopped existing. Nothing reported it, because from the bus's
side it *had* been delivered. That is the reassuring direction again: the
delivery receipt was real, the delivery was not.

**The fix needed no new file format.** The ticket proposed changing the cursor to
hold the set of acked seqs. It turns out `out.jsonl` already records every ack
with the seq it answers — the cursor simply never consulted it. So `read` now
re-offers any instruction that requires a receipt and has none, however old,
until it is acked. No migration, and no second copy of a fact that already
exists on disk.

`notice` is excluded: it is informational, needs no receipt, and redelivering it
forever would be noise that gets the whole mechanism ignored. `order`, `urgent`
and `question` are redelivered.

### What I could not reproduce, stated plainly

The ticket says RES-1 lost three instructions today. **I could not reproduce
that.** Every one of RES-1's seven inbox messages carries an ack, as do RES-2's,
RES-3's and RES-4's. The single read-but-unacked message on the whole bus is
OPS-A's `#1`, and it is a `notice` — correctly not redelivered.

So this fix is **preventive, not a repair**: the hole is real and demonstrated by
a test that fails without it, and today it happens to be empty. Recorded this
way rather than quietly inheriting the ticket's number.

## Verification

* `python -m pytest monitor/tests -q` → all pass (2 xfail, pre-existing).
* `bash monitor/verify.sh` → **GREEN**.
* Ten new tests: six on `wake_at` (including a malformed value falling back
  rather than crashing — a liveness check that dies on bad input reports nothing
  about anybody), four on redelivery. Each red has a companion green.

## Not done

`wake_at` is honoured by `_self_driving` only. Anything else reading
`ops-status/*.json` for freshness — the sweep counts several — still sees a
stale file and no reason for it.
