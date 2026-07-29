# Draft records — Line 1: World models, the three-wave genealogy

Every entry below was cross-verified against two independent sources; the queries,
URLs and per-field confirmations are in
`../search-traces/line1-world-models.md`. Where a preprint year and a venue year
differ, both are given and the venue year is the one to cite.

Deltas are stated against the axis this paper argues on: what **verification
regime** admits the model as correct, and therefore what proposition the model can
carry. Wave I keeps the model in weights and checks it by prediction error or
return, so it carries no checkable proposition. Wave II keeps it in an editable
executable program and checks it by replaying the recorded transition history, so
it carries "true of everything already experienced". This paper's Wave III keeps
it in a formal theory — a hand-written manual and playbook in a DSL, compiled to
Lean, Python, PDDL and Markdown — and checks it by replay, by machine-checked
proof, and by active probing.

**Standing caveat for all deltas.** No arm of this paper was run against any
system named below. Nothing here is a measured comparison; each delta is a
statement about what is checked, not about which performs better.

---

## Wave I — the model lives in weights

### `ha2018world`

David Ha and Jürgen Schmidhuber. *World Models*. arXiv preprint
arXiv:1803.10122, 2018. DOI 10.48550/arXiv.1803.10122.

Peer-reviewed companion, if a refereed venue is required — note the different
title and the different arXiv id:

### `ha2018recurrent`

David Ha and Jürgen Schmidhuber. *Recurrent World Models Facilitate Policy
Evolution*. In Advances in Neural Information Processing Systems 31 (NeurIPS
2018), 2018. arXiv:1809.01999.

What it did: trained a recurrent generative model of an environment's dynamics in
a compressed latent space and then evolved a small controller entirely inside
that learned model, showing that a policy trained in imagination can transfer back
to the environment.

Our delta: the latent transition model admits no place to state a proposition
about the environment and no procedure to refute one, so we keep the same
ambition — a model good enough to plan in — while moving the model into a written
theory whose individual rules can be quoted, proved, and contradicted by a probe.

---

### `hafner2019planet`

Danijar Hafner, Timothy Lillicrap, Ian Fischer, Ruben Villegas, David Ha,
Honglak Lee, and James Davidson. *Learning Latent Dynamics for Planning from
Pixels*. In Proceedings of the 36th International Conference on Machine Learning
(ICML 2019), PMLR 97, pages 2555–2565, 2019. arXiv:1811.04551 (preprint 2018).

What it did: learned a latent dynamics model from pixels alone and planned with it
online, matching model-free control on continuous tasks with substantially fewer
environment interactions.

Our delta: PlaNet's model is accepted when its rollouts score well, whereas the
manual in this work is accepted only when it reproduces the recorded transitions
exactly and its stated invariants survive a proof obligation, which is a stricter
and narrower admission test rather than a better score.

---

### `hafner2020dreamer`

Danijar Hafner, Timothy Lillicrap, Jimmy Ba, and Mohammad Norouzi. *Dream to
Control: Learning Behaviors by Latent Imagination*. In International Conference on
Learning Representations (ICLR 2020), 2020. arXiv:1912.01603 (preprint 2019).

What it did: learned long-horizon behaviours by backpropagating value gradients
through trajectories imagined inside a learned latent world model.

Our delta: the same division of labour appears here — a model of the world and a
way of acting in it — but it is made explicit as two separate written artefacts,
the manual and the playbook, so that an error can be attributed to one of them
rather than diffused across a single network.

---

### `hafner2021dreamerv2`

Danijar Hafner, Timothy Lillicrap, Mohammad Norouzi, and Jimmy Ba. *Mastering
Atari with Discrete World Models*. In International Conference on Learning
Representations (ICLR 2021), 2021. arXiv:2010.02193 (preprint 2020).

What it did: replaced the continuous latent state with discrete categorical
representations and reached human-level Atari performance from a world model
trained on a single GPU.

Our delta: discretising the latent state makes the representation more legible but
leaves it unnameable, and the step taken here is to give each piece of state a
name in a DSL so that a rule about it can be written down and checked.

---

### `hafner2025dreamerv3`

Danijar Hafner, Jurgis Pasukonis, Jimmy Ba, and Timothy Lillicrap. *Mastering
diverse control tasks through world models*. Nature, 640(8059):647–653, 2025.
DOI 10.1038/s41586-025-08744-2. Preprint arXiv:2301.04104, 2023, under the title
*Mastering Diverse Domains through World Models*.

What it did: showed that one world-model algorithm with a fixed hyperparameter
configuration reaches strong performance across more than 150 tasks, including
collecting diamonds in Minecraft without human data or curricula.

Our delta: generality across domains from a fixed configuration is orthogonal to
what we are after, since a Dreamer agent that has mastered a domain still cannot
be asked whether a given quantity is conserved in it, and answering that question
is the only thing the formal carrier buys.

---

### `schrittwieser2020muzero`

Julian Schrittwieser, Ioannis Antonoglou, Thomas Hubert, Karen Simonyan, Laurent
Sifre, Simon Schmitt, Arthur Guez, Edward Lockhart, Demis Hassabis, Thore
Graepel, Timothy Lillicrap, and David Silver. *Mastering Atari, Go, chess and
shogi by planning with a learned model*. Nature, 588(7839):604–609, 2020.
DOI 10.1038/s41586-020-03051-4. Preprint arXiv:1911.08265, 2019.

What it did: planned by tree search inside a model learned from scratch, with no
access to the rules of the game, predicting only the quantities search needs —
policy, value and reward.

Our delta: MuZero deliberately learns a model that predicts what search needs
rather than what the world is, and this work takes the opposite side of that
trade, insisting on a model that states what the world is even where that
statement is not needed to choose the next move.

---

### `bruce2024genie`

Jake Bruce, Michael D. Dennis, Ashley Edwards, Jack Parker-Holder, Yuge Shi,
Edward Hughes, Matthew Lai, Aditi Mavalankar, Richie Steigerwald, Chris Apps,
Yusuf Aytar, Sarah Bechtle, Feryal Behbahani, Stephanie C. Y. Chan, Nicolas
Heess, Lucy Gonzalez, Simon Osindero, Sherjil Ozair, Scott Reed, Jingwei Zhang,
Konrad Zolna, Jeff Clune, Nando de Freitas, Satinder Singh, and Tim Rocktäschel.
*Genie: Generative Interactive Environments*. In Proceedings of the 41st
International Conference on Machine Learning (ICML 2024), PMLR 235, pages
4603–4623, 2024. arXiv:2402.15391.

What it did: trained on unlabelled internet videos a generative model that
produces controllable, frame-by-frame playable environments with a learned latent
action space.

Our delta: a generated environment can be stepped but not interrogated, and the
question this paper asks of a world model — which propositions about it are true,
and how would we find out that one is false — has no address inside a video model.

---

### `assran2023ijepa`

Mahmoud Assran, Quentin Duval, Ishan Misra, Piotr Bojanowski, Pascal Vincent,
Michael Rabbat, Yann LeCun, and Nicolas Ballas. *Self-Supervised Learning from
Images with a Joint-Embedding Predictive Architecture*. In Proceedings of the
IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2023), pages
15619–15629, 2023. DOI 10.1109/CVPR52729.2023.01499. arXiv:2301.08243.

Note: the arXiv comment field names ICCV; the proceedings, the CVF open-access
listing and the IEEE DOI all say CVPR 2023. Cite CVPR.

What it did: learned image representations by predicting the representations of
masked target blocks from a context block, without hand-crafted augmentations and
without reconstructing pixels.

Our delta: JEPA's argument that prediction should happen in representation space
rather than in observation space is a claim about where to predict, whereas the
claim here is about what counts as having predicted correctly, and the two are
compatible.

---

### `lecun2022path`

Yann LeCun. *A Path Towards Autonomous Machine Intelligence, Version 0.9.2,
2022-06-27*. Unrefereed manuscript posted on OpenReview, 2022.
https://openreview.net/pdf?id=BZ5a1r-kVsf

Note: this is a position paper, not a peer-reviewed publication, and it has no
venue and no DOI. Bibliographies that render it as "Open Review 62(1), pp. 1–62"
are propagating an indexing artefact; do not copy that form.

What it did: set out an architecture for autonomous agents built around a
configurable predictive world model, intrinsic motivation, and hierarchical
joint-embedding predictors trained by self-supervision.

Our delta: this is the clearest statement of the first wave's programme, that a
predictive world model in learned representations is the route to autonomy, and
the position taken here is narrower — that such a model cannot state a
conservation law or an unsolvability claim, and that some tasks require one.

---

### `brooks2024sora`

Tim Brooks, Bill Peebles, Connor Holmes, Will DePue, Yufei Guo, Li Jing, David
Schnurr, Joe Taylor, Troy Luhman, Eric Luhman, Clarence Ng, Ricky Wang, and
Aditya Ramesh. *Video generation models as world simulators*. OpenAI technical
report, 2024.
https://openai.com/index/video-generation-models-as-world-simulators/

Note: this is a company technical report published on OpenAI's website. It is not
peer reviewed, has no venue and no DOI, and its own scope statement excludes model
and implementation details. Cite it as a technical report and attribute its
statements as company claims, never as results.

What it did: reported that a large text-conditional diffusion transformer trained
on spacetime patches of video exhibits emergent 3D consistency and object
persistence, and argued from those observations that scaling video generation is a
path to general-purpose simulators of the physical world.

Our delta: the argument rests on qualitative samples with no stated criterion by
which the claim could fail, which is the first wave's verification regime in its
weakest form, and the contribution here is to insist that a world model ship with
the test that would refute it.

---

## Wave II — the model lives in an editable executable program

### `tang2024worldcoder`

Hao Tang, Darren Key, and Kevin Ellis. *WorldCoder, a Model-Based LLM Agent:
Building World Models by Writing Code and Interacting with the Environment*. In
Advances in Neural Information Processing Systems 37 (NeurIPS 2024), 2024.
arXiv:2402.12275. DOI 10.52202/079017-2243.

What it did: had an LLM agent build and repeatedly repair a Python program
representing the environment's transition function, requiring the program to be
consistent with every interaction recorded so far while remaining optimistic about
attainable reward.

Our delta: WorldCoder is the closest neighbour and the regime we inherit — an
editable executable model reconciled against the full replay history — and the
step taken here is to add two checks that replay cannot perform, a machine-checked
proof of stated invariants and an active probe designed to falsify them, because
replay catches a rule written wrong but never a rule left out.

---

### `hao2023rap`

Shibo Hao, Yi Gu, Haodi Ma, Joshua Jiahua Hong, Zhen Wang, Daisy Zhe Wang, and
Zhiting Hu. *Reasoning with Language Model is Planning with World Model*. In
Proceedings of the 2023 Conference on Empirical Methods in Natural Language
Processing (EMNLP 2023), pages 8154–8173, 2023.
DOI 10.18653/v1/2023.emnlp-main.507. arXiv:2305.14992.

The method is named RAP, Reasoning via Planning, in the body of the paper.

What it did: repurposed the language model itself as the world model, giving it an
explicit state and reward and searching over reasoning traces with Monte Carlo
tree search rather than sampling a single chain of thought.

Our delta: RAP's world model is the language model's own forward pass, so it is
re-derived at every query and cannot be inspected between queries, whereas the
manual here is a persistent artefact that outlives the episode and can be diffed,
proved about, and refuted.

---

### `liang2023codeaspolicies` — optional, include only with the distinction made explicit

Jacky Liang, Wenlong Huang, Fei Xia, Peng Xu, Karol Hausman, Brian Ichter, Pete
Florence, and Andy Zeng. *Code as Policies: Language Model Programs for Embodied
Control*. In 2023 IEEE International Conference on Robotics and Automation
(ICRA 2023), pages 9493–9500, 2023. DOI 10.1109/ICRA48891.2023.10160591.
arXiv:2209.07753 (preprint 2022).

What it did: had a language model write executable policy code — recursively
defined, composing perception and control APIs — directly from a natural-language
instruction.

Our delta: this writes the policy as a program rather than the world model as a
program, which is the playbook side of the split used here and not the manual
side, so it belongs in the section only where that distinction is being drawn
rather than as a Wave II world-model system.

---

## Open obligation carried over from `sections/11_related.md`

The **Schema** system, and the 98.98% and +56pp figures attributed to it, were
outside this line's assignment and remain uncited. They are the only numbers in
the Wave II paragraph, and `Theoria.md` is their present source. They must be
traced to a primary publication or removed before submission.
