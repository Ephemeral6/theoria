# Line 6 — LLMs and theorem proving, autoformalisation, and the Lean ecosystem

Fills the `[bib: TODO]` at `sections/11_related.md` line 93 ("**LLM + theorem
proving** [bib: TODO] is the feasibility basis rather than a comparison target"),
and supplies the Lean citation that §2/§4 need, since the DSL compiles to Lean.

Verification trace, with two independent sources per record:
`../search-traces/line6-llm-theorem-proving.md`. Fourteen records confirmed, none
dropped. Nine are proposed as the core set; five are supplementary and can be cut
without damaging the argument.

## What this line is for, stated once

This literature is the **feasibility basis** for the loop, not a comparison
target. It is the evidence that "an LLM proposes a formal statement and a machine
then checks it" is a buildable arrangement rather than an aspiration. Two
qualifications apply to every entry below and are therefore stated here instead of
being repeated fourteen times.

**First, the specification comes from somewhere else in that work and from here in
this one.** Neural theorem proving operates inside a *given* formal library —
mathlib, Metamath, Isabelle's AFP, a competition problem set. The statement to be
proved is supplied, and it is correct by construction: someone already decided
that `∀ n, n + 0 = n` is the right thing to say. The hard part is the proof. Here
the LLM writes the specification itself: the manual is a formal description of an
*unknown interactive world*, induced from a ledger of observed transitions, and
nothing outside the manual vouches for it. The consequence is not symmetric with
theirs — a proof can succeed while the theorem it proves is **false of the world**,
because the theorem was stated about an induced `step` rather than the real one.
§5.6 exhibits exactly that pair of artefacts. Autoformalisation is the nearest
neighbour to this, since it also produces statements rather than only proofs, but
it produces them from a natural-language original that already says something
true; here there is no original.

**Second, this paper does not run an LLM-based prover.** No result reported here
depends on neural proof search. The Lean obligations in this work are discharged
by ordinary Lean elaboration and checking, and the engines that generate the
obligations (`lp_potential`, `zero_space`, `cegis_miner`) are classical solvers,
not learned ones. Nothing below is an ablation, a baseline, or a component of the
system; it is cited to establish that the checking half of the loop is a real
capability with a real literature behind it. Any sentence in the paper that
implies otherwise should be corrected.

---

## Core set

### `demoura2015lean` — The Lean theorem prover

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

*What it did.* Introduced Lean, a proof assistant built on a dependent type
theory with a small trusted kernel, designed so that automation can be written
against the system rather than bolted onto it.

*Our delta.* This is the checker the manual compiles into, not a neighbouring
method: the kernel is what makes "re-check rather than trust" affordable at the
boundary of §4, and the citation is load-bearing for the claim that a proposition
about an induced world is machine-checkable at all.

### `demoura2021lean4` — Lean 4

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

*What it did.* Rebuilt Lean as a general-purpose programming language in which the
elaborator and much of the system are written in Lean itself, making the language
extensible from user code.

*Our delta.* Cite this rather than (or alongside) the 2015 paper wherever the
paper names the concrete artefact it generates, since the generated form is Lean 4
and the two systems are not interchangeable; the delta in substance is the same as
above — we supply the theorem, Lean supplies only the verdict.

### `mathlib2020` — mathlib

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

*(Author is a collective and must stay double-braced.)*

*What it did.* Described mathlib, the community-maintained unified library of
formalised mathematics for Lean, together with the conventions that let a large
body of definitions and theorems stay coherent as it grows.

*Our delta.* mathlib is the standing example of the setting this work is *not* in
— a curated corpus whose statements are agreed correct before any prover touches
them — so it is the cleanest way to name what the manual lacks: there is no
community, no review, and no prior agreement that the induced statements are the
right ones.

### `polu2020generative` — GPT-f

```bibtex
@misc{polu2020generative,
  title        = {Generative Language Modeling for Automated Theorem Proving},
  author       = {Polu, Stanislas and Sutskever, Ilya},
  year         = {2020},
  eprint       = {2009.03393},
  archivePrefix= {arXiv},
  primaryClass = {cs.LG},
  note         = {arXiv preprint}
}
```

*(arXiv-only; it has no conference venue. Verified in both sources.)*

*What it did.* Applied a transformer language model to proof search in Metamath,
and had several of the resulting proofs accepted into the Metamath library.

*Our delta.* It is the origin point for the claim this line is cited to support —
that a language model's output can be admitted on the strength of a checker rather
than a reader — while the statements it proved were drawn from an existing library
and the acceptance criterion was the library's own.

### `han2022pact` — PACT

```bibtex
@inproceedings{han2022pact,
  title     = {Proof Artifact Co-Training for Theorem Proving with Language Models},
  author    = {Han, Jesse Michael and Rute, Jason and Wu, Yuhuai and Ayers, Edward W. and Polu, Stanislas},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2022},
  note      = {arXiv:2102.06203}
}
```

*What it did.* Extracted self-supervised training data from kernel-level proof
terms in Lean and co-trained on it alongside tactic prediction, raising success
rate on a held-out theorem suite.

*Our delta.* It shows that the proof assistant's own internal artefacts are a
usable training signal, which is the strongest available argument that the Lean
side of our loop could later be automated; we do not automate it, and every Lean
obligation in this paper is discharged without a learned prover.

### `lample2022hypertree` — HyperTree Proof Search

```bibtex
@inproceedings{lample2022hypertree,
  title     = {HyperTree Proof Search for Neural Theorem Proving},
  author    = {Lample, Guillaume and Lacroix, Timoth{\'e}e and Lachaux, Marie-Anne and Rodriguez, Aur{\'e}lien and Hayat, Amaury and Lavril, Thibaut and Ebner, Gabriel and Martinet, Xavier},
  booktitle = {Advances in Neural Information Processing Systems 35 (NeurIPS 2022)},
  year      = {2022},
  note      = {arXiv:2205.11491}
}
```

*(Author order follows the proceedings, which differs from arXiv.)*

*What it did.* Introduced a search procedure over hypertrees of subgoals, trained
online against the prover's own successes, and reported gains on Metamath and
Lean benchmarks.

*Our delta.* Its subject is the cost of finding a proof for a fixed goal; ours is
whether the goal was worth stating, so the two do not trade off against each other
and no number here is comparable to a number there.

### `jiang2023draft` — Draft, Sketch, and Prove

```bibtex
@inproceedings{jiang2023draft,
  title     = {Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs},
  author    = {Jiang, Albert Q. and Welleck, Sean and Zhou, Jin Peng and Lacroix, Timoth{\'e}e and Liu, Jiacheng and Li, Wenda and Jamnik, Mateja and Lample, Guillaume and Wu, Yuhuai},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2023},
  note      = {arXiv:2210.12283}
}
```

*(Author order follows the proceedings, which differs from arXiv.)*

*What it did.* Mapped informal proofs — human-written or model-generated — into
formal proof sketches, then let an automated prover close the remaining gaps.

*Our delta.* The closest structural analogue to our pipeline, in that an
informal artefact is turned into formal obligations that a machine discharges; the
difference is that its informal artefact is a proof of a statement already known
to hold, whereas ours is a hypothesis about a world that may simply be wrong, so
the failure mode it can exhibit is an unclosed gap and the failure mode we exhibit
in §5.6 is a closed proof of a false claim.

### `yang2023leandojo` — LeanDojo

```bibtex
@inproceedings{yang2023leandojo,
  title     = {LeanDojo: Theorem Proving with Retrieval-Augmented Language Models},
  author    = {Yang, Kaiyu and Swope, Aidan M. and Gu, Alex and Chalamala, Rahul and Song, Peiyang and Yu, Shixing and Godil, Saad and Prenger, Ryan and Anandkumar, Anima},
  booktitle = {Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Datasets and Benchmarks Track},
  year      = {2023},
  note      = {arXiv:2306.15626}
}
```

*(Datasets and Benchmarks track, not the main track — name the track.)*

*What it did.* Released tooling that extracts proofs and premise-selection data
from Lean, a benchmark of theorems drawn from mathlib, and a retrieval-augmented
prover trained against it.

*Our delta.* It makes explicit that the premises a prover retrieves are mathlib's,
already vetted; in this work the premises are the manual's own induced rules, so
retrieval has nothing trustworthy to retrieve from and the burden shifts entirely
onto whether the manual is true.

### `wu2022autoformalization` — Autoformalisation with LLMs

```bibtex
@inproceedings{wu2022autoformalization,
  title     = {Autoformalization with Large Language Models},
  author    = {Wu, Yuhuai and Jiang, Albert Q. and Li, Wenda and Rabe, Markus N. and Staats, Charles and Jamnik, Mateja and Szegedy, Christian},
  booktitle = {Advances in Neural Information Processing Systems 35 (NeurIPS 2022)},
  year      = {2022},
  note      = {arXiv:2205.12615}
}
```

*What it did.* Showed that few-shot prompting of a large language model translates
a non-trivial fraction of competition mathematics problems from natural language
into formal Isabelle/HOL statements, and that the resulting statements are useful
downstream.

*Our delta.* This is the entry that most nearly does what the manual does — it
generates statements, not just proofs — and it is therefore the right place to say
what is different: its source is a natural-language problem that already denotes
something definite, so its error mode is mistranslation and is detectable by
reading the original, whereas the manual is induced from a transition ledger with
no original to read back against, and its error mode is only detectable by
experiment against the world.

---

## Supplementary set

Cite these if the section has room; the argument survives without them.

### `hubert2025alphaproof` — AlphaProof

```bibtex
@article{hubert2025alphaproof,
  title   = {Olympiad-level formal mathematical reasoning with reinforcement learning},
  author  = {Hubert, Thomas and Mehta, Rishi and Sartran, Laurent and others},
  journal = {Nature},
  volume  = {651},
  number  = {8106},
  pages   = {607--613},
  year    = {2025},
  doi     = {10.1038/s41586-025-09833-y},
  note    = {Published online 12 November 2025; print issue March 2026. Describes the AlphaProof system.}
}
```

*Three notes before using this.* (i) AlphaProof **is** citable as a peer-reviewed
paper; it is no longer blog-post-only, and no arXiv id should be invented for it.
(ii) "AlphaProof" does not appear in the title, which is why title searches for
the system name come up empty. (iii) The year is genuinely ambiguous — online
November 2025, print issue March 2026 — and both were verified; pick one
deliberately. The full 39-author list is in the search trace if the bibliography
needs it, and `others` above should be expanded if house style requires.

*What it did.* Trained a reinforcement-learning agent to find formal proofs in
Lean, using auto-formalised problems at scale, and reported IMO-level performance
with every step machine-verified.

*Our delta.* It is the strongest existing demonstration that formal verification
scales as a training-time reward signal, and it is also the sharpest illustration
of the boundary: its problems were formalised from competition statements that a
human had already certified as well-posed, so its guarantee of correctness is a
guarantee about proofs and not about whether the statement describes anything.

### `trinh2024alphageometry` — AlphaGeometry

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

*("AlphaGeometry" is the system name and is not in the title.)*

*What it did.* Paired a neural language model with a symbolic deduction engine,
trained on synthetically generated problems rather than human proofs, and solved
most of a set of olympiad geometry problems.

*Our delta.* The neural-proposes / symbolic-checks division of labour is the same
one this framework adopts as "engines propose, the LLM adjudicates" — inverted in
role but identical in spirit — and the difference is again that its symbolic
engine works within a fixed and correct axiomatisation of geometry while ours
works within an axiomatisation the model just wrote.

### `xin2025deepseekproverv15` — DeepSeek-Prover-V1.5

```bibtex
@inproceedings{xin2025deepseekproverv15,
  title     = {DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search},
  author    = {Xin, Huajian and Ren, Z. Z. and Song, Junxiao and Shao, Zhihong and Zhao, Wanjia and Wang, Haocheng and Liu, Bo and Zhang, Liyue and Lu, Xuan and Du, Qiushi and Gao, Wenjun and Zhang, Haowei and Zhu, Qihao and Yang, Dejian and Gou, Zhibin and Wu, Z. F. and Luo, Fuli and Ruan, Chong},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2408.08152}
}
```

*Note.* V1.5 is the only entry in the DeepSeek-Prover line with a peer-reviewed
venue; DeepSeek-Prover (arXiv:2405.14333) and DeepSeek-Prover-V2
(arXiv:2504.21801) are arXiv-only and must not be given one.

*What it did.* Combined supervised fine-tuning on formal proof data with
reinforcement learning from proof-assistant feedback and a Monte-Carlo tree search
variant, improving open-model results on Lean 4 benchmarks.

*Our delta.* Proof-assistant feedback is here a reward channel for a prover; in
this work the assistant's verdict is a gate on a world theory, and a passing
verdict is compatible with the theory being wrong, so the same signal carries a
much weaker guarantee on our side of the boundary.

### `azerbayev2024llemma` — Llemma

```bibtex
@inproceedings{azerbayev2024llemma,
  title     = {Llemma: An Open Language Model for Mathematics},
  author    = {Azerbayev, Zhangir and Schoelkopf, Hailey and Paster, Keiran and Dos Santos, Marco and McAleer, Stephen and Jiang, Albert Q. and Deng, Jia and Biderman, Stella and Welleck, Sean},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2024},
  note      = {arXiv:2310.10631}
}
```

*What it did.* Continued pretraining of a code model on a mathematics-heavy corpus
to produce an openly released model capable of tool use and formal theorem proving
without task-specific fine-tuning.

*Our delta.* It is evidence that the capability this loop assumes is available in
open models rather than only behind a frontier API, which matters for
reproducibility but changes nothing about the specification-validity gap this
paper is about.

### `azerbayev2023proofnet` — ProofNet

```bibtex
@misc{azerbayev2023proofnet,
  title        = {ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics},
  author       = {Azerbayev, Zhangir and Piotrowski, Bartosz and Schoelkopf, Hailey and Ayers, Edward W. and Radev, Dragomir and Avigad, Jeremy},
  year         = {2023},
  eprint       = {2302.12433},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  note         = {arXiv preprint}
}
```

*(arXiv-only. It is often described as a workshop paper; that was not confirmed by
either source, so no venue is asserted.)*

*What it did.* Released a benchmark of undergraduate mathematics statements paired
across natural language and Lean, for measuring autoformalisation and formal
proving together.

*Our delta.* It measures autoformalisation against a reference formalisation
written by a human, which is precisely the instrument this work cannot have: there
is no reference manual for an unknown game, so correctness of the induced
specification can only be tested by acting in the world, not by comparison.

---

## Suggested replacement for the placeholder at `11_related.md:93`

Drop-in prose, matching the surrounding register. Adjust to fit the paragraph's
final length budget.

> **LLM + theorem proving** [`polu2020generative`, `han2022pact`,
> `lample2022hypertree`, `jiang2023draft`, `yang2023leandojo`] is the feasibility
> basis rather than a comparison target: it is why an LLM proposing a formal
> statement that a machine then checks is a buildable loop at all, and it supplies
> the checker this work compiles into [`demoura2015lean`, `demoura2021lean4`]. The
> setting differs in one respect that governs everything else. That work proves
> theorems inside a *given* formal library [`mathlib2020`] or a curated problem
> set, where the statement is supplied and correct by construction and the
> difficulty is the proof. Here the LLM writes the specification itself — the
> manual is a formal description of an unknown interactive world, induced from a
> transition ledger — so a proof can succeed while the theorem it establishes is
> false *of the world*. §5.6 exhibits that case. Autoformalisation
> [`wu2022autoformalization`] is the nearest neighbour, since it also produces
> statements and not only proofs, but its statements are translations of a
> natural-language original that already denotes something definite; the manual
> has no original to be checked against, only the world. **This paper runs no
> LLM-based prover.** The Lean obligations reported here are discharged by
> ordinary Lean checking, and no result depends on neural proof search.
