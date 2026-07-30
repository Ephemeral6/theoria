# r3 / r4 — the signature you are being asked for is much smaller than two of us told you, and it is not about sealed material

utc: 2026-07-30T03:21:20Z   (read from `date -u` in the same shell round that wrote this file)
author: OPS-M (cycle 24)
branches: `origin/agent/r3-release-classifier-defaults`, `origin/agent/r4-ruling-path`
measured against: `origin/master` = `223f78a8` (master moved 5439d07f -> 223f78a8 mid-diagnosis; all
figures below re-measured at 223f78a8)
disposition: **needs one human decision. But read section 3 before you decide who it costs.**

## 0. What I retract from my own earlier reporting this cycle

* I said **"r3 and r4 are one item, not two."** **Wrong.** r3 is an ancestor of r4, but the merged
  trees are **not** byte-identical (`1870c405…` vs `7096e2a1…`); r4 adds 10 files / 1637 lines,
  including the entire ruling mechanism. **r3 alone leaves the gate red with no ruling path at all.**
  What survives: r3-then-r4 and r4-direct produce the same tree (`7096e2a1` both ways), so no landing
  order helps — true conclusion, wrong reason.
* An earlier cycle's framing — that signing is a `needs_human -> shipped` move on ARC-derived
  material, and therefore a hard stop — is **overstated**. See section 3.

## 1. The mechanical core (re-derived independently twice, both agree)

Both branches fail **exactly one** of `release/verify.sh`'s five steps: step 3, "every tracked file is
classified". `enumerate.py --dry-run` exits non-zero because three tracked files land in class `?`:

```
figures/paper/dark/figure6_bill_shape.pdf   UnicodeDecodeError 0xac at position 10
figures/paper/light/figure6_bill_shape.pdf  UnicodeDecodeError 0xac at position 10
theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt   0xa1 at 1805
```

**Clean master is green on all five steps**, in the strict `--mode generate` path — so the red is not
master's, and master's green is not a lenient-mode artefact. Classification is mode-independent
(`build()` takes no mode).

**Master is green because it guesses from the file extension. r3 replaces the guess with deliberate
abstention.** That is the branch working as designed, not a defect.

## 2. Landing strictly tightens — confirmed twice, with a trap for whoever re-checks

Same tree, two classifiers, 6380 paths: **11 files move class — 8x C->B, 3x C->?, zero toward shipped.**

**The trap**: the naive comparison (master's tree vs r4's tree, 6353 vs 6007 rows) shows a spurious
12th move, `monitor/mailbox/OPS-A.md` C->A. That is content drift between two different trees, not the
classifier. Anyone who re-checks this the obvious way will see a false "moves toward shipped" and may
reverse the decision on it. **Compare two classifiers over one tree, not two trees.**

## 3. What the human is actually being asked for — this is the part that changed

An adversarial group was sent specifically to break the "hard stop" framing. It broke it:

* **The three files name only development-pile ids** (`ar25-0c556536`, `g50t-5849a774`,
  `sk48-d8078629`, `tn36-ef4dde99`), verified against `piles.json`. **Zero sealed-pile ids.**
* **The sealed-pile and credential red-line check read all three files successfully and passed**:
  `0 credential violation(s), 0 sealed-pile violation(s), 0 file(s) this check could not read`
  over 6380 tracked files. `check_redlines` works on **raw bytes**; it never needed to decode them.
* **`enumerate.classify()` is not the leak check.** They are different checks at different steps.
  A classifier change therefore **cannot** weaken the sealed-pile guarantee. Two of us implied it could.
* The proposed ruling (`RULINGS_PROPOSED.md:63,105`) is class **C / releasable-flagged** —
  **exactly what master's own classifier assigns to all three today**, automatically and silently,
  when run over the identical merged tree.

**So the ask is not "authorise the release of ARC-derived material."** It is: *put a name and a reason
on a disposition the machine already reaches by itself.* That is an accountability upgrade, and it is
strictly better than the status quo, in which the same three files ship on an extension guess with no
human in the loop at all.

**Honest caveat, and it cuts the other way.** "Master already ships them" is true of master's
**classifier**, not of its **published bundle**: `MANIFEST.jsonl` has 1951 rows and `BUNDLE.jsonl`
1931, against 6353 tracked files, and neither mentions `figure6_bill_shape`. That is the same
manifest-coverage gap OPS-M reported on 2026-07-29; it is RES-2's territory and I have not touched it.
**The honest form of the claim is: master's classifier would ship these; master's current bundle
predates them.**

## 4. There is a fourth exit, and it costs you less

The three exits reported earlier were: sign the rulings, repair the bytes, or relax the check. A fourth
exists: **land with the gate red-but-understood.** Today that is blocked by `monitor/ci_merge.py:138`
("conflicts and red gates stay held") and `monitor/gates.py:53`, which discovers `release/verify.sh`
by name. It still needs a decision from you — but the decision is *"accept a known-red gate on a branch
whose red we have characterised"*, which is merge-queue policy, **not** an ARC licence ruling.

**Two candidate code exits are NOT available and I want that on the record**: magic-number binary
detection (`check_redlines.py:233-241`) and `errors="replace"` decoding both re-assert "no payload"
about bytes nobody parsed — which is precisely the disease r3 exists to cure. **A route that makes the
classifier guess again is not an exit.**

## 5. What I did not do

I applied no ruling, signed nothing, committed to no branch, and pushed nothing. `RULINGS.jsonl` ships
**deliberately empty of rulings** — its author built the adjudication path and refused to self-sign,
and archived the argument in `RULINGS_PROPOSED.md`. That refusal is the correct instinct and I matched it.

## 6. What I recommend

**Land r4** (which carries r3) with **one** of:
(a) three class-C rulings signed by a human in `release/RULINGS.jsonl` — the smallest, most honest fix,
    and it is a record of a decision master already makes; or
(b) an explicit merge-queue exception to land with the release gate red-but-characterised.

**Do not** ask the branch author for another revision. There is nothing left for them to fix: the
branch is correct, and it is red *because* it is correct.
