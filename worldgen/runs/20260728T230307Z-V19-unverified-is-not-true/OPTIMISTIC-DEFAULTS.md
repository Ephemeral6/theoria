# V19 item 4 — every default that points at the good news, judged

The work order says to sweep the same file for other `.get(..., True)` /
`.get(..., 0)` shapes, on the principle that **a default pointing at the good
news is a candidate for this disease**. The sweep below covers all of
`worldgen/`, not only `core/truth.py`, because the shape is not confined to a
file and the neighbouring hit turned out to be in `build.py`.

## The judging criterion

Not every default is this disease. The distinguishing question is:

> **Does this default feed a verdict?**

An accumulator default (`counts.get(k, 0) + 1`) starts a tally. A deserialiser
default (`blob.get("colors", {})`) makes a document loadable. Neither decides
whether something passed. The disease is a default that **supplies a missing
measurement and supplies it as a passing one** — because the caller then cannot
distinguish "we checked and it was fine" from "we never checked".

A second, sharper test applies to this repository specifically: **does the
machine-read field end up more optimistic than the Markdown rendered beside
it?** That asymmetry is what made the original defect survive review — a human
auditing `GROUND_TRUTH.md` saw `unverified` and had no reason to suspect the
JSON said otherwise.

## Sweep, with verdicts

Ordered defect-first.

### 1. `core/truth.py:279` (pre-fix) — `all(i.get("holds", True) for i in invariants)`

**DEFECT. The cell itself.** Fixed: three-class partition, `classify_invariants`
/ `all_invariants_hold`, plus a separate `invariant_unverified` build gate.

### 2. `build.py:244` (pre-fix) — `for world_id in totals.get(key, ()):`

**DEFECT, and the most interesting find of the sweep.** `gate_failures` iterated
`totals.get(key, ())`, so a manifest that simply **did not carry a gate's key at
all** cleared that gate in silence. Identical shape to the cell's own defect —
a missing measurement defaulting to the good news — sitting one function away
from where the bad value was consumed.

Reachability today is nil: `build_all` and `build_mutants` both emit every key.
That is the argument *for* the check rather than against it. This territory's
last two findings were both "the measurement is computed and nothing exits on
it" (`gate_failures` before C1's audit, `check_determinism` before V16); a gate
that silently skips when its input is absent is the same failure with an extra
step. `test_build_gate.py::test_the_shipped_catalogue_passes_its_own_gate`
checks the *shipped* manifest has the keys, and by construction cannot see a
manifest built anywhere else.

Fixed: a missing key emits `gate could not be evaluated ... an unevaluated gate
is not a passed one` and fails the build. New test, parametrised over every gate
key: `test_a_missing_gate_key_is_a_failure_not_a_pass`.

### 3. `core/truth.py:437` (pre-fix) — `if corr and not corr.get("agrees", True):`

**DEFECT, same file, same shape, opposite half of the artefact.** A `truth` dict
whose `rule_correspondence` block is absent, or present without its `agrees`
verdict, rendered a `GROUND_TRUTH.md` with **no** disagreement warning — i.e.
the page read as agreement. Compounded by `truth.get("rule_correspondence", {})`
on line 412, which turns an absent block into a falsy dict the `if corr` guard
then skips entirely.

This one is worth noting for its direction: it is the *Markdown* being more
optimistic than reality, which is the mirror of the defect the cell is named
for. The reason it matters is the same. The Markdown is what a human audits.

Fixed: an unmeasured or verdict-less correspondence now renders
**"Rule correspondence was not measured for this world, so nothing below should
be read as agreement."** Two tests pin it, plus one pinning that a *measured*
agreement still renders clean — a caveat printed on every page is a caveat
nobody reads.

### 4. `mutate.py:1143` (pre-fix) — `row.get("verified") and not row.get("holds", True)`

**DEFECT IN SHAPE, DEAD IN VALUE — removed anyway; a real semantic gap behind it
left in place deliberately.**

The `.get("holds", True)` default is unreachable: it sits behind a
`row.get("verified")` guard, and a verified row always carries `holds`. So it
changed no value, before or after. It is the V19 idiom verbatim, though, and
leaving one copy in the tree invites the next reader to copy the idiom rather
than the reasoning. Rewritten to read `status` explicitly via
`truth.classify_invariants`. Value identical — confirmed: `claims_now_false` is
byte-identical for all fifteen mutants in `MUTATIONS.json`.

**The gap it was hiding is real and is NOT fixed here.** `claims_now_false`
counts violations only, so a mutation that turns a *verified* invariant into an
*unverified* one is invisible to it. Closing that means adding a
`claims_now_unverified` sibling to `MUTATIONS.json`, and `claims_now_false` is
read by name from `exam/grading/rubrics_adaptation.py:495,504` and
`exam/papers/adaptation.py:790,958,1019` — another track's territory, and a
schema change there is theirs to accept. Recorded rather than done, with the
reason in a comment at the call site.

### 5–8. Judged legitimate

| site | shape | verdict |
|---|---|---|
| `core/explorer.py:116,122` | `witnessed.get(rule, 0) + 1` | **Legitimate.** Accumulator idiom; the default starts a tally, it does not answer a question. |
| `mutate.py:1005` | `moves.get(rule, False) or (...)` | **Legitimate.** Accumulating an OR, and `False` is the *pessimistic* side of it. |
| `core/truth.py:425` | `corr.get("cascade", ())` | **Legitimate, and correctly signed.** A missing cascade set makes rules render as `**never fires**` — it defaults toward the alarm, not away from it. |
| `core/spec.py:156–162` | `blob.get("entities", ())`, `blob.get("colors", {})`, `blob.get("families", ())`, `int(blob.get("seed", 0))` | **Legitimate, with a note.** Lenient deserialisation of this module's own output; every field is always written by `dumps`. None feeds a pass/fail judgement, which is the criterion. `seed` is the one worth watching: determinism is a stated requirement and a missing seed becoming `0` is silent — but it is silent about an *input*, not about a verdict, so it is out of this cell's scope rather than absolved by it. |
| `qc/run_qc.py:111–112,270–271` | `l12.get("l1_pass")`, `mining[...].get(mover)` — no default, so missing → `None` → falsy | **Legitimate and correctly signed.** A missing measurement reads as *not passed*. This is the shape the rest of the tree should look like. |
| `qc/engine_manual.py:112,127,137` | `states.get(tid)`, `.get((track, action), [])`, `.get(tid, TrackState(None, None))` | **Legitimate.** Lookup defaults in a decoder; no verdict downstream. |
| `qc/run_qc.py:404` | `MUTANT_BASE.get(variant_id)` | **Legitimate.** `None` is handled explicitly by the caller. |
| `tests/test_mutate.py:452` | `(fast["actions"] or 0) + 1` | **Legitimate.** Bound arithmetic inside a brute-force cross-check. |

### Shapes swept and found clean

`or []` / `or ()` / `or {}` / `or True` outside the one site above: none in
`worldgen/`. `getattr(..., default)`: none. `prop(name, default)` in
`mechanisms/`: every occurrence supplies a *domain* default (`mode="toggle"`,
`net="a"`, `k=3`, `polarity="open_when_on"`) and none of them stands in for a
measurement — `count_lock.py:60–63` even documents the reasoning explicitly
("a default of 0 would make a mis-specified lock silently open, which is the
worse failure"), which is this cell's criterion, arrived at independently and
several months earlier.

## Summary

Eight sites carry a default that could point at good news. **Four are defects
(1–4); three of those were repaired here and one was repaired in shape with its
semantic half deferred to the track that owns the consumer.** The rest are
accumulators, decoders, or defaults that already point at the alarm.
