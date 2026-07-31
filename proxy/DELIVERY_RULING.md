# How to check whether a proxy delivery landed

Ruling of record for `A10-shared-ledger-real-arms`, and the method that
supersedes the one which failed it.

Written under S31-a10-said-done-prove-it, 2026-07-30, worker W-1702, base
commit `12a48ecc`. Working notes and raw evidence:
`runs/20260730T043824Z-S31-a10-said-done-prove-it/`. The executable form is
`tools/audit_delivery.py`; run it before re-judging A10.

---

## 1. The ruling, in one paragraph

**A10 is delivered.** It is merged into `origin/master` in full, its tracked
artefacts are present and reproduce, and the reason a later check could not see
it is that the check looked at a path no commit contains. The shared ledger's
zero real-arm records is **the state A10 published as its starting condition
and explicitly declined to change on territory grounds** — not a shortfall in
A10. Do not re-fail A10 for it. What remains open is real, and it belongs to
the three arm territories, not to `proxy`.

Of the three possibilities the S31 ticket offered — never done, done but not
merged, or delivered onto a gitignored path so the audit method is what is
wrong — the answer is **the third, with a fourth thing underneath it**: the
gap the check found is genuine, was already declared, and has a different
owner. Both halves matter. "The audit was wrong" and "the gap is real" are
both true, and reporting only one of them has already happened twice.

## 2. Why the check could not have worked

```
$ git merge-base --is-ancestor origin/agent/a10-shared-ledger-real-arms origin/master
  → exit 0
$ git diff --stat master...origin/agent/a10-shared-ledger-real-arms
  → (empty)
$ git check-ignore -v proxy/var/ledger.jsonl
  proxy/.gitignore:3:var/   proxy/var/ledger.jsonl
$ git ls-files proxy/var/
  → (empty)
```

The check said it verified deliveries *按 `origin/master`* and then parsed
`proxy/var/ledger.jsonl`. That path is excluded by `proxy/.gitignore:3` and has
never been tracked at any commit. **A path that cannot appear in a commit
cannot be evidence about that commit.** What it actually read was the working
tree of whichever checkout the auditor happened to be sitting in — or nothing
at all, in which case "the file is not here" and "the file is here and the
answer is zero" produced the same red.

Three failures compounded, and they need separate fixes:

**Wrong object.** A runtime artefact on one disk was used to answer a question
about repository content. `tools/audit_delivery.py:census()` now returns
`ABSENT` or `PRESENT` and never a bare count, so the two cannot be confused
again; `tests/test_audit_delivery.py` asserts they are different words.

**Wrong proposition.** "A real arm" names two independent things:

| | axis 1 — arm identity | axis 2 — liveness |
|---|---|---|
| question | is `arm` one of `bare_cc` / `schema_repro` / `theoria`, rather than `probe` / `replay` / `mock_arm`? | does the run's `run_start` name a non-localhost `env_upstream` / `model_upstream`? |
| today | 0 | 0 |
| owner | `theoria-arm` (configuration only), `baseline-arms`, `ablation-arm` | whoever authorises the first live run |
| A10's title meant | this one | not this one |

Both are zero, which is exactly why one word covering both went unnoticed for a
day. They are now counted separately and never summed.

**Circular source.** The number reported is A10's own published *before* state
— `runs/20260729T010000Z-A10/MANIFEST.json` records `records: 107,
by_arm {mock_arm: 74, replay: 33}, real_arm_records: 0` as the condition it
measured against. The same sentence is a hand-written constant in
`monitor/spec.py:593`, belonging to finding **F-19 — the ruling that created
A10 in the first place**. A check that re-reads a ticket's premise and scores
it as that ticket's result will fail the ticket forever, and will do so more
confidently each time.

## 3. A10 never claimed the thing it was failed for

This is in tracked text, written *before* the implementation
(`runs/20260729T010000Z-A10/SCOPE.md`, committed at `02115515`, ahead of every
code commit in that branch):

* `demo_three_arms.py:16-22` — "**What this does NOT show, and must not be read
  as.** These are the *ledger identities* of three arms, driven by this script.
  It is not the three real arms running their own inner loops through the proxy
  — that requires editing `theoria-arm/`, `baseline-arms/` and
  `ablation-arm/`, which is outside this item's `proxy` territory and is
  recorded as a gap in `SCOPE.md` §1."
* `MANIFEST.json:94` — `"scope": "ledger identities of three arms driven by a
  script; NOT the three real arms running their own loops -- that is
  cross-territory"`.
* `RUN_STATE.md:109-110` — the arm-side rewiring is gap #1 of seven, with the
  recommendation that it be split into three items.

The requirement was declined **in writing, on territory grounds, in advance**,
and the decline was accepted by the body that issued the ruling
(`monitor/spec.py:627-636`, F-19's same-day correction). A delivery is not
short for refusing to edit another track's source; the repo's own rule is that
it must not.

## 4. What is actually open, and who owns it

| Gap | Owner | Status |
|---|---|---|
| Arms billing into the shared ledger (axis 1) | `theoria-arm` needs **configuration only** — `harness/run.py` already takes `ledger_path` as a parameter and never forwards it from `main()`. `baseline-arms` and `ablation-arm` need source changes; `ablation-arm` also has design decision D-AB-004 pointing the other way. | open, cross-territory, unassigned |
| A live run through the proxies (axis 2) | unassigned | open — `README.md:141` and `DECISIONS.md:255,319` already say so |

Until those land, **zero real-arm records in `var/ledger.jsonl` is the expected
state.** A check that asserts otherwise is asserting against a requirement
nobody has been given.

## 5. Two things a future auditor should know about this ledger

**Auditing it mutates it.** `reconcile.py` appends a `score_mismatch` incident
whenever it finds a problem, and the CLI enables that by default —
`--no-incident` is opt-*out* (`reconcile.py:549`). Running `reconcile --all`
twice appends the same findings twice; there is no idempotency key. Six such
records are in the live ledger right now, `seq` 108–113, from two runs twelve
seconds apart during the previous pass at this item. They are documented rather
than removed: the file is append-only, and rewriting it to tidy an audit's
footprints would be the worse offence. **Pass `--no-incident` when you only
want to look.**

**Incidents wear an arm they did not earn.** `reconcile.py:521` stamps an
incident with `steps[0].get("arm", "probe")` — the arm of the run being
complained about. So counting records by `arm` counts the auditor's own
footprints. Of the live ledger's 113 records, 107 are activity and 6 are
complaints. Any census must filter `event != "incident"`; `audit_delivery.py`
does, and `test_audit_delivery.py` has the failing path for it.

## 6. The method that replaces the old one

```bash
cd proxy && python -m tools.audit_delivery              # the tracked question
cd proxy && python -m tools.audit_delivery <ledger>     # census a specific file
```

It asserts A10's artefacts against digests **read from A10's own manifest at
run time** rather than copied — the copies are what rot, and this document is
the result of a number being restated until nobody could tell which copy was
the measurement. Files that later items were meant to keep editing
(`ledger.py`, `reconcile.py`, `LEDGER_FORMAT.md`, `README.md`) are exempt from
the digest and checked for substance instead, so the audit cannot go red on
somebody else's correct work. It re-runs `demo_three_arms.py` rather than
believing its archived output.

The general rule, which is the part worth keeping when A10 is forgotten:

> **Check a delivery against the tracked artefacts it actually produced, on
> paths the commit contains. If the only evidence is on a gitignored path, the
> finding is about the audit's design, not about the delivery. And when a
> quantity can be zero for more than one reason, report the reasons
> separately — a single number that is zero twice over is how two different
> open problems became one wrong verdict.**
