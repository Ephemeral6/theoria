# Changing a shared contract

**Adding is free. Taking away is a breaking change, and it has to be announced
before it lands.**

That is the whole document. The rest is which changes are which, what an
announcement has to contain, and why a rule this obvious is written down at all.

## 1. Why this exists

On 2026-07-28 a live run of the `theoria` arm made its first desk call. The
provider was paid **$2.695**. The reply was discarded, the run's ledger
contained **zero `model_call` records**, and the arm — whose `except Exception`
around the call recorded "the desk failed" and went back for more evidence —
would have kept paying $2.70 a call until its $15 ceiling stopped it.

The cause was a documentation change. `LEDGER_FORMAT.md` §4 closed the
`model_call` field set. P-8 had been writing five fields on that record —
`beat`, `label`, `transport`, `proxied`, `proxy_gap` — since before the closure
existed. Every arm imports `proxy/` as a library from the repo root, by design,
because the ledger has to be produced by the frozen writer. So **the change
arrived on a commit the arm had never touched, in a directory it may not edit,
and nothing announced it.**

Three things about that are worth keeping:

* **Nobody did anything wrong.** Closing the field set was a defensible call
  with a written reason. Writing the five fields was a defensible call with a
  written reason. The two were made in different directories a few hours apart
  by parties who do not communicate. The gap was between them.
* **Every test passed.** P-8's suite checked the record's shape, constraint 8,
  and §1–§3 — against hand-built dictionaries. Nothing offline ever asked the
  real writer to accept what the real caller actually sends. The gap was not a
  missing assertion; it was a missing subject.
* **The pin worked and did not help.** `upstream_pin()` hashes `proxy/ledger.py`
  into every run manifest precisely so a silent upstream change cannot silently
  change results. The hashes are there and they differ. **But nothing compares
  them between runs.** A pin that is written and never diffed documents an
  incident afterwards, for someone who already knows to look.

## 2. The rule, and the asymmetry under it

A **widening** — anything that makes the proxies accept more than they did — is
free. Land it, note it in §5's ledger, done. No announcement, no wait. An
importing track that never hears about it is fine, because nothing it already
does stops working.

A **tightening** — anything that makes the proxies accept less — is a breaking
change and takes §3's procedure, *even when it is obviously correct*, *even when
you are sure nobody is relying on the thing you are removing*. INC-TA-006's
closure was obviously correct and the person making it was sure.

| tightening (announce first) | widening (just land it) |
|---|---|
| removing a field from `LEDGER_FORMAT.md` §3/§4 | adding one |
| making an optional field required | making a required field optional |
| adding a banned spelling | removing one |
| adding an envelope field (callers may no longer set it) | removing one |
| adding a required key to a §6 auxiliary | removing one, or adding a whole new auxiliary event |
| bumping `v` | — (readers reject unknown `v`, so every bump is breaking) |
| removing a key from `canon.describe()` | adding one |
| removing an `event` from `ledger.EVENTS`, an arm from `ARMS`, an incident kind from `INCIDENT_KINDS` | adding to any of them |
| tightening a type check, or a guard's accept condition | loosening one |
| turning a warning into an error | turning an error into a warning |

The asymmetry is not politeness. It is that these contracts are consumed by
**writers that run after the fact**. A ledger record is written once the request
has been sent and the money has been spent; a refusal there cannot un-spend it
and destroys the only evidence it happened. So the default has to be: record it,
say something, move on. **Refusing to record is strictly worse than recording
something a reader may have to skip.**

Which is also why §3's compatibility window is *warn, don't refuse*, and why
`validate_ledger.py` reports an unknown field as a notice rather than a problem:
the read side has the same asymmetry one direction over, and it lands on the
frozen scorer.

### What this does **not** license

Additive-safe is not permissive. The things `canon.py` still refuses outright
are the things that are *wrong* rather than merely unknown — a v0 spelling
(drift between two names for one thing), one of the five banned dollar spellings
at any depth (§5: a price in an append-only file is wrong the day the price
changes and cannot be corrected), an envelope field set by a caller (forged
ordering), a missing required field (uninterpretable), a type that would produce
a plausible wrong number. Those refusals are load-bearing and none of them
moved. "We are additive-safe now" is not an argument for relaxing one of them;
relaxing one is its own change, and by the table above it happens to be a
widening, which means it needs a reason rather than an announcement.

One of them had to be *extended* to stay the same size. §5's "no dollar figure
is ever written to the ledger" is a property of the file (RED-42), and before
this change the only way a price could hide was inside a block §4 requires
verbatim — everything else on the two shapes was refused outright. Additive
safety opens a second door, so the ban list is now scanned inside every unlisted
field and to the bottom of `usage` rather than one level in. **Widening
somewhere is not free of work elsewhere**; a property that was being held up by
a constraint you are removing has to be re-established on its own terms, and
noticing which properties those are is most of the review a tightening's removal
deserves.

Two limits, so neither reads larger than it is. The ban is a list of *names*,
not a price detector: `usd_spent` is not on it and is written — which was
already true of auxiliary payloads, always open, so what changed is that the two
shapes now behave like them. And `ledger.EVENTS` / `ledger.ARMS` are still hard
refusals, deliberately: both are fixed when a run's ledger is constructed, so a
wrong one fails on the first record, before anything has been sent or spent.
That is a typo caught, not evidence destroyed.

## 3. The procedure for a tightening

1. **Announce it on `PARTNER_SYNC.md`**, in your own track's section, with the
   milestone tag `contract-notice`. It must say, concretely enough that a reader
   can check their own code against it without reading yours:
   * the surface (`proxy/LEDGER_FORMAT.md §4`, `ledger.EVENTS`, …);
   * what stops being accepted, **by name** — not "we tightened validation";
   * what to write instead, or what the migration is;
   * the earliest date the tightening may land;
   * the current contract fingerprint
     (`python -m proxy.tools.contract --fingerprint`).
2. **Wait one cycle.** The announcement has to be on the mainline, where the
   other tracks read it, for at least one full monitor cycle before the
   tightening lands. Tracks do not communicate; the board is the only channel,
   and a channel nobody has had time to read is not one.
3. **Ship a compatibility window.** For the duration, the old form is **accepted
   with a warning**, not refused. Say in the announcement how long the window
   is and what closes it. A tightening with no window is not a tightening, it is
   a breakage with a note attached.
4. **Land it, and re-pin**: `python -m proxy.tools.contract --update`. The
   command prints every tightening in the change and exits non-zero, so the
   commit that re-pins is also the commit that lists what was owed.
5. **Add a row to §5**, citing the announcement.

A tightening that cannot wait — a credential leak, a sealed-pile hole — skips
steps 2 and 3 and is filed as an incident under its own name, with the reason
written down. That exit exists so the procedure does not have to be broken
quietly. It is not for schedule pressure.

## 4. The mechanical half

A protocol with no detector is prose, and the whole point of §1 is that prose
did not stop this.

* **`proxy/canon_contract.json`** pins `canon.describe()` — the envelope, both
  shapes, every required set, the auxiliary keys, the banned spellings — plus
  the three registries `ledger.py` owns (`EVENTS`, `ARMS`, `INCIDENT_KINDS`),
  because `append` refuses an unregistered arm or event outright and a detector
  blind to them would be narrower than the table above.
* **`python -m proxy.tools.contract`** diffs the live registry against the pin
  and labels every difference `additive`, `tightening` or `neutral`. Exit 0 only
  when nothing moved.
* **`proxy/tests/test_contract_changes.py`** fails the suite the moment the two
  disagree, and its failure message is the fork in the road: additive → re-pin
  and log it; tightening → §3.
* **`proxy/scoring/frozen.json`** carries `depends_on`. The frozen scorer's
  S-12 check delegates to `tools/validate_ledger.py`, which consults
  `canon.py`, so a contract change moves what the scorer returns while
  `arc_v1.py` hashes exactly as before — the freeze reports all clear and the
  number changes underneath it. Freezing the source of a rule whose behaviour
  lives partly in its imports is a half-freeze, and a half-freeze reads as a
  whole one.

**The fingerprint is the authority; the classifier is only the explanation.** A
classifier sees the deltas it was written to model, so a change nobody
anticipated would come back not mislabelled — which is visible — but *cleared*,
which is not. When the pinned and live fingerprints disagree in a way the
classifier cannot account for, the verdict is `tightening`. Half-explained
counts as unexplained: an additive delta must not clear the part nobody looked
at. An over-strict verdict costs a re-read; an over-permissive one costs what §1
cost.

What this cannot do is verify that the announcement happened. A test cannot read
PARTNER_SYNC and judge a paragraph. What it does is remove the excuse the
incident actually had — that nobody knew a breaking change was being made — by
putting the question in front of whoever is making it, at the moment they make
it.

### For a track that imports `proxy/`

One line in your run manifest:

```
python -m proxy.tools.contract --fingerprint    # sha256:...
```

and **diff it against the previous run's**. That is W-1521's standing
recommendation after INC-TA-006, and it is the half this directory cannot do for
you: `proxy/` can publish a fingerprint, but only the importer knows which two
runs are supposed to be comparable. A fingerprint that moved between two runs
you meant to compare is either an announcement you missed or a result you should
not average.

Do not vendor a copy of `proxy/` to escape this. The reason arms import the
frozen writer is that a ledger written by a fork is a ledger nobody else can
audit; a stale fork trades a loud incident for a quiet one.

## 5. The change ledger

Append-only. Newest last.

| id | date | change | kind | announced |
|---|---|---|---|---|
| C-001 | 2026-07-28 | `model_call` gains `beat`, `label`, `transport`, `proxied`, `proxy_gap` (§4) — the five P-8 was already writing | additive | n/a |
| C-002 | 2026-07-28 | the two shapes stop being closed: an unlisted field on `env_step`/`model_call` is warned about and written, not refused | widening | n/a |
| C-003 | 2026-07-28 | `canon.describe()` renames `closed_shapes` → `shapes`; **`closed_shapes` is kept as a deprecated alias** and may be removed no earlier than 2026-08-11, under §3 | tightening, in its window | this file; PARTNER_SYNC `contract-notice` |
| C-004 | 2026-07-28 | the pinned contract gains `events`/`arms`/`incident_kinds`; `validate_file`'s report gains `notices`; `frozen.json`'s `arc_v1` entry gains `depends_on` | additive | n/a |

C-003 is the small one deliberately. Renaming a key in a published dictionary is
about as minor as a breaking change gets, and it is the exact size of change
that gets made silently — which is how §1 happened. The alias costs three lines.

C-004's `notices` key has one consequence worth stating rather than discovering:
`proxy/runs/p9-shell-harden/MANIFEST.json` pins the sha256 of a stored
`validate_file` output, and that file no longer reproduces — the report now
carries `"notices": []`. Nothing recomputes `proxy/runs/*` hashes, so it would
have failed silently and only for whoever tried to reproduce P-9. It is left as
a documented drift rather than papered over: the run's artefact was correct when
it was written, and rewriting a past run's manifest to match a later format is
the manoeuvre `CANON_MIGRATION.md` §7 declines for the same reason. Byte-hashing
a JSON report makes every additive change look like a break; that is a property
of the pin, not of the contract.

## 6. What this document does not cover

* **The other direction.** This binds `proxy/`. `CONTRACTS/candidates_schema.md`
  is frozen and neither track may modify it at all, which is a stricter rule
  than this one and stays that way. `CONTRACTS/dsl_grammar_v0.1.md` belongs to
  the theory-compiler track and is theirs to govern.
* **Enforcing the wait.** Nothing checks that a cycle passed. The board is a
  board, not a scheduler.
* **Runtime contracts that are not field sets** — the spend gate's protocol, the
  guard's verdict semantics, `cost.py`'s pricing tables. The rule in §2 applies
  to them by its own terms, but §4's detector only sees `canon.describe()`.
  Widening the pin to cover them is the obvious next thing and is not done.
