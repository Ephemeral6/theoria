# R3 — the desk refused on principle, and half the round never asked

**Offline. No ARC action, no model call, no network, no ledger. $0.00.**
Everything below is re-derived from files already committed under
`theoria-arm/runs/`.

---

## The question

R1b ran `goal_protocol=propose`. The arm proposed — 3 asks on
`20260801T001851Z-R1b-g50t-a`, 1 on `20260801T001851Z-R1b-sk48-b` — and its
mode moved from silence to `exploring_no_goal`. And then
`goal_declared_ever` stayed `False`, `plan` reported `no_goal_declared` 16
times out of 16, and no level completed. "The mechanism fired and did not
connect" is true, and it is not a diagnosis: it covers four events with four
incompatible fixes.

| | fix |
|---|---|
| (a) the desk never saw the rider | delivery |
| (b) it saw it and ignored it | the rider's wording |
| (c) it answered and the answer never reached the manual | the transport |
| (d) it answered and the parser rejected the clause | the parser |

## The answer: the two legs are (b′) and (a), and neither is (d)

**`R1b-g50t-a` — the desk saw it, engaged with it in detail, and refused on
principle, three times out of three.** The rider was delivered on 3 calls
(`desk/call-002`+`003`, `004`, `005` — the transcripts carry the prompt
verbatim and the rider's heading is in all four). Each time
`goal.answer_proposal` read the reply back as `declined_with_argument`, and
each time the manual came back carrying
`the_goal_is_absent_because_no_instance_can_name_the_socket`.

This is not (b). The desk did not talk past the ask; it answered it four
different ways and refuted each:

> (1) `Cart.pos = exit_cell` needs ONE named instance; `arc-instances: all`
> gives me `Glyph9_r8c14` and forty-two siblings and there is no instance
> called `Glyph9` … (2) A count over the socket interior has nothing to range
> over: those cells have never changed, so they are board and carry no
> instances. (3) Counts over the four types I do have are all either true in
> some observed state … or false everywhere and unreachable … which is exactly
> the fake goal the rider warns is worse than none. (4) The goal cannot be
> conjunctive; the section takes one equation.

It also priced its own position in the arm's own numbers — `is_goal` compiles
to `False`, `plan` returns `no_goal_declared`, all eighteen commands have been
probes — and named the observation that would end it: *any pixel of the
bracket, the pip, or the comb changing colour.*

**`R1b-sk48-b` — the ask was booked and never posted.** The criterion fired on
turn 1. The rider parks for the next theorize call a surprise pays for; turns
2–4 skipped theorize under the new-transitions gate, the beat after that lost
**all five** of its replies in transit, and the leg then hit its spend
reservation at $17.39 of $29. The ask sat on the peg for the whole leg. The
record said `"answered": null`, which is true and which every later summary
read as *the desk gave no answer* — when the desk was never asked.

`armtools/goal_forensics.py` re-derives both, per leg, from tracked files:

```
20260801T001851Z-R1b-g50t-a   declined_with_argument  booked 3, answers x3
20260801T001851Z-R1b-sk48-b   booked_never_delivered  booked 1, answers []
```

## The thing nobody was looking for: 28.6% of the desk bill was thrown away

`inner/theorize.py` writes one error for a reply it cannot use: `no THEORY
block in the reply`. It has written that sentence 32 times, and it names three
unrelated events. Reading the transcripts separates them:

| class | calls | what it is |
|---|---|---|
| `well_formed` | 53 | begins with `=== THEORY ===` |
| `provider_refusal` | 24 | `You've hit your session limit` — the desk never ran |
| `empty` | 1 | nothing came back |
| **`lost_continuation`** | **11** | **the answer was there and only its end was kept** |

`harness/modelcall.py:561` reads `envelope["result"]`, which is the CLI's
**last assistant message**. When a reply spans more than one message the
earlier ones are dropped. What lands on disk is a tail:
`R1b-sk48-b/desk/call-002` begins mid-header at

> `=== THEORY (continued -- the remainder of theory.dsl, appended to the block above) ===`

and `call-006` of the same leg begins mid-word, at `ditional repaint of the
four mark cells`.

Those 11 calls were billed in full: **$31.05 of a $108.54 lifetime desk bill,
28.6%.** On R1b alone the loss was **$19.70 of $35.14 — 56% of the round**,
including $14.03 of `sk48-b`'s $17.39, which is *why* that leg had no theorize
call left to carry the goal ask before its reservation ran out.

**The discriminator is structural, not arithmetic**, and the difference
matters. Output tokens against reply characters looks like the obvious test and
does not work: `claude -p` bills thinking tokens that never reach `result`, so
the ratio sits below 1.0 on 39 of 88 archived calls, most of which parsed
perfectly. What does work is exact: **all 53 replies the arm accepted begin
with `=== THEORY ===`, and none of the 35 it rejected do.**

## Does the rider engage the desk's argument, or talk past it?

**Half and half, and the half it misses is the half the desk actually made.**

The rider engages *soundness* — "it must be false in the states you have
already seen — a goal satisfied by the current board stops the planner at the
first node and is worse than no goal at all." That is the manuals' own
argument, agreed with in their own terms. The desk quotes it back approvingly.

The rider never engages *reach*. Every one of the three refusals is a
demonstration that the goal section **cannot say the thing**: `goal Cart.pos =
<landmark>` and `goal count(<Type>, color = c) = n`, `=` only, one equation, no
conjunction. The position the desk believes wins is a 5×5 body seated in a
socket whose cells have never changed — board cells, on which `arc-instances:
all` seats nothing, which no `count` ranges over and no landmark names.

That is the same wall `20260801T0900Z-R2-frontier-by-generation` measured from
the other side, without either finding knowing about the other: **12 of 47
off-frontier probes missed by a delta containing exactly one
never-before-changed cell.** Probe expressivity and goal expressivity are one
defect seen twice.

Offered only "write one" or "argue why not", the desk smuggled its actual
target into prose of its own naming —
`the_socket_is_a_keyhole_and_names_the_winning_position`, verified cell by cell
against the frame — where nothing in the arm reads it. **The single most
valuable claim either manual made was written down and never picked up.**

So the rider grows a third channel: *if you decline because the section cannot
SAY it, name the target under `the_goal_i_cannot_write_is_...` and say which
forms you tried and what each lacked.* It buys no model call — same rider,
same already-paid-for turn.

## How a prompt change is judged without a live leg

`Theoria.md:355` lists the prompt as movable; it does not say a prompt change
is free to assert its own effect. This one cannot be judged for effect offline
and is not claimed to be. What **is** settled offline:

1. **It cannot ask for a form the compiler refuses.** The rider ships in the
   same prompt as the grammar card; the third channel asks for a `theorem`,
   which is the DSL's own home for a belief that is not an equation.
2. **Its base rate is measured, not guessed.** The desk produced exactly this
   artefact unprompted on 2 of 2 legs that got that far. The change asks for
   something already observed, under a name that can be found.
3. **The reading half pays off regardless.** `extract_target_theorems` is a
   fixture-tested parser, and it correctly returns `[]` on both R1b manuals —
   which name their targets under names of their own choosing. Whether or not
   the desk ever adopts the prefix, the arm's record now distinguishes
   *refused*, *not asked*, and *asked and lost*, which it could not on
   2026-08-01.
4. **What it would take, and what it would cost.** One carried leg on
   `g50t-5849a774` from the r3 seed books, `--goal-protocol=propose`, leg
   ceiling $25. R1b's two legs cost $35.14 and both stopped on the spend gate;
   a single leg at the same shape is **$17–25, ~9 desk calls, ~25 ARC
   actions**. It would settle exactly one thing: whether a desk given a place
   to put its target uses it. It would **not** settle whether a goal becomes
   writable — that is the grammar, and it belongs to `theory-compiler`.
   **No such leg was run. This programme is over its ceiling and this session
   had zero spend authority.**

## Order of work, if the round is repeated

1. **The transport, first and alone.** 28.6% of every desk dollar this arm has
   spent bought an answer nobody read. Until that is fixed, no A/B on any knob
   means anything: `sk48-b` lost 5 of 6 replies and would have "failed" any
   change whatsoever.
2. **Then the rider's third channel**, which is cheap and whose reading half is
   already in the record.
3. **The goal grammar last, and not here.** Both the goal refusal and R2's 12
   expressivity misses are the same missing thing: no way to name a cell the
   board explains. That is `theory-compiler`'s and goes through
   `monitor/inbox/`.

## Reproduce

```bash
cd theoria-arm
python -m pytest -q tests/test_reply_loss.py tests/test_goal_forensics.py
python -m armtools.replyloss
python -m armtools.goal_forensics
cd runs/20260801T1200Z-R3-the-desk-refused-on-principle && python measure.py
python make_manifest.py
```

## Sealed pile

None. Development-pile games only (`g50t-5849a774`, `sk48-d8078629`), and both
only as already-archived records — no game was played, opened, or inspected.
