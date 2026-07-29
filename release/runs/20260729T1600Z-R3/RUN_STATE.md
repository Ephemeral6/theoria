# R3 — every default in the release classifier pointed at "publishable"

RES-4, branch `agent/r3-release-classifier-defaults`, base `7852ef30`.
Offline: zero API calls, $0.00, zero sealed-pile contact.

`release/MANIFEST.jsonl` is the document a release is assembled from. A
permissive default in the classifier that writes it is not a rough edge; it is
the failure mode. All three defects in the work order were the same sentence in
three places — **read it wrong, don't recognise it, can't compute it: ship it.**

## What changed

| defect | file | before | after |
|---|---|---|---|
| 1 | `release/enumerate.py:123` `_arc_game_ids()` | `.get("strata", {})` — a missing key becomes an empty dict, an empty comprehension is a legal empty list, and every file is then class A on the evidence *"no ARC game id appears in this file"* | shape guard: the id count must equal `len(dev_pile) + len(sealed_pile)`, else **refuse to run** |
| 2 | `release/check_redlines.py:417` | a dead literal `("frame", "frames", "action_input")` beside a `PAYLOAD_MARKERS` constant declaring **seven** fields — five were never tested by anything | the literal is gone; `PAYLOAD_FIELDS` is derived from `PAYLOAD_MARKERS` and is the only list |
| 3 | `release/enumerate.py:146,160` | class decided by the characters after the last dot in the filename | `redlines.json_shaped` — the same content sniff `check_redlines` already used, and whose docstring already claimed both files called it |

## The numbers

`DISTRIBUTION.md` in this directory is the census: 5,980 tracked files
enumerated three times, with `snapshot.py` as the tool.

* **Measured, this tree (defect 3):** C 247 → 244, `?` 0 → **3**. Nothing moved
  in the permissive direction.
* **Counterfactual, defect 1:** with the id list forced empty against the
  *unfixed* enumerator, **284 files move into class A** — 37 from B, 247 from C,
  **92.6 MB**. The 37 class-B files are the api-derived compilations
  `LICENCE_POSTURE.md` says need written permission. Defect 1 is latent today
  because `piles.json` still carries the `strata` key it reads, so a
  counterfactual is the only honest way to measure a default that has not yet
  fired. `MOVED.tsv` lists every one, tagged by defect.
* **Defect 2** is not visible in the distribution because it lives in
  `check_redlines`, not the enumerator. Its measurement is the test matrix
  below, not a file count.

## Verify is RED, and that is this item's success

`bash release/verify.sh` → **`VERIFY: RED`**, archived byte for byte as
`verify.after.txt` here. Four of the five sections are green; the one that fails
is **"every tracked file is classified"**, exit 1, with exactly three rows:

```
figures/paper/dark/figure6_bill_shape.pdf     names ar25-0c556536, g50t-5849a774,
figures/paper/light/figure6_bill_shape.pdf    sk48-d8078629, tn36-ef4dde99
theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt   names g50t-5849a774
  ... but could not be parsed as JSON, so whether it carries environment payload is undetermined
```

The work order predicted the third row and said in advance that the correct fix
would turn the gate red. The two PDFs were not predicted; they are reported as
measured, not filed down. They reach `?` by the other half of `json_shaped`:
bytes that do not decode as UTF-8 are *"not text at all … undetermined, not
prose"*. Both PDFs do literally contain all four ids in their bytes, and the old
code asserted — from the `.pdf` suffix, having opened nothing — that those ids
carry no environment payload.

All four ids in all three rows are **development pile**, not sealed. So `?` here
blocks a manifest; it does not report a broken seal. The red says *"a licence
class has not been established for these three"*, which is true, and the
alternative on offer is the previous state, where they shipped as
`releasable-flagged` on the authority of a filename suffix.

`release/checklist.py` over the `after` rows: 7 present / 2 withheld / 0 absent /
**1 undetermined**, 3 unruled → exit 1. Over `before`: 7 / 3 / 0 / 0 → exit 0.
The item that turns is 「runs 档案（P5 条目追加）」, moving WITHHELD →
UNDETERMINED — the checklist's own distinction between *looked, not shippable*
and *could not look*.

## Tests

`python -m pytest release/tests -q` → **57 passed**, archived as `pytest.txt`.
46 was the pre-change baseline. Each defect has a negative control **and** a
positive control, in the style of the sibling file: a gate never seen to go red
is not evidence anything is green, and a gate that reddens at everything proves
nothing either.

* `test_defaults_are_not_publishable.py` — defects 1 and 3. Each test `git init`s
  a real repository under `tmp_path` and points `REPO_ROOT` at it, because
  `enumerate.build` enumerates `git ls-files` and `_arc_game_ids` reads the cut
  from that same tree; a test handing it a list of paths would exercise
  everything except the two interfaces that failed. **The broken cut file is
  planted there and never in this repository**, whose `piles.json` carries the
  binding cut.
* `test_unreadable_is_not_clean.py` (+14) — defect 2. Parametrised over
  **every** field in `PAYLOAD_FIELDS`, so a marker cannot be declared and left
  untested again; a `scorecard`-beside-a-sealed-id case, which is the shape the
  old three-field literal filed as a mere *mention*; and a positive control that
  monkeypatches `PAYLOAD_FIELDS` to `()` — agreeing with the constant today
  proves nothing, since the dead literal agreed with it once too.

Two judgement calls inside defect 2, both deliberate:

* `"frames"` was in the dead literal and **not** in the constant. Substituting
  the constant without it would have closed a hole by opening a smaller one — the
  plural is what a multi-frame reset response is keyed on. It is now in the
  constant.
* The old literal tested presence by truthiness (`d.get("frame")`). That is a
  different test by exactly one marker: `"full_reset": false` is a command sent
  to a specific game, and `bool(False)` files it as absent. `_filled()` treats
  `None` / `""` / `[]` / `{}` as unfilled and `False` as filled.

## What this run did not do, and the stale line in MANIFEST.json

**`release/MANIFEST.jsonl` was not regenerated.** It is already stale by ~4,030
rows against the current tree (1,950 rows on disk vs 5,980 tracked files), so
regenerating it is a separate change and it cascades: `BUNDLE.jsonl` and
`FRAME_HASHES.jsonl` go stale, and a `needs_human` row with no entry in
`bundle.RECIPES` fails `test_every_withheld_file_has_a_hash_and_a_recipe`.
`checklist.py` therefore still exits 0 against the manifest on disk, and exits 1
against the rows the fixed enumerator produces — which is the number reported
above.

**Correction, and why it is written here rather than fixed in place:**
`MANIFEST.json` and `DISTRIBUTION.md` in this directory were written at
2026-07-29T16:12:45Z by the enumerate half of this work, and both say *"defect 2
was not in this work order and was not looked at."* That was true when written
and is **false now** — defect 2 is fixed on this branch, as the diff of
`release/check_redlines.py` and the 14 new tests show. Neither file is edited:
`MANIFEST.json` records `DISTRIBUTION.md`'s sha256, and a provenance record that
can be quietly rewritten after the fact is worth less than one that is corrected
in the open. This paragraph supersedes that line.

## Adversarial review

The three `?` rows were put to an independent reviewer with the instruction to
**refute** the claim that they are correct abstentions — specifically on whether
routing a `.pdf` to `?` for failing a JSON parse is an abstention or a category
error that will get blanket-exempted by the next person to meet it. Its findings
are recorded in `ADVERSARIAL.md` beside this file.
