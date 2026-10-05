"""Minimal line diff (Part A) and changed-character highlights (Part B).

Both parts use Myers' O(ND) algorithm in its linear-space form: find the
"middle snake" of the edit graph with a forward and a backward search, then
solve the parts before and after it recursively.

Usage:
    python src/main.py lines     A B
    python src/main.py highlight A B
"""

import sys


# ---------------------------------------------------------------------------
# Reading input
# ---------------------------------------------------------------------------

def read_lines(path):
    """Read a file as raw bytes and split it into lines on b"\\n".

    A final newline creates no extra empty line, an empty file has no lines,
    and any b"\\r" stays part of its line.
    """
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


# ---------------------------------------------------------------------------
# Common runs
#
# Both helpers compare slices of doubling size until one differs, then of
# halving size (a binary search). A run of length L costs about 2 log L slice
# comparisons, done in C, instead of L steps of a Python loop.
# ---------------------------------------------------------------------------

def common_prefix(a, i, i_end, b, j, j_end):
    """Length of the longest run a[i:i+L] == b[j:j+L] inside both ranges."""
    limit = min(i_end - i, j_end - j)
    length = 0
    step = 1
    growing = True
    while step:
        if length + step <= limit and \
                a[i + length:i + length + step] == b[j + length:j + length + step]:
            length += step
            if growing:
                step *= 2
        else:
            growing = False
            step //= 2
    return length


def common_suffix(a, i_start, i, b, j_start, j):
    """Length of the longest run a[i-L:i] == b[j-L:j] inside both ranges."""
    limit = min(i - i_start, j - j_start)
    length = 0
    step = 1
    growing = True
    while step:
        if length + step <= limit and \
                a[i - length - step:i - length] == b[j - length - step:j - length]:
            length += step
            if growing:
                step *= 2
        else:
            growing = False
            step //= 2
    return length


# ---------------------------------------------------------------------------
# Myers' algorithm
#
# The edit graph has a point (x, y) for every 0 <= x <= n, 0 <= y <= m.
# Moving right (x + 1) deletes a[x], moving down (y + 1) inserts b[y], and a
# diagonal move keeps a[x] == b[y]. A run of diagonal moves is a snake.
# Diagonal k holds the points with x - y == k. V[k] is the furthest x
# reached on diagonal k so far.
# ---------------------------------------------------------------------------

def middle_snake(a, a_lo, a_hi, b, b_lo, b_hi):
    """Find the middle snake of a[a_lo:a_hi] against b[b_lo:b_hi].

    Returns (x_start, y_start, x_end, y_end) in absolute indices: a snake
    that lies on some shortest edit path. Returns None when the two ranges
    have nothing in common.
    """
    n = a_hi - a_lo
    m = b_hi - b_lo
    delta = n - m
    odd = delta & 1
    max_d = (n + m + 1) // 2
    off = max_d                  # V index of diagonal k is off + k
    vf = [-1] * (2 * max_d + 2)  # forward search, from (0, 0)
    vb = [-1] * (2 * max_d + 2)  # backward search, from (n, m), x counted from the end
    vf[off + 1] = 0
    vb[off + 1] = 0
    # Diagonals that have run off the edge of the grid are skipped from then on.
    f_start = f_end = b_start = b_end = 0

    for d in range(max_d):
        # Forward search: extend every (d-1)-path by one edit, then follow
        # the snake from where it lands.
        for k in range(-d + f_start, d + 1 - f_end, 2):
            if k == -d or (k != d and vf[off + k - 1] < vf[off + k + 1]):
                x = vf[off + k + 1]          # step down from diagonal k + 1
            else:
                x = vf[off + k - 1] + 1      # step right from diagonal k - 1
            y = x - k
            x0, y0 = x, y
            if x < n and y < m and a[a_lo + x] == b[b_lo + y]:
                s = 1 + common_prefix(a, a_lo + x + 1, a_hi, b, b_lo + y + 1, b_hi)
                x += s
                y += s
            vf[off + k] = x
            if x > n:
                f_end += 2
            elif y > m:
                f_start += 2
            elif odd:
                # The backward search has done d - 1 steps. Forward diagonal
                # k is backward diagonal delta - k.
                kb = delta - k
                if -(d - 1) <= kb <= d - 1:
                    xb = vb[off + kb]
                    if 0 <= xb <= n and xb - kb <= m and x + xb >= n:
                        return a_lo + x0, b_lo + y0, a_lo + x, b_lo + y

        # Backward search: the same steps, walking from the end towards the start.
        for k in range(-d + b_start, d + 1 - b_end, 2):
            if k == -d or (k != d and vb[off + k - 1] < vb[off + k + 1]):
                x = vb[off + k + 1]
            else:
                x = vb[off + k - 1] + 1
            y = x - k
            x0, y0 = x, y
            if x < n and y < m and a[a_hi - 1 - x] == b[b_hi - 1 - y]:
                s = 1 + common_suffix(a, a_lo, a_hi - 1 - x, b, b_lo, b_hi - 1 - y)
                x += s
                y += s
            vb[off + k] = x
            if x > n:
                b_end += 2
            elif y > m:
                b_start += 2
            elif not odd:
                kf = delta - k
                if -d <= kf <= d:
                    xf = vf[off + kf]
                    if 0 <= xf <= n and xf - kf <= m and xf + x >= n:
                        # Convert the backward snake to forward coordinates.
                        return a_hi - x, b_hi - y, a_hi - x0, b_hi - y0
    return None


def _diff(a, a_lo, a_hi, b, b_lo, b_hi, runs):
    """Append the kept runs (i, j, length) of a minimal diff of the ranges."""
    # A common prefix and a common suffix are always kept.
    prefix = common_prefix(a, a_lo, a_hi, b, b_lo, b_hi)
    if prefix:
        runs.append((a_lo, b_lo, prefix))
        a_lo += prefix
        b_lo += prefix
    suffix = common_suffix(a, a_lo, a_hi, b, b_lo, b_hi)
    a_hi -= suffix
    b_hi -= suffix

    if a_lo < a_hi and b_lo < b_hi:
        snake = middle_snake(a, a_lo, a_hi, b, b_lo, b_hi)
        if snake is not None:
            x0, y0, x1, y1 = snake
            _diff(a, a_lo, x0, b, b_lo, y0, runs)
            if x1 > x0:
                runs.append((x0, y0, x1 - x0))
            _diff(a, x1, a_hi, b, y1, b_hi, runs)

    if suffix:
        runs.append((a_hi, b_hi, suffix))


def diff_runs(a, b):
    """Return the kept runs (i, j, length) of a minimal diff of a and b.

    A run means a[i:i+length] == b[j:j+length] is kept. Every other element
    of a is deleted and every other element of b is inserted. Runs are in
    order, and adjacent runs are merged.
    """
    # An element that never occurs in the other sequence can never be kept,
    # so drop it before running Myers. The minimal diff does not change, and
    # real files often shrink a lot.
    in_a = set(a)
    in_b = set(b)
    a_idx = [i for i, v in enumerate(a) if v in in_b]
    b_idx = [j for j, v in enumerate(b) if v in in_a]
    a2 = [a[i] for i in a_idx]
    b2 = [b[j] for j in b_idx]

    runs = []
    _diff(a2, 0, len(a2), b2, 0, len(b2), runs)

    # Map the runs back to positions in a and b. A dropped element splits a
    # run in two, so halve any run that is not contiguous in a and b.
    result = []

    def add(i, j, length):
        ai, bj = a_idx[i], b_idx[j]
        if a_idx[i + length - 1] - ai == length - 1 and b_idx[j + length - 1] - bj == length - 1:
            if result and result[-1][0] + result[-1][2] == ai and result[-1][1] + result[-1][2] == bj:
                pi, pj, plen = result.pop()
                result.append((pi, pj, plen + length))
            else:
                result.append((ai, bj, length))
        else:
            half = length // 2
            add(i, j, half)
            add(i + half, j + half, length - half)

    for i, j, length in runs:
        add(i, j, length)
    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def changed_ranges(runs, length):
    """Format the positions outside the kept runs (start, length) as ranges."""
    parts = []
    prev = 0
    for start, size in runs:
        if start > prev:
            parts.append(f"{prev}-{start}")
        prev = start + size
    if length > prev:
        parts.append(f"{prev}-{length}")
    return ",".join(parts) if parts else "."


def highlight_line(old, new):
    """Return the "? old | new" line for one paired - and + line."""
    # Decoding to str makes indexing count Unicode code points.
    s = old.decode("utf-8", "surrogateescape")
    t = new.decode("utf-8", "surrogateescape")
    runs = diff_runs(s, t)
    old_ranges = changed_ranges([(i, size) for i, _, size in runs], len(s))
    new_ranges = changed_ranges([(j, size) for _, j, size in runs], len(t))
    return f"? {old_ranges} | {new_ranges}\n".encode("ascii")


def render(a, b, runs, highlight):
    """Build the diff output. Each change block prints its - lines first."""
    out = []
    i = j = 0
    # A final empty run at the end flushes the last change block.
    for ka, kb, length in runs + [(len(a), len(b), 0)]:
        deleted = a[i:ka]
        inserted = b[j:kb]
        if deleted:
            out.append(b"-" + b"\n-".join(deleted) + b"\n")
        if highlight:
            for t, line in enumerate(inserted):
                out.append(b"+" + line + b"\n")
                if t < len(deleted):
                    out.append(highlight_line(deleted[t], line))
        elif inserted:
            out.append(b"+" + b"\n+".join(inserted) + b"\n")
        if length:
            out.append(b" " + b"\n ".join(a[ka:ka + length]) + b"\n")
        i = ka + length
        j = kb + length
    return b"".join(out)


def main():
    args = sys.argv[1:]
    if len(args) != 3 or args[0] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)
    command, path_a, path_b = args

    try:
        a_lines = read_lines(path_a)
        b_lines = read_lines(path_b)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    # Give every distinct line a small integer id, so comparing two lines is
    # an integer comparison instead of a byte-by-byte one.
    ids = {}
    a = [ids.setdefault(line, len(ids)) for line in a_lines]
    b = [ids.setdefault(line, len(ids)) for line in b_lines]

    runs = diff_runs(a, b)
    sys.stdout.buffer.write(render(a_lines, b_lines, runs, command == "highlight"))


if __name__ == "__main__":
    main()
