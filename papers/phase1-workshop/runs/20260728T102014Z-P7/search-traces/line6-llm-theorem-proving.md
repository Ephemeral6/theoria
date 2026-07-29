# Search trace — line 6: LLMs and theorem proving / autoformalisation / the Lean ecosystem

Run: `20260728T102014Z-P7` · branch `agent/p7-paper-section7` · base commit `f1346fb97b5b739f9e03355cb335e8bd302a54ca`
Date of searching: 2026-07-28 (UTC).

Rule applied: no record is written down unless **two independent sources** agree on
authors + year + venue. Where a work has no venue, the "no venue" claim itself is
carried by two sources. Nothing below was filled in from memory.

## 0 · Source availability notes (read before auditing)

Several of the obvious registries were unreachable or walled from this machine.
The substitutions are recorded here so a spot-check knows why a given URL was used.

| Source | Status | Consequence |
|---|---|---|
| `dblp.org` (main host) | `ECONNRESET` on every request | used the mirror `dblp.uni-trier.de`, same database, same API |
| `openreview.net` / `api.openreview.net` / `api2.openreview.net` | Cloudflare interstitial (302 to `/challenge`), no content | **no OpenReview evidence was used anywhere below.** For ICLR venues the second source is the official `iclr.cc` virtual page or `proceedings.iclr.cc` |
| `link.springer.com` | 303 to `idp.springer.com` authorisation | used `api.crossref.org` by DOI instead |
| `www.nature.com` | 303 to `idp.nature.com` authorisation | used `api.crossref.org` + PubMed/E-utilities instead |
| `dl.acm.org` | HTTP 403 | used `api.crossref.org` by DOI instead |
| `api.semanticscholar.org` | intermittent HTTP 429 | used only where it responded (ProofNet); never relied on as sole source |

`dblp.uni-trier.de` and `api.crossref.org` are independent of each other
(different curators, different ingestion paths), as are `dblp.uni-trier.de` and
the conference-run proceedings sites (`proceedings.neurips.cc`,
`proceedings.iclr.cc`, `iclr.cc/virtual`). arXiv is independent of all of them.

---

## 1 · Polu & Sutskever, "Generative Language Modeling for Automated Theorem Proving"

**Queries run**

- DBLP API: `q=Generative+Language+Modeling+Automated+Theorem+Proving`
- arXiv abs page for 2009.03393
- arXiv Atom API `id_list=2009.03393` (to read the `comment` / `journal_ref` fields, which the HTML summary does not reliably surface)

**Source A** — `https://arxiv.org/abs/2009.03393`
Confirmed: title *Generative Language Modeling for Automated Theorem Proving*;
authors Stanislas Polu, Ilya Sutskever (2, in that order); v1 2020-09-07;
Comments field reads "15+5 pages"; **no journal-ref** — i.e. arXiv itself records
no publication venue.

**Source A′** — `http://export.arxiv.org/api/query?id_list=2009.03393`
Confirmed the same author list and date from the machine-readable feed, and
confirmed `journal_ref` is absent rather than merely unrendered.

**Source B** — `https://dblp.uni-trier.de/search/publ/api?q=Generative+Language+Modeling+Automated+Theorem+Proving&format=json&h=8`
Confirmed: exactly **one** hit, year 2020, venue `CoRR`, type "Informal and Other
Publications", arXiv id 2009.03393. DBLP has **no** conference or journal entry
for this title — independent corroboration that it is preprint-only.

**Verdict: CONFIRMED** — arXiv preprint, no venue. Cite as `@misc` / `@article`
with `journal = {arXiv preprint}`; **do not** attribute it to a conference. (It is
widely referred to as "GPT-f"; that is a system name, not a venue.)

```bibtex
@misc{polu2020generative,
  title        = {Generative Language Modeling for Automated Theorem Proving},
  author       = {Polu, Stanislas and Sutskever, Ilya},
  year         = {2020},
  eprint       = {2009.03393},
  archivePrefix= {arXiv},
  primaryClass = {cs.LG},
  note         = {arXiv preprint; no peer-reviewed venue}
}
```

---

## 2 · Han, Rute, Wu, Ayers & Polu, "Proof Artifact Co-training …" (PACT)

**Queries run**

- DBLP API: `q=Proof+Artifact+Co-training+Theorem+Proving+Language+Models`
- arXiv abs page + Atom API for 2102.06203
- Web search: `"Proof Artifact Co-training" ICLR 2022 proceedings Han Rute Wu Ayers Polu` → led to the `iclr.cc` virtual poster id
- Attempted `https://openreview.net/forum?id=rpxJc9j04U` — **blocked** by Cloudflare, discarded

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=Proof+Artifact+Co-training+Theorem+Proving+Language+Models&format=json&h=8`
Confirmed: two entries for one work. (i) *Proof Artifact Co-Training for Theorem
Proving with Language Models*, **ICLR, 2022**, "Conference and Workshop Papers",
authors Jesse Michael Han, Jason Rute, Yuhuai Wu, Edward W. Ayers, Stanislas Polu.
(ii) the same title, `CoRR` 2021, arXiv 2102.06203.

**Source B** — `https://iclr.cc/virtual/2022/poster/6391`
Confirmed on the conference's own site: title *Proof Artifact Co-Training for
Theorem Proving with Language Models*; authors Jesse Han, Jason Rute, Yuhuai Wu,
Edward Ayers, Stanislas Polu; explicitly an **ICLR 2022 Poster**.

**Source C (corroborating, not counted)** — `https://arxiv.org/abs/2102.06203`
v1 2021-02-11, v2 2022-03-16, no journal-ref. Consistent with a 2021 preprint
published at ICLR 2022.

**Verdict: CONFIRMED** — ICLR 2022.

```bibtex
@inproceedings{han2022pact,
  title     = {Proof Artifact Co-Training for Theorem Proving with Language Models},
  author    = {Han, Jesse Michael and Rute, Jason and Wu, Yuhuai and Ayers, Edward W. and Polu, Stanislas},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2022},
  note      = {arXiv:2102.06203}
}
```

---

## 3 · Jiang et al., "Draft, Sketch, and Prove" (DSP)

**Queries run**

- DBLP API: `q=Draft+Sketch+Prove+Guiding+Formal+Theorem+Provers+Informal+Proofs`
- arXiv abs page + Atom API for 2210.12283
- Web search: `iclr.cc virtual 2023 poster "Draft, Sketch, and Prove"` → poster id 11536
- Attempted `https://openreview.net/forum?id=SMa9EAovKMC` — **blocked**, discarded

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=Draft+Sketch+Prove+Guiding+Formal+Theorem+Provers+Informal+Proofs&format=json&h=8`
Confirmed: (i) `CoRR` 2022, arXiv 2210.12283; (ii) **ICLR, 2023**, "Conference and
Workshop Papers", authors Albert Qiaochu Jiang, Sean Welleck, Jin Peng Zhou,
Timothée Lacroix, Jiacheng Liu, Wenda Li, Mateja Jamnik, Guillaume Lample,
Yuhuai Wu.

**Source B** — `https://iclr.cc/virtual/2023/poster/11536`
Confirmed on the conference's own site: **ICLR 2023**, described as an in-person
poster presentation and a top-5% paper; author order matches DBLP's ICLR record
(Jiang, Welleck, Zhou, Lacroix, Liu, Li, Jamnik, Lample, Wu).

**Source C (corroborating)** — `https://arxiv.org/abs/2210.12283`, v1 2022-10-21.

> ⚠ **Author-order trap.** The arXiv version orders the authors
> Jiang, Welleck, Zhou, **Li, Liu, Jamnik, Lacroix**, Wu, Lample; the ICLR
> proceedings version orders them Jiang, Welleck, Zhou, **Lacroix, Liu, Li,
> Jamnik**, Lample, Wu. The record below uses the **proceedings order**, since the
> citation is to the ICLR paper.

**Verdict: CONFIRMED** — ICLR 2023.

```bibtex
@inproceedings{jiang2023draft,
  title     = {Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs},
  author    = {Jiang, Albert Q. and Welleck, Sean and Zhou, Jin Peng and Lacroix, Timoth{\'e}e and Liu, Jiacheng and Li, Wenda and Jamnik, Mateja and Lample, Guillaume and Wu, Yuhuai},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2023},
  note      = {arXiv:2210.12283}
}
```

---

## 4 · Yang et al., "LeanDojo"

**Queries run**

- DBLP API: `q=LeanDojo`
- arXiv abs page for 2306.15626
- Web search: `"LeanDojo" NeurIPS 2023 Datasets and Benchmarks proceedings volume 36` → proceedings hash

**Source A** — `https://arxiv.org/abs/2306.15626`
Confirmed: title *LeanDojo: Theorem Proving with Retrieval-Augmented Language
Models*; authors Kaiyu Yang, Aidan M. Swope, Alex Gu, Rahul Chalamala, Peiyang
Song, Shixing Yu, Saad Godil, Ryan Prenger, Anima Anandkumar; v1 2023-06-27,
v2 2023-10-27; Comments field states verbatim "Accepted to NeurIPS 2023 (Datasets
and Benchmarks Track) as an oral presentation".

**Source B** — `https://proceedings.neurips.cc/paper_files/paper/2023/hash/4441469427094f8873d0fecb0c4e1cee-Abstract-Datasets_and_Benchmarks.html`
Confirmed on the official proceedings site: same title, same nine authors in the
same order, volume given as *Advances in Neural Information Processing Systems 36
(NeurIPS 2023), Datasets and Benchmarks Track*.

**Source C (corroborating)** — DBLP `q=LeanDojo`: NeurIPS 2023 conference entry
plus a `CoRR` entry for abs/2306.15626.

**Verdict: CONFIRMED** — NeurIPS 2023, Datasets and Benchmarks Track. The track
should be named; it is not the main track.

```bibtex
@inproceedings{yang2023leandojo,
  title     = {LeanDojo: Theorem Proving with Retrieval-Augmented Language Models},
  author    = {Yang, Kaiyu and Swope, Aidan M. and Gu, Alex and Chalamala, Rahul and Song, Peiyang and Yu, Shixing and Godil, Saad and Prenger, Ryan and Anandkumar, Anima},
  booktitle = {Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track},
  year      = {2023},
  note      = {arXiv:2306.15626}
}
```

---

## 5 · Lample et al., "HyperTree Proof Search for Neural Theorem Proving"

**Queries run**

- DBLP API: `q=HyperTree+Proof+Search+Neural+Theorem+Proving`
- NeurIPS 2022 proceedings hash page

**Source A** — `https://proceedings.neurips.cc/paper_files/paper/2022/hash/a8901c5e85fb8e1823bbf0f755053672-Abstract-Conference.html`
Confirmed: title *HyperTree Proof Search for Neural Theorem Proving*; authors
Guillaume Lample, Timothee Lacroix, Marie-Anne Lachaux, Aurelien Rodriguez,
Amaury Hayat, Thibaut Lavril, Gabriel Ebner, Xavier Martinet; volume *Advances in
Neural Information Processing Systems 35 (NeurIPS 2022), Main Conference Track*.

**Source B** — `https://dblp.uni-trier.de/search/publ/api?q=HyperTree+Proof+Search+Neural+Theorem+Proving&format=json&h=8`
Confirmed: **NeurIPS 2022**, "Conference and Workshop Papers", author order
identical to the proceedings page; separate `CoRR` 2022 entry, arXiv 2205.11491.

> ⚠ **Author-order trap.** arXiv 2205.11491 lists Lample, **Lachaux, Lavril,
> Martinet, Hayat, Ebner, Rodriguez, Lacroix**. The proceedings order differs.
> The record below uses the **proceedings order**.

**Verdict: CONFIRMED** — NeurIPS 2022 (main track).

```bibtex
@inproceedings{lample2022hypertree,
  title     = {HyperTree Proof Search for Neural Theorem Proving},
  author    = {Lample, Guillaume and Lacroix, Timoth{\'e}e and Lachaux, Marie-Anne and Rodriguez, Aur{\'e}lien and Hayat, Amaury and Lavril, Thibaut and Ebner, Gabriel and Martinet, Xavier},
  booktitle = {Advances in Neural Information Processing Systems 35 (NeurIPS 2022)},
  year      = {2022},
  note      = {arXiv:2205.11491}
}
```

---

## 6 · Wu et al., "Autoformalization with Large Language Models"

**Queries run**

- DBLP API: `q=Autoformalization+with+Large+Language+Models`
- arXiv Atom API `id_list=2205.12615`
- NeurIPS 2022 proceedings hash page

**Source A** — `https://proceedings.neurips.cc/paper_files/paper/2022/hash/d0c6bc641a56bebee9d985b937307367-Abstract-Conference.html`
Confirmed: title *Autoformalization with Large Language Models*; authors Yuhuai
Wu, Albert Qiaochu Jiang, Wenda Li, Markus Rabe, Charles Staats, Mateja Jamnik,
Christian Szegedy; volume *Advances in Neural Information Processing Systems 35
(NeurIPS 2022), Main Conference Track*.

**Source B** — `https://dblp.uni-trier.de/search/publ/api?q=Autoformalization+with+Large+Language+Models&format=json&h=8`
Confirmed: **NeurIPS 2022**, "Conference and Workshop Papers", same seven authors
in the same order; separate `CoRR` entry, arXiv 2205.12615.

**Source C (corroborating)** — `http://export.arxiv.org/api/query?id_list=2205.12615`:
published 2022-05-25, comment "44 pages", no journal-ref.

**Verdict: CONFIRMED** — NeurIPS 2022 (main track).

```bibtex
@inproceedings{wu2022autoformalization,
  title     = {Autoformalization with Large Language Models},
  author    = {Wu, Yuhuai and Jiang, Albert Q. and Li, Wenda and Rabe, Markus N. and Staats, Charles and Jamnik, Mateja and Szegedy, Christian},
  booktitle = {Advances in Neural Information Processing Systems 35 (NeurIPS 2022)},
  year      = {2022},
  note      = {arXiv:2205.12615}
}
```

---

## 7 · de Moura, Kong, Avigad, van Doorn & von Raumer, "The Lean Theorem Prover (System Description)"

**Queries run**

- DBLP API: `q=Lean+Theorem+Prover+System+Description+de+Moura`
- `https://doi.org/10.1007/978-3-319-21401-6_26` → redirected to `link.springer.com`, which then demanded authorisation; abandoned
- Crossref API by DOI

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=Lean+Theorem+Prover+System+Description+de+Moura&format=json&h=10`
Confirmed: title *The Lean Theorem Prover (System Description)*; authors Leonardo
Mendonça de Moura, Soonho Kong, Jeremy Avigad, Floris van Doorn, Jakob von
Raumer; year 2015; venue **CADE**; DOI `10.1007/978-3-319-21401-6_26`.

**Source B** — `https://api.crossref.org/works/10.1007/978-3-319-21401-6_26`
Confirmed: same title; authors Leonardo de Moura, Soonho Kong, Jeremy Avigad,
Floris van Doorn, Jakob von Raumer; container *Lecture Notes in Computer Science
— Automated Deduction – CADE-25*; publisher Springer International Publishing;
pages **378–388**; year **2015**.

*Not verified, therefore not asserted:* the LNCS series volume number. It is
deliberately omitted from the record below rather than guessed.

**Verdict: CONFIRMED** — CADE-25, 2015.

```bibtex
@inproceedings{demoura2015lean,
  title     = {The {Lean} Theorem Prover (System Description)},
  author    = {de Moura, Leonardo and Kong, Soonho and Avigad, Jeremy and van Doorn, Floris and von Raumer, Jakob},
  booktitle = {Automated Deduction -- CADE-25},
  series    = {Lecture Notes in Computer Science},
  publisher = {Springer},
  pages     = {378--388},
  year      = {2015},
  doi       = {10.1007/978-3-319-21401-6_26}
}
```

---

## 8 · de Moura & Ullrich, "The Lean 4 Theorem Prover and Programming Language"

**Queries run**

- DBLP API: `q=The+Lean+4+Theorem+Prover+and+Programming+Language`
- Crossref API by DOI (Springer page auth-walled, as above)

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=The+Lean+4+Theorem+Prover+and+Programming+Language&format=json&h=8`
Confirmed: title *The Lean 4 Theorem Prover and Programming Language*; authors
Leonardo de Moura, Sebastian Ullrich; year 2021; venue **CADE**; DOI
`10.1007/978-3-030-79876-5_37`.

**Source B** — `https://api.crossref.org/works/10.1007/978-3-030-79876-5_37`
Confirmed: same title and two authors; container *Lecture Notes in Computer
Science — Automated Deduction – CADE 28*; event *International Conference on
Automated Deduction (CADE-28)*; publisher Springer International Publishing;
pages **625–635**; year **2021**.

**Verdict: CONFIRMED** — CADE-28, 2021.

```bibtex
@inproceedings{demoura2021lean4,
  title     = {The {Lean} 4 Theorem Prover and Programming Language},
  author    = {de Moura, Leonardo and Ullrich, Sebastian},
  booktitle = {Automated Deduction -- CADE 28},
  series    = {Lecture Notes in Computer Science},
  publisher = {Springer},
  pages     = {625--635},
  year      = {2021},
  doi       = {10.1007/978-3-030-79876-5_37}
}
```

---

## 9 · The mathlib Community, "The Lean Mathematical Library"

This is the entry the brief flagged for its unusual author field, so it was
checked with that specifically in mind.

**Queries run**

- DBLP API: `q=The+Lean+mathematical+library`
- `https://dl.acm.org/doi/10.1145/3372885.3373824` → **HTTP 403**, abandoned
- Crossref API by DOI

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=The+Lean+mathematical+library&format=json&h=8`
Confirmed: an entry *The lean mathematical library*, year **2020**, venue **CPP**,
"Conference and Workshop Papers", DOI `10.1145/3372885.3373824`; plus a `CoRR`
entry dated 2019. Crucially the DBLP record carries **no personal author names** —
consistent with a collective author, and *inconsistent* with any attempt to name
an individual first author.

**Source B** — `https://api.crossref.org/works/10.1145/3372885.3373824`
Confirmed, and this is the decisive check: the Crossref `author` array holds
**a single object whose `family` field is the literal string "The mathlib
Community"**, with no `given` field. Container: *Proceedings of the 9th ACM
SIGPLAN International Conference on Certified Programs and Proofs*; publisher
ACM; pages **367–381**; year **2020**; type `proceedings-article`.

**Verdict: CONFIRMED** — CPP 2020, corporate author. In BibTeX the name must be
**double-braced** so BibTeX does not reorder it into "Community, The mathlib".

```bibtex
@inproceedings{mathlib2020,
  title     = {The {Lean} Mathematical Library},
  author    = {{The mathlib Community}},
  booktitle = {Proceedings of the 9th ACM SIGPLAN International Conference on Certified Programs and Proofs (CPP)},
  publisher = {ACM},
  pages     = {367--381},
  year      = {2020},
  doi       = {10.1145/3372885.3373824}
}
```

---

## 10 · Trinh, Wu, Le, He & Luong, "Solving olympiad geometry without human demonstrations" (AlphaGeometry)

**Queries run**

- DBLP API: `q=Solving+olympiad+geometry+without+human+demonstrations`
- `https://www.nature.com/articles/s41586-023-06747-5` → 303 to `idp.nature.com`, abandoned
- Crossref API by DOI

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=Solving+olympiad+geometry+without+human+demonstrations&format=json&h=8`
Confirmed: authors Trieu H. Trinh, Yuhuai Wu, Quoc V. Le, He He, Thang Luong;
year 2024; venue **Nature**; volume **625**, number **7995**, pages **476–482**;
DOI `10.1038/S41586-023-06747-5`.

**Source B** — `https://api.crossref.org/works/10.1038/s41586-023-06747-5`
Confirmed: identical title, identical five authors in identical order, container
*Nature*, volume 625, issue 7995, pages 476–482, year 2024, journal-article.

Note that "AlphaGeometry" is the system name and does **not** appear in the title.

**Verdict: CONFIRMED** — Nature 625(7995), 2024.

```bibtex
@article{trinh2024alphageometry,
  title   = {Solving olympiad geometry without human demonstrations},
  author  = {Trinh, Trieu H. and Wu, Yuhuai and Le, Quoc V. and He, He and Luong, Thang},
  journal = {Nature},
  volume  = {625},
  number  = {7995},
  pages   = {476--482},
  year    = {2024},
  doi     = {10.1038/s41586-023-06747-5}
}
```

---

## 11 · AlphaProof — Hubert et al., "Olympiad-level formal mathematical reasoning with reinforcement learning"

The brief asked specifically whether AlphaProof has a citable publication or only
a blog post. **It has a peer-reviewed Nature paper.** The blog-post-only
assumption is out of date.

**Queries run**

- DBLP API: `q=AlphaProof` → **zero hits**. This is a false negative, not evidence
  of absence: "AlphaProof" is a system name and does not occur in the paper's
  title, and DBLP's default search is title-based.
- Crossref bibliographic query `AlphaProof formal mathematical reasoning` → no
  title match, for the same reason.
- Web search `AlphaProof DeepMind Nature paper 2025 formal mathematical reasoning publication`
  → surfaced the Nature article and its PubMed record.
- Crossref API by DOI; PubMed record; NCBI E-utilities `esummary`.

**Source A** — `https://api.crossref.org/works/10.1038/s41586-025-09833-y`
Confirmed: title *Olympiad-level formal mathematical reasoning with reinforcement
learning*; 39 authors, first Thomas Hubert, last David Silver (also Demis
Hassabis, Pushmeet Kohli); container *Nature*; volume **651**, issue **8106**,
pages **607–613**; published **2025-11-12**; DOI `10.1038/s41586-025-09833-y`;
journal-article.

**Source B** — `https://pubmed.ncbi.nlm.nih.gov/41225005/` and
`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=41225005&retmode=json`
Confirmed independently: same title, journal *Nature*, volume 651, issue 8106,
pages 607–613, DOI `10.1038/s41586-025-09833-y`; **e-publication date
2025-11-12**, **print issue date March 2026**.

> ⚠ **Year ambiguity — flagged rather than silently resolved.** Crossref's
> earliest `published` date is 2025-11-12 (advance online publication); PubMed
> records the print issue as March 2026. Volume, issue and pages are identical
> across both. The record below uses **2025** (date of publication of record) and
> states the print issue in a `note`. If the paper's house style cites by print
> issue, change the year to 2026 — but change it deliberately, and keep the note.

The author list is long enough that `et al.` is appropriate in prose; the full
39-name list is available at the Crossref URL above if the bibliography needs it.

**Verdict: CONFIRMED** — Nature 651(8106), online 2025-11-12.

```bibtex
@article{hubert2025alphaproof,
  title   = {Olympiad-level formal mathematical reasoning with reinforcement learning},
  author  = {Hubert, Thomas and Mehta, Rishi and Sartran, Laurent and Horv{\'a}th, Mikl{\'o}s Z. and {\v Z}u{\v z}i{\'c}, Goran and Wieser, Eric and Huang, Aja and Schrittwieser, Julian and Schroecker, Yannick and Masoom, Hussain and Bertolli, Ottavia and Zahavy, Tom and Mandhane, Amol and Yung, Jessica and Beloshapka, Iuliya and Ibarz, Borja and Veeriah, Vivek and Yu, Lei and Nash, Oliver and Lezeau, Paul and Mercuri, Salvatore and S{\"o}nne, Calle and Mehta, Bhavik and Davies, Alex and Zheng, Daniel and Pedregosa, Fabian and Li, Yin and von Glehn, Ingrid and Rowland, Mark and Albanie, Samuel and Velingker, Ameya and Schmitt, Simon and Lockhart, Edward and Hughes, Edward and Michalewski, Henryk and Sonnerat, Nicolas and Hassabis, Demis and Kohli, Pushmeet and Silver, David},
  journal = {Nature},
  volume  = {651},
  number  = {8106},
  pages   = {607--613},
  year    = {2025},
  doi     = {10.1038/s41586-025-09833-y},
  note    = {Published online 12 November 2025; print issue March 2026. Describes the AlphaProof system.}
}
```

---

## 12 · Xin et al., "DeepSeek-Prover-V1.5"

Chosen as the representative of the DeepSeek-Prover line because it is the one
entry in that line with a peer-reviewed venue.

**Queries run**

- DBLP API: `q=DeepSeek-Prover` (returned all four entries in the line)
- arXiv abs page for 2408.08152
- Web search `iclr.cc virtual 2025 poster "DeepSeek-Prover-V1.5"` → official proceedings hash

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=DeepSeek-Prover&format=json&h=15`
Confirmed the shape of the whole line:
- *DeepSeek-Prover: Advancing Theorem Proving in LLMs through Large-Scale Synthetic Data* — `CoRR` **2024**, arXiv 2405.14333, **no venue**.
- *DeepSeek-Prover-V1.5* — **ICLR 2025**, "Conference and Workshop Papers" (and a `CoRR` 2024 entry, arXiv 2408.08152).
- *DeepSeek-Prover-V2* — `CoRR` **2025**, arXiv 2504.21801, **no venue**.

**Source B** — `https://proceedings.iclr.cc/paper_files/paper/2025/hash/b3b55c366d641c07180c40e4f978f311-Abstract-Conference.html`
Confirmed on the official ICLR proceedings site: title *DeepSeek-Prover-V1.5:
Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo
Tree Search*; **18 authors**, Huajian Xin first, Chong Ruan last; *International
Conference on Learning Representations 2025 (ICLR 2025)*.

> ⚠ **Author-count trap.** The arXiv v1 (2408.08152, submitted 2024-08-15) lists
> **17** authors; the ICLR proceedings version lists **18**, the addition being
> **Haowei Zhang**. The record below follows the proceedings.

**Verdict: CONFIRMED** — ICLR 2025.
**Also recorded (for whoever cites the rest of the line): DeepSeek-Prover (V1) and
DeepSeek-Prover-V2 are arXiv-only as of this search. Do not attribute a venue to
either.**

```bibtex
@inproceedings{xin2025deepseekproverv15,
  title     = {DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search},
  author    = {Xin, Huajian and Ren, Z. Z. and Song, Junxiao and Shao, Zhihong and Zhao, Wanjia and Wang, Haocheng and Liu, Bo and Zhang, Liyue and Lu, Xuan and Du, Qiushi and Gao, Wenjun and Zhang, Haowei and Zhu, Qihao and Yang, Dejian and Gou, Zhibin and Wu, Z. F. and Luo, Fuli and Ruan, Chong},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2408.08152}
}
```

---

## 13 · Azerbayev et al., "Llemma: An Open Language Model for Mathematics" *(optional)*

**Queries run**

- DBLP API: `q=Llemma+open+language+model+mathematics`
- Web search `iclr.cc virtual 2024 poster "Llemma" Azerbayev` → official proceedings hash

**Source A** — `https://dblp.uni-trier.de/search/publ/api?q=Llemma+open+language+model+mathematics&format=json&h=8`
Confirmed: **ICLR 2024**, "Conference and Workshop Papers", authors Zhangir
Azerbayev, Hailey Schoelkopf, Keiran Paster, Marco Dos Santos, Stephen Marcus
McAleer, Albert Q. Jiang, Jia Deng, Stella Biderman, Sean Welleck; plus a `CoRR`
2023 entry, arXiv 2310.10631.

**Source B** — `https://proceedings.iclr.cc/paper_files/paper/2024/hash/b225f5c7cd13615e9558c3931fa4e66f-Abstract-Conference.html`
Confirmed on the official ICLR proceedings site: same title, same nine authors in
the same order, *International Conference on Learning Representations 2024
(ICLR 2024)*.

**Verdict: CONFIRMED** — ICLR 2024.

```bibtex
@inproceedings{azerbayev2024llemma,
  title     = {Llemma: An Open Language Model for Mathematics},
  author    = {Azerbayev, Zhangir and Schoelkopf, Hailey and Paster, Keiran and Dos Santos, Marco and McAleer, Stephen and Jiang, Albert Q. and Deng, Jia and Biderman, Stella and Welleck, Sean},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2024},
  note      = {arXiv:2310.10631}
}
```

---

## 14 · Azerbayev et al., "ProofNet" *(optional)*

**Queries run**

- arXiv abs page for 2302.12433
- DBLP API: `q=ProofNet+autoformalizing+formally+proving+undergraduate`, then
  `q=ProofNet`, then an author-name query — **all three returned `ECONNRESET`**
  (the mirror rate-limited after ~20 requests). DBLP could not be used here.
- Semantic Scholar Graph API by arXiv id (this call did respond)

**Source A** — `https://arxiv.org/abs/2302.12433`
Confirmed: title *ProofNet: Autoformalizing and Formally Proving
Undergraduate-Level Mathematics*; authors Zhangir Azerbayev, Bartosz Piotrowski,
Hailey Schoelkopf, Edward W. Ayers, Dragomir Radev, Jeremy Avigad; v1 2023-02-24;
**no journal-ref**.

**Source B** — `https://api.semanticscholar.org/graph/v1/paper/arXiv:2302.12433?fields=title,authors,year,venue,publicationVenue,externalIds,publicationTypes,journal`
Confirmed independently: same title and same six authors in the same order; year
2023; `venue` = **"arXiv.org"**; `journal` = *ArXiv*, volume abs/2302.12433;
`externalIds` include the DBLP key `journals/corr/abs-2302-12433` — i.e. the only
DBLP record for it is the CoRR one, so DBLP too knows of no venue.

**Verdict: CONFIRMED** — arXiv preprint, no venue. (It is often described as
having appeared at a MATH-AI workshop; **that was not confirmed by either source
above and is therefore not asserted.** Cite it as a preprint.)

```bibtex
@misc{azerbayev2023proofnet,
  title        = {ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics},
  author       = {Azerbayev, Zhangir and Piotrowski, Bartosz and Schoelkopf, Hailey and Ayers, Edward W. and Radev, Dragomir and Avigad, Jeremy},
  year         = {2023},
  eprint       = {2302.12433},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  note         = {arXiv preprint; no peer-reviewed venue confirmed}
}
```

---

## Tally

- **CONFIRMED: 14** (entries 1–14).
- **DROPPED: 0.** No candidate had to be dropped for want of a second source.
- **Never asserted (deliberate omissions):** the LNCS volume numbers for the two
  CADE papers; the claimed MATH-AI workshop venue for ProofNet; any venue for
  Polu & Sutskever, DeepSeek-Prover (V1), DeepSeek-Prover-V2, or ProofNet.

## Traps recorded for the auditor

1. **AlphaProof does have a paper.** `AlphaProof` returns zero DBLP hits and zero
   Crossref title hits because the system name is not in the title. The paper is
   Hubert et al., Nature 651(8106):607–613 — entry 11. Anyone who searches only
   the system name will wrongly conclude "blog post only" and either drop it or
   invent an arXiv id.
2. **Its year is genuinely ambiguous** — online 2025-11-12, print issue March
   2026. Both were verified; the record picks 2025 and says why.
3. **Three author-order / author-count discrepancies** between arXiv and
   proceedings versions: Draft-Sketch-Prove (entry 3), HyperTree (entry 5),
   DeepSeek-Prover-V1.5 (entry 12, 17 vs 18 authors). All three records follow the
   proceedings.
4. **mathlib's author is the literal string "The mathlib Community"**, verified in
   Crossref's raw `author` array as a `family`-only field. It needs double braces
   in BibTeX.
5. **OpenReview contributed nothing.** It was unreachable throughout; every ICLR
   venue claim here rests on DBLP plus a conference-run site, not on OpenReview.
