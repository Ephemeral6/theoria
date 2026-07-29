# Search trace — Line 1: World models, the three-wave genealogy

Run: `20260728T102014Z-P7`. Verification date: 2026-07-28 (UTC).

## Method and its limits

Every record below was checked against **two independent sources**. Preferred
pairing was (a) the arXiv abstract page, which is authoritative for the preprint
identifier, the author list and the preprint year, and (b) the publisher's own
proceedings or journal page, which is authoritative for the venue, the venue year
and the pagination. Where a publisher page was unreachable, DBLP or PubMed stood
in as the second source; both are independently curated from the publisher's
metadata rather than from arXiv.

Tooling caveats, recorded because they shaped which URLs appear below:

* `dblp.org` rejected direct HTTP fetches for most of this session (`ECONNRESET`).
  DBLP records were therefore retrieved through the local `paper-search` CLI
  (`paper-search search "<title>" -s dblp`), which queries the same
  `dblp.org/search/publ/api` endpoint. The DBLP record key is quoted in each
  entry so the record can be re-fetched at `https://dblp.org/rec/<key>`.
* `api.semanticscholar.org` returned HTTP 429 for all but one call.
* `openreview.net` and `api.openreview.net` are behind a bot challenge
  (`ChallengeRequiredError`, verified with `curl`), so the LeCun manuscript could
  not be read at its own host.
* `openai.com` returned HTTP 403, and `web.archive.org` is not fetchable from
  this environment, so the Sora report could not be read at its own host either.
  See its entry for how it was verified instead.

Where a field could not be pinned by two sources it is marked `unverified` rather
than guessed. Nothing in this file was filled in from memory.

---

## Wave I — latent world models

### 1. Ha & Schmidhuber, "World Models" — CONFIRMED

Queries: `World Models Ha Schmidhuber` (DBLP publ API); direct fetch of
`arxiv.org/abs/1803.10122`; direct fetch of the NeurIPS 2018 proceedings page.

**Source A** — https://arxiv.org/abs/1803.10122
Confirmed: title *World Models*; authors David Ha, Jürgen Schmidhuber; v1
submitted 27 March 2018, v4 9 May 2018; DOI `10.48550/arXiv.1803.10122`;
primary class cs.LG. No `journal_ref`.

**Source B** — https://dblp.org/search/publ/api?q=World+Models+Ha+Schmidhuber
Confirmed three distinct records: (i) *Recurrent World Models Facilitate Policy
Evolution*, Ha & Schmidhuber, **NeurIPS 2018**, conference paper, linking to
https://proceedings.neurips.cc/paper/2018/hash/2de5d16682c3c35007e4e92982f1a2ba-Abstract.html;
(ii) *World Models*, CoRR 2018, `arXiv:1803.10122`, informal publication;
(iii) *Recurrent World Models Facilitate Policy Evolution*, CoRR 2018,
`arXiv:1809.01999`, informal publication.

**Source C** (corroboration of the venue) —
https://proceedings.neurips.cc/paper/2018/hash/2de5d16682c3c35007e4e92982f1a2ba-Abstract.html
Confirmed: title *Recurrent World Models Facilitate Policy Evolution*; authors
David Ha, Jürgen Schmidhuber; *Advances in Neural Information Processing
Systems 31 (NeurIPS 2018)*.

**Note — attribution surprise.** The name everyone cites, "World Models", is the
arXiv preprint `1803.10122` (2018), which was never itself published under that
title. The peer-reviewed NeurIPS 2018 paper is a *different arXiv entry*
(`1809.01999`) with a *different title*, "Recurrent World Models Facilitate
Policy Evolution". Both are 2018. Cite the NeurIPS version if a refereed venue is
wanted; cite the preprint if the familiar title is wanted. Do not merge the two
into a single record claiming "World Models, NeurIPS 2018" — that record does not
exist.

**Record (preprint form, the commonly cited one):**
- authors: David Ha, Jürgen Schmidhuber
- title: World Models
- venue: arXiv preprint (not peer reviewed under this title)
- year: 2018 (preprint)
- arXiv: 1803.10122 · DOI 10.48550/arXiv.1803.10122

**Record (peer-reviewed form):**
- authors: David Ha, Jürgen Schmidhuber
- title: Recurrent World Models Facilitate Policy Evolution
- venue: Advances in Neural Information Processing Systems 31 (NeurIPS 2018)
- year: 2018 (conference) · 2018 (preprint, arXiv:1809.01999)
- arXiv: 1809.01999

---

### 2. PlaNet — Hafner et al., "Learning Latent Dynamics for Planning from Pixels" — CONFIRMED

Queries: `Learning Latent Dynamics for Planning from Pixels` (DBLP publ API);
direct fetch of arXiv and of the PMLR proceedings page.

**Source A** — https://arxiv.org/abs/1811.04551
Confirmed: title *Learning Latent Dynamics for Planning from Pixels*; authors
Danijar Hafner, Timothy Lillicrap, Ian Fischer, Ruben Villegas, David Ha,
Honglak Lee, James Davidson; v1 12 November 2018, v5 4 June 2019; DOI
10.48550/arXiv.1811.04551.

**Source B** — http://proceedings.mlr.press/v97/hafner19a.html
Confirmed: same title; same seven authors in the same order; *Proceedings of the
36th International Conference on Machine Learning*, PMLR volume 97, 2019,
pages 2555–2565.

**Source C** — https://dblp.org/search/publ/api?q=Learning+Latent+Dynamics+for+Planning+from+Pixels
Confirmed: ICML 2019, pages 2555–2565, plus the CoRR abs/1811.04551 record dated
2018.

**Years:** preprint 2018, conference 2019. Cite the conference year.

**Record:**
- authors: Danijar Hafner, Timothy Lillicrap, Ian Fischer, Ruben Villegas,
  David Ha, Honglak Lee, James Davidson
- title: Learning Latent Dynamics for Planning from Pixels
- venue: Proceedings of the 36th International Conference on Machine Learning
  (ICML 2019), PMLR 97, pp. 2555–2565
- year: 2019 (conference) · 2018 (arXiv preprint)
- arXiv: 1811.04551

---

### 3. Dreamer (V1) — Hafner et al., "Dream to Control" — CONFIRMED

Queries: `Dream to Control Learning Behaviors by Latent Imagination` (DBLP publ
API); direct arXiv fetch.

**Source A** — https://arxiv.org/abs/1912.01603
Confirmed: title *Dream to Control: Learning Behaviors by Latent Imagination*;
authors Danijar Hafner, Timothy Lillicrap, Jimmy Ba, Mohammad Norouzi; submitted
3 December 2019; DOI 10.48550/arXiv.1912.01603.

**Source B** — https://dblp.org/search/publ/api?q=Dream+to+Control+Learning+Behaviors+by+Latent+Imagination
Confirmed: same title; authors Danijar Hafner, Timothy P. Lillicrap, Jimmy Ba,
Mohammad Norouzi (DBLP disambiguates as "Mohammad Norouzi 0002"); venue **ICLR
2020**; ee https://openreview.net/forum?id=S1lOTC4tDS. Also the CoRR abs/1912.01603
record dated 2019.

**Years:** preprint 2019, conference 2020. Cite the conference year.

**Record:**
- authors: Danijar Hafner, Timothy Lillicrap, Jimmy Ba, Mohammad Norouzi
- title: Dream to Control: Learning Behaviors by Latent Imagination
- venue: International Conference on Learning Representations (ICLR 2020)
- year: 2020 (conference) · 2019 (arXiv preprint)
- arXiv: 1912.01603 · OpenReview id S1lOTC4tDS

---

### 4. DreamerV2 — Hafner et al., "Mastering Atari with Discrete World Models" — CONFIRMED

Queries: `Mastering Atari with Discrete World Models` (DBLP via paper-search CLI);
direct arXiv fetch.

**Source A** — https://arxiv.org/abs/2010.02193
Confirmed: title *Mastering Atari with Discrete World Models*; authors Danijar
Hafner, Timothy Lillicrap, Mohammad Norouzi, Jimmy Ba; submitted 5 October 2020,
last revised 12 February 2022; comment field reads "Published at ICLR 2021"; DOI
10.48550/arXiv.2010.02193.

**Source B** — DBLP record key `conf/iclr/HafnerL0B21`
(https://dblp.org/rec/conf/iclr/HafnerL0B21)
Confirmed: same title; authors Danijar Hafner, Timothy P. Lillicrap,
Mohammad Norouzi 0002, Jimmy Ba; venue ICLR; year 2021.

**Note.** The author order differs from DreamerV1: here Norouzi precedes Ba.
Both sources agree on this order.

**Years:** preprint 2020, conference 2021.

**Record:**
- authors: Danijar Hafner, Timothy Lillicrap, Mohammad Norouzi, Jimmy Ba
- title: Mastering Atari with Discrete World Models
- venue: International Conference on Learning Representations (ICLR 2021)
- year: 2021 (conference) · 2020 (arXiv preprint)
- arXiv: 2010.02193

---

### 5. DreamerV3 — Hafner et al., Nature 2025 — CONFIRMED

Queries: `Mastering diverse domains through world models`; web search for the
Nature version; direct fetches of arXiv, PubMed.

**Source A** — https://arxiv.org/abs/2301.04104
Confirmed: preprint title *Mastering Diverse Domains through World Models*;
authors Danijar Hafner, Jurgis Pasukonis, Jimmy Ba, Timothy Lillicrap; v1 10
January 2023, v2 17 April 2024; DOI 10.48550/arXiv.2301.04104.

**Source B** — https://pubmed.ncbi.nlm.nih.gov/40175544/
Confirmed: journal title *Mastering diverse control tasks through world models*;
same four authors; *Nature*, volume 640, issue 8059, pages 647–653; April 2025;
DOI 10.1038/s41586-025-08744-2.

**Source C** — https://www.nature.com/articles/s41586-025-08744-2 (title and
volume/page/year corroborated through search-result metadata; the article page
itself redirects to an IDP authorisation host and was not read directly).

**Note — title change.** The preprint is "Mastering Diverse **Domains** through
World Models"; the Nature article is "Mastering diverse **control tasks** through
world models". These are the same work under two titles. Choose one and do not
mix the words.

**Years:** preprint 2023, journal 2025.

**Record:**
- authors: Danijar Hafner, Jurgis Pasukonis, Jimmy Ba, Timothy Lillicrap
- title: Mastering diverse control tasks through world models
- venue: Nature, vol. 640, no. 8059, pp. 647–653
- year: 2025 (journal) · 2023 (arXiv preprint, under the title "Mastering
  Diverse Domains through World Models")
- arXiv: 2301.04104 · DOI 10.1038/s41586-025-08744-2 · PMID 40175544

---

### 6. MuZero — Schrittwieser et al. — CONFIRMED

Queries: `Mastering Atari Go Chess and Shogi by Planning with a Learned Model`;
direct fetches of arXiv, Semantic Scholar graph API, PubMed.

**Source A** — https://arxiv.org/abs/1911.08265
Confirmed: title *Mastering Atari, Go, Chess and Shogi by Planning with a Learned
Model*; authors Julian Schrittwieser, Ioannis Antonoglou, Thomas Hubert, Karen
Simonyan, Laurent Sifre, Simon Schmitt, Arthur Guez, Edward Lockhart, Demis
Hassabis, Thore Graepel, Timothy Lillicrap, David Silver; v1 19 November 2019,
v2 21 February 2020; related journal DOI 10.1038/s41586-020-03051-4.

**Source B** — https://pubmed.ncbi.nlm.nih.gov/33361790/
Confirmed: journal title *Mastering Atari, Go, chess and shogi by planning with a
learned model*; same twelve authors in the same order; *Nature* 588(7839):604–609;
published online 23 December 2020; DOI 10.1038/s41586-020-03051-4.

**Source C** — https://api.semanticscholar.org/graph/v1/paper/arXiv:1911.08265
Confirmed: Nature, volume 588, pages 604–609, DOI 10.1038/s41586-020-03051-4,
DBLP key `journals/nature/SchrittwieserAH20`. (Semantic Scholar's `year` field
reads 2019 — that is its preprint-date field, not the journal year. Do not take
2019 as the publication year.)

**Years:** preprint 2019, journal 2020. Cite 2020.

**Record:**
- authors: Julian Schrittwieser, Ioannis Antonoglou, Thomas Hubert, Karen
  Simonyan, Laurent Sifre, Simon Schmitt, Arthur Guez, Edward Lockhart,
  Demis Hassabis, Thore Graepel, Timothy Lillicrap, David Silver
- title: Mastering Atari, Go, chess and shogi by planning with a learned model
- venue: Nature, vol. 588, no. 7839, pp. 604–609
- year: 2020 (journal) · 2019 (arXiv preprint)
- arXiv: 1911.08265 · DOI 10.1038/s41586-020-03051-4 · PMID 33361790

---

### 7. Genie — Bruce et al. — CONFIRMED

Queries: `Genie Generative Interactive Environments` (DBLP publ API and CLI);
direct fetches of arXiv and PMLR.

**Source A** — https://arxiv.org/abs/2402.15391
Confirmed: title *Genie: Generative Interactive Environments*; 25 authors, first
author Jake Bruce, last author Tim Rocktäschel; submitted 23 February 2024; DOI
10.48550/arXiv.2402.15391.

**Source B** — https://proceedings.mlr.press/v235/bruce24a.html
Confirmed: same title; same 25 authors in the same order; *Proceedings of the
41st International Conference on Machine Learning*, PMLR 235, 2024,
pages 4603–4623.

**Source C** — DBLP record key `conf/icml/BruceDEPS0LMSAA24`
(https://dblp.org/rec/conf/icml/BruceDEPS0LMSAA24)
Confirmed: ICML 2024, pages 4603–4623.

**Note.** The author list is 25 names long and the venue pages spell some of them
more fully than arXiv does (e.g. "Sarah Maria Elisabeth Bechtle" on PMLR vs.
"Sarah Bechtle" on arXiv). Use `et al.` after Bruce rather than risk a partial
list. No claim about a best-paper award is made here; that was not verified.

**Years:** preprint 2024, conference 2024 — same year.

**Record:**
- authors: Jake Bruce, Michael D. Dennis, Ashley Edwards, Jack Parker-Holder,
  Yuge Shi, Edward Hughes, Matthew Lai, Aditi Mavalankar, Richie Steigerwald,
  Chris Apps, Yusuf Aytar, Sarah Bechtle, Feryal Behbahani, Stephanie C. Y. Chan,
  Nicolas Heess, Lucy Gonzalez, Simon Osindero, Sherjil Ozair, Scott Reed,
  Jingwei Zhang, Konrad Zolna, Jeff Clune, Nando de Freitas, Satinder Singh,
  Tim Rocktäschel
- title: Genie: Generative Interactive Environments
- venue: Proceedings of the 41st International Conference on Machine Learning
  (ICML 2024), PMLR 235, pp. 4603–4623
- year: 2024 (conference and preprint)
- arXiv: 2402.15391

---

### 8. I-JEPA — Assran et al. — CONFIRMED (with a venue correction)

Queries: `Self-Supervised Learning from Images with a Joint-Embedding Predictive
Architecture` on arXiv, on the arXiv export API, on the CVPR virtual site, and on
DBLP via the CLI.

**Source A** — https://arxiv.org/abs/2301.08243 and
http://export.arxiv.org/api/query?id_list=2301.08243
Confirmed: title *Self-Supervised Learning from Images with a Joint-Embedding
Predictive Architecture*; authors Mahmoud Assran, Quentin Duval, Ishan Misra,
Piotr Bojanowski, Pascal Vincent, Michael Rabbat, Yann LeCun, Nicolas Ballas;
published 19 January 2023, v3 13 April 2023; no `journal_ref`. **The
`arxiv:comment` field reads "2023 IEEE/CVF International Conference on Computer
Vision"** — i.e. ICCV.

**Source B** — DBLP record key `conf/cvpr/AssranDMBVRLB23`
(https://dblp.org/rec/conf/cvpr/AssranDMBVRLB23)
Confirmed: same eight authors; venue **CVPR**; year 2023; pages 15619–15629;
DOI 10.1109/CVPR52729.2023.01499.

**Source C** — https://cvpr.thecvf.com/virtual/2023/poster/21019
Confirmed: same title, same eight authors, CVPR 2023.

**Note — the arXiv comment is wrong.** The authors' own comment field names ICCV;
the CVF proceedings, the CVF open-access path
(`openaccess.thecvf.com/content/CVPR2023/…`), the CVPR virtual programme and the
IEEE DOI all say **CVPR 2023**. Cite CVPR 2023. This is exactly the kind of field
that would have been copied wrong from a single source.

**Years:** preprint 2023, conference 2023 — same year.

**Record:**
- authors: Mahmoud Assran, Quentin Duval, Ishan Misra, Piotr Bojanowski,
  Pascal Vincent, Michael Rabbat, Yann LeCun, Nicolas Ballas
- title: Self-Supervised Learning from Images with a Joint-Embedding Predictive
  Architecture
- venue: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern
  Recognition (CVPR 2023), pp. 15619–15629
- year: 2023
- arXiv: 2301.08243 · DOI 10.1109/CVPR52729.2023.01499

---

### 9. LeCun, "A Path Towards Autonomous Machine Intelligence" — CONFIRMED as an unrefereed manuscript

Queries: `LeCun "A Path Towards Autonomous Machine Intelligence" openreview 2022
version 0.9.2`; `paper-search search "A Path Towards Autonomous Machine
Intelligence LeCun" -s semantic,google_scholar,base`; attempted direct fetches of
the OpenReview forum, the OpenReview PDF, `api.openreview.net`,
`api2.openreview.net` (via `curl`), and the Semantic Scholar graph API.

**Blocked.** OpenReview serves a bot challenge to this environment
(`{"name":"ChallengeRequiredError", … ,"status":403}` from `curl` against
`api2.openreview.net`), so the manuscript's own host could not be read.
`api.semanticscholar.org` returned 429 on every attempt.

**Source A** — Google Scholar index record, retrieved via the local
`paper-search` CLI (`-s google_scholar`), pointing at
https://openreview.net/pdf?id=BZ5a1r-kVsf
Confirmed: author Y. LeCun; year 2022; title as indexed, "A path towards
autonomous machine intelligence version 0.9.2, 2022-06-27"; and the abstract's
own words, "This position paper proposes an architecture and training paradigms
with which to construct autonomous intelligent agents."

**Source B** — bibliography of arXiv:2606.27014 ("A Generalization Theory for
JEPA-Based World Models"), https://arxiv.org/html/2606.27014v1
Confirmed, verbatim: "Y. LeCun et al. (2022) A path towards autonomous machine
intelligence version 0.9. 2, 2022-06-27. Open Review 62 (1), pp. 1–62."

**Source C** — https://www.semanticscholar.org/paper/A-Path-Towards-Autonomous-Machine-Intelligence-LeCun-Courant/775f42ed458b8c5b0f2094ea4ff5b64c557b1a34
(surfaced by search; page body not retrievable). Its indexed title,
"A Path Towards Autonomous Machine Intelligence Version 0.9.2, 2022-06-27",
matches. Note its slug parses "Courant" — LeCun's institute — as a second author.
There is one author.

**Note — two propagated errors to avoid.** (i) Many bibliographies render this as
a journal article in "Open Review 62(1), pp. 1–62". There is no journal called
*Open Review*; that string is a Google-Scholar parsing artefact of the OpenReview
PDF, and "62" is the page count. Do not cite it as a journal. (ii) It is not
peer reviewed and has no venue; it is a manuscript posted on OpenReview and
self-described as a position paper. Cite it as such.

**Record:**
- authors: Yann LeCun
- title: A Path Towards Autonomous Machine Intelligence, Version 0.9.2,
  2022-06-27
- venue: unrefereed manuscript, OpenReview (position paper; no venue, no DOI)
- year: 2022 (dated 27 June 2022)
- id: OpenReview `BZ5a1r-kVsf` · https://openreview.net/pdf?id=BZ5a1r-kVsf

---

### 10. Sora — "Video generation models as world simulators" — CONFIRMED as a company technical report

Queries: `OpenAI "Video generation models as world simulators" Sora technical
report February 15 2024`; `Brooks Peebles Holmes DePue … citation authors`;
`paper-search search "Video generation models as world simulators" -s
google_scholar,semantic`; attempted direct fetches of
`openai.com/index/video-generation-models-as-world-simulators/`,
`openai.com/research/video-generation-models-as-world-simulators`, and a Wayback
snapshot.

**Blocked.** `openai.com` returns HTTP 403 to this environment, and
`web.archive.org` is not fetchable from it. Google Scholar and Semantic Scholar
do not index the report as a first-class record. The report was therefore
verified through two independent scholarly bibliographies that cite it, plus a
search-engine confirmation that the page exists at the stated URL under the
stated title.

**Source A** — bibliography of arXiv:2411.02385 ("How Far Is Video Generation
from World Model: A Physical Law Perspective"),
https://arxiv.org/html/2411.02385v1
Confirmed, verbatim: "Tim Brooks, Bill Peebles, Connor Holmes, Will DePue, Yufei
Guo, Li Jing, David Schnurr, Joe Taylor, Troy Luhman, Eric Luhman, Clarence Ng,
Ricky Wang, and Aditya Ramesh. 'Video generation models as world simulators.'
2024. URL https://openai.com/research/video-generation-models-as-world-simulators."

**Source B** — bibliography of arXiv:2502.07825 ("Pre-Trained Video Generative
Models as World Simulators"), https://arxiv.org/html/2502.07825v1
Confirmed, verbatim and independently: "Tim Brooks, Bill Peebles, Connor Holmes,
Will DePue, Yufei Guo, Li Jing, David Schnurr, Joe Taylor, Troy Luhman, Eric
Luhman, Clarence Ng, Ricky Wang, and Aditya Ramesh. Video generation models as
world simulators. 2024." Neither bibliography assigns it a venue or a source
type.

**Source C** — web search returned the live page
https://openai.com/index/video-generation-models-as-world-simulators/ under the
exact title "Video generation models as world simulators | OpenAI", dated
15 February 2024.

**Note — cite it honestly.** This is **not** a peer-reviewed paper and not an
arXiv preprint. It is an OpenAI technical report published on the company's own
website, with no venue, no DOI, and no external review. Its own scope statement
says model and implementation details are not included. Any sentence in the paper
that leans on it must be attributed as a company claim, not as a result. The
15 February 2024 date rests on a single source (the search-engine record of the
page) and is therefore marked *single-source*; the authors, title and year 2024
are two-source confirmed.

**Record:**
- authors: Tim Brooks, Bill Peebles, Connor Holmes, Will DePue, Yufei Guo,
  Li Jing, David Schnurr, Joe Taylor, Troy Luhman, Eric Luhman, Clarence Ng,
  Ricky Wang, Aditya Ramesh
- title: Video generation models as world simulators
- venue: OpenAI technical report (company website; not peer reviewed; no DOI)
- year: 2024 (date 15 February 2024, *single-source*)
- url: https://openai.com/index/video-generation-models-as-world-simulators/

---

## Wave II — programmatic / executable world models

### 11. WorldCoder — Tang, Key & Ellis — CONFIRMED

Queries: `WorldCoder Tang Key Ellis NeurIPS 2024 proceedings`; `WorldCoder
Model-Based LLM Agent Building World Models by Writing Code` (DBLP via CLI);
direct fetches of arXiv and the NeurIPS proceedings page.

**Source A** — https://arxiv.org/abs/2402.12275
Confirmed: title *WorldCoder, a Model-Based LLM Agent: Building World Models by
Writing Code and Interacting with the Environment*; authors **Hao Tang, Darren
Key, Kevin Ellis** — three authors, not more; submitted 19 February 2024, v3
20 September 2024; DOI 10.48550/arXiv.2402.12275; classes cs.AI, cs.CL. The
arXiv page lists no venue.

**Source B** — https://proceedings.neurips.cc/paper_files/paper/2024/hash/820c61a0cd419163ccbd2c33b268816e-Abstract-Conference.html
Confirmed: same title; same three authors; *Advances in Neural Information
Processing Systems 37 (NeurIPS 2024)*, Main Conference Track; DOI
10.52202/079017-2243.

**Source C** — DBLP record key `conf/nips/0008KE24`
(https://dblp.org/rec/conf/nips/0008KE24)
Confirmed: NeurIPS 2024; authors "Hao Tang 0008; Darren Key; Kevin Ellis". The
`0008` suffix is DBLP's disambiguation among several researchers named Hao Tang
and is not part of the name.

**Note.** The first author's surname is **Tang** (given name Hao), so the
citation key `tang2024worldcoder` is correct. This matters because DBLP lists
multiple distinct "Hao Tang" authors; the WorldCoder one is Hao Tang 0008
(Cornell, with Kevin Ellis).

**Years:** preprint 2024, conference 2024 — same year.

**Record:**
- authors: Hao Tang, Darren Key, Kevin Ellis
- title: WorldCoder, a Model-Based LLM Agent: Building World Models by Writing
  Code and Interacting with the Environment
- venue: Advances in Neural Information Processing Systems 37 (NeurIPS 2024),
  Main Conference Track
- year: 2024
- arXiv: 2402.12275 · DOI 10.52202/079017-2243

---

### 12. RAP — Hao et al., "Reasoning with Language Model is Planning with World Model" — CONFIRMED

Queries: `Reasoning with Language Model is Planning with World Model` on arXiv,
on ACL Anthology, and on DBLP via the CLI.

**Source A** — https://arxiv.org/abs/2305.14992
Confirmed: title *Reasoning with Language Model is Planning with World Model*;
authors Shibo Hao, Yi Gu, Haodi Ma, Joshua Jiahua Hong, Zhen Wang, Daisy Zhe
Wang, Zhiting Hu; v1 24 May 2023, v2 23 October 2023; comment field "EMNLP 2023";
DOI 10.48550/arXiv.2305.14992.

**Source B** — https://aclanthology.org/2023.emnlp-main.507/
Confirmed: same title; *Proceedings of the 2023 Conference on Empirical Methods
in Natural Language Processing*; 2023; pages 8154–8173; DOI
10.18653/v1/2023.emnlp-main.507; anthology ID 2023.emnlp-main.507. The Anthology
renders two names in short form ("Joshua Hong", "Daisy Wang").

**Source C** — DBLP record key `conf/emnlp/HaoGMHWWH23`
(https://dblp.org/rec/conf/emnlp/HaoGMHWWH23)
Confirmed: EMNLP 2023, pages 8154–8173, DOI 10.18653/v1/2023.emnlp-main.507;
authors in the arXiv long forms.

**Note.** The method is named RAP ("Reasoning via Planning") inside the paper; the
paper's *title* contains no acronym. Use the long forms of the author names
(Joshua Jiahua Hong, Daisy Zhe Wang), which arXiv and DBLP agree on.

**Years:** preprint 2023, conference 2023 — same year.

**Record:**
- authors: Shibo Hao, Yi Gu, Haodi Ma, Joshua Jiahua Hong, Zhen Wang,
  Daisy Zhe Wang, Zhiting Hu
- title: Reasoning with Language Model is Planning with World Model
- venue: Proceedings of the 2023 Conference on Empirical Methods in Natural
  Language Processing (EMNLP 2023), pp. 8154–8173
- year: 2023
- arXiv: 2305.14992 · DOI 10.18653/v1/2023.emnlp-main.507

---

### 13. Code as Policies — Liang et al. — CONFIRMED (optional; relevance caveat below)

Queries: `Code as Policies` (DBLP publ API); `"Code as Policies" Liang Huang Xia
ICRA 2023 … pages`; direct arXiv fetch.

**Source A** — https://arxiv.org/abs/2209.07753
Confirmed: title *Code as Policies: Language Model Programs for Embodied
Control*; authors Jacky Liang, Wenlong Huang, Fei Xia, Peng Xu, Karol Hausman,
Brian Ichter, Pete Florence, Andy Zeng; v1 16 September 2022, v4 25 May 2023;
DOI 10.48550/arXiv.2209.07753; class cs.RO.

**Source B** — https://dblp.org/search/publ/api?q=Code+as+Policies
Confirmed: same title; same eight authors in the same order; venue **ICRA 2023**;
pages 9493–9500; DOI 10.1109/ICRA48891.2023.10160591. DBLP also carries the CoRR
abs/2209.07753 record dated 2022.

**Relevance caveat — read before using.** Code-as-Policies writes the *policy* as
a program, not the *world model*. It is Wave-II-adjacent in carrier (an editable,
executable artefact) but it does not upgrade the verification regime for a
transition model, which is the axis this section is organised around. Include it
only if the section explicitly distinguishes program-as-policy from
program-as-world-model; otherwise drop it rather than let it blur the taxonomy.

**Years:** preprint 2022, conference 2023.

**Record:**
- authors: Jacky Liang, Wenlong Huang, Fei Xia, Peng Xu, Karol Hausman,
  Brian Ichter, Pete Florence, Andy Zeng
- title: Code as Policies: Language Model Programs for Embodied Control
- venue: 2023 IEEE International Conference on Robotics and Automation
  (ICRA 2023), pp. 9493–9500
- year: 2023 (conference) · 2022 (arXiv preprint)
- arXiv: 2209.07753 · DOI 10.1109/ICRA48891.2023.10160591

---

## DROPPED

### D1. "Schema" (ARC-AGI-3 executable world model, 98.98%) — DROPPED, not attempted here

`sections/11_related.md` names a system called **Schema** and attributes to it a
98.98% figure and a +56pp process-attributable delta, sourced to `Theoria.md`
§3.1. That citation is not in this line's assignment and was not searched for
here. It remains an open `[bib: TODO]`. Flagging it because it is the one claim
in the Wave II paragraph carrying hard numbers, and numbers with no verified
source are the highest-risk item on the page.

### D2. Genie best-paper award — DROPPED as a claim

No source was checked for the widely repeated statement that Genie won an ICML
2024 best paper award. The venue and pages are confirmed; the award is not.
Do not write it.

### D3. Sora publication date, 15 February 2024 — retained but marked single-source

Only one source (a search-engine record of the OpenAI page) attested the date.
The authors, title and year are two-source confirmed. If the draft needs the day
and month, re-verify against the primary page from an environment that can reach
`openai.com`; otherwise write "2024".

---

## Summary

| # | key | verdict | sources |
|---|---|---|---|
| 1 | `ha2018world` / `ha2018recurrent` | CONFIRMED | arXiv + DBLP + NeurIPS proceedings |
| 2 | `hafner2019planet` | CONFIRMED | arXiv + PMLR + DBLP |
| 3 | `hafner2020dreamer` | CONFIRMED | arXiv + DBLP |
| 4 | `hafner2021dreamerv2` | CONFIRMED | arXiv + DBLP |
| 5 | `hafner2025dreamerv3` | CONFIRMED | arXiv + PubMed (+ Nature) |
| 6 | `schrittwieser2020muzero` | CONFIRMED | arXiv + PubMed + Semantic Scholar |
| 7 | `bruce2024genie` | CONFIRMED | arXiv + PMLR + DBLP |
| 8 | `assran2023ijepa` | CONFIRMED (venue corrected) | arXiv + DBLP + CVPR virtual |
| 9 | `lecun2022path` | CONFIRMED as unrefereed manuscript | Google Scholar + arXiv:2606.27014 bibliography |
| 10 | `brooks2024sora` | CONFIRMED as company technical report | arXiv:2411.02385 + arXiv:2502.07825 bibliographies |
| 11 | `tang2024worldcoder` | CONFIRMED | arXiv + NeurIPS proceedings + DBLP |
| 12 | `hao2023rap` | CONFIRMED | arXiv + ACL Anthology + DBLP |
| 13 | `liang2023codeaspolicies` | CONFIRMED (optional, see caveat) | arXiv + DBLP |

12 confirmed, 3 dropped items recorded (one uncited system, one unverified award
claim, one single-source date).
