# R3, round two — what the adversarial review moved

`prompt_id: R3-release-classifier-defaults`, branch
`agent/r3-release-classifier-defaults`. Round 1's census is `DISTRIBUTION.md`
beside this file and is **not** superseded as a measurement — it is superseded as
a *description of the branch*, for the reason set out at the bottom.

This census measures **only what round 2 changed**. Both files enumerate the
**same tree** (5,992 tracked files); the only difference is which
`release/enumerate.py` classified it — round 1's (commit `3ef99920`) or round 2's.
That is the honest way to attribute a move, and it is why the file counts here do
not match round 1's 5,980: the tree grew by the run artefacts of round 1 itself.

## The numbers

| class | verdict | round-1 code | round-2 code | Δ |
|---|---|---:|---:|---:|
| A | releasable | 5676 | 5676 | 0 |
| B | needs-written-permission | 61 | **69** | **+8** |
| C | releasable-flagged | 251 | **243** | **−8** |
| D | not-releasable | 1 | 1 | 0 |
| ? | needs_human | 3 | 3 | 0 |
| | **total** | 5992 | 5992 | |

**Nothing moved in the permissive direction.** Every move is C → B: out of
*releasable-flagged* and into *needs written permission*.

## The eight, and what they actually are

`MOVED.round2.tsv` lists them with their post-move evidence. 159,153 bytes.

```
proxy/runs/p9-shell-harden/scores_ar25_lifted.json
proxy/tests/fixtures/scorecard_corpus.json
theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json
theoria-arm/runs/20260728T015354Z-g50t-first-contact/run.json
theoria-arm/runs/20260728T235841Z-leg01/run.json
theoria-arm/runs/20260728T235842Z-leg02/run.json
theoria-arm/runs/20260728T235843Z-leg01/run.json
theoria-arm/runs/a3-gate-mock/run.json
```

These are **ARC scorecard response bodies** — `card_id`, `environments[].id`,
per-run `guid`s. Every one of them was shipping as `releasable-flagged` under the
positive sentence *"no record pairs an id with environment payload — statistics
about the games, not material from them."*

They moved because `enumerate.PAYLOAD_KEYS` was a four-field literal
(`frame, frames, action_input, available_actions`) sitting beside the
`check_redlines` constant that **this same branch** had just widened to eight.
`scorecard` is one of the four that were missing, and `enumerate.py`'s own module
docstring had already named a scorecard body as class-B payload — only the
literal disagreed. The fix reproduced its own diagnosis one level up: the guard
went into one of the two readers.

`PAYLOAD_KEYS` is now `redlines.PAYLOAD_FIELDS`. Derived, never re-typed.

## Why it is eight and not eleven

The reviewer measured **11** files that the wider field list alone would move.
Three of them stayed class C, and that is the second round-2 change working:
`_records_pairing` used to test record-level co-occurrence — *is any named id
anywhere in this record's JSON, and is any payload field anywhere beneath it* —
which `check_redlines._pairings` had been rewritten on this same branch to stop
doing, with the reason written down: a whole-document `.json` parses as exactly
**one** record, at which point "record by record" degrades into "somewhere in
this file". The three that stayed are that shape, an id four levels away from an
unrelated `state` field.

So the two changes are not additive; they cut in opposite directions, and both
are needed. Widening the list without tightening the scope would have produced
three false class-B rows.

What is deliberately **not** shared between the two modules is the *fill* test.
`redlines._filled` counts `False` and a prose string as present, because
`"full_reset": false` is a real command sent to a real game and the sealed red
line must see it. `enumerate._is_payload` requires a non-empty list or dict,
because `battery/artifacts/capability_spectrum.json` carries a `frame` field
holding a *sampling* frame described in prose, and withholding the artefact the
paper's capability claim rests on because a statistician and an environment
designer chose the same English word is not a licence judgement. Two questions,
two answers — now written down rather than drifting.

## Three evidence strings that were false, corrected

No file changed class here, which is exactly why it is worth recording. The
three `?` rows used to carry a reason nobody had checked:

| | |
|---|---|
| **before** | `… but could not be parsed as JSON, so whether it carries environment payload is undetermined` |
| **after** | `… but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa1 in position 1805: invalid start byte, so …` |

Nothing was ever handed to a JSON parser. All three take `json_shaped`'s *first*
early return, `blob.decode("utf-8-sig")`. `pytest-baseline.txt` holds 45
non-empty lines of which **zero** begin with `{`; its entire defect is three
mojibake byte pairs, one inside a quoted Python comment. A gate that misnames its
own reason gets cleared by someone fixing the wrong thing — which is the disease
this work order is about, so it does not get to have it.

## The blind scan, which moved nothing and is the most dangerous of the three

`unsearchable_encoding` was wired into `check_redlines`'s two scans and into
nothing in `enumerate.py` — the same function, three lines from the id search.
Five records of `{"game_id": "<dev-pile id>", "frame": [[1,2],[3,4]]}` written as
UTF-16 classified as **A / releasable**, on the evidence *"no ARC game id appears
in this file"* — this work order's title sentence, printed over a comparison that
could not see the text.

It moves zero files on this tree because this tree holds no wide-encoded file.
That is precisely why it needed a negative sample rather than a census row, and
it has one; `?` is now the answer, and the API-transaction scan stays *above* the
guard, because a marker that matched is a positive finding and blindness cannot
make a match false.

## Gate and tests

* `bash release/verify.sh` → **`VERIFY: RED`** (`verify.round2.txt`). Four of five
  sections green; the failure is *"every tracked file is classified"*, the same
  three `?` rows, now naming the real reason.
* `python -m pytest release/tests -q` → **71 passed** (`pytest.round2.txt`), from
  57 after round 1 and 46 at base. **10 of the 14 added in round 2 fail on the
  unfixed tree**; the other 4 are positive controls that must pass both before
  and after — a gate that reddens at everything proves nothing either.

## What this supersedes, and what it does not

`MANIFEST.json` and `DISTRIBUTION.md` in this directory were written at
2026-07-29T16:12:45Z by the enumerate half of round 1, and both say *"defect 2
was not in this work order and was not looked at."* **That is false of the
branch**: `release/check_redlines.py` carries the defect-2 fix, and that
manifest's own `code_under_measurement` entry is the sha256 of the **fixed**
file — the record contradicts itself, checkable against its own hash.

Neither file is edited. `MANIFEST.json` records `DISTRIBUTION.md`'s sha256, and a
provenance record that can be quietly rewritten after the fact is worth less than
one corrected in the open. Their *numbers* still reproduce exactly; what was
wrong was the provenance they claimed for them. `ADVERSARIAL.md` findings 13 and
14 are the full account.

`release/MANIFEST.jsonl` is still **not** regenerated, for the reason round 1
gave: it is stale by ~4,000 rows against the tree, and regenerating it cascades
into `BUNDLE.jsonl` and `FRAME_HASHES.jsonl`. Unchanged by round 2.
