import time
from exam.papers import module_for
m = module_for("verdict")
end = time.time() + 240
while time.time() < end:
    try: m.build()
    except Exception: pass
