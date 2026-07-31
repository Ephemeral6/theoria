# Search log — line 1, world models (three waves)

Run `20260728T034703Z-p23`. Every query issued for this line, in order, with the
tool used and what came back. Failures and dead ends are logged too: the point of
this file is that a reader can tell which claims were retrieved and which were not.

**Sources used, and why.** Preference throughout was for machine-readable
registries that are independent of each other: the arXiv API (author-deposited),
CrossRef (publisher-deposited DOIs), DataCite (arXiv's own DOI registrar, distinct
from the arXiv API), PubMed (NLM), DBLP (curated CS bibliography), and primary
proceedings pages (PMLR, ACL Anthology, NeurIPS, ICLR). `WebSearch` was used only
to *locate* a primary page, never as one of the two verifying sources for an
admitted entry.

**Red line 3 status: clean.** No ARC game page, walkthrough, leaderboard,
`schema-harness.github.io`, or ARC-AGI-3 trajectory dataset was opened or
requested. No result began describing the mechanics of any specific game. Schema
was not searched for at any point (owned by a separate agent). No back-off was
required at any step.

---

## 1. Ha & Schmidhuber, and the title split

| # | tool | query / URL | result |
|---|---|---|---|
| 1 | WebFetch | `dblp.org/search/publ/api?q=Recurrent+World+Models+Facilitate+Policy+Evolution` | 3 hits. Target: `conf/nips/HaS18`, NeurIPS 2018, Ha & Schmidhuber; also `journals/corr/abs-1809-01999`. Third hit is a 2021 EPIA *replication* paper ("Revisiting ...") by Esteves & Melo — noted so it is not mistaken for the original. |
| 2 | WebFetch | arXiv API `id_list=1803.10122,1809.01999,1811.04551,1912.01603` | All four resolved. `1803.10122` = "World Models", 2018-03-27, DOI `10.5281/zenodo.1207631`. `1809.01999` = "Recurrent World Models Facilitate Policy Evolution", comment "To appear at NIPS 2018, selected for an oral presentation". Confirms the two arXiv records are distinct works with distinct titles. |
| 28 | WebFetch | `proceedings.neurips.cc/paper/2018/hash/2de5d16682c3c35007e4e92982f1a2ba-Abstract.html` | Confirms "Recurrent World Models Facilitate Policy Evolution", Ha & Schmidhuber, Advances in NeurIPS 31, 2018. Second source for `ha2018recurrent`. |
| 30 | WebFetch | `zenodo.org/records/1207631` | Confirms "World Models", Ha (Google Brain) & Schmidhuber (NNAISENSE), 2018-03-28, DOI `10.5281/zenodo.1207631`. Second source for `ha2018world`. |

**Finding.** The NeurIPS 2018 paper and the arXiv paper called "World Models" are
different records with different titles. Two entries were written, and the line
file flags the common miscitation.

## 2. PlaNet

| # | tool | query / URL | result |
|---|---|---|---|
| 3 | WebFetch | `dblp.org/search/publ/api?q=Learning+Latent+Dynamics+for+Planning+from+Pixels` | **HTTP 500.** Long query string appears to break the endpoint. Retried shorter. |
| 4 | WebFetch | `dblp.org/search/publ/api?q=Latent+Dynamics+Planning+Pixels` | `conf/icml/HafnerLFVHLD19`, ICML 2019, PMLR v97, pages 2555–2565, plus the CoRR record. Second source for `hafner2019learning` (arXiv API from query 2 is the first). |

## 3. Dreamer — four attempts before a usable second source

| # | tool | query / URL | result |
|---|---|---|---|
| 5 | WebFetch | `dblp.org/search/publ/api?q=Dream+to+Control` | Fuzzy-matched to unrelated "Dream*"/"Dreamer*" papers (DeCastro 2024, Koul 2020, DreamArtist, DreamRenderer). Target not returned. |
| 6 | WebFetch | `dblp.org/search/publ/api?q=Latent+Imagination` | `ECONNRESET`. |
| 8 | WebFetch | same, retry | `ECONNRESET`. |
| 9 | WebFetch | Semantic Scholar `/graph/v1/paper/search?query=Dream to Control ...` | **HTTP 429.** |
| 21 | WebSearch | `"Dream to Control" Hafner ICLR 2020 OpenReview forum id conference paper` | Located OpenReview forum id `S1lOTC4tDS`; arXiv abs page. |
| 22 | WebFetch | `openreview.net/forum?id=S1lOTC4tDS` | Served a **"Verifying your browser"** interstitial. No bibliographic data. |
| 24 | WebFetch | `dblp.org/search/publ/api?q=Dream+to+Control+Learning+Behaviors+Latent+Imagination` | `ECONNRESET`. |
| 26 | WebFetch | Semantic Scholar `/graph/v1/paper/arXiv:1912.01603` | **HTTP 429.** |
| 27 | WebFetch | `iclr.cc/virtual_2020/poster_S1lOTC4tDS.html` | **Success.** Title, four authors, "International Conference on Learning Representations (ICLR) 2020". Second source for `hafner2020dream`. |

**Note.** From query 6 onward DBLP returned `ECONNRESET` to every request for the
rest of the run — an apparent rate-limit ban after the two successful calls. Two
entries (`ha2018recurrent`, `hafner2019learning`) had already banked DBLP as a
source before this; nothing after query 5 relies on it.

## 4. MuZero and DreamerV3

| # | tool | query / URL | result |
|---|---|---|---|
| 7 | WebFetch | `dblp.org/search/publ/api?q=Mastering+Atari+Go+Chess+Shogi...` | `ECONNRESET`. |
| 10 | WebFetch | CrossRef `query.bibliographic=Mastering Atari Go chess and shogi by planning with a learned model` | Nature 588(7839):604–609, 2020-12-23, DOI `10.1038/s41586-020-03051-4`, first author Schrittwieser. |
| 11 | WebFetch | arXiv API `id_list=1911.08265,2402.15391,2402.12275,2305.14992,2301.04104` | All five resolved to the expected papers. `1911.08265` metadata carries the Nature DOI — second source for `schrittwieser2020mastering`. `2301.04104` = "Mastering Diverse Domains through World Models" (DreamerV3). |
| 17 | WebSearch | `Hafner DreamerV3 "Mastering diverse" world models Nature 2025 volume pages DOI` | Surfaced `nature.com/articles/s41586-025-08744-2` under a **different title**: "Mastering diverse control tasks through world models". |
| 18 | WebFetch | CrossRef `query.bibliographic=Mastering diverse control tasks through world models Hafner` | Nature 640(8059):647–653, 2025-04-02, DOI `10.1038/s41586-025-08744-2`, four authors matching the preprint. |
| 20 | WebFetch | `pubmed.ncbi.nlm.nih.gov/40175544/` | Same title, journal, volume 640, issue 8059, pages 647–653, DOI, PMID 40175544. Second source for `hafner2025mastering`. |

**Finding.** DreamerV3 was retitled between arXiv ("Diverse Domains") and Nature
("diverse control tasks"). Both strings are in circulation; recorded in the bib
comment so the two are not entered twice.

## 5. Genie and RAP

| # | tool | query / URL | result |
|---|---|---|---|
| 12 | WebSearch | `Genie Generative Interactive Environments ICML 2024 proceedings.mlr.press bruce24` | Located `proceedings.mlr.press/v235/bruce24a.html`. |
| 13 | WebSearch | `"Reasoning with Language Model is Planning with World Model" ACL Anthology EMNLP 2023 pages` | Located `aclanthology.org/2023.emnlp-main.507/`. |
| 14 | WebFetch | `proceedings.mlr.press/v235/bruce24a.html` | PMLR 235, pages 4603–4623, 2024, 24 authors, full BibTeX. Second source for `bruce2024genie`. |
| 15 | WebFetch | `aclanthology.org/2023.emnlp-main.507/` | EMNLP 2023, Singapore, December, ACL, pages 8154–8173, DOI `10.18653/v1/2023.emnlp-main.507`, full BibTeX. Second source for `hao2023reasoning`. |

## 6. WorldCoder

| # | tool | query / URL | result |
|---|---|---|---|
| 16 | WebSearch | `WorldCoder model-based LLM agent Tang Key Ellis NeurIPS 2024 proceedings` | Located the NeurIPS 2024 proceedings hash page. |
| 19 | WebFetch | `proceedings.neurips.cc/paper_files/paper/2024/hash/820c61a0cd419163ccbd2c33b268816e-Abstract-Conference.html` | Full title, Tang/Key/Ellis, "Advances in Neural Information Processing Systems 37 (NeurIPS 2024) Main Conference Track", BibTeX. Second source for `tang2024worldcoder`. |

## 7. JEPA — position paper blocked, I-JEPA recovered

| # | tool | query / URL | result |
|---|---|---|---|
| 23 | WebSearch | `LeCun "A Path Towards Autonomous Machine Intelligence" 2022 OpenReview version 0.9.2 JEPA position paper` | Reports OpenReview forum `BZ5a1r-kVsf`, working paper v0.9.2, 27 June 2022. Search summary only. |
| 25 | WebFetch | `api.openreview.net/notes?forum=BZ5a1r-kVsf` | **302 redirect** to `openreview.net/challenge?redirect=...` — same browser-verification wall as the HTML forum. No data. |
| 41 | WebFetch | `dblp.org/search/publ/api?q=Path+Towards+Autonomous+Machine+Intelligence` | `ECONNRESET`. |
| 33 | WebFetch | arXiv API `id_list=2301.08243,2108.13264,1907.02057` | All three resolved. `2301.08243` = I-JEPA, eight authors incl. LeCun, 2023-01-19. **Its `comments` field reads "2023 IEEE/CVF International Conference on Computer Vision"** — i.e. ICCV. |
| 34 | WebFetch | CrossRef `query.bibliographic=Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture Assran` | **CVPR**, not ICCV: "2023 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)", Vancouver, June 17–24 2023, pages 15619–15629, DOI `10.1109/cvpr52729.2023.01499`. |
| 35 | WebSearch | `"Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture" CVPR 2023 openaccess thecvf pages` | Independently reports CVPR 2023, pages 15619–15629, and the CVF open-access URL — matching CrossRef exactly. |
| 45 | WebFetch | `openaccess.thecvf.com/content/CVPR2023/html/Assran_...CVPR_2023_paper.html` | **HTTP 403** to automated fetch. Not needed: CrossRef + arXiv API already give two retrieved sources for title/authors/year, and CrossRef's publisher-deposited IEEE DOI settles the venue. |

**Finding.** The author-supplied arXiv `comments` field is not a venue source. It
said ICCV; the work is CVPR 2023. Flagged in both the line file and the bib.

**Outcome.** LeCun's position paper → **quarantined** (see line file). I-JEPA →
admitted, and it carries the JEPA route with LeCun as co-author.

## 8. The Sora technical report — quarantined after four routes failed

| # | tool | query / URL | result |
|---|---|---|---|
| 29 | WebSearch | `OpenAI "Video generation models as world simulators" Sora technical report 2024 official page` | Reports the title and February 2024, and gives `openai.com/index/video-generation-models-as-world-simulators/`. Search summary only — no byline, no stable identifier. |
| 31 | WebFetch | `openai.com/index/video-generation-models-as-world-simulators/` | **HTTP 403.** |
| 42 | WebFetch | `openai.com/research/video-generation-models-as-world-simulators` (legacy path) | **HTTP 403.** |
| 32 | WebFetch | `archive.org/wayback/available?url=openai.com/index/video-generation-...` | `ECONNREFUSED`. |
| 39 | WebFetch | `web.archive.org/web/20240301000000*/openai.com/index/...` | Blocked at the harness level ("unable to fetch from web.archive.org"). |
| 40 | WebFetch | Semantic Scholar `/graph/v1/paper/search?query=Video generation models as world simulators` | **HTTP 429.** |

**Outcome.** **Quarantined.** One search-engine summary is not a retrieval and not
two sources. Writing a `@misc` entry would have required inventing at least the
date and the byline. Red line 4 applies by analogy: no identifier is manufactured
for a work that could not be retrieved.

## 9. Replacing Sora's argumentative role with a citable paper

Since §3.1 needs the "是否世界模拟器" *debate* rather than the OpenAI report
specifically, a peer-reviewed paper that states and answers the question was sought.

| # | tool | query / URL | result |
|---|---|---|---|
| 43 | WebSearch | `"Do generative video models understand physical principles" 2025 arXiv Kang Physics-IQ benchmark` | arXiv `2501.09038`; Physics-IQ benchmark; reported as WACV 2026. Note aggregators also list a v1 title, "Do generative video models learn physical principles from watching videos?". |
| 44 | WebFetch | arXiv API `id_list=2501.09038` | v3, current title "Do generative video models understand physical principles?", five authors (Motamed, Culp, Swersky, Jaini, Geirhos), 2025-01-14. Abstract states the debate verbatim: world models vs. "sophisticated pixel predictors that achieve visual realism without understanding". |
| 46 | WebFetch | CrossRef `query.bibliographic=Do generative video models understand physical principles Motamed Geirhos` | 2026 IEEE/CVF WACV, Tucson, March 6–10 2026, pages 948–958, DOI `10.1109/wacv61042.2026.00099`. |
| 47 | WebFetch | DataCite `10.48550/arxiv.2501.09038` | Same title, same five creators, publisher arXiv, publicationYear 2025, type Preprint. Corroborates title/authors independently of the arXiv API. |

**Outcome.** Admitted as `motamed2026generative` (CrossRef + arXiv/DataCite). Note
the my-search-term/actual-author mismatch: the query guessed "Kang" as an author;
the actual authors are Motamed et al. The guess was in the *query*, not in the
record, and the record was taken from the registries.

## 10. Model-based RL evaluation

| # | tool | query / URL | result |
|---|---|---|---|
| 33 | WebFetch | arXiv API (same call as §7) | `2108.13264` = "Deep Reinforcement Learning at the Edge of the Statistical Precipice", five authors, comment "Outstanding Paper Award at NeurIPS 2021". `1907.02057` = "Benchmarking Model-Based Reinforcement Learning", ten authors, 2019-07-03. |
| 36 | WebFetch | DataCite `10.48550/arxiv.1907.02057` | Same title, same ten creators, publisher arXiv, publicationYear 2019, type Preprint. No relatedIdentifiers pointing to a venue → arXiv-only, cited as `@misc`. Second source for `wang2019benchmarking`. |
| 37 | WebSearch | `"Deep Reinforcement Learning at the Edge of the Statistical Precipice" NeurIPS 2021 proceedings.neurips.cc Advances 34` | Located the NeurIPS 2021 proceedings hash page. |
| 38 | WebFetch | `proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html` | Title, five authors, "Advances in Neural Information Processing Systems 34 (NeurIPS 2021)". Second source for `agarwal2021deep`. |

---

## Tally

* **13 entries admitted**, each with two independently retrieved sources named in
  `../../../lines/01_world_models.md`.
* **2 quarantined**: the OpenAI Sora technical report (403 on both OpenAI paths,
  Internet Archive unavailable, Semantic Scholar 429 — never retrieved) and LeCun's
  "A Path Towards Autonomous Machine Intelligence" (OpenReview browser-verification
  wall on both the HTML forum and the API, DBLP banned, Semantic Scholar 429).
* **Infrastructure notes for the next run**: DBLP tolerates roughly two requests
  then `ECONNRESET`s for the remainder of the session — bank it early or not at all.
  Semantic Scholar returned 429 on every attempt across the whole run. OpenReview,
  openai.com and `openaccess.thecvf.com` all reject automated fetches. CrossRef,
  DataCite, the arXiv API, PubMed, PMLR, ACL Anthology and the NeurIPS/ICLR
  proceedings sites were reliable throughout and should be the default pairing.
