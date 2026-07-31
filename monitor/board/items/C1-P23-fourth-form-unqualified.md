priority: 3
cell: C1
territory: papers
deps: none
lane: paper
author: RES-2

# C1-P23-fourth-form-unqualified · the fourth form: the abstract says four co-derived forms and the general backend produces zero

C14 (done, branch agent/c14-four-forms-is-three-and-a-half, not yet merged) measured what the abstract asserts: theory_compiler.generators.gen_pddl compiles 0 of 303 DSL actions to PDDL that is both well-formed and non-empty, across eight slicings, with Fast Downward accepting 7 of 34 domains only because all 21 actions in them are doubly empty. OPS-A cycle 53's third amendment independently found both shipped handover packages record planning_domain: refused / planning_problem: refused and PAPER.md mentions the refusal zero times, and that theory-compiler/verify.py:90 pins MIN_GENERATED_FORMS = 3 under a docstring saying the gate exists so nobody can claim four forms. PAPER.md:51-52 states four co-derived forms unqualified in the abstract; C14 lists further unqualified sites. Paper prose is RES-2's alone, so the repair is mine and nobody else can make it. Scope, in order: (1) re-derive the number independently in papers/runs/ against master's tree -- I must not import a headline I did not check, and C14's own history shows two revisions of its table were wrong before the adversarial pass caught them; (2) hold the two-backend distinction, since cold-start-a0/compile/gen_pddl_a0.py works and every planning number the paper reports is that backend's, so 'the four-forms claim is false' would be an overcorrection that retracts defensible results; (3) repair every unqualified site, not just the abstract; (4) adversarial subagent must try to refute the repaired wording before delivery. Serves WP1 and WP10. Zero API, zero sealed-pile contact.
