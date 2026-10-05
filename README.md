# Myers' diff

A command-line program that prints a minimal line diff of two files and, for changed lines, the exact characters that differ. Written in Python using only the standard library.

```
python src/main.py lines     A B   # Part A: line diff
python src/main.py highlight A B   # Part B: line diff plus "? old | new" character ranges
```

## How it works

Everything is in [src/main.py](src/main.py).

1. **Read** each file as bytes and split it on `\n` (`read_lines`). A trailing newline adds no empty line, and `\r` stays part of its line.
2. **Number the lines.** Each distinct line gets an integer id, so comparing two lines is a single integer comparison.
3. **Drop lines that cannot be kept** (`diff_runs`). A line of A that never appears in B must be deleted, and a line of B that never appears in A must be inserted. Removing them first leaves the minimal diff unchanged and often makes the input much smaller.
4. **Myers' algorithm, linear-space version** (`_diff` and `middle_snake`).
   - `_diff` keeps the common prefix and suffix, then asks `middle_snake` for a snake that lies on a shortest edit path. It recurses on the part before that snake and the part after it.
   - `middle_snake` runs the greedy search forward from `(0, 0)` and backward from `(n, m)` at the same time. `vf[k]` and `vb[k]` hold the furthest x reached on diagonal `k = x - y`. At step `d`, every diagonal is extended by one edit (down from `k+1` or right from `k-1`, whichever reaches further), then follows its snake. When the forward and backward paths overlap on a diagonal, the snake just followed is the middle snake.
   - Memory is O(N + M), because no V array is stored per step.
5. **Map the kept runs back** to positions in the original files, splitting a run where a dropped line used to be.
6. **Render** (`render`). Between two kept runs is one change block: print all of its `-` lines, then its `+` lines. With `highlight`, the k-th `-` line is paired with the k-th `+` line. The same `diff_runs` runs on the two lines' characters (Python `str` indexes Unicode code points), and the gaps between the kept character runs become the ranges.

`common_prefix` and `common_suffix` measure runs of equal elements by comparing slices of doubling size, then halving size. A long run therefore costs a few slice comparisons in C instead of one Python step per element.

## Testing

```
python tests/stress_test.py                      # checks against a slow O(N*M) LCS on 20,000 random cases
python tests/make_big.py 500000 2000 big         # makes big/big_a.txt and big/big_b.txt for timing
cpsdiff test                                     # the course's public tests
```

On a laptop, 500,000-line files take about 1 s with 100 scattered edits and about 2.4 s with 2,000.
