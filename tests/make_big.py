"""Make a large pair of source-like files for timing.

Usage:  python tests/make_big.py LINES EDITS OUT_DIR
Writes OUT_DIR/big_a.txt and OUT_DIR/big_b.txt. B is A with EDITS random
small edits (replace, delete or insert a few lines). Many lines repeat, as in
real code (blank lines, braces, returns), which is harder for a diff.
"""

import os
import random
import sys

COMMON = [b"", b"}", b"    }", b"        return result;", b"    else {", b"#include <stdio.h>",
          b"    for (int i = 0; i < n; i++) {", b"        break;", b"    return 0;"]


def make_line(rng):
    if rng.random() < 0.35:
        return rng.choice(COMMON)
    return b"    value_%d = compute(%d, %d);" % (rng.randrange(50000), rng.randrange(100), rng.randrange(100))


def main():
    n, edits, out_dir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rng = random.Random(42)
    a = [make_line(rng) for _ in range(n)]
    b = list(a)
    for _ in range(edits):
        p = rng.randrange(len(b))
        kind = rng.random()
        size = rng.randint(1, 3)
        if kind < 0.4:
            b[p:p + size] = [make_line(rng) for _ in range(size)]
        elif kind < 0.7:
            del b[p:p + size]
        else:
            b[p:p] = [make_line(rng) for _ in range(size)]
    os.makedirs(out_dir, exist_ok=True)
    for name, lines in (("big_a.txt", a), ("big_b.txt", b)):
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(b"\n".join(lines) + b"\n")


if __name__ == "__main__":
    main()
