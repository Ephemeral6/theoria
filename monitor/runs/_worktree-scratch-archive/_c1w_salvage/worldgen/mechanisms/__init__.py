"""The mechanism library.  Importing this package registers every family.

Each module calls `base.register(...)` at import time, so `core/world.py` can
resolve an entity kind to its owner without a hand-maintained table.  The import
list below is therefore the whole registry; adding a family is adding a module
and a line here.
"""

from . import base                     # noqa: F401
from . import push                     # noqa: F401
from . import gravity                  # noqa: F401
from . import switch_door              # noqa: F401
from . import portal                   # noqa: F401
from . import color_cycle              # noqa: F401
from . import count_lock               # noqa: F401
from . import consumable               # noqa: F401

FAMILIES = (
    "push",
    "gravity",
    "switch_door",
    "portal",
    "color_cycle",
    "count_lock",
    "consumable",
)
