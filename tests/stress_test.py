"""Check src/main.py against a slow O(N*M) LCS on many random inputs.

Run from the project root:  python tests/stress_test.py
This file is not uploaded (only myers.toml and src/ are).
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import main  # noqa: E402


def lcs_length(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def check_render(a, b, out):
    """Rebuild A and B from the output and check the delete-first rule."""
    rebuilt_a, rebuilt_b = [], []
    seen_insert = False
    for line in out.split(b"\n")[:-1]:
        tag, body = line[:1], line[1:]
        if tag == b"?":
            continue
        if tag == b" ":
            rebuilt_a.append(body)
            rebuilt_b.append(body)
            seen_insert = False
        elif tag == b"-":
            assert not seen_insert, "a - line after a + line in one block"
            rebuilt_a.append(body)
        elif tag == b"+":
            rebuilt_b.append(body)
            seen_insert = True
        else:
            raise AssertionError(f"bad prefix {tag!r}")
    assert rebuilt_a == a and rebuilt_b == b, "output does not rebuild A and B"


def check_runs(a, b, runs):
    pairs = [(i + t, j + t) for i, j, size in runs for t in range(size)]
    for (i, j), (i2, j2) in zip(pairs, pairs[1:]):
        assert i < i2 and j < j2, "pairs not increasing"
    for i, j in pairs:
        assert a[i] == b[j], "kept pair does not match"
    assert len(pairs) == lcs_length(a, b), "diff is not minimal"


def random_tests(count):
    rng = random.Random(1)
    for _ in range(count):
        alphabet = rng.randint(1, 6)
        a = [rng.randrange(alphabet) for _ in range(rng.randint(0, 40))]
        b = [rng.randrange(alphabet) for _ in range(rng.randint(0, 40))]
        if rng.random() < 0.3:  # similar sequences, like real edits
            b = list(a)
            for _ in range(rng.randint(0, 5)):
                p = rng.randint(0, len(b))
                if rng.random() < 0.5 and b:
                    del b[min(p, len(b) - 1)]
                else:
                    b.insert(p, rng.randrange(alphabet + 2))
        check_runs(a, b, main.diff_runs(a, b))
        la = [str(v).encode() for v in a]
        lb = [str(v).encode() for v in b]
        check_render(la, lb, main.render(la, lb, main.diff_runs(a, b), True))


def example_tests():
    # The paper's example: 5 edits.
    a = list(b"abcabba")
    b = list(b"cbabac")
    kept = sum(size for _, _, size in main.diff_runs(a, b))
    assert len(a) + len(b) - 2 * kept == 5

    def hl(old, new):
        return main.highlight_line(old.encode(), new.encode()).decode()

    r = hl("  port = 8000", "  port = 8080")
    assert r in ("? 12-13 | 11-12\n", "? 11-12 | 11-12\n"), r
    assert hl("a = 1", "a = 10") == "? . | 5-6\n"
    assert hl("hi \U0001F600", "hi \U0001F603") == "? 3-4 | 3-4\n"
    assert hl("abc", "abc") == "? . | .\n"
    assert hl("abc", "") == "? 0-3 | .\n"

    # Reading lines.
    assert b"".split(b"\n")[:-1] == []
    out = main.render([b"a", b"b", b"c"], [b"a", b"x", b"c"],
                      main.diff_runs([0, 1, 2], [0, 3, 2]), False)
    assert out == b" a\n-b\n+x\n c\n", out


if __name__ == "__main__":
    example_tests()
    random_tests(20000)
    print("all tests passed")
