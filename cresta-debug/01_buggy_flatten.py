"""
CRESTA DEBUG - Challenge 1: Flatten a Nested List
==================================================
This is a lightly modified version of the flatten implementation already
in this repo (exercism/flatten/flatten_array.py).

There is ONE bug in this code. It is subtle — the function appears to work
on simple inputs but silently produces wrong output on certain nested
structures. Your job is to:

  1. Find the bug.
  2. Write a one-line comment above the broken line explaining what is wrong.
  3. Fix it.

The function should recursively flatten any arbitrarily-nested list (which
may also contain sets and tuples), removing all None values.

Run this file to see which tests fail:
    python3 01_buggy_flatten.py
"""

from collections import deque
from typing import List, Union


def flatten(iterable: List[Union[int, List]]):
    flattened = []

    for elem in iterable:
        if isinstance(elem, (set, tuple, list)):
            tmp = []
            search = deque(elem)
            while search:
                next_elem = search.popleft()
                if isinstance(next_elem, (set, tuple, list)):
                    copied = []
                    # BUG IS SOMEWHERE IN THIS BLOCK
                    for inner_elem in next_elem:  # <-- look carefully here
                        copied.append(inner_elem)
                    search.extendleft(copied)  # <-- and here
                elif next_elem is not None:
                    tmp.append(next_elem)
            flattened.extend(tmp)
        elif elem is not None:
            flattened.append(elem)
    return flattened


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        ([], []),
        ([0, 1, 2], [0, 1, 2]),
        ([[[]]], []),
        ([1, [2, 3, 4, 5, 6, 7], 8], [1, 2, 3, 4, 5, 6, 7, 8]),
        ([0, 2, [[2, 3], 8, 100, 4, [[[50]]]], -2], [0, 2, 2, 3, 8, 100, 4, 50, -2]),
        ([1, [2, [[3]], [4, [[5]]], 6, 7], 8], [1, 2, 3, 4, 5, 6, 7, 8]),
        ([1, 2, None], [1, 2]),
        ([None, None, 3], [3]),
        ([0, 2, [[2, 3], 8, [[100]], None, [[None]]], -2], [0, 2, 2, 3, 8, 100, -2]),
        ([None, [[[None]]], None, None, [[None, None], None], None], []),
    ]

    passed = 0
    for i, (inp, expected) in enumerate(test_cases):
        result = flatten(inp)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            passed += 1
        print(f"[{status}] Test {i + 1}: flatten({inp})")
        if result != expected:
            print(f"         got:      {result}")
            print(f"         expected: {expected}")

    print(f"\n{passed}/{len(test_cases)} tests passed")
