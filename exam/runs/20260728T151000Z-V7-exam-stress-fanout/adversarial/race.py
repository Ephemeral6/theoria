import sys, traceback
from exam.papers import module_for
m = module_for("verdict")
bad = 0
for i in range(12):
    try:
        m.build()
    except Exception as e:
        bad += 1
        print("RACE FAILURE:", type(e).__name__, str(e)[:160])
print("worker done, failures=%d" % bad)
