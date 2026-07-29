"""Crude unused-import check for the files this run touched.  Provenance helper.

Not a linter: it parses the AST for imported names and reports any that never
appear again as a `Name`/`Attribute` root in the module. Good enough to catch
the leftovers a refactor leaves behind.
"""

import ast
import os
import sys

FILES = (
    "worldgen/mutate.py", "worldgen/build.py", "worldgen/qc/run_qc.py",
    "worldgen/core/world.py", "worldgen/core/truth.py", "worldgen/core/spec.py",
    "worldgen/verify.py", "worldgen/tests/test_mutate.py",
)


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    bad = 0
    for rel in FILES:
        path = os.path.join(root, rel)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source)
        imported = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    name = (alias.asname or alias.name).split(".")[0]
                    imported.setdefault(name, node.lineno)
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                base = node
                while isinstance(base, ast.Attribute):
                    base = base.value
                if isinstance(base, ast.Name):
                    used.add(base.id)
        # annotations are strings in some positions; fall back to a text scan
        for name, lineno in sorted(imported.items()):
            if name in used or source.count(name) > 1:
                continue
            print("%s:%d unused import %s" % (rel, lineno, name))
            bad += 1
    print("unused imports: %d" % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main())
