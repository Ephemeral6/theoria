# Audit sample A — adversarial re-verification of bibliographic records

**Auditor stance.** Independent adversarial re-verification. I did not read the
original search traces (`line1-world-models.md`, `line3-cegis-ilp.md`,
`line6-llm-theorem-proving.md`) before or during this audit, and I did not use
the drafts' own URLs. Every DOI below was resolved directly against
`api.crossref.org/works/<doi>` or `api.datacite.org`, not against a rendered
citation. Author lists were compared token by token including diacritics and
middle initials.

**Scope.** 20 records sampled from ~37 across the three drafts (≈54%, against a
20% / 8-record floor): 11 from `line1-world-models.md`, 4 from
`line3-cegis-ilp.md`, 5 from `line6-llm-theorem-proving.md`.

**Result.** 19 CLEAN, 1 DEFECT, 0 UNVERIFIABLE, plus 4 advisories that are not
defects but would embarrass the paper if left unexamined.

---

## Why these records

Selection was adversarial, not random. Priority order actually applied:

1. **Records whose draft note admits an ambiguity or a discrepancy** — the place
   a well-meaning researcher guesses. Sampled: `assran2023ijepa` (arXiv says
   ICCV, draft asserts CVPR), `hubert2025alphaproof` (online 2025 vs print 2026),
   `lample2022hypertree` (claims proceedings author order differs from arXiv),
   `hafner2025dreamerv3` (preprint title differs from the Nature title),
   `ha2018world` / `ha2018recurrent` (two ids, two titles, one result).
2. **Unusual author or venue fields.** Sampled: `mathlib2020` (collective author
   `{{The mathlib Community}}`), `solarlezama2008thesis` (PhD thesis + tech-report
   number, no DOI), `lecun2022path` (unrefereed manuscript, no venue, no DOI),
   `brooks2024sora` (company technical report, no venue, no DOI),
   `tang2024worldcoder` (a `10.52202/` DOI — an unfamiliar prefix, exactly the
   shape an invented DOI takes).
3. **System name absent from the stated title.** Sampled: `hubert2025alphaproof`
   ("AlphaProof" not in title), `trinh2024alphageometry` ("AlphaGeometry" not in
   title), `hafner2019planet` ("PlaNet" not in title), `cropper2021popper`-adjacent
   family via `cropper2022ilp30`.
4. **Every record carrying a DOI, page range, volume or issue** — the cheapest
   fields to fabricate. All 20 sampled records carrying such fields had every one
   of them checked.
5. **At least two records the draft presents as fully settled, no caveat.**
   Sampled: `schrittwieser2020muzero`, `mitchell1982generalization`-adjacent set
   (`lau2003vsa`, `muggleton1994ilptheory`, `yang2007arms`),
   `demoura2015lean`, `demoura2021lean4`, `liang2023codeaspolicies`. These carry
   no draft caveat at all and were checked precisely for that reason.

Sources used, all chosen by me: Crossref REST API, DataCite REST API, arXiv
Atom API, ACL Anthology raw BibTeX, CVF Open Access raw BibTeX, PMLR
proceedings pages, NeurIPS official proceedings, PubMed, DBLP
(`dblp.uni-trier.de` mirror), UC Berkeley EECS technical-report registry.

---

# Line 1 — `line1-world-models.md`

## L1-1 · `ha2018world` — **CLEAN**

> David Ha and Jürgen Schmidhuber. *World Models*. arXiv preprint
> arXiv:1803.10122, 2018. DOI 10.48550/arXiv.1803.10122.

Sources:
- `https://api.datacite.org/dois/10.48550/arxiv.1803.10122`
- `https://export.arxiv.org/api/query?id_list=1803.10122`
- `https://doi.org/10.48550/arXiv.1803.10122` (302 → `https://arxiv.org/abs/1803.10122`)

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Ha; Schmidhuber | `Ha, David`; `Schmidhuber, Jürgen` (umlaut present) | ok |
| Title | World Models | World Models | ok |
| Venue | arXiv preprint | publisher `arXiv` | ok |
| Year | 2018 | 2018 | ok |
| DOI | 10.48550/arXiv.1803.10122 | resolves, 302 to the right abs page | ok |

Note (not a defect): the arXiv record also carries an author-supplied DOI
`10.5281/zenodo.1207631`. The draft's arXiv DataCite DOI is the correct one to
cite.

## L1-2 · `ha2018recurrent` — **CLEAN**

> David Ha and Jürgen Schmidhuber. *Recurrent World Models Facilitate Policy
> Evolution*. NeurIPS 31 (2018). arXiv:1809.01999.

Sources:
- `https://proceedings.neurips.cc/paper/2018` (official index; entry at
  `/paper_files/paper/2018/hash/2de5d16682c3c35007e4e92982f1a2ba-Abstract.html`)
- `https://export.arxiv.org/api/query?id_list=1809.01999`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Ha; Schmidhuber | David Ha, Jürgen Schmidhuber | ok |
| Title | Recurrent World Models Facilitate Policy Evolution | identical in proceedings | ok |
| Venue | NeurIPS 31, 2018 | NeurIPS 2018 proceedings; arXiv comment "To appear at NIPS 2018, selected for an oral presentation" | ok |
| Year | 2018 | 2018 | ok |
| arXiv id | 1809.01999 | 1809.01999v1, 2018-09-04 | ok |

The draft's warning that this is a *different title with a different arXiv id*
from `ha2018world` is factually correct; arXiv's own admin note confirms
"substantial text overlap with arXiv:1803.10122".

## L1-3 · `hafner2019planet` — **CLEAN**

> Hafner, Lillicrap, Fischer, Villegas, Ha, Lee, Davidson. *Learning Latent
> Dynamics for Planning from Pixels*. ICML 2019, PMLR 97, pages 2555–2565.
> arXiv:1811.04551 (preprint 2018).

Sources:
- `https://proceedings.mlr.press/v97/hafner19a.html`
- `https://export.arxiv.org/api/query?id_list=1811.04551`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | 7, in the order given | Danijar Hafner, Timothy Lillicrap, Ian Fischer, Ruben Villegas, David Ha, Honglak Lee, James Davidson — identical order | ok |
| Title | Learning Latent Dynamics for Planning from Pixels | identical | ok |
| Venue | ICML 2019 | Proceedings of the 36th ICML | ok |
| Volume | PMLR 97 | PMLR 97 | ok |
| Pages | 2555–2565 | `PMLR 97:2555-2565` | ok |
| Year | 2019 (preprint 2018) | 2019; arXiv v1 2018-11-12 | ok |

Sampled specifically because "PlaNet" is not in the title — the failure mode
where a citation is reconstructed from a system name. It survived.

## L1-4 · `hafner2021dreamerv2` — **CLEAN**

> Hafner, Lillicrap, Norouzi, Ba. *Mastering Atari with Discrete World Models*.
> ICLR 2021. arXiv:2010.02193 (preprint 2020).

Source: `https://export.arxiv.org/api/query?id_list=2010.02193`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Hafner, Lillicrap, Norouzi, Ba | Danijar Hafner, Timothy Lillicrap, Mohammad Norouzi, Jimmy Ba — order matches | ok |
| Title | Mastering Atari with Discrete World Models | identical | ok |
| Venue/Year | ICLR 2021 | arXiv comment: "Published at ICLR 2021" | ok |
| arXiv id | 2010.02193, 2020 | v1 2020-10-05 | ok |

Author order is the trap here (it is *not* the same order as the DreamerV3
record two entries down); the draft has it right in both places.

## L1-5 · `hafner2025dreamerv3` — **CLEAN**

> Hafner, Pasukonis, Ba, Lillicrap. *Mastering diverse control tasks through
> world models*. Nature, 640(8059):647–653, 2025. DOI 10.1038/s41586-025-08744-2.
> Preprint arXiv:2301.04104, 2023, under the title *Mastering Diverse Domains
> through World Models*.

Sources:
- `https://api.crossref.org/works/10.1038/s41586-025-08744-2`
- `https://dblp.uni-trier.de/search/publ/api?q=Mastering+diverse+control+tasks+through+world+models&format=json`
- `https://export.arxiv.org/api/query?id_list=2301.04104`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Hafner, Pasukonis, Ba, Lillicrap | Crossref + DBLP both: Danijar Hafner, Jurgis Pasukonis, Jimmy Ba, Timothy (P.) Lillicrap | ok |
| Title | Mastering diverse control tasks through world models | identical, lowercase as in Nature | ok |
| Venue | Nature | Nature | ok |
| Volume | 640 | 640 | ok |
| Issue | 8059 | 8059 | ok |
| Pages | 647–653 | 647-653 | ok |
| Year | 2025 | issued/online 2025-04-02, print 2025-04-17 | ok |
| DOI | 10.1038/s41586-025-08744-2 | resolves to exactly this record | ok |
| Preprint title | Mastering Diverse Domains through World Models | arXiv 2301.04104v2, 2023-01-10, that exact title | ok |

The draft's flagged title change is real and correctly stated in both directions.

## L1-6 · `schrittwieser2020muzero` — **CLEAN** *(presented as fully settled; sampled for that reason)*

> Schrittwieser, Antonoglou, Hubert, Simonyan, Sifre, Schmitt, Guez, Lockhart,
> Hassabis, Graepel, Lillicrap, Silver. *Mastering Atari, Go, chess and shogi by
> planning with a learned model*. Nature, 588(7839):604–609, 2020.
> DOI 10.1038/s41586-020-03051-4. Preprint arXiv:1911.08265, 2019.

Sources:
- `https://api.crossref.org/works/10.1038/s41586-020-03051-4`
- `https://dblp.uni-trier.de/search/publ/api?q=Mastering+Atari+Go+chess+and+shogi+by+planning+with+a+learned+model&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | 12, in the order given | Crossref and DBLP agree on all 12 names and the order, including Sifre before Schmitt and Graepel before Lillicrap | ok |
| Title | Mastering Atari, Go, chess and shogi by planning with a learned model | identical, including Nature's lowercase "chess and shogi" | ok |
| Venue / Vol / Issue / Pages | Nature 588(7839):604–609 | Nature 588, 7839, 604-609 | ok |
| Year | 2020 | 2020-12-23 online, 2020-12-24 print | ok |
| DOI | 10.1038/s41586-020-03051-4 | resolves to exactly this record | ok |
| Preprint | arXiv:1911.08265, 2019 | DBLP CoRR abs/1911.08265, 2019 | ok |

## L1-7 · `bruce2024genie` — **CLEAN** (one advisory)

> 25 authors. *Genie: Generative Interactive Environments*. ICML 2024, PMLR 235,
> pages 4603–4623, 2024. arXiv:2402.15391.

Sources:
- `https://proceedings.mlr.press/v235/bruce24a.html`
- `https://dblp.uni-trier.de/search/publ/api?q=Genie:+Generative+Interactive+Environments&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | 25, in order | PMLR and DBLP both list 25 in the identical order, Bruce → Rocktäschel | ok |
| Diacritics | Rocktäschel | `Rocktäschel` in both | ok |
| Title | Genie: Generative Interactive Environments | identical | ok |
| Venue / Volume | ICML 2024, PMLR 235 | PMLR 235 | ok |
| Pages | 4603–4623 | 4603–4623 (PMLR), 4603-4623 (DBLP) | ok |
| Year | 2024 | 2024 | ok |
| arXiv id | 2402.15391 | DBLP CoRR abs/2402.15391 | ok |

**Advisory (not a defect).** PMLR's own author list renders two names longer
than the draft does: `Sarah Maria Elisabeth Bechtle` (draft: "Sarah Bechtle")
and `Nando De Freitas` (draft: "Nando de Freitas"). DBLP and arXiv both use the
draft's shorter forms, so the draft is defensible, but if house style is "as
printed in the proceedings" these two entries deviate from the venue of record.

## L1-8 · `assran2023ijepa` — **CLEAN**, and the draft's contested call is **correct**

> Assran, Duval, Misra, Bojanowski, Vincent, Rabbat, LeCun, Ballas.
> *Self-Supervised Learning from Images with a Joint-Embedding Predictive
> Architecture*. CVPR 2023, pages 15619–15629. DOI 10.1109/CVPR52729.2023.01499.
> arXiv:2301.08243.
> Draft note: "the arXiv comment field names ICCV; the proceedings … say CVPR 2023. Cite CVPR."

Sources:
- `https://api.crossref.org/works/10.1109/CVPR52729.2023.01499`
- `https://openaccess.thecvf.com/content/CVPR2023/html/Assran_Self-Supervised_Learning_From_Images_With_a_Joint-Embedding_Predictive_Architecture_CVPR_2023_paper.html` (raw `@InProceedings` block)
- `https://export.arxiv.org/api/query?id_list=2301.08243`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | 8, in order | CVF BibTeX and Crossref agree exactly: Assran, Duval, Misra, Bojanowski, Vincent, Rabbat, LeCun, Ballas | ok |
| Title | …from Images with a Joint-Embedding… | CVF prints "From Images With a" (title case); same string modulo case | ok |
| Venue | CVPR 2023 | Crossref event: *2023 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*; CVF booktitle: same | ok |
| Pages | 15619–15629 | 15619-15629 in both | ok |
| Year | 2023 | 2023-06 | ok |
| DOI | 10.1109/CVPR52729.2023.01499 | resolves to exactly this record | ok |

**The flagged discrepancy is real and the adjudication is right.** I independently
confirmed the arXiv comment field for 2301.08243 reads *"2023 IEEE/CVF
International Conference on Computer Vision"* — i.e. ICCV — while the IEEE DOI
and CVF open-access proceedings both say CVPR. The draft's instruction to cite
CVPR is correct. This is the single most likely place in Line 1 for a
well-meaning researcher to have guessed, and it was not guessed.

## L1-9 · `lecun2022path` — **CLEAN** *(no venue, no DOI — sampled as an unusual-venue record)*

> Yann LeCun. *A Path Towards Autonomous Machine Intelligence, Version 0.9.2,
> 2022-06-27*. Unrefereed manuscript posted on OpenReview, 2022.
> `https://openreview.net/pdf?id=BZ5a1r-kVsf`

Sources (OpenReview itself is Cloudflare-blocked to me; verified indirectly):
- Semantic Scholar record `https://www.semanticscholar.org/paper/A-Path-Towards-Autonomous-Machine-Intelligence-LeCun-Courant/775f42ed458b8c5b0f2094ea4ff5b64c557b1a34`
- Independent web index confirming the artefact at `openreview.net/pdf?id=BZ5a1r-kVsf`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Author | Yann LeCun | Yann LeCun | ok |
| Title incl. version string | "…, Version 0.9.2, 2022-06-27" | identical, version string is part of the title of record | ok |
| Venue | none (unrefereed manuscript on OpenReview) | no venue found in any index | ok |
| DOI | none asserted | none exists | ok |
| Year | 2022 | 2022 | ok |
| OpenReview id | BZ5a1r-kVsf | BZ5a1r-kVsf | ok |

**The draft's warning about the "Open Review 62(1), pp. 1–62" artefact is
corroborated.** The Semantic Scholar record for this manuscript itself carries a
parsing artefact — its slug renders the author as "LeCun-Courant", i.e. it has
absorbed the affiliation line ("Courant Institute") into the author field. This
is exactly the class of indexing corruption the draft tells the writer not to
copy, and it confirms the draft was looking at the real record rather than a
downstream one.

## L1-10 · `brooks2024sora` — **CLEAN**, with a source caveat

> Brooks, Peebles, Holmes, DePue, Guo, Jing, Schnurr, Taylor, T. Luhman,
> E. Luhman, Ng, Wang, Ramesh. *Video generation models as world simulators*.
> OpenAI technical report, 2024.

Source: independent third-party citations of the report; the primary page
`https://openai.com/index/video-generation-models-as-world-simulators/`
returned **HTTP 403** to me and I could not read it directly.

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | 13, in order | corroborated as the same 13 in the same order, incl. the Luhman pair (Troy then Eric) | ok (secondary) |
| Title | Video generation models as world simulators | identical | ok |
| Venue | OpenAI technical report, no venue, no DOI | no venue or DOI found anywhere | ok |
| Year | 2024 | 2024 | ok |

**Advisory.** The canonical OpenAI URL for this report has migrated between
`/research/…` and `/index/…` forms; the draft uses `/index/…`, which is the
current one. Because I could not open the primary page, the author list is
confirmed to secondary-source standard only. Every field the draft asserts is
consistent across those sources and nothing is contradicted. The draft's
insistence that this be attributed as *company claims, never as results* is the
right call for a 403-walled, unrefereed corporate artefact.

## L1-11 · `tang2024worldcoder` — **CLEAN** (one advisory)

> Hao Tang, Darren Key, Kevin Ellis. *WorldCoder, a Model-Based LLM Agent:
> Building World Models by Writing Code and Interacting with the Environment*.
> NeurIPS 37 (2024). arXiv:2402.12275. DOI 10.52202/079017-2243.

Sources:
- `https://api.crossref.org/works/10.52202/079017-2243`
- `https://proceedings.neurips.cc/paper_files/paper/2024/hash/820c61a0cd419163ccbd2c33b268816e-Abstract-Conference.html`
- `https://export.arxiv.org/api/query?id_list=2402.12275`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Tang; Key; Ellis | Hao Tang, Darren Key, Kevin Ellis (Crossref and arXiv) | ok |
| Title | full string incl. subtitle | byte-identical in Crossref and arXiv | ok |
| Venue | NeurIPS 37 (2024) | Crossref container: *Advances in Neural Information Processing Systems 37*, publisher NeurIPS Foundation; official proceedings page confirms main track | ok |
| Year | 2024 | 2024 | ok |
| DOI | 10.52202/079017-2243 | **resolves**, registered by the NeurIPS Foundation | ok |
| arXiv id | 2402.12275 | 2402.12275v3, 2024-02-19 | ok |

I sampled this because a `10.52202/` prefix looks like the shape of an invented
DOI. It is not — 10.52202 is the legitimate proceedings-registration prefix and
the DOI resolves to exactly this paper.

**Advisory.** Crossref records pages **70148–70212** for this entry. The draft
gives no page range, which is not wrong, but if the bibliography style wants
pages for NeurIPS entries, that is the value.

## L1-12 · `hao2023rap` — **DEFECT** *(author list)*

> Shibo Hao, Yi Gu, Haodi Ma, **Joshua Jiahua Hong**, Zhen Wang, **Daisy Zhe
> Wang**, Zhiting Hu. *Reasoning with Language Model is Planning with World
> Model*. EMNLP 2023, pages 8154–8173. DOI 10.18653/v1/2023.emnlp-main.507.
> arXiv:2305.14992.

Sources:
- `https://api.crossref.org/works/10.18653/v1/2023.emnlp-main.507`
- `https://aclanthology.org/2023.emnlp-main.507.bib` (raw BibTeX from the
  proceedings of record)

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Hao; Gu; Ma; **Joshua Jiahua Hong**; Zhen Wang; **Daisy Zhe Wang**; Hu | ACL Anthology BibTeX: `Hong, Joshua` and `Wang, Daisy`. Crossref: `Joshua Hong`, `Daisy Wang`. Both independent sources agree, and neither contains a middle name. | **DEFECT** |
| Title | Reasoning with Language Model is Planning with World Model | identical | ok |
| Venue | EMNLP 2023 | Proceedings of the 2023 Conference on EMNLP, ACL, Singapore, Dec 2023 | ok |
| Pages | 8154–8173 | `pages = "8154--8173"` in the Anthology BibTeX; `8154-8173` in Crossref | ok |
| Year | 2023 | 2023 | ok |
| DOI | 10.18653/v1/2023.emnlp-main.507 | resolves to exactly this record | ok |

**Correct value.** For a citation of the EMNLP proceedings version, the author
list is:

> Shibo Hao, Yi Gu, Haodi Ma, **Joshua Hong**, Zhen Wang, **Daisy Wang**,
> Zhiting Hu.

**Diagnosis.** The draft cites the *proceedings* (venue, pages and DOI are all
the Anthology's) but has imported the *arXiv* author forms, where the same two
authors appear as "Joshua Jiahua Hong" and "Daisy Zhe Wang". This is a
cross-version contamination, not an invention — the people are right — but it is
a real mismatch with the record being cited, and it is exactly the field the
brief asked to be checked character by character. Severity: low. Fix: either
drop the middle names to match the proceedings, or cite the arXiv version and
keep them.

## L1-13 · `liang2023codeaspolicies` — **CLEAN** *(presented with no bibliographic caveat)*

> Liang, Huang, Xia, Xu, Hausman, Ichter, Florence, Zeng. *Code as Policies:
> Language Model Programs for Embodied Control*. ICRA 2023, pages 9493–9500.
> DOI 10.1109/ICRA48891.2023.10160591. arXiv:2209.07753 (preprint 2022).

Sources:
- `https://api.crossref.org/works/10.1109/ICRA48891.2023.10160591`
- `https://dblp.uni-trier.de/search/publ/api?q=Code+as+Policies&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | 8, in order | Crossref and DBLP both: Jacky Liang, Wenlong Huang, Fei Xia, Peng Xu, Karol Hausman, Brian Ichter, Pete Florence, Andy Zeng | ok |
| Title | Code as Policies: Language Model Programs for Embodied Control | identical | ok |
| Venue | ICRA 2023 | *2023 IEEE International Conference on Robotics and Automation (ICRA)* | ok |
| Pages | 9493–9500 | 9493-9500 in both | ok |
| Year | 2023 (preprint 2022) | 2023-05-29; DBLP CoRR abs/2209.07753 dated 2022 | ok |
| DOI | 10.1109/ICRA48891.2023.10160591 | resolves to exactly this record | ok |

---

# Line 3 — `line3-cegis-ilp.md`

## L3-C1 · `solarlezama2006sketching` — **CLEAN**

> Solar-Lezama, Tancau, Bodík, Seshia, Saraswat. "Combinatorial Sketching for
> Finite Programs." ASPLOS XII, pages 404–415, ACM, 2006.
> DOI 10.1145/1168857.1168907.

Sources:
- `https://api.crossref.org/works/10.1145/1168857.1168907`
- `https://dblp.uni-trier.de/search/publ/api?q=Combinatorial+sketching+for+finite+programs&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Solar-Lezama; Tancau; **Bodík**; Sanjit A. Seshia; Vijay A. Saraswat | DBLP: `Rastislav Bodík` (caron present), `Sanjit A. Seshia`, `Vijay A. Saraswat` — matches the draft exactly, initials included | ok |
| Title | Combinatorial Sketching for Finite Programs | Crossref lowercases ("Combinatorial sketching for finite programs"); same words | ok |
| Venue | ASPLOS XII, 12th intl. conf. | Crossref event `ASPLOS06`, container "Proceedings of the 12th international conference on Architectural support for programming languages and operating systems" | ok |
| Pages | 404–415 | 404-415 in both | ok |
| Year | 2006 | 2006-10-20 | ok |
| DOI | 10.1145/1168857.1168907 | resolves to exactly this record | ok |

Note: Crossref strips the diacritic to "Bodik". DBLP and the author's own usage
keep "Bodík". The draft's form is the correct one.

## L3-C2 · `solarlezama2008thesis` — **CLEAN** *(unusual venue: thesis + tech report, no DOI)*

> Armando Solar-Lezama. *Program Synthesis by Sketching.* PhD thesis, University
> of California, Berkeley, 2008. Technical report UCB/EECS-2008-176.

Source: UC Berkeley EECS technical-report registry,
`https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-176.html`
(read the page's own BibTeX and EndNote blocks, not a third-party rendering).

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Author | Armando Solar-Lezama | registry renders `Solar Lezama, Armando` (their system drops the hyphen); the person is Armando Solar-Lezama | ok |
| Title | Program Synthesis by Sketching | registry: "Program Synthesis By Sketching" — capitalisation only | ok |
| Type | PhD thesis | registry text: "this thesis shows that sketching is a viable approach…"; filed under EECS Ph.D. Dissertations | ok |
| Institution | University of California, Berkeley | EECS Department, University of California, Berkeley | ok |
| Report number | UCB/EECS-2008-176 | `Number = {UCB/EECS-2008-176}` | ok |
| Year | 2008 | 2008, December 19 | ok |
| DOI | none asserted | none exists | ok |

Sampled because a tech-report number is a five-token string with no checksum —
the easiest thing in a bibliography to get wrong and the hardest to notice. It
is exactly right, including the `UCB/` prefix.

## L3-C5 · `lau2003vsa` — **CLEAN**

> Tessa Lau, Steven A. Wolfman, Pedro Domingos, Daniel S. Weld. "Programming by
> Demonstration Using Version Space Algebra." *Machine Learning* 53(1–2):111–156,
> 2003. DOI 10.1023/A:1025671410623.

Sources:
- `https://api.crossref.org/works/10.1023/A:1025671410623`
- `https://dblp.uni-trier.de/search/publ/api?q=Programming+by+Demonstration+Using+Version+Space+Algebra&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Tessa Lau; Steven A. Wolfman; Pedro Domingos; Daniel S. Weld | Crossref: identical strings. DBLP normalises to "Tessa A. Lau"/"Pedro M. Domingos"; the article as published uses the draft's forms | ok |
| Title | Programming by Demonstration Using Version Space Algebra | identical | ok |
| Venue | Machine Learning | Machine Learning | ok |
| Volume | 53 | 53 | ok |
| Issue | 1–2 | `1-2` in both | ok |
| Pages | 111–156 | 111-156 in both | ok |
| Year | 2003 | 2003-10 | ok |
| DOI | 10.1023/A:1025671410623 | resolves; the `A:` colon-style legacy Springer DOI is genuine | ok |

The colon-bearing legacy Springer DOI is a classic mistranscription target. It
is correct.

## L3-C7 · `muggleton1994ilptheory` — **CLEAN** *(unusual volume field)*

> Stephen Muggleton and Luc De Raedt. "Inductive Logic Programming: Theory and
> Methods." *The Journal of Logic Programming* 19–20:629–679, 1994.
> DOI 10.1016/0743-1066(94)90035-3.

Sources:
- `https://api.crossref.org/works/10.1016/0743-1066(94)90035-3`
- `https://dblp.uni-trier.de/search/publ/api?q=Inductive+Logic+Programming:+Theory+and+Methods&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Muggleton; **De Raedt** | DBLP: `Luc De Raedt` (capital D, as printed). Crossref lowercases to "de Raedt". Draft matches the published form | ok |
| Title | Inductive Logic Programming: Theory and Methods | Crossref: "Inductive Logic Programming: Theory and methods" — case only | ok |
| Venue | The Journal of Logic Programming | The Journal of Logic Programming | ok |
| Volume | **19–20** | Crossref `volume: 19-20`; DBLP `19/20` — the combined double volume is real, not a typo for a page range | ok |
| Issue | none given | none exists | ok |
| Pages | 629–679 | 629-679 in both | ok |
| Year | 1994 | 1994-05 | ok |
| DOI | 10.1016/0743-1066(94)90035-3 | resolves to exactly this record | ok |

Sampled because "19–20" in a volume field is the shape of an error. It is
correct: this is a genuine combined volume.

## L3-C11 · `yang2007arms` — **CLEAN** *(system name absent from title)*

> Qiang Yang, Kangheng Wu, Yunfei Jiang. "Learning Action Models from Plan
> Examples Using Weighted MAX-SAT." *Artificial Intelligence* 171(2–3):107–143,
> 2007. DOI 10.1016/j.artint.2006.11.005.

Sources:
- `https://api.crossref.org/works/10.1016/j.artint.2006.11.005`
- `https://dblp.uni-trier.de/search/publ/api?q=Learning+action+models+from+plan+examples+using+weighted+MAX-SAT&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Yang; Wu; Jiang | Qiang Yang, Kangheng Wu, Yunfei Jiang in both | ok |
| Title | as drafted | identical (Crossref lowercases) | ok |
| Venue | Artificial Intelligence | Artificial Intelligence | ok |
| Volume / Issue | 171(2–3) | 171, `2-3` in both | ok |
| Pages | 107–143 | 107-143 in both | ok |
| Year | 2007 | 2007-02 | ok |
| DOI | 10.1016/j.artint.2006.11.005 | resolves to exactly this record | ok |

Sampled because the draft calls the system **ARMS** while "ARMS" does not appear
in the title — the pattern that produces reconstructed citations. It survived.

## L3-C8 · `cropper2022ilp30` — **CLEAN**

> Andrew Cropper and Sebastijan Dumančić. "Inductive Logic Programming At 30: A
> New Introduction." *JAIR* 74:765–850, 2022. DOI 10.1613/jair.1.13507.

Sources:
- `https://api.crossref.org/works/10.1613/jair.1.13507`
- `https://dblp.uni-trier.de/search/publ/api?q=Inductive+Logic+Programming+At+30&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Cropper; **Dumančić** | Crossref: `Sebastijan Dumančić` — both carons present and in the right places. (DBLP ASCII-folds to "Dumancic".) | ok |
| Title | Inductive Logic Programming At 30: A New Introduction | identical, including the unusual capital "At" | ok |
| Venue | Journal of Artificial Intelligence Research | JAIR | ok |
| Volume | 74 | 74 | ok |
| Pages | 765–850 | 765-850 in both | ok |
| Year | 2022 | 2022-06-15 | ok |
| DOI | 10.1613/jair.1.13507 | resolves; the `jair.1.` infix is the genuine JAIR pattern | ok |

Note: the arXiv preprint (abs/2008.07912) is from 2020 and titled in sentence
case; the draft correctly cites the 2022 journal version.

---

# Line 6 — `line6-llm-theorem-proving.md`

## L6-1 · `demoura2015lean` — **CLEAN** *(presented as fully settled)*

> de Moura, Kong, Avigad, van Doorn, von Raumer. *The Lean Theorem Prover (System
> Description)*. CADE-25, LNCS, Springer, pages 378–388, 2015.
> DOI 10.1007/978-3-319-21401-6_26.

Sources:
- `https://api.crossref.org/works/10.1007/978-3-319-21401-6_26`
- `https://dblp.uni-trier.de/search/publ/api?q=The+Lean+Theorem+Prover+System+Description&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | de Moura, Kong, Avigad, van Doorn, von Raumer | Crossref: `Leonardo de Moura; Soonho Kong; Jeremy Avigad; Floris van Doorn; Jakob von Raumer`. DBLP: same, with "Leonardo Mendonça de Moura". Particles `van`/`von` lowercase in both | ok |
| Title | The Lean Theorem Prover (System Description) | identical, parenthetical included | ok |
| Venue | Automated Deduction — CADE-25, LNCS, Springer | Crossref: LNCS / *Automated Deduction - CADE-25*, Springer International Publishing | ok |
| Pages | 378–388 | 378-388 in both | ok |
| Year | 2015 | 2015 (online 2015-07-25) | ok |
| DOI | 10.1007/978-3-319-21401-6_26 | resolves to exactly this record | ok |

## L6-2 · `demoura2021lean4` — **CLEAN** *(presented as fully settled)*

> de Moura and Ullrich. *The Lean 4 Theorem Prover and Programming Language*.
> CADE 28, LNCS, Springer, pages 625–635, 2021.
> DOI 10.1007/978-3-030-79876-5_37.

Sources:
- `https://api.crossref.org/works/10.1007/978-3-030-79876-5_37`
- `https://dblp.uni-trier.de/search/publ/api?q=The+Lean+4+Theorem+Prover+and+Programming+Language&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | de Moura; Ullrich | `Leonardo de Moura; Sebastian Ullrich` in both | ok |
| Title | The Lean 4 Theorem Prover and Programming Language | identical | ok |
| Venue | Automated Deduction — CADE 28, LNCS, Springer | Crossref: LNCS / *Automated Deduction – CADE 28*; DBLP venue CADE | ok |
| Pages | 625–635 | 625-635 in both | ok |
| Year | 2021 | 2021 (online 2021-07-05) | ok |
| DOI | 10.1007/978-3-030-79876-5_37 | resolves to exactly this record | ok |

Note the draft correctly reproduces the venue-string inconsistency between the
two Springer volumes ("CADE-25" hyphenated, "CADE 28" spaced) rather than
regularising them. That is right; those are the printed forms.

## L6-3 · `mathlib2020` — **CLEAN** *(collective author — sampled for that reason)*

> `{The mathlib Community}`. *The Lean Mathematical Library*. CPP 2020 (9th ACM
> SIGPLAN Intl. Conf. on Certified Programs and Proofs), ACM, pages 367–381,
> 2020. DOI 10.1145/3372885.3373824.

Sources:
- `https://api.crossref.org/works/10.1145/3372885.3373824`
- `https://export.arxiv.org/api/query?id_list=1910.09336` (arXiv preprint, which
  carries the same DOI in its metadata)
- `https://dblp.uni-trier.de/search/publ/api?q=The+Lean+Mathematical+Library&format=json`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Author | collective, `{{The mathlib Community}}` | Crossref stores a single `name` entry: `The mathlib Community`. arXiv `<name>`: `The mathlib Community` — single author element, byte-identical | ok |
| Title | The Lean Mathematical Library | arXiv: "The Lean mathematical library"; ACM/Crossref lowercase it. Same words | ok |
| Venue | CPP 2020, ACM | Crossref container: *Proceedings of the 9th ACM SIGPLAN International Conference on Certified Programs and Proofs*; DBLP venue `CPP` | ok |
| Pages | 367–381 | 367-381 in Crossref and DBLP | ok |
| Year | 2020 | 2020-01-20 | ok |
| DOI | 10.1145/3372885.3373824 | resolves to exactly this record; arXiv's own metadata declares the same DOI | ok |

**Advisory (not a defect).** Crossref's `event.name` for this DOI is
`POPL '20: 47th Annual ACM SIGPLAN Symposium on Principles of Programming
Languages` — an artefact of CPP 2020 being co-located with POPL 2020. The
`container-title` is the correct CPP proceedings. Anyone re-checking this record
against Crossref's *event* field alone would wrongly conclude the venue is POPL.
The draft has it right; the note is here so the next auditor does not "correct"
it.

The draft's instruction that the collective author *must stay double-braced* is
correct and load-bearing — undoubled, BibTeX would parse "Community" as a
surname.

## L6-4 · `hubert2025alphaproof` — **CLEAN**, with a consistency advisory

> Hubert, Mehta, Sartran, and others. *Olympiad-level formal mathematical
> reasoning with reinforcement learning*. Nature, 651(8106):607–613, 2025.
> DOI 10.1038/s41586-025-09833-y. Note: online 12 Nov 2025; print March 2026.
> Draft claims a 39-author list and that "AlphaProof" is not in the title.

Sources:
- `https://api.crossref.org/works/10.1038/s41586-025-09833-y`
- `https://pubmed.ncbi.nlm.nih.gov/?term=10.1038%2Fs41586-025-09833-y` (PMID 41225005, PMCID PMC12999475)

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors (first three) | Hubert, Mehta, Sartran | `Thomas Hubert; Rishi Mehta; Laurent Sartran` — first three, in that order, in both sources | ok |
| Author count | "The full 39-author list" | Crossref returns exactly **39** author entries; PubMed lists the same 39 | ok |
| Diacritics in the tail | (draft defers to trace) | Crossref: `Miklós Z. Horváth`, `Goran Žužić`, `Calle Sönne`, `Ingrid von Glehn` — all present and matched by PubMed | ok |
| Title | Olympiad-level formal mathematical reasoning with reinforcement learning | identical in both; **"AlphaProof" indeed does not appear** | ok |
| Venue | Nature | Nature | ok |
| Volume | 651 | 651 in both | ok |
| Issue | 8106 | 8106 in both | ok |
| Pages | 607–613 | 607-613 (Crossref), 607–613 (PubMed) | ok |
| Year | 2025 | **online 2025-11-12, print 2026-03-19** — both confirmed | ok, see advisory |
| DOI | 10.1038/s41586-025-09833-y | resolves to exactly this record | ok |
| "no arXiv id should be invented" | — | I found no arXiv id for this paper | ok |

This was my single highest-suspicion record — a Nature volume/issue/page triple
plus a 39-author claim plus a flagged year ambiguity, all in one entry. Every
field is exactly right, including the count.

**Advisory (worth an editorial decision before submission).** The draft's own
note says "pick one deliberately", but the BibTeX then sets `year = {2025}`
while carrying `volume = 651`, `number = 8106`, `pages = 607--613` — which are
the coordinates of the **print** issue. PubMed indexes the record as
**2026;651(8106):607-613**; Crossref's `issued` date is 2025-11-12. Both are
defensible, but the entry as written mixes the online year with the print
issue's locators. Either set `year = {2026}` to match the volume/issue/pages, or
keep 2025 and add an explicit "advance online publication" note. Right now the
deliberate pick the draft asks for has not visibly been made.

## L6-5 · `trinh2024alphageometry` — **CLEAN** *(system name absent from title)*

> Trinh, Wu, Le, He, Luong. *Solving olympiad geometry without human
> demonstrations*. Nature, 625(7995):476–482, 2024.
> DOI 10.1038/s41586-023-06747-5.

Sources:
- `https://api.crossref.org/works/10.1038/s41586-023-06747-5`
- `https://pubmed.ncbi.nlm.nih.gov/?term=10.1038%2Fs41586-023-06747-5`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Authors | Trieu H. Trinh; Yuhuai Wu; Quoc V. Le; He He; Thang Luong | Crossref: identical with initials. PubMed: same five, PubMed style drops the periods | ok |
| Title | Solving olympiad geometry without human demonstrations | identical, lowercase "olympiad" as Nature prints it; **"AlphaGeometry" indeed absent** | ok |
| Venue | Nature | Nature | ok |
| Volume | 625 | 625 in both | ok |
| Issue | 7995 | 7995 in both | ok |
| Pages | 476–482 | 476-482 in both | ok |
| Year | 2024 | online 2024-01-17, print 2024-01-18 — no ambiguity here | ok |
| DOI | 10.1038/s41586-023-06747-5 | resolves to exactly this record. **Note the `-023-` infix on a 2024 paper** — correct, not a typo: Nature DOIs carry the submission-year stamp | ok |

The `10.1038/s41586-**023**-06747-5` / year 2024 pairing is precisely the kind of
apparent mismatch that invites a well-meaning "correction" to `-024-`. It must
not be changed.

## L6-6 · `lample2022hypertree` — **CLEAN**, and the draft's author-order claim is **confirmed**

> Lample, Lacroix, Lachaux, Rodriguez, Hayat, Lavril, Ebner, Martinet.
> *HyperTree Proof Search for Neural Theorem Proving*. NeurIPS 35 (2022).
> arXiv:2205.11491.
> Draft note: "Author order follows the proceedings, which differs from arXiv."

Sources:
- `https://proceedings.neurips.cc/paper_files/paper/2022/hash/a8901c5e85fb8e1823bbf0f755053672-Abstract-Conference.html`
- `https://export.arxiv.org/api/query?id_list=2205.11491`

| Field | Drafted | Verified | Verdict |
|---|---|---|---|
| Author order | Lample, Lacroix, Lachaux, Rodriguez, Hayat, Lavril, Ebner, Martinet | NeurIPS proceedings: **Lample, Lacroix, Lachaux, Rodriguez, Hayat, Lavril, Ebner, Martinet** — identical | ok |
| Diacritics | `Timoth{\'e}e`, `Aur{\'e}lien` | proceedings render ASCII; arXiv gives `Timothée Lacroix`, `Aurélien Rodriguez` — the draft's accented forms are the correct names | ok |
| Title | HyperTree Proof Search for Neural Theorem Proving | identical in both | ok |
| Venue / Year | NeurIPS 35, 2022 | NeurIPS 2022 main proceedings | ok |
| arXiv id | 2205.11491 | 2205.11491v1, 2022-05-23 | ok |

**The flagged discrepancy is real.** arXiv 2205.11491 lists the authors as
Lample, **Lachaux, Lavril, Martinet, Hayat, Ebner, Rodriguez, Lacroix** — a
genuinely different order from position 2 onward. The draft follows the
proceedings, as it says it does. This is a claim that could easily have been
asserted without checking; it was checked.

---

## Summary table

| # | Record | File | Verdict |
|---|---|---|---|
| 1 | `ha2018world` | line1 | CLEAN |
| 2 | `ha2018recurrent` | line1 | CLEAN |
| 3 | `hafner2019planet` | line1 | CLEAN |
| 4 | `hafner2021dreamerv2` | line1 | CLEAN |
| 5 | `hafner2025dreamerv3` | line1 | CLEAN |
| 6 | `schrittwieser2020muzero` | line1 | CLEAN |
| 7 | `bruce2024genie` | line1 | CLEAN (advisory: PMLR expands two author names) |
| 8 | `assran2023ijepa` | line1 | CLEAN; CVPR-vs-ICCV call confirmed correct |
| 9 | `lecun2022path` | line1 | CLEAN (no venue, no DOI — correctly so) |
| 10 | `brooks2024sora` | line1 | CLEAN (primary page 403 to me; secondary corroboration only) |
| 11 | `tang2024worldcoder` | line1 | CLEAN (advisory: pages 70148–70212 available) |
| 12 | `hao2023rap` | line1 | **DEFECT — author list** |
| 13 | `liang2023codeaspolicies` | line1 | CLEAN |
| 14 | `solarlezama2006sketching` (C1) | line3 | CLEAN |
| 15 | `solarlezama2008thesis` (C2) | line3 | CLEAN |
| 16 | `lau2003vsa` (C5) | line3 | CLEAN |
| 17 | `muggleton1994ilptheory` (C7) | line3 | CLEAN |
| 18 | `cropper2022ilp30` (C8) | line3 | CLEAN |
| 19 | `yang2007arms` (C11) | line3 | CLEAN |
| 20 | `demoura2015lean` | line6 | CLEAN |
| 21 | `demoura2021lean4` | line6 | CLEAN |
| 22 | `mathlib2020` | line6 | CLEAN (advisory: Crossref `event` field says POPL — ignore it) |
| 23 | `hubert2025alphaproof` | line6 | CLEAN (advisory: year/volume-issue inconsistency to resolve) |
| 24 | `trinh2024alphageometry` | line6 | CLEAN |
| 25 | `lample2022hypertree` | line6 | CLEAN; author-order claim confirmed |

*(25 verdict rows across 20+ distinct sampled entries — `ha2018world` /
`ha2018recurrent` are drafted as a pair, as are the two Lean records.)*

**Counts: 24 CLEAN, 1 DEFECT, 0 UNVERIFIABLE.**

## Actions required

1. **`hao2023rap` (line1) — fix the author list.** Replace "Joshua Jiahua Hong"
   with **"Joshua Hong"** and "Daisy Zhe Wang" with **"Daisy Wang"** to match the
   EMNLP 2023 proceedings, which is the version the entry's venue, pages and DOI
   all point at. (Alternatively, cite arXiv:2305.14992 and keep the middle names
   — but do not mix.)
2. **`hubert2025alphaproof` (line6) — resolve `year` deliberately.** `year =
   {2025}` is currently paired with the print issue's volume/number/pages.
   PubMed indexes the record as 2026;651(8106):607-613. Pick one and note the
   other.
3. **`bruce2024genie` (line1) — decide the naming policy.** PMLR prints "Sarah
   Maria Elisabeth Bechtle" and "Nando De Freitas"; the draft uses the shorter
   arXiv/DBLP forms. Either is defensible; make it a stated convention.
4. **`brooks2024sora` (line1)** — the OpenAI page is 403 to automated fetching.
   Whoever finalises the bibliography should open it in a browser once and
   confirm the 13-name contributor list against the page itself, since I could
   only reach it through secondary citations.
5. **Do not "fix" two things that look wrong and are not:**
   `10.1038/s41586-**023**-06747-5` on a 2024 AlphaGeometry paper, and the
   `19–20` volume on `muggleton1994ilptheory`. Both are correct as printed.

## Method notes for the next auditor

- `api.crossref.org/works/<doi>` is reliable and returns `author`,
  `container-title`, `event`, `volume`, `issue`, `page`, and separate
  `published-online` / `published-print` dates — the last pair is what settles
  year disputes. Beware: Crossref ASCII-folds some diacritics (Bodík → Bodik,
  de Raedt case) and abbreviates some given names; do not treat it as
  authoritative for name spelling. Cross-check DBLP or the venue's own BibTeX.
- Set `PYTHONIOENCODING=utf-8` before piping Crossref JSON through Python on
  Windows, or diacritic-bearing author lists die on a GBK encode error — which
  silently truncates exactly the field you are auditing.
- `dblp.uni-trier.de` mirror works but rate-limits hard; it returns an **empty
  body** rather than an error when throttled. Pace requests ~4s apart and treat
  a zero-length response as a retry, not as "no hits".
- ACL Anthology serves raw BibTeX at `https://aclanthology.org/<id>.bib`, and
  CVF Open Access embeds a raw `@InProceedings` block in the paper HTML. Both
  are the venue of record and beat any aggregator.
- PubMed is an excellent independent second source for Nature/Science papers and
  is not rate-limited through WebFetch; `?term=<doi>` works directly. Its
  `eutils` API was unreachable from this sandbox via curl.
- `www2.eecs.berkeley.edu/Pubs/TechRpts/<year>/<id>.html` publishes its own
  BibTeX and EndNote blocks — the authoritative source for a UCB tech-report
  number.
- OpenReview (Cloudflare), IEEE Xplore, ACM DL, SpringerLink, Nature and
  `openai.com` were all unreachable or 403. None of them was needed.
