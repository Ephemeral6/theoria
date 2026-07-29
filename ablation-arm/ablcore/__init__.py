"""The ablated inner loop: theorize -> certify(cheap) -> probe -> plan -> commit.

One module per incision, named after it (DESIGN.md §4):

    downgrade.py    C-5 and the DSL half of C-1 — laws lose their standing
    compile_abl.py  C-1, C-3 — three co-derived forms instead of four
    certify_abl.py  C-2 — the cheap layer, and a raising stub where the other was
    plan_abl.py     C-4 — UNSAT is the answer, not the question
    playbook.py     C-5 — the theorem tier is demoted to the empirical tier

plus two modules that belong to no incision and exist to keep the comparison
honest:

    surprise.py     the loop's scheduling rule, shared verbatim by both arms
    pin.py          hash the upstream trees; prove the reuse was read-only
"""
