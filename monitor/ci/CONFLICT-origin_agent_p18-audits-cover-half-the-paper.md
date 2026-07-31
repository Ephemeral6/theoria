# CONFLICT-origin_agent_p18-audits-cover-half-the-paper.md
branch: origin/agent/p18-audits-cover-half-the-paper
reason: verify gate red in papers (verify.py)
tip: f5b391965aab429901a5a143a15b8b7864f8a39e
base: d1da2c9ceb4309e602d654e4b2a74dcb8a5ee599
first_seen: 2026-07-30T12:42:07Z
last_seen: 2026-07-30T13:33:55Z
attempts: 2

```
--- cause lines (lifted out of the transcript) ---
   FAIL  phase1-workshop/verify_paper.py exited 1
verify_paper: FAIL (1/7) -- E UNCITED
--- tail of the transcript ---
act them -- one the census's, one this section's own superseded draft -- both sums over the per-pass table above, where each row carries its survey file. Nothing in this block is asserted as a count of anything.
[PASS] F BARE -- no citation is an ambiguous bare filename
  93 bare-filename citations: 0 ambiguous, 4 ruled, 0 stale rulings, 0 line anchors past the end of the file
  ruled     02_framework.md `THEORIZE_LOG.md` (1x) -- Indefinite article, and the next sentence pluralises: 'written down by the LLM in a THEORIZE_LOG.md' / 'Those logs are the primary evidence'. It names the kind of file each arm keeps.
  ruled     02_framework.md `playbook.dsl` (1x) -- Names the *form*, not an instance: the parenthetical points at `CONTRACTS/dsl_grammar_v0.1.md`, which itself uses the bare name for the form (its four sentence types). The contrast is deliberate four lines up, where the manual does get an instance and a scope -- `cold-start-a0/theory/theory.dsl` for A0.
  ruled     10_adjudication.md `ground_truth.json` (1x) -- The token is what is being counted, not what is being cited: '`worldgen/out/worlds/` holds 35 directories with a `ground_truth.json`'. The directory carrying the claim is cited in full; naming one of the 35 would be wrong here.
  ruled     11_limitations.md `theory.dsl` (1x) -- A claim about the v0.1 grammar era, so about every manual written under it, and no single instance is meant. Ten `.dsl` files across four arms carry the comment this sentence is about; the two the section is discussing are `cold-start-a0/theory/theory.dsl:25` and `cold-start-a2/theory/theory.dsl:26`. (An earlier version of this ruling also named `a0-spike/theory/theory.dsl`, which carries the keyword bare and no comment at all -- a ruling whose stated evidence was false, and nothing here would have caught that.)
[PASS] G AUDITSTAMP -- every audit report pins what it audited, correctly
  ok        CITECHECK-2026-07-30.md -- binding on `papers/phase1-workshop/PAPER.md` @ 6b633fcc, 3729 lines, 237872 bytes
  ok        CITECHECK.md -- stale, pinned @ 4208b69c (31.9% of `papers/phase1-workshop/PAPER.md` as it now is), superseded by CITECHECK-2026-07-30.md
  ok        REVIEW-2026-07-30.md -- binding on `papers/phase1-workshop/PAPER.md` @ 6b633fcc, 3729 lines, 237872 bytes
  ok        REVIEW.md -- stale, pinned @ 4208b69c (31.9% of `papers/phase1-workshop/PAPER.md` as it now is), superseded by REVIEW-2026-07-30.md

verify_paper: FAIL (1/7) -- E UNCITED

[3/3] run the suite that shows those gates can go red
   ok    274 passed, 1 xfailed in 17.59s

papers: RED (1 problem(s))

```
