"""Claim 4 attack: find an answer the marker pays for and should not, or a
ground truth it marks wrong. Runs over all 236 worldgen items and all four
hand-built papers."""
import copy, json, itertools, collections
from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.grading.rubrics_heldout import grade_frame_exact
from exam.model import Submission
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.papers import BUILDERS, module_for

d = digest()
paid_wrongly = []
truth_marked_wrong = []
silence_paid = []
n_items = 0
n_probes = 0

# ---- A. structural invariants over every worldgen item, every wrapper -------
WRAPPERS = [
    ("raw", lambda f: f),
    ("frame_after", lambda f: {"frame_after": f}),
    ("frame", lambda f: {"frame": f}),
    ("after", lambda f: {"after": f}),
    ("nested", lambda f: {"frame_after": {"frame_after": f}}),
    ("extra_key", lambda f: {"frame_after": f, "confidence": 0.0}),
    ("abstain_false", lambda f: {"abstain": False, "frame_after": f}),
    ("abstain_truthy", lambda f: {"abstain": 1, "frame_after": f}),
]
SILENCE = [None, {}, [], "", "   ", {"frame_after": None}, {"frame_after": []},
           0, False, [[]], [[None]], "null", "None", {"answers": {}},
           {"abstain": True}, {"abstain": "true"}, "abstain", "I don't know",
           "unsolvable", [[0]], {"frame_after": {}}]

for w in port.world_ids():
    paper = hw.build_for(w, 2)
    for it in paper.items:
        n_items += 1
        truth_frame = it.truth["frame_after"]
        # A1: ground truth in any accepted wrapper must be `correct`
        for name, wrap in WRAPPERS:
            n_probes += 1
            sc = grade_frame_exact(wrap(copy.deepcopy(truth_frame)), it.truth, it)
            expect_paid = name not in ("abstain_truthy",)  # abstain:1 is not `is True`
            if sc.verdict != "correct" and expect_paid:
                truth_marked_wrong.append((w, it.item_id, name, sc.verdict,
                                           sc.detail.get("why")))
        # A2: silence must never be paid
        for s in SILENCE:
            n_probes += 1
            sc = grade_frame_exact(s, it.truth, it)
            if sc.awarded > 0:
                silence_paid.append((w, it.item_id, repr(s), sc.verdict, sc.awarded))
        # A3: mutations of the truth must never be paid
        rows = [list(r) for r in truth_frame]
        legal = sorted(it.truth.get("legal_cells") or [0, 2, 4, 8])
        muts = []
        # one-cell change to every other legal value, at 3 positions
        pos = [(0, 0), (len(rows) // 2, len(rows[0]) // 2),
               (len(rows) - 1, len(rows[0]) - 1)]
        for (r, c) in pos:
            for v in legal:
                if v != rows[r][c]:
                    m = [list(x) for x in rows]; m[r][c] = v
                    muts.append(("cell(%d,%d)=%s" % (r, c, v), m))
        muts.append(("transposed", [list(x) for x in zip(*rows)]))
        muts.append(("rows_reversed", list(reversed([list(x) for x in rows]))))
        muts.append(("drop_last_row", [list(x) for x in rows[:-1]]))
        muts.append(("dup_last_row", [list(x) for x in rows] + [list(rows[-1])]))
        muts.append(("cols_reversed", [list(reversed(x)) for x in rows]))
        for name, m in muts:
            if m == rows:
                continue
            n_probes += 1
            sc = grade_frame_exact(m, it.truth, it)
            if sc.awarded > 0:
                paid_wrongly.append((w, it.item_id, name, sc.verdict, sc.awarded))

print("worldgen items probed:", n_items, " probes:", n_probes)
print("  ground truth marked NOT correct:", len(truth_marked_wrong), truth_marked_wrong[:6])
print("  silence paid                   :", len(silence_paid), silence_paid[:6])
print("  a non-truth frame paid         :", len(paid_wrongly), paid_wrongly[:6])

# ---- B. the two structural invariants on the four hand-built papers --------
for qt in BUILDERS:
    module = module_for(qt)
    paper = module.build()
    key_doc = paper.key(d)
    oracle = module.reference_answers(paper, key_doc, "oracle")
    rep = mark(key_doc, Submission("o", paper.paper_id, oracle, ("answers",)),
               axes_fn=getattr(module, "axes", None))
    bad = [s.item_id for s in rep.scores if s.verdict == "wrong"]
    lines = ["%-12s oracle fraction=%.4f  items marked wrong=%d %s"
             % (qt, rep.fraction, len(bad), bad[:4])]
    for s in SILENCE:
        r2 = mark(key_doc, Submission("n", paper.paper_id,
                                      {i: copy.deepcopy(s) for i in oracle},
                                      ("answers",)),
                  axes_fn=getattr(module, "axes", None))
        if r2.awarded > 0:
            lines.append("   SILENCE PAID %r -> %.4f of %.4f" % (s, r2.awarded, r2.possible))
    # a submission that declares no capability at all but answers anyway
    r3 = mark(key_doc, Submission("nocap", paper.paper_id, oracle, ()),
              axes_fn=getattr(module, "axes", None))
    lines.append("   capabilities=() but answers submitted -> fraction %.4f" % r3.fraction)
    print("\n".join(lines))
