"""Regenerate every fixture. Same seed -> byte-identical files."""

import sys

from fixtures import cart_world, pair_flip, peg4


def main() -> int:
    cart = cart_world.write()
    pair = pair_flip.write()
    graph = peg4.write()
    print("A cart_world : %d frames" % len(cart["rows"]))
    print("B pair_flip  : %d states" % len(pair["rows"]))
    print("C peg4       : %d states, %d edges" % (len(graph["states"]), len(graph["edges"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
