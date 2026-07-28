# P-11 · RUN_STATE

Prompt: `monitor/prompts/P-11-arc-hygiene.md` · branch `agent/p11-arc-hygiene` ·
base `df9f748` · 2026-07-28.

## Delivered

**1 · F-11 ledger — done.** Nine sealed games registered in
`data/contamination_log.jsonl` at the levels INC-BA-001 self-reported, with
one disclosed deviation (`dc22-fdcac232` keeps the stronger
`design_document_disclosed` level INC-004 gave it rather than that table's
轻微, since copying the rating would have been a downgrade);
`ls20-9607627b` and `ft09-0d8bbf25` marked `quarantined_from_claims`; `INC-006`
filed with the ruling, its basis, and the 21→19 consequence. `piles.json`
untouched and re-verified against its published sha256.

Beyond the letter of the order, because "21→19" was otherwise an assertion:
`contamination.py` derives the register and the claim set from the append-only
log, re-hashes `piles.json` the way `cut_piles.py` produced it, and audits every
tracked call record — arc-recon's ledger plus baseline-arms' `ledger.jsonl` and
`probe_log.jsonl`, 2489 calls, **0 sealed games addressed**. `data/claim_set.json`
is its output, and the numbers are computed rather than typed.

**The batch was then reviewed by an adversarial pass** whose only brief was to
find registration/ruling mismatches. It earned its keep: it reproduced a
**fail-open bug** in the claim-set derivation — matching two exact strings and
letting everything else fall into `clean`, the fully-uncontaminated bucket, so a
typo'd or missing `claims` field would silently put a contaminated game in the
strongest set while the headline number never moved. Now fails closed, with three
regression tests and a negative control. It also caught four places where the
prose outran the evidence, the sharpest being that **`dc22` is not a
"minor-exposure" game** — `design_document_disclosed` is mechanics prose, one
level above every blurb row, making it the most exposed game *inside* the claim
set. F-11 retains it and this track executes rulings rather than revising them,
so the tension is recorded as a residual question for the owner. All corrections
are `INC-006a` plus six superseding log entries; the ruling, the levels, the
quarantine set and 21→19 all stand.

**2 · Canary replay — done and baselined.** `canary.py`, spec in
`data/canary.json`, history in `data/canary_runs.jsonl`, gate in
`data/campaign_freeze.json` (absent until something drifts; `check-freeze` reads
absence as not frozen). Four games, 16 actions for a full sweep, **4/4
PASS**. Drift files an incident and writes the freeze file; `check-freeze` exits
1 so any harness in any language can gate on it.

The expectations were derived offline from `precheck.json` — only steps the
precheck's two replays already agreed on — so the baseline run was a *test* of
them, not their source. It passed, which makes three agreeing replays across two
days and three sessions.

**3 · Access check — closed, in `ACCESS_CHECK.md`.** Rate limits and quota
archived (600 rpm documented; 429 documented but absent from the OpenAPI spec; no
per-key action quota documented anywhere; failed 400/500 do not reach the
scorecard counter). Frame caching and release licensing resolved conservatively:
code is MIT, **game data has no stated licence**, and the site terms' compilation
clause arguably bars republishing a frame corpus — so publishing raw frames
should be treated as needing written permission, while hashes and metrics are
safe. Cross-session residue answered by the canary baseline: none.

## Two findings the ticket did not ask for

**INC-007 — the retry amplification is our own missing cookie jar.** The API sets
`AWSALB*` routing cookies and a `GAMESESSION` cookie; `client.ArcClient` echoes
none. Interleaved A/B: **20/20 first-attempt RESETs with a cookie jar, 0/20
without**, three runs, three games, arms on *different* games and swapped between
runs to kill the session-competition confound. Zero action cost. This reframes
INC-001b: the backend is multi-instance, but what changes replica every call is
us, and the 9.2× amplification the canary measured is largely self-inflicted.

**A scorecard trap.** Cards auto-close after 15 minutes of inactivity (official
docs). That is very likely the mechanism behind baseline-arms' 22-of-23
close-time 404s, and it means an arm whose model call can exceed 15 minutes loses
its scorecard mid-run.

## Open, and deliberately not closed here

* **The cookie fix is not applied.** Changing the transport re-bases every
  determinism verdict, the canary baseline, and both tracks' cost figures, and
  baseline-arms had processes in flight. It needs its own change with a
  before/after re-measurement. Probe is reproducible; finding is filed.
* **`data/recon_ledger.jsonl` contains raw frames and is tracked.** Phase 4
  publishes every tracked file. Before release it must be redacted to hashes or
  covered by written permission. Flagged in `ACCESS_CHECK.md` §8, not discharged.
* **ACTION6 `data` shape** still blocks tn36 and the whole `click` family.
  Untouched by this ticket.
* **tn36's canary is shallow** for the same reason the precheck's PASS was: its
  four actions are accepted no-ops with an unchanging frame, so the canary
  certifies RESET-state reproducibility and no-op consistency, not gameplay.
* **`available_actions` reads `null`** for ar25 and sk48 in `precheck.json`
  because those runs were reconstructed by `precheck_resume.py`, which does not
  carry the field. Cosmetic; the report understates what is known.
* **No sensitivity-analysis tooling exists yet.** INC-006 obliges every claim-set
  statistic to be reported twice; `claim_set.json` names the two groups, but
  nothing computes the second figure. That belongs to whoever builds the exam.
* **dc22's retention is unsettled** (INC-006a). It is inside the claim set at a
  mechanics-prose level, which the ruling's own basis arguably excludes. Owner
  call, not this track's.
* **`arc-recon/` has no `.gitattributes`** while `core.autocrlf=true`, so the
  committed blobs carry CRLF and `client.py`'s appends carry LF —
  `recon_ledger.jsonl` currently holds both (790 / 194). It parses fine and no
  content-level hash is affected, but file-level hashes are not portable across
  checkouts. Pinning `eol=lf` the way `engine-rig/.gitattributes` does would fix
  it and would also renormalise a 2 MB append-only ledger, which is not a change
  to make from a side branch during a merge round.

## Budget and red lines

| | |
|---|---|
| actions spent | **16 / 30** (canary baseline only) |
| stickiness probe | **0 actions** — RESETs, which the scorecard does not count |
| sealed-pile API calls | **0**, audited over 2489 calls in three ledgers, two tracks |
| `piles.json` | unmodified, sha256 re-verified |
| tests | 28 passed, offline |

Touched `arc-recon/` only. `PARTNER_SYNC.md` appended, never edited.
