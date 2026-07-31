# Line 1 — World models, the three waves

`Theoria.md` §3.1 reads the world-model literature as three waves and argues that
what each wave actually upgraded was neither the architecture nor the score but
the **verification regime** (检验制度) — the rule by which a model is admitted as
correct. This line is the evidence base for that reading. It is deliberately
larger than the other five, because it has to carry the whole spine of §3.1: Wave I
(the model is weights, checkable only by prediction error or return, and therefore
carrying no inspectable proposition), Wave II (the model is an executable program,
checkable by replaying recorded history, and therefore carrying "true of everything
already experienced"), and the gap that motivates Wave III (no regime here can
certify "true of *everything*" — conservation laws, unsolvability).

Two framing notes on what this line does *not* do. First, Schema is out of scope
here and is not searched for; it is owned separately (`SCHEMA_CITATION.md`), and
`Theoria.md`'s 98.98% / +56pp figures are its own summary of prior work, not a
measurement of ours. Second, the citations at the end of this line —
`agarwal2021deep`, `wang2019benchmarking`, `motamed2026generative` — are not world
models at all. They are included because they are the places where the field itself
says out loud that its verification regime is the weak link: that aggregate scores
over finite runs do not support the comparisons drawn from them, that model-based
RL results were not reproducible across implementations, and that visual realism in
a video model does not imply physical understanding. They are the strongest
*internal* evidence for §3.1's thesis, and they cost the argument nothing, since
each is a complaint the original authors made about their own field.

Every entry below names the two independent sources that agreed on title, year and
venue. Nothing in this line was verified from a single source; what could not reach
two is in the quarantine section at the bottom, with the specific failure named.

---

## Wave I — latent-vector world models

### `ha2018world`

**What it did.** Built generative neural-network models of reinforcement-learning
environments that learn a compressed spatial and temporal representation of the
environment, and trained agents inside that learned model.

**Our delta.** This is the origin point of the regime we are trying to leave: the
model is a set of weights whose only admission test is how well it predicts, so
there is no place inside it where a proposition about the world could be stated,
let alone checked — the manual/playbook split exists precisely to give that
proposition somewhere to live.

`verified:` arXiv API record for `1803.10122` (title "World Models", Ha &
Schmidhuber, submitted 2018-03-27, DOI `10.5281/zenodo.1207631`) **and** the Zenodo
record for `10.5281/zenodo.1207631` (title "World Models", Ha (Google Brain) &
Schmidhuber (NNAISENSE), 2018). *Note: this is the preprint/self-published form —
the peer-reviewed version is the separate entry below, under a different title.*

### `ha2018recurrent`

**What it did.** Trained a generative recurrent network in an unsupervised manner to
model RL environments through compressed spatio-temporal representations, and fed
those extracted features into compact policies trained by evolution.

**Our delta.** The evolved policy is judged only by return, which is the thinnest
verification regime in the three waves — our playbook is required to carry
theorem-level as well as experience-level content, so that a strategy can be wrong
in a way that is *sayable* rather than merely low-scoring.

`verified:` DBLP record `conf/nips/HaS18` (NeurIPS 2018, Ha & Schmidhuber) **and**
the NeurIPS proceedings page for hash `2de5d16682c3c35007e4e92982f1a2ba` (Advances
in Neural Information Processing Systems 31, 2018). *Attribution note: the arXiv
preprint `1809.01999` carries the comment "To appear at NIPS 2018, selected for an
oral presentation"; the widely cited `1803.10122` "World Models" is a different
arXiv record with a different title. Citing the NeurIPS version as "World Models"
is a common error and is avoided here.*

### `hafner2019learning`

**What it did.** Introduced PlaNet, which learns environment dynamics from pixels
and plans in the learned latent space, for control tasks where the dynamics are not
given.

**Our delta.** "Planning in imagination" makes the latent model an object that
search runs against, but nothing about that latent is auditable by a human or a
prover; our engines search against a model that is a written artefact, so the same
search step also produces something a proof obligation can be attached to.

`verified:` arXiv API record for `1811.04551` (title, seven authors, submitted
2018-11-12) **and** DBLP record `conf/icml/HafnerLFVHLD19` (ICML 2019, PMLR 97,
pages 2555–2565).

### `hafner2020dream`

**What it did.** Presented Dreamer, which learns long-horizon behaviours from images
by propagating analytic gradients of learned state values back through trajectories
imagined in the compact latent space of a learned world model.

**Our delta.** Dreamer is the clearest statement of Wave I's ceiling — the imagined
trajectory is the only evidence the agent ever has, and there is no second,
independent check on it; §3.1's Wave III adds exactly that second check (proof) and
a third (active experiment).

`verified:` arXiv API record for `1912.01603` (title, authors Hafner, Lillicrap, Ba,
Norouzi, v3 dated 2020-03-17) **and** the ICLR 2020 official virtual proceedings
page for `S1lOTC4tDS` (International Conference on Learning Representations, 2020).

### `hafner2025mastering`

**What it did.** Presented the third-generation Dreamer, which learns a world model
and improves behaviour by imagining future scenarios, outperforming specialised
methods across over 150 tasks with a single configuration and collecting diamonds in
Minecraft from scratch without human data or curricula.

**Our delta.** This is Wave I at its strongest and it sharpens rather than blunts
§3.1's point: a single configuration generalising across 150 tasks still yields no
statement about any of them that could be checked against anything except more
reward.

`verified:` CrossRef record for DOI `10.1038/s41586-025-08744-2` (Nature 640(8059),
647–653, published 2025-04-02) **and** the PubMed record PMID `40175544` (same
title, journal, volume, issue, pages, DOI). *Attribution note: the arXiv preprint
`2301.04104` is titled "Mastering Diverse Domains through World Models"; the Nature
version is retitled "Mastering diverse control tasks through world models". Both
strings are in circulation and they are the same work.*

### `schrittwieser2020mastering`

**What it did.** Presented MuZero, which combines tree-based search with a learned
model and achieves superhuman performance across Atari, Go, chess and shogi without
being given the rules of the environment.

**Our delta.** MuZero is the sharpest Wave I case for §3.1 because it is the one
that most looks like it has a theory of the game and most clearly does not: the
learned model is optimised only for value, reward and policy prediction, so it can
win a game whose rules it cannot state — which is the exact separation between
胜任 and 理解 that the two-book split is built around.

`verified:` CrossRef record for DOI `10.1038/s41586-020-03051-4` (Nature 588(7839),
604–609, published 2020-12-23, first author Schrittwieser) **and** the arXiv API
record for `1911.08265`, whose metadata carries the same journal DOI and the twelve
-author list.

### `bruce2024genie`

**What it did.** Introduced Genie, an 11B-parameter generative interactive
environment trained unsupervised from unlabelled Internet videos, promptable to
produce action-controllable virtual worlds from text, images, photographs or
sketches.

**Our delta.** Genie is §3.1's "若预测本身就是理解" granted in its strongest form —
the generated world is interactive and convincing frame by frame — and it is exactly
where the paper's reply bites: a world you can walk around in but cannot state a
single conservation law about is a world that has been continued, not understood.

`verified:` arXiv API record for `2402.15391` (title, 24 authors, submitted
2024-02-23) **and** the PMLR proceedings page `v235/bruce24a` (Proceedings of the
41st International Conference on Machine Learning, PMLR 235, pages 4603–4623, 2024).

### `assran2023self`

**What it did.** Introduced I-JEPA, a non-generative joint-embedding predictive
architecture that learns semantic image representations by predicting the
representations of target blocks from a single context block, without hand-crafted
data augmentations.

**Our delta.** JEPA's own premise — that predicting *representations* beats
predicting pixels because pixel detail is not worth predicting — is a concession
that raw prediction error is the wrong test, and Theoria takes the same step one
level further: predict through a named concept, and make the concept, not the
error, the thing that is checked.

`verified:` CrossRef record for DOI `10.1109/cvpr52729.2023.01499` (2023 IEEE/CVF
Conference on Computer Vision and Pattern Recognition, pages 15619–15629, eight
authors incl. LeCun) **and** the arXiv API record for `2301.08243` (same title, same
eight authors, submitted 2023-01-19). *Attribution warning: the arXiv `comments`
field on `2301.08243` reads "2023 IEEE/CVF International Conference on Computer
Vision", i.e. ICCV. This is wrong — CrossRef's IEEE DOI and the CVF open-access page
both place it at CVPR 2023. The author-supplied comment string should not be used as
a venue source.*

### `motamed2026generative`

**What it did.** Built the Physics-IQ benchmark to test whether video generation
models acquire physical principles (fluid dynamics, optics, solid mechanics,
magnetism, thermodynamics) and found physical understanding severely limited across
current models and unrelated to visual realism.

**Our delta.** This is the empirical refutation of Wave I's implicit claim, produced
from inside the video-generation community, and it is the citation that lets §8.1
state "prediction is not understanding" as a measured result rather than as our
assertion — but note that its own regime is still a held-out prediction test, which
is why Theoria adds proof and active experiment rather than a better benchmark.

`verified:` CrossRef record for DOI `10.1109/wacv61042.2026.00099` (2026 IEEE/CVF
Winter Conference on Applications of Computer Vision, pages 948–958) **and** the
arXiv API record for `2501.09038` v3, corroborated by the DataCite record for
`10.48550/arxiv.2501.09038` (same five authors, arXiv, 2025). *Note: the v1 title
circulating on aggregator sites is "Do generative video models learn physical
principles from watching videos?"; the current arXiv title and the WACV title are
"Do generative video models understand physical principles?".*

---

## Wave II — program world models

### `tang2024worldcoder`

**What it did.** Gave a model-based agent that builds a Python program representing
its knowledge of the world from its interactions with the environment, where the
program must explain those interactions while being optimistic about achievable
reward.

**Our delta.** WorldCoder is the wave that makes the model readable, editable and
replayable, and Theoria inherits all of it — the delta is only in what the program
is then obliged to do: WorldCoder's program must *explain the transitions it has
seen*, ours must additionally discharge theorem obligations that quantify over
states it has never seen.

`verified:` arXiv API record for `2402.12275` (title, authors Tang, Key, Ellis,
submitted 2024-02-19) **and** the NeurIPS 2024 proceedings page for hash
`820c61a0cd419163ccbd2c33b268816e` (Advances in Neural Information Processing
Systems 37, Main Conference Track, 2024).

### `hao2023reasoning`

**What it did.** Proposed RAP, which repurposes the LLM itself as a world model and
casts reasoning as planning — running Monte Carlo tree search over the LLM's own
predicted states for plan generation and math, logical and commonsense reasoning.

**Our delta.** RAP puts the world model back inside the weights and the session,
which is precisely the layering failure §3.1 diagnoses (reasoning substrate,
meta-method and world knowledge fused in one place); Theoria's three layers exist so
that the world model is a file that outlives the conversation and can be audited
independently of whoever is reasoning with it.

`verified:` arXiv API record for `2305.14992` (title, seven authors, comment "EMNLP
2023") **and** the ACL Anthology record `2023.emnlp-main.507` (Proceedings of the
2023 Conference on Empirical Methods in Natural Language Processing, Singapore,
December 2023, pages 8154–8173, DOI `10.18653/v1/2023.emnlp-main.507`).

---

## The verification regime, said by the field itself

### `agarwal2021deep`

**What it did.** Showed that deep-RL results reported as point estimates of
aggregate performance over a handful of training runs carry statistical uncertainty
large enough to change published conclusions, and proposed interval estimates,
performance profiles and robust aggregates (e.g. interquartile mean) instead.

**Our delta.** This is the strongest available statement that Wave I's verification
regime does not even support the comparisons already drawn from it, and it is the
direct precedent for §3.1's "分数失去分辨率" — our reply is not a better statistic
but a different kind of admission test, since no confidence interval on a score
turns a score into a proposition.

`verified:` arXiv API record for `2108.13264` (title, five authors, comment
"Outstanding Paper Award at NeurIPS 2021") **and** the NeurIPS proceedings page for
hash `f514cec81cb148559cf475e7426eed5e` (Advances in Neural Information Processing
Systems 34, 2021).

### `wang2019benchmarking`

**What it did.** Benchmarked model-based RL algorithms under a standardised protocol
and reported that research in model-based RL had not been very standardised, with
results not directly comparable across papers.

**Our delta.** Wave II's replay reconciliation is in part a response to exactly this
— a program you can re-run is a result someone else can reproduce — and Theoria
takes the reproducibility demand to its endpoint: the certificate travels with the
artefact and the consumer re-checks it rather than trusting a reported number.

`verified:` arXiv API record for `1907.02057` (title, ten authors, submitted
2019-07-03) **and** the DataCite record for DOI `10.48550/arxiv.1907.02057` (same
title, same ten creators, publisher arXiv, publicationYear 2019, type Preprint).
*This work is arXiv-only in both records — no conference or journal venue was found,
so it is cited as `@misc`.*

---

## Quarantined — not in `01_world_models.bib`

Two works that §3.1 gestures at could not be brought to two independently retrieved
sources. Both are named in `Theoria.md`'s narrative, so the gap is recorded rather
than papered over. Neither has been given a citekey, a year, or an identifier in the
`.bib` file.

### "Video generation models as world simulators" (OpenAI, 2024)

`Theoria.md` §3.1 refers to the "视频模型是否世界模拟器" debate, whose proximate cause
is this OpenAI technical report accompanying Sora.

**What could not be confirmed.** Nothing about it could be retrieved from a primary
source. `https://openai.com/index/video-generation-models-as-world-simulators/`
returned **HTTP 403** to an automated fetch, as did the legacy path
`https://openai.com/research/video-generation-models-as-world-simulators`. The
Internet Archive was not usable as a fallback: the availability API
(`archive.org/wayback/available`) returned `ECONNREFUSED` and `web.archive.org` is
blocked at the harness level. Semantic Scholar returned **HTTP 429** on every
attempt. The only evidence obtained was a search-engine summary asserting the title
and a February 2024 date — one source, and not a retrieval. Consequently the **author
list, the exact publication date, and whether the document carries a stable
identifier are all unconfirmed**, and no `@misc` entry was written, because writing
one would mean inventing at least the date field.

*Recommended next step:* fetch the page manually in a browser and record the byline
and date, then admit it as `@misc` with `howpublished` + `url` + `urldate`. The
debate itself is meanwhile citable through `motamed2026generative`, which states the
question in its abstract and answers it with a benchmark.

### LeCun, "A Path Towards Autonomous Machine Intelligence" (2022)

§3.1 names "JEPA 的预测式路线" as part of Wave I's generative branch; the position
paper is its source document.

**What could not be confirmed.** The work is hosted on OpenReview as a working paper
rather than published at a venue, and OpenReview serves a browser-verification
challenge to automated clients: `openreview.net/forum?id=BZ5a1r-kVsf` returned a
"Verifying your browser" interstitial, and `api.openreview.net/notes?forum=...`
302-redirected to the same challenge. The two fallbacks both failed independently —
DBLP returned `ECONNRESET` on every request after its first two (apparent rate-limit
ban) and Semantic Scholar returned **HTTP 429**. So the **version string (reportedly
v0.9.2), the exact date (reportedly 27 June 2022), and the document's stated venue
field** rest on a single search-engine summary and are unconfirmed.

*Impact on the line: small.* `assran2023self` (I-JEPA, CVPR 2023) carries the JEPA
route into the bibliography with LeCun as a co-author and a fully verified venue, so
§8.1's sentence about JEPA has a real citation available even if the position paper
never clears verification.

---

## Red-line-3 note

No back-off was required. Every query in this line was aimed at an academic index
(arXiv, CrossRef, DataCite, DBLP, PubMed, ACL Anthology, PMLR, NeurIPS/ICLR
proceedings), no result began describing the mechanics of any specific game, and no
ARC game page, walkthrough, leaderboard, harness homepage or trajectory dataset was
opened. Schema was not searched for at any point, per the task boundary. The full
trail is in `../runs/20260728T034703Z-p23/01_world_models/search-log.md`.
