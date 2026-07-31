# R3 — the adversarial review, and what it overturned

An independent reviewer was given one instruction: **refute** the claim that
*"all three `?` rows are correct abstentions, and the red gate is this item's
success, not a regression."* Not check it — attack it, and say so plainly if it
could not be attacked.

It did not survive intact. This file records what it found, in the order it
matters, with what was done about each. Three findings became code changes on
this branch; one became a separate board item; two were confirmations that no
criticism could be manufactured for, and are recorded as such.

## Overturned, and fixed here

### 1. The guard went into one of the two readers — again

The defect-2 fix widened `check_redlines.PAYLOAD_FIELDS` from a dead three-field
literal to the declared eight. `enumerate.PAYLOAD_KEYS` was a **separate
four-field literal** and was left alone. `enumerate.py`'s own module docstring
already names a *scorecard body* as class-B payload; only the literal disagreed.

So this branch reproduced, one level up, the exact defect its work order is
named after. Eleven files carrying `scorecard` or `state` bodies stayed class C
under the positive sentence *"no record pairs an id with environment payload —
statistics about the games, not material from them"*, and one of them,
`theoria-arm/runs/20260728T235841Z-leg01/run.json`, is a literal ARC scorecard
response body, `card_id` and `guid` and all.

**Fixed:** `PAYLOAD_KEYS = redlines.PAYLOAD_FIELDS`. Derived, never re-typed —
two spellings of one list is how the original disagreement happened.

### 2. `unsearchable_encoding` was wired into one file and not the other

`check_redlines` grew `unsearchable_encoding` precisely because both red lines
are UTF-8 byte searches and a wide encoding defeats them silently. It calls it
in two places. `enumerate.py` never called it — in the same function, three
lines from the id search.

The reviewer demonstrated it live: five records of
`{"game_id": "<dev-pile id>", "frame": [[1,2],[3,4]]}` written as UTF-16
classify as **A / releasable**, on the evidence string *"no ARC game id appears
in this file"* — the sentence this entire work order is named after, printed
over a comparison that was blind.

**Fixed:** a blindness guard before the `named` computation. The
API-transaction scan deliberately stays *above* it: a marker that matched is a
positive finding, and blindness cannot make a match false. Only the absence
conclusion has to be withheld.

### 3. The `?` rows named the wrong reason, and nothing tested them

`_records_pairing` returned a bare `None` and `classify` substituted a reason of
its own invention: *"could not be parsed as JSON"*. That was wrong for **every
row it was ever printed over**. All three `?` rows take `json_shaped`'s *first*
early return — `blob.decode("utf-8-sig")` raises `UnicodeDecodeError` — so
nothing was ever handed to a JSON parser. `pytest-baseline.txt` holds 45
non-empty lines of which **zero** begin with `{`; its only defect is three
mojibake byte pairs, one of them inside a quoted Python comment at offset 1805.

Worse, the reviewer found **no test covered the branch producing all three red
rows**. The pinned test plants a UTF-8 `.log` with valid JSON object lines and a
malformed third — a path none of the three real files take. So the red gate was
one `return False, False` away from disappearing, and nothing in the suite would
have noticed.

**Fixed:** the reader's reason travels with the refusal, and the missing
negative samples were written.

## Overturned, and split into its own item

### 4. Same figure, three containers, three licence classes

`figure6_bill_shape` is tracked as `.png` (class **A**), `.svg` (class **C**) and
`.pdf` (class **?**). The id plays an identical role in both text formats — SVG:
`<g id="text_42"><!-- g50t-5849a774 --></g>` beside a tick `<use>`; PDF:
`BT /F1 6.5 Tf 0 0 Td [ (g50t-5849a774) ] TJ ET` at the same coordinates. **It is
an axis tick label.** Before this branch the family was A/C/C; after it is
A/C/?, which is strictly *less* coherent. The work order's thesis is "judge the
bytes, not the name", and the fix swapped a filename discriminator for a
container-encoding one.

The reviewer also established that `release/` has **no adjudication path at
all** — nothing in `checklist.py`, `bundle.py` or any document lets a human rule
on a `?` row. So the gate is red forever for any binary figure that renders a
per-game label, which is a standing invitation for the next person to switch it
off, taking the true reds with it.

**Not fixed here, and deliberately.** Building a ruling path is new machinery,
not a default fix, and it needs its own negative samples — a ruling pinned to a
stale sha256 must not carry over to changed bytes, and a ruling must not be able
to overturn class D. Raised as board item **`R4-ruling-path-for-undetermined`**.

The tempting shortcut is rejected in that item's text: using the existing
`_review_note` machinery to make the PDFs class C with a visible doubt would
turn *"cannot read it"* back into *"ship it, flagged"*, which is the thing R3
exists to stop. A ruling path makes the red mean **red until adjudicated**
instead of **red until switched off**.

## Confirmed — no criticism available

* **Are the four ids a risk?** All four are **development pile**
  (`ar25-0c556536`, `g50t-5849a774`, `sk48-d8078629`, `tn36-ef4dde99`); the
  sealed pile contains none of them. The reviewer declined to call `?` an
  overstatement anyway: B-versus-C is a *licence* question and dev-pile files
  are exactly the files that can be class B. The evidence string never says
  "seal" and cannot be read as a seal claim.
* **Scope overrun?** No. The agent made exactly the one edit the work order
  ordered; the two PDFs are mechanical collateral of it, and `DISTRIBUTION.md`
  reports them as unpredicted and measured rather than filed down. What was
  wrong was the *explanation*, not the scope.
* **Do the archived numbers reproduce?** Yes, exactly. Re-running the census
  gave `A 5671, B 61, C 244, D 1, ? 3` and byte-identical class and evidence on
  every one of 5,980 rows; only two rows differed, in `size` alone, from
  unrelated edits landing after the census.

## The archive was false about its own diff

`DISTRIBUTION.md` said *"defect 2 was not in this work order"* (it is stated at
lines 19-24 of the item and instructed verbatim at line 34) and *"`check_redlines.py`
was not touched"* (it gained a marker, a derived constant, four new functions and
a rewritten pairing check). `MANIFEST.json` then recorded
`code_under_measurement["release/check_redlines.py"]` as the sha256 of the
**modified** file while its own `not_done` asserted the file had never been
looked at — a self-contradiction checkable against its own hash.

Both were written at 16:12:45Z by the enumerate half of this work, before the
`check_redlines` half existed in the same worktree. That explains it and does not
make it true. Both are regenerated against the final code rather than corrected
in prose, and this file records why the earlier bytes said what they said.

## What the reviewer got right that is worth keeping as a standing lesson

Its sharpest finding is not any single defect but the pattern: **this branch's
own diagnosis — "a guard went into one of two readers" — became true of two more
pairs of readers while the branch was being written.** Sharing a function is not
the same as sharing a rule. `json_shaped`'s docstring even names a precondition
(`check_sealed` only reaches it for a file that already matched an id in its raw
bytes) that `enumerate.classify` violates, because it calls the two in the
opposite order. Reusing a function without re-reading what it assumes is the
same failure, one level up.
