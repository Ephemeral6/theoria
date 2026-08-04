# A32 — the 74% was five defects wearing one sentence, and the cache is a net loss

Offline forensics and repair over the whole archived desk record: 104
transcripts, 103 priced calls, $147.5803 of lifetime desk spend. No model call,
no API call, no spend. Everything below is read off `desk/*.md`,
`desk_log.json` and `ledger.jsonl`, and every number in it is reproduced by
`python -m armtools.desk_discard` and `python -m armtools.cache_premium`.

## The brief's premise held, and it was too coarse to act on

R2b measured that 74% of the sk48 leg's spend bought replies the arm threw
away, and `armtools/replyloss.py` found the mechanism: `envelope["result"]` is
the CLI's **last** assistant message, so a reply that spanned more than one
message reached the arm as a tail. Both are true. Neither tells you what to
change, because "the arm threw it away" is five different events:

| class | calls | usd | who owns the repair |
|---|---:|---:|---|
| `used` | 62 | 94.8253 | — |
| `blocks_discarded` | 11 | **35.5789** | `inner/theorize.py` (the beat) |
| `transport_total_loss` | 5 | **13.6544** | `harness/modelcall.py` (the transport) |
| `truncated_theory_fragment` | 1 | **2.7911** | `inner/theorize.py` (the parser) |
| `provider_refusal` | 24 | 0.0000 | — (nothing was billed) |
| `empty` | 1 | 0.7305 | — |

$52.0245 of $147.5803 — 35.3% of the lifetime bill — bought a reply the arm did
not use. The single largest slice is **not** the transport. It is the beat:
11 replies arrived carrying a complete `PLAYBOOK` and between 19 and 31
adjudications each, and the beat discarded every one of them because the
`THEORY` block was missing. The arm asked for three blocks, was sent two, and
kept none.

## The transport discriminator is arithmetic, and the arm always had it

`replyloss` decides on where a reply *starts*, which is right for a human and
wrong for a guard — it cannot see a dropped message whose successor happens to
begin at the marker. The arm's own usage records can. The CLI reports
`usage.output_tokens` for the whole call and `usage.iterations[-1]` for the last
message alone. Across all 103 calls that difference is either **zero or an exact
multiple of 64 000** — the model's own reported `maxOutputTokens`, read from
`modelUsage` in the ledger — with no remainder anywhere. 19 calls dropped a
message; two of them are calls `replyloss` reads as `well_formed`, tails that
happened to resume at `=== THEORY ===`.

That arithmetic is now `harness/replywholeness.py`, it runs on every live call,
and `messages_dropped` is written into `desk_log.json` as the call goes out. A
transport defect visible only to a forensic sweep is a defect that gets paid for
first and found later.

**It returns `None`, not `0`, when the usage block carries no `iterations`.** A
call whose per-message output was never recorded has not been shown to be whole.

## The loop bought the same question 11 times

Every identical re-ask in the archive is labelled `round3`, and the signature is
exact: `compile_errors` for a missing `THEORY` block was a **constant string**,
so attempt 3's prompt was byte-identical to attempt 2's. 11 calls, $9.1993 of
them billed. It came back whole once in three, which is why nobody noticed.

Two changes, in that order: the complaint now varies with what actually
happened, so attempt 3 differs from attempt 2 on its own; and a backstop refuses
to send a prompt this beat has already paid for, rather than paying again.

## What the repaired paths recover, replayed against the archive

`python -m armtools.desk_discard --replay` — zero API calls, the transcripts are
the material.

    kept: 299 adjudications, 10 playbooks, across 12 of the 17 discarded calls
    usd_touched                        $38.3701  of $52.0245 discarded  (73.8%)
    unrecoverable_by_replay            $13.6544  (5 calls)
    identical_reask_usd_not_spent      $ 9.1993
    complaints_that_now_name_the_truncation   17 of 17
    complaints_still_the_old_constant          0

**What that number is not.** It is not a recovered manual. No manual was
recovered and none can be: the front of a truncated reply is not in the
envelope, not in the ledger and not in the transcript. `truncated_theory_fragment`
is read so the arm can say *why* the call failed, and is deliberately **not**
written into `theory.dsl` — a remainder of a manual compiles green over half a
world, which is worse than the refusal it replaces. The five
`transport_total_loss` calls stay lost under any offline repair.

## The cache: the premium is real, and caching is a net loss at any TTL

The A32 brief asked whether the arm still pays the one-hour cache-creation
premium while `cache_read` sits at zero. At n=103 the answer is yes and the
archive says something sharper.

* All 4 058 283 cached tokens this arm has ever written went in at the
  **one-hour** TTL (`ephemeral_1h_input_tokens`); `ephemeral_5m` is 0 on every
  call. One-hour writes bill at 2x base input, five-minute at 1.25x.
* `cache_read` is non-zero on 20 of 103 calls, and **19 of those 20 are the
  multi-message calls**. The read is the second message of a call re-reading
  what the first one wrote. Cross-call reuse has happened at most once, ever.
* The proof that prompt similarity is not the driver: on the R2b g50t leg,
  call 6's prompt shares a 104 155-character prefix with call 5's — 98.8% of it
  — and read **zero** cache, while call 5, whose overlap with call 4 was 10.5%,
  read 47 236 tokens. The CLI writes one breakpoint, at the end of the prompt;
  the arm's prompt differs at its tail every call.

Priced at list rates for `claude-opus-5`, which rebuild the CLI's own
`total_cost_usd` to **0.41%** across the archive ($146.9684 modelled against
$147.5803 billed — the rate table is not allowed to price a counterfactual until
it can do that):

    as billed (1h writes)   $146.9684
    if 5-minute writes      $131.7498      saves $15.2186  (10.3% of the bill)
    if not cached at all    $129.7700      saves $17.1984  (11.7% of the bill)

Caching pays only when reads exceed 1.11x writes at the 1h rate, or 0.28x at
the 5m rate. This archive's ratio is **0.169**. It fails both.

**What is in the arm's control, honestly.** Three of the four levers are not.
`claude -p` documents no flag for cache TTL, for breakpoint placement, or for
disabling caching, so the arm cannot choose the cheaper column through this
transport — that is A28's question (desk through the model proxy), not this
one's. The one lever the arm holds is the token count: the premium is levied per
cached token, and `inner/deskdiet.py`'s `evidence_delta` and `theory_patch`
shrink the prompt. **Both defaulted off on every leg in this archive**, which is
the negative control, and `test_the_diet_knobs_that_are_the_lever_are_still_default_off`
fails if that stops being true so the finding is re-measured rather than
re-quoted.

## Absence recorded as absence

* **The transport repair is not made here.** Reading every assistant message
  needs `--output-format stream-json`, which changes the live CLI invocation.
  It cannot be verified offline against a real CLI, `harness/modelcall.py` is on
  the path of the A26b round running right now, and an unverified change to the
  money path is exactly how $120 gets burned. What landed is the **detector**,
  which is pure arithmetic over records the arm already had. The $13.6544 of
  total loss is therefore still open, and named as open.
* **What the repaired loop would have bought is not measured.** A different
  prompt gets a different reply and there is no reply on disk for a prompt that
  was never sent. The $9.1993 of identical re-asks is reported as spend that
  would not have been made — a floor on the loop's value, not an estimate of it.
* One archived call (`g50t-first-contact-aborted` call 1) read cache without
  being multi-message. It is one call on an aborted leg and is reported as the
  one exception rather than rounded away.
* `theorize.json` covers 5 of R2b-sk48-b's 6 calls; the sixth beat never closed
  because the run ended. The census reads transcripts, not `theorize.json`, so
  it sees all 6 — but the round-level record is short by one and that is why.
* The pre-existing red on master,
  `test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive`, is
  untouched. It is R2b's finding restated by the arm's own guard and belongs to
  the ceiling-ladder ticket, not this one.

## Gate

    cd theoria-arm && python -m pytest -q
    cd theoria-arm && python verify.py

`tests/test_desk_discard.py` is 31 passed. Every claim above has its negative
control in the same block of that file, including one that makes
`armtools/cache_premium.py` report a **saving in the other direction** on a
synthetic archive whose reads clear break-even — a module that always answers
"caching is a net loss" is asserting, not measuring.
