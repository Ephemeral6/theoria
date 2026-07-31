# Three files at `?`, the evidence, and the lines that would settle them

`release/enumerate.py` currently leaves three tracked files as class `?` /
`needs_human`, which makes `release/verify.sh` red. That red is R3's deliberate
outcome: before it, all three shipped as `releasable-flagged` on the authority of
the characters after the last dot in their names.

R4 built the way to clear a `?` **by ruling on it** rather than by editing code.
This file does the work of the ruling and stops one step short of it, because a
ruling is a signature and `monitor/CHARTER.md` routes anything requiring human
identity to `needs_human` — not to the agent that built the mechanism and would
like to see its own gate go green.

Each proposal below is one line to append to `release/RULINGS.jsonl`, with the
`ruled_by` left blank. Every hash was recomputed for this document.

---

## 1 & 2 — the two `figure6_bill_shape` PDFs

| | |
|---|---|
| `figures/paper/dark/figure6_bill_shape.pdf` | sha256 `ca805a75bbd858d0…`, 257,076 bytes |
| `figures/paper/light/figure6_bill_shape.pdf` | sha256 `d4397dd8307a2647…`, 257,901 bytes |

**Why the machine abstains.** The bytes do not decode as UTF-8
(`UnicodeDecodeError` at position 10), so `json_shaped` returns *"not text at
all — undetermined, not prose"*, and no parser can say whether the four ARC ids
in the file sit beside environment payload. All four ids are **development
pile**, so no red line is implicated; what is undetermined is the *licence
class*, B versus C.

**The evidence a human would rule on.** The id appears as a PDF text-drawing
operator:

```
1 643.1695026034 818.6115705759 cm
BT
/F1 6.5 Tf
0 0 Td
[ (ar25-0c556536) ] TJ
ET
```

That is a glyph run placed at a coordinate — **an axis tick label**. The same
figure's `.svg` twin, which *is* parseable and is classified **C** by the
machine, carries the same four ids in the same role:

```xml
<g id="text_41">
 <!-- ar25-0c556536 -->
```

Both are matplotlib output from one `figures/` pipeline over one dataset; the
`.png` twin is class **A** only because rasterising destroys the text. So the
`?` is not a doubt about what the file contains — it is a doubt the classifier
cannot resolve *through a PDF parser it does not have*, about content its
sibling already settled.

**Proposed:**

```json
{"path": "figures/paper/dark/figure6_bill_shape.pdf", "sha256": "<full hash>", "class": "C", "ruled_by": "", "utc": "", "reason": "Axis tick labels. The four ids appear as PDF text operators (BT /F1 6.5 Tf ... [ (ar25-0c556536) ] TJ ET) at plot coordinates, the same role they play in the parseable .svg twin that this enumerator independently classifies C. Same matplotlib pipeline, same dataset, no environment payload. All four ids are development pile."}
```

…and the same for `light/`, with its own hash.

**The argument against ruling these, which a signer should weigh.** Ruling from
a *sibling file* is provenance reasoning, and `enumerate.py` allows that in
exactly one place (`UPSTREAM_PAYLOAD_PREFIX`, with a comment saying so). Extending
it here is a judgement, not a derivation: nothing in the PDF proves it came from
the same pipeline as the SVG. If that link is not good enough, the honest
alternative is not a ruling — it is to stop tracking a binary the release cannot
read, or to regenerate it in a form that can be read.

---

## 3 — the pytest baseline log

| | |
|---|---|
| `theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt` | sha256 `764359440f0d4444…`, 3,051 bytes |

**Why the machine abstains.** `UnicodeDecodeError` at position 1805 — three
mojibake byte pairs, one of them inside a quoted Python comment
(`# LEDGER_FORMAT.md \xa1\xec1: one file holds many runs`). The file holds 45
non-empty lines of which **zero** begin with `{`; no JSON parser was ever
involved, despite what the pre-R3 evidence string claimed.

**The evidence a human would rule on.** The single dev-pile id appears as a
source constant inside captured pytest output:

```python
    game = "g50t-5849a774"
    slug = "pytest-"
```

A test fixture naming a game is the textbook class-C case — *"ids used as
constants, guards or narrative"* — and this one is quoted source code inside a
test log, which is one step further from payload than prose is.

**Proposed:**

```json
{"path": "theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt", "sha256": "<full hash>", "class": "C", "ruled_by": "", "utc": "", "reason": "Captured pytest output. The one dev-pile id appears as a source constant in a quoted test body (game = \"g50t-5849a774\"), which is the class-C case verbatim. Undecodable only because of three mojibake byte pairs at offsets 1805/2370/2556; 45 non-empty lines, none of them JSON."}
```

**The cheaper fix, which a signer should prefer if it is available.** This file
is *nearly* UTF-8. Three byte pairs stand between it and an ordinary machine
verdict. Repairing them would make the ruling unnecessary — and a `?` that can
be removed by fixing the file is better resolved that way than by a signature,
because the signature has to be re-made every time the bytes change and the
repair does not. `theoria-arm` is another territory's, which is why this is a
recommendation and not a change.

---

## What signing does, mechanically

Append the line, with `ruled_by` and `utc` filled in. Then:

* `enumerate.build()` moves the row out of `?` into the ruled class;
* the row keeps its original evidence and gains
  `-- RULED class C by <name> at <utc>: <reason> (the machine did not determine
  this; a human did, against sha256 <prefix>)`, plus `ruled_by` / `ruled_utc`
  fields, so nothing downstream can mistake a signature for a measurement;
* `enumerate.main()` prints a `note` naming every ruled file before the
  distribution, because a class-C count containing ruled rows is not the same
  fact as one the classifier reached alone;
* `verify.sh` goes green **for these three files only**. Any future `?` is red
  again, which is the property worth having.

If the file is later regenerated, its hash changes, the ruling stops applying,
the row returns to `?` — and `main()` prints `STALE RULING`, naming the old hash
and the new one. Nobody has to remember.
