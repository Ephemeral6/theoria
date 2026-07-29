import traceback
from exam.papers import module_for
m = module_for("verdict")
for i in range(15):
    try:
        m.build()
    except Exception:
        print("RACE TRACEBACK:"); traceback.print_exc(); break
print("done")
